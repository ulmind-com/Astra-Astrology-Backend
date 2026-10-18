"""Call request and response shapes."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CallParty, CallStatus, ConsultationMode


class StartCallRequest(BaseModel):
    astrologer_id: str
    mode: ConsultationMode = ConsultationMode.VIDEO


class CallPeer(BaseModel):
    """Who is on the other end, for the call screen."""

    name: str
    avatar_url: str | None = None


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
