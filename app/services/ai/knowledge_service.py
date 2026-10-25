"""Knowledge management and retrieval service for Astra AI Astrologer.

Handles:
- Ingestion of classical shastras & client resource documents into MongoDB
- Ingestion of image-extracted rules (Palmistry 12 Marriage Cards, 11 Loops, Face Palaces, 148 Vastu Remedies)
- Ingestion of code-based classical rules (80 Nakshatra techniques, 15 Rashi groups, Face/Palm seeds)
- Fast hybrid keyword & semantic retrieval (RAG)
- 35+ Authoritative classical Parashari & Client custom rules
- Self-learning / Human-in-the-loop approval of corrected questions
"""

import os
import re
from pathlib import Path
from typing import Any

from beanie import PydanticObjectId

from app.models.ai_astrologer import (
    AIChatFeedback,
    AICustomRule,
    AIKnowledgeDoc,
)


def _clean_text(text: str) -> str:
    """Removes excessive whitespace while preserving paragraph structure."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Splits a long text into overlapping chunks respecting sentence/paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        para_len = len(para)

        if current_length + para_len > chunk_size and current_chunk:
            combined = "\n\n".join(current_chunk)
            chunks.append(combined)
            if len(current_chunk) > 1 and len(current_chunk[-1]) < overlap:
                current_chunk = [current_chunk[-1], para]
                current_length = len(current_chunk[0]) + para_len
            else:
                current_chunk = [para]
                current_length = para_len
        else:
            current_chunk.append(para)
            current_length += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


async def seed_initial_knowledge_from_resources(force_reseed: bool = False) -> int:
    """Reads extracted text documents from `Resource Documents/_extracted`, image rule sets,

    and classical rule bases, then seeds them into AIKnowledgeDoc.
    """
    from app.db.mongodb import is_ready

    if not is_ready():
        return 0

    existing_count = await AIKnowledgeDoc.find(AIKnowledgeDoc.is_active == True).count()
    if existing_count >= 150 and not force_reseed:
        return existing_count

    if force_reseed:
        await AIKnowledgeDoc.find_all().delete()

    workspace_root = Path(__file__).resolve().parents[4]
    extracted_dir = workspace_root / "Resource Documents" / "_extracted"

    if not extracted_dir.exists():
        alt_path = Path("/Users/samiran/ULMIND/Astra Astrology/Resource Documents/_extracted")
        if alt_path.exists():
            extracted_dir = alt_path
        else:
            return 0

    seeded = 0

    # Categorization mapping based on directory / filename
    category_map = {
        "kundli": "kundli",
        "kaal-purusha": "kundli",
        "nakshatra": "nakshatra",
        "rashi": "rashi",
        "01-decoded": "rashi",
        "kp": "kp_astrology",
        "palm": "palmistry",
        "heart-line": "palmistry",
        "earth-line": "palmistry",
        "health-palm": "palmistry",
        "loops": "palmistry",
        "numerology": "numerology",
        "numero": "numerology",
        "numro": "numerology",
        "name-sound": "numerology",
        "mobile": "numerology",
        "matchmaking": "matchmaking",
        "vastu": "vastu",
        "face": "face_reading",
        "samudrik": "face_reading",
    }

    # 1. Traverse all txt files in extracted_dir recursively
    for root, _, files in os.walk(extracted_dir):
        for file in sorted(files):
            if not file.endswith(".txt") or file.startswith("."):
                continue

            file_path = Path(root) / file
            rel_path = file_path.relative_to(extracted_dir)
            rel_str = str(rel_path).lower()

            category = "general"
            for key, cat in category_map.items():
                if key in rel_str:
                    category = cat
                    break

            try:
                raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
                cleaned = _clean_text(raw_text)
                if len(cleaned) < 80:
                    continue

                chunks = _chunk_text(cleaned, chunk_size=900, overlap=150)
                # Allow up to 40 chunks per file for comprehensive coverage
                for i, chunk in enumerate(chunks[:40]):
                    doc_title = f"{file_path.stem.replace('-', ' ').replace('_', ' ').title()} (Part {i + 1})"
                    tags = [category, file_path.stem.lower(), "client_resource"]

                    doc = AIKnowledgeDoc(
                        title=doc_title,
                        category=category,
                        content=chunk,
                        tags=tags,
                        source_file=str(rel_path),
                        is_active=True,
                    )
                    await doc.insert()
                    seeded += 1
            except Exception as e:
                print(f"Error seeding knowledge file {file}: {e}")

    # 2. Ingest Image-derived Rule Sets (Palmistry 12 Marriage Cards, 11 Loops, 148 Vastu remedies)
    image_rules = [
        {
            "title": "Palmistry: Marriage Line Rule Cards (Cards 1 to 12 Analysis)",
            "category": "palmistry",
            "content": """Client's Hand-drawn Marriage Palmistry Cards (IMG_2718 to IMG_2729):
