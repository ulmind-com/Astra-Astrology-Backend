"""Purohit (Vedic Priest) Self-Application Schemas."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class PurohitApplicationSendOtpIn(BaseModel):
    email: EmailStr


class PurohitApplicationVerifyOtpIn(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=10)


class PurohitApplicationCreateIn(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=25)
    otp_code: str = Field(..., min_length=4, max_length=10, description="Verification code sent to applicant's email")
    age: int | None = Field(default=None, ge=18, le=100)

    # Location
    address: str | None = Field(default=None, max_length=300)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str | None = Field(default=None, max_length=15)

    # Vedic Tradition & Expertise
    vedic_shakha: str = Field(default="যজুর্বেদীয়", max_length=100)
    specializations: list[str] = Field(default_factory=list)
    experience_years: int = Field(default=5, ge=0, le=75)
    languages: list[str] = Field(default_factory=lambda: ["Bengali", "Sanskrit"])
    bio: str | None = Field(default=None, max_length=3000)

    # Media & Verification Documents
    avatar_url: str | None = None
    identity_proof_url: str | None = None

    # Financial & Payout Information
    bank_account_number: str | None = None
    bank_ifsc: str | None = None
    bank_account_holder: str | None = None
    upi_id: str | None = None


class PurohitApplicationOut(BaseModel):
    id: str
    application_number: str
    full_name: str
    email: str
    phone: str
    age: int | None = None
    address: str | None = None
    city: str
    state: str
    pincode: str | None = None
    vedic_shakha: str
    specializations: list[str]
    experience_years: int
    languages: list[str]
    bio: str | None = None
    avatar_url: str | None = None
    identity_proof_url: str | None = None
    bank_account_number: str | None = None
    bank_ifsc: str | None = None
    bank_account_holder: str | None = None
    upi_id: str | None = None
    status: str
    rejection_reason: str | None = None
    reviewed_at: datetime | None = None
    approved_user_id: str | None = None
    approved_purohit_id: str | None = None
    created_at: datetime
    updated_at: datetime


class PurohitApplicationRejectIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class PurohitApplicationApprovalResultOut(BaseModel):
    application_id: str
    user_id: str
    purohit_id: str
    display_name: str
    email: str
    temporary_password: str
    email_sent: bool
    dashboard_url: str
    message: str
