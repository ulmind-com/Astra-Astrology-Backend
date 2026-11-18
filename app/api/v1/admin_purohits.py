"""Admin management of Purohit (Vedic Priest) accounts."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, status

from app.api.dependencies import AdminUser
from app.core.exceptions import NotFoundError
from app.models.purohit import Purohit
from app.models.user import User
from app.schemas.common import ApiResponse, MessageResponse
from app.schemas.purohit import PurohitAdminOut, PurohitCreate, PurohitUpdate
from app.services import purohit_service

router = APIRouter(prefix="/admin/purohits", tags=["admin: purohits"])


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

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
    await profile.save()

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
