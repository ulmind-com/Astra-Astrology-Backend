"""Chat sessions.

The shape mirrors calls on purpose — ask, accept, talk, end, and a sweeper for
the ones nobody closes — because the problems are the same and solving them
twice differently would be a liability.

What is different is the pipe. A call's audio flows through ZEGOCLOUD; a chat's
messages flow through Firestore, straight from one browser to the other. That
means there is no server in the middle to stop a message, so stopping one is
done by closing the conversation in Firestore, which its rules then enforce.
"""

from datetime import UTC, datetime, timedelta

from beanie import PydanticObjectId
from loguru import logger

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.astrologer import Astrologer
from app.models.chat import ChatSession
from app.models.enums import AccountStatus, CallParty, ChatStatus, ConsultationMode
from app.models.user import User
from app.services import billing

LIVE_STATUSES = [ChatStatus.REQUESTED, ChatStatus.ACTIVE]


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def _live_chat_for(user_id: PydanticObjectId) -> ChatSession | None:
    return await ChatSession.find_one(
        {
            "$or": [{"user_id": user_id}, {"astrologer_user_id": user_id}],
            "status": {"$in": [s.value for s in LIVE_STATUSES]},
        }
    )


async def start_chat(
    *, user: User, astrologer_id: PydanticObjectId, requested_minutes: int
) -> ChatSession:
    """Asks an astrologer for a chat."""
    if not user.firebase_uid:
        # Without a Firebase identity the browser cannot sign in to Firestore,
        # so it could never read the conversation it is about to be put in.
        raise BadRequestError(
            "This account cannot use chat yet. Please contact support.",
            error_code="no_chat_identity",
        )

    profile = await Astrologer.get(astrologer_id)
    if profile is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    account = await User.get(profile.user_id)
    if account is None or account.status is not AccountStatus.ACTIVE:
        raise BadRequestError(
            "This astrologer is not available.", error_code="astrologer_unavailable"
        )
    if not account.firebase_uid:
        raise BadRequestError(
            "This astrologer cannot take chats yet.", error_code="no_chat_identity"
        )

    if ConsultationMode.CHAT not in profile.modes_enabled:
        raise BadRequestError(
            "This astrologer does not take chats.", error_code="mode_not_offered"
        )
    # Presence, not the stored flag: an astrologer whose panel has closed is
    # not there to answer, whatever the flag still says.
    from app.services import presence

    if not presence.is_effectively_online(profile.availability):
        raise BadRequestError(
            "This astrologer is offline right now.", error_code="astrologer_offline"
        )
    if not profile.availability.is_available_for_chat:
        raise BadRequestError(
            "This astrologer is not taking chats at the moment.", error_code="mode_paused"
        )

    if await _live_chat_for(user.id) is not None:
        raise ConflictError("You are already in a chat.", error_code="already_in_chat")
    if await _live_chat_for(profile.user_id) is not None:
        raise ConflictError(
            "This astrologer is in another chat.", error_code="astrologer_busy"
        )

    price = await billing.price_for(profile, ConsultationMode.CHAT)
    await billing.check_can_start(
        user_id=user.id, price=price, requested_minutes=requested_minutes
    )

    session = ChatSession(
        user_id=user.id,
        astrologer_id=profile.id,
        astrologer_user_id=profile.user_id,
        user_uid=user.firebase_uid,
        astrologer_uid=account.firebase_uid,
        conversation_id="pending",
        status=ChatStatus.REQUESTED,
        user_seen_at=_now(),
        coins_per_minute=price.coins_per_minute,
        commission_percent=price.commission_percent,
        coin_value_paise=price.coin_value_paise,
        requested_minutes=requested_minutes,
    )
    await session.insert()

    # Kept equal to the Mongo id so older links and logs still resolve.
    session.conversation_id = str(session.id)
    await session.save()

    logger.info("Chat {} requested: {} -> {}", session.id, user.email, account.email)
    return session


async def get_session(session_id: PydanticObjectId) -> ChatSession:
    session = await ChatSession.get(session_id)
    if session is None:
        raise NotFoundError("Chat not found.", error_code="chat_not_found")
    return session


def _party(session: ChatSession, user: User) -> CallParty:
    if session.user_id == user.id:
        return CallParty.USER
    if session.astrologer_user_id == user.id:
        return CallParty.ASTROLOGER
    raise ForbiddenError("This is not your chat.", error_code="not_your_chat")


async def load_for(session_id: PydanticObjectId, user: User) -> tuple[ChatSession, CallParty]:
    session = await get_session(session_id)
    return session, _party(session, user)


