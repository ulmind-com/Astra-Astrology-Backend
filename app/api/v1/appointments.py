"""Scheduled appointments: the calendar, and booking a place in it."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from beanie import PydanticObjectId
from beanie.operators import In
from fastapi import APIRouter, Query, status
from fastapi.responses import HTMLResponse
from loguru import logger

from app.api.dependencies import AstrologerUser, CurrentAstrologer, CurrentUser
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.appointment import (
    SLOT_MINUTES,
    Appointment,
    AppointmentStatus,
    AvailabilityWindow,
    PrivateInviteLink,
)
from app.models.astrologer import Astrologer
from app.models.user import User
from app.schemas.appointment import (
    AbuseReportOut,
    AppointmentCardOut,
    AppointmentCardUpdate,
    AppointmentOut,
    AppointmentPeer,
    AppointmentQuote,
    BlacklistedClientOut,
    BookRequest,
    BrahmaPauseActionRequest,
    BrahmaPauseRequest,
    CancelRequest,
    CreatePrivateInviteLinkRequest,
    DayView,
    ExtensionActionRequest,
    IssueFollowUpPassRequest,
    NoShowRequest,
    OfferExtensionRequest,
    PrescriptionUpdateRequest,
    PrivateInviteLinkOut,
    QuickTatkalWindowRequest,
    QuoteRequest,
    Range,
    RedFlagRequest,
    RequestBTRRequest,
    RescheduleRequest,
    SendFollowUpMessageRequest,
    UpdateBTRRequest,
    UpdatePrivateNotesRequest,
    ValidatePrivateInviteResponse,
    VerifyPasscodeRequest,
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


async def _peers_for(
    appointments: list[Appointment], viewer: User
) -> dict[PydanticObjectId, AppointmentPeer]:
    """Every booking's other person, in two queries instead of one per booking."""
    astrologer_ids = {a.astrologer_id for a in appointments if viewer.id == a.user_id}
    user_ids = {a.user_id for a in appointments if viewer.id != a.user_id}

    profiles: dict[PydanticObjectId, Astrologer] = {}
    if astrologer_ids:
        found = await Astrologer.find(In(Astrologer.id, list(astrologer_ids))).to_list()
        profiles = {p.id: p for p in found if p.id is not None}

    others: dict[PydanticObjectId, User] = {}
    if user_ids:
        found_users = await User.find(In(User.id, list(user_ids))).to_list()
        others = {u.id: u for u in found_users if u.id is not None}

    peers: dict[PydanticObjectId, AppointmentPeer] = {}
    for appointment in appointments:
        if appointment.id is None:
            continue
        if viewer.id == appointment.user_id:
            profile = profiles.get(appointment.astrologer_id)
            if profile is not None:
                peers[appointment.id] = AppointmentPeer(
                    id=str(profile.id),
                    name=profile.display_name,
                    avatar_url=profile.profile_image_url,
                )
        else:
            other = others.get(appointment.user_id)
            if other is not None:
                peers[appointment.id] = AppointmentPeer(
                    id=str(other.id), name=other.full_name, avatar_url=None
                )
    return peers


