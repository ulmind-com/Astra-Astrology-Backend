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


class AppointmentCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    price_paise: int
    block_minutes: int


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


# ------------------------------------------------------------------ booking
class BookRequest(BaseModel):
    astrologer_id: str
    starts_at: datetime
    minutes: int = Field(ge=5, le=600)
    note: str | None = Field(default=None, max_length=1000)


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
    balance_coins: int
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

    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    user_note: str | None = None

    peer: AppointmentPeer | None = None


class CancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=300)
