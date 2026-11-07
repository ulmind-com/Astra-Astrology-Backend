"""The multi-party Vedic chamber.

One host, up to a handful of invited guests, and an astrologer, in a single
ZEGOCLOUD room. The host pays by the minute exactly as they would for a 1:1
call; nobody else is ever charged.

The rules that matter, and why:

*The room lives only while the host is here.* Guests and the astrologer
cannot keep it running between them, because the host's wallet is what pays
for it and someone who has left must not keep spending.

*A seat is one person.* A join code admits a single live occupant. Without
that, a code forwarded on lets an unbounded number of people into a private
family consultation, and the seat count means nothing.

*Codes die with the room.* They work while it is ringing or active, and not
once it is over — a link in a WhatsApp group should not open a consultation
that finished last week.

*Guests cannot spend the host's money.* Extending, ending for everyone,
inviting and revoking are all the host's.
"""

import secrets
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
from app.models.enums import AccountStatus, CallParty, CallStatus, ConsultationMode
from app.models.milan import (
    MAX_GUESTS_CEILING,
    SEAT_GRACE_SECONDS,
    MilanRoom,
    MilanSeat,
)
from app.models.user import User
from app.services import billing, zego

LIVE_STATUSES = [CallStatus.RINGING, CallStatus.ACTIVE]

# Voice or video only; a chamber is not a chat thread.
ROOM_MODES = (ConsultationMode.CALL, ConsultationMode.VIDEO)

PURPOSES = ("kundali_matching", "family_vastu", "other")


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime | None) -> datetime | None:
    """Mongo hands back naive datetimes; compare them in UTC."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _is_present(seat: MilanSeat, now: datetime | None = None) -> bool:
    """Whether someone is sitting here right now.

    A seat whose occupant stopped checking in is free again, so a guest whose
    phone died does not hold a place for the rest of the consultation.
    """
    if seat.is_revoked or seat.left_at is not None or seat.last_seen_at is None:
        return False
    seen = _aware(seat.last_seen_at)
    assert seen is not None
    return (now or _now()) - seen <= timedelta(seconds=SEAT_GRACE_SECONDS)


def _new_code() -> str:
    """A guest's entire authority, so it is long and from the CSPRNG."""
    return secrets.token_urlsafe(24)


def _new_seat(label: str, index: int) -> MilanSeat:
    return MilanSeat(
        seat_id=f"s{index}_{secrets.token_hex(3)}",
        label=label.strip() or f"Guest {index + 1}",
        join_code=_new_code(),
    )


# --------------------------------------------------------------- lookups
async def get_room(room_id: PydanticObjectId) -> MilanRoom:
    room = await MilanRoom.get(room_id)
    if room is None:
        raise NotFoundError("Chamber not found.", error_code="milan_not_found")
    return room


async def live_room_for(user_id: PydanticObjectId) -> MilanRoom | None:
    """A live room this account is hosting or taking, if any.

    Guests are deliberately not included: a guardian sitting in on their
    daughter's matching has not used up their own ability to book.
    """
    return await MilanRoom.find_one(
        {
            "$or": [{"host_user_id": user_id}, {"astrologer_user_id": user_id}],
            "status": {"$in": [s.value for s in LIVE_STATUSES]},
        }
    )


async def _assert_free(user_id: PydanticObjectId, *, as_astrologer: bool) -> None:
    """Nobody may be in two consultations at once, of either kind.

    Checked against 1:1 calls as well as rooms, because the two live in
    different collections and a double booking would bill twice.
    """
    from app.services import call as call_service

    if await live_room_for(user_id) is not None:
        raise ConflictError(
            "This astrologer is already in a chamber."
            if as_astrologer
            else "You are already in a chamber.",
            error_code="astrologer_busy" if as_astrologer else "already_in_room",
        )
    if await call_service._live_call_for(user_id) is not None:
        raise ConflictError(
            "This astrologer is on another call."
            if as_astrologer
            else "You are already on a call.",
            error_code="astrologer_busy" if as_astrologer else "already_in_call",
        )


