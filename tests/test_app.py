"""Setup smoke test — no database needed."""

from app.core.config import settings
from app.main import create_app


def test_app_builds_and_exposes_health() -> None:
    spec = create_app().openapi()
    assert f"{settings.API_V1_PREFIX}/health" in spec["paths"]
    assert f"{settings.API_V1_PREFIX}/ping" in spec["paths"]


def test_allowed_origins_parsed_as_a_list() -> None:
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert all(isinstance(origin, str) for origin in settings.ALLOWED_ORIGINS)