async def accept_chat(*, session_id: PydanticObjectId, user: User) -> ChatSession:
    session, party = await load_for(session_id, user)
    if party is not CallParty.ASTROLOGER:
        raise ForbiddenError("Only the astrologer can accept.", error_code="not_the_callee")

    if session.status is ChatStatus.ACTIVE:
        return session
    if session.status is not ChatStatus.REQUESTED:
        raise ConflictError(
            f"This chat is already {session.status.value}.", error_code="chat_not_open"
        )

    now = _now()
    session.status = ChatStatus.ACTIVE
    session.started_at = now
    session.astrologer_seen_at = now
    await session.save()

    # From here `status` is ACTIVE, and that is what `messages.send` checks
    # before accepting anything.

    # Minute one is paid for before it is used.
    await _charge(session)

    logger.info("Chat {} accepted.", session.id)
    return session


async def decline_chat(*, session_id: PydanticObjectId, user: User) -> ChatSession:
    session, party = await load_for(session_id, user)
    if party is not CallParty.ASTROLOGER:
        raise ForbiddenError("Only the astrologer can decline.", error_code="not_the_callee")
    if session.status is not ChatStatus.REQUESTED:
        raise ConflictError(
            f"This chat is already {session.status.value}.", error_code="chat_not_open"
        )
    return await _close(
        session,
        status=ChatStatus.DECLINED,
        by=CallParty.ASTROLOGER,
        reason="Declined by the astrologer",
    )


async def end_chat(
    *, session_id: PydanticObjectId, user: User, reason: str | None = None
) -> ChatSession:
    session, party = await load_for(session_id, user)
    if session.status not in LIVE_STATUSES:
        return session

    if session.status is ChatStatus.REQUESTED:
        status = ChatStatus.CANCELLED if party is CallParty.USER else ChatStatus.DECLINED
    else:
        status = ChatStatus.ENDED

    return await _close(session, status=status, by=party, reason=reason)


