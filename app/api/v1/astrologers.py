"""An astrologer's own profile."""

from fastapi import APIRouter

from app.api.dependencies import AstrologerUser, CurrentAstrologer
from app.schemas.astrologer import AstrologerProfile, AstrologerUpdate, AvailabilityUpdate
from app.schemas.common import ApiResponse
from app.services import astrologer as astrologer_service

router = APIRouter(prefix="/astrologers", tags=["astrologer"])


@router.get("/me", response_model=ApiResponse[AstrologerProfile], summary="My profile")
async def get_my_profile(
    user: AstrologerUser, profile: CurrentAstrologer
) -> ApiResponse[AstrologerProfile]:
    return ApiResponse(
        message="Profile fetched.", data=astrologer_service.to_profile(user, profile)
    )


@router.patch(
    "/me",
    response_model=ApiResponse[AstrologerProfile],
    summary="Update my profile — omit a field to leave it, send null to clear it",
)
async def update_my_profile(
    payload: AstrologerUpdate, user: AstrologerUser, profile: CurrentAstrologer
) -> ApiResponse[AstrologerProfile]:
    user, profile = await astrologer_service.update_profile(user, profile, payload)
    return ApiResponse(
        message="Profile updated.", data=astrologer_service.to_profile(user, profile)
    )


@router.patch(
    "/me/availability",
    response_model=ApiResponse[AstrologerProfile],
    summary="Go online or offline, and toggle chat and call",
)
async def update_my_availability(
    payload: AvailabilityUpdate, user: AstrologerUser, profile: CurrentAstrologer
) -> ApiResponse[AstrologerProfile]:
    profile = await astrologer_service.update_availability(profile, payload)
    return ApiResponse(
        message="Availability updated.", data=astrologer_service.to_profile(user, profile)
    )
