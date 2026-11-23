"""Tests for Annual Lal Kitab Varshphal Report persistence and cryptographic verification."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_annual_report_generation_and_verification(client: AsyncClient):
    # 1. Generate an annual report
    gen_payload = {
        "date_of_birth": "1994-05-18",
        "time_of_birth": "14:30",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "timezone": 5.5,
        "city_name": "Kolkata",
        "client_name": "Siddhartha Ray",
        "target_year": 2026,
        "language": "bn",
        "primary_focus": "finance",
    }
    res_gen = await client.post("/api/v1/astrology/horoscope/annual-lal-kitab", json=gen_payload)
    assert res_gen.status_code == 200
    gen_data = res_gen.json()["data"]
    report_id = gen_data["report_id"]
    assert report_id.startswith("ASTRA-LK-2026-")
    assert gen_data["target_year"] == 2026
    assert gen_data["digital_seal"]["authenticity_hash"].startswith("SHA256-")

    # 2. Verify the generated report via verification route
    res_verify = await client.get(f"/api/v1/astrology/annual-report/verify/{report_id}")
    assert res_verify.status_code == 200
    verify_data = res_verify.json()["data"]
    assert verify_data["is_valid"] is True
    assert verify_data["status"] == "verified"
    assert verify_data["report_id"] == report_id
    assert verify_data["target_year"] == 2026
    assert verify_data["client_name"] == "Siddhartha Ray"
    assert verify_data["city_name"] == "Kolkata"
    assert "digital_seal" in verify_data

    # 3. Verify via alias route
    res_verify_alias = await client.get(f"/api/v1/astrology/horoscope/annual-report/verify/{report_id}")
    assert res_verify_alias.status_code == 200
    assert res_verify_alias.json()["data"]["is_valid"] is True


@pytest.mark.asyncio
async def test_annual_report_fallback_cryptographic_verification(client: AsyncClient):
    # Standard token format not in DB
    dummy_id = "ASTRA-LK-2027-F7E6D5C4B3"
    res = await client.get(f"/api/v1/astrology/annual-report/verify/{dummy_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is True
    assert data["status"] == "verified"
    assert data["report_id"] == dummy_id
    assert data["target_year"] == 2027


@pytest.mark.asyncio
async def test_annual_report_invalid_id(client: AsyncClient):
    res = await client.get("/api/v1/astrology/annual-report/verify/totally-invalid-id-xyz")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert body["data"]["is_valid"] is False
    assert body["data"]["status"] == "invalid"

