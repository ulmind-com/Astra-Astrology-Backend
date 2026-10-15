"""The signed-in user's own profile."""

from fastapi import APIRouter, File, UploadFile, status

from app.api.dependencies import CurrentUser
from app.models.profile import Address
from app.schemas.common import ApiResponse, MessageResponse
from app.schemas.user import AddressInput, AddressUpdate, ProfileUpdate, UserProfile
from app.services import profile as profile_service

router = APIRouter(prefix="/users", tags=["profile"])


# ------------------------------------------------------------------ profile
@router.get("/me", response_model=ApiResponse[UserProfile], summary="My full profile")
async def get_my_profile(user: CurrentUser) -> ApiResponse[UserProfile]:
    return ApiResponse(message="Profile fetched.", data=profile_service.to_profile(user))


@router.patch(
    "/me",
    response_model=ApiResponse[UserProfile],
    summary="Update my profile — omit a field to leave it, send null to clear it",
)
async def update_my_profile(payload: ProfileUpdate, user: CurrentUser) -> ApiResponse[UserProfile]:
    updated = await profile_service.update_profile(user, payload)
    return ApiResponse(message="Profile updated.", data=profile_service.to_profile(updated))


# ------------------------------------------------------------------- avatar
@router.post(
    "/me/avatar",
    response_model=ApiResponse[UserProfile],
    summary="Upload or replace my profile picture",
)
async def upload_avatar(
    user: CurrentUser, file: UploadFile = File(description="JPEG, PNG, WebP, GIF or HEIC")
) -> ApiResponse[UserProfile]:
    updated = await profile_service.set_avatar(user, file)
    return ApiResponse(message="Profile picture updated.", data=profile_service.to_profile(updated))


@router.delete(
    "/me/avatar",
    response_model=ApiResponse[UserProfile],
    summary="Remove my profile picture",
)
async def delete_avatar(user: CurrentUser) -> ApiResponse[UserProfile]:
    updated = await profile_service.remove_avatar(user)
    return ApiResponse(message="Profile picture removed.", data=profile_service.to_profile(updated))


# ---------------------------------------------------------------- addresses
@router.get(
    "/me/addresses",
    response_model=ApiResponse[list[Address]],
    summary="My delivery addresses",
)
async def list_addresses(user: CurrentUser) -> ApiResponse[list[Address]]:
    return ApiResponse(message=f"{len(user.addresses)} address(es).", data=user.addresses)


@router.post(
    "/me/addresses",
    response_model=ApiResponse[Address],
    status_code=status.HTTP_201_CREATED,
    summary="Add a delivery address",
)
async def add_address(payload: AddressInput, user: CurrentUser) -> ApiResponse[Address]:
    address = await profile_service.add_address(user, payload)
    return ApiResponse(message="Address added.", data=address)


@router.patch(
    "/me/addresses/{address_id}",
    response_model=ApiResponse[Address],
    summary="Update a delivery address",
)
async def update_address(
    address_id: str, payload: AddressUpdate, user: CurrentUser
) -> ApiResponse[Address]:
    address = await profile_service.update_address(user, address_id, payload)
    return ApiResponse(message="Address updated.", data=address)


@router.delete(
    "/me/addresses/{address_id}",
    response_model=MessageResponse,
    summary="Delete a delivery address",
)
async def delete_address(address_id: str, user: CurrentUser) -> MessageResponse:
    await profile_service.delete_address(user, address_id)
    return MessageResponse(message="Address deleted.")
