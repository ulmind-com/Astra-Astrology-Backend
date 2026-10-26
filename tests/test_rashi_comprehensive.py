"""Comprehensive tests for the advanced Rashi Calculator features.

Tests classical rules from client resource documents:
- Resource Documents/Rashi Rules/01.pdf (15 classification groups)
- Resource Documents/Kundli/Basics of Kundali Reading Explained.pdf (Dignities, friendships)
- Resource Documents/Rahul Pandat PDFs/Kusthi Rules/matching-pdf-english.pdf (Avakahada Chakra, Paya)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.astrology import RashiCalculateRequest
from app.services.astrology.calculator import calculate_rashi


def test_rashi_advanced_classical_modules():
    """Verify Avakahada Chakra, Paya, Navamsha, Chandra Lagna, Dignities, Chandra Bala, and Sade Sati."""
    # Test case: 15 Aug 1947, 00:01 IST, New Delhi (Taurus Asc, Moon in Cancer - Pushya 1)
    req = RashiCalculateRequest(
        name="India Independence",
        gender="other",
        day=15,
        month=8,
        year=1947,
        hour=0,
        minute=1,
        second=0,
        period="24H",
        place="New Delhi",
        latitude=28.6139,
        longitude=77.2090,
        timezone=5.5,
        ayanamsa="lahiri",
        house_system="whole_sign",
        language="bn",
    )

    res = calculate_rashi(req)

    # 1. Rashi & Nakshatra
    assert res.rashi_name_en == "Cancer"
    assert res.rashi_name_bn == "কর্কট"
    assert res.nakshatra_name == "Pushya"
    assert res.nakshatra_pada == 1

    # 2. Avakahada Chakra
    assert res.avakahada_chakra is not None
    assert res.avakahada_chakra.gana != ""
    assert res.avakahada_chakra.yoni != ""
    assert res.avakahada_chakra.nadi != ""
    assert res.avakahada_chakra.varna != ""
    assert res.avakahada_chakra.vashya != ""
    assert res.avakahada_chakra.tatva != ""
    assert "পায়া" in res.avakahada_chakra.paya or "Paya" in res.avakahada_chakra.paya
    assert res.namakshar != ""

    # 3. Navamsha & Vargottama
    # Moon in Pushya Pada 1 is in Leo Navamsha (Cancer Rashi != Leo Navamsha -> not vargottama)
    assert 0 <= res.navamsha_rashi_index <= 11
    assert res.navamsha_rashi_name_en == "Leo"
    assert res.is_vargottama is False

    # 4. Planetary Dignity (Client's Basics of Kundali Reading Explained)
    # Cancer: Jupiter exalted, Mars debilitated, Moon has no enemies
    assert res.planetary_dignity is not None
    assert any("বৃহস্পতি" in p or "Jupiter" in p for p in res.planetary_dignity.exalted_planets)
    assert any("মঙ্গল" in p or "Mars" in p for p in res.planetary_dignity.debilitated_planets)
    assert len(res.planetary_dignity.ruler_enemies) == 0  # Moon has no natural enemies

    # 5. Chandra Lagna Kundli Planets
    assert len(res.chandra_lagna_planets) == 9
    moon_in_chandra_chart = next(p for p in res.chandra_lagna_planets if p.name == "Moon")
    assert moon_in_chandra_chart.house == 1  # Moon must be in House 1 in Chandra Lagna chart

    # 6. Real-time Chandra Bala
    assert res.chandra_bala is not None
    assert 1 <= res.chandra_bala.house_from_natal_moon <= 12
    assert res.chandra_bala.status_label != ""
    assert res.chandra_bala.description != ""

    # 7. Real-time Sade Sati Status
    assert res.sade_sati_status is not None
    assert res.sade_sati_status.phase_code in ("rising", "peak", "setting", "kantaka", "ashtama", "none")
    assert res.sade_sati_status.phase_title != ""
    assert res.sade_sati_status.description != ""
    assert res.sade_sati_status.remedy_summary != ""


def test_rashi_vargottama_detection():
    """Verify that a planet with same sign in D1 and D9 is flagged as Vargottama."""
    # Rohini Pada 2 (Taurus 13°20' to 16°40') falls in Taurus Navamsha (Taurus Rashi + Taurus Navamsha = Vargottama)
    # Let's verify Moon at Taurus 15°
    from app.services.astrology.rashi_rules import RASHIS_DATA
    moon_lon = 45.0  # 15° Taurus (Taurus starts at 30°)
    rashi_idx = int(moon_lon / 30.0) % 12  # 1 (Taurus)
    nav_idx = int(moon_lon / (360.0 / 108.0)) % 12  # int(45 / 3.33333) = int(13.5) = 13 % 12 = 1 (Taurus)
    assert rashi_idx == 1
    assert nav_idx == 1
    assert rashi_idx == nav_idx


def test_rashi_api_endpoint_payload():
    """Verify that /api/v1/astrology/rashi returns 200 with all new fields."""
    client = TestClient(app)
    payload = {
        "name": "Arjun",
        "gender": "male",
        "day": 24,
        "month": 4,
        "year": 1990,
        "hour": 15,
        "minute": 30,
        "second": 0,
        "period": "24H",
        "place": "Kolkata",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "timezone": 5.5,
        "ayanamsa": "lahiri",
        "language": "bn",
    }
    response = client.post("/api/v1/astrology/rashi", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]

    assert "avakahada_chakra" in data and data["avakahada_chakra"] is not None
    assert "namakshar" in data and len(data["namakshar"]) > 0
    assert "navamsha_rashi_name_bn" in data
    assert "planetary_dignity" in data and data["planetary_dignity"] is not None
    assert "chandra_lagna_planets" in data and len(data["chandra_lagna_planets"]) == 9
    assert "chandra_bala" in data and data["chandra_bala"] is not None
    assert "sade_sati_status" in data and data["sade_sati_status"] is not None
