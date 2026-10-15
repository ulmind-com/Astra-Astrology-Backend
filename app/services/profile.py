"""Reading and editing the signed-in user's profile.

PATCH semantics, so the client can add, change *and* remove values with one
endpoint:

* field absent from the body        -> left alone
* field present with a value        -> set
* field present and explicitly null -> cleared
"""

from typing import Any

from fastapi import UploadFile
from loguru import logger
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.profile import Address, BirthDetails, CurrentLocation, NotificationPreferences
from app.models.user import User
from app.schemas.user import (
    AddressInput,
    AddressUpdate,
    ProfileCompleteness,
    ProfileUpdate,
    UserProfile,
)
from app.services import storage
from app.services.storage import ALLOWED_IMAGE_TYPES

# Clearing these would leave the account unusable.
NON_CLEARABLE = {"first_name", "language"}


# ----------------------------------------------------------------- reading
def describe_completeness(user: User) -> ProfileCompleteness:
    """Tells the client exactly what is still missing, per feature."""
    birth = user.birth
    missing: list[str] = []

    if not user.first_name:
        missing.append("first_name")
    if birth.date_of_birth is None:
        missing.append("birth.date_of_birth")
    if not birth.is_time_known and birth.time_of_birth is None:
        missing.append("birth.time_of_birth")
    if birth.latitude is None or birth.longitude is None:
        missing.append("birth.latitude/longitude")
    if birth.timezone is None:
        missing.append("birth.timezone")
    if not user.current_location.is_panchang_ready:
        missing.append("current_location")

    return ProfileCompleteness(
        profile_complete=user.is_profile_complete,
        chart_ready=birth.is_chart_ready,
        panchang_ready=user.current_location.is_panchang_ready,
        numerology_ready=birth.date_of_birth is not None,
        missing=missing,
    )


def to_profile(user: User) -> UserProfile:
    profile = UserProfile.model_validate(user)
    profile.completeness = describe_completeness(user)
    return profile


# ----------------------------------------------------------------- editing
def _merge_nested(current: Any, payload: Any, model: type) -> Any:
    """Applies only the keys the client actually sent."""
    changes = payload.model_dump(exclude_unset=True)
    return model(**(current.model_dump() | changes))


async def update_profile(user: User, payload: ProfileUpdate) -> User:
    # exclude_unset (not exclude_none) is what makes an explicit null a clear.
    updates = payload.model_dump(exclude_unset=True)

    for field in NON_CLEARABLE & updates.keys():
        if updates[field] is None:
            raise BadRequestError(f"'{field}' cannot be removed.", error_code="field_not_clearable")

    # --- nested blocks merge rather than replace -------------------------
    if "birth" in updates:
        updates.pop("birth")
        user.birth = (
            BirthDetails()
            if payload.birth is None
            else _merge_nested(user.birth, payload.birth, BirthDetails)
        )

    if "current_location" in updates:
        updates.pop("current_location")
        user.current_location = (
            CurrentLocation()
            if payload.current_location is None
            else _merge_nested(user.current_location, payload.current_location, CurrentLocation)
        )

    if "notifications" in updates:
        updates.pop("notifications")
        user.notifications = payload.notifications or NotificationPreferences()

    # --- changing the phone number un-verifies it ------------------------
    if "phone" in updates and updates["phone"] != user.phone:
        user.is_phone_verified = False

    for field, value in updates.items():
        setattr(user, field, value)

    try:
        await user.save()
    except DuplicateKeyError:
        raise ConflictError(
            "That phone number is already used by another account.",
            error_code="phone_already_registered",
        )

    logger.info("Profile updated for {} ({} field(s))", user.email, len(updates))
    return user


# ---------------------------------------------------------------- avatar
async def set_avatar(user: User, file: UploadFile) -> User:
    """Stores a compressed avatar and removes the one it replaces."""
    size = settings.AVATAR_MAX_DIMENSION
    result = await storage.upload_file(
        file,
        folder="avatars",
        allowed_types=ALLOWED_IMAGE_TYPES,
        tags=[f"user:{user.id}"],
        # Shrink to fit the box (never upscale), then let Cloudinary pick the
        # compression level. Applied before storing, so the stored file is small.
        transformation=[
            {"width": size, "height": size, "crop": "limit"},
            {"quality": settings.AVATAR_QUALITY},
        ],
        image_format=settings.AVATAR_FORMAT,
    )

    previous = user.avatar_public_id
    user.avatar_url = result.url
    user.avatar_public_id = result.public_id
    await user.save()

    # Remove the old file only once the new one is safely stored and recorded,
    # so a failure here can never leave the user without a picture.
    if previous and previous != result.public_id:
        deleted = await storage.delete_file(previous)
        if not deleted:
            logger.warning("Replaced avatar {} could not be deleted from Cloudinary.", previous)

    logger.info(
        "Avatar stored for {} — {}x{}, {} bytes, {}",
        user.email,
        result.width,
        result.height,
        result.bytes,
        result.format,
    )
    return user


async def remove_avatar(user: User) -> User:
    if not user.avatar_url:
        raise NotFoundError("There is no profile picture to remove.", error_code="no_avatar")

    public_id = user.avatar_public_id
    user.avatar_url = None
    user.avatar_public_id = None
    await user.save()

    if public_id:
        await storage.delete_file(public_id)
    return user


# -------------------------------------------------------------- addresses
def _find_address(user: User, address_id: str) -> Address:
    address = next((a for a in user.addresses if a.id == address_id), None)
    if address is None:
        raise NotFoundError("Address not found.", error_code="address_not_found")
    return address


def _apply_default(user: User, address: Address) -> None:
    """Only one address can be the default."""
    if not address.is_default:
        return
    for other in user.addresses:
        if other.id != address.id:
            other.is_default = False


async def add_address(user: User, payload: AddressInput) -> Address:
    address = Address(**payload.model_dump())
    # The first address saved is the default whether or not they said so.
    if not user.addresses:
        address.is_default = True

    user.addresses.append(address)
    _apply_default(user, address)
    await user.save()

    logger.info("Address added for {}", user.email)
    return address


async def update_address(user: User, address_id: str, payload: AddressUpdate) -> Address:
    address = _find_address(user, address_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(address, field, value)

    _apply_default(user, address)
    await user.save()
    return address


async def delete_address(user: User, address_id: str) -> None:
    address = _find_address(user, address_id)
    was_default = address.is_default

    user.addresses = [a for a in user.addresses if a.id != address_id]

    # Don't leave the list without a default.
    if was_default and user.addresses:
        user.addresses[0].is_default = True

    await user.save()
    logger.info("Address removed for {}", user.email)
