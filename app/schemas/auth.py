"""Registration request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import AccountStatus, AuthProvider, UserRole


def _clean_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


class EmailRegisterRequest(BaseModel):
    """Step 1 of manual sign-up — details in, OTP out."""

    email: EmailStr
    # No strength rules of our own — the user picks whatever password they want.
    # The 6-character floor is Firebase Auth's own hard minimum, and the 72-byte
    # ceiling is bcrypt's; rejecting here means we fail before sending an OTP
    # rather than after the user has already typed the code in.
    password: str = Field(
        min_length=6,
        max_length=72,
        description="At least 6 characters (required by Firebase Auth).",
    )
    first_name: str = Field(min_length=1, max_length=60)
    middle_name: str | None = Field(default=None, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)

    @field_validator("first_name", "middle_name", "last_name", mode="before")
    @classmethod
    def _tidy(cls, v: object) -> object:
        return _clean_name(v) if isinstance(v, str) or v is None else v


class EmailRegisterVerify(BaseModel):
    """Step 2 of manual sign-up — OTP in, account out."""

    email: EmailStr
    code: str = Field(min_length=4, max_length=10)


class ResendOtpRequest(BaseModel):
    email: EmailStr


class GoogleAuthRequest(BaseModel):
    """The Firebase ID token the client gets after Google sign-in."""

    id_token: str = Field(min_length=20)


class OtpSentResult(BaseModel):
    email: EmailStr
    expires_at: datetime
    resend_available_at: datetime
    dev_code: str | None = Field(
        default=None, description="Only set when the server runs with OTP_DEV_MODE=true"
    )


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    full_name: str
    role: UserRole
    status: AccountStatus
    is_email_verified: bool
    avatar_url: str | None = None
    auth_providers: list[AuthProvider]
    firebase_uid: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v: object) -> str:
        return str(v)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime
    refresh_expires_at: datetime


class AuthResult(BaseModel):
    user: UserPublic
    tokens: TokenPair
    is_new_user: bool = False


class EmailAvailability(BaseModel):
    email: EmailStr
    available: bool
    exists_in: list[str] = Field(
        default_factory=list, description="Where the email was found: mongodb and/or firebase"
    )


class PasswordLogin(BaseModel):
    """Sign in to an existing account with its email and password."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class ForgotPasswordRequest(BaseModel):
    """Step 1 of a password reset — the registered email address."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Step 2 of a password reset — the emailed code and the new password."""

    email: EmailStr
    code: str = Field(min_length=4, max_length=10)
    # Same bounds as sign-up: 6 is Firebase Auth's minimum, 72 is bcrypt's.
    new_password: str = Field(
        min_length=6,
        max_length=72,
        description="At least 6 characters (required by Firebase Auth).",
    )
