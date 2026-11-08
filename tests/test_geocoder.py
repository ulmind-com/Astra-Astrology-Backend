import pytest
from httpx import AsyncClient
from app.services.astrology.geocoder import geocode_place


@pytest.mark.asyncio
async def test_geocode_deulia():
    results = await geocode_place("Deulia")
    assert len(results) > 0
    first = results[0]
    assert "Deulia" in first["place"]
    assert first["timezone_name"] == "Asia/Kolkata"
    assert first["timezone"] == 5.5
    assert first["latitude"] > 20.0
    assert first["longitude"] > 85.0


@pytest.mark.asyncio
async def test_geocode_kolaghat():
    results = await geocode_place("Kolaghat")
    assert len(results) > 0
    first = results[0]
    assert "Kolaghat" in first["place"]
    assert first["timezone_name"] == "Asia/Kolkata"
    assert first["timezone"] == 5.5


@pytest.mark.asyncio
async def test_geo_search_api_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/astrology/geo-search", params={"q": "Deulia"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert len(data) > 0
    assert any("Deulia" in item["place"] for item in data)

