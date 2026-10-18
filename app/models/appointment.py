"""Scheduled appointments: what an astrologer offers, and what is booked.

Three documents, and the third is the interesting one.

    AvailabilityWindow  — "I am free on this date, between these hours"
    Appointment         — one booking: who, when, how long, what it cost
    AppointmentSlot     — one five-minute unit of an astrologer's time

`AppointmentSlot` exists for a single reason: two people must never be able to
book overlapping times. Checking for a clash and then writing the booking does
not achieve that — two requests can both read "free" before either writes. So
a booking instead claims one row per five minutes it occupies, and a unique
index on (astrologer, start) makes the second claim fail at the database.
The insert *is* the lock, the same way the wallet's idempotency key is.

Five minutes rather than fifteen because appointments are booked in real
lengths — forty minutes is a perfectly ordinary request, and a coarser grid
would simply refuse it.
"""

from datetime import date as date_type
from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument
from app.models.enums import AppointmentStatus

# The grid everything is snapped to. Changing this invalidates existing slot
# rows, so it is a constant rather than a setting.
SLOT_MINUTES = 5


class AvailabilityWindow(TimestampedDocument):
    """A stretch of one day an astrologer is willing to be booked in.

    Stored as explicit dates rather than a repeating weekly rule. A rule would
    have to carry exceptions — holidays, a week off, one Tuesday that does not
    count — and every one of those is a way for the calendar shown to a user
    to disagree with what the astrologer believes they agreed to.
    """

    astrologer_id: PydanticObjectId

    # The day this window belongs to, in the platform's timezone. Kept beside
    # the instants so a day's windows can be listed without date arithmetic.
    day: date_type

    # Both UTC. The booking grid is built between them.
    starts_at: datetime
    ends_at: datetime

    class Settings:
        name = "availability_windows"
        indexes = [
            pymongo.IndexModel(
                [("astrologer_id", pymongo.ASCENDING), ("starts_at", pymongo.ASCENDING)],
                name="availability_astrologer_start",
            ),
            pymongo.IndexModel(
                [("astrologer_id", pymongo.ASCENDING), ("day", pymongo.ASCENDING)],
                name="availability_astrologer_day",
            ),
        ]


class Appointment(TimestampedDocument):
    """One booking.

    The money is frozen here at the moment of booking — the price, the
    commission, and the coin rate that converted one into the other. An admin
    changing any of them later must not restate what someone has already paid.
    """

    astrologer_id: PydanticObjectId
    astrologer_user_id: PydanticObjectId
    user_id: PydanticObjectId

    starts_at: datetime
    ends_at: datetime
    minutes: int = Field(ge=1)

    status: AppointmentStatus = AppointmentStatus.BOOKED

    # --- money, as agreed at booking time --------------------------------
    # The whole appointment, in paise.
    price_paise: int = Field(default=0, ge=0)
    # The platform's share, taken now and not given back.
    commission_percent: float = Field(default=0.0, ge=0, le=100)
    deposit_paise: int = Field(default=0, ge=0)
    # What that came to in coins, and the rate used.
    deposit_coins: int = Field(default=0, ge=0)
    coins_per_rupee: int = Field(default=1, ge=1)
    # What is still owed to the astrologer at the session itself.
    balance_due_paise: int = Field(default=0, ge=0)

    cancelled_at: datetime | None = None
    cancelled_by: PydanticObjectId | None = None
    cancel_reason: str | None = Field(default=None, max_length=300)

    # Set once the astrologer has been reminded, so a reminder is not repeated
    # every time the panel re-reads its schedule.
    reminded_at: datetime | None = None

    user_note: str | None = Field(default=None, max_length=1000)

    class Settings:
        name = "appointments"
        indexes = [
            pymongo.IndexModel(
                [("astrologer_id", pymongo.ASCENDING), ("starts_at", pymongo.ASCENDING)],
                name="appointment_astrologer_start",
            ),
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("starts_at", pymongo.DESCENDING)],
                name="appointment_user_recent",
            ),
            pymongo.IndexModel([("status", pymongo.ASCENDING)], name="appointment_status"),
        ]


class AppointmentSlot(TimestampedDocument):
    """Five minutes of one astrologer's time, claimed by one appointment.

    The unique index is the whole point: it is what makes a double booking
    impossible rather than unlikely. Released when an appointment is cancelled.
    """

    astrologer_id: PydanticObjectId
    appointment_id: PydanticObjectId
    starts_at: datetime

    class Settings:
        name = "appointment_slots"
        indexes = [
            pymongo.IndexModel(
                [("astrologer_id", pymongo.ASCENDING), ("starts_at", pymongo.ASCENDING)],
                name="appointment_slot_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("appointment_id", pymongo.ASCENDING)], name="appointment_slot_booking"
            ),
        ]
