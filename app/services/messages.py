"""The messages inside a chat.

MongoDB stores them; the live socket delivers them. There is no third party in
the middle and no database the browser can reach directly — a message is posted
to this API, checked, written, and pushed to the two people in the session.

Three rules this module keeps:

  * **A closed chat takes no messages.** The check is here, on the server, so
    it cannot be skipped by a client that ignored the close or replayed an old
    request. When the coins run out the session is ended and the next send is
    refused, whatever the browser tries.
  * **Nothing is edited.** There is no update path and no delete-one path. A
    transcript either side could rewrite is worth nothing in a dispute.
  * **The clock is ours.** `sent_at` is the server's time, never the client's,
    or a wrong device clock could reorder the conversation.

Expiry is set when the session ends, not when the message is written — an
ongoing conversation must never start disappearing underneath the people having
it. See `expire_session`.
"""

from datetime import timedelta

from beanie import PydanticObjectId
from beanie.operators import In
from loguru import logger

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.base import utcnow
from app.models.chat import ChatMessage, ChatRead, ChatSession
from app.models.enums import ChatStatus
from app.models.user import User

# The statuses in which a chat will accept a new message.
OPEN_STATUSES = {ChatStatus.ACTIVE}

MAX_MESSAGES_RETURNED = 500


def _participants(session: ChatSession) -> tuple[PydanticObjectId, PydanticObjectId]:
    return session.user_id, session.astrologer_user_id


def is_participant(session: ChatSession, user: User) -> bool:
    return user.id in _participants(session)


def require_participant(session: ChatSession, user: User) -> None:
    if not is_participant(session, user):
        raise ForbiddenError("This is not your chat.", error_code="not_a_participant")


async def _push(session: ChatSession, message: dict) -> None:
    """Sends to both sides. Never raises — a lost push is a late screen only."""
    from app.services import realtime

    for user_id in _participants(session):
        try:
            await realtime.publish_chat(user_id, message)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Chat push skipped for {}: {}", user_id, exc)


# ------------------------------------------------------------------ sending
async def send(
    *, session: ChatSession, sender: User, text: str
) -> ChatMessage:
    """Stores one message and delivers it."""
    require_participant(session, sender)

    body = text.strip()
    if not body:
        raise BadRequestError("Write something first.", error_code="empty_message")
    if len(body) > 4000:
        raise BadRequestError("That message is too long.", error_code="message_too_long")

    if session.status not in OPEN_STATUSES:
        raise BadRequestError(
            "This chat has ended.", error_code="chat_not_active"
        )

    assert session.id is not None
    message = ChatMessage(
        session_id=session.id,
        sender_id=sender.id,
        text=body,
        sent_at=utcnow(),
    )
    await message.insert()

    # Kept on the session so history can show a count without reading the
    # messages — which matters once they have been expired away.
    session.message_count += 1
    await session.save()

    await _push(session, {"type": "chat_message", "data": to_public(message)})
    return message


def to_public(message: ChatMessage) -> dict:
    return {
        "id": str(message.id),
        "session_id": str(message.session_id),
        "sender_id": str(message.sender_id),
        "text": message.text,
        "sent_at": message.sent_at.isoformat(),
    }


# ------------------------------------------------------------------ reading
async def history(
    *, session: ChatSession, viewer: User, limit: int = MAX_MESSAGES_RETURNED
) -> list[ChatMessage]:
    """The conversation so far, oldest first."""
    require_participant(session, viewer)
    assert session.id is not None
    return (
        await ChatMessage.find(ChatMessage.session_id == session.id)
        .sort(+ChatMessage.sent_at)
        .limit(min(limit, MAX_MESSAGES_RETURNED))
        .to_list()
    )


async def markers(session: ChatSession) -> list[ChatRead]:
    """Both participants' read markers, which is what draws the ticks."""
    assert session.id is not None
    return await ChatRead.find(ChatRead.session_id == session.id).to_list()


def marker_to_public(marker: ChatRead) -> dict:
    return {
        "user_id": str(marker.user_id),
        "delivered_at": marker.delivered_at.isoformat() if marker.delivered_at else None,
        "read_at": marker.read_at.isoformat() if marker.read_at else None,
    }