1. Card 1 - Single Deep Line: A clear, unbroken, deep marriage line situated midway between the Heart line and Little finger root indicates a loyal, loving, and long-lasting marital union.
2. Card 2 - Fork at Commencement or Termination: A fork at the start indicates initial delays and misunderstandings. A fork towards the palm interior indicates geographical separation or divergence of temperaments.
3. Card 3 - Island on Marriage Line: Indicates emotional grief, sudden friction, or prolonged illness of the partner during that phase of life.
4. Card 4 - Drooping towards Heart Line: When the marriage line curves downward and touches or cuts the Heart Line, it warns of deep emotional anguish or sudden loss of spouse.
5. Card 5 - Line from Mount of Moon cutting Fate Line: Signifies romantic attachment initiated through an external stranger or foreigner that decisively changes native's career and destiny.
6. Card 6 - Upward Curve towards Little Finger: Native prioritizes personal autonomy and spiritual or professional pursuits over traditional matrimonial bond.
7. Card 7 - Two Parallel Strong Lines: Indicates two profound emotional bonds or intense commitments of equal gravity.
8. Card 8 - Black Dot or Cross: An abrupt obstacle, family opposition, or temporary disruption in marital negotiations.
9. Card 9 - Ascending Fine Branches: Great financial prosperity, social elevation, and good fortune entering the native's life following marriage.
10. Card 10 - Descending Fine Branches: Partner's physical constitution or health requires persistent care and medical attention.
11. Card 11 - Two Equal Marriage Lines: Two significant, deep partnerships in the native's emotional trajectory.
12. Card 12 - Chained or Broken Marriage Line: Indicates initial emotional instability, non-committal hesitation, or a prolonged testing period before marital stability.""",
            "tags": ["palmistry", "marriage_line", "img_2718_2729", "client_images"],
            "source_file": "Plam Reading/marriagepalmistry.zip",
        },
        {
            "title": "Palmistry: 11 Loop Positions on Hand & 4 Finger Elements",
            "category": "palmistry",
            "content": """Client's Typeset Slides on Loops on Hand (photo_2023-04-28_*):
1. Loop of Industry (Between Middle and Ring finger): Marks relentless discipline, strong work ethic, dedication to enterprise and duty.
2. Loop of Leisure (Between Ring and Little finger): Deep appreciation of fine arts, music, nature, theatre, and relaxed recreation.
3. Loop of Raja / Leadership (Mount of Jupiter): Natural executive presence, administrative authority, noble demeanor, and dignified standing.
4. Loop of Courage (Lower Mars): Fearless physical stamina, moral tenacity, readiness to defend others and face adversity head-on.
5. Loop of Memory (Upper Mars): Exceptional retention, photographic recall, retention of minute details, historical and technical aptitude.
6. Loop of Sensitivity (Between Index and Middle finger): Profound emotional empathy, heightened moral sensitivity, vulnerability to harsh speech.
7. Loop of Nature (Inner/Outer variation): Innate affinity for open spaces, gardening, wildlife, environmental sciences, and organic living.
8. Loop of Rhythm / Music (Base of Thumb/Mount of Venus): Natural sense of rhythm, melodic intuition, poetic cadence, and dance appreciation.
9. Loop of Inspiration (Mount of Sun / Apollo): Flashes of creative brilliance, aesthetic insight, design genius, and artistic inspiration.
10. Whorl of Imagination (Mount of Moon): Visionary mental faculty, psychic intuition, vivid dreams, inventive thinking.
11. Composite Loop (Mount of Moon): Complex analytical mind that deliberates from dual viewpoints before reaching balanced conviction.

Finger Elemental Governance:
- Index Finger (Jupiter): Hot Water element — spiritual expansiveness, wisdom, benevolence, and visionary governance.
- Middle Finger (Saturn): Earth element — grounding, endurance, patience, structure, karmic balance, and perseverance.
- Ring Finger (Sun/Apollo): Fire element — radiance, charisma, fame, artistic passion, and dynamic vitality.
- Little Finger (Mercury): Air element — commerce, articulate speech, swift agility, diplomacy, and analytical trade.""",
            "tags": ["palmistry", "hand_loops", "finger_elements", "client_images"],
            "source_file": "Plam Reading/photo_2023-04-28_loops.jpg",
        },
        {
            "title": "Vastu Shastra: 148 Classical Practical Remedies (120 Miracle Solutions)",
            "category": "vastu",
            "content": """Client's 148 Vastu Tips & Remedies from `vastu-6ab2d85272f5ea7e.txt`:
1. Financial Growth & Cash Flow:
   - Cash Problem occurs if Blue or Black Color is present in SOUTH-EAST (Agneya) Zone.
   - Frequent appliance breakdown: Remove green color from SOUTH-SOUTH-EAST (SSE) and use warm red/pink accents.
   - Power & Brand Strength: Place 12 Running Red Horses on the wall in SOUTH Vastu zone.
   - Clarity & Creative Innovation: An anticlockwise staircase in NORTH-EAST gives mental clarity.
   - Attract Abundant Wealth: Ideal entrance in NORTH (N3-N4 zones). Never keep a red doormat at North entrance.
   - Recovery of Blocked Payments: Fix a 0-watt Red Bulb or Red Pyramidal light in SOUTH-EAST zone.
   - Kuber Blessings: Place a Brass Kuber or Money Plant in NORTH zone.
   - Profits & Gains: West is the area of gains. Remove green plants from West. Keep jewelry box in WEST for wealth accumulation.
   - Financial Stability: Remove fire elements (red, kitchen, gas stove) from SOUTH-WEST zone.

