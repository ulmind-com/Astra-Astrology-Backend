"""The public astrologer directory, and an astrologer's own profile.

Route order matters: `/me` is declared before `/{identifier}`, so the literal
path wins over the slug lookup.
"""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, File, Header, Query, UploadFile, status

from app.api.dependencies import AstrologerUser, CurrentAstrologer, CurrentUser, OptionalUser
from app.core.exceptions import NotFoundError
from app.models.astrologer import Astrologer
from app.models.enums import ConsultationMode, Skill
from app.models.user import User
from app.schemas.astrologer import (
    AstrologerFilters,
    AstrologerProfile,
    AstrologerPublic,
    AstrologerUpdate,
    AvailabilityUpdate,
    FavoriteStatusResult,
    FavoriteToggleResult,
    GalleryUploadResult,
)
from app.schemas.common import ApiResponse, MessageResponse, Paginated
from app.schemas.review import ReviewOut, ReviewPage, ReviewSummary
from app.schemas.wallet import ConsultationQuote
from app.services import astrologer as astrologer_service
from app.services import billing
from app.services import favorite as favorite_service
from app.services import reviews as review_service
from app.services import settings as settings_service
from app.services import wallet as wallet_service

router = APIRouter(prefix="/astrologers", tags=["astrologers"])


# ======================================================== the astrologer's own
@router.get("/me", response_model=ApiResponse[AstrologerProfile], summary="My profile")
async def get_my_profile(
    user: AstrologerUser, profile: CurrentAstrologer
) -> ApiResponse[AstrologerProfile]:
    fresh = await Astrologer.find_one(Astrologer.user_id == user.id)
    if fresh is not None:
        profile = fresh
    return ApiResponse(
        message="Profile fetched.", data=astrologer_service.to_profile(user, profile)
    )


@router.get("/me/reviews", response_model=ApiResponse[ReviewPage], summary="My client reviews")
async def get_my_reviews(
    _: AstrologerUser,
    profile: CurrentAstrologer,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ApiResponse[ReviewPage]:
    items, total = await review_service.for_astrologer(profile.id, skip=skip, limit=limit)
    user_ids = [r.user_id for r in items if r.user_id]
    user_map = {}
    if user_ids:
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        user_map = {u.id: u for u in users}

    review_outs = [
        ReviewOut(
            id=str(r.id),
            astrologer_id=str(r.astrologer_id),
            kind=r.kind,
            stars=r.stars,
            text=r.text,
            author_name=r.author_name,
            author_avatar=user_map.get(r.user_id).avatar_url
            if user_map.get(r.user_id)
            else None,
            session_id=str(r.session_id) if r.session_id else None,
            created_at=r.created_at,
        )
        for r in items
    ]
    return ApiResponse(
        message="Reviews fetched.",
        data=ReviewPage(
            items=review_outs,
            total=total,
            summary=ReviewSummary(
                average=profile.rating.average,
                count=profile.rating.count,
                breakdown=await review_service.breakdown(profile.id),
            ),
        ),
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


# ------------------------------------------------------------------ banner
@router.post(
    "/me/banner",
    response_model=ApiResponse[AstrologerProfile],
    summary="Upload or replace my card banner",
)
async def upload_my_banner(
    user: AstrologerUser,
    profile: CurrentAstrologer,
    file: UploadFile = File(description="JPEG, PNG, WebP, GIF or HEIC"),
) -> ApiResponse[AstrologerProfile]:
    profile = await astrologer_service.set_banner_image(user, profile, file)
    return ApiResponse(message="Banner updated.", data=astrologer_service.to_profile(user, profile))


@router.delete(
    "/me/banner",
    response_model=ApiResponse[AstrologerProfile],
    summary="Remove my card banner",
)
async def delete_my_banner(
    user: AstrologerUser, profile: CurrentAstrologer
) -> ApiResponse[AstrologerProfile]:
    profile = await astrologer_service.remove_banner_image(profile)
    return ApiResponse(message="Banner removed.", data=astrologer_service.to_profile(user, profile))


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
        data=GalleryUploadResult(image=image, gallery=profile.gallery or []),
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


# ============================================================ favorites
@router.get(
    "/favorites/my",
    response_model=ApiResponse[list[AstrologerPublic]],
    summary="My favorited astrologers",
)
async def my_favorite_astrologers(user: CurrentUser) -> ApiResponse[list[AstrologerPublic]]:
    astros = await favorite_service.list_user_favorites(user)
    public_list = [await astrologer_service.to_public(a) for a in astros]
    return ApiResponse(message=f"{len(public_list)} favorite astrologer(s).", data=public_list)


@router.post(
    "/{identifier}/favorite",
    response_model=ApiResponse[FavoriteToggleResult],
    summary="Toggle favorite status for an astrologer",
)
async def toggle_favorite(
    identifier: str, user: CurrentUser
) -> ApiResponse[FavoriteToggleResult]:
    is_fav, count = await favorite_service.toggle_favorite(user, identifier)
    msg = "Added to sacred favorites." if is_fav else "Removed from favorites."
    return ApiResponse(
        message=msg,
        data=FavoriteToggleResult(is_favorite=is_fav, favorites_count=count, message=msg),
    )


@router.get(
    "/{identifier}/favorite",
    response_model=ApiResponse[FavoriteStatusResult],
    summary="Check favorite status and count for an astrologer",
)
async def get_favorite_status(
    identifier: str, user: OptionalUser
) -> ApiResponse[FavoriteStatusResult]:
    is_fav, count = await favorite_service.get_favorite_status(user, identifier)
    return ApiResponse(
        message="Favorite status fetched.",
        data=FavoriteStatusResult(is_favorite=is_fav, favorites_count=count),
    )


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