async def _out(
    appointment: Appointment,
    viewer: User,
    peers: dict[PydanticObjectId, AppointmentPeer] | None = None,
) -> AppointmentOut:
    from datetime import timedelta
    from app.models.base import utcnow

    now = utcnow()
    window_mins = getattr(appointment, "cancellation_window_minutes", 30) or 30
    deadline = appointment.cancel_deadline or (
        appointment.created_at + timedelta(minutes=window_mins)
    )
    is_client = viewer.id == appointment.user_id
    if appointment.status != AppointmentStatus.BOOKED:
        can_cancel = False
    elif is_client:
        can_cancel = now < deadline and now < appointment.starts_at
    else:
        can_cancel = True

    coins_rate = appointment.coins_per_rupee or 1
    balance_due_coins = service.coins_for_paise(appointment.balance_due_paise, coins_rate)

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
        balance_due_coins=balance_due_coins,
        held_coins=getattr(appointment, "held_coins", 0),
        held_status=getattr(appointment, "held_status", "none"),
        cancellation_window_minutes=window_mins,
        cancel_deadline=deadline,
        can_cancel=can_cancel,
        completed_at=getattr(appointment, "completed_at", None),
        cancelled_at=appointment.cancelled_at,
        cancel_reason=appointment.cancel_reason,
        user_note=appointment.user_note,
        consultation_pillar=appointment.consultation_pillar,
        kundli_id=str(appointment.kundli_id) if appointment.kundli_id else None,
        birth_details=appointment.birth_details,
        prescription=appointment.prescription,
        muhurat_type=appointment.muhurat_type,
        preflight_dossier=getattr(appointment, "preflight_dossier", None),
        cosmic_synergy_score=getattr(appointment, "cosmic_synergy_score", None),
        certificate_data=getattr(appointment, "certificate_data", None),
        rescheduled_count=getattr(appointment, "rescheduled_count", 0),
        rescheduled_at=getattr(appointment, "rescheduled_at", None),
        previous_starts_at=getattr(appointment, "previous_starts_at", None),
        reschedule_reason=getattr(appointment, "reschedule_reason", None),
        is_no_show=getattr(appointment, "is_no_show", False),
        no_show_marked_at=getattr(appointment, "no_show_marked_at", None),
        call_session_id=str(appointment.call_session_id) if getattr(appointment, "call_session_id", None) else None,
        brahma_pause_affected=getattr(appointment, "brahma_pause_affected", False),
        brahma_pause_reason=getattr(appointment, "brahma_pause_reason", None),
        brahma_pause_until=getattr(appointment, "brahma_pause_until", None),
        rescue_deadline=getattr(appointment, "rescue_deadline", None),
        abuse_flagged=getattr(appointment, "abuse_flagged", False),
        abuse_reason=getattr(appointment, "abuse_reason", None),
        abuse_flagged_at=getattr(appointment, "abuse_flagged_at", None),
        btr_requested=getattr(appointment, "btr_requested", False),
        btr_request_note=getattr(appointment, "btr_request_note", None),
        btr_requested_at=getattr(appointment, "btr_requested_at", None),
        btr_fulfilled=getattr(appointment, "btr_fulfilled", False),
        btr_updated_at=getattr(appointment, "btr_updated_at", None),
        extension_offered=getattr(appointment, "extension_offered", False),
        extension_offered_minutes=getattr(appointment, "extension_offered_minutes", None),
        extension_cost_coins=getattr(appointment, "extension_cost_coins", 0),
        extension_cost_paise=getattr(appointment, "extension_cost_paise", 0),
        extension_offered_at=getattr(appointment, "extension_offered_at", None),
        extension_status=getattr(appointment, "extension_status", "none"),
        extension_total_extended_minutes=getattr(appointment, "extension_total_extended_minutes", 0),
        follow_up_pass_enabled=getattr(appointment, "follow_up_pass_enabled", False),
        follow_up_window_days=getattr(appointment, "follow_up_window_days", 7),
        follow_up_expires_at=getattr(appointment, "follow_up_expires_at", None),
        follow_up_max_messages=getattr(appointment, "follow_up_max_messages", 3),
        follow_up_messages_used=getattr(appointment, "follow_up_messages_used", 0),
        follow_up_granted_at=getattr(appointment, "follow_up_granted_at", None),
        follow_up_notes=getattr(appointment, "follow_up_notes", None),
        follow_up_thread=getattr(appointment, "follow_up_thread", []) or [],
        is_tatkal=getattr(appointment, "is_tatkal", False),
        tatkal_multiplier=getattr(appointment, "tatkal_multiplier", None),
        tatkal_premium_paise=getattr(appointment, "tatkal_premium_paise", 0),
        tatkal_premium_coins=getattr(appointment, "tatkal_premium_coins", 0),
        is_private=getattr(appointment, "is_private", False),
        invite_code=getattr(appointment, "invite_code", None),
        astrologer_private_notes=(
            None if is_client else getattr(appointment, "astrologer_private_notes", None)
        ),
        astrologer_private_notes_updated_at=(
            None if is_client else getattr(appointment, "astrologer_private_notes_updated_at", None)
        ),
        peer=(
            peers.get(appointment.id)
            if peers is not None
            else await _peer_for(appointment, viewer)
        ),
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

    # If price is set (> 0) and enabled wasn't explicitly set to False, default to enabled
    if "enabled" not in changes and profile.appointment.price_paise > 0:
        profile.appointment.enabled = True

    if profile.appointment.enabled and profile.appointment.price_paise <= 0:
        raise BadRequestError(
            "Set a price before taking appointments.", error_code="price_required"
        )

    await profile.save()
    try:
        from app.services import realtime
        await realtime.publish_astrologer(profile)
    except Exception as exc:
        logger.debug("Realtime astrologer publish skipped: {}", exc)

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
            WindowOut(
                id=str(w.id),
                day=w.day,
                starts_at=w.starts_at,
                ends_at=w.ends_at,
                is_tatkal=getattr(w, "is_tatkal", False),
                tatkal_multiplier=getattr(w, "tatkal_multiplier", 1.5),
                tatkal_fixed_paise=getattr(w, "tatkal_fixed_paise", None),
                custom_title=getattr(w, "custom_title", None),
                is_private=getattr(w, "is_private", False),
            )
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
        astrologer_id=profile.id,
        day=starts.date(),
        starts_at=starts,
        ends_at=ends,
        is_tatkal=payload.is_tatkal,
        tatkal_multiplier=payload.tatkal_multiplier,
        tatkal_fixed_paise=payload.tatkal_fixed_paise,
        custom_title=payload.custom_title,
        is_private=payload.is_private,
    )
    await window.insert()

    # If the astrologer has a price set, opening an availability window means they are
    # actively taking appointments — auto-enable appointment card so users can book immediately.
    if profile.appointment.price_paise > 0 and not profile.appointment.enabled:
        profile.appointment.enabled = True
        await profile.save()
        try:
            from app.services import realtime
            await realtime.publish_astrologer(profile)
        except Exception as exc:
            logger.debug("Realtime astrologer publish skipped: {}", exc)

    try:
        from app.services import realtime
        await realtime.publish_availability_event(profile.id, str(window.day))
    except Exception as exc:
        logger.debug("Realtime availability publish skipped: {}", exc)

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

    day_str = str(window.day)
    await window.delete()

    try:
        from app.services import realtime
        await realtime.publish_availability_event(profile.id, day_str)
    except Exception as exc:
        logger.debug("Realtime availability delete publish skipped: {}", exc)

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
    peers = await _peers_for(bookings, user)
    return ApiResponse(
        message="Schedule fetched.",
        data=[await _out(a, user, peers) for a in bookings],
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
    invite_code: Annotated[str | None, Query(description="Optional private invitation code")] = None,
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
        invite_code=invite_code,
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

    starts = (
        payload.starts_at.astimezone(UTC).replace(second=0, microsecond=0)
        if payload.starts_at
        else None
    )
    ends = starts + timedelta(minutes=payload.minutes) if starts else None

    # Check for private invite link
    invite_link = None
    if payload.invite_code:
        invite_link = await PrivateInviteLink.find_one(
            {"invite_code": payload.invite_code, "astrologer_id": profile.id, "is_active": True}
        )

    # Check for Tatkal covering window
    is_tatkal_slot = False
    tatkal_multiplier = 1.0
    tatkal_fixed_paise = None
    if starts and ends:
        windows = await service._windows_for(profile.id, starts, ends, include_private=True)
        covering = service._find_covering_window(windows, starts, ends)
        if covering and getattr(covering, "is_tatkal", False):
            is_tatkal_slot = True
            tatkal_multiplier = getattr(covering, "tatkal_multiplier", 1.5) or 1.5
            tatkal_fixed_paise = getattr(covering, "tatkal_fixed_paise", None)
    elif invite_link and invite_link.is_tatkal:
        is_tatkal_slot = True

    standard_price = service.price_for(profile.appointment, payload.minutes)
    price = service.price_for(
        profile.appointment,
        payload.minutes,
        tatkal_multiplier=tatkal_multiplier if is_tatkal_slot else None,
        tatkal_fixed_paise=tatkal_fixed_paise,
        custom_price_paise=getattr(invite_link, "custom_price_paise", None),
        discount_percent=getattr(invite_link, "discount_percent", None),
    )
    tatkal_premium_paise = max(0, price - standard_price) if is_tatkal_slot else 0
    tatkal_premium_coins = service.coins_for_paise(tatkal_premium_paise, platform.coins_per_rupee)

    deposit_paise = service.deposit_for(price, platform.appointment_commission_percent)
    deposit_coins = service.coins_for_paise(deposit_paise, platform.coins_per_rupee)
    balance_due_paise = max(price - deposit_paise, 0)
    balance_due_coins = service.coins_for_paise(balance_due_paise, platform.coins_per_rupee)
    total_coins = deposit_coins + balance_due_coins

    wallet = await wallet_service.get_or_create_wallet(user.id)
    spendable = wallet.available_coins
    can_afford = spendable >= total_coins

    return ApiResponse(
        message="Quote ready.",
        data=AppointmentQuote(
            minutes=payload.minutes,
            price_paise=price,
            commission_percent=platform.appointment_commission_percent,
            deposit_paise=deposit_paise,
            deposit_coins=deposit_coins,
            balance_due_paise=balance_due_paise,
            balance_due_coins=balance_due_coins,
            total_coins=total_coins,
            available_coins=spendable,
            balance_coins=wallet.balance_coins,
            can_afford=can_afford,
            is_tatkal=is_tatkal_slot,
            tatkal_multiplier=tatkal_multiplier,
            tatkal_premium_paise=tatkal_premium_paise,
            tatkal_premium_coins=tatkal_premium_coins,
            is_private=bool(invite_link),
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
        consultation_pillar=payload.consultation_pillar,
        kundli_id=PydanticObjectId(payload.kundli_id) if payload.kundli_id else None,
        birth_details=payload.birth_details,
        invite_code=payload.invite_code,
        invite_passcode=payload.invite_passcode,
    )
    return ApiResponse(message="Booked.", data=await _out(appointment, user))


@router.patch(
    "/{appointment_id}/prescription",
    response_model=ApiResponse[AppointmentOut],
    summary="Update astrological remedy prescription",
)
async def update_prescription_endpoint(
    appointment_id: PydanticObjectId,
    payload: PrescriptionUpdateRequest,
    user: CurrentUser,
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    updated = await service.update_prescription(
        appointment=appointment,
        astrologer_user_id=user.id,
        prescription_data=payload.model_dump(exclude_unset=True),
    )
    return ApiResponse(message="Prescription saved.", data=await _out(updated, user))


@router.patch(
    "/{appointment_id}/private-notes",
    response_model=ApiResponse[AppointmentOut],
    summary="Update confidential astrologer dossier vault notes",
)
async def update_private_notes_endpoint(
    appointment_id: PydanticObjectId,
    payload: UpdatePrivateNotesRequest,
    user: CurrentUser,
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    updated = await service.update_private_notes(
        appointment=appointment,
        astrologer_user_id=user.id,
        notes=payload.notes,
    )
    return ApiResponse(message="Private vault notes saved.", data=await _out(updated, user))



@router.get(
    "/mine",
    response_model=ApiResponse[list[AppointmentOut]],
    summary="My appointments",
)
async def mine(
    user: CurrentUser, upcoming_only: bool = False
) -> ApiResponse[list[AppointmentOut]]:
    bookings = await service.for_user(user.id, upcoming_only=upcoming_only)
    peers = await _peers_for(bookings, user)
    return ApiResponse(
        message="Appointments fetched.",
        data=[await _out(a, user, peers) for a in bookings],
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
    summary="Cancel — user grace period and refund rules applied",
)
async def cancel(
    appointment_id: PydanticObjectId, payload: CancelRequest, user: CurrentUser
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    cancelled = await service.cancel(appointment=appointment, by=user, reason=payload.reason)
    return ApiResponse(message="Cancelled.", data=await _out(cancelled, user))


@router.post(
    "/{appointment_id}/complete",
    response_model=ApiResponse[AppointmentOut],
    summary="Complete appointment and capture escrowed balance",
)
async def complete(
    appointment_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    completed = await service.complete(appointment=appointment, by=user)
    return ApiResponse(message="Appointment completed.", data=await _out(completed, user))


@router.post(
    "/{appointment_id}/reschedule",
    response_model=ApiResponse[AppointmentOut],
    summary="Courtesy Reschedule: 1-time free slot move by astrologer",
)
async def reschedule(
    appointment_id: PydanticObjectId,
    payload: RescheduleRequest,
    user: CurrentUser,
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    rescheduled = await service.reschedule(
        appointment=appointment,
        by=user,
        new_starts_at=payload.new_starts_at,
        reason=payload.reason,
    )
    return ApiResponse(message="Appointment courtesy rescheduled.", data=await _out(rescheduled, user))


@router.post(
    "/{appointment_id}/no-show",
    response_model=ApiResponse[AppointmentOut],
    summary="Mark client no-show after waiting 10-15m in chamber",
)
async def mark_no_show(
    appointment_id: PydanticObjectId,
    payload: NoShowRequest,
    user: CurrentUser,
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    marked = await service.mark_no_show(
        appointment=appointment,
        by=user,
        reason=payload.reason,
    )
    return ApiResponse(message="Appointment marked as Client No-Show.", data=await _out(marked, user))


@router.post(
    "/{appointment_id}/chamber",
    response_model=ApiResponse[dict],
    summary="Join live video chamber for a scheduled appointment",
)
async def join_appointment_chamber(
    appointment_id: PydanticObjectId,
    user: CurrentUser,
) -> ApiResponse[dict]:
    """Provides authorized access and ZegoCloud room credentials for this appointment."""
    from app.models.base import utcnow
    from app.models.call import CallSession
    from app.models.enums import CallStatus, ConsultationMode
    from app.services import call as call_service

    appointment = await service.get(appointment_id)
    if not service.may_see(appointment, user):
        raise ForbiddenError("This is not your appointment.", error_code="not_yours")
    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError("This appointment is not active.", error_code="appointment_not_open")

    now = utcnow()
    earliest = appointment.starts_at - timedelta(minutes=10)
    latest = appointment.ends_at + timedelta(minutes=15)
    if now < earliest:
        raise BadRequestError(
            f"Chamber opens 10 minutes prior to session. Your session starts at {appointment.starts_at.strftime('%I:%M %p')}.",
            error_code="chamber_not_open_yet",
        )
    if now > latest:
        raise BadRequestError(
            "This appointment window has closed.",
            error_code="chamber_window_closed",
        )

    call_session = None
    if getattr(appointment, "call_session_id", None):
        call_session = await CallSession.get(appointment.call_session_id)
        if call_session and call_session.status not in (CallStatus.ACTIVE, CallStatus.RINGING):
            call_session = None

    if not call_session:
        call_session = CallSession(
            user_id=appointment.user_id,
            astrologer_id=appointment.astrologer_id,
            astrologer_user_id=appointment.astrologer_user_id,
            mode=ConsultationMode.VIDEO,
            room_id=f"astra_apt_{appointment.id}_{int(now.timestamp())}",
            status=CallStatus.ACTIVE,
            started_at=now,
            requested_minutes=appointment.minutes,
            coins_per_minute=0,  # Prepaid through appointment escrow!
            appointment_id=appointment.id,
        )
        await call_session.insert()
        appointment.call_session_id = call_session.id
        await appointment.save()

    token = await call_service.token_for(call_session, user)
    return ApiResponse(
        message="Chamber ready.",
        data={
            "call_id": str(call_session.id),
            "room_id": call_session.room_id,
            "token": token,
            "starts_at": appointment.starts_at.isoformat(),
            "ends_at": appointment.ends_at.isoformat(),
            "minutes": appointment.minutes,
        },
    )


@router.post(
    "/brahma-pause",
    response_model=ApiResponse[dict],
    summary="Activate Brahma Pause (emergency break) and trigger seeker auto-rescue",
)
async def activate_brahma_pause(
    payload: BrahmaPauseRequest,
    profile: CurrentAstrologer,
) -> ApiResponse[dict]:
    """Takes astrologer offline, shields upcoming slots, and sends 1-click rescue choices to affected seekers."""
    result = await service.activate_brahma_pause(
        astrologer=profile,
        duration_hours=payload.duration_hours,
        reason=payload.reason,
    )
    return ApiResponse(
        message=f"Brahma Pause activated for {payload.duration_hours} hours.",
        data=result,
    )


@router.post(
    "/brahma-pause/resume",
    response_model=ApiResponse[dict],
    summary="End Brahma Pause early and restore normal schedule",
)
async def resume_brahma_pause(
    profile: CurrentAstrologer,
) -> ApiResponse[dict]:
    """Resumes astrologer schedule and clears active emergency break."""
    result = await service.resume_brahma_pause(astrologer=profile)
    return ApiResponse(message="Brahma Pause ended successfully.", data=result)


@router.post(
    "/{appointment_id}/brahma-pause-action",
    response_model=ApiResponse[AppointmentOut],
    summary="Seeker choice during Brahma Pause: complimentary reschedule or 100% instant refund",
)
async def brahma_pause_rescue_action(
    appointment_id: PydanticObjectId,
    payload: BrahmaPauseActionRequest,
    user: CurrentUser,
) -> ApiResponse[AppointmentOut]:
    """Processes seeker's 1-click decision when an astrologer activates Brahma Pause."""
    appointment = await service.get(appointment_id)
    updated = await service.handle_brahma_pause_rescue_action(
        appointment=appointment,
        user=user,
        action=payload.action,
        new_starts_at=payload.new_starts_at,
        reason=payload.reason,
    )
    return ApiResponse(
        message="Brahma Pause action processed successfully.",
        data=await _out(updated, user),
    )


@router.get(
    "/synergy",
    response_model=ApiResponse[dict],
    summary="Calculate cosmic resonance compatibility index between user and astrologer",
)
async def get_cosmic_synergy(
    astrologer_id: str,
    dob: str | None = None,
    user: CurrentUser = None,
) -> ApiResponse[dict]:
    from app.services.cosmic_intelligence import calculate_cosmic_synergy

    profile = await Astrologer.get(PydanticObjectId(astrologer_id))
    if profile is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")
    synergy = calculate_cosmic_synergy({"dob": dob} if dob else None, profile.id)
    return ApiResponse(message="Cosmic synergy calculated.", data=synergy)


@router.get(
    "/{appointment_id}/preflight",
    response_model=ApiResponse[dict],
    summary="Get or generate AI Astrological Pre-Flight Dossier (Astrologer & Admin only)",
)
async def get_preflight(
    appointment_id: PydanticObjectId,
    user: CurrentUser,
) -> ApiResponse[dict]:
    appointment = await service.get(appointment_id)
    if appointment.astrologer_user_id != user.id and getattr(user, "role", None) != "admin":
        raise ForbiddenError("Only the consulting astrologer or admin can access the pre-flight dossier.")

    dossier = appointment.preflight_dossier
    if not dossier:
        from app.services.cosmic_intelligence import generate_preflight_dossier

        dossier = await generate_preflight_dossier(appointment)
    return ApiResponse(message="Pre-flight dossier fetched.", data=dossier)


@router.get(
    "/{appointment_id}/certificate",
    response_model=ApiResponse[dict],
    summary="Get Divya Paramarsha Sacred Certificate data",
)
async def get_certificate(
    appointment_id: PydanticObjectId,
    user: CurrentUser,
) -> ApiResponse[dict]:
    appointment = await service.get(appointment_id)
    if not service.may_see(appointment, user):
        raise ForbiddenError("This is not your appointment.")

    cert = appointment.certificate_data
    if not cert and appointment.status == AppointmentStatus.COMPLETED:
        from app.services.cosmic_intelligence import generate_divya_paramarsha_certificate_data

        astro = await Astrologer.get(appointment.astrologer_id)
        client_u = await User.get(appointment.user_id)
        if astro and client_u:
            cert = generate_divya_paramarsha_certificate_data(appointment, astro, client_u)
            appointment.certificate_data = cert
            await appointment.save()

    if not cert:
        raise BadRequestError("Certificate is only generated once consultation is completed.")
    return ApiResponse(message="Certificate fetched.", data=cert)


@router.get(
    "/{appointment_id}/certificate/html",
    response_class=HTMLResponse,
    summary="Render printable high-res Divya Paramarsha Sacred Certificate HTML",
)
async def get_certificate_html_endpoint(
    appointment_id: PydanticObjectId,
    user: CurrentUser,
) -> HTMLResponse:
    appointment = await service.get(appointment_id)
    if not service.may_see(appointment, user):
        raise ForbiddenError("This is not your appointment.")

    cert = appointment.certificate_data
    if not cert and appointment.status == AppointmentStatus.COMPLETED:
        from app.services.cosmic_intelligence import generate_divya_paramarsha_certificate_data

        astro = await Astrologer.get(appointment.astrologer_id)
        client_u = await User.get(appointment.user_id)
        if astro and client_u:
            cert = generate_divya_paramarsha_certificate_data(appointment, astro, client_u)
            appointment.certificate_data = cert
            await appointment.save()

    if not cert:
        raise BadRequestError("Certificate is only generated once consultation is completed.")

    from app.services.cosmic_intelligence import generate_certificate_html

    html_content = generate_certificate_html(cert)
    return HTMLResponse(content=html_content)


@router.post(
    "/{appointment_id}/standby",
    response_model=ApiResponse[dict],
    summary="Join the Cosmic Standby Waitlist for a booked appointment slot",
)
async def join_standby_waitlist(
    appointment_id: PydanticObjectId,
    user: CurrentUser,
) -> ApiResponse[dict]:
    appointment = await service.get(appointment_id)
    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError("Standby queue is only available for booked appointments.")

    queue = getattr(appointment, "standby_queue", []) or []
    if any(q.get("user_id") == str(user.id) for q in queue):
        return ApiResponse(
            message="You are already in the standby queue for this slot.",
            data={"position": len(queue)},
        )

    from app.models.base import utcnow

    queue.append({
        "user_id": str(user.id),
        "email": user.email,
        "name": user.full_name or user.first_name or "Seeker",
        "joined_at": utcnow().isoformat(),
    })
    appointment.standby_queue = queue
    await appointment.save()
    return ApiResponse(
        message="Successfully joined Cosmic Standby Queue. You will be notified instantly if this slot opens up.",
        data={"position": len(queue)},
    )


# ======================================================= Client Screening & Abuse Shield
@router.post(
    "/{appointment_id}/red-flag",
    response_model=ApiResponse[AppointmentOut],
    summary="Red-flag appointment for misconduct, capture compensation and blacklist client",
)
async def red_flag_appointment(
    appointment_id: PydanticObjectId,
    req: RedFlagRequest,
    current_user: AstrologerUser,
) -> ApiResponse[AppointmentOut]:
    appt = await service.red_flag_appointment(
        appointment_id=appointment_id,
        by=current_user,
        reason=req.reason,
        notes=req.notes,
        blacklist_client=req.blacklist_client,
        terminate_call=req.terminate_call,
    )
    return ApiResponse(
        message="Session terminated and red-flagged. Escrow fee captured as earned compensation.",
        data=await _out(appt, current_user),
    )


@router.get(
    "/me/blacklist",
    response_model=ApiResponse[list[BlacklistedClientOut]],
    summary="List clients blacklisted by this astrologer",
)
async def get_my_blacklist(
    current_user: AstrologerUser,
) -> ApiResponse[list[BlacklistedClientOut]]:
    records = await service.get_astrologer_blacklist(current_user)
    return ApiResponse(
        message="Blacklist fetched.",
        data=[BlacklistedClientOut(**r) for r in records],
    )


@router.post(
    "/me/blacklist/{client_user_id}/unblock",
    response_model=ApiResponse[MessageResponse],
    summary="Unblock a blacklisted client",
)
async def unblock_client(
    client_user_id: PydanticObjectId,
    current_user: AstrologerUser,
) -> ApiResponse[MessageResponse]:
    unblocked = await service.unblock_astrologer_client(current_user, client_user_id)
    if not unblocked:
        raise NotFoundError("Client was not found in your blacklist.")
    return ApiResponse(
        message="Client has been unblocked from booking your schedule.",
        data=MessageResponse(message="Client unblocked successfully."),
    )


# ======================================================= Birth Time Rectification (BTR) Authority
@router.post(
    "/{appointment_id}/request-btr",
    response_model=ApiResponse[AppointmentOut],
    summary="Request Birth Time Rectification (BTR) from the client",
)
async def request_btr(
    appointment_id: PydanticObjectId,
    req: RequestBTRRequest,
    current_user: AstrologerUser,
) -> ApiResponse[AppointmentOut]:
    appt = await service.request_birth_time_rectification(
        appointment_id=appointment_id,
        by=current_user,
        note=req.note,
    )
    return ApiResponse(
        message="Birth Time Rectification requested from client.",
        data=await _out(appt, current_user),
    )


@router.post(
    "/{appointment_id}/update-btr",
    response_model=ApiResponse[AppointmentOut],
    summary="Client submits rectified exact birth time parameters",
)
async def update_btr(
    appointment_id: PydanticObjectId,
    req: UpdateBTRRequest,
    current_user: CurrentUser,
) -> ApiResponse[AppointmentOut]:
    appt = await service.update_birth_time_rectification(
        appointment_id=appointment_id,
        by=current_user,
        birth_date=req.birth_date,
        birth_time=req.birth_time,
        birth_place=req.birth_place,
        latitude=req.latitude,
        longitude=req.longitude,
        timezone_offset=req.timezone_offset,
        notes=req.notes,
    )
    return ApiResponse(
        message="Birth parameters updated successfully. Astrologer has been notified.",
        data=await _out(appt, current_user),
    )


@router.post(
    "/{appointment_id}/extension/offer",
    response_model=ApiResponse[AppointmentOut],
    summary="Astrologer offers an in-chamber consultation extension (+10/15 mins)",
)
async def offer_appointment_extension(
    appointment_id: PydanticObjectId,
    payload: OfferExtensionRequest,
    user: AstrologerUser,
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    updated = await service.offer_session_extension(
        appointment=appointment,
        by=user,
        extra_minutes=payload.extra_minutes,
    )
    return ApiResponse(
        message=f"Extension offer of {payload.extra_minutes} minutes sent to seeker.",
        data=await _out(updated, user),
    )


@router.post(
    "/{appointment_id}/extension/action",
    response_model=ApiResponse[AppointmentOut],
    summary="Client accepts or declines an in-chamber consultation extension offer",
)
async def handle_appointment_extension_action(
    appointment_id: PydanticObjectId,
    payload: ExtensionActionRequest,
    user: CurrentUser,
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    updated = await service.handle_session_extension_action(
        appointment=appointment,
        by=user,
        action=payload.action,
    )
    msg = (
        f"Extension accepted! Session extended by {payload.action} successfully."
        if payload.action.lower() == "accept"
        else "Extension offer declined."
    )
    return ApiResponse(message=msg, data=await _out(updated, user))


@router.post(
    "/{appointment_id}/follow-up/issue",
    response_model=ApiResponse[AppointmentOut],
    summary="Astrologer issues or customizes a complimentary remedy clarification pass",
)
async def issue_appointment_follow_up_pass(
    appointment_id: PydanticObjectId,
    payload: IssueFollowUpPassRequest,
    user: AstrologerUser,
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    updated = await service.issue_follow_up_pass(
        appointment=appointment,
        by=user,
        window_days=payload.window_days,
        max_messages=payload.max_messages,
        notes=payload.notes,
    )
    return ApiResponse(
        message=f"Complimentary {payload.window_days}-day remedy clarification pass issued.",
        data=await _out(updated, user),
    )


@router.post(
    "/{appointment_id}/follow-up/message",
    response_model=ApiResponse[AppointmentOut],
    summary="Send a remedy clarification message under the complimentary follow-up pass",
)
async def send_appointment_follow_up_message(
    appointment_id: PydanticObjectId,
    payload: SendFollowUpMessageRequest,
    user: CurrentUser,
) -> ApiResponse[AppointmentOut]:
    appointment = await service.get(appointment_id)
    updated, msg_item = await service.send_follow_up_message(
        appointment=appointment,
        by=user,
        text=payload.text,
    )
    return ApiResponse(
        message="Follow-up message delivered.",
        data=await _out(updated, user),
    )


# ================================================================= VIP & Private Links
@router.post(
    "/me/private-links",
    response_model=ApiResponse[PrivateInviteLinkOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create a VIP private invite-only booking link",
)
async def create_private_link(
    payload: CreatePrivateInviteLinkRequest,
    profile: CurrentAstrologer,
) -> ApiResponse[PrivateInviteLinkOut]:
    link = await service.create_private_invite_link(
        astrologer=profile,
        title=payload.title,
        client_name=payload.client_name,
        client_email=payload.client_email,
        passcode=payload.passcode,
        custom_price_paise=payload.custom_price_paise,
        discount_percent=payload.discount_percent,
        is_tatkal=payload.is_tatkal,
        max_uses=payload.max_uses,
        expires_in_hours=payload.expires_in_hours,
        notes=payload.notes,
    )
    return ApiResponse(
        message="Private invitation link created.",
        data=PrivateInviteLinkOut(
            id=str(link.id),
            astrologer_id=str(link.astrologer_id),
            invite_code=link.invite_code,
            title=link.title,
            client_name=link.client_name,
            client_email=link.client_email,
            has_passcode=link.has_passcode,
            custom_price_paise=link.custom_price_paise,
            discount_percent=link.discount_percent,
            is_tatkal=link.is_tatkal,
            max_uses=link.max_uses,
            uses_count=link.uses_count,
            expires_at=link.expires_at,
            is_active=link.is_active,
            created_at=link.created_at,
            notes=link.notes,
        ),
    )


@router.get(
    "/me/private-links",
    response_model=ApiResponse[list[PrivateInviteLinkOut]],
    summary="List all my private invite-only booking links",
)
async def get_my_private_links(
    profile: CurrentAstrologer,
) -> ApiResponse[list[PrivateInviteLinkOut]]:
    links = await service.list_private_invite_links(profile.id)
    return ApiResponse(
        message="Private links fetched.",
        data=[
            PrivateInviteLinkOut(
                id=str(link.id),
                astrologer_id=str(link.astrologer_id),
                invite_code=link.invite_code,
                title=link.title,
                client_name=link.client_name,
                client_email=link.client_email,
                has_passcode=link.has_passcode,
                custom_price_paise=link.custom_price_paise,
                discount_percent=link.discount_percent,
                is_tatkal=link.is_tatkal,
                max_uses=link.max_uses,
                uses_count=link.uses_count,
                expires_at=link.expires_at,
                is_active=link.is_active,
                created_at=link.created_at,
                notes=link.notes,
            )
            for link in links
        ],
    )


@router.delete(
    "/me/private-links/{link_id}",
    response_model=MessageResponse,
    summary="Deactivate a private invite link",
)
async def delete_private_link(
    link_id: PydanticObjectId,
    profile: CurrentAstrologer,
) -> MessageResponse:
    await service.deactivate_private_invite_link(link_id, profile.id)
    return MessageResponse(message="Private invite link deactivated.")


@router.get(
    "/private-links/{invite_code}/validate",
    response_model=ApiResponse[ValidatePrivateInviteResponse],
    summary="Validate an invite code and retrieve its consultation details",
)
async def validate_invite_link(
    invite_code: str,
) -> ApiResponse[ValidatePrivateInviteResponse]:
    data = await service.validate_private_invite_link(invite_code)
    return ApiResponse(
        message="Invitation link verified.",
        data=ValidatePrivateInviteResponse(**data),
    )


@router.post(
    "/private-links/{invite_code}/verify-passcode",
    response_model=MessageResponse,
    summary="Verify passcode for private invitation link",
)
async def verify_invite_passcode(
    invite_code: str,
    payload: VerifyPasscodeRequest,
) -> MessageResponse:
    await service.verify_private_invite_passcode(invite_code, payload.passcode)
    return MessageResponse(message="Passcode verified successfully.")


@router.post(
    "/me/tatkal-window",
    response_model=ApiResponse[WindowOut],
    status_code=status.HTTP_201_CREATED,
    summary="1-Click quick open an emergency VIP / Tatkal slot",
)
async def open_tatkal_window(
    payload: QuickTatkalWindowRequest,
    profile: CurrentAstrologer,
) -> ApiResponse[WindowOut]:
    window = await service.open_quick_tatkal_window(
        astrologer=profile,
        starts_at=payload.starts_at,
        minutes=payload.minutes,
        multiplier=payload.multiplier,
        fixed_paise=payload.fixed_paise,
        custom_title=payload.custom_title,
        is_private=payload.is_private,
    )
    return ApiResponse(
        message="Emergency VIP Tatkal slot opened successfully.",
        data=WindowOut(
            id=str(window.id),
            day=window.day,
            starts_at=window.starts_at,
            ends_at=window.ends_at,
            is_tatkal=window.is_tatkal,
            tatkal_multiplier=window.tatkal_multiplier,
            tatkal_fixed_paise=window.tatkal_fixed_paise,
            custom_title=window.custom_title,
            is_private=window.is_private,
        ),
    )




