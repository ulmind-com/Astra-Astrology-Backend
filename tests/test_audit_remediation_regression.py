"""Regression test suite for audit remediation fixes (AUD-001, AUD-002, AUD-003, AUD-008)."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.rate_limit import rate_limiter
from app.main import app
from app.models.ai_astrologer import AIChatSession
from app.models.astrologer import Astrologer


def test_astrologer_model_indexes_remediation():
    """Verify AUD-001: Astrologer model includes availability and rating compound indexes."""
    indexes = Astrologer.Settings.indexes
    index_reprs = [str(idx) for idx in indexes]

    # Verify compound availability and rating sort indexes exist
    has_availability_index = any("availability.is_online" in s for s in index_reprs)
    has_rating_index = any("rating.average" in s for s in index_reprs)
    has_user_unique = any("astrologer_user_unique" in s or "user_id" in s for s in index_reprs)
    has_slug_unique = any("astrologer_slug_unique" in s or "slug" in s for s in index_reprs)

    assert has_availability_index, "Astrologer model must have compound availability index"
    assert has_rating_index, "Astrologer model must have rating sort index"
    assert has_user_unique, "Astrologer model must have user_id index"
    assert has_slug_unique, "Astrologer model must have slug index"


def test_ai_chat_session_ttl_index_remediation():
    """Verify AUD-008: AIChatSession includes expireAfterSeconds TTL index."""
    indexes = AIChatSession.Settings.indexes
    ttl_index_found = False
    for idx in indexes:
        doc = getattr(idx, "document", idx)
        if isinstance(doc, dict) and "expireAfterSeconds" in doc:
            ttl_index_found = True
            assert doc["expireAfterSeconds"] == 7776000

    assert ttl_index_found, "AIChatSession must define expireAfterSeconds TTL index on updated_at"


def test_production_config_debug_safety_remediation():
    """Verify AUD-003: Setting APP_ENV='production' automatically enforces DEBUG=False."""
    prod_settings = Settings(APP_ENV="production", DEBUG=True)
    assert prod_settings.DEBUG is False, "Production settings must force DEBUG to False to prevent stacktrace leaks"


@pytest.mark.asyncio
async def test_auth_rate_limiting_enforcement():
    """Verify AUD-002: Rapid requests to auth endpoints trigger HTTP 429 Too Many Requests."""
    test_ip = "198.51.100.42"
    rate_limiter.reset_for_ip(test_ip)

    from datetime import UTC, datetime
    from types import SimpleNamespace

    now = datetime.now(UTC)
    fake_otp = SimpleNamespace(
        identifier="attacker@example.com",
        expires_at=now,
        resend_available_at=now,
    )
    transport = ASGITransport(app=app)
    with patch(
        "app.api.v1.auth.auth_service.request_password_reset",
        AsyncMock(return_value=(fake_otp, "123456")),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"x-forwarded-for": test_ip}

            # Route /api/v1/auth/password/forgot has rule: max 5 requests per 60s
            status_codes = []
            for _ in range(6):
                resp = await client.post(
                    "/api/v1/auth/password/forgot",
                    json={"email": "attacker@example.com"},
                    headers=headers,
                )
                status_codes.append(resp.status_code)

            # First 5 should not be 429 (they will be 404 or 200 depending on DB state)
            assert status_codes[0] != 429
            # The 6th request must be throttled with HTTP 429
            assert status_codes[-1] == 429, f"6th request was {status_codes[-1]}, expected 429"

            # Verify 429 response structure and headers
            last_resp = await client.post(
                "/api/v1/auth/password/forgot",
                json={"email": "attacker@example.com"},
                headers=headers,
            )
            assert last_resp.status_code == 429
            assert "Retry-After" in last_resp.headers
            data = last_resp.json()
            assert data["success"] is False
            assert data["error_code"] == "rate_limit_exceeded"

            # Spoofed bypass header must NOT bypass rate limiting
            bypass_headers = {"x-forwarded-for": test_ip, "x-bypass-rate-limit": "true"}
            bypass_resp = await client.post(
                "/api/v1/auth/password/forgot",
                json={"email": "admin@example.com"},
                headers=bypass_headers,
            )
            assert bypass_resp.status_code == 429, "x-bypass-rate-limit must never bypass rate limits"

    # Cleanup test IP
    rate_limiter.reset_for_ip(test_ip)
