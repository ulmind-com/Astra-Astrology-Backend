"""User document. Mirrored into Firebase Auth at creation time."""

from datetime import datetime
from typing import Annotated

import pymongo
from beanie import Indexed
from pydantic import EmailStr, Field

from app.models.base import TimestampedDocument
from app.models.enums import AccountStatus, AuthProvider, Gender, MaritalStatus, UserRole
from app.models.profile import (
    Address,
    BirthDetails,
    CurrentLocation,
    NotificationPreferences,
)


class User(TimestampedDocument):
    # ------------------------------------------------------------- identity
    email: Annotated[EmailStr, Indexed(unique=True)]
    first_name: str = Field(max_length=60)
    middle_name: str | None = Field(default=None, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)

    # ------------------------------------------------------------- sign-in
    hashed_password: str | None = Field(
        default=None, description="None for accounts that only use Google"
    )
    firebase_uid: str | None = None
    auth_providers: list[AuthProvider] = Field(default_factory=list)

    # -------------------------------------------------------------- access
    role: UserRole = UserRole.USER
    status: AccountStatus = AccountStatus.ACTIVE
    is_email_verified: bool = False
    # Set when an admin opens an account on someone's behalf and emails them a
    # generated password. Cleared the first time they choose their own.
    must_change_password: bool = False

    # -------------------------------------------------------------- phone
    phone: str | None = None
    country_code: str | None = Field(default="+91", max_length=6)
    is_phone_verified: bool = False

    # ------------------------------------------------------------- profile
    avatar_url: str | None = None
    avatar_public_id: str | None = None
    gender: Gender = Gender.UNDISCLOSED
    marital_status: MaritalStatus = MaritalStatus.UNDISCLOSED
    occupation: str | None = Field(default=None, max_length=120)
    language: str = Field(default="en", max_length=10)

    # ------------------------------------------------- names for numerology
    # The Chaldean calculation may use a different spelling to the legal name,
    # and the number of call-names is itself meaningful.
    numerology_name: str | None = Field(default=None, max_length=180)
    call_names: list[str] = Field(default_factory=list)

    # ------------------------------------------------- astrology input data
    birth: BirthDetails = Field(default_factory=BirthDetails)
    current_location: CurrentLocation = Field(default_factory=CurrentLocation)

    # ------------------------------------------------------------ platform
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences)
    addresses: list[Address] = Field(default_factory=list)

    # ------------------------------------------------------------ activity
    last_login_at: datetime | None = None

    class Settings(TimestampedDocument.Settings):
        name = "users"
        indexes = [
            [("role", pymongo.ASCENDING), ("status", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
            # Partial, not sparse: a sparse index still covers documents whose
            # field is explicitly null, so every user without a phone number
            # would collide with every other one.
            pymongo.IndexModel(
                [("phone", pymongo.ASCENDING)],
                name="phone_unique",
                unique=True,
                partialFilterExpression={"phone": {"$type": "string"}},
            ),
            pymongo.IndexModel(
                [("firebase_uid", pymongo.ASCENDING)],
                name="firebase_uid_unique",
                unique=True,
                partialFilterExpression={"firebase_uid": {"$type": "string"}},
            ),
        ]

    # ---------------------------------------------------------- behaviour
    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(part for part in parts if part)

    @property
    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE

    @property
    def has_password(self) -> bool:
        return self.hashed_password is not None

    @property
    def name_for_numerology(self) -> str:
        """The spelling the Chaldean calculation should use."""
        return self.numerology_name or self.full_name

    @property
    def is_profile_complete(self) -> bool:
        """Enough on file to run the astrology features."""
        return bool(self.first_name) and self.birth.is_chart_ready

    @property
    def default_address(self) -> Address | None:
        return next((a for a in self.addresses if a.is_default), None)

    def add_provider(self, provider: AuthProvider) -> None:
        if provider not in self.auth_providers:
            self.auth_providers.append(provider)