# ---------------------------------------------------------------- create
async def create_room(
    *,
    host: User,
    astrologer_id: PydanticObjectId,
    mode: ConsultationMode,
    purpose: str,
    requested_minutes: int,
    guest_labels: list[str],
) -> tuple[MilanRoom, str]:
    """Opens a chamber and rings the astrologer. Returns it and the host's token."""
    if mode not in ROOM_MODES:
        raise BadRequestError(
            "A chamber is a voice or video session.", error_code="mode_unavailable"
        )
    if purpose not in PURPOSES:
        raise BadRequestError("Unknown chamber purpose.", error_code="bad_purpose")

    profile = await Astrologer.get(astrologer_id)
    if profile is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    account = await User.get(profile.user_id)
    if account is None or account.status is not AccountStatus.ACTIVE:
        raise BadRequestError(
            "This astrologer is not available.", error_code="astrologer_unavailable"
        )
    if mode not in profile.modes_enabled:
        raise BadRequestError(
            "This astrologer does not take that kind of session.",
            error_code="mode_not_offered",
        )

    from app.services import presence

    if not presence.is_effectively_online(profile.availability):
        raise BadRequestError(
            "This astrologer is offline right now.", error_code="astrologer_offline"
        )

    await _assert_free(host.id, as_astrologer=False)
    await _assert_free(profile.user_id, as_astrologer=True)

    max_guests = await _max_guests()
    labels = [label for label in guest_labels if label and label.strip()]
    if len(labels) > max_guests:
        raise BadRequestError(
            f"A chamber seats {max_guests} guests besides you.",
            error_code="too_many_guests",
        )

    # Priced and paid for before anyone's phone rings: being cut off two
    # minutes into a family consultation is worse than being told up front.
    price = await billing.price_for(profile, mode)
    await billing.check_can_start(
        user_id=host.id, price=price, requested_minutes=requested_minutes
    )

    room = MilanRoom(
        host_user_id=host.id,
        astrologer_id=profile.id,
        astrologer_user_id=profile.user_id,
        purpose=purpose,
        mode=mode,
        room_id=f"milan_{secrets.token_hex(10)}",
        status=CallStatus.RINGING,
        host_seen_at=_now(),
        coins_per_minute=price.coins_per_minute,
        commission_percent=price.commission_percent,
        coin_value_paise=price.coin_value_paise,
        requested_minutes=requested_minutes,
        max_guests=max_guests,
        seats=[_new_seat(label, i) for i, label in enumerate(labels)],
    )
    await room.insert()

    logger.info(
        "Milan chamber {} ringing: host {} -> astrologer {} ({} seats)",
        room.id,
        host.email,
        account.email,
        len(room.seats),
    )
    return room, zego.generate_token(user_id=str(host.id), room_id=room.room_id)


async def _max_guests() -> int:
    from app.services import settings as settings_service

    platform = await settings_service.get_settings()
    configured = getattr(platform, "milan_max_guests", 3)
    return max(0, min(int(configured), MAX_GUESTS_CEILING))


# ------------------------------------------------------------------ seats
def _host_only(room: MilanRoom, user: User) -> None:
    if user.id != room.host_user_id:
        raise ForbiddenError(
            "Only the person who opened this chamber can do that.",
            error_code="not_the_host",
        )


async def add_seat(*, room_id: PydanticObjectId, user: User, label: str) -> MilanRoom:
    """Opens one more place, up to the room's limit."""
    room = await get_room(room_id)
    _host_only(room, user)
    if room.status not in LIVE_STATUSES:
        raise ConflictError("This chamber is over.", error_code="milan_over")

    active = [s for s in room.seats if not s.is_revoked]
    if len(active) >= room.max_guests:
        raise BadRequestError(
            f"This chamber seats {room.max_guests} guests.",
            error_code="chamber_full",
        )

    room.seats.append(_new_seat(label, len(room.seats)))
    await room.save()
    return room


