"""The Firestore half of a chat.

MongoDB decides whether a conversation may exist; this writes the matching
document the browser actually subscribes to. Only three fields matter to the
client, and only one of them matters to security:

    participants — the two Firebase uids, which the rules check on every read
    status       — 'active' or 'ended'; the rules refuse a new message unless
                   this says 'active', and only this server can change it
    lastMessage  — so a chat list can show a preview without reading messages

The Firestore SDK is synchronous, so every call is pushed off the event loop,
the same way the mailer does it.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.core.exceptions import ServiceUnavailableError
from app.services import firebase

CONVERSATIONS = "conversations"
MESSAGES = "messages"

_client: Any = None


def is_enabled() -> bool:
    return firebase.is_enabled()


def _db() -> Any:
    """The Firestore client, built once against the app Firebase already set up."""
    global _client
    if _client is not None:
        return _client

    if not firebase.is_enabled():
        raise ServiceUnavailableError(
            "Chat is not configured yet. Please try again later.",
            error_code="chat_unavailable",
        )

    from firebase_admin import firestore

    _client = firestore.client(app=firebase.get_app())
    return _client


async def create_conversation(
    *, conversation_id: str, participants: list[str], session_id: str
) -> None:
    """Opens the conversation the browser will subscribe to."""

    def _write() -> None:
        _db().collection(CONVERSATIONS).document(conversation_id).set(
            {
                "participants": participants,
                "sessionId": session_id,
                # Not active yet: the astrologer has not accepted, and the rules
                # will refuse messages until they do.
                "status": "pending",
                "lastMessage": None,
                "createdAt": datetime.now(UTC),
                "updatedAt": datetime.now(UTC),
            }
        )

    await asyncio.to_thread(_write)
    logger.info("Firestore conversation {} opened.", conversation_id)


async def set_status(conversation_id: str, status: str) -> None:
    """Opens or closes the conversation to new messages.

    This is the lever the whole thing turns on: the rules read `status`, and
    nothing but this server can write it.
    """

    def _write() -> None:
        _db().collection(CONVERSATIONS).document(conversation_id).update(
            {"status": status, "updatedAt": datetime.now(UTC)}
        )

    await asyncio.to_thread(_write)
    logger.info("Firestore conversation {} -> {}", conversation_id, status)


async def count_messages(conversation_id: str) -> int:
    """How many messages were exchanged, for the record kept in MongoDB."""

    def _count() -> int:
        stream = (
            _db()
            .collection(CONVERSATIONS)
            .document(conversation_id)
            .collection(MESSAGES)
            .stream()
        )
        return sum(1 for _ in stream)

    try:
        return await asyncio.to_thread(_count)
    except Exception as exc:  # noqa: BLE001 - a count is never worth failing over
        logger.warning("Could not count messages for {}: {}", conversation_id, exc)
        return 0


async def delete_conversation(conversation_id: str) -> None:
    """Removes a conversation and its messages. Used when a chat never started."""

    def _delete() -> None:
        doc = _db().collection(CONVERSATIONS).document(conversation_id)
        for message in doc.collection(MESSAGES).stream():
            message.reference.delete()
        doc.delete()

    try:
        await asyncio.to_thread(_delete)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not delete conversation {}: {}", conversation_id, exc)


async def mint_token(uid: str) -> str:
    """A Firebase custom token, so the browser can sign in to Firestore.

    Our own login issues our own JWT, which Firestore has never heard of. This
    is the bridge: the browser exchanges this for a Firebase session, and the
    rules then see a real uid instead of an anonymous request.
    """
    if not firebase.is_enabled():
        raise ServiceUnavailableError(
            "Chat is not configured yet. Please try again later.",
            error_code="chat_unavailable",
        )

    from firebase_admin import auth as firebase_auth

    def _mint() -> bytes:
        return firebase_auth.create_custom_token(uid, app=firebase.get_app())

    token = await asyncio.to_thread(_mint)
    return token.decode() if isinstance(token, bytes) else str(token)
