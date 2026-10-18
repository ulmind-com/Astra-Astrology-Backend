"""A one-to-one chat between a user and an astrologer.

The messages live in Firestore, because the browser subscribes to them directly
and that is what makes a chat feel live. Everything that decides *whether* the
conversation may happen lives here, in MongoDB:

    MongoDB   — the authority: who, when, how long, and (later) what it cost
    Firestore — the pipe: the messages, and a mirror of `status`

The mirror is the important part. Firestore's rules refuse a new message unless
the conversation there says `active`, and only this server can change that
field. So closing a chat is not a request the client can ignore — once the
server writes `ended`, the browser physically cannot send another message.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument
from app.models.enums import CallParty, ChatStatus


class ChatSession(TimestampedDocument):
    user_id: PydanticObjectId
    astrologer_id: PydanticObjectId
    astrologer_user_id: PydanticObjectId

    # Firebase uids, copied in when the session opens — Firestore only knows
    # people by these, and looking them up again later would be a second
    # source of truth.
    user_uid: str
    astrologer_uid: str

    # The Firestore document id. Same value as this document's own id, so the
    # two halves can always be matched up by eye.
    conversation_id: str

    status: ChatStatus = ChatStatus.REQUESTED

    # When the astrologer accepted. Nobody is charged for waiting.
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int = 0

    ended_by: CallParty | None = None
    end_reason: str | None = None

    user_seen_at: datetime | None = None
    astrologer_seen_at: datetime | None = None

    # --- price, frozen when the session starts ---------------------------
    # An admin re-pricing mid-session must not change a session in progress,
    # and a later change to the coin rate must not restate what was earned.
    coins_per_minute: int = Field(default=0, ge=0)
    commission_percent: float = Field(default=0.0, ge=0, le=100)
    coin_value_paise: int = Field(default=0, ge=0)

    # What the user booked. A hard cap: the session ends here even if the
    # wallet could carry on.
    requested_minutes: int = Field(default=0, ge=0)

    # --- what has actually been taken ------------------------------------
    minutes_charged: int = Field(default=0, ge=0)
    coins_charged: int = Field(default=0, ge=0)
    earning_paise: int = Field(default=0, ge=0)

    message_count: int = 0

    class Settings:
        name = "chat_sessions"
        indexes = [
            pymongo.IndexModel(
                [("conversation_id", pymongo.ASCENDING)],
                name="chat_conversation_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="chat_user_recent",
            ),
            pymongo.IndexModel(
                [
                    ("astrologer_user_id", pymongo.ASCENDING),
                    ("created_at", pymongo.DESCENDING),
                ],
                name="chat_astrologer_recent",
            ),
            pymongo.IndexModel([("status", pymongo.ASCENDING)], name="chat_status"),
        ]
