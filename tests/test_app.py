"""Setup smoke tests.

The health tests point the app at a dead database on purpose: the monitoring
endpoints must answer 200 regardless, which is what keeps uptime checks green.
"""

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import create_app


def test_app_builds_and_exposes_health() -> None:
    spec = create_app().openapi()
    assert f"{settings.API_V1_PREFIX}/health" in spec["paths"]
    assert f"{settings.API_V1_PREFIX}/ping" in spec["paths"]


def test_allowed_origins_parsed_as_a_list() -> None:
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert all(isinstance(origin, str) for origin in settings.ALLOWED_ORIGINS)


@pytest.fixture
async def offline_client(monkeypatch: pytest.MonkeyPatch):
    """A client whose database is unreachable."""
    monkeypatch.setattr(settings, "MONGODB_URI", "mongodb://127.0.0.1:59999/")
    monkeypatch.setattr(settings, "MONGODB_CONNECT_TIMEOUT_MS", 300)
    monkeypatch.setattr(settings, "HEALTH_DB_TIMEOUT_SECONDS", 0.5)

    app = create_app()
    async with LifespanManager(app, startup_timeout=30, shutdown_timeout=30):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.mark.parametrize("path", ["/health", "/ping"])
@pytest.mark.parametrize("method", ["GET", "HEAD"])
async def test_monitoring_endpoints_answer_200_even_without_a_database(
    offline_client: AsyncClient, path: str, method: str
) -> None:
    response = await offline_client.request(method, f"{settings.API_V1_PREFIX}{path}")

    assert response.status_code == 200
    assert response.headers["cache-control"].startswith("no-store")


async def test_health_reports_degraded_without_a_database(
    offline_client: AsyncClient,
) -> None:
    response = await offline_client.get(f"{settings.API_V1_PREFIX}/health")
    data = response.json()["data"]

    assert data["status"] == "degraded"
    assert data["database"] == "disconnected"
    assert data["services"]["mongodb"] is False


def test_allow_test_razorpay_flag_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production refuses rzp_test_ by default, unless ALLOW_TEST_RAZORPAY=True."""
    from app.main import _check_config

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "OTP_DEV_MODE", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "a" * 32)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "b" * 32)
    monkeypatch.setattr(settings, "MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setattr(settings, "FIREBASE_REQUIRED", False)
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_dummy_key")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_test_123456")

    monkeypatch.setattr(settings, "ALLOW_TEST_RAZORPAY", False)
    with pytest.raises(RuntimeError, match="bad configuration value"):
        _check_config()

    monkeypatch.setattr(settings, "ALLOW_TEST_RAZORPAY", True)
    _check_config()  # Should pass with warning only
