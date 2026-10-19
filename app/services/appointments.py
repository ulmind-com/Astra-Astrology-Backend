"""Scheduled appointments.

The hard part here is not the price, it is making a double booking impossible.
Two people asking for overlapping times must not both succeed, and checking
"is this free?" before writing does not achieve that — both requests can read
"free" before either writes.

So a booking claims the five-minute units it needs, one row each, against a
unique index on (astrologer, start). The second claim on any shared unit fails
at the database. The insert is the lock; nothing here relies on being the only
request in flight.

Order matters too: the units are claimed **before** the wallet is touched. A
clash is the ordinary failure, and it should happen before anyone's money
moves rather than after.
"""

from datetime import UTC, datetime, timedelta

from beanie import PydanticObjectId
from beanie.operators import GTE, LT, And, In, Or
from loguru import logger
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.appointment import (
    SLOT_MINUTES,
    Appointment,
    AppointmentSlot,
    AvailabilityWindow,
)
from app.models.astrologer import Astrologer
from app.models.base import utcnow
from app.models.enums import AppointmentStatus, TransactionReason
from app.models.user import User

# Bookings that still hold their time. A cancelled one has given it back.
LIVE_STATUSES = [AppointmentStatus.BOOKED, AppointmentStatus.COMPLETED]


# --------------------------------------------------------------- the grid
def _aligned(moment: datetime) -> bool:
    """Does this land on the five-minute grid everything is snapped to?"""
    return moment.second == 0 and moment.microsecond == 0 and moment.minute % SLOT_MINUTES == 0


def slot_starts(starts_at: datetime, minutes: int) -> list[datetime]:
    """Every five-minute unit a booking of this length occupies."""
    count = minutes // SLOT_MINUTES
    return [starts_at + timedelta(minutes=SLOT_MINUTES * i) for i in range(count)]


# ----------------------------------------------------------------- pricing
def price_for(card, minutes: int) -> int:
    """What a booking of this length costs, in paise.

    Pro rata from the astrologer's block price, so "thirty minutes for two
    hundred and fifty" also prices forty minutes without them having to say
    so. Rounded to the nearest paisa; the money is integer from here on.
    """
    if card.block_minutes <= 0:
        return 0
    return round(card.price_paise * minutes / card.block_minutes)


def deposit_for(price_paise: int, commission_percent: float) -> int:
    """The platform's share, taken up front and not returned.

    Rounded down, so the deposit is never a paisa more than the share the
    platform is owed.
    """
    return int(price_paise * commission_percent / 100)


