"""Public-facing client APIs for Astra AstroStore / Remedy E-Commerce.

Endpoints:
- GET /api/v1/shop/categories: List active categories with icons and banners.
- GET /api/v1/shop/products: Browse active products with sorting, filtering, and pagination.
- GET /api/v1/shop/products/{slug_or_id}: Fetch single product details with astrological metadata.
- GET /api/v1/shop/banners: Fetch promotional hero carousel banners and announcement bar.
"""

from fastapi import APIRouter, Body, File, Query, UploadFile

from app.api.dependencies import CurrentUser, OptionalUser
from app.core.exceptions import BadRequestError
from app.schemas.common import ApiResponse
from app.schemas.shop import (
    PincodeCheckResponse,
    ProductCategoryOut,
    ProductListResponse,
    ProductOut,
    ShopBannerSettingsOut,
    ShopCancelOrderPayload,
    ShopCheckoutRequest,
    ShopCheckoutResponse,
    ShopCouponRecommendationsResponse,
    ShopCouponValidateRequest,
    ShopCouponValidateResponse,
    ShopOrderListResponse,
    ShopOrderOut,
    ShopPaymentVerifyRequest,
    ShopProductRecommendationOut,
    StockReservationRequest,
    StockReservationResponse,
)
from app.services import shop_admin, shop_remedy_recommender
from app.services.shop_order_service import ShopOrderService

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
    summary="Get active store hero banners, announcements and reels",
)
async def get_public_banners() -> ApiResponse[ShopBannerSettingsOut]:
    settings = await shop_admin.get_shop_banner_settings()
    active_banners = [b for b in settings.hero_banners if b.is_active]
    active_reels = [r for r in settings.reels if r.is_active]
    return ApiResponse.ok(
        data=ShopBannerSettingsOut(
            announcement_bar_text=settings.announcement_bar_text if settings.announcement_bar_active else None,
            announcement_bar_link=settings.announcement_bar_link if settings.announcement_bar_active else None,
            announcement_bar_active=settings.announcement_bar_active,
            hero_banners=active_banners,
            reels=active_reels,
            cashback_enabled=settings.cashback_enabled,
            cashback_percent=settings.cashback_percent,
            cashback_credit_timing=settings.cashback_credit_timing,
            allow_user_cancellation=settings.allow_user_cancellation,
            cancellation_grace_hours=settings.cancellation_grace_hours,
            cod_enabled=settings.cod_enabled,
            free_shipping_threshold=settings.free_shipping_threshold,
            standard_shipping_fee=settings.standard_shipping_fee,
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


# ===========================================================================
# Pincode Serviceability Check
# ===========================================================================


@router.get(
    "/pincode/{pincode}",
    response_model=ApiResponse[PincodeCheckResponse],
    summary="Check delivery timeline and COD availability by Indian PIN code with anti-abuse blacklist check",
)
async def check_pincode_availability(
    pincode: str,
    phone: str | None = None,
    user: OptionalUser = None,
) -> ApiResponse[PincodeCheckResponse]:
    uid = user.id if user else None
    result = await ShopOrderService.check_pincode(pincode=pincode, phone=phone, user_id=uid)
    return ApiResponse.ok(data=result)


# ===========================================================================
# Checkout & Order Placement with 100% Wallet Cashback
# ===========================================================================


@router.post(
    "/checkout",
    response_model=ApiResponse[ShopCheckoutResponse],
    summary="Place a remedy order with Vedic Sankalpa, free gifts, and 100% wallet cashback calculation",
)
async def shop_checkout(
    payload: ShopCheckoutRequest,
    user: CurrentUser,
) -> ApiResponse[ShopCheckoutResponse]:
    user_phone = (
        getattr(user, "phone", None)
        or getattr(user, "phone_number", None)
        or payload.shipping_address.phone_number
        or ""
    )
    result = await ShopOrderService.create_order(
        user_id=user.id,
        user_email=user.email,
        user_phone=user_phone,
        payload=payload,
    )
    return ApiResponse.ok(data=result)


@router.post(
    "/verify-payment",
    response_model=ApiResponse[ShopOrderOut],
    summary="Verify Razorpay payment signature and execute instant 100% wallet cashback credit",
)
async def shop_verify_payment(
    payload: ShopPaymentVerifyRequest,
    user: CurrentUser,
) -> ApiResponse[ShopOrderOut]:
    order = await ShopOrderService.verify_razorpay_payment(
        user_id=user.id,
        payload=payload,
    )
    return ApiResponse.ok(data=order)


@router.get(
    "/orders/mine",
    response_model=ApiResponse[ShopOrderListResponse],
    summary="List past remedy orders placed by current user",
)
async def list_my_shop_orders(
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> ApiResponse[ShopOrderListResponse]:
    result = await ShopOrderService.get_user_orders(
        user_id=user.id,
        page=page,
        limit=limit,
    )
    return ApiResponse.ok(data=result)


@router.get(
    "/orders/{order_key}",
    response_model=ApiResponse[ShopOrderOut],
    summary="Get order details, Vedic consecration status, and tracking information",
)
async def get_shop_order_detail(
    order_key: str,
    user: CurrentUser,
) -> ApiResponse[ShopOrderOut]:
    order = await ShopOrderService.get_order_by_number_or_id(
        order_key=order_key,
        user_id=user.id,
    )
    return ApiResponse.ok(data=order)


@router.post(
    "/upload-refund-qr",
    response_model=ApiResponse[dict[str, str]],
    summary="Upload customer UPI QR Code image to Cloudinary for order refund payout",
)
async def upload_refund_qr_code(
    user: CurrentUser,
    file: UploadFile = File(...),
) -> ApiResponse[dict[str, str]]:
    """Uploads customer's UPI payment QR screenshot to Cloudinary."""
    from app.services.storage import ALLOWED_IMAGE_TYPES, upload_file

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestError("Only JPEG, PNG, or WebP images are allowed.")

    # Read and check size (max 5 MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise BadRequestError("QR code image size must not exceed 5MB.")

    result = await upload_file(
        contents=contents,
        filename=file.filename or "refund_qr.png",
        folder="divinlink/shop/refund_qrs",
    )
    return ApiResponse.ok(
        data={"url": result.secure_url, "public_id": result.public_id},
        message="UPI QR Code uploaded successfully.",
    )


@router.post(
    "/orders/{order_key}/cancel",
    response_model=ApiResponse[ShopOrderOut],
    summary="Cancel order before shipment with automatic cashback claw-back and UPI refund request",
)
async def cancel_my_shop_order(
    order_key: str,
    user: CurrentUser,
    payload: ShopCancelOrderPayload = Body(default_factory=ShopCancelOrderPayload),
) -> ApiResponse[ShopOrderOut]:
    order = await ShopOrderService.cancel_order(
        order_id=order_key,
        user_id=user.id,
        reason=payload.reason or "Cancelled by devotee from order tracking dashboard",
        upi_id=payload.upi_id,
        qr_code_url=payload.qr_code_url,
        qr_code_public_id=payload.qr_code_public_id,
    )
    return ApiResponse.ok(data=order)


# ===========================================================================
# Coupon Validation & Smart Recommendation Endpoints
# ===========================================================================


@router.post(
    "/coupons/validate",
    response_model=ApiResponse[ShopCouponValidateResponse],
    summary="Validate coupon code against cart subtotal and user eligibility",
)
async def validate_shop_coupon(
    payload: ShopCouponValidateRequest,
    user: OptionalUser = None,
) -> ApiResponse[ShopCouponValidateResponse]:
    result = await ShopOrderService.validate_coupon(
        code=payload.code,
        subtotal=payload.subtotal,
        user_id=user.id if user else None,
    )
    return ApiResponse.ok(data=result)


@router.post(
    "/coupons/recommendations",
    response_model=ApiResponse[ShopCouponRecommendationsResponse],
    summary="Get personalized coupon recommendations ranked by highest savings",
)
async def get_shop_coupon_recommendations(
    subtotal: float = Query(default=0.0, ge=0),
    user: OptionalUser = None,
) -> ApiResponse[ShopCouponRecommendationsResponse]:
    result = await ShopOrderService.get_coupon_recommendations(
        subtotal=subtotal,
        user_id=user.id if user else None,
    )
    return ApiResponse.ok(data=result)




