"""Astrologer accounts.

Astrologers never sign themselves up. An admin opens the account, a password is
generated, and the astrologer is emailed it — so the same "both stores or
neither" rule as registration applies here, with the same rollback.
"""

import secrets
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from pymongo.errors import DuplicateKeyError
from slugify import slugify

from app.core.exceptions import ConflictError, ForbiddenError
from app.core.security import hash_password
from app.models.astrologer import Astrologer
from app.models.enums import AccountStatus, AuthProvider, ConsultationMode, UserRole
from app.models.pending_registration import PendingRegistration
from app.models.user import User
from app.schemas.astrologer import (
    AstrologerAdminUpdate,
    AstrologerCreate,
    AstrologerFilters,
    AstrologerProfile,
    AstrologerPublic,
    AstrologerUpdate,
    AvailabilityUpdate,
    ResolvedRates,
    ServiceDurationOut,
)
from app.schemas.common import Paginated, build_page
from app.services import firebase, realtime, storage
from app.services.email import send_astrologer_welcome_email
from app.services.storage import ALLOWED_IMAGE_TYPES

# No look-alike characters, so it survives being read off a screen or a phone call.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"

# Clearing these would leave the profile unusable.
NON_CLEARABLE = {"first_name", "display_name"}


def generate_initial_password(length: int = 10) -> str:
    """A readable one-off password, comfortably over Firebase's 6-character floor."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


async def _unique_slug(display_name: str) -> str:
    base = slugify(display_name, max_length=120) or "astrologer"
    candidate, suffix = base, 2
    while await Astrologer.find_one(Astrologer.slug == candidate) is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _format_service_duration(profile: Astrologer) -> ServiceDurationOut:
    """Calculates hours and human-readable badges purely from actual real session minutes."""
    sd = getattr(profile, "service_duration", None)
    c_min = int(sd.chat_minutes) if sd and sd.chat_minutes else 0
    cl_min = int(sd.call_minutes) if sd and sd.call_minutes else 0
    v_min = int(sd.video_minutes) if sd and sd.video_minutes else 0

    tot_min = c_min + cl_min + v_min

    v_hr = round(v_min / 60, 1) if v_min > 0 else 0.0
    c_hr = round(c_min / 60, 1) if c_min > 0 else 0.0
    cl_hr = round(cl_min / 60, 1) if cl_min > 0 else 0.0
    tot_hr = round(tot_min / 60, 1) if tot_min > 0 else 0.0

    def _fmt(mins: int) -> str:
        if mins <= 0:
            return "0 mins"
        if mins < 60:
            return f"{mins} mins"
        h = round(mins / 60, 1)
        if h == int(h):
            return f"{int(h)} hrs"
        return f"{h} hrs"

    return ServiceDurationOut(
        chat_minutes=c_min,
        call_minutes=cl_min,
        video_minutes=v_min,
        total_minutes=tot_min,
        chat_hours=c_hr,
        call_hours=cl_hr,
        video_hours=v_hr,
        total_hours=tot_hr,
        formatted_chat=_fmt(c_min),
        formatted_call=_fmt(cl_min),
        formatted_video=_fmt(v_min),
        formatted_total=_fmt(tot_min),
    )


def to_profile(user: User, profile: Astrologer) -> AstrologerProfile:
    return AstrologerProfile(
        id=str(profile.id),
        user_id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        middle_name=user.middle_name,
        last_name=user.last_name,
        full_name=user.full_name,
        phone=user.phone,
        display_name=profile.display_name,
        slug=profile.slug,
        tagline=profile.tagline,
        bio=profile.bio,
        profile_image_url=profile.profile_image_url,
        banner_image_url=profile.banner_image_url,
        gallery=profile.gallery or [],
        intro_video_url=profile.intro_video_url,
        skills=profile.skills,
        languages=profile.languages,
        specialisations=profile.specialisations,
        qualifications=profile.qualifications,
        experience_years=profile.experience_years,
        rates=profile.rates,
        modes_enabled=profile.modes_enabled,
        commission_percent=profile.commission_percent,
        bank=profile.bank,
        availability=profile.availability,
        rating=profile.rating,
        total_consultations=profile.total_consultations,
        service_duration=_format_service_duration(profile),
        followers_count=profile.followers_count,
        is_listed=profile.is_listed,
        is_featured=profile.is_featured,
        display_order=profile.display_order,
        status=user.status,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
        created_at=profile.created_at,
    )


# ------------------------------------------------------------ admin: create
async def create_astrologer(payload: AstrologerCreate) -> tuple[User, Astrologer, str, bool]:
    """Opens an astrologer account. Returns (user, profile, password, email_sent)."""
    email = payload.email.lower().strip()
    firebase.require_enabled()

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
    created_in_firebase = False
    user: User | None = None

    try:
        # --- Firebase first, as in registration -----------------------------
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
                logger.info(
                    "Adopted orphaned Firebase user {} for astrologer {}", existing.uid, email
                )
            else:
                record = await firebase.create_user(
                    email=email,
                    password=password,
                    display_name=display_name,
                    email_verified=True,
                )
                firebase_uid = record.uid
                created_in_firebase = True

        # --- the account ----------------------------------------------------
        user = User(
            email=email,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            last_name=payload.last_name,
            phone=payload.phone,
            hashed_password=hash_password(password),
            firebase_uid=firebase_uid,
            auth_providers=[AuthProvider.PASSWORD],
            role=UserRole.ASTROLOGER,
            is_email_verified=True,
            # They did not choose this password, so they are asked to replace it.
            must_change_password=True,
        )
        await user.insert()

        # --- the professional profile ---------------------------------------
        profile = Astrologer(
            user_id=user.id,
            display_name=display_name,
            slug=await _unique_slug(display_name),
            tagline=payload.tagline,
            bio=payload.bio,
            skills=payload.skills,
            languages=payload.languages,
            specialisations=payload.specialisations,
            qualifications=payload.qualifications,
            experience_years=payload.experience_years,
            rates=payload.rates,
            commission_percent=payload.commission_percent,
            is_listed=payload.is_listed,
            is_featured=payload.is_featured,
            display_order=payload.display_order,
            **({"modes_enabled": payload.modes_enabled} if payload.modes_enabled else {}),
        )
        await profile.insert()

    except DuplicateKeyError:
        if user is not None and user.id is not None:
            await user.delete()
        if created_in_firebase and firebase_uid:
            await firebase.delete_user(firebase_uid)
        raise ConflictError(
            "An account with this email or phone number already exists.",
            error_code="account_already_exists",
        )
    except Exception:
        # Unwind in the reverse order it was built.
        if user is not None and user.id is not None:
            await user.delete()
        if created_in_firebase and firebase_uid:
            await firebase.delete_user(firebase_uid)
        raise

    # A half-finished self-signup on the same email is now meaningless.
    await PendingRegistration.find(PendingRegistration.email == email).delete()

    # --- tell them, without letting a mail failure undo the account ---------
    email_sent = False
    try:
        email_sent = await send_astrologer_welcome_email(
            to=email, name=payload.first_name, password=password
        )
    except Exception as exc:  # noqa: BLE001 - the account is already created
        logger.error(
            "Astrologer {} was created but the welcome email failed: {}. The admin "
            "must pass the password on by hand.",
            email,
            exc,
        )

    # On the directory from this moment, without waiting for a poll.
    from app.services import realtime

    await realtime.publish_astrologer(profile)

    logger.success("Astrologer account created by admin: {} -> {}", email, user.id)
    return user, profile, password, email_sent


# -------------------------------------------------------------- editing
def _apply(target: object, updates: dict) -> None:
    for field, value in updates.items():
        setattr(target, field, value)


async def update_profile(
    user: User,
    profile: Astrologer,
    payload: AstrologerUpdate | AstrologerAdminUpdate,
    *,
    by_admin: bool = False,
) -> tuple[User, Astrologer]:
    updates = payload.model_dump(exclude_unset=True)

    for field in NON_CLEARABLE & updates.keys():
        if updates[field] is None:
            raise ForbiddenError(f"'{field}' cannot be removed.", error_code="field_not_clearable")

    # --- fields that live on the account, not the profile -----------------
    account_fields = {"first_name", "middle_name", "last_name", "phone"}
    account_updates = {k: updates.pop(k) for k in list(updates) if k in account_fields}

    status = updates.pop("status", None)
    if status is not None:
        if not by_admin:
            raise ForbiddenError(
                "Only an admin can change the account status.", error_code="admin_only"
            )
        user.status = AccountStatus(status)
        # The directory is gated on `is_listed` alone, so suspending has to pull
        # them out of it — otherwise a suspended astrologer stays on the site.
        if user.status is not AccountStatus.ACTIVE:
            profile.is_listed = False
            profile.availability.is_online = False

    if "phone" in account_updates and account_updates["phone"] != user.phone:
        user.is_phone_verified = False

    if account_updates or status is not None:
        _apply(user, account_updates)
        try:
            await user.save()
        except DuplicateKeyError:
            raise ConflictError(
                "That phone number is already used by another account.",
                error_code="phone_already_registered",
            )

    # --- the professional profile ------------------------------------------
    if "bank" in updates:
        from app.models.astrologer import BankDetails

        bank = updates.pop("bank")
        profile.bank = BankDetails(**bank) if bank else BankDetails()

    if "rates" in updates:
        from app.models.astrologer import RateCard

        rates = updates.pop("rates")
        profile.rates = RateCard(**rates) if rates else RateCard()

    # Renaming re-slugs, so the public URL follows the name.
    if updates.get("display_name") and updates["display_name"] != profile.display_name:
        profile.slug = await _unique_slug(updates["display_name"])

    _apply(profile, updates)
    await profile.save()

    # Price, name, skills and listing all live on the public card, so anyone
    # looking at the directory right now should see the change without
    # reloading.
    from app.services import realtime

    await realtime.publish_astrologer(profile)

    logger.info("Astrologer profile updated: {}", user.email)
    return user, profile


async def update_availability(profile: Astrologer, payload: AvailabilityUpdate) -> Astrologer:
    """The astrologer's own switches.

    `is_online` is the one switch that is not simply stored. Switching *off*
    has to clear the heartbeat stamp too, or the astrologer would keep counting
    as present; switching *on* has to stamp it, or they would be flagged online
    while every reader still judged them stale and showed them grey.
    """
    from app.models.base import utcnow
    from app.services import presence, realtime

    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    online = updates.pop("is_online", None)

    _apply(profile.availability, updates)

    if online is False:
        # Clears the stamp as well as the flag, and mirrors it.
        return await presence.go_offline(profile, reason="switched off")

    if online is True:
        profile.availability.is_online = True
        profile.availability.last_online_at = utcnow()
        profile.availability.last_seen_at = utcnow()

    await profile.save()
    await realtime.publish_astrologer(profile)
    return profile


# ------------------------------------------------------ public directory
# Only `is_listed` gates the directory, so every path that suspends an account
# must clear it — see `update_profile` and the admin deactivate route.
MAX_GALLERY_IMAGES = 12


async def to_public(profile: Astrologer, platform: Any = None) -> AstrologerPublic:
    """Fills in the platform defaults, so a card never shows a blank price.

    Also reports presence as it is *now*: an astrologer whose panel stopped
    heartbeating is shown offline here even though MongoDB still holds the
    flag they set, so a closed browser never leaves a ghost on the directory.
    """
    from app.services import billing, presence
    from app.services import settings as settings_service

    if platform is None:
        platform = await settings_service.get_settings()

    public = AstrologerPublic.model_validate(
        {**profile.model_dump(), "rates": {
            "chat_coins_per_minute": 0,
            "call_coins_per_minute": 0,
            "video_coins_per_minute": 0,
        }}
    )
    public.rates = ResolvedRates(
        chat_coins_per_minute=(
            await billing.price_for(profile, ConsultationMode.CHAT, platform=platform)
        ).coins_per_minute,
        call_coins_per_minute=(
            await billing.price_for(profile, ConsultationMode.CALL, platform=platform)
        ).coins_per_minute,
        video_coins_per_minute=(
            await billing.price_for(profile, ConsultationMode.VIDEO, platform=platform)
        ).coins_per_minute,
    )
    public.availability.is_online = presence.is_effectively_online(profile.availability)

    sd = getattr(profile, "service_duration", None)
    if not sd or (sd.chat_minutes == 0 and sd.call_minutes == 0 and sd.video_minutes == 0):
        try:
            from app.models.astrologer import ServiceDuration
            from app.models.call import CallSession
            from app.models.chat import ChatSession
            from app.models.enums import CallStatus, ChatStatus

            chats = await ChatSession.find(
                ChatSession.astrologer_id == profile.id,
                ChatSession.status == ChatStatus.ENDED,
            ).to_list()
            calls = await CallSession.find(
                CallSession.astrologer_id == profile.id,
                CallSession.status == CallStatus.ENDED,
            ).to_list()

            c_mins = sum(max(1, round(c.duration_seconds / 60)) for c in chats if c.duration_seconds > 0)
            v_mins = sum(
                max(1, round(c.duration_seconds / 60))
                for c in calls
                if c.mode == ConsultationMode.VIDEO and c.duration_seconds > 0
            )
            cl_mins = sum(
                max(1, round(c.duration_seconds / 60))
                for c in calls
                if c.mode != ConsultationMode.VIDEO and c.duration_seconds > 0
            )
            if c_mins > 0 or v_mins > 0 or cl_mins > 0:
                profile.service_duration = ServiceDuration(
                    chat_minutes=c_mins,
                    call_minutes=cl_mins,
                    video_minutes=v_mins,
                )
                await profile.save()
        except Exception:
            pass

    public.service_duration = _format_service_duration(profile)
    return public


def _directory_query(filters: AstrologerFilters, default_chat_rate: int | None = None):
    from beanie.operators import And, In, Or, RegEx

    conditions: list = [Astrologer.is_listed == True]  # noqa: E712

    if filters.search:
        pattern = filters.search.strip()
        conditions.append(
            Or(
                RegEx(Astrologer.display_name, pattern, options="i"),
                RegEx(Astrologer.specialisations, pattern, options="i"),
                RegEx(Astrologer.tagline, pattern, options="i"),
            )
        )
    if filters.skill:
        conditions.append(In(Astrologer.skills, [filters.skill]))
    if filters.language:
        conditions.append(In(Astrologer.languages, [filters.language]))
    if filters.mode:
        conditions.append(In(Astrologer.modes_enabled, [filters.mode]))
    if filters.online_only:
        # Both halves, or "online now" would list everyone who ever forgot to
        # switch off. The TTL is applied in the query so the count and the
        # pages agree with what the cards end up showing.
        from app.services import presence

        conditions.append(Astrologer.availability.is_online == True)  # noqa: E712
        conditions.append(
            {"availability.last_seen_at": {"$gte": presence.stale_before()}}
        )
    if filters.featured_only:
        conditions.append(Astrologer.is_featured == True)  # noqa: E712
    if filters.min_experience is not None:
        conditions.append(Astrologer.experience_years >= filters.min_experience)
    if filters.max_coins_per_minute is not None:
        # An astrologer with no chat rate of their own charges the platform
        # default, so whether they match depends on what that default is.
        # Leaving them out would quietly hide everyone who was never priced
        # individually — which is most of them.
        ceiling = filters.max_coins_per_minute
        rate_field = "rates.chat_coins_per_minute"
        if default_chat_rate is not None and default_chat_rate <= ceiling:
            conditions.append(
                Or(
                    {rate_field: {"$lte": ceiling}},
                    {rate_field: None},
                    {rate_field: {"$exists": False}},
                )
            )
        else:
            conditions.append({rate_field: {"$lte": ceiling}})

    return Astrologer.find(And(*conditions))


async def list_public(
    filters: AstrologerFilters, page: int, limit: int
) -> Paginated[AstrologerPublic]:
    """The directory: whoever is online comes first, then the featured ones."""
    from app.services import settings as settings_service

    platform = await settings_service.get_settings()
    query = _directory_query(filters, platform.default_chat_coins_per_minute)
    total = await query.count()

    profiles = (
        await query.sort(
            -Astrologer.availability.is_online,
            -Astrologer.availability.last_seen_at,
            -Astrologer.is_featured,
            Astrologer.display_order,
            -Astrologer.rating.average,
        )
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list()
    )
    return build_page(
        [await to_public(p, platform=platform) for p in profiles], total, page, limit
    )


async def get_public(identifier: str) -> AstrologerPublic:
    """Fetch one astrologer by slug, or by id."""
    from beanie import PydanticObjectId

    from app.core.exceptions import NotFoundError

    profile = await Astrologer.find_one(Astrologer.slug == identifier)
    if profile is None and PydanticObjectId.is_valid(identifier):
        profile = await Astrologer.get(PydanticObjectId(identifier))

    # An unlisted astrologer is not found as far as the public is concerned.
    if profile is None or not profile.is_listed:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    return await to_public(profile)


# --------------------------------------------------------------- images
async def _upload_image(file, folder: str, user_id) -> storage.UploadResult:  # noqa: ANN001
    from app.core.config import settings

    size = settings.AVATAR_MAX_DIMENSION
    return await storage.upload_file(
        file,
        folder=folder,
        allowed_types=ALLOWED_IMAGE_TYPES,
        tags=[f"astrologer:{user_id}"],
        # Compressed before storing, as for user avatars.
        transformation=[
            {"width": size, "height": size, "crop": "limit"},
            {"quality": settings.AVATAR_QUALITY},
        ],
        image_format=settings.AVATAR_FORMAT,
    )


async def set_profile_image(user: User, profile: Astrologer, file) -> Astrologer:  # noqa: ANN001
    result = await _upload_image(file, "astrologers", user.id)

    previous = profile.profile_image_public_id
    profile.profile_image_url = result.url
    profile.profile_image_public_id = result.public_id
    await profile.save()

    # Only once the replacement is safely stored and recorded.
    if previous and previous != result.public_id:
        await storage.delete_file(previous)

    logger.info("Astrologer photo stored for {} ({} bytes)", user.email, result.bytes)
    return profile


async def remove_profile_image(profile: Astrologer) -> Astrologer:
    from app.core.exceptions import NotFoundError

    if not profile.profile_image_url:
        raise NotFoundError("There is no photo to remove.", error_code="no_profile_image")

    public_id = profile.profile_image_public_id
    profile.profile_image_url = None
    profile.profile_image_public_id = None
    await profile.save()

    if public_id:
        await storage.delete_file(public_id)
    return profile


async def _upload_banner_image(file, folder: str, user_id) -> storage.UploadResult:  # noqa: ANN001
    return await storage.upload_file(
        file,
        folder=folder,
        allowed_types=ALLOWED_IMAGE_TYPES,
        tags=[f"astrologer:{user_id}", "banner"],
        transformation=[
            {"width": 1200, "height": 600, "crop": "limit"},
            {"quality": "auto"},
        ],
        image_format="webp",
    )


async def set_banner_image(user: User, profile: Astrologer, file) -> Astrologer:  # noqa: ANN001
    result = await _upload_banner_image(file, "astrologers/banners", user.id)

    previous = profile.banner_image_public_id
    profile.banner_image_url = result.url
    profile.banner_image_public_id = result.public_id
    await profile.save()

    if previous and previous != result.public_id:
        await storage.delete_file(previous)

    from app.services import realtime

    await realtime.publish_astrologer(profile)
    logger.info("Astrologer banner stored for {} ({} bytes)", user.email, result.bytes)
    return profile


async def remove_banner_image(profile: Astrologer) -> Astrologer:
    from app.core.exceptions import NotFoundError
    from app.services import realtime

    if not profile.banner_image_url:
        raise NotFoundError("There is no banner to remove.", error_code="no_banner_image")

    public_id = profile.banner_image_public_id
    profile.banner_image_url = None
    profile.banner_image_public_id = None
    await profile.save()

    if public_id:
        await storage.delete_file(public_id)

    await realtime.publish_astrologer(profile)
    return profile


async def _upload_gallery_image(file, folder: str, user_id) -> storage.UploadResult:  # noqa: ANN001
    return await storage.upload_file(
        file,
        folder=folder,
        allowed_types=ALLOWED_IMAGE_TYPES,
        tags=[f"astrologer:{user_id}", "gallery"],
        transformation=[
            {"width": 1600, "height": 1600, "crop": "limit"},
            {"quality": "auto"},
        ],
        image_format="webp",
    )


async def add_gallery_image(user: User, profile: Astrologer, file):  # noqa: ANN001
    from app.core.exceptions import BadRequestError
    from app.models.astrologer import GalleryImage

    if profile.gallery is None:
        profile.gallery = []

    if len(profile.gallery) >= MAX_GALLERY_IMAGES:
        raise BadRequestError(
            f"The gallery is full — {MAX_GALLERY_IMAGES} images at most. "
            "Remove one before adding another.",
            error_code="gallery_full",
        )

    result = await _upload_gallery_image(file, "astrologers/gallery", user.id)
    raw_item = {"url": result.url, "public_id": result.public_id}

    # Build updated gallery list and atomically set on MongoDB collection
    # Using $set avoids MongoDB errors if gallery was previously null
    existing_items = [
        {"url": g.url, "public_id": g.public_id}
        for g in (profile.gallery or [])
    ]
    new_gallery = [*existing_items, raw_item]

    await Astrologer.get_pymongo_collection().update_one(
        {"_id": profile.id},
        {
            "$set": {
                "gallery": new_gallery,
                "updated_at": datetime.now(UTC),
            }
        },
    )

    image = GalleryImage(url=result.url, public_id=result.public_id)
    profile.gallery = [GalleryImage(**item) for item in new_gallery]

    try:
        from app.services import realtime
        await realtime.publish_astrologer(profile)
    except Exception as exc:
        logger.warning("Realtime publish failed (non-fatal): {}", exc)

    logger.info("Astrologer gallery photo added for {} ({} bytes)", user.email, result.bytes)
    return image, profile


async def remove_gallery_image(profile: Astrologer, public_id: str) -> Astrologer:
    from app.core.exceptions import NotFoundError

    if profile.gallery is None:
        profile.gallery = []

    image = next((g for g in profile.gallery if g.public_id == public_id), None)
    if image is None:
        raise NotFoundError("That image is not in the gallery.", error_code="image_not_found")

    # Direct atomic $set on MongoDB collection guarantees immediate persistence
    remaining_items = [
        {"url": g.url, "public_id": g.public_id}
        for g in (profile.gallery or [])
        if g.public_id != public_id
    ]

    await Astrologer.get_pymongo_collection().update_one(
        {"_id": profile.id},
        {
            "$set": {
                "gallery": remaining_items,
                "updated_at": datetime.now(UTC),
            }
        },
    )

    profile.gallery = [GalleryImage(**item) for item in remaining_items]

    try:
        from app.services import realtime
        await realtime.publish_astrologer(profile)
    except Exception as exc:
        logger.warning("Realtime publish failed (non-fatal): {}", exc)

    await storage.delete_file(public_id)
    logger.info("Astrologer gallery photo removed: {}", public_id)
    return profile
