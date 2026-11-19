"""Astrologer Self-Application Schemas."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class AstrologerApplicationSendOtpIn(BaseModel):
    email: EmailStr


class AstrologerApplicationVerifyOtpIn(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=10)


class AstrologerApplicationCreateIn(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=25)
    otp_code: str = Field(
        ...,
        min_length=4,
        max_length=10,
        description="Verification code sent to applicant's email",
    )
    gender: str | None = Field(default=None, max_length=20)
    age: int | None = Field(default=None, ge=18, le=100)

    # Location
    address: str | None = Field(default=None, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str | None = Field(default=None, max_length=15)

    # Astrological Competence & Skills
    skills: list[str] = Field(default_factory=lambda: ["vedic_astrology"])
    specialisations: list[str] = Field(default_factory=list)
    experience_years: int = Field(default=5, ge=0, le=80)
    languages: list[str] = Field(default_factory=lambda: ["Bengali", "English"])
    qualifications: list[str] = Field(default_factory=list)
    bio: str | None = Field(default=None, max_length=4000)

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


class AstrologerApplicationOut(BaseModel):
    id: str
    application_number: str
    full_name: str
    email: str
    phone: str
    gender: str | None = None
    age: int | None = None
    address: str | None = None
    city: str
    state: str
    pincode: str | None = None
    skills: list[str]
    specialisations: list[str]
    experience_years: int
    languages: list[str]
    qualifications: list[str]
    bio: str | None = None
    avatar_url: str | None = None
    identity_proof_url: str | None = None
    bank_account_number: str | None = None
    bank_ifsc: str | None = None
    bank_account_holder: str | None = None
    bank_name: str | None = None
    upi_id: str | None = None
    pan_card: str | None = None
    status: str
    rejection_reason: str | None = None
    reviewed_at: datetime | None = None
    approved_user_id: str | None = None
    approved_astrologer_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AstrologerApplicationRejectIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class AstrologerApplicationApprovalResultOut(BaseModel):
    application_id: str
    user_id: str
    astrologer_id: str
    display_name: str
    email: str
    temporary_password: str
    email_sent: bool
    dashboard_url: str
    message: str
