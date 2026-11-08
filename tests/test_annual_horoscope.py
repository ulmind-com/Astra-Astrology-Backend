"""Unit & Integration Tests for 1-Year Annual Horoscope & Lal Kitab Varshphal Engine."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.astrology.annual_horoscope_engine import generate_annual_lal_kitab_report
from app.services.astrology.lal_kitab_data import (
    get_combination,
    get_special_remedy,
    get_all_special_remedies,
    get_gomti_chakra_remedies,
    LAL_KITAB_COMBINATIONS,
    SPECIAL_MAHAUPAY,
)


def test_lal_kitab_combinations_count():
    """Verify that all 108 Graha-House combinations and 8 special sections exist."""
    assert len(LAL_KITAB_COMBINATIONS) == 108
    assert len(SPECIAL_MAHAUPAY) == 8


def test_lal_kitab_multilingual_remedies():
    """Verify authentic Lal Kitab remedies retrieve correctly in Bengali, Hindi, and English."""
    comb_bn = get_combination("sun", 1, "bn")
    assert comb_bn["planet"] == "sun"
    assert comb_bn["house"] == 1
    assert "সূর্য" in comb_bn["title"]
    assert len(comb_bn["precautions"]) >= 1
    assert len(comb_bn["remedies"]) >= 1

    comb_hi = get_combination("saturn", 8, "hi")
    assert "शनि" in comb_hi["title"]
    assert len(comb_hi["precautions"]) >= 1
    assert len(comb_hi["remedies"]) >= 1

    comb_en = get_combination("jupiter", 11, "en")
    assert "Jupiter" in comb_en["title"]
    assert len(comb_en["remedies"]) >= 1


def test_gomti_chakra_8_remedies():
    """Verify all 8 Gomti chakra remedies are present with problem-remedy pairs."""
    for lang in ["bn", "hi", "en"]:
        gomti = get_gomti_chakra_remedies(lang)
        assert len(gomti) == 8
        for item in gomti:
            assert "problem" in item and len(item["problem"]) > 0
            assert "remedy" in item and len(item["remedy"]) > 0


def test_special_mahaupay_categories():
    """Verify specialized life concern remedies exist with instructions."""
    categories = [
        "debt_removal",
        "blocked_money",
        "relationship_harmony",
        "health_protection",
        "childbirth_progeny",
        "memory_focus",
        "exam_success",
        "gomti_chakra",
    ]
    for cat in categories:
        remedy = get_special_remedy(cat, "bn")
        assert remedy is not None
        assert "title" in remedy and len(remedy["title"]) > 0
        assert len(remedy["items"]) >= 1


def test_annual_horoscope_engine_generation():
    """Verify complete report generation with 6 pillars, 4 quarters, and digital seal."""
    report = generate_annual_lal_kitab_report(
        date_of_birth="1995-05-15",
        time_of_birth="14:30",
        latitude=22.5726,
        longitude=88.3639,
        timezone_offset=5.5,
        city_name="Kolkata",
        client_name="Test Seeker",
        target_year=2026,
        language="bn",
        primary_focus="finance",
    )

    assert report["report_id"].startswith("ASTRA-LK-2026-")
    assert report["target_year"] == 2026
    assert report["language"] == "bn"
    assert 50 <= report["overall_score"] <= 100

    # 6 Life Pillars
    assert len(report["pillars"]) == 6
    pillar_ids = [p["id"] for p in report["pillars"]]
    assert "career" in pillar_ids
    assert "finance" in pillar_ids
    assert "health" in pillar_ids
    assert "love" in pillar_ids
    assert "family" in pillar_ids
    assert "luck" in pillar_ids

    # 4 Quarters
    assert len(report["quarters"]) == 4

    # Varshphal 9 Planets
    assert len(report["varshphal_planets"]) == 9

    # Shubh and Ashubh Phal
    assert len(report["shubh_phal"]) >= 3
    assert len(report["ashubh_phal"]) >= 3

    # Primary Mahaupay & Gomti Chakra
    assert report["primary_mahaupay"] is not None
    assert len(report["gomti_chakra_remedies"]) == 8

    # Royal Digital Seal
    assert "report_id" in report["digital_seal"]
    assert "seal_motto" in report["digital_seal"]
    assert "authenticity_hash" in report["digital_seal"]


@pytest.mark.asyncio
async def test_annual_horoscope_api_endpoint():
    """Verify the POST /api/v1/astrology/horoscope/annual-lal-kitab endpoint works."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "date_of_birth": "1992-08-18",
            "time_of_birth": "10:15",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5,
            "city_name": "New Delhi",
            "target_year": 2026,
            "language": "hi",
            "primary_focus": "career",
        }
        resp = await client.post("/api/v1/astrology/horoscope/annual-lal-kitab", json=payload)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()["data"]
        assert data["target_year"] == 2026
        assert data["language"] == "hi"
        assert len(data["pillars"]) == 6
        assert len(data["gomti_chakra_remedies"]) == 8
