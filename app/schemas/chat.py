"""Chat request and response shapes."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CallParty, ChatStatus
from app.schemas.call import CallPeer


class StartChatRequest(BaseModel):
    astrologer_id: str


class ChatOut(BaseModel):
    id: str
    conversation_id: str
    status: ChatStatus

    user_id: str
    astrologer_id: str
    astrologer_user_id: str
    peer: CallPeer | None = None

    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int = 0
    message_count: int = 0
    ended_by: CallParty | None = None
    end_reason: str | None = None
    created_at: datetime


class FirebaseCredentials(BaseModel):
    """What the browser needs to reach Firestore as itself.

    The custom token is short-lived and single-purpose: it only proves which
    Firebase user this is, so the rules can check participation.
    """

    custom_token: str
    uid: str
    project_id: str


class ChatSessionOut(BaseModel):
    chat: ChatOut
    firebase: FirebaseCredentials | None = None


class EndChatRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=200)


class ChatSweepResult(BaseModel):
    missed: int
    dropped: int
    capped: int
