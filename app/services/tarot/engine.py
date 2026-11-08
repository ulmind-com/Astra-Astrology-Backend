"""Chrono-Astrological Tarot Engine (CATE).

Implements world-class 78-card Tarot reading engine with:
- Canonical Major and Minor Arcana symbolism
- Astrological (Zodiac/Planetary) and Vedic Graha resonance
- Elemental Dignities & Harmonic balance calculation
- Multi-pillar interpretations (General, Love, Career, Finance, Spiritual)
- Trilingual synthesis: English, Bengali (বাংলা), Hindi (हिन्दी)
- High-precision Chrono-Elemental Timing Window predictions
- Interactive tactile draws or planetary dasha-weighted draws
- Comprehensive karmic synthesis and Vedic remedial guidance
"""

from __future__ import annotations

import hashlib
import random
import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas.tarot import (
    DailyTarotRequest,
    DrawnCardDetail,
    OrientationType,
    QuestionCategory,
    SpreadConfig,
    TarotCardSchema,
    TarotDrawRequest,
    TarotDrawResponse,
)
from app.services.tarot.cards_data import ALL_TAROT_CARDS, TAROT_DECK_BY_ID
from app.services.tarot.spreads_data import ALL_SPREADS, SPREADS_BY_ID

GRAHA_MANTRAS_I18N: dict[str, dict[str, str]] = {
    "Surya": {
        "en": "ॐ सूर्याय नमः (Om Suryaya Namaha) — Chanted for vitality, sovereign clarity, and dispelling inner doubts.",
        "bn": "ॐ सूर्याय नमः (ওঁ সূর্যায় নমঃ) — আত্মবিশ্বাস, সুস্বাস্থ্য ও সার্বভৌম সংকল্প জাগ্রত করার জন্য প্রাতঃকালে জপ করুন।",
        "hi": "ॐ सूर्याय नमः (ॐ सूर्याय नमः) — आत्मबल, यश, स्वास्थ्य और अटूट संकल्प के लिए प्रातःकाल जपें।",
    },
    "Chandra": {
        "en": "ॐ सोमाय नमः (Om Somaya Namaha) — Chanted for emotional equilibrium and intuitive receptivity.",
        "bn": "ॐ सोमाय नमः (ওঁ সোমায় নমঃ) — মানসিক প্রশান্তি, অন্তর্জ্ঞান ও সম্পর্কের পবিত্র সম্প্রীতির জন্য জপ করুন।",
        "hi": "ॐ सोमाय नमः (ॐ सोमाय नमः) — मानसिक शांति, सहज बोध और भावनात्मक संतुलन हेतु जपें।",
    },
    "Mangal": {
        "en": "ॐ अङ्गारकाय नमः (Om Angarakaya Namaha) — Chanted for righteous courage, vitality, and overcoming obstacles.",
        "bn": "ॐ अङ्गारकाय नमः (ওঁ অঙ্গারকায় নমঃ) — নির্ভীক পরাক্রম, বাধা দূরীকরণ ও কর্মে অদম্য সাফল্যের জন্য জপ করুন।",
        "hi": "ॐ अङ्गारकाय नमः (ॐ अंगारकाय नमः) — अदम्य साहस, ऊर्जा और संकट निवारण हेतु जपें।",
    },
    "Budha": {
        "en": "ॐ बुधाय नमः (Om Budhaya Namaha) — Chanted for intellect, discerning communication, and business acumen.",
        "bn": "ॐ बुधाय नमः (ওঁ বুধায় নমঃ) — প্রখর মেধা, সঠিক যোগাযোগ ও ব্যবসায়িক প্রজ্ঞার জন্য জপ করুন।",
        "hi": "ॐ बुधाय नमः (ॐ बुधाय नमः) — तीव्र बुद्धि, व्यापारिक विवेक और वाणी सिद्धि हेतु जपें।",
    },
    "Guru": {
        "en": "ॐ गुरवे नमः (Om Guruve Namaha) — Chanted for divine wisdom, spiritual expansion, and cosmic grace.",
        "bn": "ॐ गुरवे नमঃ (ওঁ গুরবে নমঃ) — পরম প্রজ্ঞা, সৌভাগ্য, আধ্যাত্মিক উত্তরণ ও ঐশ্বরিক কৃপার জন্য জপ করুন।",
        "hi": "ॐ गुरवे नमः (ॐ गुरवे नमः) — परम ज्ञान, गुरु कृपा और आध्यात्मिक समृद्धि हेतु जपें।",
    },
    "Shukra": {
        "en": "ॐ शुक्राय नमः (Om Shukraya Namaha) — Chanted for harmony, creative magnetism, and deep love.",
        "bn": "ॐ शुक्राय नमঃ (ওঁ শুক্রায় নমঃ) — প্রেম, দাম্পত্য সুখ, শিল্পকলা ও ধনৈশ্বর্য আকর্ষণের জন্য জপ করুন।",
        "hi": "ॐ शुक्राय नमः (ॐ शुक्राय नमः) — प्रेम, दांपत्य सुख, कला और आकर्षण ऊर्जा हेतु जपें।",
    },
    "Shani": {
        "en": "ॐ शं शनैश्चराय नमः (Om Sham Shanaishcharaya Namaha) — Chanted for patience, discipline, and karmic liberation.",
        "bn": "ॐ शं शनैश्चराय नमঃ (ওঁ শং শনৈশ্চরায় নমঃ) — ধৈর্য, সুবিচার, নিষ্ঠা ও অশুভ কর্মবন্ধন মুক্তির জন্য জপ করুন।",
        "hi": "ॐ शं शनैश्चराय नमः (ॐ शं शनैश्चराय नमः) — धैर्य, कर्म निष्ठा और शनि शांति हेतु जपें।",
    },
    "Rahu": {
        "en": "ॐ राहवे नमः (Om Rahave Namaha) — Chanted for dissolving illusions and mastering unconventional paths.",
        "bn": "ॐ राहवे नमঃ (ওঁ রাহবে নমঃ) — মোহ-মায়া দূরীকরণ, অন্তরের ধোঁয়াশা কাটানো ও উদ্ভাবনী শক্তির জন্য জপ করুন।",
        "hi": "ॐ राहवे नमः (ॐ राहवे नमः) — भ्रम निवारण और अप्रत्याशित सफलता हेतु जपें।",
    },
    "Ketu": {
        "en": "ॐ केतवे नमः (Om Ketave Namaha) — Chanted for spiritual detachment, deep enlightenment, and moksha.",
        "bn": "ॐ केतवे नमঃ (ওঁ কেতবে নমঃ) — মোহমুক্তি, গভীর আত্মদর্শন ও আধ্যাত্মিক মোক্ষলাভের জন্য জপ করুন।",
        "hi": "ॐ केतवे नमः (ॐ केतवे नमः) — वैराग्य, आत्मबोध और आध्यात्मिक मुक्ति हेतु जपें।",
    },
}

