"""Admin management of Purohit (Vedic Priest) accounts."""

import asyncio
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.api.dependencies import AdminUser
from app.core.exceptions import NotFoundError
from app.models.purohit import Purohit
from app.models.purohit_application import PurohitApplication
from app.models.user import User
from app.schemas.common import ApiResponse, MessageResponse
from app.schemas.purohit import PurohitAdminOut, PurohitCreate, PurohitUpdate
from app.schemas.purohit_application import (
    PurohitApplicationApprovalResultOut,
    PurohitApplicationOut,
    PurohitApplicationRejectIn,
)
from app.services import purohit_application_service, purohit_service
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


def _app_to_out(app: PurohitApplication) -> PurohitApplicationOut:
    return PurohitApplicationOut(
        id=str(app.id),
        application_number=app.application_number,
        full_name=app.full_name,
        email=app.email,
        phone=app.phone,
        age=app.age,
        address=app.address,
        city=app.city,
        state=app.state,
        pincode=app.pincode,
        vedic_shakha=app.vedic_shakha,
        specializations=app.specializations,
        experience_years=app.experience_years,
        languages=app.languages,
        bio=app.bio,
        avatar_url=app.avatar_url,
        identity_proof_url=app.identity_proof_url,
        bank_account_number=app.bank_account_number,
        bank_ifsc=app.bank_ifsc,
        bank_account_holder=app.bank_account_holder,
        upi_id=app.upi_id,
        status=app.status,
        rejection_reason=app.rejection_reason,
        reviewed_at=app.reviewed_at,
        approved_user_id=str(app.approved_user_id) if app.approved_user_id else None,
        approved_purohit_id=str(app.approved_purohit_id) if app.approved_purohit_id else None,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


# ---------------------------------------------------------------------------
# Purohit Application Management (Admin)
# ---------------------------------------------------------------------------
@router.get(
    "/applications",
    response_model=ApiResponse[list[PurohitApplicationOut]],
    summary="List Purohit onboarding applications with filtering",
)
async def list_purohit_applications(
    admin: AdminUser,
    status: Annotated[str | None, Query(description="pending, approved, rejected, or all")] = None,
    search: Annotated[str | None, Query(description="Search by name, email, phone, city, application_number")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[PurohitApplicationOut]]:
    items, total = await purohit_application_service.list_applications(
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=[_app_to_out(it) for it in items],
        meta={"total": total, "limit": limit, "offset": offset},
    )


@router.get(
    "/applications/{app_id}",
    response_model=ApiResponse[PurohitApplicationOut],
    summary="Get detail of a Purohit application",
)
async def get_purohit_application_detail(
    app_id: str,
    admin: AdminUser,
) -> ApiResponse[PurohitApplicationOut]:
    app = await purohit_application_service.get_application(app_id)
    return ApiResponse(data=_app_to_out(app))


@router.post(
    "/applications/{app_id}/approve",
    response_model=ApiResponse[PurohitApplicationApprovalResultOut],
    summary="Approve Purohit application, create account & catalog, email credentials",
)
async def approve_purohit_application(
    app_id: str,
    admin: AdminUser,
) -> ApiResponse[PurohitApplicationApprovalResultOut]:
    user, profile, temp_pass, email_sent, dashboard_url = await purohit_application_service.approve_application(
        app_id=app_id,
        admin_user=admin,
    )
    out = PurohitApplicationApprovalResultOut(
        application_id=app_id,
        user_id=str(user.id),
        purohit_id=str(profile.id),
        display_name=profile.display_name,
        email=user.email,
        temporary_password=temp_pass,
        email_sent=email_sent,
        dashboard_url=dashboard_url,
        message=(
            f"Purohit {profile.display_name} approved successfully! Welcome email sent to {user.email}."
            if email_sent
            else f"Purohit {profile.display_name} approved successfully! Temporary credentials generated."
        ),
    )
    return ApiResponse(data=out, message=out.message)


@router.post(
    "/applications/{app_id}/reject",
    response_model=ApiResponse[PurohitApplicationOut],
    summary="Reject Purohit application with reason",
)
async def reject_purohit_application(
    app_id: str,
    payload: PurohitApplicationRejectIn,
    admin: AdminUser,
) -> ApiResponse[PurohitApplicationOut]:
    app = await purohit_application_service.reject_application(
        app_id=app_id,
        reason=payload.reason,
        admin_user=admin,
    )
    return ApiResponse(data=_app_to_out(app), message="Application has been marked as rejected.")


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
