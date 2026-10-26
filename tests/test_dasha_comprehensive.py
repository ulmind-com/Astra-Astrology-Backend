"""Comprehensive test suite for Advanced Dasha Calculator."""

import pytest
from app.schemas.astrology import KPCalculateRequest
from app.services.astrology.dasha_calculator import calculate_advanced_dasha


def test_dasha_calculation_comprehensive():
    """Validates complete 5-tier Vimshottari, Yogini, Sandhi/Chidra, Phala, Transit, and Timeline."""
    payload = KPCalculateRequest(
        name="Arjun Mukherjee",
        gender="male",
        day=15,
        month=8,
        year=1995,
        hour=14,
        minute=30,
        second=0,
        place="Kolkata, India",
        latitude=22.5726,
        longitude=88.3639,
        timezone=5.5,
        ayanamsa="krishnamurti",
        language="en",
    )

    res = calculate_advanced_dasha(payload)

    # 1. Basic properties
    assert res.name == "Arjun Mukherjee"
    assert len(res.planets) == 9  # 9 classical planets
    assert len(res.cusps) == 12

    # 2. Vimshottari Dasha Hierarchy
    assert len(res.dashas) == 9
    first_md = res.dashas[0]
    assert len(first_md.sub_periods) > 0

    # 3. Running Dasha 5-Tier Snapshot
    assert res.current_running_dasha is not None
    running = res.current_running_dasha
    assert running.mahadasha != ""
    assert running.antardasha != ""
    assert running.pratyantardasha != ""
    assert running.sookshma_dasha != ""
    assert running.pran_dasha != ""
    assert ">" in running.active_path
    assert len(running.sookshma_periods) == 9
    assert len(running.pran_periods) == 9

    # 4. Dasha Sandhi & Chidra
    assert res.dasha_sandhi_chidra is not None
    sandhi = res.dasha_sandhi_chidra
    assert sandhi.current_md_lord == running.mahadasha
    assert sandhi.next_md_lord != ""

    # 5. Personalized Lagna-Aware Phala
    assert len(res.personalized_dasha_phala) == 9
    phala_planets = [item.planet for item in res.personalized_dasha_phala]
    assert "Sun" in phala_planets
    assert "Venus" in phala_planets
    assert "Saturn" in phala_planets
    for p in res.personalized_dasha_phala:
        assert p.functional_nature != ""
        assert 10 <= p.favorability_score <= 100
        assert p.career_impact != ""
        assert p.wealth_impact != ""

    # 6. Yogini Dasha System
    assert res.yogini_dasha is not None
    yogini = res.yogini_dasha
    assert yogini.birth_nakshatra != ""
    assert yogini.starting_yogini in [
        "Mangala", "Pingala", "Dhanya", "Bhramari",
        "Bhadrika", "Ulka", "Siddha", "Sankata",
    ]
    assert len(yogini.periods) >= 8
    assert yogini.current_yogini != ""

    # 7. Dasha-Transit Synergy & Sade Sati
    assert res.dasha_transit_synergy is not None
    transit = res.dasha_transit_synergy
    assert transit.md_lord == running.mahadasha
    assert transit.ad_lord == running.antardasha
    assert transit.md_transit_sign != ""
    assert 1 <= transit.md_transit_house_from_moon <= 12
    assert transit.sade_sati_phase != ""

    # 8. Life Timeline Bar Segments
    assert len(res.dasha_life_timeline) == 9
    for seg in res.dasha_life_timeline:
        assert seg.duration_years > 0
        assert seg.nature in ["favorable", "neutral", "challenging"]
        assert 10 <= seg.favorability_score <= 100


def test_dasha_api_endpoint():
    """Ensures POST /api/v1/astrology/dasha returns 200 with rich dasha modules."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    payload = {
        "name": "Kavita Sen",
        "gender": "female",
        "day": 20,
        "month": 11,
        "year": 1990,
        "hour": 8,
        "minute": 15,
        "second": 0,
        "place": "Delhi, India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": 5.5,
        "ayanamsa": "lahiri",
        "language": "en",
    }
    resp = client.post("/api/v1/astrology/dasha", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "Kavita Sen"
    assert "current_running_dasha" in data
    assert data["current_running_dasha"]["mahadasha"] != ""
    assert "yogini_dasha" in data
    assert "dasha_sandhi_chidra" in data
    assert "dasha_transit_synergy" in data
    assert len(data["personalized_dasha_phala"]) == 9
    assert len(data["dasha_life_timeline"]) == 9

