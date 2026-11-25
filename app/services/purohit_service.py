"""Purohit service: onboarding, puja catalog management, and live puja booking orchestrator."""

import asyncio
import hashlib
import hmac
import secrets
import string
import uuid
from datetime import UTC, datetime

from beanie import PydanticObjectId
from loguru import logger
from pymongo import ReturnDocument
from slugify import slugify

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
)
from app.core.security import hash_password


def generate_initial_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


from app.models.enums import (
    AuthProvider,
    PujaBookingStatus,
    PujaPaymentStatus,
    TransactionReason,
    UserRole,
)
from app.models.purohit import PujaBooking, Purohit, PurohitPujaItem
from app.models.user import User
from app.models.wallet import TransactionRef
from app.schemas.purohit import (
    PujaBookingCreate,
    PujaPaymentVerifyRequest,
    PurohitCreate,
    PurohitPujaItemCreate,
    PurohitPujaItemUpdate,
    PurohitUpdate,
)
from app.services import (
    email as email_service,
    firebase,
    payments,
    settings as settings_service,
    wallet as wallet_service,
    zego,
)


async def _unique_slug(display_name: str) -> str:
    base = slugify(display_name, max_length=120) or "purohit"
    candidate, suffix = base, 2
    while await Purohit.find_one(Purohit.slug == candidate) is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _get_starting_price(purohit: Purohit) -> float:
    active_prices = [p.price_inr for p in purohit.pujas if p.is_active]
    return min(active_prices) if active_prices else 0.0


# ---------------------------------------------------------------------------
# Admin: Create Purohit
# ---------------------------------------------------------------------------
async def create_purohit_by_admin(payload: PurohitCreate) -> tuple[User, Purohit, str, bool]:
    """Creates a Purohit account in Firebase + MongoDB and emails login credentials."""
    email = payload.email.lower().strip()

    if await User.find_one(User.email == email) is not None:
        raise ConflictError(
            "An account with this email already exists.",
            error_code="email_already_registered",
        )

    full_name = " ".join(
        part for part in (payload.first_name, payload.middle_name, payload.last_name) if part
    )
    display_name = payload.display_name or full_name
    password = generate_initial_password()

    firebase_uid: str | None = None
    if firebase.is_enabled():
        existing = await firebase.get_user_by_email(email)
        if existing is not None:
            await firebase.update_user(
                existing.uid,
                password=password,
                display_name=display_name,
                email_verified=True,
            )
            firebase_uid = existing.uid
        else:
            record = await firebase.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=True,
            )
            firebase_uid = record.uid

    user = User(
        email=email,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        phone=payload.phone,
        hashed_password=hash_password(password),
        firebase_uid=firebase_uid,
        auth_providers=[AuthProvider.PASSWORD],
        role=UserRole.PUROHIT,
        is_email_verified=True,
        must_change_password=True,
    )
    await user.insert()

    profile = Purohit(
        user_id=user.id,
        display_name=display_name,
        slug=await _unique_slug(display_name),
        title=payload.title,
        bio=payload.bio,
        avatar_url=payload.avatar_url,
        phone=payload.phone,
        email=email,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        pincode=payload.pincode,
        experience_years=payload.experience_years,
        languages=payload.languages or ["Bengali", "Sanskrit"],
        is_online=True,  # Initially online upon onboarding
        is_verified=True,
        pujas=[],
        rating=0.0,
        total_pujas_performed=0,
    )
    await profile.insert()

    email_sent = False
    try:
        email_sent = await email_service.send_purohit_welcome_email(
            to=email, name=display_name, password=password
        )
    except Exception as exc:
        logger.warning("Could not send welcome email to Purohit {}: {}", email, exc)

    logger.info("Purohit created successfully: {} ({})", display_name, email)
    return user, profile, password, email_sent


# ---------------------------------------------------------------------------
# Purohit Dashboard operations
# ---------------------------------------------------------------------------
async def get_purohit_by_user_id(user_id: PydanticObjectId) -> Purohit:
    profile = await Purohit.find_one(Purohit.user_id == user_id)
    if profile is None:
        raise NotFoundError("Purohit profile not found.", error_code="purohit_not_found")
    return profile


