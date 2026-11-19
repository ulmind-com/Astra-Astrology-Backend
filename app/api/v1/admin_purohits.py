"""Admin management of Purohit (Vedic Priest) accounts."""

import asyncio
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.api.dependencies import AdminUser
from app.core.exceptions import NotFoundError
from app.models.purohit import Purohit
from app.models.user import User
from app.schemas.common import ApiResponse, MessageResponse
from app.schemas.purohit import PurohitAdminOut, PurohitCreate, PurohitUpdate
from app.services import purohit_service
from app.services.storage import ALLOWED_IMAGE_TYPES, safe_delete_cloudinary_image, upload_file

router = APIRouter(prefix="/admin/purohits", tags=["admin: purohits"])

PUROHIT_AVATAR_TRANSFORMATION = [
    {"width": 800, "height": 800, "crop": "fill", "gravity": "face"},
    {"quality": "auto:good"},
    {"fetch_format": "auto"},
]


@router.post(
    "/upload-avatar",
    response_model=ApiResponse[dict[str, str]],
    summary="Upload a Purohit avatar image with auto WebP compression & Cloudinary storage",
)
async def upload_purohit_avatar(
    file: UploadFile = File(...),
    previous_avatar_url: Annotated[str | None, Form()] = None,
    admin: AdminUser = None,
) -> ApiResponse[dict[str, str]]:
    """Uploads an avatar to Cloudinary in the 'purohits' folder.
    If previous_avatar_url is provided, cleans up the old Cloudinary asset to optimize storage.
    """
    result = await upload_file(
        file,
        folder="purohits",
        allowed_types=ALLOWED_IMAGE_TYPES,
        transformation=PUROHIT_AVATAR_TRANSFORMATION,
        image_format="webp",
    )

    # If the user is replacing an avatar previously uploaded in this session,
    # safely clean up the replaced asset from Cloudinary
    if previous_avatar_url and "cloudinary.com" in previous_avatar_url:
        asyncio.create_task(safe_delete_cloudinary_image(previous_avatar_url))

    return ApiResponse.ok(
        data={
            "url": result.secure_url,
            "public_id": result.public_id,
            "format": result.format or "webp",
        },
        message="Avatar uploaded and compressed successfully.",
    )


@router.post(
    "/delete-avatar",
    response_model=ApiResponse[dict[str, bool]],
    summary="Remove a Purohit avatar from Cloudinary",
)
async def delete_purohit_avatar(
    url: Annotated[str, Query(description="Cloudinary avatar URL to remove")],
    admin: AdminUser = None,
) -> ApiResponse[dict[str, bool]]:
    deleted = await safe_delete_cloudinary_image(url)
    return ApiResponse.ok(
        data={"deleted": deleted},
        message="Avatar removed from cloud storage.",
    )


class PurohitCreatedOut(PurohitAdminOut):
    temporary_password: str
    email_sent: bool


