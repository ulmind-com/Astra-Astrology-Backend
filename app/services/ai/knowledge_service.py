"""Knowledge management and retrieval service for Astra AI Astrologer.

Handles:
- Ingestion of classical shastras & client resource documents into MongoDB
- Keyword & semantic retrieval (RAG)
- Admin custom rules management
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
            # Retain the last paragraph for overlap if possible
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


async def seed_initial_knowledge_from_resources() -> int:
    """Reads extracted text documents from `Resource Documents/_extracted` and seeds AIKnowledgeDoc.

    Only runs if the collection is empty or has fewer than 10 documents.
    """
    from app.db.mongodb import is_ready

    if not is_ready():
        return 0

    existing_count = await AIKnowledgeDoc.find(AIKnowledgeDoc.is_active == True).count()
    if existing_count >= 20:
        return existing_count

    workspace_root = Path(__file__).resolve().parents[4]
    extracted_dir = workspace_root / "Resource Documents" / "_extracted"

    if not extracted_dir.exists():
        # Fallback relative to project if running in another context
        alt_path = Path("/Users/samiran/ULMIND/Astra Astrology/Resource Documents/_extracted")
        if alt_path.exists():
            extracted_dir = alt_path
        else:
            return 0

    seeded = 0

    # Categorization mapping based on directory / filename
    category_map = {
        "kundli": "kundli",
        "rashi": "rashi",
        "palm": "palmistry",
        "numerology.txt": "numerology",
        "vedic-numero.txt": "numerology",
        "new-numro.txt": "numerology",
        "name-sound.txt": "numerology",
        "name-sound-v2.txt": "numerology",
        "mobile-number.txt": "numerology",
        "mobile-number-v2.txt": "numerology",
        "matchmaking-sample-report.txt": "matchmaking",
        "vastu": "vastu",
        "face": "face_reading",
        "astrology-api-research.txt": "kundli",
    }

    # Traverse all txt files in extracted_dir
    for root, _, files in os.walk(extracted_dir):
        for file in files:
            if not file.endswith(".txt") or file.startswith("."):
                continue

            file_path = Path(root) / file
            rel_path = file_path.relative_to(extracted_dir)

            # Determine category
            category = "general"
            for key, cat in category_map.items():
                if key in str(rel_path).lower():
                    category = cat
                    break

            try:
                raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
                cleaned = _clean_text(raw_text)
                if len(cleaned) < 100:
                    continue

                chunks = _chunk_text(cleaned, chunk_size=900, overlap=150)
                for i, chunk in enumerate(chunks[:25]):  # Cap at 25 chunks per large file for balance
                    doc_title = f"{file_path.stem.replace('-', ' ').title()} (Part {i + 1})"
                    tags = [category, file_path.stem.lower()]

                    # Create document
                    doc = AIKnowledgeDoc(
                        title=doc_title,
                        category=category,
                        content=chunk,
                        tags=tags,
                        source_file=file,
                        is_active=True,
                    )
                    await doc.insert()
                    seeded += 1
            except Exception as e:
                print(f"Error seeding knowledge file {file}: {e}")

    # Also seed core classical Parashari rules into AICustomRule
    await _seed_default_custom_rules()

    return seeded


async def _seed_default_custom_rules() -> None:
    """Seeds baseline authoritative classical rules into AICustomRule if collection is empty."""
    count = await AICustomRule.find(AICustomRule.is_active == True).count()
    if count > 0:
        return

    defaults = [
        AICustomRule(
            rule_title="মাঙ্গলিক দোষ (Manglik Dosha) ও পরিহার",
            trigger_keywords=["মাঙ্গলিক", "মঙ্গল দোষ", "manglik", "mars dosha", "ভৌমিক দোষ"],
            category="kundli",
            response_bn="বৃহৎ পরাশর হোরাশাস্ত্র মতে লগ্ন, চন্দ্র বা শুক্র থেকে ১ম, ৪র্থ, ৭ম, ৮ম বা ১২শ ভাবে মঙ্গল অবস্থান করলে মাঙ্গলিক দোষ গঠিত হয়। তবে মেষ রাশিতে মঙ্গল ১ম ভাবে, কর্কটে ৮ম ভাবে বা ধনুতে ১২শ ভাবে অবস্থান করলে দোষ স্বয়ংভঙ্গ হয়। পাত্র ও পাত্রী উভয়েই মাঙ্গলিক হলে একে অপরের দোষ খণ্ডিত হয়।",
            response_en="Manglik Dosha occurs when Mars is placed in 1st, 4th, 7th, 8th or 12th from Lagna, Moon or Venus. It cancels when Mars is in own/exalted sign or when both partners are Manglik.",
            remedy_bn="প্রতি মঙ্গলবার হনুমান চালিসা পাঠ, উজ্জ্বল রক্তচন্দন ধারণ এবং ঘট বিবাহ বা পিপল বিবাহ শাস্ত্রীয়ভাবে অত্যন্ত ফলপ্রসূ প্রতিকার।",
            priority=10,
            is_active=True,
        ),
        AICustomRule(
            rule_title="কালসর্প দোষ (Kaal Sarp Dosha) ও শিবসাধনা",
            trigger_keywords=["কালসর্প", "কাল সর্প", "kaal sarp", "rahu ketu dosha"],
            category="kundli",
            response_bn="রাহু ও কেতুর অক্ষের একদিকে সমস্ত গ্রহ আবদ্ধ হয়ে পড়লে কালসর্প যোগ গঠিত হয়। অনন্ত, কুলিক, বাসুকী, শঙ্খপাল, পদ্ম, মহাপদ্ম, তক্ষক, শঙ্খচূড়, ঘাতক, বিষধর, শেষনাগ সহ ১২ প্রকার কালসর্প দোষের প্রভাব ভেদে জীবনে সংগ্রাম আসে। ২৮-৩৩ বছর বয়সের পর সাধারণত এর প্রভাব প্রশমিত হয়।",
            response_en="Kaal Sarp Dosha forms when all planets are hemmed between Rahu and Ketu axis across 12 classical forms.",
            remedy_bn="উজ্জয়িনী বা ত্র্যম্বকেশ্বর মহামৃত্যুঞ্জয় জপ, শিবলিঙ্গে কাঁচা দুধ ও বিল্বপত্র অর্পণ এবং নাগপঞ্চমীতে রৌপ্য নাগ-নাগিনী বিসর্জন সর্বোত্তম প্রতিকার।",
            priority=10,
            is_active=True,
        ),
        AICustomRule(
            rule_title="শনির সাড়ে সাতি (Shani Sade Sati) মার্গদর্শন",
            trigger_keywords=["সাড়ে সাতি", "সাড়েসাতি", "শনি", "sade sati", "shani dasha", "শনির দৃষ্টি"],
            category="rashi",
            response_bn="জন্মরাশির দ্বাদশ, জন্মরাশি এবং দ্বিতীয় ভাবে শনির গোচরকালীন সাড়ে সাত বছর সময়কালকে শনির সাড়ে সাতি বলা হয়। শনি হলেন ন্যায়ের দেবতা ও কর্মফলদাতা। এই সময়ে অহংকার ত্যাগ করে সততা ও নিষ্ঠার সাথে কর্ম সম্পাদন করলে শনিদেব শুভ ফল প্রদান করেন।",
            response_en="Saturn's 7.5-year transit through 12th, 1st and 2nd houses from natal Moon is Sade Sati.",
            remedy_bn="শনিবার সন্ধ্যায় অশ্বত্থ বৃক্ষমূলে সরিষার তেলের প্রদীপ প্রজ্জ্বলন, শনি চালিসা পাঠ এবং কালো তিল ও কালো কম্বল দান পরম শুভ।",
            priority=9,
            is_active=True,
        ),
        AICustomRule(
            rule_title="বৃহস্পতির শুভ গোচর ও গুরু আশীর্বাদ",
            trigger_keywords=["বৃহস্পতি", "গুরু", "jupiter", "guru gochar", "বৃহস্পতির প্রভাব"],
            category="rashi",
            response_bn="দেবগুরু বৃহস্পতি ধর্ম, জ্ঞান, সন্তান ও সৌভাগ্যের কারক। জন্মরাশি সাপেক্ষে ২য়, ৫ম, ৭ম, ৯ম ও ১১শ ভাবে বৃহস্পতির গোচর সর্বতোভাবে শুভ ফল ও সমৃদ্ধি প্রদান করে। ৫ম ও ৯ম দৃষ্টির দ্বারা তিনি যেকোনো অশুভ প্রভাব বিনাশ করেন।",
            response_en="Jupiter transit through 2nd, 5th, 7th, 9th, 11th from Moon confers wisdom, expansion and wealth.",
            remedy_bn="প্রতি বৃহস্পতিবার হলুদ পোশাক পরিধান, ছোলার ডাল ও কলা দান এবং 'ॐ বৃহস্পতয়ে নমঃ' ১০৮ বার জপ করা শুভ।",
            priority=8,
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


async def search_knowledge(query: str, category: str | None = None, top_k: int = 4) -> list[dict[str, Any]]:
    """Performs keyword and token-based search across AIKnowledgeDoc."""
    from app.db.mongodb import is_ready

    if not is_ready():
        return []

    # Extract search tokens (words with >= 3 characters)
    tokens = [t.lower() for t in re.findall(r"[\w\u0980-\u09FF]+", query) if len(t) >= 2]
    if not tokens:
        return []

    # Build query
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
                # Title matches have higher weight
                title_count = doc.title.lower().count(token)
                score += (count * 1.0) + (title_count * 3.0)

        # Boost if category matches tokens
        for token in tokens:
            if token in doc.category.lower():
                score += 2.0

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
    feedback_reason: str = "",
) -> AIChatFeedback:
    """Records user thumbs-up/thumbs-down feedback for human review."""
    feedback = AIChatFeedback(
        session_id=session_id,
        message_index=message_index,
        user_query=user_query,
        ai_response=ai_response,
        rating=rating,
        feedback_reason=feedback_reason,
        reviewed_by_admin=False,
    )
    await feedback.insert()
    return feedback


async def approve_feedback_and_learn(
    feedback_id: str,
    admin_corrected_response: str,
    rule_title: str | None = None,
    keywords: list[str] | None = None,
) -> AICustomRule:
    """Admin approves/corrects a question and automatically converts it into a learned rule."""
    feedback = await AIChatFeedback.get(PydanticObjectId(feedback_id))
    if not feedback:
        raise ValueError(f"Feedback {feedback_id} not found")

    feedback.reviewed_by_admin = True
    feedback.admin_corrected_response = admin_corrected_response
    feedback.added_to_knowledge = True
    await feedback.save()

    # Create new custom rule so AI permanently learns the exact verified answer
    title = rule_title or f"Learned Rule: {feedback.user_query[:50]}"
    kw = keywords or [w.strip() for w in feedback.user_query.split() if len(w) > 3][:6]
    if not kw:
        kw = [feedback.user_query[:20]]

    new_rule = AICustomRule(
        rule_title=title,
        trigger_keywords=kw,
        category="learned",
        response_bn=admin_corrected_response,
        priority=12,  # Higher than default to prioritize learned knowledge
        is_active=True,
    )
    await new_rule.insert()
    return new_rule
