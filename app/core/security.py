"""Password hashing and JWT token helpers."""

import hashlib
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import BadRequestError, UnauthorizedError

TokenType = Literal["access", "refresh", "application_upload"]

# bcrypt silently truncates anything past 72 bytes, so reject it instead.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Hashes a password. No strength rules — the user picks their own."""
    pwd = password.encode("utf-8")
    if not pwd:
        raise BadRequestError("Password cannot be empty.", error_code="password_empty")
    if len(pwd) > MAX_PASSWORD_BYTES:
        raise BadRequestError(
            f"Password is too long (max {MAX_PASSWORD_BYTES} bytes).",
            error_code="password_too_long",
        )
    return bcrypt.hashpw(pwd, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def create_access_token(
    subject: str, extra_claims: dict[str, Any] | None = None
) -> tuple[str, datetime]:
    return _create_token(
        subject, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), extra_claims
    )


def create_refresh_token(
    subject: str, extra_claims: dict[str, Any] | None = None
) -> tuple[str, datetime]:
    return _create_token(
        subject, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), extra_claims
    )


def create_application_upload_token(
    email: str,
    expires_minutes: int = 30,
) -> str:
    """Short-lived token issued after OTP verification to authorize document uploads."""
    token, _ = _create_token(
        email.strip().lower(),
        "application_upload",
        timedelta(minutes=expires_minutes),
    )
    return token


def verify_application_upload_token(token: str) -> str:
    """Validates an onboarding upload token and returns the verified email subject."""
    payload = decode_token(token, expected_type="application_upload")
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise UnauthorizedError("Invalid upload token.", error_code="invalid_token")
    return sub


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired.", error_code="token_expired")
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid token.", error_code="invalid_token")

    if expected_type and payload.get("type") != expected_type:
        raise UnauthorizedError(
            f"Expected a {expected_type} token.", error_code="invalid_token_type"
        )
    return payload


def hash_token(token: str) -> str:
    """SHA-256 of a token, for storing it without storing the token itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def safe_regex_pattern(term: str, max_len: int = 120) -> dict[str, str]:
    """Escapes untrusted user input for safe, bounded case-insensitive MongoDB $regex."""
    cleaned = term.strip()[:max_len]
    return {"$regex": re.escape(cleaned), "$options": "i"}