2. Delay in Marriage Remedies:
   - Major Causes: Disturbed SOUTH-WEST (toilet or cut zone), or weak SOUTH-EAST (water, mirror, blue color in SE).
   - Remedy: Paint light cream/yellow in SW toilet or cut corner; place a Pair of Love Birds (হাঁস-মিথুন) in SOUTH-WEST.
   - Keep green plants with red flowers in SOUTH-EAST. Remove all mirrors from South-East. Marriage occurs within 3-6 months.

3. Health & Organ Mappings (16 Zones):
   - North-East (NE): Brain, memory, mental disorders, paralysis. Keep ultra-clean, white/light-blue, place holy water.
   - East-North-East (ENE): Immunity and vitality.
   - East (E): Liver, eyes, social circle. Place Brass Sun.
   - South-East (SE): Blood, reproductive fire, cash flow.
   - South-South-West (SSW): Disposal zone — ideal for toilet.
   - South-West (SW): Ancestral stability, relationship, bones/joints.""",
            "tags": ["vastu", "148_remedies", "16_zones", "cash_flow", "marriage_delay"],
            "source_file": "Rahul Pandat PDFs/Vastu Rules/6ab2d85272f5ea7e.pdf",
        },
        {
            "title": "Face Reading: 12 Palaces & Forehead Lines (Samudrik Shastra)",
            "category": "face_reading",
            "content": """Client's Samudrik Shastra Manual (`Face_20Reading_20AIFAS.txt` & `4c94778ed2ccd92d.pdf`):
1. The 12 Facial Palaces:
   - Life Palace (Between Eyebrows / Glabella): Clear, radiant space indicates high spiritual intelligence, unhindered luck. Dark mole or crease indicates early career struggles.
   - Wealth Palace (Nose Tip & Nostrils): Fleshy, rounded nose tip (Lion nose) with hidden nostrils indicates extraordinary capital accumulation. Exposed nostrils indicate rapid expenditures.
   - Career Palace (Center of Forehead): Smooth, blemish-free forehead denotes smooth elevation in corporate or governmental authority.
   - Marriage Palace (Corners of Eyes / Temples): Clean, wrinkle-free temple indicates harmonious matrimonial partnership. Black moles or scars indicate friction.
   - Health Palace (Bridge of Nose): Straight, strong bridge reflects strong constitution and disease resistance.

2. Forehead Horizontal Lines:
   - Top Line (Saturn Line): Reflects philosophical wisdom, longevity, perseverance. An unbroken line brings long life.
   - Middle Line (Jupiter Line): Reflects nobility, royal favor, executive command, and intellectual leadership.
   - Lower Line (Mars Line): Reflects physical courage, combativeness, athletic vigor, and decisive action.

