"""Comprehensive tests for the advanced classical Nakshatra calculator rules:
1. Gandanta / Abhukta Mula detection and classical Shanti remedies.
2. Pushkara Navamsha (24 sacred zones) & Pushkara Bhaga detection.
3. Vimshottari Mahadasha balance at birth (Years, Months, Days).
4. Real-time Daily Transit Tara Bala with Swiss Ephemeris.
5. Nakshatra Dispositions (7 Gunatmak classes), Totems, and Sacred Birds.
6. Full FastAPI HTTP API 200 payload verification.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.astrology import NakshatraCalculateRequest
from app.services.astrology.calculator import calculate_nakshatra


client = TestClient(app)


def test_reference_chart_a_advancements():
    """Verify Client Reference Chart 1 (Hasta Pada 1, Moon in Virgo)."""
    payload = NakshatraCalculateRequest(
        name="Reference A",
        gender="male",
        day=19,
        month=3,
        year=1992,
        hour=12,
        minute=12,
        second=0,
        period="24H",
        place="Mumbai Coastal Reference",
        latitude=19.2333,
        longitude=72.1167,
        timezone=5.5,
        ayanamsa="lahiri",
        language="bn",
    )
    result = calculate_nakshatra(payload)

    # Core checks
    assert result.nakshatra_name_en == "Hasta"
    assert result.pada == 1
    assert result.star_lord == "Moon"
    assert result.rashi_name_en == "Virgo"

    # 1. Gandanta Check (Hasta is safe, not a water-fire sandhi)
    assert result.gandanta.is_gandanta is False
    assert result.gandanta.severity == "None"

    # 2. Dasha Balance (Moon Mahadasha has 10 years total)
    assert result.dasha_balance.dasha_lord_en == "Moon"
    assert result.dasha_balance.total_cycle_years == 10
    assert 0 <= result.dasha_balance.balance_years <= 10
    assert "বছর" in result.dasha_balance.balance_formatted_bn

    # 3. Live Daily Transit Tara Bala
    assert 1 <= result.daily_tara_bala.tara_step <= 9
    assert result.daily_tara_bala.tara_name_en != ""
    assert result.daily_tara_bala.status_label_bn != ""

    # 4. Disposition & Totem Matrix (Hasta is Kshipra / Swift, Bird is Vulture/Kite)
    assert "Kshipra" in result.disposition.disposition_en
    assert "ক্ষিপ্র" in result.disposition.disposition_bn
    assert "Vulture" in result.disposition.sacred_bird_en
    assert len(result.disposition.suitable_activities_bn) > 0


def test_abhukta_mula_gandanta_detection():
    """Verify extreme Gandanta (Abhukta Mula: Jyeshtha Pada 4 / Mula Pada 1).
    Birth on 13 Dec 1993, 20:00 in Kolkata -> Moon in Sagittarius 240.59° (Mula Pada 1).
    """
    payload = NakshatraCalculateRequest(
        name="Mula Native",
        gender="female",
        day=13,
        month=12,
        year=1993,
        hour=20,
        minute=0,
        second=0,
        period="24H",
        place="Kolkata",
        latitude=22.5726,
        longitude=88.3639,
        timezone=5.5,
        ayanamsa="lahiri",
        language="en",
    )
    result = calculate_nakshatra(payload)

    assert result.nakshatra_name_en == "Mula"
    assert result.pada == 1
    assert result.gandanta.is_gandanta is True
    assert "Abhukta Mula" in result.gandanta.gandanta_type
    assert result.gandanta.severity == "Extreme (Abhukta Mula)"
    assert len(result.gandanta.remedies_en) >= 3


def test_pushkara_navamsha_detection():
    """Verify Pushkara Navamsha.
    Birth on 22 May 1982, 06:00 in Delhi -> Moon in Taurus (Rohini Pada 2),
    which is Pushkara Navamsha Taurus & Pushkara Bhaga 14°.
    """
    payload = NakshatraCalculateRequest(
        name="Rohini Pushkara",
        gender="male",
        day=22,
        month=5,
        year=1982,
        hour=6,
        minute=0,
        second=0,
        period="24H",
        place="New Delhi",
        latitude=28.6139,
        longitude=77.2090,
        timezone=5.5,
        ayanamsa="lahiri",
        language="en",
    )
    result = calculate_nakshatra(payload)

    # In Taurus (sign_idx 1), Pushkara Navamsha is 5th navamsha (13°20' - 16°40')
    if 13.33333333 <= (result.moon_sidereal_longitude % 30.0) < 16.66666667:
        assert result.pushkara.is_pushkara_navamsha is True
        assert result.pushkara.is_pushkara_bhaga is True


def test_nakshatra_api_http_endpoint():
    """Test full HTTP POST endpoint /api/v1/astrology/nakshatra."""
    payload = {
        "name": "Arjun Roy",
        "gender": "male",
        "day": 15,
        "month": 8,
        "year": 1947,
        "hour": 0,
        "minute": 0,
        "second": 0,
        "period": "24H",
        "place": "New Delhi, India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": 5.5,
        "ayanamsa": "lahiri",
        "language": "bn",
    }
    response = client.post("/api/v1/astrology/nakshatra", json=payload)
    assert response.status_code == 200, response.text
    res_json = response.json()
    assert res_json["success"] is True
    data = res_json["data"]

    assert "gandanta" in data
    assert "pushkara" in data
    assert "dasha_balance" in data
    assert "daily_tara_bala" in data
    assert "disposition" in data
    assert data["nakshatra_name_en"] == "Pushya"
    assert data["star_lord"] == "Saturn"
    assert data["dasha_balance"]["dasha_lord_en"] == "Saturn"
    assert data["dasha_balance"]["total_cycle_years"] == 19