SPREAD_POSITIONS_I18N: dict[str, dict[str, list[dict[str, str]]]] = {
    "daily_guidance": {
        "bn": [{"title": "দৈনিক মহাজাগতিক পরিবেশ", "role": "মুখ্য শক্তি"}],
        "hi": [{"title": "दैनिक ब्रह्मांडीय ऊर्जा", "role": "प्रमुख ऊर्जा"}],
        "en": [{"title": "Daily Cosmic Atmosphere", "role": "Core Energy"}],
    },
    "past_present_future": {
        "bn": [
            {"title": "ভিত্তিপ্রস্তর (অতীত)", "role": "পরিস্থিতির অতীত উৎস ও কারণ"},
            {"title": "বর্তমান অবস্থান (বর্তমান)", "role": "বর্তমান সক্রিয় মহাজাগতিক শক্তি"},
            {"title": "সম্ভাব্য দিগন্ত (ভবিষ্যৎ)", "role": "ভবিষ্যতের অবশ্যম্ভাবী গতিপ্রবাহ"},
        ],
        "hi": [
            {"title": "मूल आधार (भूत)", "role": "अतीत का मूल कारण"},
            {"title": "वर्तमान चक्र (वर्तमान)", "role": "वर्तमान सक्रिय ऊर्जा"},
            {"title": "भावी क्षितिज (भविष्य)", "role": "भविष्य की संभावित दिशा"},
        ],
        "en": [
            {"title": "The Foundation (Past)", "role": "Root genesis & cause"},
            {"title": "The Crucible (Present)", "role": "Active energy right now"},
            {"title": "The Horizon (Future)", "role": "Projected outcome & horizon"},
        ],
    },
    "two_choices": {
        "bn": [
            {"title": "মূল অন্তর্নিহিত অবস্থা", "role": "সিদ্ধান্তের পেছনের মূল পরিস্থিতি"},
            {"title": "প্রথম পথ (বিকল্প ক)", "role": "প্রথম সিদ্ধান্তের ফলাফল ও দিক"},
            {"title": "দ্বিতীয় পথ (বিকল্প খ)", "role": "দ্বিতীয় সিদ্ধান্তের ফলাফল ও দিক"},
            {"title": "সারসংক্ষেপ ও সঠিক পরামর্শ", "role": "পরম কল্যাণকর পদক্ষেপ"},
        ],
        "hi": [
            {"title": "मूल स्थिति", "role": "निर्णय का केंद्रीय आधार"},
            {"title": "प्रथम मार्ग (विकल्प क)", "role": "पहले विकल्प का परिणाम"},
            {"title": "द्वितीय मार्ग (विकल्प ख)", "role": "दूसरे विकल्प का परिणाम"},
            {"title": "मार्गदर्शन व निष्कर्ष", "role": "सर्वश्रेष्ठ कल्याणकारी मार्ग"},
        ],
        "en": [
            {"title": "The Core Dilemma", "role": "Underlying situation"},
            {"title": "Path A: First Option", "role": "Energy of option A"},
            {"title": "Path B: Second Option", "role": "Energy of option B"},
            {"title": "The Harmonizing Factor", "role": "Higher spiritual resolution"},
        ],
    },
    "love_soulmate": {
        "bn": [
            {"title": "আপনার আন্তরিক মনোভাব", "role": "আপনার গভীরতম অনুভূতি"},
            {"title": "সঙ্গীর মানসিক অবস্থা", "role": "সঙ্গীর ভাবনা ও দৃষ্টিভঙ্গি"},
            {"title": "সম্পর্কের অভ্যন্তরীণ টান", "role": "পারস্পরিক বন্ধনের প্রকৃতি"},
            {"title": "লুকানো অন্তরায়", "role": "যেখানে সতর্ক থাকা প্রয়োজন"},
            {"title": "মিলন ও ভবিষ্যৎ ঐক্য", "role": "সম্পর্কের পরম সম্ভাবনা"},
        ],
        "hi": [
            {"title": "आपकी आंतरिक भावनाएं", "role": "हृदय की सच्ची स्थिति"},
            {"title": "साथी का दृष्टिकोण", "role": "साथी की मानसिक स्थिति"},
            {"title": "संबंधों की अंतर्धारा", "role": "आपसी ऊर्जा व जुड़ाव"},
            {"title": "गुप्त चुनौती", "role": "सावधानी का मुख्य बिंदु"},
            {"title": "भविष्य का मिलन", "role": "संबंधों की परम दिशा"},
        ],
        "en": [
            {"title": "Your True Emotional Energy", "role": "Your subconscious feeling"},
            {"title": "Partner's Perception & Energy", "role": "Their thoughts & state"},
            {"title": "The Relationship Crucible", "role": "Dynamics of the bond"},
            {"title": "The Hidden Blockage", "role": "Vulnerability to heal"},
            {"title": "The Higher Destiny", "role": "Potential union & future"},
        ],
    },
    "career_wealth": {
        "bn": [
            {"title": "বর্তমান পেশাগত স্থিতি", "role": "আপনার বর্তমান কর্মক্ষেত্রের শক্তি ও অবস্থান"},
            {"title": "অপ্রকাশিত সুযোগ ও সম্পদ", "role": "লুকানো সম্ভাবনা ও সহায়ক শক্তি"},
            {"title": "কর্মক্ষেত্রের মূল অন্তরায়", "role": "যেখানে সতর্ক থাকা অত্যন্ত জরুরি"},
            {"title": "কৌশলগত কার্যকরী পদক্ষেপ", "role": "সাফল্য নিশ্চিত করার নির্ভুল পদক্ষেপ"},
            {"title": "চূড়ান্ত ফল ও সমৃদ্ধি", "role": "অর্থনৈতিক ও পেশাগত উজ্জ্বল ভবিষ্যৎ"},
        ],
        "hi": [
            {"title": "वर्तमान कार्य स्थिति", "role": "आपकी वर्तमान व्यावसायिक ऊर्जा"},
            {"title": "अप्रत्याशित धन अवसर", "role": "छिपी हुई संभावनाएं व शक्ति"},
            {"title": "कार्यक्षेत्र की मुख्य बाधा", "role": "सावधानी का मुख्य केंद्र"},
            {"title": "सटीक रणनीतिक कदम", "role": "सफलता का अचूक मार्ग"},
            {"title": "अंतिम उपलब्धि व समृद्धि", "role": "आर्थिक व करियर उन्नति"},
        ],
        "en": [
            {"title": "Current Professional Stance", "role": "Current career standing & authority"},
            {"title": "Hidden Asset & Opportunity", "role": "Unseen talent or advantage"},
            {"title": "The Career Obstacle", "role": "Obstacle requiring vigilance"},
            {"title": "The Strategic Action", "role": "Bold move to shift momentum"},
            {"title": "Financial & Career Harvest", "role": "Long-term reward & authority"},
        ],
    },
    "celtic_cross": {
        "bn": [
            {"title": "১. বর্তমান সার্বিক অবস্থা", "role": "জীবনের মূল কেন্দ্রবিন্দু"},
            {"title": "২. তাৎক্ষণিক বাধা বা চ্যালেঞ্জ", "role": "সরাসরি মুখোমুখি হওয়া শক্তি"},
            {"title": "৩. দূরবর্তী অতীত উৎস", "role": "সমস্যার প্রাচীন ভিত্তি"},
            {"title": "৪. সাম্প্রতিক অতীতের প্রভাব", "role": "যে শক্তির প্রভাব কমছে"},
            {"title": "৫. সর্বোচ্চ প্রাপ্তি ও উচ্চাকাঙ্ক্ষা", "role": "আপনার চেতনার চূড়া"},
            {"title": "৬. নিকট ভবিষ্যৎ দিগন্ত", "role": "আসন্ন কয়েক সপ্তাহের প্রবাহ"},
            {"title": "৭. নিজস্ব মনোভাব ও শক্তি", "role": "আপনার আত্মবিশ্বাস ও ক্ষমতা"},
            {"title": "৮. পরিবেশ ও পারিপার্শ্বিক প্রভাব", "role": "অন্যদের মতামত ও সহায়তা"},
            {"title": "৯. অন্তরের আশা ও ভীতি", "role": "মনস্তাত্ত্বিক প্রত্যাশা"},
            {"title": "১০. চূড়ান্ত কার্মিক পরিণতি", "role": "মহাজাগতিক চূড়ান্ত ফল"},
        ],
        "hi": [
            {"title": "1. वर्तमान स्थिति", "role": "जीवन का मुख्य केंद्र"},
            {"title": "2. तात्कालिक चुनौती", "role": "सीधा अवरोध"},
            {"title": "3. सुदूर अतीत", "role": "प्राचीन जड़ें"},
            {"title": "4. हाल का अतीत", "role": "समाप्त होती ऊर्जा"},
            {"title": "5. सर्वोच्च लक्ष्य", "role": "उच्चतम संभावना"},
            {"title": "6. निकट भविष्य", "role": "आगामी कुछ सप्ताह"},
            {"title": "7. आपका आत्मबल", "role": "आपकी आंतरिक शक्ति"},
            {"title": "8. परिवेशीय प्रभाव", "role": "बाहरी सहयोग व माहौल"},
            {"title": "9. आशाएं व भय", "role": "मनोवैज्ञानिक अपेक्षाएं"},
            {"title": "10. अंतिम परिणाम", "role": "ब्रह्मांडीय अंतिम फल"},
        ],
        "en": [
            {"title": "1. The Present Stance", "role": "The central core energy"},
            {"title": "2. Immediate Challenge", "role": "Cross & obstacle"},
            {"title": "3. The Distant Past", "role": "Root foundation"},
            {"title": "4. The Recent Past", "role": "Receding influence"},
            {"title": "5. Highest Potential", "role": "Crown of aspiration"},
            {"title": "6. The Immediate Future", "role": "Upcoming horizon"},
            {"title": "7. The Self & Attitude", "role": "Your personal agency"},
            {"title": "8. External Environment", "role": "Surrounding influences"},
            {"title": "9. Hopes and Fears", "role": "Psychological driver"},
            {"title": "10. Karmic Culmination", "role": "Final divine outcome"},
        ],
    },
}