async def _close(
    session: ChatSession, *, status: ChatStatus, by: CallParty, reason: str | None
) -> ChatSession:
    now = _now()
    started = _aware(session.started_at)

    # The count is kept on the session because the messages themselves are
    # eventually removed, and history should still be able to say how much was
    # said.
    from app.services import messages as message_service

    assert session.id is not None
    session.message_count = await message_service.count_for(session.id)
    session.status = status
    session.ended_at = now
    session.ended_by = by
    session.end_reason = reason
    session.duration_seconds = int((now - started).total_seconds()) if started else 0
    await session.save()

    if status is ChatStatus.ENDED and session.started_at:
        try:
            from app.models.astrologer import Astrologer, ServiceDuration

            astro = await Astrologer.get(session.astrologer_id)
            if astro:
                minutes = max(1, round(session.duration_seconds / 60)) if session.duration_seconds > 0 else 1
                if not hasattr(astro, "service_duration") or astro.service_duration is None:
                    astro.service_duration = ServiceDuration()
                astro.service_duration.chat_minutes += minutes
                astro.total_consultations += 1
                await astro.save()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not update astrologer service duration for chat {}: {}", session.id, exc)

    # Saved first, so the expiry is counted from an `ended_at` that is on
    # disk. Never allowed to fail the close: a chat that stayed open because
    # its cleanup threw would keep charging.
    try:
        await message_service.expire_session(session)
    except Exception as exc:  # noqa: BLE001
        logger.error("Could not schedule expiry for chat {}: {}", session.id, exc)

    # Both sides' screens should close themselves rather than wait to be told.
    try:
        from app.services import realtime

        for participant in (session.user_id, session.astrologer_user_id):
            await realtime.publish_chat(
                participant,
                {
                    "type": "chat_ended",
                    "data": {"session_id": str(session.id), "reason": reason},
                },
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Chat end push skipped: {}", exc)

    logger.info(
        "Chat {} {} by {} after {}s, {} messages",
        session.id,
        status.value,
        by.value,
        session.duration_seconds,
        session.message_count,
    )
    return session


def _price_of(session: ChatSession) -> billing.Price:
    return billing.Price(
        coins_per_minute=session.coins_per_minute,
        commission_percent=session.commission_percent,
        coin_value_paise=session.coin_value_paise,
    )


async def _charge(session: ChatSession) -> billing.ChargeResult:
    """Charges the minutes due, and closes the chat if the wallet cannot.

    Closing also shuts the Firestore conversation, so a browser that ignores
    the UI still cannot send another message.
    """
    result = await billing.charge_due(
        session_id=session.id,
        mode=ConsultationMode.CHAT,
        user_id=session.user_id,
        astrologer_id=session.astrologer_id,
        astrologer_user_id=session.astrologer_user_id,
        started_at=session.started_at or _now(),
        price=_price_of(session),
        already_charged=session.minutes_charged,
        cap_minutes=session.requested_minutes or None,
    )

    if result.coins_charged:
        session.minutes_charged = result.minutes_charged
        session.coins_charged += result.coins_charged
        session.earning_paise += result.earning_paise
        await session.save()

    if result.out_of_coins:
        await _close(session, status=ChatStatus.ENDED, by=CallParty.SYSTEM,
                     reason="Ran out of coins")
    elif session.requested_minutes and result.minutes_charged >= session.requested_minutes:
        elapsed = billing.minutes_elapsed(session.started_at or _now())
        if elapsed > session.requested_minutes:
            await _close(session, status=ChatStatus.ENDED, by=CallParty.SYSTEM,
                         reason="The booked time is over")

    return result


async def extend_chat(
    *, session_id: PydanticObjectId, user: User, extra_minutes: int
) -> ChatSession:
    """Buys more time on a chat already running."""
    session, party = await load_for(session_id, user)
    if party is not CallParty.USER:
        raise ForbiddenError(
            "Only the person who started the chat can extend it.",
            error_code="not_the_payer",
        )
    if session.status is not ChatStatus.ACTIVE:
        raise ConflictError("This chat is not running.", error_code="chat_not_active")

    await billing.check_can_extend(
        user_id=session.user_id,
        price=_price_of(session),
        current_minutes=session.requested_minutes,
        extra_minutes=extra_minutes,
        minutes_used=session.minutes_charged,
    )

    session.requested_minutes += extra_minutes
    await session.save()
    logger.info("Chat {} extended by {} minutes", session.id, extra_minutes)
    return session


async def heartbeat(*, session_id: PydanticObjectId, user: User) -> ChatSession:
    session, party = await load_for(session_id, user)
    if session.status not in LIVE_STATUSES:
        return session

    now = _now()
    if party is CallParty.USER:
        session.user_seen_at = now
    else:
        session.astrologer_seen_at = now
    await session.save()

    if session.status is ChatStatus.ACTIVE:
        await _charge(session)

    return session


async def incoming_for_astrologer(user: User) -> ChatSession | None:
    return await ChatSession.find_one(
        {
            "astrologer_user_id": user.id,
            "status": {"$in": [s.value for s in LIVE_STATUSES]},
        }
    )


async def active_for_user(user: User) -> ChatSession | None:
    return await ChatSession.find_one(
        {"user_id": user.id, "status": {"$in": [s.value for s in LIVE_STATUSES]}}
    )


async def history(
    *, user: User, as_astrologer: bool, page: int = 1, limit: int = 20
) -> tuple[list[ChatSession], int]:
    field = "astrologer_user_id" if as_astrologer else "user_id"
    query = ChatSession.find({field: user.id})
    total = await query.count()
    items = (
        await query.sort(-ChatSession.created_at).skip((page - 1) * limit).limit(limit).to_list()
    )
    return items, total


async def sweep() -> dict[str, int]:
    """Closes chats nobody closed — the same safety net calls have."""
    now = _now()
    missed = ended = capped = 0

    wait_deadline = now - timedelta(seconds=settings.CHAT_REQUEST_TIMEOUT_SECONDS)
    async for session in ChatSession.find(
        {"status": ChatStatus.REQUESTED.value, "created_at": {"$lt": wait_deadline}}
    ):
        await _close(session, status=ChatStatus.MISSED, by=CallParty.SYSTEM,
                     reason="Nobody picked it up")
        missed += 1

    grace = timedelta(seconds=settings.CHAT_IDLE_GRACE_SECONDS)
    max_len = timedelta(seconds=settings.CHAT_MAX_DURATION_SECONDS)

    async for session in ChatSession.find({"status": ChatStatus.ACTIVE.value}):
        await _charge(session)
        if session.status is not ChatStatus.ACTIVE:
            ended += 1
            continue

        started = _aware(session.started_at) or _aware(session.created_at) or now
        if now - started > max_len:
            await _close(session, status=ChatStatus.ENDED, by=CallParty.SYSTEM,
                         reason="Reached the maximum chat length")
            capped += 1
            continue

        seen = [s for s in (_aware(session.user_seen_at), _aware(session.astrologer_seen_at)) if s]
        last_seen = max(seen) if seen else started
        if now - last_seen > grace:
            await _close(session, status=ChatStatus.ENDED, by=CallParty.SYSTEM,
                         reason="Both sides went quiet")
            ended += 1

    if missed or ended or capped:
        logger.info("Chat sweep: {} missed, {} dropped, {} capped", missed, ended, capped)
    return {"missed": missed, "dropped": ended, "capped": capped}
