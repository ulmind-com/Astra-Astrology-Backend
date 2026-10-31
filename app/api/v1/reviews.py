"""Reviews: leaving one, and reading what everybody else said."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, status

from app.api.dependencies import AdminUser, CurrentAstrologer, CurrentUser
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.astrologer import Astrologer
from app.models.review import Review
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.review import (
    HideReviewRequest,
    LeaveReviewRequest,
    PendingReview,
    ReviewOut,
    ReviewPage,
    ReviewSummary,
)
from app.services import reviews as service

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _out(review: Review, author_avatar: str | None = None) -> ReviewOut:
    return ReviewOut(
        id=str(review.id),
        astrologer_id=str(review.astrologer_id),
        kind=review.kind,
        stars=review.stars,
        text=review.text,
        author_name=review.author_name,
        author_avatar=author_avatar,
        session_id=str(review.session_id) if review.session_id else None,
        created_at=review.created_at,
    )


@router.post(
    "",
    response_model=ApiResponse[ReviewOut],
    status_code=status.HTTP_201_CREATED,
    summary="Leave a review for a consultation you had",
)
async def leave_review(
    payload: LeaveReviewRequest, user: CurrentUser
) -> ApiResponse[ReviewOut]:
    if not PydanticObjectId.is_valid(payload.session_id):
        raise BadRequestError("That consultation id is not valid.", error_code="bad_id")

    review = await service.leave(
        user=user,
        kind=payload.kind,
        session_id=PydanticObjectId(payload.session_id),
        stars=payload.stars,
        text=payload.text,
    )
    return ApiResponse(message="Thanks for the review.", data=_out(review))


@router.get(
    "/pending",
    response_model=ApiResponse[list[PendingReview]],
    summary="Consultations I have finished but not reviewed",
)
async def pending(user: CurrentUser) -> ApiResponse[list[PendingReview]]:
    """What the prompt is built from.

    Looked up rather than stored against the session, so a review written on a
    phone stops the prompt appearing on a laptop.
    """
    items = await service.pending_for(user)
    return ApiResponse(
        message="Pending reviews fetched.",
        data=[PendingReview(**item) for item in items],
    )


@router.get(
    "/mine",
    response_model=ApiResponse[list[ReviewOut]],
    summary="Reviews I have written",
)
async def my_reviews(user: CurrentUser) -> ApiResponse[list[ReviewOut]]:
    return ApiResponse(
        message="Reviews fetched.", data=[_out(r) for r in await service.mine(user.id)]
    )


@router.get(
    "/astrologer/me",
    response_model=ApiResponse[ReviewPage],
    summary="All client reviews and feedback left for me as an astrologer",
)
async def my_astrologer_reviews(
    astrologer: CurrentAstrologer,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ApiResponse[ReviewPage]:
    items, total = await service.for_astrologer(astrologer.id, skip=skip, limit=limit)
    user_ids = [r.user_id for r in items if r.user_id]
    user_map = {}
    if user_ids:
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        user_map = {u.id: u for u in users}

    review_outs = [
        _out(
            r,
            author_avatar=user_map.get(r.user_id).avatar_url
            if user_map.get(r.user_id)
            else None,
        )
        for r in items
    ]
    return ApiResponse(
        message="Reviews fetched.",
        data=ReviewPage(
            items=review_outs,
            total=total,
            summary=ReviewSummary(
                average=astrologer.rating.average,
                count=astrologer.rating.count,
                breakdown=await service.breakdown(astrologer.id),
            ),
        ),
    )


@router.get(
    "/astrologers/{astrologer_id}",
    response_model=ApiResponse[ReviewPage],
    summary="What people said about an astrologer",
)
async def for_astrologer(
    astrologer_id: str,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> ApiResponse[ReviewPage]:
    """Public. This is the whole point of a review."""
    profile = await Astrologer.find_one(Astrologer.slug == astrologer_id)
    if profile is None and PydanticObjectId.is_valid(astrologer_id):
        profile = await Astrologer.get(PydanticObjectId(astrologer_id))

    if profile is None or not profile.is_listed:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    items, total = await service.for_astrologer(profile.id, skip=skip, limit=limit)
    user_ids = [r.user_id for r in items if r.user_id]
    user_map = {}
    if user_ids:
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        user_map = {u.id: u for u in users}

    review_outs = [
        _out(
            r,
            author_avatar=user_map.get(r.user_id).avatar_url
            if user_map.get(r.user_id)
            else None,
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
                breakdown=await service.breakdown(profile.id),
            ),
        ),
    )


# -------------------------------------------------------------------- admin
admin_router = APIRouter(prefix="/admin/reviews", tags=["admin"])


@admin_router.patch(
    "/{review_id}/hidden",
    response_model=ApiResponse[ReviewOut],
    summary="Hide a review, or put it back",
)
async def set_hidden(
    review_id: PydanticObjectId, payload: HideReviewRequest, admin: AdminUser
) -> ApiResponse[ReviewOut]:
    """Hiding is not deleting.

    The row stays — it is still a record of what was said — but it stops
    counting towards the average and stops being shown.
    """
    review = await service.set_hidden(
        review_id=review_id, hidden=payload.hidden, reason=payload.reason
    )
    return ApiResponse(
        message="Review hidden." if payload.hidden else "Review restored.",
        data=_out(review),
    )


@admin_router.get(
    "/astrologers/{astrologer_id}/recalculate",
    response_model=ApiResponse[dict],
    summary="Rebuild an astrologer's rating from their reviews",
)
async def recalculate(
    astrologer_id: PydanticObjectId, admin: AdminUser
) -> ApiResponse[dict]:
    return ApiResponse(
        message="Rating rebuilt.", data=await service.recalculate(astrologer_id)
    )
