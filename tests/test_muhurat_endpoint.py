"""Tests for Vedic Muhurat calculation endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_muhurat_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        params = {
            "date": "2026-11-23",
            "latitude": 22.5726,
            "longitude": 88.3639,
            "timezone": 5.5,
            "language": "bn",
        }
        res = await client.get("/api/v1/astrology/muhurat", params=params)
        assert res.status_code == 200
        data = res.json()["data"]

        # Check core attributes
        assert data["date"] == "2026-11-23"
        assert "sunrise" in data
        assert "sunset" in data
        assert "solar_noon" in data
        assert data["day_duration_hours"] > 0
        assert data["night_duration_hours"] > 0

        # Check core windows
        assert data["abhijit"]["quality"] == "super_auspicious"
        assert data["rahu_kaal"]["quality"] == "inauspicious"
        assert data["yamaganda"]["quality"] == "inauspicious"
        assert data["gulika_kaal"]["quality"] == "remedial"
        assert data["brahma_muhurat"]["quality"] == "super_auspicious"

        # Check Choghadiyas (8 day + 8 night = 16)
        assert len(data["choghadiyas"]) == 16
        day_choghadiyas = [c for c in data["choghadiyas"] if c["period_type"] == "day"]
        night_choghadiyas = [c for c in data["choghadiyas"] if c["period_type"] == "night"]
        assert len(day_choghadiyas) == 8
        assert len(night_choghadiyas) == 8

        # Check Horas (24 total)
        assert len(data["horas"]) == 24

        # Check Milestone Guidance
        assert len(data["milestone_muhurats"]) >= 8
        vivah = next(m for m in data["milestone_muhurats"] if m["id"] == "vivah")
        assert "name" in vivah
        assert vivah["today_compatibility"] in ("Favorable", "Moderate", "Avoid")


@pytest.mark.asyncio
async def test_post_muhurat_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "date": "2026-04-14",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": 5.5,
            "language": "hi",
        }
        res = await client.post("/api/v1/astrology/muhurat", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["date"] == "2026-04-14"
        assert len(data["core_windows"]) >= 6