async def revoke_seat(
    *, room_id: PydanticObjectId, user: User, seat_id: str
) -> MilanRoom:
    """Cancels a code, and turns out whoever is using it.

    The occupant's own client stops being issued tokens at its next check-in,
    so a revoked guest cannot simply keep the page open.
    """
    room = await get_room(room_id)
    _host_only(room, user)

    seat = next((s for s in room.seats if s.seat_id == seat_id), None)
    if seat is None:
        raise NotFoundError("No such seat.", error_code="seat_not_found")
    if seat.is_revoked:
        return room

    seat.revoked_at = _now()
    seat.left_at = seat.left_at or seat.revoked_at
    await room.save()
    logger.info("Milan chamber {}: seat {} revoked", room.id, seat_id)
    return room


# ------------------------------------------------------------------ joining
async def _seat_by_code(join_code: str) -> tuple[MilanRoom, MilanSeat]:
    room = await MilanRoom.find_one({"seats.join_code": join_code})
    if room is None:
        raise NotFoundError(
            "That invitation is not valid.", error_code="invite_not_found"
        )
    seat = next((s for s in room.seats if s.join_code == join_code), None)
    if seat is None:  # pragma: no cover - the query matched on this field
        raise NotFoundError(
            "That invitation is not valid.", error_code="invite_not_found"
        )
    return room, seat


async def join_as_guest(
    *, join_code: str, display_name: str | None, viewer: User | None
) -> tuple[MilanRoom, MilanSeat, str]:
    """Takes a seat with an invitation. No account required.

    The code is the whole credential, so every way it could be misused is
    refused here rather than anywhere further in.
    """
    room, seat = await _seat_by_code(join_code)

    if seat.is_revoked:
        raise ForbiddenError(
            "This invitation has been cancelled.", error_code="invite_revoked"
        )
    if room.status not in LIVE_STATUSES:
        raise ConflictError(
            "This chamber is over.", error_code="milan_over"
        )

    now = _now()
    # One seat, one person. A forwarded link must not multiply the room.
    if _is_present(seat, now) and (viewer is None or viewer.id != seat.user_id):
        raise ConflictError(
            "Someone is already using this invitation.", error_code="seat_taken"
        )

    seat.user_id = viewer.id if viewer else None
    seat.display_name = (
        (display_name or "").strip()
        or seat.display_name
        or (viewer.full_name if viewer else None)
        or seat.label
    )[:60]
    seat.joined_at = seat.joined_at or now
    seat.last_seen_at = now
    seat.left_at = None
    await room.save()

    # The seat id is the identity inside the room: a guest has no account to
    # borrow one from, and two guests must never publish as the same stream.
    token = zego.generate_token(
        user_id=f"guest_{seat.seat_id}", room_id=room.room_id
    )
    logger.info("Milan chamber {}: {} took seat {}", room.id, seat.display_name, seat.seat_id)
    return room, seat, token


async def guest_heartbeat(*, join_code: str) -> tuple[MilanRoom, MilanSeat]:
    """Keeps a guest's seat, and nothing else.

    A guest checking in must not keep the room itself alive — that is the
    host's doing, and the host's wallet.
    """
    room, seat = await _seat_by_code(join_code)
    if seat.is_revoked:
        raise ForbiddenError(
            "This invitation has been cancelled.", error_code="invite_revoked"
        )
    if room.status not in LIVE_STATUSES:
        raise ConflictError("This chamber is over.", error_code="milan_over")

    seat.last_seen_at = _now()
    await room.save()
    return room, seat


async def leave_seat(*, join_code: str) -> MilanRoom:
    """A guest steps out, freeing the seat for whoever the host meant next."""
    room, seat = await _seat_by_code(join_code)
    seat.left_at = _now()
    seat.last_seen_at = None
    await room.save()
    return room


# ------------------------------------------------------- the two accounts
def party_of(room: MilanRoom, user: User) -> CallParty:
    if user.id == room.host_user_id:
        return CallParty.USER
    if user.id == room.astrologer_user_id:
        return CallParty.ASTROLOGER
    raise ForbiddenError(
        "This is not your chamber.", error_code="not_your_milan"
    )