ELEMENT_NAMES_I18N: dict[str, dict[str, str]] = {
    "Fire": {"en": "Fire", "bn": "অগ্নি (তেজ)", "hi": "अग्नि तत्व"},
    "Water": {"en": "Water", "bn": "জল (আপঃ)", "hi": "जल तत्व"},
    "Air": {"en": "Air", "bn": "বায়ু (মরুৎ)", "hi": "वायु तत्व"},
    "Earth": {"en": "Earth", "bn": "পৃথিবী (ক্ষিতি)", "hi": "पृथ्वी तत्व"},
    "Spirit": {"en": "Spirit", "bn": "ব্যোম (আকাশ)", "hi": "आकाश तत्व"},
}

SPREAD_NAMES_I18N: dict[str, dict[str, str]] = {
    "daily_guidance": {"en": "Card of the Day", "bn": "আজকের নির্দেশক কার্ড", "hi": "आज का प्रेरक कार्ड"},
    "past_present_future": {"en": "Past – Present – Future", "bn": "অতীত – বর্তমান – ভবিষ্যৎ", "hi": "भूत – वर्तमान – भविष्य"},
    "two_choices": {"en": "Two Choices Crossroad", "bn": "দ্বিধা ও দুই পথ স্প্রেড", "hi": "दो विकल्प चौराहा"},
    "love_soulmate": {"en": "Love & Soulmate Mirror", "bn": "প্রেম ও জীবনসঙ্গী দর্পণ", "hi": "प्रेम व जीवनसाथी दर्पण"},
    "career_wealth": {"en": "Career & Wealth Pathway", "bn": "কর্মজীবন ও ধনসম্পদ পথ", "hi": "करियर व धन मार्ग"},
    "celtic_cross": {"en": "The Grand Celtic Cross", "bn": "১০-কার্ড সেল্টিক ক্রস স্প্রেড", "hi": "10-कार्ड सेल्टिक क्रॉस स्प्रेड"},
}

