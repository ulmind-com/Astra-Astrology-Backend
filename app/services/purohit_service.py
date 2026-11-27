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

PUJA_ACCEPT_SLA_SECONDS = 45
PUJA_PAYMENT_WINDOW_SECONDS = 90
PUJA_JOIN_SLA_SECONDS = 60
PUJA_REQUEST_ACCEPT_TIMEOUT_SECONDS = 120
PUJA_ABUSE_LOOKBACK_MINUTES = 30
PUJA_ABUSE_COOLDOWN_MINUTES = 15


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
        "purohit_user_id": str(booking.purohit_user_id),
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
        "payment_method": getattr(booking, "payment_method", "razorpay"),
        "started_at": booking.started_at.isoformat() if booking.started_at else None,
        "accepted_at": booking.accepted_at.isoformat() if getattr(booking, "accepted_at", None) else None,
        "accept_expires_at": (
            booking.accept_expires_at.isoformat() if getattr(booking, "accept_expires_at", None) else None
        ),
        "payment_expires_at": (
            booking.payment_expires_at.isoformat() if getattr(booking, "payment_expires_at", None) else None
        ),
        "purohit_join_deadline_at": (
            booking.purohit_join_deadline_at.isoformat()
            if getattr(booking, "purohit_join_deadline_at", None)
            else None
        ),
        "purohit_joined_at": (
            booking.purohit_joined_at.isoformat() if getattr(booking, "purohit_joined_at", None) else None
        ),
        "devotee_joined_at": (
            booking.devotee_joined_at.isoformat() if getattr(booking, "devotee_joined_at", None) else None
        ),
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
    if not is_online:
        await cancel_unpaid_requests_for_offline_purohit(purohit.id)
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


