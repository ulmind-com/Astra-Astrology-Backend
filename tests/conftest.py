"""Test fixtures.

The database-backed tests need a reachable `MONGODB_URI`; they are skipped when
one is not configured. Firebase is replaced by an in-memory double, so the
sync and rollback behaviour can be exercised without real credentials.
"""

import os
import uuid
from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.services import firebase as firebase_module
from app.services.firebase import FirebaseUser

# Disable Sentry and OpenTelemetry during automated tests to avoid polluting
# production monitoring dashboards and consuming monthly event quotas.
os.environ["SENTRY_DSN"] = ""
settings.SENTRY_DSN = ""
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""
settings.OTEL_EXPORTER_OTLP_ENDPOINT = ""

# A name of this run's own. Two pytest sessions against one shared database
# drop each other's data between tests, and the failures that causes look like
# real bugs in whatever happened to be running — which costs far more time than
# the stray databases this leaves behind.
TEST_DB_NAME = f"astra_astrology_pytest_{os.getpid()}"


def _mongo_uri() -> str | None:
    return os.environ.get("TEST_MONGODB_URI") or os.environ.get("MONGODB_URI") or None


requires_mongo = pytest.mark.skipif(
    _mongo_uri() is None,
    reason="Set MONGODB_URI (or TEST_MONGODB_URI) to run the database-backed tests.",
)


# --------------------------------------------------------------- firebase double
class FakeFirebase:
    """In-memory stand-in for Firebase Auth."""

    def __init__(self) -> None:
        self.users: dict[str, FirebaseUser] = {}
        self.enabled = True
        self.fail_next_create = False
        self.created_uids: list[str] = []
        self.deleted_uids: list[str] = []

    # -- lookups
    def _by_email(self, email: str) -> FirebaseUser | None:
        email = email.lower()
        return next((u for u in self.users.values() if u.email == email), None)

    async def get_user_by_email(self, email: str) -> FirebaseUser | None:
        return self._by_email(email)

    async def get_user(self, uid: str) -> FirebaseUser | None:
        return self.users.get(uid)

    # -- writes
    async def create_user(
        self,
        *,
        email: str,
        password: str | None = None,
        display_name: str | None = None,
        email_verified: bool = False,
        photo_url: str | None = None,
    ) -> FirebaseUser:
        from app.core.exceptions import ConflictError, ServiceUnavailableError

        if self.fail_next_create:
            self.fail_next_create = False
            raise ServiceUnavailableError("boom", error_code="firebase_unavailable")
        if self._by_email(email):
            raise ConflictError("exists", error_code="email_already_exists")

        uid = f"fb-{uuid.uuid4().hex[:12]}"
        user = FirebaseUser(
            uid=uid,
            email=email.lower(),
            display_name=display_name,
            photo_url=photo_url,
            email_verified=email_verified,
            providers=["password"],
        )
        self.users[uid] = user
        self.created_uids.append(uid)
        return user

    async def update_user(self, uid: str, **kwargs: object) -> FirebaseUser:
        current = self.users[uid]
        self.users[uid] = FirebaseUser(
            uid=uid,
            email=current.email,
            display_name=kwargs.get("display_name", current.display_name),  # type: ignore[arg-type]
            photo_url=kwargs.get("photo_url", current.photo_url),  # type: ignore[arg-type]
            email_verified=bool(kwargs.get("email_verified", current.email_verified)),
            providers=current.providers,
        )
        return self.users[uid]

    async def delete_user(self, uid: str) -> bool:
        self.deleted_uids.append(uid)
        return self.users.pop(uid, None) is not None

    # -- state
    def is_enabled(self) -> bool:
        return self.enabled

    def require_enabled(self) -> None:
        from app.core.exceptions import ServiceUnavailableError

        if not self.enabled and settings.FIREBASE_REQUIRED:
            raise ServiceUnavailableError(
                "Sign-up is temporarily unavailable. Please try again shortly.",
                error_code="firebase_not_configured",
            )

    # -- google sign-in
    def seed_google_user(
        self, email: str, name: str | None = "Google User", picture: str | None = None
    ) -> dict[str, object]:
        """Creates the Firebase user a client-side Google sign-in would, and
        returns the claims `verify_id_token` should produce for it."""
        uid = f"fb-{uuid.uuid4().hex[:12]}"
        self.users[uid] = FirebaseUser(
            uid=uid,
            email=email.lower(),
            display_name=name,
            photo_url=picture,
            email_verified=True,
            providers=["google.com"],
        )
        return {
            "uid": uid,
            "sub": uid,
            "email": email.lower(),
            "name": name,
            "picture": picture,
            "email_verified": True,
        }


@pytest.fixture
def fake_firebase(monkeypatch: pytest.MonkeyPatch) -> FakeFirebase:
    fake = FakeFirebase()

    monkeypatch.setattr(firebase_module, "get_user_by_email", fake.get_user_by_email)
    monkeypatch.setattr(firebase_module, "get_user", fake.get_user)
    monkeypatch.setattr(firebase_module, "create_user", fake.create_user)
    monkeypatch.setattr(firebase_module, "update_user", fake.update_user)
    monkeypatch.setattr(firebase_module, "delete_user", fake.delete_user)
    monkeypatch.setattr(firebase_module, "is_enabled", fake.is_enabled)
    monkeypatch.setattr(firebase_module, "require_enabled", fake.require_enabled)

    async def _verify(id_token: str) -> dict[str, object]:
        """The test passes the claims through as the token itself."""
        import json

        from app.core.exceptions import UnauthorizedError

        try:
            return json.loads(id_token)
        except json.JSONDecodeError:
            raise UnauthorizedError("bad token", error_code="invalid_id_token")

    monkeypatch.setattr(firebase_module, "verify_id_token", _verify)
    return fake


# ------------------------------------------------------------------- app client
@pytest.fixture
async def client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    uri = _mongo_uri()
    if uri is None:
        pytest.skip("MONGODB_URI is not set")

    monkeypatch.setattr(settings, "MONGODB_URI", uri)
    monkeypatch.setattr(settings, "MONGODB_DB_NAME", TEST_DB_NAME)
    monkeypatch.setattr(settings, "OTP_DEV_MODE", True)
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")  # no real email
    monkeypatch.setattr(settings, "OTP_RESEND_COOLDOWN_SECONDS", 60)

    admin = AsyncMongoClient(uri)
    await admin.drop_database(TEST_DB_NAME)
    await admin.close()

    from app.main import create_app

    app = create_app()
    async with (
        LifespanManager(app, startup_timeout=120, shutdown_timeout=60),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=120) as ac,
    ):
        yield ac

    admin = AsyncMongoClient(uri)
    await admin.drop_database(TEST_DB_NAME)
    await admin.close()