ELEMENT_RELATIONSHIPS: dict[str, dict[str, str]] = {
    "Fire": {
        "Fire": "Intensifying — dynamic passion and rapid catalytic expansion.",
        "Air": "Complementary & Fueling — thoughts instantly ignite inspired action.",
        "Water": "Volatile / Steamy — emotional depth challenges impulsive will.",
        "Earth": "Grounding — stabilizes creative vision into tangible reality.",
        "Spirit": "Divine Spark — transcendent inspiration and soul realization.",
    },
    "Water": {
        "Water": "Deepening — profound emotional resonance and psychic attunement.",
        "Earth": "Fertile & Harmonious — feelings find safety, structure, and nurture.",
        "Air": "Misty — analytical intellect meets intuitive emotion.",
        "Fire": "Steam & Friction — inner tension demanding emotional maturity.",
        "Spirit": "Oceanic Oneness — deep mystical surrender and cosmic compassion.",
    },
    "Air": {
        "Air": "Hyper-intellectual — razor-sharp ideas, needs grounding in physical deed.",
        "Fire": "Dynamic Harmony — visionary ideals find explosive execution.",
        "Earth": "Contrasting — abstract strategy anchored by pragmatic facts.",
        "Water": "Diffusing — intellectual processing of emotional tides.",
        "Spirit": "Cosmic Illumination — mind tuning into divine universal truth.",
    },
    "Earth": {
        "Earth": "Solid & Enduring — immovable foundation, caution against stagnation.",
        "Water": "Flourishing & Nourishing — wealth and emotional growth take root.",
        "Fire": "Tempering — fiery passion is channeled into disciplined craft.",
        "Air": "Pragmatic balance — ideas are rigorously tested against reality.",
        "Spirit": "Sacred Incarnation — spirit materializing into righteous form.",
    },
    "Spirit": {
        "Fire": "Divine Illumination",
        "Water": "Mystic Oceanic Grace",
        "Air": "Transcendent Wisdom",
        "Earth": "Sacred Embodiment",
        "Spirit": "Pure Cosmic Transcendence",
    },
}


def get_all_cards(arcana: str | None = None, suit: str | None = None) -> list[TarotCardSchema]:
    """Return all cards or filtered subset."""
    results = []
    for card_data in ALL_TAROT_CARDS:
        if arcana and card_data.get("arcana") != arcana:
            continue
        if suit and card_data.get("suit") != suit:
            continue
        results.append(TarotCardSchema(**card_data))
    return results


def get_card_by_id(card_id: str) -> TarotCardSchema | None:
    """Return a single card by its ID."""
    card_data = TAROT_DECK_BY_ID.get(card_id)
    if not card_data:
        return None
    return TarotCardSchema(**card_data)


def get_all_spreads() -> list[SpreadConfig]:
    """Return all supported spread configurations."""
    return [SpreadConfig(**s) for s in ALL_SPREADS]


def get_spread_by_id(spread_id: str) -> SpreadConfig | None:
    """Return spread configuration by ID."""
    s = SPREADS_BY_ID.get(spread_id)
    if not s:
        return None
    return SpreadConfig(**s)


def _compute_card_weights(
    cards: list[dict[str, Any]],
    user_moon_sign: str | None,
    active_dasha_lord: str | None,
    category: QuestionCategory,
) -> list[float]:
    """Calculate resonance weights for each card based on astrological factors."""
    weights: list[float] = []
    for c in cards:
        w = 1.0
        if user_moon_sign and c.get("astrology"):
            if user_moon_sign.lower() in c["astrology"].lower():
                w += 0.8
        if active_dasha_lord and c.get("vedic_graha"):
            if active_dasha_lord.lower() in c["vedic_graha"].lower():
                w += 1.0

        suit = c.get("suit")
        if category == "love" and suit == "cups":
            w += 0.3
        elif category == "career" and suit == "wands":
            w += 0.3
        elif category == "finance" and suit == "pentacles":
            w += 0.3
        elif category == "spiritual" and (c.get("arcana") == "major" or suit == "cups"):
            w += 0.4

        weights.append(w)
    return weights


