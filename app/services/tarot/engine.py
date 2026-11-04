"""Chrono-Astrological Tarot Engine (CATE).

Implements world-class 78-card Tarot reading engine with:
- Canonical Major and Minor Arcana symbolism
- Astrological (Zodiac/Planetary) and Vedic Graha resonance
- Elemental Dignities & Harmonic balance calculation
- Multi-pillar interpretations (General, Love, Career, Finance, Spiritual)
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

GRAHA_MANTRAS: dict[str, str] = {
    "Surya": "ॐ सूर्याय नमः (Om Suryaya Namaha) — Chanted for vitality, clarity, and sovereign purpose.",
    "Chandra": "ॐ सोमाय नमः (Om Somaya Namaha) — Chanted for emotional equilibrium and intuitive receptivity.",
    "Mangal": "ॐ अङ्गारकाय नमः (Om Angarakaya Namaha) — Chanted for righteous courage, vitality, and overcoming obstacles.",
    "Budha": "ॐ बुधाय नमः (Om Budhaya Namaha) — Chanted for intellect, discerning communication, and business acumen.",
    "Guru": "ॐ गुरवे नमः (Om Guruve Namaha) — Chanted for divine wisdom, spiritual expansion, and cosmic grace.",
    "Shukra": "ॐ शुक्राय नमः (Om Shukraya Namaha) — Chanted for harmony, creative magnetism, and deep love.",
    "Shani": "ॐ शं शनैश्चराय नमः (Om Sham Shanaishcharaya Namaha) — Chanted for patience, discipline, and karmic liberation.",
    "Rahu": "ॐ राहवे नमः (Om Rahave Namaha) — Chanted for dissolving illusions and mastering unconventional paths.",
    "Ketu": "ॐ केतवे नमः (Om Ketave Namaha) — Chanted for spiritual detachment, deep enlightenment, and moksha.",
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
    """Perform a comprehensive tarot draw for the requested spread."""
    spread_data = SPREADS_BY_ID.get(request.spread_id)
    if not spread_data:
        # Fallback to past_present_future
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

    # If user provided partial or no indices, sample the rest
    if len(selected_indices) < card_count:
        remaining_indices = [i for i in range(deck_size) if i not in selected_indices]
        weights = _compute_card_weights(
            [deck[i] for i in remaining_indices],
            request.user_moon_sign,
            request.active_dasha_lord,
            request.category,
        )
        needed = card_count - len(selected_indices)

        # Weighted sampling without replacement
        sampled = []
        cur_pool = list(remaining_indices)
        cur_weights = list(weights)
        for _ in range(needed):
            if not cur_pool:
                break
            # Choices with current weights
            chosen = rng.choices(cur_pool, weights=cur_weights, k=1)[0]
            sampled.append(chosen)
            idx_in_pool = cur_pool.index(chosen)
            cur_pool.pop(idx_in_pool)
            cur_weights.pop(idx_in_pool)

        selected_indices.extend(sampled)

    # Orientation determination (~75% upright, 25% reversed base probability)
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

        # Category interpretation
        cat_key = request.category if request.category in interp_data else "general"
        relevant_interp = interp_data.get(cat_key, interp_data.get("general", ""))

        # Element count
        elem = raw_card.get("element", "Spirit")
        element_counts[elem] = element_counts.get(elem, 0) + 1

        if raw_card.get("arcana") == "major":
            major_arcana_count += 1

        graha = raw_card.get("vedic_graha")
        if graha and graha not in grahas_present:
            grahas_present.append(graha)

        # Advice formulation
        card_name = raw_card["name"]
        role = pos_info["role"]
        if orientation == "upright":
            advice = (
                f"Embrace the expansive power of {card_name}. Channel its authentic virtues into your {pos_info['title'].lower()}."
            )
        else:
            advice = (
                f"Be mindful of inner resistance or misdirection regarding {card_name}. Clear internal blockages to restore equilibrium."
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
            rel = ELEMENT_RELATIONSHIPS.get(curr_elem, {}).get(
                next_elem, "Neutral celestial balance."
            )
            drawn_cards_details[i].elemental_harmony = f"Dynamic with next card ({next_elem}): {rel}"
        elif len(drawn_cards_details) > 1:
            prev_elem = drawn_cards_details[i - 1].card.element
            rel = ELEMENT_RELATIONSHIPS.get(curr_elem, {}).get(
                prev_elem, "Neutral celestial balance."
            )
            drawn_cards_details[i].elemental_harmony = f"Rooted in preceding card ({prev_elem}): {rel}"

    # Dominant element
    dominant_elem = max(element_counts, key=lambda k: element_counts[k])

    # Astrological resonance metadata
    major_ratio = round((major_arcana_count / card_count) * 100)
    if major_ratio >= 60:
        karmic_momentum = "High Karmic Destiny — Situations are orchestrated by cosmic momentum; your spiritual surrender and aligned response are pivotal."
    elif major_ratio >= 30:
        karmic_momentum = "Balanced Karmic & Mundane Flow — Both personal tactical choices and larger destiny patterns are equally shaping the reality."
    else:
        karmic_momentum = "High Personal Agency — Day-to-day tactical decisions, practical communication, and immediate habits dictate the trajectory."

    astrological_resonance = {
        "major_arcana_percentage": major_ratio,
        "karmic_momentum": karmic_momentum,
        "active_grahas": grahas_present,
        "dominant_element": dominant_elem,
        "aligned_with_user_moon": bool(request.user_moon_sign),
        "aligned_with_active_dasha": bool(request.active_dasha_lord),
    }

    # Generate Holistic Karmic Synthesis
    first_card = drawn_cards_details[0]
    lead_card_name = f"{first_card.card.name} ({first_card.orientation.capitalize()})"
    
    if len(drawn_cards_details) == 1:
        synthesis = (
            f"The cosmic spotlight falls squarely upon {lead_card_name}. "
            f"As your {first_card.position_title}, this presence indicates that {first_card.relevant_interpretation.lower()} "
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
        # Multi-card general synthesis
        key_cards_summary = ", ".join(
            f"{c.position_title}: {c.card.name} ({c.orientation})" for c in drawn_cards_details[:3]
        )
        synthesis = (
            f"This profound spread anchors through {key_cards_summary}. "
            f"The dominant elemental frequency of {dominant_elem} combined with {karmic_momentum.lower()} "
            f"calls for unwavering discernment in your {request.category} affairs. "
            f"Core takeaway: {first_card.relevant_interpretation} Moving forward, align your actions with truth and elevated conscious intent."
        )

    # Actionable guidance
    primary_challenge_card = drawn_cards_details[-1]
    actionable_guidance = (
        f"Focus your immediate efforts on grounding the highest vibrational expression of {first_card.card.name}. "
        f"Avoid haste or reactive fear regarding {primary_challenge_card.card.name} ({primary_challenge_card.orientation}). "
        f"Meditation on {dominant_elem.lower()} qualities will provide strategic equilibrium over the next lunar cycle."
    )

    # Vedic Remedy & Mantra selection
    # Select remedy from either the first major card or the final card
    chosen_card_for_remedy = next((c.card for c in drawn_cards_details if c.card.arcana == "major"), drawn_cards_details[-1].card)
    prescribed_remedy = chosen_card_for_remedy.remedy
    chosen_graha = chosen_card_for_remedy.vedic_graha
    vedic_mantra = GRAHA_MANTRAS.get(
        chosen_graha,
        "ॐ नमः शिवाय (Om Namah Shivaya) — Master mantra for universal peace, protection, and psychic purification.",
    )

    draw_id = uuid.uuid4().hex[:12]
    now_iso = datetime.now(timezone.utc).isoformat()

    return TarotDrawResponse(
        draw_id=draw_id,
        timestamp=now_iso,
        spread_id=spread_data["id"],
        spread_name=spread_data["name"],
        category=request.category,
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
    """Return deterministic Daily Card for today or requested date."""
    target_date = request.date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Hash the date string with optional moon sign to get a consistent integer seed
    seed_key = f"daily_tarot:{target_date}:{request.moon_sign or 'universal'}:{request.category}"
    int_seed = int(hashlib.sha256(seed_key.encode("utf-8")).hexdigest()[:8], 16)

    draw_req = TarotDrawRequest(
        spread_id="daily_guidance",
        category=request.category,
        question=f"Universal Divine Guidance for {target_date}",
        user_moon_sign=request.moon_sign,
        intention_seed=int_seed,
    )

    return draw_tarot_spread(draw_req)

