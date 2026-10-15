"""OTP generation, delivery and verification."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from loguru import logger

from app.core.config import settings
from app.core.exceptions import BadRequestError, TooManyRequestsError
from app.models.enums import OtpChannel, OtpPurpose
from app.models.otp import OtpCode
from app.services.email import send_otp_email


def generate_code(length: int | None = None) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length or settings.OTP_LENGTH))


def hash_code(code: str, identifier: str) -> str:
    """HMAC keyed on the app secret and salted per identifier."""
    return hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        f"{identifier.lower()}:{code}".encode(),
        hashlib.sha256,
    ).hexdigest()


async def _latest(identifier: str, purpose: OtpPurpose) -> OtpCode | None:
    return (
        await OtpCode.find(OtpCode.identifier == identifier, OtpCode.purpose == purpose)
        .sort(-OtpCode.created_at)
        .first_or_none()
    )


async def _enforce_resend_cooldown(identifier: str, purpose: OtpPurpose) -> None:
    latest = await _latest(identifier, purpose)
    if latest is None:
        return

    now = datetime.now(UTC)
    available_at = latest.resend_available_at
    if now < available_at:
        wait = max(int((available_at - now).total_seconds()), 1)
        raise TooManyRequestsError(
            f"Please wait {wait} second{'s' if wait != 1 else ''} before asking for a new code.",
            error_code="otp_cooldown",
            details={"retry_after_seconds": wait},
        )


async def create_and_send_otp(
    identifier: str,
    purpose: OtpPurpose = OtpPurpose.SIGNUP,
    *,
    channel: OtpChannel = OtpChannel.EMAIL,
    name: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[OtpCode, str]:
    """Invalidates earlier codes, issues a fresh one and emails it.

    Returns the record plus the plaintext code; only expose the code when
    `OTP_DEV_MODE` is on.
    """
    identifier = identifier.lower().strip()
    await _enforce_resend_cooldown(identifier, purpose)

    # Only the newest code stays usable.
    await OtpCode.find(
        OtpCode.identifier == identifier,
        OtpCode.purpose == purpose,
        OtpCode.consumed_at == None,  # noqa: E711 - Beanie builds the Mongo query from `==`
    ).set({OtpCode.consumed_at: datetime.now(UTC)})

    code = generate_code()
    otp = OtpCode(
        identifier=identifier,
        channel=channel,
        purpose=purpose,
        hashed_code=hash_code(code, identifier),
        expires_at=datetime.now(UTC) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await otp.insert()

    try:
        if channel is OtpChannel.EMAIL:
            await send_otp_email(to=identifier, code=code, purpose=purpose.value, name=name)
        else:
            logger.warning("Channel {} is not wired up yet — the code was not delivered.", channel)
    except Exception:
        # Delivery failed, so this code is unusable. Drop it rather than leaving a
        # row behind that would put the caller on the resend cooldown for a
        # failure that was not theirs.
        await otp.delete()
        raise

    if settings.OTP_DEV_MODE:
        logger.info("OTP_DEV_MODE: code for {} is {}", identifier, code)

    return otp, code


async def verify_otp(
    identifier: str, code: str, purpose: OtpPurpose = OtpPurpose.SIGNUP
) -> OtpCode:
    """Consumes the code on success; raises an `AppError` on every failure."""
    identifier = identifier.lower().strip()
    otp = await _latest(identifier, purpose)

    if otp is None:
        raise BadRequestError(
            "No verification code was requested for this email.", error_code="otp_not_found"
        )
    if otp.is_consumed:
        raise BadRequestError("This code has already been used.", error_code="otp_already_used")
    if otp.is_expired:
        raise BadRequestError(
            "This code has expired. Please ask for a new one.", error_code="otp_expired"
        )
    if otp.is_exhausted:
        raise TooManyRequestsError(
            "Too many incorrect attempts. Please ask for a new code.",
            error_code="otp_attempts_exceeded",
        )

    if not hmac.compare_digest(otp.hashed_code, hash_code(code.strip(), identifier)):
        otp.attempts += 1
        await otp.save()
        remaining = max(otp.max_attempts - otp.attempts, 0)
        raise BadRequestError(
            f"Incorrect code. {remaining} attempt{'s' if remaining != 1 else ''} left.",
            error_code="otp_invalid",
            details={"attempts_left": remaining},
        )

    otp.mark_consumed()
    await otp.save()
    return otp
