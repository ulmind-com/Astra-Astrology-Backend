"""Purohit service: onboarding, puja catalog management, and live puja booking orchestrator."""

import asyncio
import hashlib
import hmac
import secrets
import string
import uuid
from datetime import UTC, datetime, timedelta

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
from app.models.wallet import TransactionRef, WalletTransaction
from app.schemas.purohit import (
    PujaBookingCreate,
    PujaPaymentVerifyRequest,
    PurohitCreate,
    PurohitPujaItemCreate,
    PurohitPujaItemUpdate,
)
from app.services import (
    email as email_service,
)
from app.services import (
    firebase,
    payments,
    purohit_presence,
    realtime,
    zego,
)
from app.services import (
    settings as settings_service,
)
from app.services import (
    wallet as wallet_service,
)

PUJA_REQUEST_ACCEPT_TIMEOUT_SECONDS = 120


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def serialize_purohit(purohit: Purohit) -> dict:
    """Serialize Purohit with live TTL-evaluated `is_online` and `is_busy` fields."""
    p_dict = purohit.model_dump()
    p_dict["id"] = str(purohit.id)
    p_dict["user_id"] = str(purohit.user_id)
    p_dict["is_online"] = purohit_presence.is_effectively_online(purohit)
    p_dict["is_busy"] = bool(getattr(purohit, "is_busy", False))
    busy_bid = getattr(purohit, "busy_booking_id", None)
    p_dict["busy_booking_id"] = str(busy_bid) if busy_bid else None
    p_dict["starting_price_inr"] = _get_starting_price(purohit)
    return p_dict


def serialize_booking_event(booking: PujaBooking) -> dict:
    """Serialize PujaBooking into JSON-safe dict for real-time WebSocket broadcasts."""
    return {
        "id": str(booking.id),
        "booking_number": booking.booking_number,
        "user_id": str(booking.user_id),
        "user_name": booking.user_name,
        "user_phone": booking.user_phone,
        "purohit_id": str(booking.purohit_id),
        "purohit_name": booking.purohit_name,
        "puja_item_id": booking.puja_item_id,
        "puja_name": booking.puja_name,
        "puja_duration_minutes": booking.puja_duration_minutes,
        "amount_inr": booking.amount_inr,
        "sankalpa_name": booking.sankalpa_name,
        "sankalpa_gotra": booking.sankalpa_gotra,
        "sankalpa_nakshatra": booking.sankalpa_nakshatra,
        "sankalpa_wish": booking.sankalpa_wish,
        "room_id": booking.room_id,
        "status": booking.status.value if hasattr(booking.status, "value") else str(booking.status),
        "payment_status": (
            booking.payment_status.value
            if hasattr(booking.payment_status, "value")
            else str(booking.payment_status)
        ),
        "started_at": booking.started_at.isoformat() if booking.started_at else None,
        "accepted_at": booking.accepted_at.isoformat() if getattr(booking, "accepted_at", None) else None,
        "expires_at": booking.expires_at.isoformat() if getattr(booking, "expires_at", None) else None,
        "completed_at": booking.completed_at.isoformat() if booking.completed_at else None,
        "declined_at": booking.declined_at.isoformat() if getattr(booking, "declined_at", None) else None,
        "cancel_reason": getattr(booking, "cancel_reason", None),
        "refund_id": getattr(booking, "refund_id", None),
        "refunded_at": booking.refunded_at.isoformat() if getattr(booking, "refunded_at", None) else None,
        "created_at": booking.created_at.isoformat() if booking.created_at else None,
    }


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
    """Toggle online/offline presence for live on-demand pujas."""
    now = _utcnow()
    purohit.is_online = is_online
    if is_online:
        purohit.last_seen_at = now
        if purohit.last_online_at is None:
            purohit.last_online_at = now
    else:
        purohit.last_seen_at = None

    if available_days is not None:
        purohit.available_days = available_days
    if available_slots is not None:
        purohit.available_slots = available_slots
    if weekly_schedule is not None:
        purohit.weekly_schedule = weekly_schedule
    purohit.updated_at = now
    await Purohit.get_pymongo_collection().update_one(
        {"_id": purohit.id},
        {
            "$set": {
                "is_online": purohit.is_online,
                "last_seen_at": purohit.last_seen_at,
                "last_online_at": purohit.last_online_at,
                "available_days": purohit.available_days,
                "available_slots": purohit.available_slots,
                "weekly_schedule": purohit.weekly_schedule,
                "updated_at": now,
            }
        },
    )
    logger.info("Purohit {} availability updated: is_online={}", purohit.display_name, is_online)
    await realtime.publish_purohit(purohit)
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
    purohit.updated_at = _utcnow()
    await purohit.save()
    await realtime.publish_purohit(purohit)
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

    purohit.updated_at = _utcnow()
    await purohit.save()
    await realtime.publish_purohit(purohit)
    return target_item