async def _expire_unpaid_booking(
    booking: PujaBooking,
    *,
    target_status: PujaBookingStatus = PujaBookingStatus.EXPIRED,
    reason: str,
    event_name: str = "puja_expired",
) -> PujaBooking:
    """Atomically expire or cancel an unpaid/unaccepted booking and release the Purohit lock."""
    now = _utcnow()
    raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
        {
            "_id": booking.id,
            "status": {
                "$in": [
                    PujaBookingStatus.AWAITING_ACCEPTANCE,
                    PujaBookingStatus.AWAITING_PAYMENT,
                    PujaBookingStatus.PENDING,
                ]
            },
            "payment_status": {"$ne": PujaPaymentStatus.PAID},
        },
        {
            "$set": {
                "status": target_status,
                "declined_at": now,
                "cancel_reason": reason,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    await _release_purohit_busy_lock(booking.purohit_id, booking.id)
    refreshed = await PujaBooking.get(booking.id)
    target = refreshed or booking
    if raw is not None:
        await realtime.publish_puja_event(
            target.user_id,
            target.purohit_user_id,
            event_name,
            serialize_booking_event(target),
        )
    return target


async def _abort_ghost_purohit_session(booking: PujaBooking, *, reason: str) -> PujaBooking:
    """Abort an IN_PROGRESS booking where Purohit failed the 60s room-join SLA, refund 100%, and penalize presence."""
    now = _utcnow()
    raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
        {
            "_id": booking.id,
            "status": PujaBookingStatus.IN_PROGRESS,
            "purohit_joined_at": None,
        },
        {
            "$set": {
                "status": PujaBookingStatus.DECLINED,
                "declined_at": now,
                "completed_at": now,
                "cancel_reason": reason,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    await _release_purohit_busy_lock(booking.purohit_id, booking.id)
    if raw is None:
        return await PujaBooking.get(booking.id) or booking

    # Track consecutive no-shows; auto-offline after 2 consecutive ghosted paid sessions
    p_doc = await Purohit.get_pymongo_collection().find_one_and_update(
        {"_id": booking.purohit_id},
        {"$inc": {"consecutive_missed_pujas": 1}, "$set": {"updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    if p_doc and int(p_doc.get("consecutive_missed_pujas", 0)) >= 2:
        await Purohit.get_pymongo_collection().update_one(
            {"_id": booking.purohit_id},
            {"$set": {"is_online": False, "last_seen_at": None, "updated_at": now}},
        )
        p_model = await Purohit.get(booking.purohit_id)
        if p_model is not None:
            await realtime.publish_purohit(p_model)

    latest = await PujaBooking.get(booking.id) or booking
    refunded = await _refund_booking(latest, reason=reason)
    await realtime.publish_puja_event(
        refunded.user_id,
        refunded.purohit_user_id,
        "puja_declined",
        serialize_booking_event(refunded),
    )
    return refunded


async def _reconcile_booking_state(booking: PujaBooking) -> PujaBooking:
    """Lazily enforce all SLA timers (45s accept, 90s payment, 60s join, session duration) at read time."""
    now = _utcnow()

    if booking.status == PujaBookingStatus.AWAITING_ACCEPTANCE:
        exp = _as_utc(getattr(booking, "accept_expires_at", None))
        if exp and exp <= now:
            return await _expire_unpaid_booking(
                booking,
                target_status=PujaBookingStatus.EXPIRED,
                reason="পুরোহিতজী ৪৫ সেকেন্ডের মধ্যে অনুরোধ গ্রহণ করেননি — কোনো টাকা কাটা হয়নি।",
            )

    elif booking.status == PujaBookingStatus.AWAITING_PAYMENT:
        exp = _as_utc(getattr(booking, "payment_expires_at", None))
        if exp and exp <= now:
            return await _expire_unpaid_booking(
                booking,
                target_status=PujaBookingStatus.EXPIRED,
                reason="৯০ সেকেন্ডের পেমেন্ট সময়সীমা শেষ হয়েছে।",
            )

    elif booking.status == PujaBookingStatus.CONFIRMED and booking.payment_status == PujaPaymentStatus.PAID:
        started = _as_utc(booking.started_at)
        if started and (now - started).total_seconds() >= PUJA_REQUEST_ACCEPT_TIMEOUT_SECONDS:
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
                latest = await PujaBooking.get(booking.id) or booking
                refunded = await _refund_booking(latest, reason=latest.cancel_reason or "Request timed out")
                await realtime.publish_puja_event(
                    refunded.user_id,
                    refunded.purohit_user_id,
                    "puja_declined",
                    serialize_booking_event(refunded),
                )
                return refunded

    elif booking.status == PujaBookingStatus.IN_PROGRESS and booking.payment_status == PujaPaymentStatus.PAID:
        join_deadline = _as_utc(getattr(booking, "purohit_join_deadline_at", None))
        if join_deadline and getattr(booking, "purohit_joined_at", None) is None and join_deadline <= now:
            return await _abort_ghost_purohit_session(
                booking,
                reason="পুরোহিত পেমেন্টের ৬০ সেকেন্ডের মধ্যে ভিডিও রুমে যোগ দেননি — ১০০% অটো-রিফান্ড করা হয়েছে।",
            )
        exp = _as_utc(getattr(booking, "expires_at", None))
        if exp and exp <= now:
            return await _finalize_puja_session(
                booking,
                status=PujaBookingStatus.COMPLETED,
                reason="Scheduled puja duration completed",
            )

    return booking


async def cancel_unpaid_requests_for_offline_purohit(purohit_id: PydanticObjectId) -> int:
    """Immediately cancel/refund pending requests when a Purohit closes dashboard or goes offline."""
    pending = await PujaBooking.find(
        {
            "purohit_id": purohit_id,
            "status": {
                "$in": [
                    PujaBookingStatus.AWAITING_ACCEPTANCE,
                    PujaBookingStatus.AWAITING_PAYMENT,
                    PujaBookingStatus.CONFIRMED,
                ]
            },
        }
    ).to_list()
    cancelled_count = 0
    for booking in pending:
        if booking.payment_status == PujaPaymentStatus.PAID:
            now = _utcnow()
            raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
                {"_id": booking.id, "status": booking.status},
                {
                    "$set": {
                        "status": PujaBookingStatus.DECLINED,
                        "declined_at": now,
                        "cancel_reason": "পুরোহিত ড্যাশবোর্ড বন্ধ করে অফলাইন হয়ে গেছেন — ১০০% অটো-রিফান্ড করা হয়েছে।",
                        "updated_at": now,
                    }
                },
                return_document=ReturnDocument.AFTER,
            )
            await _release_purohit_busy_lock(booking.purohit_id, booking.id)
            if raw is not None:
                latest = await PujaBooking.get(booking.id) or booking
                refunded = await _refund_booking(latest, reason=latest.cancel_reason or "Purohit went offline")
                await realtime.publish_puja_event(
                    refunded.user_id,
                    refunded.purohit_user_id,
                    "puja_declined",
                    serialize_booking_event(refunded),
                )
        else:
            await _expire_unpaid_booking(
                booking,
                target_status=PujaBookingStatus.CANCELLED,
                reason="পুরোহিত অফলাইন হয়ে যাওয়ায় অনুরোধ বাতিল হয়েছে — কোনো টাকা কাটা হয়নি।",
                event_name="puja_declined",
            )
        cancelled_count += 1
    return cancelled_count


async def _enforce_devotee_request_eligibility(user_id: PydanticObjectId) -> None:
    """Prevent griefing/busy-lock abuse: max 1 active unpaid request & 15m cooldown after repeated unpaid abandons."""
    now = _utcnow()
    # First lazily reconcile any expired requests belonging to this user
    stale_candidates = await PujaBooking.find(
        {
            "user_id": user_id,
            "status": {"$in": [PujaBookingStatus.AWAITING_ACCEPTANCE, PujaBookingStatus.AWAITING_PAYMENT]},
        }
    ).to_list()
    for candidate in stale_candidates:
        refreshed = await _reconcile_booking_state(candidate)
        if refreshed.status in (PujaBookingStatus.AWAITING_ACCEPTANCE, PujaBookingStatus.AWAITING_PAYMENT):
            raise ConflictError(
                "আপনার একটি পূজা অনুরোধ ইতোমধ্যে চলমান রয়েছে। সেটি সম্পন্ন বা বাতিল না হওয়া পর্যন্ত নতুন অনুরোধ পাঠানো যাবে না।",
                error_code="active_unpaid_request_exists",
            )

    lookback = now - timedelta(minutes=PUJA_ABUSE_LOOKBACK_MINUTES)
    abandoned = (
        await PujaBooking.find(
            {
                "user_id": user_id,
                "accepted_at": {"$ne": None},
                "payment_status": {"$ne": PujaPaymentStatus.PAID},
                "status": {"$in": [PujaBookingStatus.EXPIRED, PujaBookingStatus.CANCELLED]},
                "updated_at": {"$gte": lookback},
            }
        )
        .sort("-updated_at")
        .to_list()
    )
    if len(abandoned) >= 2:
        last_at = _as_utc(abandoned[0].updated_at) or now
        cooldown_until = last_at + timedelta(minutes=PUJA_ABUSE_COOLDOWN_MINUTES)
        if cooldown_until > now:
            mins_left = max(1, int((cooldown_until - now).total_seconds() // 60) + 1)
            raise BadRequestError(
                f"পরপর একাধিকবার পুরোহিত অনুমোদনের পর পেমেন্ট না করায় নতুন অনুরোধ {mins_left} মিনিটের জন্য স্থগিত রয়েছে।",
                error_code="puja_request_cooldown",
            )


async def book_puja(user: User, payload: PujaBookingCreate) -> tuple[PujaBooking, str | None]:
    """Pay-After-Accept Step 1: Send a zero-charge live puja request to an online Purohit (45s SLA)."""
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

    await _enforce_devotee_request_eligibility(user.id)

    target_puja = None
    for p in purohit.pujas:
        if p.id == payload.puja_item_id and p.is_active:
            target_puja = p
            break
    if target_puja is None:
        raise BadRequestError("This puja offering is currently unavailable.", error_code="puja_unavailable")

    now = _utcnow()
    booking_id = PydanticObjectId()
    claimed = await _acquire_purohit_busy_lock(purohit.id, booking_id, now)
    if claimed is None:
        raise ConflictError(
            "This Purohit just received another devotee's puja request. Please select another online Purohit.",
            error_code="purohit_busy",
        )

    booking_number = f"PUJA-{now.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    room_id = f"puja_room_{secrets.token_hex(10)}"
    user_full_name = f"{user.first_name} {user.last_name or ''}".strip() or "Devotee"

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
        status=PujaBookingStatus.AWAITING_ACCEPTANCE,
        payment_status=PujaPaymentStatus.PENDING,
        payment_method=payload.payment_method or "deferred",
        accept_expires_at=now + timedelta(seconds=PUJA_ACCEPT_SLA_SECONDS),
        started_at=now,
    )
    try:
        await booking.insert()
    except Exception:
        await _release_purohit_busy_lock(purohit.id, booking_id)
        raise

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
        "Puja request #{} sent (AWAITING_ACCEPTANCE, 45s SLA, ₹0 charged yet) by {}",
        booking_number,
        user.email,
    )
    return booking, None


async def accept_puja_booking(booking_id: str, current_user: User) -> tuple[PujaBooking, str]:
    """Purohit accepts request: transitions AWAITING_ACCEPTANCE -> AWAITING_PAYMENT (90s SLA) or legacy CONFIRMED -> IN_PROGRESS."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    booking = await _reconcile_booking_state(booking)

    is_purohit = booking.purohit_user_id == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not (is_purohit or is_admin):
        raise ForbiddenError("Only the assigned Purohit can accept this puja request.", error_code="access_denied")

    if booking.status == PujaBookingStatus.AWAITING_PAYMENT:
        return booking, ""

    if booking.status == PujaBookingStatus.AWAITING_ACCEPTANCE:
        now = _utcnow()
        pay_exp = now + timedelta(seconds=PUJA_PAYMENT_WINDOW_SECONDS)
        raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
            {"_id": booking.id, "status": PujaBookingStatus.AWAITING_ACCEPTANCE},
            {
                "$set": {
                    "status": PujaBookingStatus.AWAITING_PAYMENT,
                    "accepted_at": now,
                    "payment_expires_at": pay_exp,
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if raw is None:
            latest = await PujaBooking.get(booking.id)
            if latest and latest.status == PujaBookingStatus.AWAITING_PAYMENT:
                return latest, ""
            raise BadRequestError(
                "This puja request expired or was cancelled before acceptance.",
                error_code="invalid_booking_state",
            )
        updated = await PujaBooking.get(booking.id)
        assert updated is not None
        await Purohit.get_pymongo_collection().update_one(
            {"_id": updated.purohit_id},
            {
                "$set": {
                    "is_busy": True,
                    "busy_booking_id": updated.id,
                    "busy_since": now,
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
            "puja_accepted_for_payment",
            serialize_booking_event(updated),
        )
        logger.info(
            "Puja request #{} accepted by Purohit -> AWAITING_PAYMENT (90s SLA until {})",
            updated.booking_number,
            pay_exp.isoformat(),
        )
        return updated, ""

    # Legacy pre-paid flow (CONFIRMED + PAID)
    if booking.payment_status != PujaPaymentStatus.PAID:
        raise BadRequestError("Payment is not active for this booking.", error_code="payment_not_paid")

    if booking.status == PujaBookingStatus.IN_PROGRESS:
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
                "purohit_joined_at": now if is_purohit else None,
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


async def create_puja_razorpay_order(booking_id: str, user: User) -> PujaBooking:
    """Create (or reuse) a Razorpay order ONLY after Purohit accepted and while 90s payment window is active."""
    booking = await PujaBooking.get(PydanticObjectId(booking_id))
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")
    if booking.user_id != user.id and user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise ForbiddenError("You are not authorized to pay for this booking.", error_code="access_denied")

    booking = await _reconcile_booking_state(booking)
    if booking.status != PujaBookingStatus.AWAITING_PAYMENT:
        raise BadRequestError(
            booking.cancel_reason or "এই পূজা অনুরোধের পেমেন্ট সময়সীমা শেষ হয়েছে বা বাতিল হয়েছে।",
            error_code="payment_window_closed",
        )

    purohit = await Purohit.get(booking.purohit_id)
    if purohit is None or not purohit_presence.is_effectively_online(purohit):
        cancelled = await _expire_unpaid_booking(
            booking,
            target_status=PujaBookingStatus.CANCELLED,
            reason="পুরোহিত অফলাইন হয়ে যাওয়ায় পেমেন্ট বাতিল হয়েছে।",
            event_name="puja_declined",
        )
        raise ConflictError(cancelled.cancel_reason or "Purohit went offline.", error_code="purohit_offline")

    if booking.razorpay_order_id:
        return booking

    if not settings.razorpay_configured:
        raise ServiceUnavailableError("Payments are not configured.", error_code="payments_unavailable")

    amount_paise = max(100, int(round(booking.amount_inr * 100)))
    rzp = payments._razorpay()
    try:
        created_order = await asyncio.to_thread(
            rzp.order.create,
            {
                "amount": amount_paise,
                "currency": settings.WALLET_CURRENCY,
                "receipt": booking.booking_number,
                "notes": {
                    "purpose": "puja_booking",
                    "booking_id": str(booking.id),
                    "booking_number": booking.booking_number,
                    "user_id": str(user.id),
                },
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.opt(exception=exc).error("Razorpay order creation failed for accepted puja {}", booking.booking_number)
        raise ServiceUnavailableError(
            "পেমেন্ট গেটওয়ে শুরু করা যায়নি। অনুগ্রহ করে ওয়ালেট বা অন্য পদ্ধতি চেষ্টা করুন।",
            error_code="payment_order_failed",
        ) from exc

    now = _utcnow()
    await PujaBooking.get_pymongo_collection().update_one(
        {"_id": booking.id},
        {
            "$set": {
                "razorpay_order_id": created_order["id"],
                "payment_method": "razorpay",
                "updated_at": now,
            }
        },
    )
    return await PujaBooking.get(booking.id) or booking


async def _activate_paid_puja_session(
    booking: PujaBooking,
    *,
    payment_method: str,
    razorpay_payment_id: str | None = None,
    allow_grace_seconds: int = 10,
) -> tuple[PujaBooking, str]:
    """Atomically validate lock & payment window, transition to IN_PROGRESS, or 100% auto-refund if expired/offline."""
    now = _utcnow()

    if booking.payment_status == PujaPaymentStatus.PAID:
        token = (
            zego.generate_token(user_id=str(booking.user_id), room_id=booking.room_id)
            if booking.status in (PujaBookingStatus.CONFIRMED, PujaBookingStatus.IN_PROGRESS)
            else ""
        )
        return booking, token

    if booking.payment_status == PujaPaymentStatus.REFUNDED:
        return booking, ""

    # Check if window expired beyond network grace OR booking already closed
    pay_exp = _as_utc(getattr(booking, "payment_expires_at", None))
    window_expired = bool(pay_exp and now > (pay_exp + timedelta(seconds=allow_grace_seconds)))
    purohit = await Purohit.get(booking.purohit_id)
    purohit_ok = bool(
        purohit is not None
        and purohit_presence.is_effectively_online(purohit)
        and (
            getattr(purohit, "busy_booking_id", None) == booking.id
            or not bool(getattr(purohit, "is_busy", False))
        )
    )

    if booking.status not in (PujaBookingStatus.AWAITING_PAYMENT, PujaBookingStatus.PENDING) or window_expired or not purohit_ok:
        # Atomically record payment so _refund_booking issues a verified refund to the original source
        await PujaBooking.get_pymongo_collection().update_one(
            {"_id": booking.id, "payment_status": {"$nin": [PujaPaymentStatus.PAID, PujaPaymentStatus.REFUNDED]}},
            {
                "$set": {
                    "status": PujaBookingStatus.CANCELLED,
                    "payment_status": PujaPaymentStatus.PAID,
                    "payment_method": payment_method,
                    "razorpay_payment_id": razorpay_payment_id,
                    "updated_at": now,
                }
            },
        )
        refreshed = await PujaBooking.get(booking.id) or booking
        reason = (
            "৯০ সেকেন্ডের পেমেন্ট সময়সীমা শেষ হয়ে যাওয়ায় বা পুরোহিত অফলাইন হওয়ায় ১০০% অটো-রিফান্ড করা হয়েছে।"
        )
        refunded = await _refund_booking(refreshed, reason=reason)
        await realtime.publish_puja_event(
            refunded.user_id,
            refunded.purohit_user_id,
            "puja_declined",
            serialize_booking_event(refunded),
        )
        return refunded, ""

    # Re-ensure Purohit busy lock points strictly to this booking
    if getattr(purohit, "busy_booking_id", None) != booking.id:
        claimed = await _acquire_purohit_busy_lock(booking.purohit_id, booking.id, now)
        if claimed is None:
            await PujaBooking.get_pymongo_collection().update_one(
                {"_id": booking.id},
                {
                    "$set": {
                        "status": PujaBookingStatus.CANCELLED,
                        "payment_status": PujaPaymentStatus.PAID,
                        "payment_method": payment_method,
                        "razorpay_payment_id": razorpay_payment_id,
                        "updated_at": now,
                    }
                },
            )
            refreshed = await PujaBooking.get(booking.id) or booking
            refunded = await _refund_booking(
                refreshed,
                reason="পুরোহিত ইতোমধ্যে অন্য পূজায় যুক্ত হয়ে গেছেন — ১০০% অটো-রিফান্ড করা হয়েছে।",
            )
            return refunded, ""

    duration_mins = max(1, int(booking.puja_duration_minutes or 30))
    expires_at = now + timedelta(minutes=duration_mins)
    join_deadline = now + timedelta(seconds=PUJA_JOIN_SLA_SECONDS)

    raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
        {
            "_id": booking.id,
            "payment_status": {"$nin": [PujaPaymentStatus.PAID, PujaPaymentStatus.REFUNDED]},
        },
        {
            "$set": {
                "status": PujaBookingStatus.IN_PROGRESS,
                "payment_status": PujaPaymentStatus.PAID,
                "payment_method": payment_method,
                "razorpay_payment_id": razorpay_payment_id,
                "started_at": now,
                "expires_at": expires_at,
                "purohit_join_deadline_at": join_deadline,
                "purohit_joined_at": None,
                "devotee_joined_at": now,
                "updated_at": now,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    refreshed = await PujaBooking.get(booking.id)
    assert refreshed is not None

    if raw is not None:
        updated_purohit = await Purohit.get(refreshed.purohit_id)
        if updated_purohit is not None:
            await realtime.publish_purohit(updated_purohit)
        await realtime.publish_puja_event(
            refreshed.user_id,
            refreshed.purohit_user_id,
            "puja_accepted",
            serialize_booking_event(refreshed),
        )

    token = zego.generate_token(user_id=str(refreshed.user_id), room_id=refreshed.room_id)
    logger.info(
        "Puja booking #{} PAID via {} -> IN_PROGRESS until {} (Purohit join SLA: {}s)",
        refreshed.booking_number,
        payment_method,
        expires_at.isoformat(),
        PUJA_JOIN_SLA_SECONDS,
    )
    return refreshed, token


async def pay_puja_with_wallet(booking_id: str, user: User) -> tuple[PujaBooking, str]:
    """Debits user's Wallet Coins for an AWAITING_PAYMENT booking and activates the live puja room."""
    booking = await PujaBooking.get(PydanticObjectId(booking_id))
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")
    if booking.user_id != user.id and user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise ForbiddenError("You are not authorized to pay for this booking.", error_code="access_denied")

    booking = await _reconcile_booking_state(booking)
    if booking.payment_status == PujaPaymentStatus.PAID and booking.status == PujaBookingStatus.IN_PROGRESS:
        return booking, zego.generate_token(user_id=str(user.id), room_id=booking.room_id)
    if booking.status != PujaBookingStatus.AWAITING_PAYMENT:
        raise BadRequestError(
            booking.cancel_reason or "এই পূজাটির পেমেন্ট সময়সীমা শেষ হয়েছে বা বাতিল হয়েছে।",
            error_code="payment_window_closed",
        )

    purohit = await Purohit.get(booking.purohit_id)
    if purohit is None or not purohit_presence.is_effectively_online(purohit):
        await _expire_unpaid_booking(
            booking,
            target_status=PujaBookingStatus.CANCELLED,
            reason="পুরোহিত অফলাইন হয়ে গেছেন — কোনো কয়েন কাটা হয়নি।",
            event_name="puja_declined",
        )
        raise ConflictError("পুরোহিত বর্তমানে অফলাইন হয়ে গেছেন।", error_code="purohit_offline")

    platform = await settings_service.get_settings()
    coins_required = max(1, int(round(booking.amount_inr * platform.coins_per_rupee)))
    amount_paise = max(100, int(round(booking.amount_inr * 100)))

    await wallet_service.debit(
        user_id=booking.user_id,
        amount_coins=coins_required,
        reason=TransactionReason.FEATURE_USAGE,
        idempotency_key=f"puja_booking:{booking.booking_number}",
        ref=TransactionRef(),
        note=f"Live Puja: {booking.puja_name} (#{booking.booking_number})",
        amount_paise=amount_paise,
        coins_per_rupee=platform.coins_per_rupee,
    )

    activated, tok = await _activate_paid_puja_session(booking, payment_method="wallet", allow_grace_seconds=5)
    return activated, tok


async def verify_puja_payment(
    booking_id: str,
    user: User,
    payload: PujaPaymentVerifyRequest,
) -> tuple[PujaBooking, str]:
    """Verifies Razorpay HMAC signature, activates live puja room, or auto-refunds if window/purohit lapsed."""
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

    return await _activate_paid_puja_session(
        booking,
        payment_method="razorpay",
        razorpay_payment_id=payload.razorpay_payment_id,
        allow_grace_seconds=15,
    )


async def confirm_puja_from_webhook(
    *,
    booking: PujaBooking,
    payment_id: str,
    payment: dict,
) -> str:
    """Razorpay webhook fallback when devotee browser disconnected before calling verify-payment."""
    if booking.payment_status == PujaPaymentStatus.PAID:
        return "already_paid"
    if booking.payment_status == PujaPaymentStatus.REFUNDED:
        return "already_refunded"

    activated, _ = await _activate_paid_puja_session(
        booking,
        payment_method="razorpay",
        razorpay_payment_id=payment_id,
        allow_grace_seconds=30,
    )
    if activated.payment_status == PujaPaymentStatus.REFUNDED:
        return "refunded_window_lapsed"
    return "activated_in_progress"


async def mark_puja_payment_failed_from_webhook(*, booking: PujaBooking) -> None:
    """Record Razorpay payment failure without false refund."""
    if booking.payment_status != PujaPaymentStatus.PENDING:
        return
    await PujaBooking.get_pymongo_collection().update_one(
        {"_id": booking.id, "payment_status": PujaPaymentStatus.PENDING},
        {"$set": {"payment_status": PujaPaymentStatus.FAILED, "updated_at": _utcnow()}},
    )


async def cancel_puja_booking(booking_id: str, current_user: User, reason: str | None = None) -> PujaBooking:
    """Devotee cancels their own pending/waiting booking and releases Purohit immediately."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    is_devotee = booking.user_id == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not (is_devotee or is_admin):
        raise ForbiddenError("You are not authorized to cancel this booking.", error_code="access_denied")

    booking = await _reconcile_booking_state(booking)
    if booking.status in (PujaBookingStatus.CANCELLED, PujaBookingStatus.DECLINED, PujaBookingStatus.EXPIRED):
        return booking

    if booking.status in (PujaBookingStatus.AWAITING_ACCEPTANCE, PujaBookingStatus.AWAITING_PAYMENT, PujaBookingStatus.PENDING):
        return await _expire_unpaid_booking(
            booking,
            target_status=PujaBookingStatus.CANCELLED,
            reason=(reason or "").strip() or "ভক্ত অনুরোধটি বাতিল করেছেন — কোনো টাকা কাটা হয়নি।",
            event_name="puja_declined",
        )

    if booking.status == PujaBookingStatus.CONFIRMED:
        now = _utcnow()
        cancel_reason = (reason or "").strip() or "ভক্ত অনুরোধ বাতিল করেছেন — ১০০% অটো-রিফান্ড করা হয়েছে।"
        raw = await PujaBooking.get_pymongo_collection().find_one_and_update(
            {"_id": booking.id, "status": PujaBookingStatus.CONFIRMED},
            {
                "$set": {
                    "status": PujaBookingStatus.CANCELLED,
                    "declined_at": now,
                    "cancel_reason": cancel_reason,
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        await _release_purohit_busy_lock(booking.purohit_id, booking.id)
        target = await PujaBooking.get(booking.id) or booking
        if raw is not None:
            target = await _refund_booking(target, reason=cancel_reason)
            await realtime.publish_puja_event(
                target.user_id,
                target.purohit_user_id,
                "puja_declined",
                serialize_booking_event(target),
            )
        return target

    raise BadRequestError(
        f"Cannot cancel a puja booking that is already {booking.status.value}.",
        error_code="invalid_booking_state",
    )


async def decline_puja_booking(
    booking_id: str,
    current_user: User,
    reason: str | None = None,
) -> PujaBooking:
    """Purohit declines an incoming puja request -> unlocks Purohit and refunds devotee if paid."""
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

    decline_reason = (reason or "").strip() or "পুরোহিত এই মুহূর্তে ব্যস্ত থাকায় অনুরোধ প্রত্যাখ্যান করেছেন।"
    if booking.status in (PujaBookingStatus.AWAITING_ACCEPTANCE, PujaBookingStatus.AWAITING_PAYMENT):
        return await _expire_unpaid_booking(
            booking,
            target_status=PujaBookingStatus.DECLINED,
            reason=decline_reason,
            event_name="puja_declined",
        )

    if booking.status != PujaBookingStatus.CONFIRMED:
        raise BadRequestError(
            f"Cannot decline a booking that is already {booking.status.value}.",
            error_code="invalid_booking_state",
        )

    now = _utcnow()
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
    """Authorizes room access, tracks Purohit/Devotee join timestamps, and issues Zego token when paid."""
    b_oid = PydanticObjectId(booking_id)
    booking = await PujaBooking.get(b_oid)
    if booking is None:
        raise NotFoundError("Booking not found.", error_code="booking_not_found")

    booking = await _reconcile_booking_state(booking)

    is_devotee = booking.user_id == current_user.id
    is_purohit = booking.purohit_user_id == current_user.id
    is_admin = current_user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    if not (is_devotee or is_purohit or is_admin):
        raise ForbiddenError("You are not authorized to enter this sacred puja room.", error_code="access_denied")

    if booking.status in (PujaBookingStatus.AWAITING_ACCEPTANCE, PujaBookingStatus.AWAITING_PAYMENT):
        return booking, ""

    if booking.status in (PujaBookingStatus.DECLINED, PujaBookingStatus.CANCELLED):
        raise ForbiddenError(
            getattr(booking, "cancel_reason", None) or "This puja booking was cancelled/declined and refunded.",
            error_code="puja_cancelled",
        )
    if booking.status in (PujaBookingStatus.COMPLETED, PujaBookingStatus.EXPIRED):
        reason = getattr(booking, "cancel_reason", None)
        is_exp = booking.status == PujaBookingStatus.EXPIRED or reason == "Scheduled puja duration completed"
        raise ForbiddenError(
            reason or "This live puja session has completed.",
            error_code="puja_expired" if is_exp else "puja_completed",
        )
    if booking.payment_status != PujaPaymentStatus.PAID:
        raise ForbiddenError(
            "Complete payment before entering the live puja room.",
            error_code="payment_required",
        )

    now = _utcnow()
    if booking.status == PujaBookingStatus.IN_PROGRESS:
        exp = _as_utc(getattr(booking, "expires_at", None))
        if exp and exp <= now:
            await _finalize_puja_session(
                booking,
                status=PujaBookingStatus.COMPLETED,
                reason="Scheduled puja duration completed",
            )
            raise ForbiddenError(
                "The allocated time for this puja session has ended.",
                error_code="puja_expired",
            )
        join_patch: dict = {}
        if is_purohit and getattr(booking, "purohit_joined_at", None) is None:
            join_patch["purohit_joined_at"] = now
        if is_devotee and getattr(booking, "devotee_joined_at", None) is None:
            join_patch["devotee_joined_at"] = now
        if join_patch:
            join_patch["updated_at"] = now
            await PujaBooking.get_pymongo_collection().update_one({"_id": booking.id}, {"$set": join_patch})
            if "purohit_joined_at" in join_patch:
                await Purohit.get_pymongo_collection().update_one(
                    {"_id": booking.purohit_id},
                    {"$set": {"consecutive_missed_pujas": 0, "updated_at": now}},
                )
            booking = await PujaBooking.get(booking.id) or booking

    token = zego.generate_token(user_id=str(current_user.id), room_id=booking.room_id)
    return booking, token


async def get_booking(booking_id: str, current_user: User) -> PujaBooking:
    """Fetches a single PujaBooking with lazy SLA reconciliation."""
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

    return await _reconcile_booking_state(booking)


async def get_active_purohit_booking(purohit_user_id: PydanticObjectId) -> PujaBooking | None:
    """Returns currently active request/payment/live puja booking for the Purohit after lazy reconciliation."""
    booking = await PujaBooking.find_one(
        PujaBooking.purohit_user_id == purohit_user_id,
        {
            "status": {
                "$in": [
                    PujaBookingStatus.AWAITING_ACCEPTANCE,
                    PujaBookingStatus.AWAITING_PAYMENT,
                    PujaBookingStatus.IN_PROGRESS,
                    PujaBookingStatus.CONFIRMED,
                ]
            }
        },
    )
    if booking is None:
        return None
    reconciled = await _reconcile_booking_state(booking)
    if reconciled.status in (
        PujaBookingStatus.AWAITING_ACCEPTANCE,
        PujaBookingStatus.AWAITING_PAYMENT,
        PujaBookingStatus.IN_PROGRESS,
        PujaBookingStatus.CONFIRMED,
    ):
        return reconciled
    return None


async def list_purohit_bookings(
    purohit_user_id: PydanticObjectId, limit: int = 100, offset: int = 0
) -> list[PujaBooking]:
    """Lists request/active/historical bookings for the logged-in Purohit's dashboard."""
    cap = min(max(1, limit), 100)
    return (
        await PujaBooking.find(
            PujaBooking.purohit_user_id == purohit_user_id,
            PujaBooking.status != PujaBookingStatus.PENDING,
        )
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
    """Enforce 45s accept, 90s payment, 60s ghost-join SLA, room expiry, busy locks, and stale presence."""
    now = _utcnow()
    expired_accept = 0
    expired_payment = 0
    ghost_aborted = 0
    expired_count = 0
    timed_out_count = 0
    unlocked_orphans = 0

    # 1. Expire AWAITING_ACCEPTANCE requests past 45s SLA
    unaccepted = await PujaBooking.find(
        {
            "status": PujaBookingStatus.AWAITING_ACCEPTANCE,
            "accept_expires_at": {"$ne": None, "$lte": now},
        }
    ).to_list()
    for booking in unaccepted:
        await _reconcile_booking_state(booking)
        expired_accept += 1

    # 2. Expire AWAITING_PAYMENT requests past 90s payment window
    unpaid = await PujaBooking.find(
        {
            "status": PujaBookingStatus.AWAITING_PAYMENT,
            "payment_expires_at": {"$ne": None, "$lte": now},
        }
    ).to_list()
    for booking in unpaid:
        await _reconcile_booking_state(booking)
        expired_payment += 1

    # 3. Abort & 100% refund IN_PROGRESS bookings where Purohit didn't join within 60s
    ghosted = await PujaBooking.find(
        {
            "status": PujaBookingStatus.IN_PROGRESS,
            "payment_status": PujaPaymentStatus.PAID,
            "purohit_joined_at": None,
            "purohit_join_deadline_at": {"$ne": None, "$lte": now},
        }
    ).to_list()
    for booking in ghosted:
        await _reconcile_booking_state(booking)
        ghost_aborted += 1

    # 4. End any IN_PROGRESS rooms whose puja duration has elapsed
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

    # 5. Legacy: auto-decline & refund CONFIRMED requests unanswered past 120s
    cutoff = now - timedelta(seconds=PUJA_REQUEST_ACCEPT_TIMEOUT_SECONDS)
    unanswered = await PujaBooking.find(
        {
            "status": PujaBookingStatus.CONFIRMED,
            "payment_status": PujaPaymentStatus.PAID,
            "started_at": {"$ne": None, "$lte": cutoff},
        }
    ).to_list()
    for booking in unanswered:
        await _reconcile_booking_state(booking)
        timed_out_count += 1

    # 6. Release any orphaned busy locks pointing to finished bookings
    busy_purohits = await Purohit.find({"is_busy": True}).to_list()
    for p in busy_purohits:
        b = await PujaBooking.get(p.busy_booking_id) if p.busy_booking_id else None
        if b is None or b.status not in (
            PujaBookingStatus.AWAITING_ACCEPTANCE,
            PujaBookingStatus.AWAITING_PAYMENT,
            PujaBookingStatus.CONFIRMED,
            PujaBookingStatus.IN_PROGRESS,
        ):
            await _release_purohit_busy_lock(p.id)
            unlocked_orphans += 1

    # 7. Sweep stale WebSocket presence
    presence_stats = await purohit_presence.sweep()

    return {
        "expired_accept": expired_accept,
        "expired_payment": expired_payment,
        "ghost_aborted": ghost_aborted,
        "expired_rooms": expired_count,
        "timed_out_requests": timed_out_count,
        "unlocked_orphans": unlocked_orphans,
        **presence_stats,
    }


async def live_puja_worker_loop() -> None:
    """Background worker enforcing 45s accept, 90s payment, 60s join SLAs, room timers, and Purohit presence."""
    from pymongo.errors import PyMongoError

    logger.info("Live Purohit session timer & presence worker started (10s sweep).")
    while True:
        try:
            await asyncio.sleep(10)
            stats = await reconcile_live_puja_sessions()
            if any(stats.values()):
                logger.info("Live Purohit worker tick: {}", stats)
        except asyncio.CancelledError:
            logger.info("Live Purohit worker stopped gracefully.")
            break
        except (PyMongoError, TimeoutError, OSError) as db_err:
            logger.warning("MongoDB temporarily unavailable in live Purohit worker: {}", db_err)
            await asyncio.sleep(10)
        except Exception as exc:  # noqa: BLE001
            logger.opt(exception=exc).error("Unexpected error in live Purohit worker: {}", exc)
            await asyncio.sleep(10)