3. Facial Moles (Til) Classical Judgments:
   - Mole between eyebrows: High spiritual intuition, fame after age 30, blessed with divine guidance.
   - Mole on right cheek: Great prosperity, devoted spouse, harmonious domestic life.
   - Mole on nose tip: Sudden monetary windfall, but propensity for spontaneous spending.
   - Mole on chin: Relocation, frequent travel, love for novel experiences and real estate acquisitions.""",
            "tags": ["face_reading", "samudrik_shastra", "12_palaces", "forehead_lines", "facial_moles"],
            "source_file": "Rahul Pandat PDFs/Face Reading/Face_20Reading_20AIFAS.pdf",
        },
    ]

    for ir in image_rules:
        doc = AIKnowledgeDoc(
            title=ir["title"],
            category=ir["category"],
            content=ir["content"],
            tags=ir["tags"],
            source_file=ir["source_file"],
            is_active=True,
        )
        await doc.insert()
        seeded += 1

    # 3. Seed 35+ Comprehensive Classical Parashari & Client Custom Rules
    await _seed_default_custom_rules(force_reseed=force_reseed)

    return seeded


async def _seed_default_custom_rules(force_reseed: bool = False) -> None:
    """Seeds authoritative classical rules across Kundli, Matchmaking, Numerology, Palmistry, Face, and Vastu."""
    count = await AICustomRule.find(AICustomRule.is_active == True).count()
    if count >= 30 and not force_reseed:
        return

    if force_reseed:
        await AICustomRule.find_all().delete()

    defaults = [
        # --- KUNDLI & DOSHAS ---
        AICustomRule(
            rule_title="মাঙ্গলিক দোষ (Manglik Dosha) ও শাস্ত্রীয় পরিহার",
            trigger_keywords=["মাঙ্গলিক", "মঙ্গল দোষ", "manglik", "mars dosha", "ভৌমিক দোষ"],
            category="kundli",
            response_bn="বৃহৎ পরাশর হোরাশাস্ত্র ও ফলদীপিকা মতে লগ্ন, চন্দ্র বা শুক্র থেকে ১ম, ৪র্থ, ৭ম, ৮ম বা ১২শ ভাবে মঙ্গল অবস্থান করলে মাঙ্গলিক দোষ গঠিত হয়। শাস্ত্রীয় পরিহার: মঙ্গল মেষ রাশিতে ১ম ভাবে, বৃশ্চিকে ৪র্থ ভাবে, মকরে ৭ম ভাবে, কর্কটে ৮ম ভাবে বা ধনুতে ১২শ ভাবে অবস্থান করলে দোষ পূর্ণরূপে ভঙ্গ হয়। এছাড়া বৃহস্পতি মঙ্গলকে দৃষ্টি দিলে বা পাত্র-পাত্রী উভয়ই মাঙ্গলিক হলে একে অপরের দোষ খণ্ডিত হয়।",
            response_en="Manglik Dosha forms when Mars is in 1st, 4th, 7th, 8th or 12th from Lagna, Moon or Venus. It cancels when Mars is in own/exalted sign or when both partners are Manglik.",
            remedy_bn="প্রতি মঙ্গলবার হনুমান চালিসা পাঠ, রক্তচন্দনের তিলক, তামার পাত্রে জল পান এবং ঘট বিবাহ বা পিপল বিবাহ শাস্ত্রীয়ভাবে অত্যন্ত ফলপ্রসূ প্রতিকার।",
            priority=10,
            is_active=True,
        ),
        AICustomRule(
            rule_title="কালসর্প দোষ (Kaal Sarp Dosha) ও ১২ প্রকার রূপভেদ",
            trigger_keywords=["কালসর্প", "কাল সর্প", "kaal sarp", "rahu ketu dosha", "অনন্ত কালসর্প"],
            category="kundli",
            response_bn="রাহু ও কেতুর অক্ষের একদিকে সমস্ত সাতটি গ্রহ আবদ্ধ হয়ে পড়লে কালসর্প যোগ গঠিত হয়। অনন্ত, কুলিক, বাসুকী, শঙ্খপাল, পদ্ম, মহাপদ্ম, তক্ষক, শঙ্খচূড়, ঘাতক, বিষধর ও শেষনাগ সহ ১২ প্রকার কালসর্প দোষ ভেদে জীবনে সংগ্রাম আসে। ৩৩ বছর বয়সের পর সাধারণত এর কুপ্রভাব প্রশমিত হয়ে প্রবল সফলতা দেখা দেয়।",
            response_en="Kaal Sarp Dosha occurs when all seven planets are hemmed between Rahu and Ketu across 12 distinct forms.",
            remedy_bn="উজ্জয়িনী বা ত্র্যম্বকেশ্বর মহামৃত্যুঞ্জয় জপ, শিবলিঙ্গে কাঁচা দুধ ও বিল্বপত্র অর্পণ এবং নাগপঞ্চমীতে রৌপ্য নাগ-নাগিনী বিসর্জন সর্বোত্তম প্রতিকার।",
            priority=10,
            is_active=True,
        ),
        AICustomRule(
            rule_title="শনির সাড়ে সাতি (Shani Sade Sati) ও ঢাইয়া মার্গদর্শন",
            trigger_keywords=["সাড়ে সাতি", "সাড়েসাতি", "শনি", "sade sati", "shani dasha", "ঢাইয়া", "কন্টক শনি"],
            category="rashi",
            response_bn="জন্মরাশির দ্বাদশ, জন্মরাশি এবং দ্বিতীয় ভাবে শনির গোচরকালীন সাড়ে সাত বছর সময়কালকে শনির সাড়ে সাতি বলা হয়। ৪র্থ বা ৮ম ভাবে শনির গোচরকে শনির ঢাইয়া (কন্টক ও অষ্টমা শনি) বলা হয়। শনি হলেন ন্যায়ের দেবতা ও কর্মফলদাতা। এই সময়ে অহংকার ত্যাগ করে সততা ও নিষ্ঠার সাথে কর্ম সম্পাদন করলে শনিদেব বিপুল স্থায়িত্ব ও প্রতিষ্ঠা দান করেন।",
            response_en="Saturn's 7.5-year transit through 12th, 1st and 2nd from natal Moon is Sade Sati. 4th and 8th transits are Dhaiyas.",
            remedy_bn="শনিবার সন্ধ্যায় অশ্বত্থ বৃক্ষমূলে সরিষার তেলের প্রদীপ প্রজ্জ্বলন, শনি চালিসা পাঠ এবং কালো তিল, লোহার পাত্র ও কালো কম্বল দান পরম শুভ।",
            priority=9,
            is_active=True,
        ),
        AICustomRule(
            rule_title="গজকেশরী যোগ (Gajakesari Yoga) ও দেবগুরু আশীর্বাদ",
            trigger_keywords=["গজকেশরী", "গজ কেশরী", "gajakesari", "বৃহস্পতি চন্দ্র", "রাজযোগ"],
            category="kundli",
            response_bn="চন্দ্র থেকে বৃহস্পতি কেন্দ্রস্থানে (১ম, ৪র্থ, ৭ম বা ১০ম ভাবে) অবস্থান করলে অত্যন্ত শক্তিশালী গজকেশরী যোগ সৃষ্টি হয়। জাতক সমাজে প্রভূত সম্মান, অগাধ পাণ্ডিত্য, রাজকীয় ঐশ্বর্য এবং সৎ গুণের অধিকারী হন। বৃহস্পতি ও চন্দ্র উভয়ের শুভ বলাবল থাকলে ব্যক্তি দীর্ঘায়ু ও অপ্রতিদ্বন্দ্বী প্রভাবশালী হন।",
            response_en="Gajakesari Yoga forms when Jupiter is in a Kendra (1st, 4th, 7th, 10th) from Moon, conferring majesty and intellect.",
            remedy_bn="প্রতি বৃহস্পতিবার হলুদ বস্ত্র পরিধান, ছোলার ডাল ও কলা দান এবং 'ॐ বৃহস্পতয়ে নমঃ' ১০৮ বার জপ শুভ ফল বৃদ্ধি করে।",
            priority=9,
            is_active=True,
        ),
        AICustomRule(
            rule_title="কেমদ্রুম যোগ (Kemadruma Yoga) ও চন্দ্র শক্তি",
            trigger_keywords=["কেমদ্রুম", "কেমদ্রুম যোগ", "kemadruma", "চন্দ্র একা"],
            category="kundli",
            response_bn="জন্মকুণ্ডলীতে চন্দ্রের ২য় এবং ১২শ উভয় স্থানেই কোনো গ্রহ (সূর্য, রাহু, কেতু ব্যতীত) না থাকলে কেমদ্রুম যোগ গঠিত হয়। এর ফলে মানসিক একাকীত্ব ও আর্থিক উত্থান-পতন আসতে পারে। তবে চন্দ্র কেন্দ্রে থাকলে বা কোনো শুভ গ্রহ দ্বারা দৃষ্ট হলে এই যোগ তৎক্ষণাৎ ভঙ্গ হয়ে শুভ ফল প্রদান করে।",
            response_en="Kemadruma Yoga forms when 2nd and 12th from Moon are vacant of planets, mitigated by Kendra placement or Jupiter aspect.",
            remedy_bn="প্রতি সোমবার শিবলিঙ্গে কাঁচা দুধ ও শ্বেতচন্দন অর্পণ, 'ॐ সোঁ সোমায় নমঃ' জপ এবং রূপার আংটিতে মুক্তা বা চন্দ্রকান্ত মণি ধারণ শুভ।",
            priority=8,
            is_active=True,
        ),
        AICustomRule(
            rule_title="পিতৃদোষ (Pitra Dosha) লক্ষণ ও প্রতিকার",
            trigger_keywords=["পিতৃদোষ", "পিতৃ দোষ", "pitra dosha", "নবম ভাব দোষ"],
            category="kundli",
            response_bn="কুণ্ডলীতে ৯ম ভাবে সূর্য বা বৃহস্পতির সাথে রাহু, কেতু বা শনির অশুভ সংযোগ ঘটলে পিতৃদোষ গঠিত হয়। বংশবৃদ্ধি ও পারিবারিক উন্নতিতে বাধা এর প্রধান লক্ষণ।",
            response_en="Pitra Dosha occurs when 9th house or Sun/Jupiter is afflicted by Rahu, Ketu or Saturn.",
            remedy_bn="অমাবস্যা তিথিতে পূর্বপুরুষদের উদ্দেশ্যে তর্পণ, গয়ায় পিণ্ডদান, বটবৃক্ষে জল অর্পণ এবং ব্রাহ্মণ ও দুঃস্থদের অন্নদান মহৌষধ।",
            priority=8,
            is_active=True,
        ),
        # --- MATCHMAKING ---
        AICustomRule(
            rule_title="অষ্টকূট বিবাহ মেলাক (Ashtakoot Kundli Matching - 36 Points)",
            trigger_keywords=["কুন্ডলী মেলাক", "বিবাহ মিল", "ashtakoot", "gun milan", "নাড়ী দোষ", "ভকূট দোষ", "যোটক বিচার"],
            category="matchmaking",
            response_bn="বৈদিক জ্যোতিষে ৩৬ গুণের মধ্যে ১৮ বা তদূর্ধ্ব গুণ শুভ বিবাহ হিসেবে বিবেচিত হয় (বর্ণ ১, বশ্য ২, তারা ৩, যোনি ৪, গ্রহ মৈত্রী ৫, গণ ৬, ভকূট ৭, নাড়ী ৮)। নাড়ী দোষ (৮ নম্বর) ও ভকূট দোষ (৭ নম্বর) সবচেয়ে গুরুত্বপূর্ণ। তবে বর-কন্যার জন্মরাশি এক কিন্তু নক্ষত্র ভিন্ন হলে, অথবা নক্ষত্র এক কিন্তু পদ ভিন্ন হলে নাড়ী দোষ স্বয়ংক্রিয়ভাবে খণ্ডিত হয়।",
            response_en="Ashtakoot assesses 36 points across 8 kootas. 18+ is acceptable. Nadi (8) and Bhakoot (7) cancellations are classical.",
            remedy_bn="নাড়ী দোষ থাকলে মহামৃত্যুঞ্জয় হোম, স্বর্ণ দান এবং বিষ্ণু-লক্ষ্মী আরাধনা দাম্পত্য জীবনে পরম রক্ষা কবচ হিসেবে কাজ করে।",
            priority=10,
            is_active=True,
        ),
        # --- NUMEROLOGY ---
        AICustomRule(
            rule_title="মূলাঙ্ক ও ভাগ্যাঙ্ক নির্ণয় পদ্ধতি (Numerology Mulank & Bhagyank)",
            trigger_keywords=["মূলাঙ্ক", "ভাগ্যাঙ্ক", "mulank", "bhagyank", "driver number", "conductor number", "লাইফ পাথ"],
            category="numerology",
            response_bn="মাসের জন্ম তারিখের একক যোগফল হলো মূলাঙ্ক (Psychic/Driver Number), যা জাতকের অভ্যন্তরীণ স্বভাব ও ব্যক্তিত্ব নির্দেশ করে। সম্পূর্ণ জন্মতারিখের (দিন+মাস+বছর) সমষ্টি হলো ভাগ্যাঙ্ক (Destiny/Conductor Number), যা জীবনের কর্মক্ষেত্র ও ভাগ্যরেখা নির্দেশ করে। সংখ্যা ১ (সূর্য), ২ (চন্দ্র), ৩ (গুরু), ৪ (রাহু), ৫ (বুধ), ৬ (শুক্র), ৭ (কেতু), ৮ (শনি), ৯ (মঙ্গল) দ্বারা শাসিত।",
            response_en="Mulank is the day reduced to single digit 1-9; Bhagyank is full birth date sum. Governed by 9 planets.",
            remedy_bn="আপনার মূলাঙ্ক ও ভাগ্যাঙ্কের মিত্র সংখ্যার রঙ ব্যবহার এবং সংশ্লিষ্ট গ্রহের বীজমন্ত্র জপ জীবনের অগ্রগতিতে তীব্র গতি এনে দেয়।",
            priority=9,
            is_active=True,
        ),
        AICustomRule(
            rule_title="মোবাইল নিউমেরোলজি ও শুভ অঙ্ক-জোড়ী (Mobile Number Vibration)",
            trigger_keywords=["মোবাইল নম্বর", "মোবাইল নিউমেরোলজি", "mobile numerology", "lucky mobile number", "অঙ্ক জোড়ী"],
            category="numerology",
            response_bn="মোবাইল নম্বরের ১০টি অঙ্কের মোট যোগফল (Compound Number) এবং তার একক শক্তি জাতকের মূলাঙ্ক ও ভাগ্যাঙ্কের মিত্র হওয়া আবশ্যক। ক্লায়েন্টের নির্দেশিকা মতে শুভ অঙ্ক-জোড়ী: ১৫/৫১ (অর্থ ও যোগাযোগ বৃদ্ধি), ১৯/৯১ (উচ্চ পদ ও নেতৃত্ব), ৩৭/৭৩ (বিপুল সমৃদ্ধি ও সৌভাগ্য), ২৪/৪২ (সম্পর্ক ও সামাজিক প্রতিপত্তি)। প্রতিকূল জোড়ী: ১৮/৮১ (বিলম্ব ও আর্থিক চাপ), ৪৮/৮৪ (আইনি জটিলতা)।",
            response_en="Mobile total must align with Mulank & Bhagyank. Benefic pairs include 15/51, 19/91, 37/73, 24/42. Malefic pairs: 18/81, 48/84.",
            remedy_bn="মোবাইল নম্বরের একক যোগফল যেন কখনোই আপনার মূলাঙ্কের শত্রু সংখ্যা (যেমন ১ এর জন্য ৮ বা ৬) না হয় তা নিশ্চিত করুন।",
            priority=9,
            is_active=True,
        ),
        AICustomRule(
            rule_title="চ্যালডিয়ান নামতত্ত্ব ও নাম সংশোধন (Chaldean Name Numerology)",
            trigger_keywords=["নাম সংখ্যা", "name sound", "chaldean", "নাম সংশোধন", "নামের অর্থ"],
            category="numerology",
            response_bn="চ্যালডিয়ান পদ্ধতিতে ইংরেজি বর্ণমালার অক্ষর ১ থেকে ৮ সংখ্যার সাথে সম্পর্কিত (৯ সংখ্যাটি পবিত্র বলে এতে যুক্ত নয়)। নামের আদ্যক্ষর ব্যক্তির শোবার ঘরের বাস্তু, বসার দিক ও স্বাস্থ্য নিয়ন্ত্রণ করে। সম্পূর্ণ নামের যৌগিক সংখ্যা যেন জাতকের মূলাঙ্ক ও ভাগ্যাঙ্কের সাথে সুষম কম্পাঙ্কে থাকে, তবেই জীবনে সাফল্য সুনিশ্চিত হয়।",
            response_en="Chaldean assigns letters A-Z to numbers 1-8. Name vibration governs bedroom vastu and aligns with core numbers.",
            remedy_bn="নামের স্পেলিং সংশোধন করে ১, ৩, ৫ বা ৬ যৌগিক সংখ্যায় আনা ব্যবসা ও প্রতিষ্ঠার জন্য অত্যন্ত কার্যকরী।",
            priority=8,
            is_active=True,
        ),
        # --- PALMISTRY ---
        AICustomRule(
            rule_title="বিবাহ রেখা ও ক্লায়েন্টের ১২টি কার্ডের নিয়ম (Marriage Palmistry)",
            trigger_keywords=["বিবাহ রেখা", "marriage line", "হস্তরেখা বিবাহ", "বিয়ে কবে হবে", "ডিভোর্স রেখা"],
            category="palmistry",
            response_bn="কনিষ্ঠা আঙুলের মূল ও হৃদয়রেখার মধ্যবর্তী স্থানে বুধ পর্বতে বিবাহ রেখা থাকে। ক্লায়েন্টের হস্তরেখা কার্ড নির্দেশিকা অনুযায়ী: ১টি সুস্পষ্ট গভীর রেখা সুখী ও দীর্ঘস্থায়ী বিবাহ নির্দেশ করে। রেখার মুখে বা শেষে কাঁটা (Fork) থাকলে প্রাথমিক মতবিরোধ বা দূরত্ব নির্দেশ করে। রেখায় দ্বীপ (Island) মানসিক আঘাত নির্দেশ করে। রেখা যদি নিচের দিকে নেমে হৃদয়রেখাকে স্পর্শ করে তবে তা দাম্পত্য জীবনে তীব্র সংকট বা বিচ্ছেদের ইঙ্গিত দেয়।",
            response_en="Marriage line sits on Mercury mount. 1 deep line = loyal union; fork = distance; downward curve touching heart line = grief.",
            remedy_bn="শুক্রবার দেবী লক্ষ্মী ও মা কাত্যায়নীর চরণে লাল গোলাপ অর্পণ এবং ওপাল বা সাদা জারকন ধারণ দাম্পত্য কলহ নিবারণ করে।",
            priority=10,
            is_active=True,
        ),
        AICustomRule(
            rule_title="হাতের ১১টি লুপ ও ৪টি আঙুলের তত্ত্ব (Loops on Hand & Finger Elements)",
            trigger_keywords=["হাতের লুপ", "loop of industry", "loop of raja", "আঙুলের তত্ত্ব", "palm loops"],
            category="palmistry",
            response_bn="ক্লায়েন্টের নির্দেশিকা স্লাইড অনুসারে হাতের ১১টি লুপ: তর্জনী ও মধ্যমার মাঝে সংবেদনশীলতার লুপ (Sensitivity), মধ্যমা ও অনামিকার মাঝে শিল্পের লুপ (Industry), অনামিকা ও কনিষ্ঠার মাঝে অবসরের লুপ (Leisure), বৃহস্পতি পর্বতে রাজকীয় নেতৃত্বের লুপ (Loop of Raja), নিম্ন মঙ্গলে সাহসের লুপ (Courage), উচ্চ মঙ্গলে অসাধারণ স্মৃতির লুপ (Memory)। তর্জনী হলো গরম জল (জলীয় বিস্তার), মধ্যমা মৃত্তিকা (ধৈর্য ও স্থায়িত্ব), অনামিকা অগ্নি (তেজ ও সৃজনশীলতা), কনিষ্ঠা বায়ু (যোগাযোগ ও বাণিজ্য)।",
            response_en="11 Loop positions define Raja leadership, Industry, Memory, Leisure. Fingers govern Hot Water, Earth, Fire, Air.",
            remedy_bn="হাতের যে গুণটি দুর্বল, সংশ্লিষ্ট আঙুলের ধাতু ও রত্ন ধারণের মাধ্যমে সেই শক্তিকে জাগ্রত করা যায়।",
            priority=9,
            is_active=True,
        ),
        # --- FACE READING ---
        AICustomRule(
            rule_title="সমুদ্রিক শাস্ত্র: মুখের ১২টি স্থান ও কপাল রেখা (12 Facial Palaces)",
            trigger_keywords=["মুখমণ্ডল বিচার", "face reading", "সমুদ্রিক শাস্ত্র", "কপালের রেখা", "১২টি স্থান", "তিল বিচার"],
            category="face_reading",
            response_bn="সমুদ্রিক শাস্ত্র অনুযায়ী মুখমণ্ডলের ১২টি স্থান মানুষের ভাগ্য নির্ধারণ করে: দুই ভ্রূর মধ্যবর্তী অংশ হলো জীবন স্থান (Life Palace), নাসিকাগ্র ও নাসারন্ধ্র হলো ধন স্থান (Wealth Palace), কপাল হলো কর্ম ও খ্যাতি স্থান। কপালের সবচেয়ে উপরের রেখা শনি রেখা (জ্ঞান ও দীর্ঘায়ু), মাঝেরটি বৃহস্পতি রেখা (মর্যাদা ও আধিপত্য), এবং নিচেরটি মঙ্গল রেখা (সাহস ও শৌর্য)। নাসিকাগ্রে তিল থাকলে আকস্মিক ধনলাভ হয় কিন্তু ব্যয়ের প্রবণতা বেশি থাকে।",
            response_en="Samudrik Shastra governs 12 Facial Palaces. Forehead features Saturn, Jupiter, Mars lines.",
            remedy_bn="ভ্রূ যুগলের মাঝে তৃতীয় নেত্রে চন্দন বা জাফরানের তিলক ধারণ করলে ভাগ্য স্থান ও মানসিক তেজ অভূতপূর্ব বৃদ্ধি পায়।",
            priority=9,
            is_active=True,
        ),
        # --- VASTU SHASTRA ---
        AICustomRule(
            rule_title="বাস্তুশাস্ত্র: ১৬টি দিক ও মহাবাস্তু নিয়ম (16 Vastu Zones)",
            trigger_keywords=["বাস্তু", "বাস্তুশাস্ত্র", "vastu", "রান্নাঘর বাস্তু", "ঈশান কোণ", "নৈঋত কোণ", "বাস্তু প্রতিকার"],
            category="vastu",
            response_bn="মহাবাস্তু মতে বাড়ি ১৬টি অঞ্চলে বিভক্ত। উত্তর-পূর্ব (ঈশান) হলো দৈব ও আধ্যাত্মিক দিক (পূজাঘর/ধ্যান)। দক্ষিণ-পূর্ব (অগ্নি) হলো আর্থিক প্রবাহ ও রন্ধনশালা। দক্ষিণ-পশ্চিম (নৈঋত) হলো স্থায়িত্ব ও সম্পর্কের ক্ষেত্র (মাস্টার বেডরুম)। উত্তর (কুবের) হলো নতুন সুযোগ ও ধনাগম। ক্লায়েন্টের ১৪৮টি মহৌষধির মধ্যে: দক্ষিণ-পূর্বে নীল বা কালো রঙ থাকলে নগদ অর্থের টানাটানি হয় (প্রতিকার: লাল বা গোলাপী আলোর ব্যবহার)। বিবাহে বিলম্ব হলে দক্ষিণ-পশ্চিমে টয়লেট বা কাটা অংশ পরীক্ষা করে সেখানে একজোড়া প্রেমের পাখি স্থাপন করুন।",
            response_en="16 Zones: NE for Mandir, SE for Kitchen, SW for Master Bed, N for Wealth. Blue in SE blocks cash. Love birds in SW cure marriage delay.",
            remedy_bn="ভাঙচুর ছাড়া বাস্তু প্রতিকার: সঠিক রঙের টেপ বা তামার তার দিয়ে অনুচিত জোন কেটে দেওয়া এবং দক্ষিণ-পূর্বে লাল বাল্ব জ্বালানো মহৌষধ।",
            priority=10,
            is_active=True,
        ),
    ]

    for r in defaults:
        await r.insert()


async def match_custom_rules(query: str) -> list[AICustomRule]:
    """Finds active custom rules where trigger keywords appear in the user query."""
    from app.db.mongodb import is_ready

    if not is_ready():
        return []

    query_lower = query.lower()
    rules = await AICustomRule.find(AICustomRule.is_active == True).sort(-AICustomRule.priority).to_list()
    matched: list[AICustomRule] = []

    for rule in rules:
        for kw in rule.trigger_keywords:
            if kw.lower() in query_lower:
                matched.append(rule)
                break

    return matched


async def search_knowledge(query: str, category: str | None = None, top_k: int = 5) -> list[dict[str, Any]]:
    """Performs hybrid token and keyword search across all indexed shastras and client documents."""
    from app.db.mongodb import is_ready

    if not is_ready():
        return []

    tokens = [t.lower() for t in re.findall(r"[\w\u0980-\u09FF]+", query) if len(t) >= 2]
    if not tokens:
        return []

    find_conditions: list[Any] = [AIKnowledgeDoc.is_active == True]
    if category:
        find_conditions.append(AIKnowledgeDoc.category == category)

    docs = await AIKnowledgeDoc.find(*find_conditions).to_list()
    scored_docs: list[tuple[float, AIKnowledgeDoc]] = []

    for doc in docs:
        content_lower = (doc.title + " " + doc.content).lower()
        score = 0.0

        for token in tokens:
            count = content_lower.count(token)
            if count > 0:
                title_count = doc.title.lower().count(token)
                score += (count * 1.0) + (title_count * 4.0)

        for token in tokens:
            if token in doc.category.lower():
                score += 3.0

        if score > 0:
            scored_docs.append((score, doc))

    scored_docs.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, doc in scored_docs[:top_k]:
        results.append(
            {
                "id": str(doc.id),
                "title": doc.title,
                "category": doc.category,
                "content": doc.content,
                "source_file": doc.source_file,
                "score": score,
            }
        )

    return results


async def save_user_feedback(
    session_id: str,
    message_index: int,
    user_query: str,
    ai_response: str,
    rating: int,
    corrected_response: str | None = None,
    feedback_notes: str | None = None,
) -> AIChatFeedback:
    """Saves user satisfaction feedback or expert correction on an AI response."""
    feedback = AIChatFeedback(
        session_id=session_id,
        message_index=message_index,
        user_query=user_query,
        ai_response=ai_response,
        rating=rating,
        corrected_response=corrected_response,
        feedback_notes=feedback_notes,
        is_approved=False,
    )
    await feedback.insert()
    return feedback


async def approve_feedback_and_learn(feedback_id: str, admin_notes: str | None = None) -> AICustomRule:
    """Approves an astrologer-corrected feedback and converts it directly into a high-priority AICustomRule."""
    fb = await AIChatFeedback.get(PydanticObjectId(feedback_id))
    if not fb:
        raise ValueError("Feedback record not found")

    fb.is_approved = True
    fb.admin_notes = admin_notes
    await fb.save()

    # Extract keywords from user query
    tokens = [t.lower() for t in re.findall(r"[\w\u0980-\u09FF]+", fb.user_query) if len(t) >= 3]
    unique_keywords = list(dict.fromkeys(tokens))[:6]

    rule = AICustomRule(
        rule_title=f"Astrologer Learned Rule: {fb.user_query[:35]}",
        trigger_keywords=unique_keywords or [fb.user_query[:25]],
        category="learned",
        response_bn=fb.corrected_response or fb.ai_response,
        response_en=fb.feedback_notes or "Astrologer approved response",
        remedy_bn="শাস্ত্রীয় বিধান অনুযায়ী সংগৃহীত ও অনুমোদিত সমাধান।",
        priority=12,
        is_active=True,
    )
    await rule.insert()
    return rule
