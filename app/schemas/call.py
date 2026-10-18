"""Call request and response shapes."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CallParty, CallStatus, ConsultationMode


class StartCallRequest(BaseModel):
    astrologer_id: str
    mode: ConsultationMode = ConsultationMode.VIDEO
    # How long they booked. A hard cap, and what the wallet is checked against.
    requested_minutes: int = Field(ge=1, le=600)


class CallPeer(BaseModel):
    """Who is on the other end, for the call screen."""

    name: str
    avatar_url: str | None = None


class SessionBilling(BaseModel):
    """Everything the session screen shows, worked out on the server.

    The client could compute most of this from a start time and a rate, but it
    would drift — and would be wrong at exactly the moment it matters, which is
    the minute before someone is cut off.
    """

    coins_per_minute: int
    requested_minutes: int
    minutes_charged: int
    coins_charged: int

    # Of the time booked, how much is left.
    minutes_remaining: int
    # Coins left in the wallet, and how many more minutes they would buy.
    balance_coins: int
    minutes_left: int
    # Whether there is room and money to buy more time.
    can_extend: bool
    max_extend_minutes: int


class CallOut(BaseModel):
    id: str
    room_id: str
    mode: ConsultationMode
    status: CallStatus

    user_id: str
    astrologer_id: str
    astrologer_user_id: str
    peer: CallPeer | None = None

    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int = 0
    ended_by: CallParty | None = None
    end_reason: str | None = None
    created_at: datetime
    billing: SessionBilling | None = None


class CallCredentials(BaseModel):
    """Everything the SDK needs, and nothing it does not.

    The ServerSecret is absent on purpose — it signs the token here and never
    leaves the server.
    """

    app_id: int
    token: str
    room_id: str
    user_id: str
    user_name: str
    server_url: str | None = None
    server_url_backup: str | None = None


class CallSessionOut(BaseModel):
    call: CallOut
    credentials: CallCredentials | None = None


class ExtendRequest(BaseModel):
    extra_minutes: int = Field(ge=1, le=600)


class EndCallRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=200)


class SweepResult(BaseModel):
    missed: int
    dropped: int
    capped: int