async def update_purohit_availability(
    purohit: Purohit,
    is_online: bool,
    available_days: list[str] | None = None,
    available_slots: list[str] | None = None,
    weekly_schedule: dict[str, list[str]] | None = None,
) -> Purohit:
    """Toggle online/offline presence and configure weekly auspicious slots for live puja availability."""
    purohit.is_online = is_online
    if available_days is not None:
        purohit.available_days = available_days
    if available_slots is not None:
        purohit.available_slots = available_slots
    if weekly_schedule is not None:
        purohit.weekly_schedule = weekly_schedule
    purohit.updated_at = datetime.now(UTC)
    await purohit.save()
    logger.info(
        "Purohit {} availability updated: is_online={}, days={}, slots={}",
        purohit.display_name,
        is_online,
        len(purohit.available_days or []),
        len(purohit.available_slots or []),
    )
    return purohit


async def add_puja_to_catalog(purohit: Purohit, payload: PurohitPujaItemCreate) -> PurohitPujaItem:
    """Adds a new puja with custom pricing to the Purohit's personal price catalog."""
    new_item = PurohitPujaItem(
        id=uuid.uuid4().hex[:12],
        puja_name=payload.puja_name.strip(),
        description=payload.description.strip(),
        duration_minutes=payload.duration_minutes,
        price_inr=payload.price_inr,
        samagri_notes=payload.samagri_notes.strip() if payload.samagri_notes else None,
        is_active=payload.is_active,
    )
    purohit.pujas.append(new_item)
    purohit.updated_at = datetime.now(UTC)
    await purohit.save()
    return new_item


async def update_puja_in_catalog(
    purohit: Purohit, puja_id: str, payload: PurohitPujaItemUpdate
) -> PurohitPujaItem:
    """Edits price, duration, or notes of an existing puja."""
    target_item = None
    for item in purohit.pujas:
        if item.id == puja_id:
            target_item = item
            break

    if target_item is None:
        raise NotFoundError("Puja item not found in catalog.", error_code="puja_not_found")

    if payload.puja_name is not None:
        target_item.puja_name = payload.puja_name.strip()
    if payload.description is not None:
        target_item.description = payload.description.strip()
    if payload.duration_minutes is not None:
        target_item.duration_minutes = payload.duration_minutes
    if payload.price_inr is not None:
        target_item.price_inr = payload.price_inr
    if payload.samagri_notes is not None:
        target_item.samagri_notes = payload.samagri_notes.strip() if payload.samagri_notes else None
    if payload.is_active is not None:
        target_item.is_active = payload.is_active

    purohit.updated_at = datetime.now(UTC)
    await purohit.save()
    return target_item


async def delete_puja_from_catalog(purohit: Purohit, puja_id: str) -> bool:
    """Removes a puja from catalog."""
    initial_len = len(purohit.pujas)
    purohit.pujas = [p for p in purohit.pujas if p.id != puja_id]
    if len(purohit.pujas) == initial_len:
        raise NotFoundError("Puja item not found in catalog.", error_code="puja_not_found")
    purohit.updated_at = datetime.now(UTC)
    await purohit.save()
    return True


