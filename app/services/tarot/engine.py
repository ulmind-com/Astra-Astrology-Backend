"""Chrono-Astrological Tarot Engine (CATE).

Implements world-class 78-card Tarot reading engine with:
- Canonical Major and Minor Arcana symbolism
- Astrological (Zodiac/Planetary) and Vedic Graha resonance
- Elemental Dignities & Harmonic balance calculation
- Multi-pillar interpretations (General, Love, Career, Finance, Spiritual)
- Trilingual synthesis: English, Bengali (বাংলা), Hindi (हिन्दी)
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
        "bn": "ॐ गुरवे नमः (ওঁ গুরবে নমঃ) — পরম প্রজ্ঞা, সৌভাগ্য, আধ্যাত্মিক উত্তরণ ও ঐশ্বরিক কৃপার জন্য জপ করুন।",
        "hi": "ॐ गुरवे नमः (ॐ गुरवे नमः) — परम ज्ञान, गुरु कृपा और आध्यात्मिक समृद्धि हेतु जपें।",
    },
    "Shukra": {
        "en": "ॐ शुक्राय नमः (Om Shukraya Namaha) — Chanted for harmony, creative magnetism, and deep love.",
        "bn": "ॐ शुक्राय नमः (ওঁ শুক্রায় নমঃ) — প্রেম, দাম্পত্য সুখ, শিল্পকলা ও ধনৈশ্বর্য আকর্ষণের জন্য জপ করুন।",
        "hi": "ॐ शुक्राय नमः (ॐ शुक्राय नमः) — प्रेम, दांपत्य सुख, कला और आकर्षण ऊर्जा हेतु जपें।",
    },
    "Shani": {
        "en": "ॐ शं शनैश्चराय नमः (Om Sham Shanaishcharaya Namaha) — Chanted for patience, discipline, and karmic liberation.",
        "bn": "ॐ शं शनैश्चराय नमः (ওঁ শং শনৈশ্চরায় নমঃ) — ধৈর্য, সুবিচার, নিষ্ঠা ও অশুভ কর্মবন্ধন মুক্তির জন্য জপ করুন।",
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

CARD_NAMES_BN: dict[str, str] = {
    "the_fool": "দ্য ফুল (অবোধ পরিব্রাজক)",
    "the_magician": "দ্য ম্যাজিশিয়ান (মায়াবী সাধক)",
    "the_high_priestess": "দ্য হাই প্রিস্টেস (রহস্যময়ী দেবী)",
    "the_empress": "দ্য এমপ্রেস (মাতৃরূপিণী প্রকৃতি)",
    "the_emperor": "দ্য এম্পেরর (সার্বভৌম সম্রাট)",
    "the_hierophant": "দ্য হায়ারোফ্যান্ট (মহাগুরু)",
    "the_lovers": "দ্য লাভার্স (পবিত্র প্রণয়ী)",
    "the_chariot": "দ্য চ্যারিয়ট (বিজয়ী রথ)",
    "strength": "স্ট্রেন্থ (আত্মিক শক্তি)",
    "the_hermit": "দ্য হার্মিট (তপস্বী সাধক)",
    "wheel_of_fortune": "হুইল অফ ফরচুন (ভাগ্যচক্র)",
    "justice": "জাস্টিস (ন্যায়দণ্ড)",
    "the_hanged_man": "দ্য হ্যাংড ম্যান (সমর্পিত আত্মা)",
    "death": "ডেথ (মহাজাগতিক রূপান্তর)",
    "temperance": "টেম্পারেন্স (সংযম ও ভারসাম্য)",
    "the_devil": "দ্য ডেভিল (মোহ ও আসক্তি)",
    "the_tower": "দ্য টাওয়ার (ভ্রান্তিভঙ্গ ও নবসূচনা)",
    "the_star": "দ্য স্টার (আশার আলোকবর্তিকা)",
    "the_moon": "দ্য মুন (স্বপ্ন ও অন্তর্লোক)",
    "the_sun": "দ্য সান (প্রদীপ্ত সূর্য ও বিজয়)",
    "judgement": "জাজমেন্ট (আত্মজাগরণ ও মুক্তি)",
    "the_world": "দ্য ওয়ার্ল্ড (পূর্ণতা ও সিদ্ধি)",
}

CARD_NAMES_HI: dict[str, str] = {
    "the_fool": "द फूल (निश्चल यात्री)",
    "the_magician": "द मैजिशियन (जादूगर)",
    "the_high_priestess": "द हाई प्रीस्टेस (गूढ़ साध्वी)",
    "the_empress": "द एम्प्रेस (सृजन दात्री)",
    "the_emperor": "द एम्परर (सम्राट)",
    "the_hierophant": "द हायरोफैंट (धर्मगुरु)",
    "the_lovers": "द लवर्स (प्रेमी युगल)",
    "the_chariot": "द चेरियट (विजय रथ)",
    "strength": "स्ट्रेंथ (आत्मबल)",
    "the_hermit": "द हर्मिट (एकांत साधक)",
    "wheel_of_fortune": "व्हील ऑफ फॉर्च्यून (भाग्य चक्र)",
    "justice": "जस्टिस (न्याय चक्र)",
    "the_hanged_man": "द हैंग्ड मैन (समर्पित आत्मा)",
    "death": "डेथ (महा-रूपांतरण)",
    "temperance": "टेम्परेंस (संयम संतुलन)",
    "the_devil": "द डेविल (माया बंधन)",
    "the_tower": "द टॉवर (भ्रम ध्वंस)",
    "the_star": "द स्टार (दिव्य आशा)",
    "the_moon": "द मून (अंतर्मन रहस्य)",
    "the_sun": "द सन (दिव्य सूर्य तेज)",
    "judgement": "जजमेंट (आत्मजागरण)",
    "the_world": "द वर्ल्ड (परम सिद्धि)",
}

ELEMENT_NAMES_I18N: dict[str, dict[str, str]] = {
    "Fire": {"en": "Fire", "bn": "অগ্নি (তেজ)", "hi": "अग्नि तत्व"},
    "Water": {"en": "Water", "bn": "জল (আপঃ)", "hi": "जल तत्व"},
    "Air": {"en": "Air", "bn": "বায়ু (মরুৎ)", "hi": "वायु तत्व"},
    "Earth": {"en": "Earth", "bn": "পৃথিবী (ক্ষিতি)", "hi": "पृथ्वी तत्व"},
    "Spirit": {"en": "Spirit", "bn": "ব্যোম (আকাশ/আত্মা)", "hi": "आकाश तत्व"},
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
        # Astrological sign harmonic
        if user_moon_sign and c.get("astrology"):
            if user_moon_sign.lower() in c["astrology"].lower():
                w += 0.8

        # Vedic Graha harmonic
        if active_dasha_lord and c.get("vedic_graha"):
            if active_dasha_lord.lower() in c["vedic_graha"].lower():
                w += 1.0

        # Suit category affinity
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


def draw_tarot_spread(request: TarotDrawRequest) -> TarotDrawResponse:
    """Perform a comprehensive tarot draw with multilingual synthesis."""
    lang = request.language or "en"
    spread_data = SPREADS_BY_ID.get(request.spread_id)
    if not spread_data:
        spread_data = SPREADS_BY_ID["past_present_future"]

    card_count = spread_data["card_count"]
    positions = spread_data["positions"]

    # Seed RNG if intention_seed provided
    rng = random.Random()
    if request.intention_seed is not None:
        rng.seed(request.intention_seed)

    # Determine drawn card indices
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

    # If seeker provided partial or no indices, sample the rest
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
        pos_info = positions[pos_idx] if pos_idx < len(positions) else {
            "index": pos_idx + 1,
            "title": f"Position {pos_idx + 1}",
            "role": "insight",
            "description": "Cosmic perspective",
        }

        # Orientation: 28% chance of reversed
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

        # Advice formulation by language
        card_name = raw_card["name"]
        if lang == "bn":
            loc_card = CARD_NAMES_BN.get(raw_card["id"], card_name)
            advice = (
                f"{loc_card}-এর জাগ্রত শক্তিকে গ্রহণ করুন এবং আপনার কর্মে প্রতিফলিত করুন।"
                if orientation == "upright"
                else f"{loc_card}-এর উল্টো শক্তির কারণে ভেতরের দ্বিধা ও বাধা দূর করে আত্মশুদ্ধি বজায় রাখুন।"
            )
        elif lang == "hi":
            loc_card = CARD_NAMES_HI.get(raw_card["id"], card_name)
            advice = (
                f"{loc_card} की सकारात्मक ऊर्जा को अपनाएं और कर्म में उतारें।"
                if orientation == "upright"
                else f"{loc_card} की उल्टी स्थिति में आंतरिक संशय और नकारात्मकता को दूर करें।"
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
                position_index=pos_info["index"],
                position_title=pos_info["title"],
                position_role=pos_info["role"],
                position_description=pos_info["description"],
                card=card_schema,
                orientation=orientation,
                relevant_interpretation=relevant_interp,
                keywords=interp_data.get("keywords", []),
                advice=advice,
            )
        )

    # Compute Elemental Harmony between adjacent cards
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

    # Generate Holistic Karmic Synthesis by Language
    first_card = drawn_cards_details[0]
    first_name_bn = CARD_NAMES_BN.get(first_card.card.id, first_card.card.name)
    first_name_hi = CARD_NAMES_HI.get(first_card.card.id, first_card.card.name)

    if lang == "bn":
        spread_display_name = SPREAD_NAMES_I18N.get(spread_data["id"], {}).get("bn", spread_data["name"])
        orient_bn = "জাগ্রত শক্তি" if first_card.orientation == "upright" else "অন্তর্মুখী রূপান্তর"

        if len(drawn_cards_details) == 1:
            synthesis = (
                f"আজকের দিনে আপনার মুখ্য মহাজাগতিক স্পটলাইট পড়েছে {first_name_bn} ({orient_bn})-এর ওপর। "
                f"এই কার্ডটি নির্দেশ করছে: {first_card.relevant_interpretation} "
                f"প্রধান উপাদান '{dominant_elem_loc}' আপনাকে আত্মবিশ্বাসের সাথে স্থির লক্ষ্যে অগ্রসর হতে পরামর্শ দিচ্ছে।"
            )
        elif len(drawn_cards_details) == 3:
            past_c = drawn_cards_details[0]
            pres_c = drawn_cards_details[1]
            fut_c = drawn_cards_details[2]
            p_name = CARD_NAMES_BN.get(past_c.card.id, past_c.card.name)
            pr_name = CARD_NAMES_BN.get(pres_c.card.id, pres_c.card.name)
            f_name = CARD_NAMES_BN.get(fut_c.card.id, fut_c.card.name)
            synthesis = (
                f"আপনার অতীত ভিত্তিপ্রস্তর উন্মোচিত হয়েছে {p_name} ({past_c.orientation})-এর মাধ্যমে: {past_c.relevant_interpretation} "
                f"বর্তমানে পরিস্থিতির কেন্দ্রে অবস্থান করছে {pr_name} ({pres_c.orientation}): {pres_c.relevant_interpretation} "
                f"এবং আগামী দিনে ঘটনার গতিপ্রবাহ পরিচালিত হবে {f_name} ({fut_c.orientation})-এর নির্দেশনায়: {fut_c.relevant_interpretation}"
            )
        else:
            cards_str = ", ".join(f"{CARD_NAMES_BN.get(c.card.id, c.card.name)}" for c in drawn_cards_details[:3])
            synthesis = (
                f"এই গভীর মহাজাগতিক স্প্রেডের মূল ভিত্তি আবর্তিত হচ্ছে {cards_str}-এর মাধ্যমে। "
                f"প্রধান উপাদান '{dominant_elem_loc}' এবং {karmic_momentum} "
                f"নির্দেশ করছে যে আপনার {request.category} ক্ষেত্রে দূরদর্শী ও সত্যনিষ্ঠ সিদ্ধান্ত নেওয়া আবশ্যক। "
                f"মুখ্য শিক্ষা: {first_card.relevant_interpretation}"
            )

        last_c = drawn_cards_details[-1]
        last_name_bn = CARD_NAMES_BN.get(last_c.card.id, last_c.card.name)
        actionable_guidance = (
            f"{first_name_bn}-এর সর্বোচ্চ সম্ভাবনাকে নিজের কর্মে রূপায়িত করুন। "
            f"{last_name_bn}-সংক্রান্ত কোনো ক্ষণস্থায়ী ভীতি বা উত্তেজনায় হঠকারী সিদ্ধান্ত এড়িয়ে চলুন। "
            f"'{dominant_elem_loc}' উপাদানের শান্ত গুণাবলি ধারণ করলে আগামী এক চান্দ্রমাস আপনার সার্বিক স্থিতি বজায় থাকবে।"
        )

    elif lang == "hi":
        spread_display_name = SPREAD_NAMES_I18N.get(spread_data["id"], {}).get("hi", spread_data["name"])
        orient_hi = "सीधी स्थिति" if first_card.orientation == "upright" else "उल्टी स्थिति"

        if len(drawn_cards_details) == 1:
            synthesis = (
                f"आज के दिन आपका मुख्य ब्रह्मांडीय ध्यान {first_name_hi} ({orient_hi}) पर केंद्रित है। "
                f"यह कार्ड संकेत देता है: {first_card.relevant_interpretation} "
                f"प्रमुख '{dominant_elem_loc}' आपको आत्मबल व स्पष्टता के साथ आगे बढ़ने की प्रेरणा देता है।"
            )
        elif len(drawn_cards_details) == 3:
            past_c = drawn_cards_details[0]
            pres_c = drawn_cards_details[1]
            fut_c = drawn_cards_details[2]
            p_name = CARD_NAMES_HI.get(past_c.card.id, past_c.card.name)
            pr_name = CARD_NAMES_HI.get(pres_c.card.id, pres_c.card.name)
            f_name = CARD_NAMES_HI.get(fut_c.card.id, fut_c.card.name)
            synthesis = (
                f"आपकी स्थिति का मूल आधार {p_name} ({past_c.orientation}) से प्रकट होता है: {past_c.relevant_interpretation} "
                f"वर्तमान में घटनाक्रम के केंद्र में {pr_name} ({pres_c.orientation}) स्थित है: {pres_c.relevant_interpretation} "
                f"तथा भविष्य की दिशा {f_name} ({fut_c.orientation}) द्वारा प्रशस्त होगी: {fut_c.relevant_interpretation}"
            )
        else:
            cards_str = ", ".join(f"{CARD_NAMES_HI.get(c.card.id, c.card.name)}" for c in drawn_cards_details[:3])
            synthesis = (
                f"इस दिव्य स्प्रेड का मुख्य आधार {cards_str} द्वारा संचालित है। "
                f"प्रमुख '{dominant_elem_loc}' एवं {karmic_momentum} "
                f"बताते हैं कि आपके {request.category} क्षेत्र में विवेकपूर्ण निर्णय आवश्यक हैं। "
                f"मुख्य संदेश: {first_card.relevant_interpretation}"
            )

        last_c = drawn_cards_details[-1]
        last_name_hi = CARD_NAMES_HI.get(last_c.card.id, last_c.card.name)
        actionable_guidance = (
            f"{first_name_hi} के सकारात्मक प्रभाव को जीवन में उतारें। "
            f"{last_name_hi} से संबंधित किसी भी जल्दबाजी या भय से बचें। "
            f"'{dominant_elem_loc}' का संतुलन बनाए रखने से आगामी समय में मनोवांछित स्थिरता प्राप्त होगी।"
        )

    else:
        spread_display_name = spread_data["name"]
        lead_card_name = f"{first_card.card.name} ({first_card.orientation.capitalize()})"
        if len(drawn_cards_details) == 1:
            synthesis = (
                f"The cosmic spotlight falls squarely upon {lead_card_name}. "
                f"As your {first_card.position_title}, this presence indicates that {first_card.relevant_interpretation} "
                f"The primary element of {dominant_elem} asks you to anchor clarity and act with deliberate intention."
            )
        elif len(drawn_cards_details) == 3:
            past_card = drawn_cards_details[0]
            pres_card = drawn_cards_details[1]
            fut_card = drawn_cards_details[2]
            synthesis = (
                f"Your timeline unfolds from the energetic genesis of {past_card.card.name} ({past_card.orientation}), "
                f"revealing that {past_card.relevant_interpretation} "
                f"Presently, {pres_card.card.name} ({pres_card.orientation}) stands at the vortex: {pres_card.relevant_interpretation} "
                f"The forward trajectory crystallizes through {fut_card.card.name} ({fut_card.orientation}), promising that {fut_card.relevant_interpretation}"
            )
        else:
            key_cards_summary = ", ".join(
                f"{c.position_title}: {c.card.name} ({c.orientation})" for c in drawn_cards_details[:3]
            )
            synthesis = (
                f"This profound spread anchors through {key_cards_summary}. "
                f"The dominant elemental frequency of {dominant_elem} combined with {karmic_momentum.lower()} "
                f"calls for unwavering discernment in your {request.category} affairs. "
                f"Core takeaway: {first_card.relevant_interpretation} Moving forward, align your actions with truth and elevated conscious intent."
            )

        primary_challenge_card = drawn_cards_details[-1]
        actionable_guidance = (
            f"Focus your immediate efforts on grounding the highest vibrational expression of {first_card.card.name}. "
            f"Avoid haste or reactive fear regarding {primary_challenge_card.card.name} ({primary_challenge_card.orientation}). "
            f"Meditation on {dominant_elem.lower()} qualities will provide strategic equilibrium over the next lunar cycle."
        )

    # Vedic Remedy & Mantra selection
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
