"""One-to-one calls.

The server owns the call, not the SDK. ZEGOCLOUD will happily let anyone with a
token into any room, so every rule that matters — who may call whom, whether
the astrologer is free, when the call actually began, when it is over — is
decided here and the room is minted to match.

Three things can end a call, and all three are handled:

* somebody hangs up, which is the normal path;
* the ring times out without an answer, so it is marked missed;
* both sides go quiet, which is what a closed laptop or a dead network looks
  like — the sweeper closes those, or a call would stay open forever.

Billing is deliberately absent for now.
"""

import secrets
from datetime import UTC, datetime, timedelta

from beanie import PydanticObjectId
from loguru import logger

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.astrologer import Astrologer
from app.models.call import CallSession
from app.models.enums import (
    AccountStatus,
    CallParty,
    CallStatus,
    ConsultationMode,
)
from app.models.user import User
from app.services import billing, zego

# A call in one of these is still going on, so neither side may start another.
LIVE_STATUSES = [CallStatus.RINGING, CallStatus.ACTIVE]

# What can be dialled. Chat is a conversation, not a call, so it is not here.
CALLABLE_MODES = (ConsultationMode.CALL, ConsultationMode.VIDEO)

MODE_NOUN = {
    ConsultationMode.CALL: "voice call",
    ConsultationMode.VIDEO: "video call",
    ConsultationMode.CHAT: "chat",
}


def _accepts_now(profile: Astrologer, mode: ConsultationMode) -> bool:
    """Whether this astrologer has this kind of call switched on right now."""
    if mode is ConsultationMode.VIDEO:
        return profile.availability.is_available_for_video
    return profile.availability.is_available_for_call


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    """Mongo hands back naive datetimes; compare them in UTC."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def _live_call_for(user_id: PydanticObjectId) -> CallSession | None:
    return await CallSession.find_one(
        {
            "$or": [{"user_id": user_id}, {"astrologer_user_id": user_id}],
            "status": {"$in": [s.value for s in LIVE_STATUSES]},
        }
    )


async def start_call(
    *,
    user: User,
    astrologer_id: PydanticObjectId,
    mode: ConsultationMode,
    requested_minutes: int,
) -> tuple[CallSession, str]:
    """Rings an astrologer. Returns the session and the caller's room token."""
    # A voice call and a video call are the same session down the same room —
    # the only difference is whether the camera is on, which the client decides.
    # Chat is not a call at all and does not belong here.
    if mode not in CALLABLE_MODES:
        raise BadRequestError(
            "That is not something you can call about.", error_code="mode_unavailable"
        )

    profile = await Astrologer.get(astrologer_id)
    if profile is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    account = await User.get(profile.user_id)
    if account is None or account.status is not AccountStatus.ACTIVE:
        raise BadRequestError(
            "This astrologer is not available.", error_code="astrologer_unavailable"
        )

    noun = MODE_NOUN[mode]

    if mode not in profile.modes_enabled:
        raise BadRequestError(
            f"This astrologer does not take {noun}s.", error_code="mode_not_offered"
        )
    # Presence, not the stored flag: an astrologer whose panel has closed is
    # not there to answer, whatever the flag still says.
    from app.services import presence

    if not presence.is_effectively_online(profile.availability):
        raise BadRequestError(
            "This astrologer is offline right now.", error_code="astrologer_offline"
        )
    # Online, offers this kind of call, but has paused it — a different thing
    # from not offering it at all, and the message should say so.
    if not _accepts_now(profile, mode):
        raise BadRequestError(
            f"This astrologer is not taking {noun}s at the moment.",
            error_code="mode_paused",
        )

    # Neither side may be on another call. Checked for both, because the
    # astrologer could be busy with someone else.
    if await _live_call_for(user.id) is not None:
        raise ConflictError("You are already on a call.", error_code="already_in_call")
    if await _live_call_for(profile.user_id) is not None:
        raise ConflictError(
            "This astrologer is on another call.", error_code="astrologer_busy"
        )

    # Price it and check the wallet before anyone's phone rings — being cut off
    # two seconds in is worse than being told up front.
    price = await billing.price_for(profile, mode)
    await billing.check_can_start(
        user_id=user.id, price=price, requested_minutes=requested_minutes
    )

    # A fresh room every time: reusing one would let an old token back in.
    room_id = f"call_{secrets.token_hex(10)}"
    session = CallSession(
        user_id=user.id,
        astrologer_id=profile.id,
        astrologer_user_id=profile.user_id,
        mode=mode,
        room_id=room_id,
        status=CallStatus.RINGING,
        user_seen_at=_now(),
        coins_per_minute=price.coins_per_minute,
        commission_percent=price.commission_percent,
        coin_value_paise=price.coin_value_paise,
        requested_minutes=requested_minutes,
    )
    await session.insert()

    token = zego.generate_token(user_id=str(user.id), room_id=room_id)
    logger.info(
        "{} {} ringing: user {} -> astrologer {}",
        MODE_NOUN[mode].capitalize(),
        session.id,
        user.email,
        account.email,
    )
    return session, token


