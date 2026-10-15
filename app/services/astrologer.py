"""Astrologer accounts.

Astrologers never sign themselves up. An admin opens the account, a password is
generated, and the astrologer is emailed it — so the same "both stores or
neither" rule as registration applies here, with the same rollback.
"""

import secrets

from loguru import logger
from pymongo.errors import DuplicateKeyError
from slugify import slugify

from app.core.exceptions import ConflictError, ForbiddenError
from app.core.security import hash_password
from app.models.astrologer import Astrologer
from app.models.enums import AccountStatus, AuthProvider, UserRole
from app.models.pending_registration import PendingRegistration
from app.models.user import User
from app.schemas.astrologer import (
    AstrologerAdminUpdate,
    AstrologerCreate,
    AstrologerProfile,
    AstrologerUpdate,
    AvailabilityUpdate,
)
from app.services import firebase
from app.services.email import send_astrologer_welcome_email

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
        gallery=profile.gallery,
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
    email_sent = True
    try:
        await send_astrologer_welcome_email(to=email, name=payload.first_name, password=password)
    except Exception as exc:  # noqa: BLE001 - the account is already created
        email_sent = False
        logger.error(
            "Astrologer {} was created but the welcome email failed: {}. The admin "
            "must pass the password on by hand.",
            email,
            exc,
        )

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

    logger.info("Astrologer profile updated: {}", user.email)
    return user, profile


async def update_availability(profile: Astrologer, payload: AvailabilityUpdate) -> Astrologer:
    from app.models.base import utcnow

    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    _apply(profile.availability, updates)
    if updates.get("is_online"):
        profile.availability.last_online_at = utcnow()
    await profile.save()
    return profile
