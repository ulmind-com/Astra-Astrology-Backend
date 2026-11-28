"""Tests for endpoints defined in App and newly implemented in Backend."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_panchang_daily_endpoint(client: AsyncClient):
    params = {
        "date": "2026-11-23",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "timezone": 5.5,
        "language": "bn",
    }
    res = await client.get("/api/v1/astrology/panchang/daily", params=params)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "tithi" in data
    assert "nakshatra" in data
    assert "yoga" in data
    assert "karana" in data
    assert "sunrise" in data
    assert "sunset" in data
    assert "abhijit_muhurat" in data
    assert "rahu_kaal" in data


@pytest.mark.asyncio
async def test_purohit_catalog_not_found_clean_404(client: AsyncClient):
    res = await client.get("/api/v1/purohits/non-existent-purohit-12345/catalog")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_shop_order_track_not_found(client: AsyncClient):
    res = await client.get("/api/v1/shop/orders/NONEXISTENT999/track")
    assert res.status_code == 404
