"""Appointment request and response shapes."""

from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AppointmentStatus


# ------------------------------------------------- the astrologer's calendar
class WindowInput(BaseModel):
    """One stretch of a day the astrologer will take bookings in."""

    starts_at: datetime
    ends_at: datetime


class WindowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    day: date_type
    starts_at: datetime
    ends_at: datetime


class AppointmentCardUpdate(BaseModel):
    """What the astrologer charges, quoted per block."""

    enabled: bool | None = None
    price_paise: int | None = Field(default=None, ge=0, le=100_000_00)
    block_minutes: int | None = Field(default=None, ge=5, le=600)
    cancellation_window_minutes: int | None = Field(default=None, ge=0, le=1440)


class AppointmentCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    price_paise: int
    block_minutes: int
    cancellation_window_minutes: int = 30


# ------------------------------------------------------------- what is free
class Range(BaseModel):
    starts_at: datetime
    ends_at: datetime


class DayView(BaseModel):
    """Open hours and what is already gone, so a chooser can see both."""

    windows: list[Range]
    booked: list[Range]
    slot_minutes: int
    min_minutes: int
    max_minutes: int
    muhurat_ratings: dict[str, dict] | None = None


# ------------------------------------------------------------------ booking
class BookRequest(BaseModel):
    astrologer_id: str
    starts_at: datetime
    minutes: int = Field(ge=5, le=600)
    note: str | None = Field(default=None, max_length=1000)
    consultation_pillar: str | None = Field(default=None, max_length=50)
    kundli_id: str | None = None
    birth_details: dict | None = None


class QuoteRequest(BaseModel):
    astrologer_id: str
    minutes: int = Field(ge=5, le=600)


class AppointmentQuote(BaseModel):
    """What a booking of this length would cost, before committing to it."""

    minutes: int
    price_paise: int
    commission_percent: float
    deposit_paise: int
    deposit_coins: int
    balance_due_paise: int
    balance_due_coins: int = 0
    total_coins: int = 0
    # Available wallet balance that can be used for booking
    available_coins: int = 0
    # Total wallet balance
    balance_coins: int
    # True only if user's available_coins >= total_coins needed for the consultation
    can_afford: bool


class AppointmentPeer(BaseModel):
    id: str | None = None
    name: str | None = None
    avatar_url: str | None = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: AppointmentStatus
    starts_at: datetime
    ends_at: datetime
    minutes: int

    price_paise: int
    commission_percent: float
    deposit_paise: int
    deposit_coins: int
    balance_due_paise: int
    balance_due_coins: int = 0
    held_coins: int = 0
    held_status: str = "none"

    cancellation_window_minutes: int = 30
    cancel_deadline: datetime | None = None
    can_cancel: bool = False
    completed_at: datetime | None = None

    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    user_note: str | None = None

    consultation_pillar: str | None = None
    kundli_id: str | None = None
    birth_details: dict | None = None
    prescription: dict | None = None
    muhurat_type: str | None = None
    preflight_dossier: dict | None = None
    cosmic_synergy_score: int | None = None
    certificate_data: dict | None = None

    peer: AppointmentPeer | None = None


class CancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=300)


class PrescriptionUpdateRequest(BaseModel):
    gemstone: str | None = Field(default=None, max_length=200)
    rudraksha: str | None = Field(default=None, max_length=200)
    mantra: str | None = Field(default=None, max_length=500)
    mantra_count: int | None = Field(default=108, ge=1)
    daan_remedy: str | None = Field(default=None, max_length=300)
    astrologer_notes: str | None = Field(default=None, max_length=2000)
