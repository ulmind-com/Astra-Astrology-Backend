"""Passkey / WebAuthn credentials and challenges."""

from datetime import UTC, datetime
from typing import Annotated

import pymongo
from beanie import Indexed, PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument


class PasskeyCredential(TimestampedDocument):
    """Stores a public key credential for WebAuthn/Passkey passwordless sign-in."""

    user_id: Annotated[PydanticObjectId, Indexed()]
    credential_id: Annotated[str, Indexed(unique=True)]
    public_key: str = Field(description="Base64url encoded public key bytes")
    sign_count: int = Field(default=0, ge=0)
    device_name: str = Field(default="Biometric Device / Passkey", max_length=120)
    transports: list[str] = Field(default_factory=list)
    last_used_at: datetime | None = None

    class Settings(TimestampedDocument.Settings):
        name = "passkey_credentials"
        indexes = [
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)], name="passkey_user_id"),
            pymongo.IndexModel([("credential_id", pymongo.ASCENDING)], name="passkey_cred_id_unique", unique=True),
        ]


class PasskeyChallenge(TimestampedDocument):
    """Short-lived cryptographic challenge for WebAuthn ceremonies."""

    challenge: Annotated[str, Indexed(unique=True)]
    user_id: PydanticObjectId | None = None
    ceremony: str = Field(description="'registration' or 'authentication'")
    rp_id: str = Field(default="localhost")

    class Settings(TimestampedDocument.Settings):
        name = "passkey_challenges"
        indexes = [
            pymongo.IndexModel([("challenge", pymongo.ASCENDING)], name="passkey_challenge_unique", unique=True),
            pymongo.IndexModel(
                [("created_at", pymongo.ASCENDING)],
                name="passkey_challenge_ttl",
                expireAfterSeconds=300,  # 5 minutes TTL
            ),
        ]
