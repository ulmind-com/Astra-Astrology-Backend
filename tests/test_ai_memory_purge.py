"""Tests for AI Astrologer cosmic memory purge endpoint (DELETE /ai-astrologer/memory)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.models.ai_astrologer import AIChatSession, AIUserMemory
from app.models.user import User


@pytest.mark.asyncio
async def test_purge_memory_no_credentials_rejected(client: AsyncClient):
    """Calling purge without session_id and without auth raises 401 Unauthorized."""
    res = await client.delete("/api/v1/ai-astrologer/memory")
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert "Sign in or provide a session ID" in data["message"]


@pytest.mark.asyncio
async def test_purge_memory_guest_session(client: AsyncClient):
    """Guest session deletion purges the session record cleanly."""
    sess_id = f"test_guest_sess_{int(datetime.now(timezone.utc).timestamp())}"
    sess = AIChatSession(
        session_id=sess_id,
        user_id=None,
        title="Sample Consultation",
        messages=[{"role": "user", "content": "What is my rashi?"}],
    )
    await sess.insert()

    # Verify session exists
    found = await AIChatSession.find_one(AIChatSession.session_id == sess_id)
    assert found is not None

    # Call purge endpoint
    res = await client.delete(f"/api/v1/ai-astrologer/memory?session_id={sess_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["cleared"] is True
    assert data["data"]["deleted_sessions"] >= 1

    # Verify session was erased from DB
    purged = await AIChatSession.find_one(AIChatSession.session_id == sess_id)
    assert purged is None


@pytest.mark.asyncio
async def test_purge_memory_alias_route(client: AsyncClient):
    """Alias /ai-chat/memory works identically."""
    sess_id = f"test_alias_sess_{int(datetime.now(timezone.utc).timestamp())}"
    sess = AIChatSession(
        session_id=sess_id,
        user_id=None,
        title="Alias Consultation",
        messages=[],
    )
    await sess.insert()

    res = await client.delete(f"/api/v1/ai-chat/memory?session_id={sess_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["cleared"] is True
