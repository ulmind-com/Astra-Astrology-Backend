"""Comprehensive unit & integration tests for Chrono-Astrological Tarot Engine."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.tarot import (
    ALL_TAROT_CARDS,
    ALL_SPREADS,
    TAROT_DECK_BY_ID,
    SPREADS_BY_ID,
    get_all_cards,
    get_card_by_id,
    get_all_spreads,
    get_spread_by_id,
    draw_tarot_spread,
    get_daily_tarot_card,
)
from app.schemas.tarot import TarotDrawRequest, DailyTarotRequest


def test_deck_completeness_and_canonical_structure():
    """Verify standard 78-card Tarot system (22 Major + 56 Minor)."""
    assert len(ALL_TAROT_CARDS) == 78
    assert len(TAROT_DECK_BY_ID) == 78

    major = [c for c in ALL_TAROT_CARDS if c["arcana"] == "major"]
    minor = [c for c in ALL_TAROT_CARDS if c["arcana"] == "minor"]
    assert len(major) == 22
    assert len(minor) == 56

    suits = {"wands": 0, "cups": 0, "swords": 0, "pentacles": 0}
    for c in minor:
        assert c["suit"] in suits
        suits[c["suit"]] += 1
    assert suits == {"wands": 14, "cups": 14, "swords": 14, "pentacles": 14}

    # Verify each card has both upright and reversed interpretations across all 5 life areas
    for c in ALL_TAROT_CARDS:
        assert "id" in c and len(c["id"]) > 0
        assert "name" in c and len(c["name"]) > 0
        assert "element" in c
        assert "astrology" in c
        assert "vedic_graha" in c
        assert "remedy" in c and len(c["remedy"]) > 10
        assert "affirmation" in c

        for orientation in ("upright", "reversed"):
            interp = c[orientation]
            for area in ("general", "love", "career", "finance", "spiritual"):
                assert area in interp and len(interp[area]) > 0
            assert "keywords" in interp and len(interp["keywords"]) > 0


def test_spread_architectures():
    """Verify all 6 authentic spreads and position counts."""
    assert len(ALL_SPREADS) == 6
    expected_spreads = {
        "daily_guidance": 1,
        "past_present_future": 3,
        "two_choices": 4,
        "love_soulmate": 5,
        "career_wealth": 5,
        "celtic_cross": 10,
    }

    for spread in ALL_SPREADS:
        s_id = spread["id"]
        assert s_id in expected_spreads
        expected_count = expected_spreads[s_id]
        assert spread["card_count"] == expected_count
        assert len(spread["positions"]) == expected_count

        # Ensure unique position indices
        indices = [p["index"] for p in spread["positions"]]
        assert len(set(indices)) == expected_count


def test_draw_engine_execution():
    """Verify draw logic across different spreads and life categories."""
    req = TarotDrawRequest(
        spread_id="past_present_future",
        category="career",
        question="Should I accept the senior leadership position?",
        user_moon_sign="Sagittarius",
        active_dasha_lord="Guru",
        intention_seed=4242,
    )
    res = draw_tarot_spread(req)

    assert res.spread_id == "past_present_future"
    assert len(res.drawn_cards) == 3
    assert res.category == "career"
    assert sum(res.elemental_breakdown.values()) == 3
    assert res.dominant_element in ("Fire", "Water", "Air", "Earth", "Spirit")
    assert len(res.karmic_synthesis) > 50
    assert len(res.actionable_guidance) > 20
    assert len(res.prescribed_remedy) > 10
    assert "ॐ" in res.vedic_mantra

    # Test Celtic Cross (10 cards)
    cc_req = TarotDrawRequest(
        spread_id="celtic_cross",
        category="general",
        intention_seed=999,
    )
    cc_res = draw_tarot_spread(cc_req)
    assert len(cc_res.drawn_cards) == 10
    card_names = [c.card.name for c in cc_res.drawn_cards]
    # Verify cards drawn are unique (no duplicates in single spread)
    assert len(set(card_names)) == 10


def test_manual_interactive_card_selection():
    """Verify seeker tactile selection is respected."""
    custom_indices = [0, 1, 2]  # The Fool, The Magician, The High Priestess
    req = TarotDrawRequest(
        spread_id="past_present_future",
        category="love",
        selected_indices=custom_indices,
    )
    res = draw_tarot_spread(req)
    drawn_ids = [c.card.id for c in res.drawn_cards]
    assert drawn_ids == ["the_fool", "the_magician", "the_high_priestess"]


def test_daily_tarot_determinism():
    """Verify daily card returns deterministic reading for same date and moon sign."""
    req1 = DailyTarotRequest(category="spiritual", date_str="2026-11-04", moon_sign="Cancer")
    req2 = DailyTarotRequest(category="spiritual", date_str="2026-11-04", moon_sign="Cancer")

    res1 = get_daily_tarot_card(req1)
    res2 = get_daily_tarot_card(req2)

    assert res1.drawn_cards[0].card.id == res2.drawn_cards[0].card.id
    assert res1.drawn_cards[0].orientation == res2.drawn_cards[0].orientation


def test_tarot_fastapi_endpoints():
    """Integration test with FastAPI TestClient."""
    client = TestClient(app)

    # 1. Deck
    res_deck = client.get("/api/v1/tarot/deck")
    assert res_deck.status_code == 200
    deck_data = res_deck.json()
    assert deck_data["success"] is True
    assert len(deck_data["data"]) == 78

    # Filter major arcana
    res_major = client.get("/api/v1/tarot/deck?arcana=major")
    assert res_major.status_code == 200
    assert len(res_major.json()["data"]) == 22

    # 2. Specific card
    res_card = client.get("/api/v1/tarot/cards/the_fool")
    assert res_card.status_code == 200
    card_data = res_card.json()["data"]
    assert card_data["name"] == "The Fool"
    assert card_data["arcana"] == "major"
    assert card_data["vedic_graha"] == "Rahu"

    # Nonexistent card
    res_404 = client.get("/api/v1/tarot/cards/invalid_card_xyz")
    assert res_404.status_code == 404

    # 3. Spreads
    res_spreads = client.get("/api/v1/tarot/spreads")
    assert res_spreads.status_code == 200
    assert len(res_spreads.json()["data"]) == 6

    res_single_spread = client.get("/api/v1/tarot/spreads/past_present_future")
    assert res_single_spread.status_code == 200
    assert res_single_spread.json()["data"]["card_count"] == 3

    # 4. Draw endpoint
    res_draw = client.post(
        "/api/v1/tarot/draw",
        json={
            "spread_id": "past_present_future",
            "category": "finance",
            "question": "What is the cosmic financial trajectory?",
            "user_moon_sign": "Taurus",
            "active_dasha_lord": "Shukra",
        },
    )
    assert res_draw.status_code == 200
    draw_data = res_draw.json()
    assert draw_data["success"] is True
    assert len(draw_data["data"]["drawn_cards"]) == 3
    assert draw_data["data"]["category"] == "finance"

    # 5. Daily endpoint
    res_daily = client.post(
        "/api/v1/tarot/daily",
        json={
            "category": "career",
            "date_str": "2026-11-04",
        },
    )
    assert res_daily.status_code == 200
    assert res_daily.json()["success"] is True
    assert len(res_daily.json()["data"]["drawn_cards"]) == 1
