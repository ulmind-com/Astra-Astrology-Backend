"""Public-facing client APIs for Astra AstroStore / Remedy E-Commerce.

Endpoints:
- GET /api/v1/shop/categories: List active categories with icons and banners.
- GET /api/v1/shop/products: Browse active products with sorting, filtering, and pagination.
- GET /api/v1/shop/products/{slug_or_id}: Fetch single product details with astrological metadata.
- GET /api/v1/shop/banners: Fetch promotional hero carousel banners and announcement bar.
"""

from fastapi import APIRouter, Body, File, Query, Response, UploadFile
from fastapi.responses import HTMLResponse
from loguru import logger

from app.api.dependencies import AdminUser, CurrentUser, OptionalUser
from app.core.exceptions import BadRequestError
from app.schemas.common import ApiResponse
from app.schemas.shop import (
    CartApplyCouponRequest,
    CartItemIn,
    CartOut,
    CartSyncRequest,
    CartUpdateItemRequest,
    InvoiceDataOut,
    PincodeCheckResponse,
    ProductCategoryOut,
    ProductListResponse,
    ProductOut,
    ProductReviewCreate,
    ProductReviewOut,
    ProductReviewsResponse,
    ProductReviewUpdate,
    ReviewEligibilityResponse,
    ShopBannerSettingsOut,
    ShopCancelOrderPayload,
    ShopCheckoutRequest,
    ShopCheckoutResponse,
    ShopCouponRecommendationsResponse,
    ShopCouponValidateRequest,
    ShopCouponValidateResponse,
    ShopOrderListResponse,
    ShopOrderOut,
    ShopOrderTrackingOut,
    ShopPaymentVerifyRequest,
    ShopProductRecommendationOut,
    StockReservationRequest,
    StockReservationResponse,
)
from app.services import shop_admin, shop_cart_service, shop_invoice_service, shop_remedy_recommender, shop_review_service
from app.services.shop_order_service import ShopOrderService

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get(
    "/categories",
    response_model=ApiResponse[list[ProductCategoryOut]],
    summary="List active store categories",
)
async def get_public_categories(response: Response) -> ApiResponse[list[ProductCategoryOut]]:
    cats = await shop_admin.list_categories(include_inactive=False)
    response.headers["Cache-Control"] = "public, max-age=60, s-maxage=300, stale-while-revalidate=600"
    return ApiResponse.ok(data=cats)


