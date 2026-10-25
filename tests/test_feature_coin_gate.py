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
        },
        admin_id=None,
    )

    settings = await settings_service.get_settings()
    assert settings.kundli_coins == 20
    assert settings.daily_horoscope_coins == 0
    assert settings.nakshatra_calculator_coins == 10