async def get_session(session_id: PydanticObjectId) -> CallSession:
    session = await CallSession.get(session_id)
    if session is None:
        raise NotFoundError("Call not found.", error_code="call_not_found")
    return session


def _party(session: CallSession, user: User) -> CallParty:
    if session.user_id == user.id:
        return CallParty.USER
    if session.astrologer_user_id == user.id:
        return CallParty.ASTROLOGER
    raise ForbiddenError("This is not your call.", error_code="not_your_call")


async def load_for(session_id: PydanticObjectId, user: User) -> tuple[CallSession, CallParty]:
    session = await get_session(session_id)
    return session, _party(session, user)


async def accept_call(*, session_id: PydanticObjectId, user: User) -> tuple[CallSession, str]:
    """The astrologer picks up. Returns their room token."""
    session, party = await load_for(session_id, user)
    if party is not CallParty.ASTROLOGER:
        raise ForbiddenError("Only the astrologer can answer.", error_code="not_the_callee")

    if session.status is CallStatus.ACTIVE:
        # Answering twice is harmless — hand back a token and carry on.
        return session, zego.generate_token(user_id=str(user.id), room_id=session.room_id)
    if session.status is not CallStatus.RINGING:
        raise ConflictError(
            f"This call is already {session.status.value}.", error_code="call_not_ringing"
        )

    now = _now()
    session.status = CallStatus.ACTIVE
    session.started_at = now
    session.astrologer_seen_at = now
    await session.save()

    # Minute one is paid for before it is spoken.
    await _charge(session)

    logger.info("Call {} answered.", session.id)
    return session, zego.generate_token(user_id=str(user.id), room_id=session.room_id)


async def decline_call(*, session_id: PydanticObjectId, user: User) -> CallSession:
    session, party = await load_for(session_id, user)
    if party is not CallParty.ASTROLOGER:
        raise ForbiddenError("Only the astrologer can decline.", error_code="not_the_callee")
    if session.status is not CallStatus.RINGING:
        raise ConflictError(
            f"This call is already {session.status.value}.", error_code="call_not_ringing"
        )

    return await _close(session, status=CallStatus.DECLINED, by=CallParty.ASTROLOGER,
                        reason="Declined by the astrologer")


async def end_call(
    *, session_id: PydanticObjectId, user: User, reason: str | None = None
) -> CallSession:
    session, party = await load_for(session_id, user)

    if session.status not in LIVE_STATUSES:
        # Both sides may press End at once; the second one is not an error.
        return session

    # Hanging up while it is still ringing is a cancel, not a completed call.
    if session.status is CallStatus.RINGING:
        status = (
            CallStatus.CANCELLED if party is CallParty.USER else CallStatus.DECLINED
        )
    else:
        status = CallStatus.ENDED

    return await _close(session, status=status, by=party, reason=reason)


async def _close(
    session: CallSession, *, status: CallStatus, by: CallParty, reason: str | None
) -> CallSession:
    now = _now()
    session.status = status
    session.ended_at = now
    session.ended_by = by
    session.end_reason = reason
    started = _aware(session.started_at)
    session.duration_seconds = int((now - started).total_seconds()) if started else 0
    await session.save()

    if status is CallStatus.ENDED and session.started_at:
        try:
            from app.models.astrologer import Astrologer, ServiceDuration
            from app.models.enums import ConsultationMode

            astro = await Astrologer.get(session.astrologer_id)
            if astro:
                minutes = max(1, round(session.duration_seconds / 60)) if session.duration_seconds > 0 else 1
                if not hasattr(astro, "service_duration") or astro.service_duration is None:
                    astro.service_duration = ServiceDuration()
                if session.mode == ConsultationMode.VIDEO:
                    astro.service_duration.video_minutes += minutes
                else:
                    astro.service_duration.call_minutes += minutes
                astro.total_consultations += 1
                await astro.save()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not update astrologer service duration for call {}: {}", session.id, exc)

    logger.info(
        "Call {} {} by {} after {}s", session.id, status.value, by.value, session.duration_seconds
    )
    return session


def _price_of(session: CallSession) -> billing.Price:
    return billing.Price(
        coins_per_minute=session.coins_per_minute,
        commission_percent=session.commission_percent,
        coin_value_paise=session.coin_value_paise,
    )


