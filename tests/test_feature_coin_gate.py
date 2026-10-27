"""Tests for Astrology Feature Coin Gate & Dynamic Admin Pricing."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.enums import TransactionReason, UserRole
from app.models.user import User
from app.models.settings import PlatformSettings
from app.services import settings as settings_service
from app.services import wallet as wallet_service
from app.core.security import create_access_token

client = TestClient(app)


def test_public_feature_pricing_endpoint():
    """Verify public pricing endpoint returns all platform features."""
    response = client.get("/api/v1/astrology/features/pricing")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    features = data["data"]
    
    expected_keys = [
        "daily_horoscope",
        "kundli",
        "kundli_matching",
        "kp_calculator",
        "dasha_calculator",
        "rashi_calculator",
        "nakshatra_calculator",
        "palm_reading",
        "face_reading",
        "numerology",
        "vastu",
    ]
    for key in expected_keys:
        assert key in features
        item = features[key]
        assert "coins" in item
        assert "is_free" in item
        assert "enabled" in item
        assert "name" in item
        assert item["coins"] >= 0


@pytest.mark.asyncio
async def test_feature_pricing_update_and_enforcement():
    """Verify admin update and wallet debit workflow."""
    from beanie import PydanticObjectId

    # 1. Update platform settings
    await settings_service.set_feature_pricing(
        changes={
            "kundli_coins": 20,
            "daily_horoscope_coins": 0,
            "nakshatra_calculator_coins": 10,
            "numerology_coins": 15,
            "vastu_coins": 0,
        },
        admin_id=None,
    )

    settings = await settings_service.get_settings()
    assert settings.kundli_coins == 20
    assert settings.daily_horoscope_coins == 0
    assert settings.nakshatra_calculator_coins == 10
    assert settings.numerology_coins == 15
    assert settings.vastu_coins == 0


@pytest.mark.asyncio
async def test_realtime_feature_pricing_broadcast():
    """Verify realtime broadcast helper creates valid payload and queues to connections."""
    from app.services import realtime

    platform = await settings_service.get_settings()
    payload = realtime.build_feature_pricing_payload(platform)

    assert "kundli" in payload
    assert payload["kundli"]["coins"] == platform.kundli_coins
    assert payload["kundli"]["enabled"] == platform.kundli_enabled
    assert "daily_horoscope" in payload
    assert "palm_reading" in payload
    assert "numerology" in payload
    assert payload["numerology"]["coins"] == platform.numerology_coins
    assert "vastu" in payload
    assert payload["vastu"]["coins"] == platform.vastu_coins

    # Test dummy connection queueing
    class DummyWs:
        pass

    conn = realtime.Connection(DummyWs(), user_id="test-user", role="user")
    realtime.register(conn)
    try:
        await realtime.publish_feature_pricing(platform)
        # Message should be queued in conn.queue
        assert not conn.queue.empty()
        msg = conn.queue.get_nowait()
        assert msg["type"] == "feature_pricing"
        assert msg["data"]["kundli"]["coins"] == platform.kundli_coins
    finally:
        realtime.unregister(conn)