@router.get(
    "/products",
    response_model=ApiResponse[ProductListResponse],
    summary="Browse active remedy products",
)
async def get_public_products(
    response: Response,
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
    response.headers["Cache-Control"] = "public, max-age=20, s-maxage=60, stale-while-revalidate=180"
    return ApiResponse.ok(data=result)


@router.get(
    "/products/{id_or_slug}",
    response_model=ApiResponse[ProductOut],
    summary="Get remedy product by ID or slug",
)
async def get_public_product_detail(id_or_slug: str, response: Response) -> ApiResponse[ProductOut]:
    product = await shop_admin.get_product_by_id_or_slug(id_or_slug)
    response.headers["Cache-Control"] = "public, max-age=30, s-maxage=120, stale-while-revalidate=300"
    return ApiResponse.ok(data=product)


@router.get(
    "/banners",
    response_model=ApiResponse[ShopBannerSettingsOut],
    summary="Get active store hero banners, announcements and reels",
)
async def get_public_banners(response: Response) -> ApiResponse[ShopBannerSettingsOut]:
    response.headers["Cache-Control"] = "public, max-age=60, s-maxage=300, stale-while-revalidate=600"
    try:
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
                free_gift_enabled=getattr(settings, "free_gift_enabled", False),
                free_gift_min_cart_value=getattr(settings, "free_gift_min_cart_value", 0.0),
                free_gift_default_title=getattr(settings, "free_gift_default_title", None),
                free_gift_default_value=getattr(settings, "free_gift_default_value", 0.0),
                free_gift_default_badge=getattr(settings, "free_gift_default_badge", None),
                free_gift_default_image_url=getattr(settings, "free_gift_default_image_url", None),
            )
        )
    except Exception as exc:
        logger.warning("MongoDB read failed for banners ({}); serving default fallback banners.", exc)
        return ApiResponse.ok(
            data=ShopBannerSettingsOut(
                announcement_bar_text=None,
                announcement_bar_link=None,
                announcement_bar_active=False,
                hero_banners=shop_admin.default_shop_hero_banners(),
                reels=shop_admin.default_shop_reels(),
                cashback_enabled=True,
                cashback_percent=100,
                cashback_credit_timing="on_delivery",
                allow_user_cancellation=True,
                cancellation_grace_hours=24,
                cod_enabled=True,
                free_shipping_threshold=499.0,
                standard_shipping_fee=70.0,
                free_gift_enabled=False,
                free_gift_min_cart_value=0.0,
                free_gift_default_title=None,
                free_gift_default_value=0.0,
                free_gift_default_badge=None,
                free_gift_default_image_url=None,
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
    _admin: AdminUser,
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
    _admin: AdminUser,
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
    "/checkout/{order_id}/abort",
    response_model=ApiResponse[dict[str, bool]],
    summary="Abort unpaid checkout attempt and immediately release reserved inventory stock",
)
async def abort_shop_checkout(
    order_id: str,
    user: CurrentUser,
) -> ApiResponse[dict[str, bool]]:
    success = await ShopOrderService.abort_checkout(order_id=order_id, user_id=user.id)
    return ApiResponse.ok(data={"success": success, "aborted": True})


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


@router.get(
    "/orders/{order_key}/track",
    response_model=ApiResponse[ShopOrderTrackingOut],
    summary="Track delivery status, carrier timeline and consecration status for a remedy order",
)
async def track_shop_order(
    order_key: str,
    user: OptionalUser = None,
) -> ApiResponse[ShopOrderTrackingOut]:
    """Retrieves dedicated tracking events, courier AWB and status history for the order."""
    order = await ShopOrderService.get_order_by_number_or_id(
        order_key=order_key,
        user_id=user.id if user else None,
    )
    items_summary = [
        {
            "product_name": it.title,
            "quantity": it.quantity,
            "image_url": it.featured_image,
            "unit_price": it.unit_sale_price,
            "selected_option": None,
        }
        for it in order.items
    ]
    data = ShopOrderTrackingOut(
        order_id=order.id,
        order_number=order.order_number,
        order_status=order.order_status,
        courier_partner=order.courier_partner,
        tracking_id=order.tracking_id,
        tracking_url=order.tracking_url,
        estimated_delivery_date=order.estimated_delivery_date,
        delivered_at=order.delivered_at,
        shipping_address=order.shipping_address,
        items_count=len(order.items),
        items_summary=items_summary,
        status_history=order.status_history,
        consecration_certificate_url=order.consecration_certificate_url,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
    return ApiResponse.ok(data=data, message="Order tracking status retrieved successfully.")


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

    # Check size (max 5 MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise BadRequestError("QR code image size must not exceed 5MB.")
    await file.seek(0)

    result = await upload_file(
        file=file,
        folder="divinlink/shop/refund_qrs",
        allowed_types=ALLOWED_IMAGE_TYPES,
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


# ===========================================================================
# 8. Product Reviews & Verified Buyer Endpoints
# ===========================================================================


@router.get(
    "/products/{slug}/reviews",
    response_model=ApiResponse[ProductReviewsResponse],
    summary="Get paginated verified devotee reviews and rating distribution for a product",
)
async def get_product_reviews(
    slug: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    rating: int | None = Query(default=None, ge=1, le=5),
    sort: str = Query(default="recent", pattern="^(recent|highest|lowest|helpful)$"),
    user: OptionalUser = None,
) -> ApiResponse[ProductReviewsResponse]:
    res = await shop_review_service.get_product_reviews(
        product_slug_or_id=slug,
        page=page,
        limit=limit,
        rating=rating,
        sort=sort,
        current_user_id=user.id if user else None,
    )
    return ApiResponse.ok(data=res)


@router.get(
    "/products/{slug}/reviews/eligibility",
    response_model=ApiResponse[ReviewEligibilityResponse],
    summary="Check if current user is eligible to review (has delivered order & hasn't reviewed yet)",
)
async def check_review_eligibility(
    slug: str,
    user: CurrentUser,
) -> ApiResponse[ReviewEligibilityResponse]:
    res = await shop_review_service.check_review_eligibility(
        product_slug_or_id=slug,
        user_id=user.id,
    )
    return ApiResponse.ok(data=res)


@router.post(
    "/products/{slug}/reviews",
    response_model=ApiResponse[ProductReviewOut],
    summary="Submit a verified buyer review with rating, testimony, and photos",
)
async def create_product_review(
    slug: str,
    payload: ProductReviewCreate,
    user: CurrentUser,
) -> ApiResponse[ProductReviewOut]:
    res = await shop_review_service.create_product_review(
        product_slug_or_id=slug,
        payload=payload,
        user=user,
    )
    return ApiResponse.ok(data=res, message="ধন্যবাদ! আপনার পবিত্র রিভিউ সফলভাবে প্রকাশিত হয়েছে।")


@router.put(
    "/products/{slug}/reviews/mine",
    response_model=ApiResponse[ProductReviewOut],
    summary="Update customer's existing review for a product",
)
@router.patch(
    "/products/{slug}/reviews/mine",
    response_model=ApiResponse[ProductReviewOut],
    summary="Update customer's existing review for a product (PATCH alias)",
)
async def update_product_review(
    slug: str,
    payload: ProductReviewUpdate,
    user: CurrentUser,
) -> ApiResponse[ProductReviewOut]:
    res = await shop_review_service.update_my_review(
        product_slug_or_id=slug,
        payload=payload,
        user=user,
    )
    return ApiResponse.ok(data=res, message="রিভিউ সফলভাবে আপডেট করা হয়েছে।")


@router.post(
    "/reviews/{review_id}/helpful",
    response_model=ApiResponse[dict],
    summary="Upvote or toggle helpful feedback on a review",
)
async def toggle_review_helpful(
    review_id: str,
    user: CurrentUser,
) -> ApiResponse[dict]:
    res = await shop_review_service.toggle_review_helpful(
        review_id=review_id,
        user_id=user.id,
    )
    return ApiResponse.ok(data=res)


@router.post(
    "/reviews/upload-image",
    response_model=ApiResponse[dict[str, str]],
    summary="Upload devotee photo of consecrated parcel/item to Cloudinary",
)
async def upload_review_photo(
    user: CurrentUser,
    file: UploadFile = File(...),
) -> ApiResponse[dict[str, str]]:
    from app.services.storage import ALLOWED_IMAGE_TYPES, upload_file

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestError("Only JPEG, PNG, or WebP images are allowed.")

    contents = await file.read()
    if len(contents) > 8 * 1024 * 1024:
        raise BadRequestError("Review image size must not exceed 8MB.")
    await file.seek(0)

    result = await upload_file(
        file=file,
        folder="divinlink/shop/reviews",
        allowed_types=ALLOWED_IMAGE_TYPES,
    )
    return ApiResponse.ok(
        data={"url": result.secure_url, "public_id": result.public_id},
        message="Image uploaded successfully.",
    )


# ===========================================================================
# 9. Printable GST & Commercial Order Invoice Endpoints
# ===========================================================================


@router.get(
    "/orders/{order_key}/invoice",
    response_model=ApiResponse[InvoiceDataOut],
    summary="Get structured JSON invoice data for an order (Tax Invoice or Bill of Supply)",
)
async def get_order_invoice(
    order_key: str,
    user: CurrentUser,
) -> ApiResponse[InvoiceDataOut]:
    data = await shop_invoice_service.get_or_create_invoice_data(
        order_key=order_key,
        user_id=user.id,
        is_admin=False,
    )
    return ApiResponse.ok(data=data)


@router.get(
    "/orders/{order_key}/invoice/html",
    response_class=HTMLResponse,
    summary="Get standalone high-res luxury printable HTML invoice and packing slip",
)
async def get_order_invoice_html(
    order_key: str,
    auto_print: bool = Query(default=False, alias="print"),
    token: str | None = Query(default=None),
    user: OptionalUser = None,
) -> HTMLResponse:
    data = await shop_invoice_service.get_or_create_invoice_data(
        order_key=order_key,
        user_id=user.id if user else None,
        is_admin=bool(user and getattr(user, "role", None) in ("admin", "super_admin")),
        access_token=token,
    )
    html_content = shop_invoice_service.generate_invoice_html(data, auto_print=auto_print)
    return HTMLResponse(content=html_content)


# ===========================================================================
# 10. Multi-Device Persistent Shopping Cart Endpoints
# ===========================================================================


@router.get(
    "/cart",
    response_model=ApiResponse[CartOut],
    summary="Get authenticated user's persistent synchronized cart",
)
async def get_cart(
    user: CurrentUser,
) -> ApiResponse[CartOut]:
    cart = await shop_cart_service.get_user_cart(user.id)
    return ApiResponse.ok(data=cart)


@router.post(
    "/cart/sync",
    response_model=ApiResponse[CartOut],
    summary="Merge local/guest items into server cart on login or device mount",
)
async def sync_cart(
    payload: CartSyncRequest,
    user: CurrentUser,
) -> ApiResponse[CartOut]:
    cart = await shop_cart_service.sync_cart(
        user_id=user.id,
        local_items=payload.items,
        coupon_code=payload.coupon_code,
    )
    return ApiResponse.ok(data=cart, message="Cart synchronized successfully.")


@router.post(
    "/cart/items",
    response_model=ApiResponse[CartOut],
    summary="Add an item or increment quantity in persistent cart",
)
async def add_item_to_cart(
    payload: CartItemIn,
    user: CurrentUser,
) -> ApiResponse[CartOut]:
    cart = await shop_cart_service.add_cart_item(
        user_id=user.id,
        product_id_str=payload.product_id,
        quantity=payload.quantity,
        sankalpa=payload.sankalpa,
    )
    return ApiResponse.ok(data=cart, message="Item added to cart.")


@router.patch(
    "/cart/items/{product_id}",
    response_model=ApiResponse[CartOut],
    summary="Update item quantity or Sankalpa details in persistent cart",
)
async def update_cart_item(
    product_id: str,
    payload: CartUpdateItemRequest,
    user: CurrentUser,
) -> ApiResponse[CartOut]:
    cart = await shop_cart_service.update_cart_item(
        user_id=user.id,
        product_id_str=product_id,
        quantity=payload.quantity,
        sankalpa=payload.sankalpa,
    )
    return ApiResponse.ok(data=cart, message="Cart item updated.")


@router.delete(
    "/cart/items/{product_id}",
    response_model=ApiResponse[CartOut],
    summary="Remove a specific product from persistent cart",
)
async def remove_cart_item(
    product_id: str,
    user: CurrentUser,
) -> ApiResponse[CartOut]:
    cart = await shop_cart_service.remove_cart_item(
        user_id=user.id,
        product_id_str=product_id,
    )
    return ApiResponse.ok(data=cart, message="Item removed from cart.")


@router.delete(
    "/cart",
    response_model=ApiResponse[CartOut],
    summary="Clear all items from persistent cart",
)
async def clear_cart(
    user: CurrentUser,
) -> ApiResponse[CartOut]:
    cart = await shop_cart_service.clear_cart(user.id)
    return ApiResponse.ok(data=cart, message="Cart cleared successfully.")


@router.post(
    "/cart/coupon",
    response_model=ApiResponse[CartOut],
    summary="Apply or remove a promo coupon in persistent cart",
)
async def apply_cart_coupon(
    payload: CartApplyCouponRequest,
    user: CurrentUser,
) -> ApiResponse[CartOut]:
    cart = await shop_cart_service.apply_cart_coupon(
        user_id=user.id,
        code=payload.code,
    )
    return ApiResponse.ok(
        data=cart,
        message="Coupon applied successfully." if cart.is_coupon_valid else "Coupon removed or invalid.",
    )