def coins_for_paise(paise: int, coins_per_rupee: int) -> int:
    """Paise to coins, rounded up.

    Up rather than down: rounding down would let a booking be paid for with
    fewer coins than it is worth, and across enough bookings that is the
    platform quietly giving money away.
    """
    return -(-paise * coins_per_rupee // 100)


# ------------------------------------------------------------ availability
async def _windows_for(
    astrologer_id: PydanticObjectId, start: datetime, end: datetime
) -> list[AvailabilityWindow]:
    return (
        await AvailabilityWindow.find(
            And(
                AvailabilityWindow.astrologer_id == astrologer_id,
                LT(AvailabilityWindow.starts_at, end),
                GTE(AvailabilityWindow.ends_at, start),
            )
        )
        .sort(+AvailabilityWindow.starts_at)
        .to_list()
    )


async def booked_between(
    astrologer_id: PydanticObjectId, start: datetime, end: datetime
) -> list[Appointment]:
    """Bookings that touch this range, soonest first."""
    return (
        await Appointment.find(
            And(
                Appointment.astrologer_id == astrologer_id,
                In(Appointment.status, LIVE_STATUSES),
                LT(Appointment.starts_at, end),
                GTE(Appointment.ends_at, start),
            )
        )
        .sort(+Appointment.starts_at)
        .to_list()
    )


async def day_view(
    *, astrologer: Astrologer, day_start: datetime, day_end: datetime
) -> dict:
    """What a user needs to pick a time: the open hours, and what is gone.

    Both halves are returned rather than only the free gaps, because someone
    choosing a time is helped by seeing that 6–7 is taken — a calendar that
    silently omits it looks like a calendar with nothing on it.
    """
    assert astrologer.id is not None
    windows = await _windows_for(astrologer.id, day_start, day_end)
    taken = await booked_between(astrologer.id, day_start, day_end)

    return {
        "windows": [{"starts_at": w.starts_at, "ends_at": w.ends_at} for w in windows],
        "booked": [{"starts_at": a.starts_at, "ends_at": a.ends_at} for a in taken],
    }


def _covered_by_a_window(
    windows: list[AvailabilityWindow], starts_at: datetime, ends_at: datetime
) -> bool:
    """Is the whole booking inside one window?

    One window, not several stitched together: two adjoining windows are two
    separate stretches the astrologer offered, and a booking running across
    the join would span a gap they did not agree to.
    """
    return any(w.starts_at <= starts_at and ends_at <= w.ends_at for w in windows)


# ------------------------------------------------------------------ booking
async def book(
    *,
    user: User,
    astrologer: Astrologer,
    starts_at: datetime,
    minutes: int,
    note: str | None = None,
) -> Appointment:
    """Takes a slot, takes the deposit, and writes the booking."""
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    assert astrologer.id is not None
    platform = await settings_service.get_settings()
    card = astrologer.appointment

    # --- is this even on offer? ------------------------------------------
    if not card.enabled or card.price_paise <= 0:
        raise BadRequestError(
            "This astrologer is not taking appointments.",
            error_code="appointments_not_offered",
        )

    starts_at = starts_at.astimezone(UTC).replace(second=0, microsecond=0)
    if not _aligned(starts_at):
        raise BadRequestError(
            f"Pick a time on a {SLOT_MINUTES}-minute mark.", error_code="unaligned_start"
        )

    if minutes % SLOT_MINUTES:
        raise BadRequestError(
            f"Book in multiples of {SLOT_MINUTES} minutes.", error_code="unaligned_length"
        )
    if not platform.min_appointment_minutes <= minutes <= platform.max_appointment_minutes:
        raise BadRequestError(
            f"Appointments run from {platform.min_appointment_minutes} to "
            f"{platform.max_appointment_minutes} minutes.",
            error_code="bad_duration",
        )

    now = utcnow()
    if starts_at <= now:
        raise BadRequestError("That time has passed.", error_code="in_the_past")
    horizon = now + timedelta(days=platform.appointment_booking_days_ahead)
    if starts_at > horizon:
        raise BadRequestError(
            f"Bookings open {platform.appointment_booking_days_ahead} days ahead.",
            error_code="beyond_horizon",
        )

    ends_at = starts_at + timedelta(minutes=minutes)

    windows = await _windows_for(astrologer.id, starts_at, ends_at)
    if not _covered_by_a_window(windows, starts_at, ends_at):
        raise BadRequestError(
            "The astrologer is not available for that whole time.",
            error_code="outside_availability",
        )

    # --- the money, worked out before anything is claimed -----------------
    price_paise = price_for(card, minutes)
    commission = platform.appointment_commission_percent
    deposit_paise = deposit_for(price_paise, commission)
    deposit_coins = coins_for_paise(deposit_paise, platform.coins_per_rupee)

    # --- claim the time ---------------------------------------------------
    # Before the wallet, because a clash is the ordinary failure and nobody's
    # money should move for it.
    appointment_id = PydanticObjectId()
    claimed: list[AppointmentSlot] = []
    try:
        for moment in slot_starts(starts_at, minutes):
            slot = AppointmentSlot(
                astrologer_id=astrologer.id,
                appointment_id=appointment_id,
                starts_at=moment,
            )
            await slot.insert()
            claimed.append(slot)
    except DuplicateKeyError:
        await _release(claimed)
        raise ConflictError(
            "Someone has just booked part of that time. Please pick another slot.",
            error_code="slot_taken",
        )
    except Exception:
        await _release(claimed)
        raise

    # --- the deposit ------------------------------------------------------
    try:
        if deposit_coins > 0:
            await wallet_service.debit(
                user_id=user.id,
                amount_coins=deposit_coins,
                reason=TransactionReason.APPOINTMENT_DEPOSIT,
                idempotency_key=f"appointment:{appointment_id}:deposit",
                note=f"Appointment with {astrologer.display_name}",
            )
    except Exception:
        # The time goes straight back: holding it for a booking that was never
        # paid for would quietly take the astrologer off the market.
        await _release(claimed)
        raise

    appointment = Appointment(
        id=appointment_id,
        astrologer_id=astrologer.id,
        astrologer_user_id=astrologer.user_id,
        user_id=user.id,
        starts_at=starts_at,
        ends_at=ends_at,
        minutes=minutes,
        price_paise=price_paise,
        commission_percent=commission,
        deposit_paise=deposit_paise,
        deposit_coins=deposit_coins,
        coins_per_rupee=platform.coins_per_rupee,
        balance_due_paise=max(price_paise - deposit_paise, 0),
        user_note=note,
    )
    try:
        await appointment.insert()
    except Exception:
        # Nothing to refund yet that the ledger cannot explain, but the time
        # must not stay claimed by a booking that does not exist.
        await _release(claimed)
        raise

    logger.info(
        "Appointment {} booked: {} with {} for {} min, deposit {} coins",
        appointment_id,
        user.email,
        astrologer.display_name,
        minutes,
        deposit_coins,
    )
    await _notify(appointment)
    return appointment


async def _release(slots: list[AppointmentSlot]) -> None:
    for slot in slots:
        try:
            await slot.delete()
        except Exception as exc:  # noqa: BLE001 - best effort; see release_orphans
            logger.error("Could not release slot {}: {}", slot.starts_at, exc)


async def release_orphans() -> int:
    """Frees time claimed by bookings that do not exist.

    Only reachable if a release failed midway through an aborted booking. Left
    alone, those units would block an astrologer's calendar for ever with
    nothing to show for it.
    """
    orphans = 0
    async for slot in AppointmentSlot.find_all():
        if await Appointment.get(slot.appointment_id) is None:
            await slot.delete()
            orphans += 1
    if orphans:
        logger.warning("Released {} orphaned appointment slot(s).", orphans)
    return orphans


# --------------------------------------------------------------- cancelling
async def cancel(
    *, appointment: Appointment, by: User, reason: str | None = None
) -> Appointment:
    """Gives the time back. The deposit is not returned.

    That is the point of taking it: a calendar that can be filled and emptied
    for nothing is a calendar the astrologer cannot plan around.
    """
    if appointment.status is not AppointmentStatus.BOOKED:
        raise BadRequestError(
            "This appointment is not open.", error_code="appointment_not_open"
        )
    if by.id not in (appointment.user_id, appointment.astrologer_user_id):
        raise ForbiddenError("This is not your appointment.", error_code="not_yours")

    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = utcnow()
    appointment.cancelled_by = by.id
    appointment.cancel_reason = reason
    await appointment.save()

    assert appointment.id is not None
    await AppointmentSlot.find(
        AppointmentSlot.appointment_id == appointment.id
    ).delete()

    logger.info("Appointment {} cancelled by {}", appointment.id, by.email)
    await _notify(appointment)
    return appointment


# ------------------------------------------------------------------ reading
async def get(appointment_id: PydanticObjectId) -> Appointment:
    appointment = await Appointment.get(appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.", error_code="appointment_not_found")
    return appointment


def may_see(appointment: Appointment, user: User) -> bool:
    return user.id in (appointment.user_id, appointment.astrologer_user_id)


async def for_user(user_id: PydanticObjectId, *, upcoming_only: bool = False):
    query = [Appointment.user_id == user_id]
    if upcoming_only:
        query.append(GTE(Appointment.ends_at, utcnow()))
        query.append(In(Appointment.status, [AppointmentStatus.BOOKED]))
    return await Appointment.find(And(*query)).sort(+Appointment.starts_at).to_list()


async def for_astrologer(
    astrologer_user_id: PydanticObjectId, *, upcoming_only: bool = False
):
    profile = await Astrologer.find_one(Astrologer.user_id == astrologer_user_id)
    if profile and profile.id:
        astro_match = Or(
            Appointment.astrologer_user_id == astrologer_user_id,
            Appointment.astrologer_id == profile.id,
        )
    else:
        astro_match = Appointment.astrologer_user_id == astrologer_user_id

    query = [astro_match]
    if upcoming_only:
        query.append(GTE(Appointment.ends_at, utcnow()))
        query.append(In(Appointment.status, [AppointmentStatus.BOOKED]))
        return await Appointment.find(And(*query)).sort(+Appointment.starts_at).to_list()
    return await Appointment.find(And(*query)).sort(-Appointment.starts_at).to_list()


async def _notify(appointment: Appointment) -> None:
    """Tells both sides their calendar moved. Never fails the booking."""
    try:
        from app.services import realtime

        payload = {
            "type": "appointment",
            "data": {
                "id": str(appointment.id),
                "status": appointment.status.value,
                "starts_at": appointment.starts_at.isoformat(),
                "ends_at": appointment.ends_at.isoformat(),
                "minutes": appointment.minutes,
            },
        }
        for who in (appointment.user_id, appointment.astrologer_user_id):
            await realtime.publish_chat(who, payload)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Appointment push skipped: {}", exc)
