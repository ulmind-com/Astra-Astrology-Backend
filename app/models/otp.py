"""One-time passcodes. Codes are stored hashed and expire via a TTL index."""

from datetime import UTC, datetime, timedelta

import pymongo
from pydantic import Field

from app.core.config import settings
from app.models.base import TimestampedDocument, utcnow
from app.models.enums import OtpChannel, OtpPurpose


class OtpCode(TimestampedDocument):
    identifier: str = Field(description="Email address (lowercased) the OTP was sent to")
    channel: OtpChannel = OtpChannel.EMAIL
    purpose: OtpPurpose = OtpPurpose.SIGNUP
    hashed_code: str
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = Field(default_factory=lambda: settings.OTP_MAX_ATTEMPTS)
    consumed_at: datetime | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    class Settings(TimestampedDocument.Settings):
        name = "otp_codes"
        indexes = [
            [
                ("identifier", pymongo.ASCENDING),
                ("purpose", pymongo.ASCENDING),
                ("created_at", pymongo.DESCENDING),
            ],
            pymongo.IndexModel(
                [("expires_at", pymongo.ASCENDING)],
                name="otp_ttl",
                expireAfterSeconds=60 * 60,  # keep an hour past expiry for auditing
            ),
        ]

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= self._aware(self.expires_at)

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    @property
    def is_exhausted(self) -> bool:
        return self.attempts >= self.max_attempts

    @property
    def resend_available_at(self) -> datetime:
        return self._aware(self.created_at) + timedelta(
            seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
        )

    def mark_consumed(self) -> None:
        self.consumed_at = utcnow()