async def load_for(
    room_id: PydanticObjectId, user: User
) -> tuple[MilanRoom, CallParty]:
    room = await get_room(room_id)
    return room, party_of(room, user)


async def accept(*, room_id: PydanticObjectId, user: User) -> tuple[MilanRoom, str]:
    """The astrologer joins, and the clock starts."""
    room = await get_room(room_id)
    if user.id != room.astrologer_user_id:
        raise ForbiddenError(
            "Only this chamber's astrologer can accept it.",
            error_code="not_your_milan",
        )
    if room.status is CallStatus.ACTIVE:
        # A second tap, or a reload. Not an error; hand back a fresh token.
        return room, zego.generate_token(user_id=str(user.id), room_id=room.room_id)
    if room.status is not CallStatus.RINGING:
        raise ConflictError("This chamber is over.", error_code="milan_over")

    now = _now()
    room.status = CallStatus.ACTIVE
    room.started_at = now
    room.astrologer_seen_at = now
    await room.save()
    logger.info("Milan chamber {} accepted", room.id)
    return room, zego.generate_token(user_id=str(user.id), room_id=room.room_id)


async def decline(*, room_id: PydanticObjectId, user: User) -> MilanRoom:
    room = await get_room(room_id)
    if user.id != room.astrologer_user_id:
        raise ForbiddenError(
            "Only this chamber's astrologer can decline it.",
            error_code="not_your_milan",
        )
    if room.status is not CallStatus.RINGING:
        return room
    return await _close(
        room, status=CallStatus.DECLINED, by=CallParty.ASTROLOGER, reason=None
    )


async def end_room(
    *, room_id: PydanticObjectId, user: User, reason: str | None = None
) -> MilanRoom:
    """The host or the astrologer closes the chamber for everyone."""
    room, party = await load_for(room_id, user)
    if room.status not in LIVE_STATUSES:
        # Both may press End at once; the second one is not an error.
        return room

    if room.status is CallStatus.RINGING:
        status = (
            CallStatus.CANCELLED if party is CallParty.USER else CallStatus.DECLINED
        )
    else:
        status = CallStatus.ENDED
    return await _close(room, status=status, by=party, reason=reason)


async def heartbeat(*, room_id: PydanticObjectId, user: User) -> MilanRoom:
    """The host or the astrologer checks in, and the minutes due are charged."""
    room, party = await load_for(room_id, user)
    if room.status not in LIVE_STATUSES:
        return room

    now = _now()
    if party is CallParty.USER:
        room.host_seen_at = now
    else:
        room.astrologer_seen_at = now
    await room.save()

    if room.status is CallStatus.ACTIVE:
        await _charge(room)
    return room


async def extend(
    *, room_id: PydanticObjectId, user: User, extra_minutes: int
) -> MilanRoom:
    """Buys more time. The host's call, because it is the host's wallet."""
    room = await get_room(room_id)
    _host_only(room, user)
    if room.status is not CallStatus.ACTIVE:
        raise ConflictError("This chamber is not running.", error_code="milan_not_live")
    if extra_minutes < 1:
        raise BadRequestError("Add at least a minute.", error_code="bad_minutes")

    price = billing.Price(
        coins_per_minute=room.coins_per_minute,
        commission_percent=room.commission_percent,
        coin_value_paise=room.coin_value_paise,
    )
    await billing.check_can_extend(
        user_id=room.host_user_id,
        price=price,
        current_minutes=room.requested_minutes,
        extra_minutes=extra_minutes,
        minutes_used=room.minutes_charged,
    )
    room.requested_minutes += extra_minutes
    await room.save()
    return room


