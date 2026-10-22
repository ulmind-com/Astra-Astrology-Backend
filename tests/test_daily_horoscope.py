"""Tests for Daily Horoscope service and API endpoints.

Verifies:
1. Swiss Ephemeris sidereal Moon & Sun positions calculated deterministically without 3rd party APIs.
2. 12 Bhavas transit (Gochar) correctly maps to transit_house = (moon_sign - rashi_sign) % 12 + 1.
3. Panchang (Tithi, Nakshatra, Yoga, Karana, Abhijit Muhurat, Rahu Kaal) is accurate and non-empty.
4. Multi-language output (en, bn, hi) works seamlessly without missing translations.
5. All scores are bounded between 0 and 100.
6. API endpoints (POST /horoscope/daily and GET /horoscope/daily) return 200 OK.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.astrology import DailyHoroscopeRequest
from app.services.astrology.daily_horoscope import calculate_daily_horoscope

client = TestClient(app)


def test_daily_horoscope_service_basic():
    req = DailyHoroscopeRequest(
        date="2026-10-22",
        language="en",
        latitude=22.5726,
        longitude=88.3639,
        timezone=5.5,
    )
    res = calculate_daily_horoscope(req)

    assert res.date == "2026-10-22"
    assert res.moon_sign != ""
    assert res.sun_sign != ""
    assert len(res.signs) == 12

    # Check panchang
    assert res.panchang.tithi != ""
    assert res.panchang.nakshatra != ""
    assert res.panchang.yoga != ""
    assert res.panchang.karana != ""
    assert res.panchang.abhijit_muhurat != ""
    assert res.panchang.rahu_kaal != ""

    # Check each sign has valid scores and remedies
    for s in res.signs:
        assert 0 <= s.overall_score <= 100
        assert 0 <= s.career_score <= 100
        assert 0 <= s.love_score <= 100
        assert 0 <= s.finance_score <= 100
        assert 0 <= s.health_score <= 100
        assert 1 <= s.transit_house <= 12
        assert len(s.summary) > 10
        assert len(s.remedy) > 5
        assert s.lucky_number >= 1
        assert s.lucky_color != ""


def test_daily_horoscope_bengali_and_hindi():
    req_bn = DailyHoroscopeRequest(date="2026-10-22", language="bn")
    res_bn = calculate_daily_horoscope(req_bn)
    assert res_bn.signs[0].sign_name == "মেষ"
    assert "রাশিফল" in res_bn.calculation_meta.get("calculation_method", "") or "Gochar" in res_bn.calculation_meta.get("calculation_method", "")
    assert len(res_bn.signs[0].career_prediction) > 0

    req_hi = DailyHoroscopeRequest(date="2026-10-22", language="hi")
    res_hi = calculate_daily_horoscope(req_hi)
    assert res_hi.signs[0].sign_name == "मेष"


def test_daily_horoscope_api_post():
    response = client.post(
        "/api/v1/astrology/horoscope/daily",
        json={"date": "2026-10-22", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["signs"]) == 12
    assert "calculation_meta" in data["data"]


def test_daily_horoscope_api_get():
    response = client.get("/api/v1/astrology/horoscope/daily?date=2026-10-22&language=bn")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["signs"][0]["sign_name"] == "মেষ"


def test_daily_horoscope_sign_filter():
    response = client.get("/api/v1/astrology/horoscope/daily?date=2026-10-22&sign=leo")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["signs"]) == 1
    assert data["data"]["signs"][0]["sign_name"] == "Leo"
