"""Product Review & Verified Buyer Rating Service.

Enforces:
1. Only users with a successfully DELIVERED order containing the product can submit a review.
2. Strict lifetime uniqueness: exactly 1 review per product per devotee (enforced by DB index).
3. Ratings breakdown (5, 4, 3, 2, 1 star percentages) and atomic recalculation of Product.average_rating and Product.review_count.
4. Devotee photo uploads (consecrated parcel/remedy proofs).
5. Community helpfulness voting with deduplication.
6. Admin moderation (hide/show, delete).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from beanie import PydanticObjectId
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.security import safe_regex_pattern

from app.models.enums import ShopOrderStatus
from app.models.shop import Product, ProductReview, ShopOrder
from app.models.user import User
from app.schemas.shop import (
    AdminProductReviewListResponse,
    AdminReviewModerationUpdate,
    ProductRatingBreakdown,
    ProductReviewCreate,
    ProductReviewOut,
    ProductReviewsResponse,
    ProductReviewUpdate,
    ReviewEligibilityResponse,
)

logger = logging.getLogger("astra.shop.review_service")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _review_to_out(review: ProductReview, current_user_id: PydanticObjectId | None = None) -> ProductReviewOut:
    is_helpful = False
    if current_user_id and current_user_id in review.helpful_user_ids:
        is_helpful = True

    return ProductReviewOut(
        id=str(review.id),
        product_id=str(review.product_id),
        product_slug=review.product_slug,
        user_id=str(review.user_id),
        order_id=str(review.order_id),
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        images=review.images or [],
        is_verified_buyer=review.is_verified_buyer,
        author_name=review.author_name,
        author_avatar=review.author_avatar,
        helpful_count=review.helpful_count,
        is_helpful_by_me=is_helpful,
        is_hidden=review.is_hidden,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


async def _resolve_product(product_slug_or_id: str) -> Product | None:
    """Find product by ObjectId or slug."""
    product = None
    if PydanticObjectId.is_valid(product_slug_or_id):
        product = await Product.get(PydanticObjectId(product_slug_or_id))
    if not product:
        product = await Product.find_one(Product.slug == product_slug_or_id, Product.is_deleted == False)
    return product


async def check_review_eligibility(
    product_slug_or_id: str,
    user_id: PydanticObjectId,
) -> ReviewEligibilityResponse:
    """Check if the user is eligible to review a product.
    
    Rules:
    - User must have an order with order_status == DELIVERED containing this product.
    - User must NOT have already reviewed this product (lifetime 1-review rule).
    """
    product = await _resolve_product(product_slug_or_id)
    if not product:
        return ReviewEligibilityResponse(
            can_review=False,
            already_reviewed=False,
            is_delivered_buyer=False,
            reason="Product not found",
        )

    # 1. Has user already reviewed this product?
    existing = await ProductReview.find_one(
        ProductReview.product_id == product.id,
        ProductReview.user_id == user_id,
    )
    if existing:
        return ReviewEligibilityResponse(
            can_review=False,
            already_reviewed=True,
            is_delivered_buyer=True,
            reason="You have already submitted a review for this sacred remedy. Each devotee may submit exactly 1 review per product.",
            existing_review=_review_to_out(existing, user_id),
            order_id=str(existing.order_id),
        )

    # 2. Check for a DELIVERED order containing this product
    delivered_order = await ShopOrder.find_one(
        ShopOrder.user_id == user_id,
        ShopOrder.order_status == ShopOrderStatus.DELIVERED,
        {"items.product_id": product.id},
    )

    if not delivered_order:
        # Check if an order exists in progress (in-transit, sanctifying, placed)
        in_progress_order = await ShopOrder.find_one(
            ShopOrder.user_id == user_id,
            ShopOrder.order_status != ShopOrderStatus.CANCELLED,
            ShopOrder.order_status != ShopOrderStatus.RETURNED,
            ShopOrder.order_status != ShopOrderStatus.RTO,
            ShopOrder.order_status != ShopOrderStatus.EXPIRED,
            {"items.product_id": product.id},
        )
        if in_progress_order:
            reason = "Your order is currently being consecrated or in transit. You will be eligible to submit your review once the parcel is successfully delivered."
        else:
            reason = "Only verified buyers who have received delivery of this consecrated item can submit a review."

        return ReviewEligibilityResponse(
            can_review=False,
            already_reviewed=False,
            is_delivered_buyer=False,
            reason=reason,
        )

    return ReviewEligibilityResponse(
        can_review=True,
        already_reviewed=False,
        is_delivered_buyer=True,
        reason=None,
        order_id=str(delivered_order.id),
    )


async def recalculate_product_ratings(product_id: PydanticObjectId) -> None:
    """Recalculate average rating and review count for a product from active reviews."""
    product = await Product.get(product_id)
    if not product:
        return

    active_reviews = await ProductReview.find(
        ProductReview.product_id == product_id,
        ProductReview.is_hidden == False,
    ).to_list()

    total = len(active_reviews)
    if total > 0:
        avg = round(sum(r.rating for r in active_reviews) / total, 1)
    else:
        avg = 5.0

    product.average_rating = avg
    product.review_count = total
    await product.save()


async def create_product_review(
    product_slug_or_id: str,
    payload: ProductReviewCreate,
    user: User,
) -> ProductReviewOut:
    """Submit a verified buyer review."""
    product = await _resolve_product(product_slug_or_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    eligibility = await check_review_eligibility(str(product.id), user.id)
    if not eligibility.can_review:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=eligibility.reason or "You are not eligible to review this product.",
        )

    author_name = getattr(user, "full_name", None) or getattr(user, "name", None) or "Devotee"
    # Format name for customer privacy e.g. "Rahul S."
    parts = author_name.strip().split()
    if len(parts) > 1:
        masked_name = f"{parts[0]} {parts[-1][0]}."
    else:
        masked_name = author_name

    review = ProductReview(
        product_id=product.id,
        product_slug=product.slug,
        user_id=user.id,
        order_id=PydanticObjectId(eligibility.order_id),
        rating=payload.rating,
        title=payload.title.strip() if payload.title else None,
        comment=payload.comment.strip(),
        images=payload.images[:5] if payload.images else [],
        is_verified_buyer=True,
        author_name=masked_name,
        author_avatar=getattr(user, "avatar_url", None),
    )

    try:
        await review.insert()
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted a review for this remedy.",
        )

    # Recalculate product rating
    await recalculate_product_ratings(product.id)

    return _review_to_out(review, user.id)


async def update_my_review(
    product_slug_or_id: str,
    payload: ProductReviewUpdate,
    user: User,
) -> ProductReviewOut:
    """Update user's existing review for a product."""
    product = await _resolve_product(product_slug_or_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    review = await ProductReview.find_one(
        ProductReview.product_id == product.id,
        ProductReview.user_id == user.id,
    )
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")

    rating_changed = False
    if payload.rating is not None and payload.rating != review.rating:
        review.rating = payload.rating
        rating_changed = True

    if payload.title is not None:
        review.title = payload.title.strip() if payload.title else None

    if payload.comment is not None:
        review.comment = payload.comment.strip()

    if payload.images is not None:
        review.images = payload.images[:5]

    review.updated_at = _utcnow()
    await review.save()

    if rating_changed:
        await recalculate_product_ratings(product.id)

    return _review_to_out(review, user.id)


async def get_product_reviews(
    product_slug_or_id: str,
    page: int = 1,
    limit: int = 10,
    rating: int | None = None,
    sort: str = "recent",
    current_user_id: PydanticObjectId | None = None,
) -> ProductReviewsResponse:
    """Fetch public non-hidden reviews for a product with breakdown statistics."""
    product = await _resolve_product(product_slug_or_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # 1. Compute rating breakdown across all non-hidden reviews
    all_reviews = await ProductReview.find(
        ProductReview.product_id == product.id,
        ProductReview.is_hidden == False,
    ).to_list()

    total = len(all_reviews)
    stars_5 = sum(1 for r in all_reviews if r.rating == 5)
    stars_4 = sum(1 for r in all_reviews if r.rating == 4)
    stars_3 = sum(1 for r in all_reviews if r.rating == 3)
    stars_2 = sum(1 for r in all_reviews if r.rating == 2)
    stars_1 = sum(1 for r in all_reviews if r.rating == 1)

    pct_5 = round((stars_5 / total) * 100) if total > 0 else 0
    pct_4 = round((stars_4 / total) * 100) if total > 0 else 0
    pct_3 = round((stars_3 / total) * 100) if total > 0 else 0
    pct_2 = round((stars_2 / total) * 100) if total > 0 else 0
    pct_1 = round((stars_1 / total) * 100) if total > 0 else 0

    avg_rating = round(sum(r.rating for r in all_reviews) / total, 1) if total > 0 else 5.0

    breakdown = ProductRatingBreakdown(
        stars_5=stars_5,
        stars_4=stars_4,
        stars_3=stars_3,
        stars_2=stars_2,
        stars_1=stars_1,
        stars_5_pct=pct_5,
        stars_4_pct=pct_4,
        stars_3_pct=pct_3,
        stars_2_pct=pct_2,
        stars_1_pct=pct_1,
    )

    # 2. Build filtered paginated query
    query_filters: dict[str, Any] = {
        "product_id": product.id,
        "is_hidden": False,
    }
    if rating and 1 <= rating <= 5:
        query_filters["rating"] = rating

    query = ProductReview.find(query_filters)

    if sort == "highest":
        query = query.sort("-rating", "-created_at")
    elif sort == "lowest":
        query = query.sort("+rating", "-created_at")
    elif sort == "helpful":
        query = query.sort("-helpful_count", "-created_at")
    else:  # recent
        query = query.sort("-created_at")

    filtered_total = await query.count()
    skip = (page - 1) * limit
    reviews = await query.skip(skip).limit(limit).to_list()

    pages = max(1, (filtered_total + limit - 1) // limit) if filtered_total > 0 else 1

    return ProductReviewsResponse(
        items=[_review_to_out(r, current_user_id) for r in reviews],
        total=filtered_total,
        average_rating=avg_rating,
        breakdown=breakdown,
        page=page,
        limit=limit,
        pages=pages,
    )


async def toggle_review_helpful(review_id: str, user_id: PydanticObjectId) -> dict[str, Any]:
    """Toggle helpful upvote on a review."""
    if not PydanticObjectId.is_valid(review_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review ID")

    review = await ProductReview.get(PydanticObjectId(review_id))
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if user_id in review.helpful_user_ids:
        # Remove upvote
        review.helpful_user_ids.remove(user_id)
        review.helpful_count = max(0, review.helpful_count - 1)
        voted = False
    else:
        # Add upvote
        review.helpful_user_ids.append(user_id)
        review.helpful_count += 1
        voted = True

    await review.save()
    return {"helpful_count": review.helpful_count, "is_helpful_by_me": voted}


# ---------------------------------------------------------------------------
# Admin Review Moderation Methods
# ---------------------------------------------------------------------------


async def admin_list_reviews(
    page: int = 1,
    limit: int = 20,
    rating: int | None = None,
    is_hidden: bool | None = None,
    product_id: str | None = None,
    search: str | None = None,
) -> AdminProductReviewListResponse:
    """Admin endpoint to list and audit devotee product reviews."""
    query_filters: dict[str, Any] = {}

    if rating and 1 <= rating <= 5:
        query_filters["rating"] = rating

    if is_hidden is not None:
        query_filters["is_hidden"] = is_hidden

    if product_id and PydanticObjectId.is_valid(product_id):
        query_filters["product_id"] = PydanticObjectId(product_id)

    if search and search.strip():
        pat = safe_regex_pattern(search)
        query_filters["$or"] = [
            {"author_name": pat},
            {"comment": pat},
            {"title": pat},
        ]

    query = ProductReview.find(query_filters).sort("-created_at")
    total = await query.count()
    skip = (page - 1) * limit
    reviews = await query.skip(skip).limit(limit).to_list()
    pages = max(1, (total + limit - 1) // limit) if total > 0 else 1

    return AdminProductReviewListResponse(
        items=[_review_to_out(r) for r in reviews],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


async def admin_moderate_review(
    review_id: str,
    payload: AdminReviewModerationUpdate,
) -> ProductReviewOut:
    """Admin moderate (hide or restore) a review."""
    if not PydanticObjectId.is_valid(review_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review ID")

    review = await ProductReview.get(PydanticObjectId(review_id))
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    review.is_hidden = payload.is_hidden
    if payload.is_hidden:
        review.hidden_reason = payload.hidden_reason
        review.hidden_at = _utcnow()
    else:
        review.hidden_reason = None
        review.hidden_at = None

    await review.save()
    await recalculate_product_ratings(review.product_id)
    return _review_to_out(review)


async def admin_delete_review(review_id: str) -> None:
    """Admin permanently delete a review and recalculate ratings."""
    if not PydanticObjectId.is_valid(review_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review ID")

    review = await ProductReview.get(PydanticObjectId(review_id))
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    product_id = review.product_id
    await review.delete()
    await recalculate_product_ratings(product_id)
