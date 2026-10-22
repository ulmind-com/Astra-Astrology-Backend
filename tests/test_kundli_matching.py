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
    assert "forecast" in data["data"]
    assert data["data"]["forecast"]["ideal_marriage_age_groom"] != ""
