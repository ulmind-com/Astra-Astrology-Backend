"""Scheduled appointments: the calendar, and booking a place in it."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, status

from app.api.dependencies import AstrologerUser, CurrentAstrologer, CurrentUser
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.appointment import SLOT_MINUTES, Appointment, AvailabilityWindow
from app.models.astrologer import Astrologer
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCardOut,
    AppointmentCardUpdate,
    AppointmentOut,
    AppointmentPeer,
    AppointmentQuote,
    BookRequest,
    CancelRequest,
    DayView,
    QuoteRequest,
    Range,
    WindowInput,
    WindowOut,
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services import appointments as service

router = APIRouter(prefix="/appointments", tags=["appointments"])


async def _peer_for(appointment: Appointment, viewer: User) -> AppointmentPeer | None:
    """The other person, from this viewer's side of the booking."""
    if viewer.id == appointment.user_id:
        profile = await Astrologer.get(appointment.astrologer_id)
        if profile is None:
            return None
        return AppointmentPeer(
            id=str(profile.id),
            name=profile.display_name,
            avatar_url=profile.profile_image_url,
        )

    other = await User.get(appointment.user_id)
    if other is None:
        return None
    return AppointmentPeer(id=str(other.id), name=other.full_name, avatar_url=None)


async def _out(appointment: Appointment, viewer: User) -> AppointmentOut:
    return AppointmentOut(
        id=str(appointment.id),
        status=appointment.status,
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
        minutes=appointment.minutes,
        price_paise=appointment.price_paise,
        commission_percent=appointment.commission_percent,
        deposit_paise=appointment.deposit_paise,
        deposit_coins=appointment.deposit_coins,
        balance_due_paise=appointment.balance_due_paise,
        cancelled_at=appointment.cancelled_at,
        cancel_reason=appointment.cancel_reason,
        user_note=appointment.user_note,
        peer=await _peer_for(appointment, viewer),
    )


# ======================================================= the astrologer's own
@router.get(
    "/me/card",
    response_model=ApiResponse[AppointmentCardOut],
    summary="What I charge for an appointment",
)
async def my_card(profile: CurrentAstrologer) -> ApiResponse[AppointmentCardOut]:
    return ApiResponse(
        message="Card fetched.", data=AppointmentCardOut(**profile.appointment.model_dump())
    )


@router.patch(
    "/me/card",
    response_model=ApiResponse[AppointmentCardOut],
    summary="Set what I charge",
)
async def update_my_card(
    payload: AppointmentCardUpdate, profile: CurrentAstrologer
) -> ApiResponse[AppointmentCardOut]:
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in changes.items():
        setattr(profile.appointment, field, value)

    if profile.appointment.enabled and profile.appointment.price_paise <= 0:
        raise BadRequestError(
            "Set a price before taking appointments.", error_code="price_required"
        )

    await profile.save()
    return ApiResponse(
        message="Saved.", data=AppointmentCardOut(**profile.appointment.model_dump())
    )


@router.get(
    "/me/windows",
    response_model=ApiResponse[list[WindowOut]],
    summary="The hours I have opened",
)
async def my_windows(
    profile: CurrentAstrologer,
    days: Annotated[int, Query(ge=1, le=365)] = 60,
) -> ApiResponse[list[WindowOut]]:
    from beanie.operators import GTE, And

    from app.models.base import utcnow

    windows = (
        await AvailabilityWindow.find(
            And(
                AvailabilityWindow.astrologer_id == profile.id,
                GTE(AvailabilityWindow.ends_at, utcnow() - timedelta(days=1)),
                # Only as far ahead as was asked for.
                AvailabilityWindow.starts_at <= utcnow() + timedelta(days=days),
            )
        )
        .sort(+AvailabilityWindow.starts_at)
        .to_list()
    )
    return ApiResponse(
        message="Windows fetched.",
        data=[
            WindowOut(id=str(w.id), day=w.day, starts_at=w.starts_at, ends_at=w.ends_at)
            for w in windows
        ],
    )


@router.post(
    "/me/windows",
    response_model=ApiResponse[WindowOut],
    status_code=status.HTTP_201_CREATED,
    summary="Open some hours for booking",
)
async def add_window(
    payload: WindowInput, profile: CurrentAstrologer
) -> ApiResponse[WindowOut]:
    """Adds one stretch of one day.

    Overlapping an existing window is refused rather than merged: two windows
    that overlap are almost always a mistake, and silently joining them would
    open hours the astrologer never chose.
    """
    starts = payload.starts_at.astimezone(UTC).replace(second=0, microsecond=0)
    ends = payload.ends_at.astimezone(UTC).replace(second=0, microsecond=0)

    if ends <= starts:
        raise BadRequestError("The end must be after the start.", error_code="bad_window")
    if (ends - starts).total_seconds() < SLOT_MINUTES * 60:
        raise BadRequestError(
            f"A window must be at least {SLOT_MINUTES} minutes.", error_code="window_too_short"
        )
    if starts.minute % SLOT_MINUTES or ends.minute % SLOT_MINUTES:
        raise BadRequestError(
            f"Use {SLOT_MINUTES}-minute marks.", error_code="unaligned_window"
        )

    from beanie.operators import GTE, LT, And

    clash = await AvailabilityWindow.find_one(
        And(
            AvailabilityWindow.astrologer_id == profile.id,
            LT(AvailabilityWindow.starts_at, ends),
            GTE(AvailabilityWindow.ends_at, starts),
        )
    )
    if clash is not None:
        raise BadRequestError(
            "That overlaps hours you have already opened.", error_code="window_overlap"
        )

    window = AvailabilityWindow(
        astrologer_id=profile.id, day=starts.date(), starts_at=starts, ends_at=ends
    )
    await window.insert()
    return ApiResponse(
        message="Hours opened.",
        data=WindowOut(
            id=str(window.id), day=window.day, starts_at=window.starts_at, ends_at=window.ends_at
        ),
    )


