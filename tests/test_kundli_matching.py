"""Unit & regression tests for Kundli Matching and Marriage Life Forecast."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.astrology import KundliMatchingRequest, KundliMatchingPersonInput
from app.services.astrology.kundli_matching_service import calculate_kundli_matching

client = TestClient(app)


def test_kundli_matching_forecast_service():
    req = KundliMatchingRequest(
        groom=KundliMatchingPersonInput(
            name="Rahul Sharma",
            gender="male",
            day=15,
            month=8,
            year=1995,
            hour=14,
            minute=30,
            second=0,
            period="PM",
            place="Kolkata",
            latitude=22.5726,
            longitude=88.3639,
            timezone=5.5,
        ),
        bride=KundliMatchingPersonInput(
            name="Priya Patel",
            gender="female",
            day=20,
            month=11,
            year=1997,
            hour=9,
            minute=15,
            second=0,
            period="AM",
            place="Kolkata",
            latitude=22.5726,
            longitude=88.3639,
            timezone=5.5,
        ),
        language="bn",
    )

    res = calculate_kundli_matching(req)

    assert res.total_received >= 0
    assert res.total_out_of == 36.0
    assert len(res.kootas) == 8
    assert res.forecast is not None

    # Check 7 core marriage insights
    fc = res.forecast
    assert len(fc.ideal_marriage_age_groom) > 0
    assert len(fc.ideal_marriage_age_bride) > 0
    assert len(fc.auspicious_marriage_years) >= 1
    assert len(fc.auspicious_marriage_years_text) > 0
    assert 0 <= fc.marital_harmony_score <= 100
    assert len(fc.marital_harmony_verdict) > 0
    assert len(fc.marital_harmony_description) > 0
    assert 0 <= fc.children_progeny_score <= 100
    assert len(fc.children_progeny_verdict) > 0
    assert 0 <= fc.conflict_friction_score <= 100
    assert len(fc.conflict_friction_verdict) > 0
    assert 0 <= fc.financial_prosperity_score <= 100
    assert len(fc.financial_prosperity_verdict) > 0
    assert 0 <= fc.future_longevity_score <= 100
    assert len(fc.future_longevity_verdict) > 0
    assert len(fc.remedies_guidance) >= 1


def test_kundli_matching_api():
    payload = {
        "groom": {
            "name": "Amit",
            "gender": "male",
            "day": 10,
            "month": 5,
            "year": 1994,
            "hour": 11,
            "minute": 20,
            "period": "AM",
            "place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5,
        },
        "bride": {
            "name": "Sneha",
            "gender": "female",
            "day": 25,
            "month": 8,
            "year": 1996,
            "hour": 18,
            "minute": 45,
            "period": "PM",
            "place": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5,
        },
        "language": "en",
    }
    response = client.post("/api/v1/astrology/kundli-matching", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    res_data = data["data"]
    assert "forecast" in res_data
    assert res_data["forecast"]["ideal_marriage_age_groom"] != ""

    # Verify new features
    assert "dashakoot" in res_data and res_data["dashakoot"] is not None
    assert len(res_data["dashakoot"]["items"]) == 10
    assert res_data["dashakoot"]["total_out_of"] == 36.0

    assert "avakahada_comparison" in res_data
    assert len(res_data["avakahada_comparison"]) >= 15

    assert "cancellations" in res_data
    assert len(res_data["cancellations"]) >= 3

    assert "papasamya" in res_data and res_data["papasamya"] is not None
    assert res_data["papasamya"]["groom_score"]["total_points"] >= 0

    assert "personality" in res_data and res_data["personality"] is not None
    assert len(res_data["personality"]["groom_positive_traits"]) >= 3

    assert "groom_charts" in res_data and res_data["groom_charts"] is not None
    assert len(res_data["groom_charts"]["d9_planets"]) == 10
    assert len(res_data["groom_charts"]["moon_chart_planets"]) == 10


def test_kundli_matching_client_reference_benchmark():
    """Verifies against the client's worked reference sample report:
    Rahul Pandat PDFs / Kusthi Rules / matching-pdf-english.pdf
    Sanjay (19/3/1992 12:12 AM Mumbai 19N14 72E07) &
    Neha (12/1/1995 12:16 PM 19N14 72E14)
    """
    req = KundliMatchingRequest(
        groom=KundliMatchingPersonInput(
            name="SANJAY RAJPOOT",
            gender="male",
            day=19,
            month=3,
            year=1992,
            hour=12,
            minute=12,
            second=0,
            period="PM",
            place="Mumbai",
            latitude=19.2333,
            longitude=72.1167,
            timezone=5.5,
        ),
        bride=KundliMatchingPersonInput(
            name="NEHA SINGH",
            gender="female",
            day=12,
            month=1,
            year=1995,
            hour=12,
            minute=16,
            second=0,
            period="PM",
            place="Mumbai Coords",
            latitude=19.2333,
            longitude=72.2333,
            timezone=5.5,
        ),
        language="en",
    )

    res = calculate_kundli_matching(req)

    # 1. Sanjay Moon: Virgo, Hast; Neha Moon: Taurus, Krittika
    assert res.groom.janam_rasi == "Virgo"
    assert res.groom.janam_nakshatra == "Hasta"
    assert res.bride.janam_rasi == "Taurus"
    assert res.bride.janam_nakshatra == "Krittika"

    # 2. Ashtakoot Milan: exactly 21 / 36 points in client reference report!
    assert res.total_received == 21.0
    assert res.total_out_of == 36.0

    # 3. Dashakoot: exactly 19 / 36 points in client reference report!
    assert res.dashakoot is not None
    assert res.dashakoot.total_received == 19.0
    assert res.dashakoot.total_out_of == 36.0

    # 4. Avakahada comparison attributes
    attr_map = {item.attribute: (item.male, item.female) for item in res.avakahada_comparison}
    assert attr_map["Varna"] == ("Vaishya", "Vaishya")
    assert attr_map["Vashya"] == ("Manava", "Chatushpada")
    assert attr_map["Gan"] == ("Deva", "Rakshasa")
    assert attr_map["Nadi"] == ("Adi", "Antya")
    assert attr_map["Tatva"] == ("Earth", "Earth")
    assert attr_map["Name Alphabet"] == ("Poo", "E")  # Krittika pada 4

    # 5. Dosha cancellations: Bhakoot dosha cancelled due to friendly sign lords Mercury & Venus
    bhakoot_canc = next(c for c in res.cancellations if c.dosha_name == "Bhakoot Dosha")
    assert bhakoot_canc.is_present is True
    assert bhakoot_canc.is_cancelled is True

    # 6. Quad Charts present
    assert res.groom_charts is not None
    assert len(res.groom_charts.d1_planets) == 10
    assert len(res.groom_charts.d9_planets) == 10

