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
    # Coins held in escrow for the remaining balance until completion
    held_coins: int = Field(default=0, ge=0)
    # Status of held balance coins: "none", "held", "released", "captured"
    held_status: str = Field(default="none")

    # Astrologer's cancellation window for client in minutes (e.g. 30m)
    cancellation_window_minutes: int = Field(default=30, ge=0)
    # The exact UTC deadline until which client is allowed to cancel
    cancel_deadline: datetime | None = None

    cancelled_at: datetime | None = None
    cancelled_by: PydanticObjectId | None = None
    cancel_reason: str | None = Field(default=None, max_length=300)
    completed_at: datetime | None = None

    # Set once the astrologer has been reminded, so a reminder is not repeated
    # every time the panel re-reads its schedule.
    reminded_at: datetime | None = None

    user_note: str | None = Field(default=None, max_length=1000)

    # Consultation focus area (e.g. marriage, career, wealth, health, dosha, spiritual)
    consultation_pillar: str | None = Field(default=None, max_length=50)
    kundli_id: PydanticObjectId | None = None
    birth_details: dict | None = None

    # Astrologer's sacred prescription & remedial advice (gemstone, mantra, rudraksha, notes)
    prescription: dict | None = None

    # Vedic Muhurat classification calculated for the slot (amrit, shubh, labh, char, etc.)
    muhurat_type: str | None = Field(default=None, max_length=50)

    # AI Pre-Flight Astrological Intelligence Dossier (generated 15m prior or on-demand)
    preflight_dossier: dict | None = None

    # Cosmic Resonance & Synastry Compatibility Score (0-100%)
    cosmic_synergy_score: int | None = Field(default=None, ge=0, le=100)

    # Post-session Divya Paramarsha PDF Certificate data
    certificate_data: dict | None = None

    # Cosmic standby waitlist for auto-fill on cancellation
    standby_queue: list[dict] = Field(default_factory=list)

    # Courtesy Reschedule (Allowed 1 time by astrologer without extra fee)
    rescheduled_count: int = Field(default=0, ge=0)
    rescheduled_at: datetime | None = None
    previous_starts_at: datetime | None = None
    reschedule_reason: str | None = Field(default=None, max_length=500)

    # Client No-Show Tracking (when client fails to join chamber after 10-15m wait)
    is_no_show: bool = False
    no_show_marked_at: datetime | None = None
    no_show_wait_minutes: int | None = None

    # Dedicated CallSession ID for video chamber
    call_session_id: PydanticObjectId | None = None

    # Brahma Pause Seeker Auto-Rescue Engine
    brahma_pause_affected: bool = False
    brahma_pause_reason: str | None = None
    brahma_pause_until: datetime | None = None
    rescue_deadline: datetime | None = None

    # Client Screening & Abuse Shield (Red-Flag & Call Termination)
    abuse_flagged: bool = False
    abuse_reason: str | None = None
    abuse_flagged_at: datetime | None = None
    abuse_notes: str | None = None

    # Birth Time Rectification (BTR) Authority
    btr_requested: bool = False
    btr_request_note: str | None = None
    btr_requested_at: datetime | None = None
    btr_fulfilled: bool = False
    btr_updated_at: datetime | None = None

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
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING)],
                unique=True,
                partialFilterExpression={"status": "booked"},
                name="unique_active_user_booking",
            ),
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
