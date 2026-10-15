"""Profile request/response schemas.

Validation here is deliberately strict about the astrology inputs: a bad
timezone or an impossible time silently produces a wrong chart rather than an
error, so it is rejected at the edge instead.
"""

import zoneinfo
from datetime import UTC, date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import AccountStatus, AuthProvider, Gender, MaritalStatus, UserRole
from app.models.profile import Address, BirthDetails, CurrentLocation, NotificationPreferences

TIME_24H = r"^([01]\d|2[0-3]):([0-5]\d)$"

_VALID_TIMEZONES = zoneinfo.available_timezones()


def _validate_timezone(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if value not in _VALID_TIMEZONES:
        raise ValueError(
            f"'{value}' is not a known IANA timezone (expected something like Asia/Kolkata)."
        )
    return value


def _validate_past_date(value: date | None) -> date | None:
    if value is None:
        return None
    if value > datetime.now(UTC).date():
        raise ValueError("Date of birth cannot be in the future.")
    if value.year < 1900:
        raise ValueError("Date of birth must be in 1900 or later.")
    return value


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


# --------------------------------------------------------------------- input
class BirthDetailsInput(BaseModel):
    """Every field optional — a PATCH merges into whatever is already stored."""

    date_of_birth: date | None = None
    time_of_birth: str | None = Field(default=None, pattern=TIME_24H, examples=["14:35"])
    is_time_known: bool | None = None
    place: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = Field(default=None, examples=["Asia/Kolkata"])
    timezone_offset: float | None = Field(default=None, ge=-12, le=14)

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str | None) -> str | None:
        return _validate_timezone(v)

    @field_validator("date_of_birth")
    @classmethod
    def _dob(cls, v: date | None) -> date | None:
        return _validate_past_date(v)


class CurrentLocationInput(BaseModel):
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = Field(default=None, examples=["Asia/Kolkata"])

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str | None) -> str | None:
        return _validate_timezone(v)


class ProfileUpdate(BaseModel):
    """Partial update. Only the fields present in the body are touched.

    `extra="forbid"` is deliberate: `email` is the sign-in identity and is not
    editable here, so an attempt to change it fails loudly instead of being
    quietly dropped. It also turns a misspelt field name into an error rather
    than a silent no-op.
    """

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=1, max_length=60)
    middle_name: str | None = Field(default=None, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)

    phone: str | None = Field(default=None, min_length=4, max_length=20)
    country_code: str | None = Field(default=None, max_length=6)

    gender: Gender | None = None
    marital_status: MaritalStatus | None = None
    occupation: str | None = Field(default=None, max_length=120)
    language: str | None = Field(default=None, max_length=10)

    numerology_name: str | None = Field(default=None, max_length=180)
    call_names: list[Annotated[str, Field(max_length=60)]] | None = Field(
        default=None, max_length=20
    )

    birth: BirthDetailsInput | None = None
    current_location: CurrentLocationInput | None = None
    notifications: NotificationPreferences | None = None

    @field_validator("first_name", "middle_name", "last_name", "occupation", "numerology_name")
    @classmethod
    def _tidy(cls, v: str | None) -> str | None:
        return _clean(v)

    @field_validator("phone")
    @classmethod
    def _digits_only(cls, v: str | None) -> str | None:
        if v is None:
            return None
        digits = "".join(ch for ch in v if ch.isdigit())
        if not digits:
            raise ValueError("Phone number must contain digits.")
        return digits

    @field_validator("call_names")
    @classmethod
    def _tidy_call_names(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned = [name for name in (_clean(n) for n in v) if name]
        # Keep them unique, preserving the order they were given in.
        return list(dict.fromkeys(cleaned))


class AddressInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, max_length=40)
    full_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=4, max_length=20)
    line1: str = Field(min_length=1, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    landmark: str | None = Field(default=None, max_length=120)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=3, max_length=20)
    country: str = Field(default="India", max_length=100)
    is_default: bool = False


class AddressUpdate(BaseModel):
    """Partial update of one address."""

    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, max_length=40)
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=4, max_length=20)
    line1: str | None = Field(default=None, min_length=1, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    landmark: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, min_length=3, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    is_default: bool | None = None


# -------------------------------------------------------------------- output
class ProfileCompleteness(BaseModel):
    """What the client still needs before each feature can run."""

    profile_complete: bool
    chart_ready: bool = Field(description="Birth date, coordinates and timezone are all on file")
    panchang_ready: bool = Field(description="Current coordinates and timezone are on file")
    numerology_ready: bool = Field(description="Date of birth is on file")
    missing: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    """The full profile, returned by the /users/me endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    full_name: str

    phone: str | None = None
    country_code: str | None = None
    is_phone_verified: bool
    is_email_verified: bool

    avatar_url: str | None = None
    gender: Gender
    marital_status: MaritalStatus
    occupation: str | None = None
    language: str

    numerology_name: str | None = None
    name_for_numerology: str
    call_names: list[str]

    birth: BirthDetails
    current_location: CurrentLocation
    notifications: NotificationPreferences
    addresses: list[Address]

    role: UserRole
    status: AccountStatus
    auth_providers: list[AuthProvider]
    completeness: ProfileCompleteness | None = None
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v: object) -> str:
        return str(v)
