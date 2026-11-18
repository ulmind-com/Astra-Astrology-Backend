"""Tests for Vedic Festival Calendar dynamic calculation service and endpoints."""

from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.astrology.festival_calculator import (
    calculate_festivals_for_year,
    get_festival_calendar,
    get_upcoming_festivals,
)


def test_festival_calculation_2026():
    """Verify dynamic calculation of 2026 festivals via Swiss Ephemeris."""
    festivals = calculate_festivals_for_year(2026)
    assert len(festivals) >= 15

    fest_ids = {f.id for f in festivals}
    assert "makar-sankranti" in fest_ids
    assert "vasant-panchami" in fest_ids
    assert "maha-shivaratri" in fest_ids
    assert "holi" in fest_ids
    assert "chaitra-navratri" in fest_ids
    assert "pohela-boishakh" in fest_ids
    assert "durga-puja" in fest_ids
    assert "diwali" in fest_ids

    # Check dates are in chronological order
    dates = [f.date for f in festivals]
    assert dates == sorted(dates)


def test_festival_calculation_2027():
    """Verify that 2027 festivals are automatically calculated with 2027 dates."""
    festivals = calculate_festivals_for_year(2027)
    assert len(festivals) >= 15

    # Check that all dates fall in 2027
    for f in festivals:
        d = date.fromisoformat(f.date)
        assert d.year == 2027 or (d.month == 1 and d.year == 2028)


def test_upcoming_festivals_relative_to_november_2026():
    """Critical user bug test: On Nov 19, 2026, upcoming festival MUST NOT be Makar Sankranti 2026 (past)."""
    ref_date = date(2026, 11, 19)

    calendar = get_festival_calendar(2026, ref_date=ref_date)
    assert calendar.next_upcoming is not None

    # Next upcoming must be on or after 2026-11-19
    next_date = date.fromisoformat(calendar.next_upcoming.date)
    assert next_date >= ref_date, f"Expected next upcoming >= {ref_date}, but got {next_date}"
    assert calendar.next_upcoming.days_remaining >= 0

    # Ensure get_upcoming_festivals returns future dates
    upcoming = get_upcoming_festivals(ref_date=ref_date, limit=10)
    assert len(upcoming) > 0
    for u in upcoming:
        u_date = date.fromisoformat(u.date)
        assert u_date >= ref_date
        assert u.days_remaining >= 0


@pytest.mark.asyncio
async def test_festivals_api_endpoints():
    """Test public GET /api/v1/astrology/festivals and /festivals/upcoming endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Full year calendar
        resp = await client.get("/api/v1/astrology/festivals?year=2026&ref_date=2026-11-19")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["year"] == 2026
        assert data["total_count"] >= 15
        assert data["next_upcoming"] is not None
        assert date.fromisoformat(data["next_upcoming"]["date"]) >= date(2026, 11, 19)

        # 2. Upcoming festivals endpoint
        resp_up = await client.get("/api/v1/astrology/festivals/upcoming?ref_date=2026-11-19&limit=5")
        assert resp_up.status_code == 200
        up_data = resp_up.json()["data"]
        assert len(up_data) == 5
        for item in up_data:
            assert date.fromisoformat(item["date"]) >= date(2026, 11, 19)