async def delete_puja_from_catalog(purohit: Purohit, puja_id: str) -> bool:
    """Removes a puja from catalog."""
    initial_len = len(purohit.pujas)
    purohit.pujas = [p for p in purohit.pujas if p.id != puja_id]
    if len(purohit.pujas) == initial_len:
        raise NotFoundError("Puja item not found in catalog.", error_code="puja_not_found")
    purohit.updated_at = _utcnow()
    await purohit.save()
    await realtime.publish_purohit(purohit)
    return True


# ---------------------------------------------------------------------------
# Public Directory & Search
# ---------------------------------------------------------------------------
async def list_purohits(
    *,
    is_online_only: bool = True,
    exclude_busy: bool = True,
    search_puja: str | None = None,
    language: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Find live available purohits with optional search by specific puja name."""
    from app.core.security import safe_regex_pattern

    query: dict = {"is_verified": True}
    if is_online_only:
        query["is_online"] = True
        query["last_seen_at"] = {"$gte": purohit_presence.stale_before()}
    if exclude_busy:
        query["is_busy"] = {"$ne": True}
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
        await cursor.sort("-is_online", "-rating", "-total_pujas_performed")
        .skip(safe_offset)
        .limit(cap_limit)
        .to_list()
    )

    return [serialize_purohit(p) for p in purohits], total


async def get_purohit_by_id_or_slug(identifier: str) -> dict:
    profile = None
    if PydanticObjectId.is_valid(identifier):
        profile = await Purohit.get(PydanticObjectId(identifier))
    if profile is None:
        profile = await Purohit.find_one(Purohit.slug == identifier)
    if profile is None:
        raise NotFoundError("Purohit not found.", error_code="purohit_not_found")

    return serialize_purohit(profile)


# ---------------------------------------------------------------------------
# Puja Booking, Atomic Busy Lock & Live Video Room
# ---------------------------------------------------------------------------
async def _acquire_purohit_busy_lock(
    purohit_id: PydanticObjectId,
    booking_id: PydanticObjectId,
    now: datetime,
) -> dict | None:
    """Atomically reserve an online, non-busy, verified Purohit for one live puja."""
    return await Purohit.get_pymongo_collection().find_one_and_update(
        {
            "_id": purohit_id,
            "is_verified": True,
            "is_online": True,
            "last_seen_at": {"$gte": purohit_presence.stale_before()},
            "is_busy": {"$ne": True},
        },
        {
            "$set": {
                "is_busy": True,
                "busy_booking_id": booking_id,
                "busy_since": now,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )


async def _release_purohit_busy_lock(
    purohit_id: PydanticObjectId,
    booking_id: PydanticObjectId | None = None,
    *,
    increment_performed: bool = False,
) -> Purohit | None:
    """Release a Purohit from busy state so they reappear in live search if still online."""
    now = _utcnow()
    filt: dict = {"_id": purohit_id}
    if booking_id is not None:
        filt["busy_booking_id"] = booking_id

    update: dict = {
        "$set": {
            "is_busy": False,
            "busy_booking_id": None,
            "busy_since": None,
            "updated_at": now,
        }
    }
    if increment_performed:
        update["$inc"] = {"total_pujas_performed": 1}

    raw = await Purohit.get_pymongo_collection().find_one_and_update(
        filt,
        update,
        return_document=ReturnDocument.AFTER,
    )
    if raw is None and increment_performed:
        await Purohit.get_pymongo_collection().update_one(
            {"_id": purohit_id},
            {"$inc": {"total_pujas_performed": 1}, "$set": {"updated_at": now}},
        )
    refreshed = await Purohit.get(purohit_id)
    if refreshed is not None:
        await realtime.publish_purohit(refreshed)
    return refreshed


async def _refund_booking(booking: PujaBooking, *, reason: str) -> PujaBooking:
    """Idempotently refund a paid live puja booking via original payment method (or wallet fallback)."""
    if booking.payment_status == PujaPaymentStatus.REFUNDED:
        return booking
    if booking.payment_status != PujaPaymentStatus.PAID:
        return booking

    now = _utcnow()
    refund_id: str | None = None

    if booking.payment_method == "wallet":
        txn = await WalletTransaction.find_one(
            WalletTransaction.idempotency_key == f"puja_booking:{booking.booking_number}"
        )
        if txn is not None and txn.amount_coins > 0:
            coins_to_refund = txn.amount_coins
        else:
            platform = await settings_service.get_settings()
            coins_to_refund = max(1, int(round(booking.amount_inr * platform.coins_per_rupee)))

        await wallet_service.credit(
            user_id=booking.user_id,
            amount_coins=coins_to_refund,
            reason=TransactionReason.REFUND,
            idempotency_key=f"puja_refund:{booking.booking_number}",
            note=f"100% Refund for Live Puja #{booking.booking_number}: {reason}",
        )
        refund_id = f"wallet_refund:{booking.booking_number}"
    else:
        credited_via_rzp = False
        if booking.razorpay_payment_id and payments.is_enabled():
            amount_paise = max(100, int(round(booking.amount_inr * 100)))
            try:
                res = await asyncio.to_thread(
                    payments._razorpay().payment.refund,
                    booking.razorpay_payment_id,
                    {
                        "amount": amount_paise,
                        "notes": {
                            "booking_number": booking.booking_number,
                            "reason": reason[:200],
                        },
                    },
                )
                refund_id = str(res.get("id") or f"rzp_refund:{booking.razorpay_payment_id}")
                credited_via_rzp = True
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Razorpay refund failed for puja #{}, crediting wallet fallback: {}",
                    booking.booking_number,
                    exc,
                )

        if not credited_via_rzp:
            platform = await settings_service.get_settings()
            coins_to_refund = max(1, int(round(booking.amount_inr * platform.coins_per_rupee)))
            await wallet_service.credit(
                user_id=booking.user_id,
                amount_coins=coins_to_refund,
                reason=TransactionReason.REFUND,
                idempotency_key=f"puja_refund:{booking.booking_number}",
                note=f"100% Refund to wallet for Live Puja #{booking.booking_number}: {reason}",
            )
            refund_id = f"wallet_fallback:{booking.booking_number}"

    await PujaBooking.get_pymongo_collection().update_one(
        {"_id": booking.id},
        {
            "$set": {
                "payment_status": PujaPaymentStatus.REFUNDED,
                "cancel_reason": reason,
                "refund_id": refund_id,
                "refunded_at": now,
                "updated_at": now,
            }
        },
    )
    refreshed = await PujaBooking.get(booking.id)
    logger.info("Refunded Puja booking #{} -> refund_id={}", booking.booking_number, refund_id)
    return refreshed or booking


async def _finalize_puja_session(
    booking: PujaBooking,
    *,
    status: PujaBookingStatus = PujaBookingStatus.COMPLETED,
    reason: str | None = None,
) -> PujaBooking:
    """Atomically end an active/confirmed puja session, release busy lock, and broadcast."""
    now = _utcnow()
    update_fields: dict = {
        "status": status,
        "completed_at": now,
        "updated_at": now,
    }
    if reason:
        update_fields["cancel_reason"] = reason

    raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
        {
            "_id": booking.id,
            "status": {"$in": [PujaBookingStatus.CONFIRMED, PujaBookingStatus.IN_PROGRESS]},
        },
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )
    refreshed = await PujaBooking.get(booking.id)
    target = refreshed or booking

    if raw is not None:
        await _release_purohit_busy_lock(
            booking.purohit_id,
            booking.id,
            increment_performed=(status == PujaBookingStatus.COMPLETED),
        )
        await realtime.publish_puja_event(
            target.user_id,
            target.purohit_user_id,
            "puja_ended",
            serialize_booking_event(target),
        )
    else:
        # Ensure busy lock is not orphaned if already completed elsewhere
        await _release_purohit_busy_lock(booking.purohit_id, booking.id)

    return target


async def book_puja(user: User, payload: PujaBookingCreate) -> tuple[PujaBooking, str | None]:
    """Initiates a live puja booking against an online, non-busy Purohit."""
    purohit_oid = PydanticObjectId(payload.purohit_id)
    purohit = await Purohit.get(purohit_oid)
    if purohit is None:
        raise NotFoundError("Purohit not found.", error_code="purohit_not_found")
    if not purohit.is_verified:
        raise BadRequestError("This Purohit is not currently verified.", error_code="purohit_unverified")
    if purohit.user_id == user.id:
        raise BadRequestError("You cannot book a puja with your own account.", error_code="self_booking_forbidden")
    if not purohit_presence.is_effectively_online(purohit):
        raise BadRequestError("This Purohit is currently offline. Please choose an online Purohit.", error_code="purohit_offline")
    if bool(getattr(purohit, "is_busy", False)):
        raise ConflictError(
            "This Purohit is currently performing another live puja. Please choose another available Purohit.",
            error_code="purohit_busy",
        )

    target_puja = None
    for p in purohit.pujas:
        if p.id == payload.puja_item_id and p.is_active:
            target_puja = p
            break

    if target_puja is None:
        raise BadRequestError("This puja offering is currently unavailable.", error_code="puja_unavailable")

    now = _utcnow()
    booking_id = PydanticObjectId()
    booking_number = f"PUJA-{now.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    room_id = f"puja_room_{secrets.token_hex(10)}"
    user_full_name = f"{user.first_name} {user.last_name or ''}".strip() or "Devotee"
    amount_paise = max(100, int(round(target_puja.price_inr * 100)))

    razorpay_order_id: str | None = None
    user_token: str | None = None
    booking_status = PujaBookingStatus.PENDING
    payment_status = PujaPaymentStatus.PENDING
    started_at: datetime | None = None
    locked_purohit = False

    if payload.payment_method == "wallet":
        claimed = await _acquire_purohit_busy_lock(purohit.id, booking_id, now)
        if claimed is None:
            raise ConflictError(
                "This Purohit just accepted another devotee's puja. Please select another online Purohit.",
                error_code="purohit_busy",
            )
        locked_purohit = True
        try:
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
        except Exception:
            await _release_purohit_busy_lock(purohit.id, booking_id)
            raise

        booking_status = PujaBookingStatus.CONFIRMED
        payment_status = PujaPaymentStatus.PAID
        started_at = now
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
        id=booking_id,
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

    if locked_purohit and payment_status == PujaPaymentStatus.PAID:
        updated_purohit = await Purohit.get(purohit.id)
        if updated_purohit is not None:
            await realtime.publish_purohit(updated_purohit)
        await realtime.publish_puja_event(
            booking.user_id,
            booking.purohit_user_id,
            "puja_request",
            serialize_booking_event(booking),
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
    """Verifies Razorpay HMAC signature, atomically locks the Purohit, or auto-refunds if busy/offline."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    if booking.user_id != user.id and user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise ForbiddenError("You are not authorized to verify payment for this booking.", error_code="access_denied")

    if booking.payment_status == PujaPaymentStatus.PAID:
        token = (
            zego.generate_token(user_id=str(user.id), room_id=booking.room_id)
            if booking.status in (PujaBookingStatus.CONFIRMED, PujaBookingStatus.IN_PROGRESS)
            else ""
        )
        return booking, token

    if booking.payment_status == PujaPaymentStatus.REFUNDED:
        return booking, ""

    if not settings.razorpay_configured:
        raise ServiceUnavailableError("Payments are not configured.", error_code="payments_unavailable")

    if not booking.razorpay_order_id or booking.razorpay_order_id != payload.razorpay_order_id:
        raise BadRequestError("Razorpay order ID mismatch.", error_code="order_mismatch")

    msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode()
    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        raise BadRequestError("Payment signature verification failed.", error_code="invalid_signature")

    now = _utcnow()
    raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
        {"_id": booking.id, "payment_status": {"$nin": [PujaPaymentStatus.PAID, PujaPaymentStatus.REFUNDED]}},
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
    refreshed = await PujaBooking.get(booking.id)
    assert refreshed is not None

    if raw is not None:
        claimed = await _acquire_purohit_busy_lock(refreshed.purohit_id, refreshed.id, now)
        if claimed is None:
            # Purohit was booked by someone else or went offline during checkout — refund 100% automatically.
            await PujaBooking.get_pymongo_collection().update_one(
                {"_id": refreshed.id},
                {"$set": {"status": PujaBookingStatus.CANCELLED, "updated_at": _utcnow()}},
            )
            refunded = await _refund_booking(
                refreshed,
                reason="Purohit became busy or offline before payment finished — 100% refund initiated.",
            )
            return refunded, ""

        updated_purohit = await Purohit.get(refreshed.purohit_id)
        if updated_purohit is not None:
            await realtime.publish_purohit(updated_purohit)
        await realtime.publish_puja_event(
            refreshed.user_id,
            refreshed.purohit_user_id,
            "puja_request",
            serialize_booking_event(refreshed),
        )

    token = zego.generate_token(user_id=str(user.id), room_id=refreshed.room_id)
    logger.info("Puja booking #{} payment verified -> CONFIRMED/PAID (Purohit locked)", refreshed.booking_number)
    return refreshed, token


async def accept_puja_booking(booking_id: str, current_user: User) -> tuple[PujaBooking, str]:
    """Presiding Purohit accepts an incoming live puja request and starts the exact countdown clock."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    is_purohit = booking.purohit_user_id == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not (is_purohit or is_admin):
        raise ForbiddenError("Only the assigned Purohit can accept this puja request.", error_code="access_denied")

    if booking.payment_status != PujaPaymentStatus.PAID:
        raise BadRequestError("Payment is not active for this booking.", error_code="payment_not_paid")

    if booking.status == PujaBookingStatus.IN_PROGRESS:
        now = _utcnow()
        exp = _as_utc(booking.expires_at)
        if exp and exp <= now:
            await _finalize_puja_session(booking, status=PujaBookingStatus.COMPLETED, reason="Session duration completed")
            raise BadRequestError("This puja session has already expired.", error_code="puja_expired")
        token = zego.generate_token(user_id=str(current_user.id), room_id=booking.room_id)
        return booking, token

    if booking.status != PujaBookingStatus.CONFIRMED:
        raise BadRequestError(
            f"This booking is {booking.status.value} and cannot be accepted.",
            error_code="invalid_booking_state",
        )

    now = _utcnow()
    duration_mins = max(1, int(booking.puja_duration_minutes or 30))
    expires_at = now + timedelta(minutes=duration_mins)

    raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
        {
            "_id": booking.id,
            "status": PujaBookingStatus.CONFIRMED,
            "payment_status": PujaPaymentStatus.PAID,
        },
        {
            "$set": {
                "status": PujaBookingStatus.IN_PROGRESS,
                "accepted_at": now,
                "started_at": now,
                "expires_at": expires_at,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if raw is None:
        latest = await PujaBooking.get(booking.id)
        if latest and latest.status == PujaBookingStatus.IN_PROGRESS:
            return latest, zego.generate_token(user_id=str(current_user.id), room_id=latest.room_id)
        raise BadRequestError("This booking could not be accepted because its status changed.", error_code="invalid_booking_state")

    updated = await PujaBooking.get(booking.id)
    assert updated is not None

    # Ensure Purohit remains locked and marked online during live ritual
    await Purohit.get_pymongo_collection().update_one(
        {"_id": updated.purohit_id},
        {
            "$set": {
                "is_busy": True,
                "busy_booking_id": updated.id,
                "busy_since": updated.started_at or now,
                "last_seen_at": now,
                "updated_at": now,
            }
        },
    )
    updated_purohit = await Purohit.get(updated.purohit_id)
    if updated_purohit is not None:
        await realtime.publish_purohit(updated_purohit)

    await realtime.publish_puja_event(
        updated.user_id,
        updated.purohit_user_id,
        "puja_accepted",
        serialize_booking_event(updated),
    )

    token = zego.generate_token(user_id=str(current_user.id), room_id=updated.room_id)
    logger.info(
        "Puja booking #{} accepted by Purohit; room active for {}m until {}",
        updated.booking_number,
        duration_mins,
        expires_at.isoformat(),
    )
    return updated, token


async def decline_puja_booking(
    booking_id: str,
    current_user: User,
    reason: str | None = None,
) -> PujaBooking:
    """Purohit declines an incoming puja request -> unlocks Purohit and refunds devotee 100%."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    is_purohit = booking.purohit_user_id == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not (is_purohit or is_admin):
        raise ForbiddenError("Only the assigned Purohit can decline this request.", error_code="access_denied")

    if booking.status == PujaBookingStatus.DECLINED:
        return booking
    if booking.status != PujaBookingStatus.CONFIRMED:
        raise BadRequestError(
            f"Cannot decline a booking that is already {booking.status.value}.",
            error_code="invalid_booking_state",
        )

    now = _utcnow()
    decline_reason = (reason or "").strip() or "Purohit declined the request right now."
    raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
        {"_id": booking.id, "status": PujaBookingStatus.CONFIRMED},
        {
            "$set": {
                "status": PujaBookingStatus.DECLINED,
                "declined_at": now,
                "cancel_reason": decline_reason,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    await _release_purohit_busy_lock(booking.purohit_id, booking.id)

    latest = await PujaBooking.get(booking.id)
    target = latest or booking
    if raw is not None:
        target = await _refund_booking(target, reason=decline_reason)
        await realtime.publish_puja_event(
            target.user_id,
            target.purohit_user_id,
            "puja_declined",
            serialize_booking_event(target),
        )
    return target


async def get_booking_token(booking_id: str, current_user: User) -> tuple[PujaBooking, str]:
    """Generates a fresh ZEGOCLOUD token only while paid and within scheduled duration."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    is_devotee = booking.user_id == current_user.id
    is_purohit = booking.purohit_user_id == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    if not (is_devotee or is_purohit or is_admin):
        raise ForbiddenError("You are not authorized to enter this sacred puja room.", error_code="access_denied")

    if booking.status in (PujaBookingStatus.DECLINED, PujaBookingStatus.CANCELLED):
        raise ForbiddenError(
            getattr(booking, "cancel_reason", None) or "This puja booking was cancelled/declined and refunded.",
            error_code="puja_cancelled",
        )
    if booking.status in (PujaBookingStatus.COMPLETED, PujaBookingStatus.EXPIRED):
        raise ForbiddenError("This live puja session has completed.", error_code="puja_completed")
    if booking.payment_status != PujaPaymentStatus.PAID:
        raise ForbiddenError(
            "Complete payment before entering the live puja room.",
            error_code="payment_required",
        )

    now = _utcnow()
    exp = _as_utc(getattr(booking, "expires_at", None))
    if booking.status == PujaBookingStatus.IN_PROGRESS and exp and exp <= now:
        await _finalize_puja_session(
            booking,
            status=PujaBookingStatus.COMPLETED,
            reason="Puja session allocated duration ended",
        )
        raise ForbiddenError(
            "The allocated time for this puja session has ended.",
            error_code="puja_expired",
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


async def get_active_purohit_booking(purohit_user_id: PydanticObjectId) -> PujaBooking | None:
    """Returns currently waiting (CONFIRMED) or live (IN_PROGRESS) puja booking for the Purohit."""
    return await PujaBooking.find_one(
        PujaBooking.purohit_user_id == purohit_user_id,
        PujaBooking.payment_status == PujaPaymentStatus.PAID,
        {"status": {"$in": [PujaBookingStatus.IN_PROGRESS, PujaBookingStatus.CONFIRMED]}},
    )


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
    """Marks a live puja session as completed early and frees the Purohit immediately."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    if booking.purohit_user_id != current_user.id and current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise ForbiddenError("Only the presiding Purohit or Admin can complete this session.")

    if booking.status == PujaBookingStatus.COMPLETED:
        await _release_purohit_busy_lock(booking.purohit_id, booking.id)
        return booking

    completed = await _finalize_puja_session(booking, status=PujaBookingStatus.COMPLETED)
    logger.info("Puja booking #{} marked COMPLETED early", completed.booking_number)
    return completed


async def reconcile_live_puja_sessions() -> dict[str, int]:
    """Expire timed-out rooms, refund unanswered requests, clear orphaned busy locks, and sweep stale presence."""
    now = _utcnow()
    expired_count = 0
    timed_out_count = 0
    unlocked_orphans = 0

    # 1. End any IN_PROGRESS rooms whose puja duration has elapsed
    expired_bookings = await PujaBooking.find(
        {
            "status": PujaBookingStatus.IN_PROGRESS,
            "expires_at": {"$ne": None, "$lte": now},
        }
    ).to_list()
    for booking in expired_bookings:
        await _finalize_puja_session(
            booking,
            status=PujaBookingStatus.COMPLETED,
            reason="Scheduled puja duration completed",
        )
        expired_count += 1

    # 2. Auto-decline & 100% refund CONFIRMED requests unanswered past timeout window
    cutoff = now - timedelta(seconds=PUJA_REQUEST_ACCEPT_TIMEOUT_SECONDS)
    unanswered = await PujaBooking.find(
        {
            "status": PujaBookingStatus.CONFIRMED,
            "payment_status": PujaPaymentStatus.PAID,
            "started_at": {"$ne": None, "$lte": cutoff},
        }
    ).to_list()
    for booking in unanswered:
        raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
            {"_id": booking.id, "status": PujaBookingStatus.CONFIRMED},
            {
                "$set": {
                    "status": PujaBookingStatus.DECLINED,
                    "declined_at": now,
                    "cancel_reason": "Purohit did not join within 2 minutes — automatic 100% refund",
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        await _release_purohit_busy_lock(booking.purohit_id, booking.id)
        if raw is not None:
            latest = await PujaBooking.get(booking.id)
            if latest is not None:
                refunded = await _refund_booking(latest, reason=latest.cancel_reason or "Request timed out")
                await realtime.publish_puja_event(
                    refunded.user_id,
                    refunded.purohit_user_id,
                    "puja_declined",
                    serialize_booking_event(refunded),
                )
            timed_out_count += 1

    # 3. Release any orphaned busy locks pointing to finished bookings
    busy_purohits = await Purohit.find({"is_busy": True}).to_list()
    for p in busy_purohits:
        b = await PujaBooking.get(p.busy_booking_id) if p.busy_booking_id else None
        if b is None or b.status not in (PujaBookingStatus.CONFIRMED, PujaBookingStatus.IN_PROGRESS):
            await _release_purohit_busy_lock(p.id)
            unlocked_orphans += 1

    # 4. Sweep stale WebSocket presence
    presence_stats = await purohit_presence.sweep()

    return {
        "expired_rooms": expired_count,
        "timed_out_requests": timed_out_count,
        "unlocked_orphans": unlocked_orphans,
        **presence_stats,
    }


async def live_puja_worker_loop() -> None:
    """Background worker enforcing exact live puja room timers and Purohit presence TTL."""
    from pymongo.errors import PyMongoError

    logger.info("Live Purohit session timer & presence worker started.")
    while True:
        try:
            await asyncio.sleep(30)
            stats = await reconcile_live_puja_sessions()
            if any(stats.values()):
                logger.info("Live Purohit worker tick: {}", stats)
        except asyncio.CancelledError:
            logger.info("Live Purohit worker stopped gracefully.")
            break
        except (PyMongoError, TimeoutError, OSError) as db_err:
            logger.warning("MongoDB temporarily unavailable in live Purohit worker: {}", db_err)
            await asyncio.sleep(15)
        except Exception as exc:  # noqa: BLE001
            logger.opt(exception=exc).error("Unexpected error in live Purohit worker: {}", exc)
            await asyncio.sleep(15)
