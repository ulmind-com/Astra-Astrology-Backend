"""A one-to-one chat between a user and an astrologer.

Everything lives in MongoDB — the session and the messages both. The browser
never writes to a database directly: it posts a message to this API, which
decides whether the chat is still open, stores it, and pushes it to the other
person over the live socket.

That is what makes "the chat is closed" mean something. The check is on this
server, so a client that ignores the close, or replays an old request, is
simply refused — there is no path to the data that goes around it.

Messages do not live for ever. When a session ends they are given an expiry,
and MongoDB removes them on its own; how long that is, is the admin's to set
(see `PlatformSettings.chat_retention_days`).
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

    # Kept because accounts are mirrored into Firebase Auth and older sessions
    # recorded them. Nothing in chat reads them any more.
    user_uid: str
    astrologer_uid: str

    # Same value as this document's own id. Kept so links and logs written
    # before messages moved into MongoDB still resolve.
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


class ChatMessage(TimestampedDocument):
    """One line of a conversation.

    Append-only as far as the API is concerned: there is no route that edits
    or deletes a single message, because a transcript either side can rewrite
    is worth nothing when a session is disputed.

    `expires_at` is what eventually removes it. It stays null while the chat
    is open — an ongoing conversation must never vanish underneath the people
    having it — and is set when the session ends, to `ended_at + retention`.
    MongoDB's TTL monitor deletes the document once that moment passes, so
    nothing has to run on a schedule and nothing can forget.
    """

    session_id: PydanticObjectId
    sender_id: PydanticObjectId

    text: str = Field(max_length=4000)

    # The server's clock, always. A client-set time could reorder history.
    sent_at: datetime

    # Null until the session ends; see the class docstring.
    expires_at: datetime | None = None

    class Settings:
        name = "chat_messages"
        indexes = [
            # The one query this collection exists for: a session's messages,
            # oldest first.
            pymongo.IndexModel(
                [("session_id", pymongo.ASCENDING), ("sent_at", pymongo.ASCENDING)],
                name="chat_message_session",
            ),
            # MongoDB deletes a document once `expires_at` has passed.
            # expireAfterSeconds=0 means "at exactly that time" rather than
            # "that long afterwards" — the delay is carried by the field, so
            # changing the retention is a matter of rewriting these dates
            # rather than rebuilding the index.
            pymongo.IndexModel(
                [("expires_at", pymongo.ASCENDING)],
                name="chat_message_ttl",
                expireAfterSeconds=0,
            ),
        ]


class ChatRead(TimestampedDocument):
    """How far one person has got in one conversation.

    One document per reader rather than a flag per message, which is what
    makes ticks cheap: catching up on a hundred messages is a single small
    write, and every tick is then worked out by comparing timestamps.

    Expires with the messages it refers to.
    """

    session_id: PydanticObjectId
    user_id: PydanticObjectId

    # Their app has the messages.
    delivered_at: datetime | None = None
    # They were actually looking.
    read_at: datetime | None = None

    expires_at: datetime | None = None

    class Settings:
        name = "chat_reads"
        indexes = [
            pymongo.IndexModel(
                [("session_id", pymongo.ASCENDING), ("user_id", pymongo.ASCENDING)],
                name="chat_read_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("expires_at", pymongo.ASCENDING)],
                name="chat_read_ttl",
                expireAfterSeconds=0,
            ),
        ]
