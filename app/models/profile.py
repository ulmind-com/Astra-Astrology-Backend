"""Embedded profile documents stored inside a user.

The field list comes from what the astrology and numerology features actually
need as input:

* kundli      -> birth date, birth time, latitude, longitude, timezone
* panchang    -> the city the person is in *now*, not where they were born
* numerology  -> birth date only
* name sound  -> the spelling used for the name, and how many call-names exist
* mobile      -> the 10-digit number without its country code
* store       -> delivery addresses
"""

import uuid
from datetime import date

from pydantic import BaseModel, Field


class BirthDetails(BaseModel):
    """Everything the chart engine needs to place the planets."""

    date_of_birth: date | None = None
    time_of_birth: str | None = Field(default=None, description="24-hour HH:MM, local to birth")
    is_time_known: bool = Field(
        default=False, description="False means only a limited chart can be produced"
    )

    place: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)

    # Without these three a kundli cannot be calculated at all.
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = Field(default=None, description="IANA name, e.g. Asia/Kolkata")
    timezone_offset: float | None = Field(
        default=None, ge=-12, le=14, description="Hours from UTC at the moment of birth"
    )

    @property
    def is_chart_ready(self) -> bool:
        return (
            self.date_of_birth is not None
            and self.latitude is not None
            and self.longitude is not None
            and self.timezone is not None
        )


class CurrentLocation(BaseModel):
    """Where the person is now. Panchang is calculated for this, not for birth."""

    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = Field(default=None, description="IANA name, e.g. Asia/Kolkata")

    @property
    def is_panchang_ready(self) -> bool:
        return (
            self.latitude is not None and self.longitude is not None and self.timezone is not None
        )


class NotificationPreferences(BaseModel):
    push: bool = True
    email: bool = True
    sms: bool = True
    whatsapp: bool = True
    marketing: bool = True
    daily_horoscope: bool = True
    remedy_reminders: bool = True


class Address(BaseModel):
    """A delivery address for the store."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    label: str | None = Field(default=None, max_length=40, description="Home, Office, ...")
    full_name: str = Field(max_length=120)
    phone: str = Field(max_length=20)
    line1: str = Field(max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    landmark: str | None = Field(default=None, max_length=120)
    city: str = Field(max_length=100)
    state: str = Field(max_length=100)
    postal_code: str = Field(max_length=20)
    country: str = Field(default="India", max_length=100)
    is_default: bool = False
