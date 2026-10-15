"""A signup that has been started but is still waiting on its email OTP.

Nothing is created in MongoDB or Firebase until the OTP is verified, so this
holds the details in the meantime. The password is encrypted (not hashed),
because Firebase needs it in plaintext when the account is finally created.
"""

from datetime import UTC, datetime
from typing import Annotated

import pymongo
from beanie import Indexed
from pydantic import EmailStr, Field

from app.core.config import settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.models.base import TimestampedDocument


class PendingRegistration(TimestampedDocument):
    email: Annotated[EmailStr, Indexed(unique=True)]
    encrypted_password: str
    first_name: str = Field(max_length=60)
    middle_name: str | None = Field(default=None, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)
    expires_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None

    class Settings(TimestampedDocument.Settings):
        name = "pending_registrations"
        indexes = [
            pymongo.IndexModel(
                [("expires_at", pymongo.ASCENDING)],
                name="pending_registration_ttl",
                expireAfterSeconds=0,
            ),
        ]

    @classmethod
    def build(
        cls,
        *,
        email: str,
        password: str,
        first_name: str,
        middle_name: str | None,
        last_name: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "PendingRegistration":
        from datetime import timedelta

        return cls(
            email=email.lower(),
            encrypted_password=encrypt_secret(password),
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.PENDING_REGISTRATION_EXPIRE_MINUTES),
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @property
    def password(self) -> str:
        return decrypt_secret(self.encrypted_password)

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(part for part in parts if part)

    @property
    def is_expired(self) -> bool:
        expires = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=UTC)
        return datetime.now(UTC) >= expires
