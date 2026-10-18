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
    """What this session costs and how far it has got."""

    coins_per_minute: int
    requested_minutes: int
    minutes_charged: int
    coins_charged: int
    # Coins left in the wallet, and what that buys at this rate — so the UI can
    # warn before the wallet empties rather than after.
    balance_coins: int
    minutes_left: int


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


class EndCallRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=200)


class SweepResult(BaseModel):
    missed: int
    dropped: int
    capped: int
