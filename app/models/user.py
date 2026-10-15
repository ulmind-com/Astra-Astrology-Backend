"""User document. Mirrored into Firebase Auth at creation time."""

from datetime import datetime
from typing import Annotated

import pymongo
from beanie import Indexed
from pydantic import EmailStr, Field

from app.models.base import TimestampedDocument
from app.models.enums import AccountStatus, AuthProvider, UserRole


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
    firebase_uid: Annotated[str | None, Indexed(unique=True, sparse=True)] = None
    auth_providers: list[AuthProvider] = Field(default_factory=list)

    # -------------------------------------------------------------- access
    role: UserRole = UserRole.USER
    status: AccountStatus = AccountStatus.ACTIVE
    is_email_verified: bool = False

    # ------------------------------------------------------------- profile
    avatar_url: str | None = None

    # ------------------------------------------------------------ activity
    last_login_at: datetime | None = None

    class Settings(TimestampedDocument.Settings):
        name = "users"
        indexes = [
            [("role", pymongo.ASCENDING), ("status", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
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

    def add_provider(self, provider: AuthProvider) -> None:
        if provider not in self.auth_providers:
            self.auth_providers.append(provider)