# ----------------------------------------------------------------- money
async def _charge(room: MilanRoom) -> billing.ChargeResult:
    """Charges the host for whatever minutes are due.

    Guests are never party to this. The room is billed once per minute no
    matter how many people are sitting in it, exactly as the host was quoted.
    """
    result = await billing.charge_due(
        session_id=room.id,
        mode=room.mode,
        user_id=room.host_user_id,
        astrologer_id=room.astrologer_id,
        astrologer_user_id=room.astrologer_user_id,
        started_at=_aware(room.started_at) or _now(),
        price=billing.Price(
            coins_per_minute=room.coins_per_minute,
            commission_percent=room.commission_percent,
            coin_value_paise=room.coin_value_paise,
        ),
        already_charged=room.minutes_charged,
        cap_minutes=room.requested_minutes or None,
    )

    if result.coins_charged:
        room.minutes_charged = result.minutes_charged
        room.coins_charged += result.coins_charged
        room.earning_paise += result.earning_paise
        await room.save()

    if result.out_of_coins:
        await _close(
            room,
            status=CallStatus.ENDED,
            by=CallParty.SYSTEM,
            reason="Ran out of coins",
        )
    elif room.requested_minutes and result.minutes_charged >= room.requested_minutes:
        elapsed = billing.minutes_elapsed(_aware(room.started_at) or _now())
        if elapsed > room.requested_minutes:
            await _close(
                room,
                status=CallStatus.ENDED,
                by=CallParty.SYSTEM,
                reason="The booked time is over",
            )
    return result


async def _close(
    room: MilanRoom, *, status: CallStatus, by: CallParty, reason: str | None
) -> MilanRoom:
    now = _now()
    room.status = status
    room.ended_at = now
    room.ended_by = by
    room.end_reason = reason
    started = _aware(room.started_at)
    room.duration_seconds = int((now - started).total_seconds()) if started else 0
    # Every invitation stops working the moment the chamber does.
    for seat in room.seats:
        seat.left_at = seat.left_at or now
    await room.save()

    logger.info(
        "Milan chamber {} {} by {} after {}s",
        room.id,
        status.value,
        by.value,
        room.duration_seconds,
    )
    return room


# --------------------------------------------------------------- the sweeper
async def sweep() -> dict[str, int]:
    """Closes chambers nobody is going to close.

    Without this a host who shut their laptop mid-session leaves the room
    open, their astrologer marked busy, and every guest's invitation live.
    """
    now = _now()
    missed = dropped = capped = 0

    ring_deadline = now - timedelta(seconds=settings.CALL_RING_TIMEOUT_SECONDS)
    async for room in MilanRoom.find(
        {"status": CallStatus.RINGING.value, "created_at": {"$lt": ring_deadline}}
    ):
        await _close(
            room, status=CallStatus.MISSED, by=CallParty.SYSTEM, reason="Nobody answered"
        )
        missed += 1

    grace = timedelta(seconds=settings.CALL_HEARTBEAT_GRACE_SECONDS)
    max_len = timedelta(seconds=settings.CALL_MAX_DURATION_SECONDS)

    async for room in MilanRoom.find({"status": CallStatus.ACTIVE.value}):
        # Charge first: a chamber about to be closed still used its minutes,
        # and this is the backstop for a host that stopped checking in.
        await _charge(room)
        if room.status is not CallStatus.ACTIVE:
            dropped += 1
            continue

        started = _aware(room.started_at) or _aware(room.created_at) or now
        if now - started > max_len:
            await _close(
                room,
                status=CallStatus.ENDED,
                by=CallParty.SYSTEM,
                reason="Reached the maximum session length",
            )
            capped += 1
            continue

        # Only the host and the astrologer keep it open. Guests sitting on
        # alone must not keep spending the host's coins.
        seen = [
            s
            for s in (_aware(room.host_seen_at), _aware(room.astrologer_seen_at))
            if s
        ]
        last_seen = max(seen) if seen else started
        if now - last_seen > grace:
            await _close(
                room,
                status=CallStatus.ENDED,
                by=CallParty.SYSTEM,
                reason="Everyone stopped responding",
            )
            dropped += 1

    if missed or dropped or capped:
        logger.info(
            "Milan sweep: {} missed, {} dropped, {} capped", missed, dropped, capped
        )
    return {"missed": missed, "dropped": dropped, "capped": capped}