async def _charge(session: CallSession) -> billing.ChargeResult:
    """Charges whatever minutes are due, and closes the call if it cannot.

    Called from the heartbeat and from the sweeper, so a client that stops
    talking to us cannot use minutes it never paid for.
    """
    result = await billing.charge_due(
        session_id=session.id,
        mode=session.mode,
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
        await _close(session, status=CallStatus.ENDED, by=CallParty.SYSTEM,
                     reason="Ran out of coins")
    elif session.requested_minutes and result.minutes_charged >= session.requested_minutes:
        # The booked time is up. They chose it, so it is not a failure.
        elapsed = billing.minutes_elapsed(session.started_at or _now())
        if elapsed > session.requested_minutes:
            await _close(session, status=CallStatus.ENDED, by=CallParty.SYSTEM,
                         reason="The booked time is over")

    return result


async def extend_call(
    *, session_id: PydanticObjectId, user: User, extra_minutes: int
) -> CallSession:
    """Buys more time on a call already running.

    Only the person paying may extend — an astrologer able to lengthen a call
    would be spending somebody else's coins.
    """
    session, party = await load_for(session_id, user)
    if party is not CallParty.USER:
        raise ForbiddenError(
            "Only the caller can extend a call.", error_code="not_the_payer"
        )
    if session.status is not CallStatus.ACTIVE:
        raise ConflictError(
            "This call is not running.", error_code="call_not_active"
        )

    await billing.check_can_extend(
        user_id=session.user_id,
        price=_price_of(session),
        current_minutes=session.requested_minutes,
        extra_minutes=extra_minutes,
        minutes_used=session.minutes_charged,
    )

    session.requested_minutes += extra_minutes
    await session.save()
    logger.info("Call {} extended by {} minutes", session.id, extra_minutes)
    return session


async def heartbeat(*, session_id: PydanticObjectId, user: User) -> CallSession:
    """Says "I am still here". The sweeper reads these."""
    session, party = await load_for(session_id, user)
    if session.status not in LIVE_STATUSES:
        return session

    now = _now()
    if party is CallParty.USER:
        session.user_seen_at = now
    else:
        session.astrologer_seen_at = now
    await session.save()

    if session.status is CallStatus.ACTIVE:
        await _charge(session)

    return session


async def incoming_for_astrologer(user: User) -> CallSession | None:
    """What the astrologer's panel polls for."""
    return await CallSession.find_one(
        {
            "astrologer_user_id": user.id,
            "status": {"$in": [s.value for s in LIVE_STATUSES]},
        }
    )


async def active_for_user(user: User) -> CallSession | None:
    return await CallSession.find_one(
        {"user_id": user.id, "status": {"$in": [s.value for s in LIVE_STATUSES]}}
    )


async def token_for(session: CallSession, user: User) -> str:
    """Re-issues a token, for a page reload mid-call."""
    _party(session, user)
    if session.status not in LIVE_STATUSES:
        raise ConflictError(
            "This call is over.", error_code="call_over"
        )
    return zego.generate_token(user_id=str(user.id), room_id=session.room_id)


async def history(
    *, user: User, as_astrologer: bool, page: int = 1, limit: int = 20
) -> tuple[list[CallSession], int]:
    field = "astrologer_user_id" if as_astrologer else "user_id"
    query = CallSession.find({field: user.id})
    total = await query.count()
    items = (
        await query.sort(-CallSession.created_at)
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list()
    )
    return items, total


async def sweep() -> dict[str, int]:
    """Closes calls nobody is going to close.

    Run from a scheduled ping. Without it a tab that was closed mid-call leaves
    the session open, and both people look "busy" forever.
    """
    now = _now()
    missed = ended = capped = 0

    ring_deadline = now - timedelta(seconds=settings.CALL_RING_TIMEOUT_SECONDS)
    async for session in CallSession.find(
        {"status": CallStatus.RINGING.value, "created_at": {"$lt": ring_deadline}}
    ):
        await _close(session, status=CallStatus.MISSED, by=CallParty.SYSTEM,
                     reason="Nobody answered")
        missed += 1

    grace = timedelta(seconds=settings.CALL_HEARTBEAT_GRACE_SECONDS)
    max_len = timedelta(seconds=settings.CALL_MAX_DURATION_SECONDS)

    async for session in CallSession.find({"status": CallStatus.ACTIVE.value}):
        # Charge first: a session about to be closed still used the minutes it
        # used, and this is the backstop for a client that stopped heartbeating.
        await _charge(session)
        if session.status is not CallStatus.ACTIVE:
            ended += 1
            continue

        started = _aware(session.started_at) or _aware(session.created_at) or now
        if now - started > max_len:
            await _close(session, status=CallStatus.ENDED, by=CallParty.SYSTEM,
                         reason="Reached the maximum call length")
            capped += 1
            continue

        seen = [s for s in (_aware(session.user_seen_at), _aware(session.astrologer_seen_at)) if s]
        last_seen = max(seen) if seen else started
        if now - last_seen > grace:
            await _close(session, status=CallStatus.ENDED, by=CallParty.SYSTEM,
                         reason="Both sides stopped responding")
            ended += 1

    if missed or ended or capped:
        logger.info("Call sweep: {} missed, {} dropped, {} capped", missed, ended, capped)
    return {"missed": missed, "dropped": ended, "capped": capped}
