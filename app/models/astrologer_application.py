"""Astrologer Self-Application & Verification Model."""

from datetime import UTC, datetime
from typing import ClassVar

import pymongo
from beanie import PydanticObjectId
from pydantic import EmailStr, Field

from app.models.base import TimestampedDocument


class AstrologerApplication(TimestampedDocument):
    """A self-submitted application from an Astrologer seeking onboarding and verification."""

    application_number: str = Field(
        ...,
        max_length=32,
        description="Unique human-readable application code, e.g. DIVIN-ASTRO-2026-0001",
    )
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=25)
    gender: str | None = Field(default=None, max_length=20)
    age: int | None = Field(default=None, ge=18, le=100)

    # Location
    address: str | None = Field(default=None, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str | None = Field(default=None, max_length=15)

    # Astrological Competence & Skills
    skills: list[str] = Field(
        default_factory=lambda: ["vedic_astrology"],
        description="Systems practiced, e.g. vedic_astrology, tarot, numerology, kp_astrology, palmistry, vastu",
    )
    specialisations: list[str] = Field(
        default_factory=list,
        description="Life domain focus, e.g. Career, Love, Marriage, Wealth, Health",
    )
    experience_years: int = Field(default=5, ge=0, le=80)
    languages: list[str] = Field(default_factory=lambda: ["Bengali", "English"])
    qualifications: list[str] = Field(
        default_factory=list,
        description="Diplomas, certifications, titles (e.g. Jyotish Ratna, Gold Medalist)",
    )
    bio: str | None = Field(
        default=None,
        max_length=4000,
        description="Lineage, institute, background, consultation approach",
    )

    # Media & Verification Documents
    avatar_url: str | None = None
    identity_proof_url: str | None = None

    # Financial & Payout Information
    bank_account_number: str | None = None
    bank_ifsc: str | None = None
    bank_account_holder: str | None = None
    bank_name: str | None = None
    upi_id: str | None = None
    pan_card: str | None = None

    # Review Lifecycle
    status: str = Field(default="pending", description="pending | approved | rejected")
    rejection_reason: str | None = None
    reviewed_by: PydanticObjectId | None = None
    reviewed_at: datetime | None = None

    # Linked Created Entities upon Approval
    approved_user_id: PydanticObjectId | None = None
    approved_astrologer_id: PydanticObjectId | None = None

    class Settings:
        name = "astrologer_applications"
        indexes: ClassVar[list] = [
            pymongo.IndexModel(
                [("application_number", pymongo.ASCENDING)],
                unique=True,
                name="astrologer_app_num_uniq",
            ),
            pymongo.IndexModel([("email", pymongo.ASCENDING)], name="astrologer_app_email_idx"),
            pymongo.IndexModel(
                [("status", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="astrologer_app_status_created_idx",
            ),
            pymongo.IndexModel([("phone", pymongo.ASCENDING)], name="astrologer_app_phone_idx"),
        ]
