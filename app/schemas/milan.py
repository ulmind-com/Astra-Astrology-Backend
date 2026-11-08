"""Schemas for the multi-party Vedic chamber.

Two shapes of seat leave this service, and keeping them apart is the point:
`MilanSeatOut` carries the join code and goes only to the host, while
`MilanOccupantOut` is what everyone in the room sees of everyone else. A
guest must never be handed another guest's code, and the astrologer has no
use for any of them.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CallParty, CallStatus, ConsultationMode
from app.models.milan import MAX_GUESTS_CEILING
from app.schemas.call import CallCredentials

PURPOSES = ("kundali_matching", "family_vastu", "other")


class CreateMilanRoomRequest(BaseModel):
    astrologer_id: str
    mode: ConsultationMode = ConsultationMode.VIDEO
    purpose: str = Field(default="kundali_matching")
    requested_minutes: int = Field(ge=1, le=600)
    # The seats to open, by who they are for: "Bride", "Groom's father". The
    # host holds a place of their own and is not listed here.
    guests: list[str] = Field(
        default_factory=list,
        max_length=MAX_GUESTS_CEILING,
        description="A label per guest seat, e.g. ['Bride', \"Bride's father\"]",
    )


class AddSeatRequest(BaseModel):
    label: str = Field(min_length=1, max_length=60)


class JoinAsGuestRequest(BaseModel):
    join_code: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=60)


class MilanOccupantOut(BaseModel):
    """One person in the room, as the others see them. No codes, no ids."""

    seat_id: str
    label: str
    display_name: str | None = None
    is_present: bool
    joined_at: datetime | None = None


class MilanSeatOut(MilanOccupantOut):
    """The host's view of a seat, which is the only view with the code in it."""

    join_code: str
    is_revoked: bool = False


class MilanBilling(BaseModel):
    """What the room costs. Shown to the host and the astrologer, not guests."""

    coins_per_minute: int
    minutes_booked: int
    minutes_charged: int
    coins_charged: int


class MilanRoomOut(BaseModel):
    id: str
    purpose: str
    mode: ConsultationMode
    status: CallStatus

    astrologer_id: str
    astrologer_name: str | None = None
    astrologer_avatar_url: str | None = None

    host_name: str | None = None
    # True for whoever is reading this response.
    viewer_is_host: bool = False
    viewer_is_astrologer: bool = False
    viewer_is_guest: bool = False

    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int = 0
    end_reason: str | None = None
    ended_by: CallParty | None = None

    max_guests: int
    seats_taken: int
    occupants: list[MilanOccupantOut] = Field(default_factory=list)

    # Host only. Empty for everyone else, so a guest cannot read the codes of
    # the people sitting with them.
    seats: list[MilanSeatOut] = Field(default_factory=list)
    # Host and astrologer only.
    billing: MilanBilling | None = None


class MilanRoomSession(BaseModel):
    """A room plus the credentials for the person who asked."""

    room: MilanRoomOut
    credentials: CallCredentials | None = None


class MilanSweepResult(BaseModel):
    missed: int = 0
    dropped: int = 0
    capped: int = 0
