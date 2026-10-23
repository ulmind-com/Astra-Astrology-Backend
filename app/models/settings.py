"""Platform-wide settings an admin can change at runtime.

The coin rate lives here rather than in the environment because the client has
to be able to change it from the panel. It decides how much a person gets for
their money, so every change is recorded with the admin who made it.
"""

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument

SETTINGS_KEY = "platform"


class PlatformSettings(TimestampedDocument):
    """A singleton. The unique index on `key` makes a second row impossible."""

    key: str = SETTINGS_KEY

    # How many coins one rupee buys. An integer, so that a whole-rupee recharge
    # can never produce a fractional coin.
    coins_per_rupee: int = Field(default=1, ge=1, le=10_000)

    # What a user may top up. Here rather than in the environment because the
    # client changes these as offers come and go, and a redeploy for that would
    # be absurd.
    min_recharge_paise: int = Field(default=1_000, ge=100)  # Rs 10
    max_recharge_paise: int = Field(default=5_000_000, ge=100)  # Rs 50,000

    # What a consultation costs, in coins per started minute. An astrologer may
    # override any of these; leaving theirs unset means "use the platform's".
    # One place to set a price means onboarding needs no pricing decision.
    default_chat_coins_per_minute: int = Field(default=3, ge=1, le=100_000)
    default_call_coins_per_minute: int = Field(default=5, ge=1, le=100_000)
    default_video_coins_per_minute: int = Field(default=8, ge=1, le=100_000)

    # The platform's share. Also overridable per astrologer.
    default_commission_percent: float = Field(default=20.0, ge=0, le=100)

    # The longest a user may book in one go, and the least.
    min_session_minutes: int = Field(default=1, ge=1, le=600)
    max_session_minutes: int = Field(default=60, ge=1, le=600)

    # How long a finished chat's messages are kept before MongoDB removes
    # them. Counted from the moment the session ends, and applied by a TTL
    # index rather than a job, so nothing has to run for it to happen.
    #
    # Zero means delete as soon as the chat ends. That is allowed, but it
    # leaves nothing to look at when someone disputes what was said or what
    # they were charged — so the default keeps a week.
    chat_retention_days: int = Field(default=7, ge=0, le=3650)

    # ---------------------------------------------------------- appointments
    # The platform's share of a booked appointment. Taken from the user's
    # wallet when they book, and not returned if they cancel — which is what
    # stops a calendar filling up with bookings nobody intends to keep.
    appointment_commission_percent: float = Field(default=20.0, ge=0, le=100)

    # What a user may book in one go. The shortest is also the step: a booking
    # is always a whole number of these.
    min_appointment_minutes: int = Field(default=15, ge=5, le=600)
    max_appointment_minutes: int = Field(default=180, ge=5, le=600)

    # How far ahead the calendar opens. Beyond this an astrologer's windows
    # are not offered, so a booking cannot be made for a date nobody has
    # thought about yet.
    appointment_booking_days_ahead: int = Field(default=30, ge=1, le=365)

    # --------------------------------------------------------- face reading
    # What one face reading costs, in coins. Zero makes it free, which is a
    # legitimate choice while the rule set is still being tuned.
    face_reading_coins: int = Field(default=50, ge=0, le=1_000_000)

    # Whether the feature is offered at all. Lets an admin take it down
    # without a deploy if a reading is going wrong.
    face_reading_enabled: bool = True

    # What one palm reading costs, in coins. Zero makes it free, matching how face
    # reading is priced, so the admin sets both the same way.
    palm_reading_coins: int = Field(default=50, ge=0, le=1_000_000)

    # Lets the admin take palm reading down without a deploy, which matters for a
    # feature whose accuracy depends on photo quality in the field.
    palm_reading_enabled: bool = True

    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "platform_settings"
        indexes = [
            pymongo.IndexModel(
                [("key", pymongo.ASCENDING)], name="settings_key_unique", unique=True
            ),
        ]


class CoinRateChange(TimestampedDocument):
    """One row per change to the coin rate. Append-only, like the ledger."""

    from_rate: int
    to_rate: int
    changed_by: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=300)

    class Settings:
        name = "coin_rate_changes"
        indexes = [
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)], name="rate_change_recent"),
        ]
