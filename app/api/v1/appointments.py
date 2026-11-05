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
)
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
    PrescriptionUpdateRequest,
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
    can_cancel = (not is_client) or (
        appointment.status == AppointmentStatus.BOOKED and now <= deadline
    )

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