async def mark_progress(
    *, session: ChatSession, viewer: User, level: str
) -> ChatRead:
    """Says how far this person has got.

    `delivered` means their app has the messages; `read` means they were
    looking. Reading implies delivery, so marking read writes both — otherwise
    a message could show two blue ticks without ever having shown grey ones.

    Timestamps only ever move forward: a late "delivered" arriving after a
    "read" must not drag the marker backwards and un-blue the ticks.
    """
    require_participant(session, viewer)
    if level not in {"delivered", "read"}:
        raise BadRequestError("Unknown progress level.", error_code="bad_level")

    assert session.id is not None
    now = utcnow()

    marker = await ChatRead.find_one(
        ChatRead.session_id == session.id, ChatRead.user_id == viewer.id
    )
    if marker is None:
        marker = ChatRead(session_id=session.id, user_id=viewer.id)

    if marker.delivered_at is None or now > marker.delivered_at:
        marker.delivered_at = now
    if level == "read" and (marker.read_at is None or now > marker.read_at):
        marker.read_at = now

    await marker.save()
    await _push(
        session,
        {
            "type": "chat_read",
            "data": {"session_id": str(session.id), **marker_to_public(marker)},
        },
    )
    return marker


# ----------------------------------------------------------------- expiring
async def expire_session(session: ChatSession, *, retention_days: int | None = None) -> int:
    """Gives a finished session's messages their expiry date.

    Called when the chat ends. With a retention of zero the rows are removed
    straight away rather than being given an expiry a moment in the past —
    MongoDB's TTL monitor only runs every sixty seconds, and "deleted when the
    chat ends" should not mean "deleted within the next minute".

    Returns how many messages were affected.
    """
    from app.services import settings as settings_service

    if retention_days is None:
        retention_days = (await settings_service.get_settings()).chat_retention_days

    assert session.id is not None
    if retention_days <= 0:
        deleted = await ChatMessage.find(ChatMessage.session_id == session.id).delete()
        await ChatRead.find(ChatRead.session_id == session.id).delete()
        count = getattr(deleted, "deleted_count", 0)
        logger.info("Chat {} ended: {} message(s) removed at once.", session.id, count)
        return count

    expires_at = (session.ended_at or utcnow()) + timedelta(days=retention_days)
    result = await ChatMessage.find(ChatMessage.session_id == session.id).set(
        {ChatMessage.expires_at: expires_at}
    )
    await ChatRead.find(ChatRead.session_id == session.id).set(
        {ChatRead.expires_at: expires_at}
    )
    logger.info(
        "Chat {} ended: messages expire on {}.", session.id, expires_at.date()
    )
    return getattr(result, "modified_count", 0)


async def reschedule_expiry(retention_days: int) -> int:
    """Re-dates every finished chat after an admin changes the retention.

    Without this, a change would only affect chats that ended afterwards, and
    an admin shortening the period would be surprised to find months of old
    messages still sitting there.

    Only finished sessions are touched: a chat still in progress has no expiry
    yet and must not be given one.
    """
    finished = await ChatSession.find(
        In(ChatSession.status, [ChatStatus.ENDED, ChatStatus.DECLINED, ChatStatus.MISSED])
    ).to_list()

    touched = 0
    for session in finished:
        if session.ended_at is None:
            continue
        touched += await expire_session(session, retention_days=retention_days)

    logger.info(
        "Chat retention set to {} day(s); {} message(s) re-dated.", retention_days, touched
    )
    return touched


async def count_for(session_id: PydanticObjectId) -> int:
    return await ChatMessage.find(ChatMessage.session_id == session_id).count()


async def purge(session_id: PydanticObjectId) -> None:
    """Removes a conversation outright. Used when a chat never started."""
    await ChatMessage.find(ChatMessage.session_id == session_id).delete()
    await ChatRead.find(ChatRead.session_id == session_id).delete()


async def session_for(session_id: PydanticObjectId) -> ChatSession:
    session = await ChatSession.get(session_id)
    if session is None:
        raise NotFoundError("Chat not found.", error_code="chat_not_found")
    return session