def _calculate_timing_and_verdict(
    drawn_cards: list[DrawnCardDetail],
    dominant_elem: str,
    lang: str,
    category: str,
) -> tuple[str, str, int, str, str, dict[str, Any]]:
    """Calculate precise timing window, divine verdict score, astrological day/color, and master course breakdown."""
    upright_count = sum(1 for c in drawn_cards if c.orientation == "upright")
    total = len(drawn_cards)
    ratio = upright_count / total if total > 0 else 0.5

    base_score = int(60 + (ratio * 35))
    if base_score > 96:
        base_score = 96
    elif base_score < 55:
        base_score = 55

    last_card_detail = drawn_cards[-1]
    last_card = last_card_detail.card
    last_orientation = last_card_detail.orientation

    card_speed = last_card.timing_speed or "Days to Weeks"
    card_season = last_card.timing_season or "Spring"
    card_window = last_card.timing_window or "Upcoming Solar Cycle"
    card_yes_no = last_card.yes_no or "YES"
    if last_orientation == "reversed":
        effective_yes_no = "NO / Caution (Reversed)"
    else:
        effective_yes_no = card_yes_no

    timing_breakdown = {
        "speed": card_speed,
        "season": card_season,
        "window": card_window,
        "verdict_card": last_card.name,
        "orientation": last_orientation,
        "card_yes_no": effective_yes_no,
    }

    if lang == "bn":
        timeframe = f"প্রকাশের গতি: {card_speed} | ঋতু: {card_season} | মহাজাগতিক কাল: {card_window}"
        if "NO" in effective_yes_no.upper():
            verdict = f"সতর্কতা / না ({effective_yes_no}) — অনুকূল সম্ভাবনা: {base_score}%"
        elif "MAYBE" in effective_yes_no.upper():
            verdict = f"সম্ভাব্য কিন্তু শর্তসাপেক্ষ ({effective_yes_no}) — সম্ভাবনা: {base_score}%"
        else:
            verdict = f"অত্যন্ত শুভ ও অনুকূল সংকেত (হাঁ / {effective_yes_no}) — সম্ভাবনা: {base_score}%"

        graha_colors_bn = {
            "Surya": ("রবিবার", "সোনালী / প্রদীপ্ত লাল"),
            "Chandra": ("সোমবার", "দুধসাদা / রূপালী"),
            "Mangal": ("মঙ্গলবার", "উজ্জ্বল রক্তিম / প্রবাল"),
            "Budha": ("বুধবার", "পান্না সবুজ"),
            "Guru": ("বৃহস্পতিবার", "উজ্জ্বল হলুদ / কাঁচা সোনা"),
            "Shukra": ("শুক্রবার", "সিল্ক হোয়াইট / হালকা গোলাপী"),
            "Shani": ("শনিবার", "গাঢ় নীল / আসমানি"),
            "Rahu": ("শনিবার", "ধূসর / গাঢ় বাদামী"),
            "Ketu": ("মঙ্গলবার", "বহুবর্ণ / গৈরিক"),
        }
        lead_graha = drawn_cards[0].card.vedic_graha
        day, color = graha_colors_bn.get(lead_graha, ("বৃহস্পতিবার", "সোনালী হলুদ"))

    elif lang == "hi":
        timeframe = f"फल प्राप्ति गति: {card_speed} | ऋतु: {card_season} | ब्रह्मांडीय काल: {card_window}"
        if "NO" in effective_yes_no.upper():
            verdict = f"सावधानी / नहीं ({effective_yes_no}) — संभावना: {base_score}%"
        elif "MAYBE" in effective_yes_no.upper():
            verdict = f"संभावित / विचारणीय ({effective_yes_no}) — संभावना: {base_score}%"
        else:
            verdict = f"अत्यंत शुभ व सकारात्मक (हाँ / {effective_yes_no}) — संभावना: {base_score}%"

        graha_colors_hi = {
            "Surya": ("रविवार", "सुनहरा / लाल"),
            "Chandra": ("सोमवार", "सफेद / चांदी"),
            "Mangal": ("मंगलवार", "लाल / मूंगा"),
            "Budha": ("बुधवार", "पन्ना हरा"),
            "Guru": ("गुरुवार", "पीला / सुनहरा"),
            "Shukra": ("शुक्रवार", "चमकीला सफेद / गुलाबी"),
            "Shani": ("शनिवार", "गहरा नीला / काला"),
            "Rahu": ("शनिवार", "धूम्र वर्ण"),
            "Ketu": ("मंगलवार", "चितकबरा / पीला"),
        }
        lead_graha = drawn_cards[0].card.vedic_graha
        day, color = graha_colors_hi.get(lead_graha, ("गुरुवार", "पीला सुनहरा"))

    else:
        timeframe = f"{card_speed} | Season: {card_season} | Window: {card_window}"
        if "NO" in effective_yes_no.upper():
            verdict = f"Caution / NO ({effective_yes_no}) — {base_score}% Alignment"
        elif "MAYBE" in effective_yes_no.upper():
            verdict = f"Conditional / MAYBE ({effective_yes_no}) — {base_score}% Alignment"
        else:
            verdict = f"Strongly Favorable / YES ({effective_yes_no}) — {base_score}% Alignment"

        graha_colors_en = {
            "Surya": ("Sunday", "Golden Yellow / Sunburst Orange"),
            "Chandra": ("Monday", "Pearl White / Lunar Silver"),
            "Mangal": ("Tuesday", "Crimson Red / Coral"),
            "Budha": ("Wednesday", "Emerald Green"),
            "Guru": ("Thursday", "Royal Yellow / Radiant Gold"),
            "Shukra": ("Friday", "Diamond White / Rose Pink"),
            "Shani": ("Saturday", "Sapphire Navy / Charcoal"),
            "Rahu": ("Saturday", "Smoky Topaz / Slate"),
            "Ketu": ("Tuesday", "Ochre / Variegated Gold"),
        }
        lead_graha = drawn_cards[0].card.vedic_graha
        day, color = graha_colors_en.get(lead_graha, ("Thursday", "Royal Gold"))

    return timeframe, verdict, base_score, day, color, timing_breakdown


