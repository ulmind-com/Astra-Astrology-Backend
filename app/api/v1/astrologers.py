"""The public astrologer directory, and an astrologer's own profile.

Route order matters: `/me` is declared before `/{identifier}`, so the literal
path wins over the slug lookup.
"""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, File, Header, Query, UploadFile, status

from app.api.dependencies import AstrologerUser, CurrentAstrologer, CurrentUser
from app.core.exceptions import NotFoundError
from app.models.astrologer import Astrologer
from app.models.enums import ConsultationMode, Skill
from app.schemas.astrologer import (
    AstrologerFilters,
    AstrologerProfile,
    AstrologerPublic,
    AstrologerUpdate,
    AvailabilityUpdate,
    GalleryUploadResult,
)
from app.schemas.common import ApiResponse, MessageResponse, Paginated
from app.schemas.wallet import ConsultationQuote
from app.services import astrologer as astrologer_service
from app.services import billing
from app.services import settings as settings_service
from app.services import wallet as wallet_service

router = APIRouter(prefix="/astrologers", tags=["astrologers"])


# ======================================================== the astrologer's own
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


# ------------------------------------------------------------------- photo
@router.post(
    "/me/image",
    response_model=ApiResponse[AstrologerProfile],
    summary="Upload or replace my photo",
)
async def upload_my_image(
    user: AstrologerUser,
    profile: CurrentAstrologer,
    file: UploadFile = File(description="JPEG, PNG, WebP, GIF or HEIC"),
) -> ApiResponse[AstrologerProfile]:
    profile = await astrologer_service.set_profile_image(user, profile, file)
    return ApiResponse(message="Photo updated.", data=astrologer_service.to_profile(user, profile))


@router.delete(
    "/me/image",
    response_model=ApiResponse[AstrologerProfile],
    summary="Remove my photo",
)
async def delete_my_image(
    user: AstrologerUser, profile: CurrentAstrologer
) -> ApiResponse[AstrologerProfile]:
    profile = await astrologer_service.remove_profile_image(profile)
    return ApiResponse(message="Photo removed.", data=astrologer_service.to_profile(user, profile))


# ----------------------------------------------------------------- gallery
@router.post(
    "/me/gallery",
    response_model=ApiResponse[GalleryUploadResult],
    status_code=status.HTTP_201_CREATED,
    summary="Add an image to my gallery",
)
async def add_gallery_image(
    user: AstrologerUser,
    profile: CurrentAstrologer,
    file: UploadFile = File(description="JPEG, PNG, WebP, GIF or HEIC"),
) -> ApiResponse[GalleryUploadResult]:
    image, profile = await astrologer_service.add_gallery_image(user, profile, file)
    return ApiResponse(
        message="Image added to your gallery.",
        data=GalleryUploadResult(image=image, gallery=profile.gallery),
    )


@router.delete(
    "/me/gallery/{public_id:path}",
    response_model=MessageResponse,
    summary="Remove an image from my gallery",
)
async def remove_gallery_image(
    public_id: str, user: AstrologerUser, profile: CurrentAstrologer
) -> MessageResponse:
    await astrologer_service.remove_gallery_image(profile, public_id)
    return MessageResponse(message="Image removed from your gallery.")


# ============================================================ public directory
@router.get(
    "",
    response_model=ApiResponse[Paginated[AstrologerPublic]],
    summary="Browse astrologers — online first, then featured",
)
async def list_astrologers(
    search: Annotated[str | None, Query(description="Name, tagline or speciality")] = None,
    skill: Annotated[Skill | None, Query()] = None,
    language: Annotated[str | None, Query()] = None,
    mode: Annotated[ConsultationMode | None, Query()] = None,
    online_only: Annotated[bool, Query()] = False,
    featured_only: Annotated[bool, Query()] = False,
    min_experience: Annotated[int | None, Query(ge=0, le=90)] = None,
    max_coins_per_minute: Annotated[
        int | None, Query(ge=1, description="Chat rate ceiling, in coins a minute")
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> ApiResponse[Paginated[AstrologerPublic]]:
    filters = AstrologerFilters(
        search=search,
        skill=skill,
        language=language,
        mode=mode,
        online_only=online_only,
        featured_only=featured_only,
        min_experience=min_experience,
        max_coins_per_minute=max_coins_per_minute,
    )
    page_of = await astrologer_service.list_public(filters, page, limit)
    return ApiResponse(message=f"{page_of.meta.total} astrologer(s) found.", data=page_of)


@router.get(
    "/{identifier}",
    response_model=ApiResponse[AstrologerPublic],
    summary="One astrologer, by slug or id",
)
async def get_astrologer(identifier: str) -> ApiResponse[AstrologerPublic]:
    return ApiResponse(
        message="Astrologer fetched.", data=await astrologer_service.get_public(identifier)
    )


@router.get(
    "/{astrologer_id}/quote",
    response_model=ApiResponse[ConsultationQuote],
    summary="What a session with this astrologer costs me",
)
async def consultation_quote(
    astrologer_id: PydanticObjectId,
    mode: ConsultationMode,
    user: CurrentUser,
) -> ApiResponse[ConsultationQuote]:
    """Drives the "how long do you want to talk?" picker.

    Returned before anything is booked, so the choice is made against real
    numbers rather than a guess the server then refuses.
    """
    profile = await Astrologer.get(astrologer_id)
    if profile is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    price = await billing.price_for(profile, mode)
    platform = await settings_service.get_settings()
    wallet = await wallet_service.get_or_create_wallet(user.id)

    return ApiResponse(
        message="Quote.",
        data=ConsultationQuote(
            mode=mode,
            coins_per_minute=price.coins_per_minute,
            balance_coins=wallet.balance_coins,
            affordable_minutes=billing.affordable_minutes(
                wallet.balance_coins, price.coins_per_minute
            ),
            min_minutes=platform.min_session_minutes,
            max_minutes=platform.max_session_minutes,
        ),
    )


# -------------------------------------------------------------- maintenance
maintenance_router = APIRouter(prefix="/internal", tags=["internal"])


@maintenance_router.post(
    "/presence/sweep",
    response_model=ApiResponse[dict],
    summary="Settle the stored online flag for anyone who stopped reporting in",
    include_in_schema=False,
)
async def sweep_presence(
    x_internal_key: Annotated[str | None, Header()] = None,
) -> ApiResponse[dict]:
    """Optional housekeeping.

    Nothing depends on this: every read applies the same TTL, so the site is
    correct whether or not this ever runs. It exists so MongoDB stops claiming
    someone is online once they are plainly gone, and so one last update
    reaches anyone subscribed to the live mirror.
    """
    import hmac

    from app.core.config import settings
    from app.core.exceptions import ForbiddenError
    from app.services import presence

    if not x_internal_key or not hmac.compare_digest(x_internal_key, settings.SECRET_KEY):
        raise ForbiddenError("Not allowed.", error_code="forbidden")

    return ApiResponse(message="Swept.", data=await presence.sweep())
