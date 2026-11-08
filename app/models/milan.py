"""The multi-party Vedic chamber — the Milan Room.

A kundali matching or family vastu consultation is rarely one person. The
groom, the bride and a guardian or two sit in different cities, and all of
them need to be in the same room as the astrologer.

This is deliberately *not* a `CallSession` with extra fields. A call is
1:1 all the way down — two heartbeats, two parties, one payer who is also
the only client — and widening it would put the busiest, most money-critical
path in the product at risk for a feature it does not serve. A room is its
own thing: one host who pays, several guests who do not, and an astrologer.

Guests join by a per-seat code rather than an account, because asking a
bride's father in another country to register before a scheduled
consultation is how a consultation gets missed. The code is the credential,
so it is long, it belongs to exactly one seat, it only works while the room
is live, and the host can revoke it.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument
from app.models.enums import CallParty, CallStatus, ConsultationMode

# A room holds the host, their guests and the astrologer. The spec is a
# three-to-four person chamber; this is the ceiling an admin may raise to,
# not the default.
MAX_GUESTS_CEILING = 8

# How long a seat stays "occupied" after its last heartbeat. Short enough
# that a dropped guest frees their seat, long enough to survive a lift.
SEAT_GRACE_SECONDS = 90


class MilanSeat(BaseModel):
    """One invited place in the room.

    A seat is created empty, with a code the host passes to one person. It is
    occupied when someone opens that code, and freed again when they leave or
    stop checking in.
    """

    seat_id: str = Field(description="Short id, unique within this room")
    label: str = Field(max_length=60, description="Who this seat is for, e.g. 'Bride'")

    # The credential. Never returned to anyone but the host.
    join_code: str = Field(description="Secret; the whole of a guest's authority")

    # Set when a signed-in user opens the code. Guests need no account, so
    # this stays None for most of them.
    user_id: PydanticObjectId | None = None
    display_name: str | None = Field(default=None, max_length=60)

    joined_at: datetime | None = None
    last_seen_at: datetime | None = None
    left_at: datetime | None = None

    # The host can take a seat back — a code shared with the wrong person
    # must be cancellable without ending the consultation.
    revoked_at: datetime | None = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None


class MilanRoom(TimestampedDocument):
    """One multi-party consultation.

    The money is frozen at creation, exactly as a call freezes it: an admin
    re-pricing mid-session must not restate what the host has already agreed
    to pay.
    """

    # Who booked it, and whose wallet pays. Guests are never charged.
    host_user_id: PydanticObjectId
    astrologer_id: PydanticObjectId
    astrologer_user_id: PydanticObjectId

    purpose: str = Field(
        default="kundali_matching",
        description="kundali_matching | family_vastu | other",
    )
    # Voice or video. A Milan room is normally video, but a family on a poor
    # line may want audio only, and the room does not care which.
    mode: ConsultationMode = ConsultationMode.VIDEO

    # A fresh ZEGOCLOUD room every time. Reusing one would let a token from a
    # previous consultation back into this family's conversation.
    room_id: str

    status: CallStatus = CallStatus.RINGING

    # When the astrologer accepted, which is when billing starts. Nobody pays
    # for the time their guests spend arriving.
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int = 0

    ended_by: CallParty | None = None
    end_reason: str | None = None

    # The host's and the astrologer's own check-ins. Guests check in on their
    # seat. The room lives only while the host is here — see the service.
    host_seen_at: datetime | None = None
    astrologer_seen_at: datetime | None = None

    # --- price, frozen when the room is created -------------------------
    coins_per_minute: int = Field(default=0, ge=0)
    commission_percent: float = Field(default=0.0, ge=0, le=100)
    coin_value_paise: int = Field(default=0, ge=0)

    # A hard cap: the room ends here even if the wallet could carry on.
    requested_minutes: int = Field(default=0, ge=0)

    # --- what has actually been taken ------------------------------------
    minutes_charged: int = Field(default=0, ge=0)
    coins_charged: int = Field(default=0, ge=0)
    earning_paise: int = Field(default=0, ge=0)

    # --- the guests -------------------------------------------------------
    max_guests: int = Field(default=3, ge=0, le=MAX_GUESTS_CEILING)
    seats: list[MilanSeat] = Field(default_factory=list)

    class Settings:
        name = "milan_rooms"
        indexes = [
            pymongo.IndexModel(
                [("room_id", pymongo.ASCENDING)], name="milan_room_unique", unique=True
            ),
            pymongo.IndexModel(
                [("host_user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="milan_host_recent",
            ),
            pymongo.IndexModel(
                [("astrologer_user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="milan_astrologer_recent",
            ),
            pymongo.IndexModel([("status", pymongo.ASCENDING)], name="milan_status"),
            # A guest arrives with nothing but a code, so this lookup has to be
            # an index hit rather than a scan of every room ever held.
            pymongo.IndexModel(
                [("seats.join_code", pymongo.ASCENDING)], name="milan_seat_code"
            ),
        ]
