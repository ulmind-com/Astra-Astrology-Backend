"""Chat request and response shapes."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import CallParty, ChatStatus
from app.schemas.call import CallPeer, SessionBilling


class StartChatRequest(BaseModel):
    astrologer_id: str
    requested_minutes: int = Field(ge=1, le=600)


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
    billing: SessionBilling | None = None


class ChatSessionOut(BaseModel):
    chat: ChatOut


class SendMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: str
    session_id: str
    sender_id: str
    text: str
    sent_at: datetime


class ReadMarkerOut(BaseModel):
    user_id: str
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class TranscriptOut(BaseModel):
    """Everything a chat window needs to draw itself from cold.

    Messages and markers together, because the ticks are worked out by
    comparing the two and a window that had one without the other would show
    the wrong state for a moment.
    """

    messages: list[MessageOut]
    reads: list[ReadMarkerOut]


class MarkProgressRequest(BaseModel):
    level: Literal["delivered", "read"] = "read"


class EndChatRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=200)


class ChatSweepResult(BaseModel):
    missed: int
    dropped: int
    capped: int