# ---------------------------------------------------------------------------
# Public Directory & Search
# ---------------------------------------------------------------------------
async def list_purohits(
    *,
    is_online_only: bool = False,
    search_puja: str | None = None,
    language: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Find available purohits with optional search by specific puja name."""
    from app.core.security import safe_regex_pattern

    query: dict = {"is_verified": True}
    if is_online_only:
        query["is_online"] = True
    if language:
        query["languages"] = language

    if search_puja and search_puja.strip():
        pat = safe_regex_pattern(search_puja)
        query["pujas"] = {
            "$elemMatch": {
                "is_active": True,
                "$or": [{"puja_name": pat}, {"description": pat}],
            }
        }

    cap_limit = min(max(1, limit), 100)
    safe_offset = max(0, offset)
    cursor = Purohit.find(query)
    total = await cursor.count()
    purohits = (
        await cursor.sort("-is_online", "-rating")
        .skip(safe_offset)
        .limit(cap_limit)
        .to_list()
    )

    results = []
    for p in purohits:
        p_dict = p.model_dump()
        p_dict["id"] = str(p.id)
        p_dict["user_id"] = str(p.user_id)
        p_dict["starting_price_inr"] = _get_starting_price(p)
        results.append(p_dict)

    return results, total


async def get_purohit_by_id_or_slug(identifier: str) -> dict:
    profile = None
    if PydanticObjectId.is_valid(identifier):
        profile = await Purohit.get(PydanticObjectId(identifier))
    if profile is None:
        profile = await Purohit.find_one(Purohit.slug == identifier)
    if profile is None:
        raise NotFoundError("Purohit not found.", error_code="purohit_not_found")

    p_dict = profile.model_dump()
    p_dict["id"] = str(profile.id)
    p_dict["user_id"] = str(profile.user_id)
    p_dict["starting_price_inr"] = _get_starting_price(profile)
    return p_dict


# ---------------------------------------------------------------------------
# Puja Booking & Live Video Room
# ---------------------------------------------------------------------------
async def book_puja(user: User, payload: PujaBookingCreate) -> tuple[PujaBooking, str | None]:
    """Initiates a live puja booking with verified wallet debit or pending Razorpay checkout."""
    purohit_oid = PydanticObjectId(payload.purohit_id)
    purohit = await Purohit.get(purohit_oid)
    if purohit is None:
        raise NotFoundError("Purohit not found.", error_code="purohit_not_found")

    target_puja = None
    for p in purohit.pujas:
        if p.id == payload.puja_item_id and p.is_active:
            target_puja = p
            break

    if target_puja is None:
        raise BadRequestError("This puja offering is currently unavailable.", error_code="puja_unavailable")

    booking_number = f"PUJA-{datetime.now(UTC).strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    room_id = f"puja_room_{secrets.token_hex(10)}"
    user_full_name = f"{user.first_name} {user.last_name or ''}".strip() or "Devotee"
    amount_paise = max(100, int(round(target_puja.price_inr * 100)))

    razorpay_order_id: str | None = None
    user_token: str | None = None
    booking_status = PujaBookingStatus.PENDING
    payment_status = PujaPaymentStatus.PENDING
    started_at: datetime | None = None

    if payload.payment_method == "wallet":
        platform = await settings_service.get_settings()
        coins_required = max(1, int(round(target_puja.price_inr * platform.coins_per_rupee)))
        await wallet_service.debit(
            user_id=user.id,
            amount_coins=coins_required,
            reason=TransactionReason.FEATURE_USAGE,
            idempotency_key=f"puja_booking:{booking_number}",
            ref=TransactionRef(),
            note=f"Live Puja: {target_puja.puja_name} (#{booking_number})",
            amount_paise=amount_paise,
            coins_per_rupee=platform.coins_per_rupee,
        )
        booking_status = PujaBookingStatus.CONFIRMED
        payment_status = PujaPaymentStatus.PAID
        started_at = datetime.now(UTC)
        user_token = zego.generate_token(user_id=str(user.id), room_id=room_id)
    else:
        rzp = payments._razorpay()
        try:
            created_order = await asyncio.to_thread(
                rzp.order.create,
                {
                    "amount": amount_paise,
                    "currency": settings.WALLET_CURRENCY,
                    "receipt": booking_number,
                    "notes": {
                        "purpose": "puja_booking",
                        "booking_number": booking_number,
                        "user_id": str(user.id),
                    },
                },
            )
            razorpay_order_id = created_order["id"]
        except Exception as exc:  # noqa: BLE001
            logger.opt(exception=exc).error("Razorpay order creation failed for puja {}", booking_number)
            raise ServiceUnavailableError(
                "Could not initiate payment for this puja booking. Please try again.",
                error_code="payment_order_failed",
            ) from exc

    booking = PujaBooking(
        booking_number=booking_number,
        user_id=user.id,
        user_name=user_full_name,
        user_phone=user.phone or "",
        user_email=user.email,
        purohit_id=purohit.id,
        purohit_user_id=purohit.user_id,
        purohit_name=purohit.display_name,
        puja_item_id=target_puja.id,
        puja_name=target_puja.puja_name,
        puja_duration_minutes=target_puja.duration_minutes,
        amount_inr=target_puja.price_inr,
        sankalpa_name=payload.sankalpa_name.strip(),
        sankalpa_gotra=payload.sankalpa_gotra.strip() or "Kashyapa",
        sankalpa_nakshatra=payload.sankalpa_nakshatra.strip() if payload.sankalpa_nakshatra else None,
        sankalpa_wish=payload.sankalpa_wish.strip() if payload.sankalpa_wish else None,
        room_id=room_id,
        status=booking_status,
        payment_status=payment_status,
        payment_method=payload.payment_method,
        razorpay_order_id=razorpay_order_id,
        started_at=started_at,
    )
    await booking.insert()

    if payment_status == PujaPaymentStatus.PAID:
        await Purohit.get_pymongo_collection().update_one(
            {"_id": purohit.id},
            {"$inc": {"total_pujas_performed": 1}},
        )

    logger.info(
        "Puja booking initiated: #{} status={} payment={} via {} by {}",
        booking_number,
        booking_status.value,
        payment_status.value,
        payload.payment_method,
        user.email,
    )
    return booking, user_token


async def verify_puja_payment(
    booking_id: str,
    user: User,
    payload: PujaPaymentVerifyRequest,
) -> tuple[PujaBooking, str]:
    """Verifies Razorpay HMAC signature and marks a pending puja booking CONFIRMED + PAID."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    if booking.user_id != user.id and user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise ForbiddenError("You are not authorized to verify payment for this booking.", error_code="access_denied")

    if booking.payment_status == PujaPaymentStatus.PAID:
        return booking, zego.generate_token(user_id=str(user.id), room_id=booking.room_id)

    if not settings.razorpay_configured:
        raise ServiceUnavailableError("Payments are not configured.", error_code="payments_unavailable")

    if not booking.razorpay_order_id or booking.razorpay_order_id != payload.razorpay_order_id:
        raise BadRequestError("Razorpay order ID mismatch.", error_code="order_mismatch")

    msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode()
    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        raise BadRequestError("Payment signature verification failed.", error_code="invalid_signature")

    now = datetime.now(UTC)
    raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
        {"_id": booking.id, "payment_status": {"$ne": PujaPaymentStatus.PAID}},
        {
            "$set": {
                "status": PujaBookingStatus.CONFIRMED,
                "payment_status": PujaPaymentStatus.PAID,
                "razorpay_payment_id": payload.razorpay_payment_id,
                "started_at": now,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if raw is not None:
        await Purohit.get_pymongo_collection().update_one(
            {"_id": booking.purohit_id},
            {"$inc": {"total_pujas_performed": 1}},
        )

    refreshed = await PujaBooking.get(booking.id)
    assert refreshed is not None
    token = zego.generate_token(user_id=str(user.id), room_id=refreshed.room_id)
    logger.info("Puja booking #{} payment verified -> CONFIRMED/PAID", refreshed.booking_number)
    return refreshed, token


async def get_booking_token(booking_id: str, current_user: User) -> tuple[PujaBooking, str]:
    """Generates a fresh ZEGOCLOUD token for either the devotee or the assigned Purohit."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    # Authorize: Must be the devotee or the Purohit or an admin
    is_devotee = booking.user_id == current_user.id
    is_purohit = booking.purohit_user_id == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    if not (is_devotee or is_purohit or is_admin):
        raise ForbiddenError("You are not authorized to enter this sacred puja room.", error_code="access_denied")

    if booking.payment_status != PujaPaymentStatus.PAID or booking.status == PujaBookingStatus.CANCELLED:
        raise ForbiddenError(
            "Complete payment before entering the live puja room.",
            error_code="payment_required",
        )

    token = zego.generate_token(user_id=str(current_user.id), room_id=booking.room_id)
    return booking, token


async def get_booking(booking_id: str, current_user: User) -> PujaBooking:
    """Fetches a single PujaBooking, authorizing only the devotee, assigned Purohit, or admin."""
    booking: PujaBooking | None = None
    try:
        b_oid = PydanticObjectId(booking_id)
        booking = await PujaBooking.get(b_oid)
    except Exception:
        pass

    if booking is None:
        booking = await PujaBooking.find_one(PujaBooking.booking_number == booking_id)

    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    is_devotee = booking.user_id == current_user.id
    is_purohit = booking.purohit_user_id == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    if not (is_devotee or is_purohit or is_admin):
        raise ForbiddenError("You are not authorized to view this booking.", error_code="access_denied")

    return booking


async def list_purohit_bookings(
    purohit_user_id: PydanticObjectId, limit: int = 100, offset: int = 0
) -> list[PujaBooking]:
    """Lists bookings for the logged-in Purohit's dashboard."""
    cap = min(max(1, limit), 100)
    return (
        await PujaBooking.find(PujaBooking.purohit_user_id == purohit_user_id)
        .sort("-created_at")
        .skip(max(0, offset))
        .limit(cap)
        .to_list()
    )


async def list_user_bookings(
    user_id: PydanticObjectId, limit: int = 100, offset: int = 0
) -> list[PujaBooking]:
    """Lists bookings for the devotee."""
    cap = min(max(1, limit), 100)
    return (
        await PujaBooking.find(PujaBooking.user_id == user_id)
        .sort("-created_at")
        .skip(max(0, offset))
        .limit(cap)
        .to_list()
    )


async def complete_puja_session(booking_id: str, current_user: User) -> PujaBooking:
    """Marks a live puja session as completed."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    if booking.purohit_user_id != current_user.id and current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise ForbiddenError("Only the presiding Purohit or Admin can complete this session.")

    booking.status = PujaBookingStatus.COMPLETED
    booking.completed_at = datetime.now(UTC)
    await booking.save()
    logger.info("Puja booking #{} marked COMPLETED", booking.booking_number)
    return booking