@router.delete(
    "/me/windows/{window_id}",
    response_model=MessageResponse,
    summary="Close hours I had opened",
)
async def remove_window(
    window_id: PydanticObjectId, profile: CurrentAstrologer
) -> MessageResponse:
    """Refused if anything is booked inside it, which would strand the booking."""
    window = await AvailabilityWindow.get(window_id)
    if window is None or window.astrologer_id != profile.id:
        raise NotFoundError("Those hours were not found.", error_code="window_not_found")

    booked = await service.booked_between(profile.id, window.starts_at, window.ends_at)
    if booked:
        raise BadRequestError(
            "Someone has booked inside those hours. Cancel the appointment first.",
            error_code="window_has_bookings",
        )

    await window.delete()
    return MessageResponse(message="Hours closed.")


@router.get(
    "/me/schedule",
    response_model=ApiResponse[list[AppointmentOut]],
    summary="My appointments",
)
async def my_schedule(
    user: AstrologerUser,
    upcoming_only: bool = True,
) -> ApiResponse[list[AppointmentOut]]:
    bookings = await service.for_astrologer(user.id, upcoming_only=upcoming_only)
    return ApiResponse(
        message="Schedule fetched.",
        data=[await _out(a, user) for a in bookings],
    )


# ================================================================ the user's
@router.get(
    "/astrologers/{astrologer_id}/day",
    response_model=ApiResponse[DayView],
    summary="What is open and what is taken on one day",
)
async def day(
    astrologer_id: PydanticObjectId,
    on: Annotated[str, Query(description="The day, as YYYY-MM-DD")],
) -> ApiResponse[DayView]:
    from app.services import settings as settings_service

    profile = await Astrologer.get(astrologer_id)
    if profile is None or not profile.is_listed:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    try:
        chosen = datetime.strptime(on, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        raise BadRequestError("Use YYYY-MM-DD.", error_code="bad_date")

    # A generous span either side, so a window that straddles midnight in the
    # viewer's timezone is still included.
    view = await service.day_view(
        astrologer=profile,
        day_start=chosen - timedelta(days=1),
        day_end=chosen + timedelta(days=2),
    )
    platform = await settings_service.get_settings()

    return ApiResponse(
        message="Day fetched.",
        data=DayView(
            windows=[Range(**w) for w in view["windows"]],
            booked=[Range(**b) for b in view["booked"]],
            slot_minutes=SLOT_MINUTES,
            min_minutes=platform.min_appointment_minutes,
            max_minutes=platform.max_appointment_minutes,
        ),
    )


@router.post(
    "/quote",
    response_model=ApiResponse[AppointmentQuote],
    summary="What a booking of this length would cost",
)
async def quote(payload: QuoteRequest, user: CurrentUser) -> ApiResponse[AppointmentQuote]:
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    profile = await Astrologer.get(PydanticObjectId(payload.astrologer_id))
    if profile is None or not profile.is_listed:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    platform = await settings_service.get_settings()
    price = service.price_for(profile.appointment, payload.minutes)
    deposit = service.deposit_for(price, platform.appointment_commission_percent)
    coins = service.coins_for_paise(deposit, platform.coins_per_rupee)
    wallet = await wallet_service.get_or_create_wallet(user.id)

    return ApiResponse(
        message="Quote ready.",
        data=AppointmentQuote(
            minutes=payload.minutes,
            price_paise=price,
            commission_percent=platform.appointment_commission_percent,
            deposit_paise=deposit,
            deposit_coins=coins,
            balance_due_paise=max(price - deposit, 0),
            balance_coins=wallet.balance_coins,
            can_afford=wallet.balance_coins >= coins,
        ),
    )


@router.post(
    "",
    response_model=ApiResponse[AppointmentOut],
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment",
)
async def book(payload: BookRequest, user: CurrentUser) -> ApiResponse[AppointmentOut]:
    profile = await Astrologer.get(PydanticObjectId(payload.astrologer_id))
    if profile is None or not profile.is_listed:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    appointment = await service.book(
        user=user,
        astrologer=profile,
        starts_at=payload.starts_at,
        minutes=payload.minutes,
        note=payload.note,
    )
    return ApiResponse(message="Booked.", data=await _out(appointment, user))


@router.get(
    "/mine",
    response_model=ApiResponse[list[AppointmentOut]],
    summary="My appointments",
)
async def mine(
    user: CurrentUser, upcoming_only: bool = False
) -> ApiResponse[list[AppointmentOut]]:
    bookings = await service.for_user(user.id, upcoming_only=upcoming_only)
    return ApiResponse(
        message="Appointments fetched.", data=[await _out(a, user) for a in bookings]
    )


@router.get(
    "/{appointment_id}",
    response_model=ApiResponse[AppointmentOut],
    summary="One appointment",
)
async def one(
    appointment_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    if not service.may_see(appointment, user):
        raise ForbiddenError("This is not your appointment.", error_code="not_yours")
    return ApiResponse(message="Appointment fetched.", data=await _out(appointment, user))


@router.post(
    "/{appointment_id}/cancel",
    response_model=ApiResponse[AppointmentOut],
    summary="Cancel — the deposit is not returned",
)
async def cancel(
    appointment_id: PydanticObjectId, payload: CancelRequest, user: CurrentUser
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    cancelled = await service.cancel(appointment=appointment, by=user, reason=payload.reason)
    return ApiResponse(message="Cancelled.", data=await _out(cancelled, user))
