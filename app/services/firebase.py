"""Firebase Auth, used as the mirror of every account in MongoDB.

Every call is wrapped so the caller gets an `AppError`, never a raw Firebase
exception, and every blocking SDK call runs off the event loop.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from loguru import logger

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ServiceUnavailableError,
    UnauthorizedError,
)

_app: firebase_admin.App | None = None
_APP_NAME = "astra-astrology"


@dataclass(frozen=True)
class FirebaseUser:
    uid: str
    email: str | None
    display_name: str | None
    photo_url: str | None
    email_verified: bool
    providers: list[str]


def _load_credentials() -> credentials.Base | None:
    if settings.FIREBASE_CREDENTIALS_JSON:
        try:
            data: dict[str, Any] = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        except json.JSONDecodeError as exc:
            logger.error("FIREBASE_CREDENTIALS_JSON is not valid JSON: {}", exc)
            return None
        return credentials.Certificate(data)

    if settings.FIREBASE_CREDENTIALS_PATH:
        try:
            return credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        except Exception as exc:  # noqa: BLE001 - bad path/file is a config error
            logger.error(
                "Could not read FIREBASE_CREDENTIALS_PATH '{}': {}",
                settings.FIREBASE_CREDENTIALS_PATH,
                exc,
            )
            return None

    return None


def init_firebase() -> None:
    """Called once on startup. Safe to call again; never raises."""
    global _app

    if _app is not None:
        return
    if not settings.firebase_configured:
        logger.warning(
            "Firebase is not configured — set FIREBASE_CREDENTIALS_PATH or "
            "FIREBASE_CREDENTIALS_JSON. Registration will be refused while "
            "FIREBASE_REQUIRED is true."
        )
        return

    creds = _load_credentials()
    if creds is None:
        return

    options = {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None
    try:
        _app = firebase_admin.initialize_app(creds, options, name=_APP_NAME)
    except ValueError:
        # Already initialised (e.g. the app was reloaded) — reuse it.
        _app = firebase_admin.get_app(name=_APP_NAME)
    logger.success("Firebase Auth initialised for project '{}'.", _app.project_id)


def is_enabled() -> bool:
    return _app is not None


def require_enabled() -> None:
    """Guards the registration paths that must write to Firebase."""
    if is_enabled():
        return
    if settings.FIREBASE_REQUIRED:
        raise ServiceUnavailableError(
            "Sign-up is temporarily unavailable. Please try again shortly.",
            error_code="firebase_not_configured",
        )
    logger.warning("Firebase is disabled — continuing with MongoDB only.")


async def _call(func: Any, *args: Any, **kwargs: Any) -> Any:
    """Runs a blocking Firebase call in a thread, with the app injected."""
    return await asyncio.to_thread(func, *args, app=_app, **kwargs)


def _to_user(record: firebase_auth.UserRecord) -> FirebaseUser:
    return FirebaseUser(
        uid=record.uid,
        email=record.email,
        display_name=record.display_name,
        photo_url=record.photo_url,
        email_verified=bool(record.email_verified),
        providers=[p.provider_id for p in (record.provider_data or [])],
    )


# --------------------------------------------------------------------- reads
async def get_user_by_email(email: str) -> FirebaseUser | None:
    """None when the email is free. Raises only if Firebase itself is broken."""
    if not is_enabled():
        return None
    try:
        record = await _call(firebase_auth.get_user_by_email, email.lower())
        return _to_user(record)
    except firebase_auth.UserNotFoundError:
        return None
    except Exception as exc:  # noqa: BLE001 - Firebase outage
        logger.opt(exception=exc).error("Firebase lookup failed for {}", email)
        raise ServiceUnavailableError(
            "Could not verify the account right now. Please try again.",
            error_code="firebase_unavailable",
        )


async def get_user(uid: str) -> FirebaseUser | None:
    if not is_enabled():
        return None
    try:
        return _to_user(await _call(firebase_auth.get_user, uid))
    except firebase_auth.UserNotFoundError:
        return None
    except Exception as exc:  # noqa: BLE001 - Firebase outage
        logger.opt(exception=exc).error("Firebase lookup failed for uid {}", uid)
        raise ServiceUnavailableError(
            "Could not verify the account right now. Please try again.",
            error_code="firebase_unavailable",
        )


# -------------------------------------------------------------------- writes
async def create_user(
    *,
    email: str,
    password: str | None = None,
    display_name: str | None = None,
    email_verified: bool = False,
    photo_url: str | None = None,
) -> FirebaseUser:
    require_enabled()
    if not is_enabled():
        raise ServiceUnavailableError("Firebase is disabled.", error_code="firebase_not_configured")

    kwargs: dict[str, Any] = {"email": email.lower(), "email_verified": email_verified}
    if password:
        kwargs["password"] = password
    if display_name:
        kwargs["display_name"] = display_name
    if photo_url:
        kwargs["photo_url"] = photo_url

    try:
        record = await _call(firebase_auth.create_user, **kwargs)
    except firebase_auth.EmailAlreadyExistsError:
        raise ConflictError(
            "An account with this email already exists.", error_code="email_already_exists"
        )
    except ValueError as exc:
        # Firebase rejected the input itself (e.g. a password under 6 characters).
        logger.warning("Firebase rejected the details for {}: {}", email, exc)
        raise BadRequestError(str(exc), error_code="firebase_invalid_input")
    except Exception as exc:  # noqa: BLE001 - Firebase outage
        logger.opt(exception=exc).error("Firebase user creation failed for {}", email)
        raise ServiceUnavailableError(
            "Could not create the account right now. Please try again.",
            error_code="firebase_unavailable",
        )

    logger.info("Firebase user created: {} ({})", email, record.uid)
    return _to_user(record)


async def update_user(
    uid: str,
    *,
    password: str | None = None,
    display_name: str | None = None,
    email_verified: bool | None = None,
    photo_url: str | None = None,
) -> FirebaseUser:
    if not is_enabled():
        raise ServiceUnavailableError("Firebase is disabled.", error_code="firebase_not_configured")

    kwargs: dict[str, Any] = {}
    if password is not None:
        kwargs["password"] = password
    if display_name is not None:
        kwargs["display_name"] = display_name
    if email_verified is not None:
        kwargs["email_verified"] = email_verified
    if photo_url is not None:
        kwargs["photo_url"] = photo_url

    try:
        record = await _call(firebase_auth.update_user, uid, **kwargs)
    except ValueError as exc:
        logger.warning("Firebase rejected the update for uid {}: {}", uid, exc)
        raise BadRequestError(str(exc), error_code="firebase_invalid_input")
    except Exception as exc:  # noqa: BLE001 - Firebase outage
        logger.opt(exception=exc).error("Firebase user update failed for uid {}", uid)
        raise ServiceUnavailableError(
            "Could not update the account right now. Please try again.",
            error_code="firebase_unavailable",
        )

    logger.info("Firebase user updated: {}", uid)
    return _to_user(record)


async def delete_user(uid: str) -> bool:
    """Best-effort delete, used to roll back a half-finished registration."""
    if not is_enabled():
        return False
    try:
        await _call(firebase_auth.delete_user, uid)
        logger.info("Firebase user deleted (rollback): {}", uid)
        return True
    except Exception as exc:  # noqa: BLE001 - rollback must never mask the real error
        logger.opt(exception=exc).error(
            "Firebase rollback failed — uid {} is now orphaned and needs cleanup.", uid
        )
        return False


# ------------------------------------------------------------------- tokens
async def verify_id_token(id_token: str) -> dict[str, Any]:
    """Verifies a Firebase ID token from the client (Google sign-in)."""
    if not is_enabled():
        raise ServiceUnavailableError(
            "Google sign-in is temporarily unavailable.",
            error_code="firebase_not_configured",
        )
    try:
        # check_revoked needs a network call; the signature check alone is enough here.
        return await asyncio.to_thread(firebase_auth.verify_id_token, id_token, app=_app)
    except (
        firebase_auth.ExpiredIdTokenError,
        firebase_auth.RevokedIdTokenError,
        firebase_auth.InvalidIdTokenError,
        ValueError,
    ) as exc:
        logger.warning("Rejected Firebase ID token: {}", exc)
        raise UnauthorizedError(
            "This Google sign-in could not be verified. Please try again.",
            error_code="invalid_id_token",
        )
    except Exception as exc:  # noqa: BLE001 - Firebase outage
        logger.opt(exception=exc).error("Firebase token verification failed")
        raise ServiceUnavailableError(
            "Could not verify your sign-in right now. Please try again.",
            error_code="firebase_unavailable",
        )
