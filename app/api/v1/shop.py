"""Public-facing client APIs for Astra AstroStore / Remedy E-Commerce.

Endpoints:
- GET /api/v1/shop/categories: List active categories with icons and banners.
- GET /api/v1/shop/products: Browse active products with sorting, filtering, and pagination.
- GET /api/v1/shop/products/{slug_or_id}: Fetch single product details with astrological metadata.
- GET /api/v1/shop/banners: Fetch promotional hero carousel banners and announcement bar.
"""

from fastapi import APIRouter, Query

from app.schemas.common import ApiResponse
from app.schemas.shop import (
    ProductCategoryOut,
    ProductListResponse,
    ProductOut,
    ShopBannerSettingsOut,
    ShopProductRecommendationOut,
    StockReservationRequest,
    StockReservationResponse,
)
from app.services import shop_admin, shop_remedy_recommender

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get(
    "/categories",
    response_model=ApiResponse[list[ProductCategoryOut]],
    summary="List active store categories",
)
async def get_public_categories() -> ApiResponse[list[ProductCategoryOut]]:
    cats = await shop_admin.list_categories(include_inactive=False)
    return ApiResponse.ok(data=cats)


@router.get(
    "/products",
    response_model=ApiResponse[ProductListResponse],
    summary="Browse active remedy products",
)
async def get_public_products(
    search: str | None = Query(default=None),
    category_id: str | None = Query(default=None),
    ruling_planet: str | None = Query(default=None),
    in_stock_only: bool = Query(default=False),
    is_featured: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="-created_at"),
) -> ApiResponse[ProductListResponse]:
    stock_status = "in_stock" if in_stock_only else None
    result = await shop_admin.list_products(
        search=search,
        category_id=category_id,
        ruling_planet=ruling_planet,
        stock_status=stock_status,
        is_active=True,
        is_featured=is_featured,
        page=page,
        limit=limit,
        sort_by=sort_by,
    )
    return ApiResponse.ok(data=result)


@router.get(
    "/products/{id_or_slug}",
    response_model=ApiResponse[ProductOut],
    summary="Get remedy product by ID or slug",
)
async def get_public_product_detail(id_or_slug: str) -> ApiResponse[ProductOut]:
    product = await shop_admin.get_product_by_id_or_slug(id_or_slug)
    return ApiResponse.ok(data=product)


@router.get(
    "/banners",
    response_model=ApiResponse[ShopBannerSettingsOut],
    summary="Get active store hero banners and announcements",
)
async def get_public_banners() -> ApiResponse[ShopBannerSettingsOut]:
    settings = await shop_admin.get_shop_banner_settings()
    active_banners = [b for b in settings.hero_banners if b.is_active]
    return ApiResponse.ok(
        data=ShopBannerSettingsOut(
            announcement_bar_text=settings.announcement_bar_text if settings.announcement_bar_active else None,
            announcement_bar_link=settings.announcement_bar_link if settings.announcement_bar_active else None,
            announcement_bar_active=settings.announcement_bar_active,
            hero_banners=active_banners,
        )
    )


@router.get(
    "/recommendations",
    response_model=ApiResponse[list[ShopProductRecommendationOut]],
    summary="Get dynamic remedy product recommendations based on astrological transit, dosha, or rashi",
)
async def get_astrological_remedy_recommendations(
    planet: str | None = Query(default=None, description="e.g. Saturn, Mars, Sun, Jupiter"),
    dosha: str | None = Query(default=None, description="e.g. sade_sati, manglik, kaal_sarp, pitra_dosha, blocked_money"),
    rashi: str | None = Query(default=None, description="e.g. Aries, Leo, Capricorn"),
    life_pillar: str | None = Query(default=None, description="e.g. Career, Wealth, Health, Marriage"),
    lang: str = Query(default="bn", description="'bn', 'hi', or 'en'"),
    limit: int = Query(default=4, ge=1, le=12),
) -> ApiResponse[list[ShopProductRecommendationOut]]:
    recs = await shop_remedy_recommender.get_shop_recommendations_for_astrology(
        planet=planet,
        dosha=dosha,
        rashi=rashi,
        life_pillar=life_pillar,
        lang=lang,
        limit=limit,
    )
    return ApiResponse.ok(data=recs)


@router.post(
    "/reserve-stock",
    response_model=ApiResponse[StockReservationResponse],
    summary="Atomically reserve inventory quantity to prevent concurrent over-ordering race conditions",
)
async def reserve_stock(
    payload: StockReservationRequest,
) -> ApiResponse[StockReservationResponse]:
    success = await shop_admin.atomic_reserve_stock(payload.product_id, payload.quantity)
    message = (
        "Stock reserved successfully for checkout."
        if success
        else "Insufficient stock or item is currently being purchased by another seeker."
    )
    return ApiResponse.ok(
        data=StockReservationResponse(
            success=success,
            reserved=success,
            product_id=payload.product_id,
            quantity=payload.quantity,
            message=message,
        )
    )


@router.post(
    "/release-stock",
    response_model=ApiResponse[StockReservationResponse],
    summary="Atomically release reserved inventory quantity upon checkout abort or payment failure",
)
async def release_stock(
    payload: StockReservationRequest,
) -> ApiResponse[StockReservationResponse]:
    success = await shop_admin.atomic_release_stock(payload.product_id, payload.quantity)
    return ApiResponse.ok(
        data=StockReservationResponse(
            success=success,
            reserved=False,
            product_id=payload.product_id,
            quantity=payload.quantity,
            message="Stock released back to inventory successfully.",
        )
    )