def draw_tarot_spread(request: TarotDrawRequest) -> TarotDrawResponse:
    """Perform a comprehensive tarot draw with multilingual synthesis and timing predictions."""
    lang = request.language or "en"
    spread_data = SPREADS_BY_ID.get(request.spread_id)
    if not spread_data:
        spread_data = SPREADS_BY_ID["past_present_future"]

    card_count = spread_data["card_count"]
    positions = spread_data["positions"]

    # Localized position lookups
    localized_pos_list = SPREAD_POSITIONS_I18N.get(spread_data["id"], {}).get(lang, [])

    rng = random.Random()
    if request.intention_seed is not None:
        rng.seed(request.intention_seed)

    deck = ALL_TAROT_CARDS
    deck_size = len(deck)

    selected_indices: list[int] = []
    if request.selected_indices and len(request.selected_indices) > 0:
        seen = set()
        for idx in request.selected_indices:
            if 0 <= idx < deck_size and idx not in seen:
                selected_indices.append(idx)
                seen.add(idx)
                if len(selected_indices) >= card_count:
                    break

    if len(selected_indices) < card_count:
        remaining_indices = [i for i in range(deck_size) if i not in selected_indices]
        weights = _compute_card_weights(
            [deck[i] for i in remaining_indices],
            request.user_moon_sign,
            request.active_dasha_lord,
            request.category,
        )
        needed = card_count - len(selected_indices)

        cur_pool = list(remaining_indices)
        cur_weights = list(weights)
        for _ in range(needed):
            if not cur_pool:
                break
            chosen = rng.choices(cur_pool, weights=cur_weights, k=1)[0]
            selected_indices.append(chosen)
            idx_in_pool = cur_pool.index(chosen)
            cur_pool.pop(idx_in_pool)
            cur_weights.pop(idx_in_pool)

    drawn_cards_details: list[DrawnCardDetail] = []
    element_counts: dict[str, int] = {"Fire": 0, "Water": 0, "Air": 0, "Earth": 0, "Spirit": 0}
    grahas_present: list[str] = []
    major_arcana_count = 0

    for pos_idx, card_idx in enumerate(selected_indices):
        raw_card = deck[card_idx]
        pos_raw = positions[pos_idx] if pos_idx < len(positions) else {
            "index": pos_idx + 1,
            "title": f"Position {pos_idx + 1}",
            "role": "insight",
            "description": "Cosmic perspective",
        }

        # Human-friendly localized position title and role
        if pos_idx < len(localized_pos_list):
            loc_p = localized_pos_list[pos_idx]
            pos_title = loc_p["title"]
            pos_role = loc_p["role"]
        else:
            pos_title = pos_raw["title"]
            pos_role = pos_raw["description"]

        is_reversed = rng.random() < 0.28
        orientation: OrientationType = "reversed" if is_reversed else "upright"

        interp_data = raw_card["reversed"] if is_reversed else raw_card["upright"]
        cat_key = request.category if request.category in interp_data else "general"
        relevant_interp = interp_data.get(cat_key, interp_data.get("general", ""))

        elem = raw_card.get("element", "Spirit")
        element_counts[elem] = element_counts.get(elem, 0) + 1

        if raw_card.get("arcana") == "major":
            major_arcana_count += 1

        graha = raw_card.get("vedic_graha")
        if graha and graha not in grahas_present:
            grahas_present.append(graha)

        card_name = raw_card["name"]
        if lang == "bn":
            advice = (
                f"{card_name}-এর জাগ্রত শক্তিকে গ্রহণ করুন এবং আপনার কর্মে প্রতিফলিত করুন।"
                if orientation == "upright"
                else f"{card_name}-এর উল্টো শক্তির কারণে ভেতরের দ্বিধা ও বাধা দূর করে আত্মশুদ্ধি বজায় রাখুন।"
            )
        elif lang == "hi":
            advice = (
                f"{card_name} की सकारात्मक ऊर्जा को अपनाएं और कर्म में उतारें।"
                if orientation == "upright"
                else f"{card_name} की उल्टी स्थिति में आंतरिक संशय और नकारात्मकता को दूर करें।"
            )
        else:
            advice = (
                f"Embrace the expansive power of {card_name}. Channel its authentic virtues into your life."
                if orientation == "upright"
                else f"Be mindful of inner resistance regarding {card_name}. Clear blockages to restore equilibrium."
            )

        card_schema = TarotCardSchema(**raw_card)

        drawn_cards_details.append(
            DrawnCardDetail(
                position_index=pos_raw["index"],
                position_title=pos_title,
                position_role=pos_role,
                position_description=pos_raw["description"],
                card=card_schema,
                orientation=orientation,
                relevant_interpretation=relevant_interp,
                keywords=interp_data.get("keywords", []),
                advice=advice,
                numerology=card_schema.numerology,
                timing_window=card_schema.timing_window,
                timing_season=card_schema.timing_season,
                timing_speed=card_schema.timing_speed,
                yes_no=card_schema.yes_no if orientation == "upright" else "NO Card (Reversed)",
                one_liner=card_schema.one_liner,
                symbols=card_schema.symbols,
                professions=card_schema.professions,
            )
        )

    for i in range(len(drawn_cards_details)):
        curr_elem = drawn_cards_details[i].card.element
        if i + 1 < len(drawn_cards_details):
            next_elem = drawn_cards_details[i + 1].card.element
            rel = ELEMENT_RELATIONSHIPS.get(curr_elem, {}).get(next_elem, "Neutral celestial balance.")
            drawn_cards_details[i].elemental_harmony = f"Dynamic with next card ({next_elem}): {rel}"
        elif len(drawn_cards_details) > 1:
            prev_elem = drawn_cards_details[i - 1].card.element
            rel = ELEMENT_RELATIONSHIPS.get(curr_elem, {}).get(prev_elem, "Neutral celestial balance.")
            drawn_cards_details[i].elemental_harmony = f"Rooted in preceding card ({prev_elem}): {rel}"

    dominant_elem = max(element_counts, key=lambda k: element_counts[k])
    dominant_elem_loc = ELEMENT_NAMES_I18N.get(dominant_elem, {}).get(lang, dominant_elem)

    major_ratio = round((major_arcana_count / card_count) * 100)
    if lang == "bn":
        if major_ratio >= 60:
            karmic_momentum = "তীব্র কার্মিক প্রভাব — পরিস্থিতি মূলত পূর্বনির্ধারিত ভাগ্য ও মহাজাগতিক নিয়মের অধীন।"
        elif major_ratio >= 30:
            karmic_momentum = "ভারসাম্যপূর্ণ কার্মিক ও বৈষয়িক গতি — ব্যক্তিগত কর্ম ও ভাগ্যের প্রভাব সমানভাবে সক্রিয়।"
        else:
            karmic_momentum = "উচ্চ ব্যক্তিগত নিয়ন্ত্রণ — আপনার তাৎক্ষণিক সিদ্ধান্ত ও বুদ্ধিমত্তা বর্তমান ফলাফল নির্ধারণ করবে।"
    elif lang == "hi":
        if major_ratio >= 60:
            karmic_momentum = "प्रबल कार्मिक प्रभाव — परिस्थितियां ब्रह्मांडीय प्रारब्ध द्वारा संचालित हैं।"
        elif major_ratio >= 30:
            karmic_momentum = "संतुलित कर्म व प्रारब्ध — व्यक्तिगत निर्णय और भाग्य समान रूप से प्रभावी हैं।"
        else:
            karmic_momentum = "व्यक्तिगत कर्म प्रधान — आपके वर्तमान विवेक और प्रयासों से ही दिशा तय होगी।"
    else:
        if major_ratio >= 60:
            karmic_momentum = "High Karmic Destiny — Events are governed by destiny and cosmic cycles."
        elif major_ratio >= 30:
            karmic_momentum = "Balanced Karmic & Mundane Flow — Personal choices and fate share equal influence."
        else:
            karmic_momentum = "High Personal Agency — Day-to-day decisions and immediate efforts guide outcomes."

    astrological_resonance = {
        "major_arcana_percentage": major_ratio,
        "karmic_momentum": karmic_momentum,
        "active_grahas": grahas_present,
        "dominant_element": dominant_elem,
        "aligned_with_user_moon": bool(request.user_moon_sign),
        "aligned_with_active_dasha": bool(request.active_dasha_lord),
    }

    # High-precision Timing Window and Verdict adhering to Tarot Master Course
    timeframe, verdict, score, auspicious_day, auspicious_color, timing_breakdown = _calculate_timing_and_verdict(
        drawn_cards_details, dominant_elem, lang, request.category
    )

    first_card = drawn_cards_details[0]
    lead_name = f"{first_card.card.name} ({first_card.orientation})"

    # Detect user intent from question (e.g. Job, Love, Marriage)
    q_lower = (request.question or "").lower()
    is_job_query = any(k in q_lower for k in ["job", "chakri", "kobe", "career", "interview", "চাকরি", "পাবো"])

    if lang == "bn":
        spread_display_name = SPREAD_NAMES_I18N.get(spread_data["id"], {}).get("bn", spread_data["name"])
        orient_bn = "জাগ্রত শক্তি" if first_card.orientation == "upright" else "অন্তর্মুখী রূপান্তর"

        job_prefix = ""
        if is_job_query:
            job_prefix = f"আপনার কর্মপ্রাপ্তি এবং জীবিকার ভবিষ্যৎ সম্পর্কে এই স্প্রেড সুস্পষ্ট ইতিবাচক সংকেত বহন করছে। "

        if len(drawn_cards_details) == 1:
            synthesis = (
                f"{job_prefix}আজকের দিনে আপনার মুখ্য মহাজাগতিক স্পটলাইট পড়েছে {first_card.card.name} ({orient_bn})-এর ওপর। "
                f"আপনার {first_card.position_title} অবস্থান অনুযায়ী: {first_card.relevant_interpretation} "
                f"প্রধান উপাদান '{dominant_elem_loc}' নির্দেশ করে যে প্রত্যাশিত ফলপ্রাপ্তির সম্ভাব্য সময়: {timeframe}।"
            )
        elif len(drawn_cards_details) == 3:
            p_c = drawn_cards_details[0]
            pr_c = drawn_cards_details[1]
            f_c = drawn_cards_details[2]
            synthesis = (
                f"{job_prefix}আপনার অতীত ভিত্তিপ্রস্তর উন্মোচিত হয়েছে {p_c.card.name} ({p_c.orientation})-এর মাধ্যমে: {p_c.relevant_interpretation} "
                f"বর্তমানে পরিস্থিতির কেন্দ্রে অবস্থান করছে {pr_c.card.name} ({pr_c.orientation}): {pr_c.relevant_interpretation} "
                f"এবং আগামী দিনে ঘটনার গতিপ্রবাহ পরিচালিত হবে {f_c.card.name} ({f_c.orientation})-এর নির্দেশনায়: {f_c.relevant_interpretation} "
                f"ফলাফল প্রকাশের প্রত্যাশিত সময়কাল: {timeframe}।"
            )
        else:
            cards_summary = ", ".join(f"{c.position_title}: {c.card.name}" for c in drawn_cards_details[:3])
            synthesis = (
                f"{job_prefix}এই গভীর মহাজাগতিক স্প্রেডের মূল চক্র আবর্তিত হচ্ছে {cards_summary}-এর মাধ্যমে। "
                f"প্রধান উপাদান '{dominant_elem_loc}' এবং {karmic_momentum} "
                f"নির্দেশ করছে যে আপনার {request.category} ক্ষেত্রে সঠিক পরিকল্পনা ও একাগ্রতা থাকলে নিশ্চিত সাফল্য আসবে। "
                f"মূল শিক্ষা: {first_card.relevant_interpretation}। "
                f"প্রত্যাশিত সময়সীমা: {timeframe}।"
            )

        last_c = drawn_cards_details[-1]
        actionable_guidance = (
            f"{first_card.card.name}-এর সর্বোচ্চ সম্ভাবনাকে নিজের কর্মে রূপায়িত করুন। "
            f"{last_c.card.name}-সংক্রান্ত কোনো ক্ষণস্থায়ী ভীতি বা উত্তেজনায় হঠকারী সিদ্ধান্ত এড়িয়ে চলুন। "
            f"'{dominant_elem_loc}' উপাদানের শান্ত গুণাবলি ধারণ করলে আগামী সময়ে আপনার সার্বিক স্থিতি বজায় থাকবে।"
        )

    elif lang == "hi":
        spread_display_name = SPREAD_NAMES_I18N.get(spread_data["id"], {}).get("hi", spread_data["name"])
        orient_hi = "सीधी स्थिति" if first_card.orientation == "upright" else "उल्टी स्थिति"

        if len(drawn_cards_details) == 1:
            synthesis = (
                f"आज के दिन आपका मुख्य ब्रह्मांडीय ध्यान {first_card.card.name} ({orient_hi}) पर केंद्रित है। "
                f"यह कार्ड संकेत देता है: {first_card.relevant_interpretation} "
                f"प्रमुख तत्व '{dominant_elem_loc}' के अनुसार अपेक्षित समय सीमा: {timeframe}।"
            )
        elif len(drawn_cards_details) == 3:
            p_c = drawn_cards_details[0]
            pr_c = drawn_cards_details[1]
            f_c = drawn_cards_details[2]
            synthesis = (
                f"आपकी स्थिति का मूल आधार {p_c.card.name} ({p_c.orientation}) से प्रकट होता है: {p_c.relevant_interpretation} "
                f"वर्तमान में घटनाक्रम के केंद्र में {pr_c.card.name} ({pr_c.orientation}) स्थित है: {pr_c.relevant_interpretation} "
                f"तथा भविष्य की दिशा {f_c.card.name} ({f_c.orientation}) द्वारा प्रशस्त होगी: {f_c.relevant_interpretation} "
                f"अपेक्षित समय काल: {timeframe}।"
            )
        else:
            cards_summary = ", ".join(f"{c.position_title}: {c.card.name}" for c in drawn_cards_details[:3])
            synthesis = (
                f"इस दिव्य स्प्रेड का मुख्य आधार {cards_summary} द्वारा संचालित है। "
                f"प्रमुख तत्व '{dominant_elem_loc}' एवं {karmic_momentum} "
                f"बताते हैं कि आपके {request.category} क्षेत्र में विवेकपूर्ण निर्णय आवश्यक हैं। "
                f"मुख्य संदेश: {first_card.relevant_interpretation}। "
                f"अपेक्षित समयावधि: {timeframe}।"
            )

        last_c = drawn_cards_details[-1]
        actionable_guidance = (
            f"{first_card.card.name} के सकारात्मक प्रभाव को जीवन में उतारें। "
            f"{last_c.card.name} से संबंधित किसी भी जल्दबाजी या भय से बचें। "
            f"'{dominant_elem_loc}' का संतुलन बनाए रखने से मनोवांछित स्थिरता प्राप्त होगी।"
        )

    else:
        spread_display_name = spread_data["name"]
        job_prefix = "Regarding your career and vocational breakthrough, this spread reveals clear momentum. " if is_job_query else ""

        if len(drawn_cards_details) == 1:
            synthesis = (
                f"{job_prefix}The cosmic spotlight falls squarely upon {lead_name}. "
                f"As your {first_card.position_title}, this presence indicates that {first_card.relevant_interpretation} "
                f"The primary element of {dominant_elem} indicates expected culmination: {timeframe}."
            )
        elif len(drawn_cards_details) == 3:
            past_card = drawn_cards_details[0]
            pres_card = drawn_cards_details[1]
            fut_card = drawn_cards_details[2]
            synthesis = (
                f"{job_prefix}Your timeline unfolds from the energetic genesis of {past_card.card.name} ({past_card.orientation}): {past_card.relevant_interpretation} "
                f"Presently, {pres_card.card.name} ({pres_card.orientation}) stands at the vortex: {pres_card.relevant_interpretation} "
                f"The forward trajectory crystallizes through {fut_card.card.name} ({fut_card.orientation}): {fut_card.relevant_interpretation} "
                f"Predicted Manifestation Window: {timeframe}."
            )
        else:
            key_cards_summary = ", ".join(f"{c.position_title}: {c.card.name}" for c in drawn_cards_details[:3])
            synthesis = (
                f"{job_prefix}This profound spread anchors through {key_cards_summary}. "
                f"The dominant elemental frequency of {dominant_elem} combined with {karmic_momentum.lower()} "
                f"calls for unwavering discernment in your {request.category} affairs. "
                f"Core takeaway: {first_card.relevant_interpretation} "
                f"Expected Window of Culmination: {timeframe}."
            )

        primary_challenge_card = drawn_cards_details[-1]
        actionable_guidance = (
            f"Focus your immediate efforts on grounding the highest vibrational expression of {first_card.card.name}. "
            f"Avoid haste or reactive fear regarding {primary_challenge_card.card.name} ({primary_challenge_card.orientation}). "
            f"Meditation on {dominant_elem.lower()} qualities will provide strategic equilibrium over the next lunar cycle."
        )

    chosen_card_for_remedy = next((c.card for c in drawn_cards_details if c.card.arcana == "major"), drawn_cards_details[-1].card)
    prescribed_remedy = chosen_card_for_remedy.remedy
    chosen_graha = chosen_card_for_remedy.vedic_graha

    graha_mantra_dict = GRAHA_MANTRAS_I18N.get(chosen_graha, {})
    vedic_mantra = graha_mantra_dict.get(
        lang,
        graha_mantra_dict.get(
            "en",
            "ॐ नमः शिवाय (Om Namah Shivaya) — Master mantra for universal peace, protection, and psychic purification.",
        ),
    )

    draw_id = uuid.uuid4().hex[:12]
    now_iso = datetime.now(timezone.utc).isoformat()

    return TarotDrawResponse(
        draw_id=draw_id,
        timestamp=now_iso,
        spread_id=spread_data["id"],
        spread_name=spread_display_name,
        category=request.category,
        language=lang,
        question=request.question,
        drawn_cards=drawn_cards_details,
        elemental_breakdown=element_counts,
        dominant_element=dominant_elem,
        astrological_resonance=astrological_resonance,
        karmic_synthesis=synthesis,
        actionable_guidance=actionable_guidance,
        prescribed_remedy=prescribed_remedy,
        vedic_mantra=vedic_mantra,
        predicted_timeframe=timeframe,
        divine_verdict=verdict,
        timing_breakdown=timing_breakdown,
        favorable_score=score,
        auspicious_day=auspicious_day,
        auspicious_color=auspicious_color,
    )


def get_daily_tarot_card(request: DailyTarotRequest) -> TarotDrawResponse:
    """Return deterministic Daily Card for today or requested date with language support."""
    target_date = request.date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lang = request.language or "en"

    seed_key = f"daily_tarot:{target_date}:{request.moon_sign or 'universal'}:{request.category}:{lang}"
    int_seed = int(hashlib.sha256(seed_key.encode("utf-8")).hexdigest()[:8], 16)

    draw_req = TarotDrawRequest(
        spread_id="daily_guidance",
        category=request.category,
        language=lang,
        question=f"Divine Guidance for {target_date}",
        user_moon_sign=request.moon_sign,
        intention_seed=int_seed,
    )

    return draw_tarot_spread(draw_req)
