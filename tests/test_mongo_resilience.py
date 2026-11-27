"""Tests for MongoDB pool resilience, bounded retry budget, 503s, and Sentry filtering."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pymongo.errors import AutoReconnect, OperationFailure, WaitQueueTimeoutError

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middleware
from app.core.sentry import _before_send
from app.db import mongodb


@pytest.mark.asyncio
async def test_connect_to_mongo_enforces_resilient_pool_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """connect_to_mongo must respect minPoolSize=0 and cap idle/socket/connect timeouts."""
    monkeypatch.setattr(settings, "MONGODB_MIN_POOL_SIZE", 0)
    monkeypatch.setattr(settings, "MONGODB_MAX_POOL_SIZE", 100)
    monkeypatch.setattr(settings, "MONGODB_SOCKET_TIMEOUT_MS", 45_000)
    monkeypatch.setattr(settings, "MONGODB_MAX_IDLE_TIME_MS", 300_000)
    monkeypatch.setattr(settings, "MONGODB_CONNECT_TIMEOUT_MS", 10_000)

    captured_kwargs: dict = {}

    class FakeAdmin:
        command = AsyncMock(return_value={"ok": 1})

    class FakeClient:
        def __init__(self, uri: str, **kwargs):
            captured_kwargs.update(kwargs)
            self.admin = FakeAdmin()

        def get_database(self, name: str, **kwargs):
            return MagicMock()

        async def close(self) -> None:
            pass

    monkeypatch.setattr(mongodb, "AsyncMongoClient", FakeClient)
    monkeypatch.setattr(mongodb, "_init_models", AsyncMock())

    ok = await mongodb.connect_to_mongo()
    assert ok is True
    assert captured_kwargs["minPoolSize"] == 0
    assert captured_kwargs["maxPoolSize"] <= 50
    assert captured_kwargs["socketTimeoutMS"] <= 15_000
    assert captured_kwargs["maxIdleTimeMS"] <= 60_000
    assert captured_kwargs["connectTimeoutMS"] <= 6_000

    await mongodb.close_mongo_connection()


@pytest.mark.asyncio
async def test_with_mongo_retry_recovers_fast_and_respects_time_budget() -> None:
    """Transient errors retry with budget; exhausted budget fails fast without cascading stalls."""
    calls = 0

    async def flaky_ok() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise AutoReconnect("connection reset by peer")
        return "recovered"

    with patch("asyncio.sleep", new_callable=AsyncMock):
        res = await mongodb.with_mongo_retry(flaky_ok, max_retries=2, delay=0.01, total_budget=5.0)
    assert res == "recovered"
    assert calls == 2

    # When total_budget is 0, it must NOT stack multiple retries
    fail_calls = 0

    async def slow_fail() -> str:
        nonlocal fail_calls
        fail_calls += 1
        raise WaitQueueTimeoutError("Timed out checking out a connection from pool")

    with pytest.raises(WaitQueueTimeoutError):
        await mongodb.with_mongo_retry(slow_fail, max_retries=3, delay=0.01, total_budget=0.0)
    assert fail_calls == 1


@pytest.mark.asyncio
async def test_heal_connection_acquires_topology_lock() -> None:
    """_async_heal_topology must hold topology._lock when invoking _request_check_all."""
    events: list[str] = []

    class FakeLock:
        async def __aenter__(self):
            events.append("lock_enter")
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            events.append("lock_exit")

    class FakeTopology:
        def __init__(self):
            self._lock = FakeLock()

        def _request_check_all(self):
            events.append("check_all")

    fake_client = MagicMock()
    fake_client._topology = FakeTopology()

    await mongodb._async_heal_topology(fake_client)
    assert events == ["lock_enter", "check_all", "lock_exit"]


@pytest.mark.asyncio
async def test_wait_queue_timeout_returns_503_and_does_not_log_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """WaitQueueTimeoutError and 503 responses must log at WARNING, never ERROR (no Sentry spam)."""
    app = FastAPI()
    register_middleware(app)
    register_exception_handlers(app)

    @app.get("/pool-timeout")
    async def pool_timeout():
        raise WaitQueueTimeoutError(
            "Timed out checking out a connection from pool. maxPoolSize: 50, timeout: 5.0"
        )

    @app.get("/bad-query")
    async def bad_query():
        raise OperationFailure("bad query syntax", code=2)

    logged_errors: list[str] = []
    logged_warnings: list[str] = []

    from app.core import exceptions as exc_mod
    from app.core import middleware as mw_mod

    monkeypatch.setattr(
        exc_mod.logger, "error", lambda msg, *a, **kw: logged_errors.append(str(msg))
    )
    monkeypatch.setattr(
        exc_mod.logger, "warning", lambda msg, *a, **kw: logged_warnings.append(str(msg))
    )
    monkeypatch.setattr(
        mw_mod.logger,
        "bind",
        lambda **kw: MagicMock(
            error=lambda msg, *a: logged_errors.append(str(msg)),
            warning=lambda msg, *a: logged_warnings.append(str(msg)),
            info=lambda msg, *a: None,
        ),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get("/pool-timeout")
        assert r1.status_code == 503
        assert r1.headers.get("retry-after") == "2"
        assert r1.json()["error_code"] == "database_unavailable"
        assert len(logged_errors) == 0
        assert len(logged_warnings) >= 2  # exception handler + middleware 503 access log

        # Non-transient OperationFailure should still log at ERROR in exceptions handler
        r2 = await client.get("/bad-query")
        assert r2.status_code == 503
        assert len(logged_errors) == 1


def test_sentry_before_send_suppresses_pymongo_background_cancellations() -> None:
    """_before_send drops PyMongo _OperationCancelled & background executor log noise."""

    class _OperationCancelled(Exception):
        pass

    exc = _OperationCancelled("operation cancelled")
    event_exc = {
        "logger": "logging",
        "logentry": {"message": "MongoClient background task encountered an error:"},
        "exception": {
            "values": [
                {
                    "type": "_OperationCancelled",
                    "value": "operation cancelled",
                    "module": "pymongo.network_layer",
                }
            ]
        },
    }
    assert _before_send(event_exc, {"exc_info": (_OperationCancelled, exc, None)}) is None

    event_pymongo_logger = {
        "logger": "pymongo.client",
        "logentry": {"message": "some background noise"},
    }
    assert _before_send(event_pymongo_logger, {}) is None

    # Legitimate app exception must still pass through
    legit_event = {
        "logger": "app.api",
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "unexpected value",
                    "module": "app.services.billing",
                }
            ]
        },
    }
    assert _before_send(legit_event, {}) is legit_event