@router.post(
    "",
    response_model=ApiResponse[PurohitCreatedOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create a Purohit account and email them their initial password",
)
async def create_purohit(
    payload: PurohitCreate, admin: AdminUser
) -> ApiResponse[PurohitCreatedOut]:
    user, profile, password, email_sent = await purohit_service.create_purohit_by_admin(payload)

    out = PurohitCreatedOut(
        id=str(profile.id),
        user_id=str(user.id),
        display_name=profile.display_name,
        slug=profile.slug,
        title=profile.title,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        phone=profile.phone,
        email=profile.email,
        address=profile.address,
        city=profile.city,
        state=profile.state,
        pincode=profile.pincode,
        experience_years=profile.experience_years,
        languages=profile.languages,
        is_online=profile.is_online,
        is_verified=profile.is_verified,
        pujas=[p.model_dump() for p in profile.pujas],
        rating=profile.rating,
        total_pujas_performed=profile.total_pujas_performed,
        starting_price_inr=purohit_service._get_starting_price(profile),
        created_at=profile.created_at,
        temporary_password=password,
        email_sent=email_sent,
    )

    msg = (
        f"Purohit created successfully. Sign-in credentials emailed to {user.email}."
        if email_sent
        else "Purohit created successfully. Welcome email could not be sent; provide password manually."
    )
    return ApiResponse(message=msg, data=out)


@router.get(
    "",
    response_model=ApiResponse[list[PurohitAdminOut]],
    summary="List all registered Purohits for admin",
)
async def list_purohits(
    admin: AdminUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[PurohitAdminOut]]:
    cursor = Purohit.find().sort("-created_at").skip(offset).limit(limit)
    items = await cursor.to_list()

    out = [
        PurohitAdminOut(
            id=str(p.id),
            user_id=str(p.user_id),
            display_name=p.display_name,
            slug=p.slug,
            title=p.title,
            bio=p.bio,
            avatar_url=p.avatar_url,
            phone=p.phone,
            email=p.email,
            address=p.address,
            city=p.city,
            state=p.state,
            pincode=p.pincode,
            experience_years=p.experience_years,
            languages=p.languages,
            is_online=p.is_online,
            is_verified=p.is_verified,
            pujas=[it.model_dump() for it in p.pujas],
            rating=p.rating,
            total_pujas_performed=p.total_pujas_performed,
            starting_price_inr=purohit_service._get_starting_price(p),
            created_at=p.created_at,
        )
        for p in items
    ]
    return ApiResponse(data=out)


@router.get(
    "/{purohit_id}",
    response_model=ApiResponse[PurohitAdminOut],
    summary="Fetch admin detail of a Purohit",
)
async def get_purohit_detail(
    purohit_id: PydanticObjectId, admin: AdminUser
) -> ApiResponse[PurohitAdminOut]:
    profile = await Purohit.get(purohit_id)
    if profile is None:
        raise NotFoundError("Purohit not found.", error_code="purohit_not_found")

    out = PurohitAdminOut(
        id=str(profile.id),
        user_id=str(profile.user_id),
        display_name=profile.display_name,
        slug=profile.slug,
        title=profile.title,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        phone=profile.phone,
        email=profile.email,
        address=profile.address,
        city=profile.city,
        state=profile.state,
        pincode=profile.pincode,
        experience_years=profile.experience_years,
        languages=profile.languages,
        is_online=profile.is_online,
        is_verified=profile.is_verified,
        pujas=[it.model_dump() for it in profile.pujas],
        rating=profile.rating,
        total_pujas_performed=profile.total_pujas_performed,
        starting_price_inr=purohit_service._get_starting_price(profile),
        created_at=profile.created_at,
    )
    return ApiResponse(data=out)


@router.put(
    "/{purohit_id}",
    response_model=ApiResponse[PurohitAdminOut],
    summary="Update a Purohit's details as admin",
)
async def update_purohit(
    purohit_id: PydanticObjectId, payload: PurohitUpdate, admin: AdminUser
) -> ApiResponse[PurohitAdminOut]:
    profile = await Purohit.get(purohit_id)
    if profile is None:
        raise NotFoundError("Purohit not found.", error_code="purohit_not_found")

    old_avatar = profile.avatar_url
    update_data = payload.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(profile, k, v)
    await profile.save()

    # If avatar was replaced or removed, purge the old Cloudinary asset
    new_avatar = profile.avatar_url
    if "avatar_url" in update_data and old_avatar and old_avatar != new_avatar:
        asyncio.create_task(safe_delete_cloudinary_image(old_avatar))

    # Also keep the linked User's avatar in sync
    if "avatar_url" in update_data and profile.user_id:
        user = await User.get(profile.user_id)
        if user and user.avatar_url != new_avatar:
            user.avatar_url = new_avatar
            await user.save()

    out = PurohitAdminOut(
        id=str(profile.id),
        user_id=str(profile.user_id),
        display_name=profile.display_name,
        slug=profile.slug,
        title=profile.title,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        phone=profile.phone,
        email=profile.email,
        address=profile.address,
        city=profile.city,
        state=profile.state,
        pincode=profile.pincode,
        experience_years=profile.experience_years,
        languages=profile.languages,
        is_online=profile.is_online,
        is_verified=profile.is_verified,
        pujas=[it.model_dump() for it in profile.pujas],
        rating=profile.rating,
        total_pujas_performed=profile.total_pujas_performed,
        starting_price_inr=purohit_service._get_starting_price(profile),
        created_at=profile.created_at,
    )
    return ApiResponse(message="Purohit profile updated successfully.", data=out)


@router.delete(
    "/{purohit_id}",
    response_model=MessageResponse,
    summary="Deactivate or remove a Purohit",
)
async def delete_purohit(purohit_id: PydanticObjectId, admin: AdminUser) -> MessageResponse:
    profile = await Purohit.get(purohit_id)
    if profile is None:
        raise NotFoundError("Purohit not found.", error_code="purohit_not_found")

    user = await User.get(profile.user_id)
    if user:
        user.is_active = False
        await user.save()

    profile.is_verified = False
    profile.is_online = False
    await profile.save()

    return MessageResponse(message="Purohit deactivated successfully.")
