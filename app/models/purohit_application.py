"""Purohit (Vedic Priest) Self-Application & Verification Model."""

from datetime import UTC, datetime
from typing import ClassVar

import pymongo
from beanie import PydanticObjectId
from pydantic import EmailStr, Field

from app.models.base import TimestampedDocument


class PurohitApplication(TimestampedDocument):
    """A self-submitted application from a Purohit / Vedic Acharya seeking onboarding."""

    application_number: str = Field(..., max_length=32, description="Unique human-readable application code, e.g. DIVIN-PA-2026-0001")
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=25)
    age: int | None = Field(default=None, ge=18, le=100)

    # Location
    address: str | None = Field(default=None, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str | None = Field(default=None, max_length=15)

    # Vedic Tradition & Expertise
    vedic_shakha: str = Field(default="যজুর্বেদীয়", max_length=100, description="Vedic tradition, e.g. যজুর্বেদীয়, সামবেদীয়, ঋগবেদীয়, স্মার্ত আচার্য")
    specializations: list[str] = Field(default_factory=list, description="List of pujas, e.g. রুদ্রাভিষেক, সত্যনারায়ণ কথা")
    experience_years: int = Field(default=5, ge=0, le=75)
    languages: list[str] = Field(default_factory=lambda: ["Bengali", "Sanskrit"])
    bio: str | None = Field(default=None, max_length=3000, description="Vedic lineage, Gurukul, or lineage history")

    # Media & Verification Documents
    avatar_url: str | None = None
    identity_proof_url: str | None = None

    # Financial & Payout Information
    bank_account_number: str | None = None
    bank_ifsc: str | None = None
    bank_account_holder: str | None = None
    upi_id: str | None = None

    # Review Lifecycle
    status: str = Field(default="pending", description="pending | approved | rejected")
    rejection_reason: str | None = None
    reviewed_by: PydanticObjectId | None = None
    reviewed_at: datetime | None = None

    # Linked Created Entities upon Approval
    approved_user_id: PydanticObjectId | None = None
    approved_purohit_id: PydanticObjectId | None = None

    class Settings:
        name = "purohit_applications"
        indexes: ClassVar[list] = [
            pymongo.IndexModel([("application_number", pymongo.ASCENDING)], unique=True, name="purohit_app_num_uniq"),
            pymongo.IndexModel([("email", pymongo.ASCENDING)], name="purohit_app_email_idx"),
            pymongo.IndexModel([("status", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)], name="purohit_app_status_created_idx"),
            pymongo.IndexModel([("phone", pymongo.ASCENDING)], name="purohit_app_phone_idx"),
        ]
