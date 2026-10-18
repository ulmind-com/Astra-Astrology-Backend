"""Astrologer schemas — admin creation, admin editing, and self-service."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.astrologer import (
    Availability,
    BankDetails,
    GalleryImage,
    RateCard,
    RatingSummary,
)
from app.models.enums import AccountStatus, ConsultationMode, Skill


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


# ------------------------------------------------------- admin: create
class AstrologerCreate(BaseModel):
    """What an admin fills in to open an astrologer's account.

    No password field: one is generated and emailed to the astrologer, because
    nobody — not even the admin — should be choosing someone else's password.
    """

    model_config = ConfigDict(extra="forbid")

    # account
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=60)
    middle_name: str | None = Field(default=None, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)
    phone: str | None = Field(default=None, min_length=4, max_length=20)

    # profile
    display_name: str | None = Field(
        default=None, max_length=120, description="Defaults to the full name"
    )
    tagline: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=5000)
    skills: list[Skill] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    specialisations: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0, le=90)

    # commerce
    rates: RateCard = Field(default_factory=RateCard)
    modes_enabled: list[ConsultationMode] | None = None
    # None means the platform default. Defaulting to a number here would
    # give every new astrologer a private deal nobody chose.
    commission_percent: float | None = Field(default=None, ge=0, le=100)

    # curation
    is_listed: bool = True
    is_featured: bool = False
    display_order: int = 0

    @field_validator("first_name", "middle_name", "last_name", "display_name", "tagline")
    @classmethod
    def _tidy(cls, v: str | None) -> str | None:
        return _clean(v)

    @field_validator("phone")
    @classmethod
    def _digits(cls, v: str | None) -> str | None:
        if v is None:
            return None
        digits = "".join(ch for ch in v if ch.isdigit())
        if not digits:
            raise ValueError("Phone number must contain digits.")
        return digits


# ------------------------------------------- astrologer: own profile edit
class AstrologerUpdate(BaseModel):
    """What the astrologer may change about themselves.

    Rates, commission and the curation flags are absent on purpose — those are
    the platform's to set, not the astrologer's.
    """

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=1, max_length=60)
    middle_name: str | None = Field(default=None, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)
    phone: str | None = Field(default=None, min_length=4, max_length=20)

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    tagline: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=5000)
    skills: list[Skill] | None = None
    languages: list[str] | None = Field(default=None, max_length=20)
    specialisations: list[str] | None = Field(default=None, max_length=30)
    qualifications: list[str] | None = Field(default=None, max_length=30)
    experience_years: int | None = Field(default=None, ge=0, le=90)
    intro_video_url: str | None = Field(default=None, max_length=500)
    bank: BankDetails | None = None

    @field_validator("first_name", "middle_name", "last_name", "display_name", "tagline")
    @classmethod
    def _tidy(cls, v: str | None) -> str | None:
        return _clean(v)

    @field_validator("phone")
    @classmethod
    def _digits(cls, v: str | None) -> str | None:
        if v is None:
            return None
        digits = "".join(ch for ch in v if ch.isdigit())
        if not digits:
            raise ValueError("Phone number must contain digits.")
        return digits

    @field_validator("languages", "specialisations", "qualifications")
    @classmethod
    def _tidy_list(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned = [item for item in (_clean(x) for x in v) if item]
        return list(dict.fromkeys(cleaned))


class AvailabilityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_online: bool | None = None
    is_available_for_chat: bool | None = None
    is_available_for_call: bool | None = None
    is_available_for_video: bool | None = None
    is_busy: bool | None = None


# --------------------------------------------------- admin: edit / manage
class AstrologerAdminUpdate(AstrologerUpdate):
    """Everything the astrologer can change, plus what only the platform can."""

    rates: RateCard | None = None
    modes_enabled: list[ConsultationMode] | None = None
    commission_percent: float | None = Field(default=None, ge=0, le=100)
    is_listed: bool | None = None
    is_featured: bool | None = None
    display_order: int | None = None
    status: AccountStatus | None = Field(default=None, description="Applies to the account")


# ---------------------------------------------------------------- output
class AstrologerProfile(BaseModel):
    """The astrologer's own view, and the admin's."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    email: EmailStr
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    full_name: str
    phone: str | None = None

    display_name: str
    slug: str | None = None
    tagline: str | None = None
    bio: str | None = None
    profile_image_url: str | None = None
    gallery: list[GalleryImage]
    intro_video_url: str | None = None

    skills: list[Skill]
    languages: list[str]
    specialisations: list[str]
    qualifications: list[str]
    experience_years: int

    rates: RateCard
    modes_enabled: list[ConsultationMode]
    commission_percent: float | None = None
    bank: BankDetails

    availability: Availability
    rating: RatingSummary
    total_consultations: int
    followers_count: int

    is_listed: bool
    is_featured: bool
    display_order: int
    status: AccountStatus
    must_change_password: bool = Field(
        description="True until the astrologer replaces the password they were emailed"
    )
    last_login_at: datetime | None = None
    created_at: datetime


class AstrologerCreated(BaseModel):
    """Returned once, when an admin opens the account."""

    astrologer: AstrologerProfile
    welcome_email_sent: bool
    initial_password: str | None = Field(
        default=None,
        description=(
            "Only filled in when the welcome email could not be sent, so the admin "
            "can pass the password on another way."
        ),
    )


# ------------------------------------------------------- public directory
class ResolvedRates(BaseModel):
    """Coins per started minute, with no blanks left to interpret."""

    chat_coins_per_minute: int
    call_coins_per_minute: int
    video_coins_per_minute: int


class AstrologerPublic(BaseModel):
    """What the website and app may show about an astrologer.

    Deliberately narrower than `AstrologerProfile`: no email, phone, bank
    details, commission or account status — this is served to anyone.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    slug: str | None = None
    tagline: str | None = None
    bio: str | None = None
    profile_image_url: str | None = None
    gallery: list[GalleryImage]
    intro_video_url: str | None = None

    skills: list[Skill]
    languages: list[str]
    specialisations: list[str]
    qualifications: list[str]
    experience_years: int

    # What a minute actually costs, in coins, with the platform default already
    # filled in where this astrologer has no rate of their own. The raw card
    # with its blanks is an admin's business, not a visitor's.
    rates: ResolvedRates
    modes_enabled: list[ConsultationMode]

    availability: Availability
    rating: RatingSummary
    total_consultations: int
    followers_count: int
    is_featured: bool

    @field_validator("id", mode="before")
    @classmethod
    def _stringify_id(cls, v: object) -> str:
        return str(v)


class AstrologerFilters(BaseModel):
    search: str | None = None
    skill: Skill | None = None
    language: str | None = None
    mode: ConsultationMode | None = None
    online_only: bool = False
    featured_only: bool = False
    min_experience: int | None = None
    max_coins_per_minute: int | None = None


class GalleryUploadResult(BaseModel):
    image: GalleryImage
    gallery: list[GalleryImage]
