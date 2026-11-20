"""Admin API endpoints for Astra AstroStore / Remedy E-Commerce.

Covers:
- Image uploads with automatic bounded WebP compression (preserves Cloudinary quotas & bandwidth).
- Category CRUD with product assignment checks and asset cleanup.
- Product CRUD with automatic orphaned Cloudinary asset deletion upon replacement/deletion.
- Real-time inventory overview and quick 1-click stock adjustments.
- Store Hero Carousel & Announcement Bar CMS customization.
"""

from typing import Annotated, Any
from fastapi import APIRouter, Body, File, Query, UploadFile
from fastapi.responses import HTMLResponse

from app.api.dependencies import AdminUser
from app.models.enums import ShopOrderStatus, ShopPaymentStatus, ShopRefundStatus
from app.schemas.common import ApiResponse
from app.schemas.shop import (
    AdminProductReviewListResponse,
    AdminReviewModerationUpdate,
    CloudinaryOrphanCleanupReport,
    InventorySummaryResponse,
    InvoiceDataOut,
    ProductCategoryCreate,
    ProductCategoryOut,
    ProductCategoryUpdate,
    ProductCreate,
    ProductListResponse,
    ProductOut,
    ProductReviewOut,
    ProductUpdate,
    ShopAdminCompleteRefundPayload,
    ShopAdminOrderUpdate,
    ShopBannerSettingsOut,
    ShopBannerSettingsUpdate,
    ShopCouponCreate,
    ShopCouponListResponse,
    ShopCouponOut,
    ShopCouponUpdate,
    ShopOrderListResponse,
    ShopOrderOut,
    StockUpdatePayload,
)
from app.services import shop_admin, shop_invoice_service, shop_review_service
from app.services.shop_order_service import ShopOrderService
from app.services.storage import upload_product_image

router = APIRouter(prefix="/admin/shop", tags=["admin: shop"])


# ===========================================================================
# Media Uploads (Auto-Compressed WebP)
# ===========================================================================


@router.post(
    "/upload-image",
    response_model=ApiResponse[dict[str, str]],
    summary="Upload a store product image with auto WebP compression",
)
async def upload_shop_image(
    file: UploadFile = File(...),
    admin: AdminUser = None,
) -> ApiResponse[dict[str, str]]:
    """Uploads an image, applies auto-format (WebP), 1200x1200px limit, and auto:good compression."""
    result = await upload_product_image(file)
    return ApiResponse.ok(
        data={
            "url": result.secure_url,
            "public_id": result.public_id,
            "format": result.format or "webp",
        },
        message="Image uploaded and compressed successfully.",
    )


# ===========================================================================
# Category Management
# ===========================================================================


@router.get(
    "/categories",
    response_model=ApiResponse[list[ProductCategoryOut]],
    summary="List all product categories with product counts",
)
async def list_shop_categories(
    admin: AdminUser = None,
    include_inactive: bool = Query(default=True),
) -> ApiResponse[list[ProductCategoryOut]]:
    cats = await shop_admin.list_categories(include_inactive=include_inactive)
    return ApiResponse.ok(data=cats)


@router.post(
    "/categories",
    response_model=ApiResponse[ProductCategoryOut],
    summary="Create a new store category",
)
async def create_shop_category(
    payload: ProductCategoryCreate,
    admin: AdminUser = None,
) -> ApiResponse[ProductCategoryOut]:
    cat = await shop_admin.create_category(payload)
    return ApiResponse.ok(data=cat, message="Category created successfully.")


@router.put(
    "/categories/{cat_id}",
    response_model=ApiResponse[ProductCategoryOut],
    summary="Update category details and purge replaced icons/banners",
)
async def update_shop_category(
    cat_id: str,
    payload: ProductCategoryUpdate,
    admin: AdminUser = None,
) -> ApiResponse[ProductCategoryOut]:
    cat = await shop_admin.update_category(cat_id, payload)
    # Refresh to return full out representation with counts
    all_cats = await shop_admin.list_categories(include_inactive=True)
    matched = next((c for c in all_cats if c.id == str(cat.id)), None)
    if not matched:
        return ApiResponse.ok(
            data=ProductCategoryOut(
                id=str(cat.id),
                name=cat.name,
                slug=cat.slug,
                description=cat.description,
                icon_url=cat.icon_url,
                banner_url=cat.banner_url,
                category_type=cat.category_type,
                parent_id=str(cat.parent_id) if cat.parent_id else None,
                display_order=cat.display_order,
                is_active=cat.is_active,
                seo_title=cat.seo_title,
                seo_description=cat.seo_description,
                product_count=0,
                created_at=cat.created_at,
                updated_at=cat.updated_at,
            )
        )
    return ApiResponse.ok(data=matched, message="Category updated successfully.")


@router.delete(
    "/categories/{cat_id}",
    response_model=ApiResponse[dict[str, bool]],
    summary="Delete a category if empty and purge its media",
)
async def delete_shop_category(
    cat_id: str,
    admin: AdminUser = None,
) -> ApiResponse[dict[str, bool]]:
    await shop_admin.delete_category(cat_id)
    return ApiResponse.ok(data={"deleted": True}, message="Category deleted successfully.")


# ===========================================================================
# Product Management
# ===========================================================================


@router.get(
    "/products",
    response_model=ApiResponse[ProductListResponse],
    summary="List products with filtering, search, and pagination",
)
async def list_shop_products(
    admin: AdminUser = None,
    search: str | None = Query(default=None),
    category_id: str | None = Query(default=None),
    ruling_planet: str | None = Query(default=None),
    stock_status: str | None = Query(default=None, description="'in_stock', 'low_stock', or 'out_of_stock'"),
    is_active: bool | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    archived_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="-created_at"),
) -> ApiResponse[ProductListResponse]:
    result = await shop_admin.list_products(
        search=search,
        category_id=category_id,
        ruling_planet=ruling_planet,
        stock_status=stock_status,
        is_active=is_active,
        is_featured=is_featured,
        include_deleted=include_deleted,
        archived_only=archived_only,
        page=page,
        limit=limit,
        sort_by=sort_by,
    )
    return ApiResponse.ok(data=result)


@router.post(
    "/products",
    response_model=ApiResponse[ProductOut],
    summary="Create a new store remedy product",
)
async def create_shop_product(
    payload: ProductCreate,
    admin: AdminUser = None,
) -> ApiResponse[ProductOut]:
    product = await shop_admin.create_product(payload)
    return ApiResponse.ok(data=product, message="Product created successfully.")


@router.get(
    "/products/{product_id}",
    response_model=ApiResponse[ProductOut],
    summary="Get single product details by ID or slug",
)
async def get_shop_product(
    product_id: str,
    admin: AdminUser = None,
) -> ApiResponse[ProductOut]:
    product = await shop_admin.get_product_by_id_or_slug(product_id)
    return ApiResponse.ok(data=product)


@router.put(
    "/products/{product_id}",
    response_model=ApiResponse[ProductOut],
    summary="Update product details and purge removed Cloudinary images",
)
async def update_shop_product(
    product_id: str,
    payload: ProductUpdate,
    admin: AdminUser = None,
) -> ApiResponse[ProductOut]:
    product = await shop_admin.update_product(product_id, payload)
    return ApiResponse.ok(data=product, message="Product updated successfully.")


@router.delete(
    "/products/{product_id}",
    response_model=ApiResponse[dict[str, Any]],
    summary="Delete product (safely soft-deletes if order history exists)",
)
async def delete_shop_product(
    product_id: str,
    hard_delete: bool = Query(default=False),
    admin: AdminUser = None,
) -> ApiResponse[dict[str, Any]]:
    result = await shop_admin.delete_product(product_id, hard_delete=hard_delete)
    return ApiResponse.ok(data=result, message=result.get("message", "Product deleted."))


@router.post(
    "/products/{product_id}/restore",
    response_model=ApiResponse[ProductOut],
    summary="Restore a soft-deleted product back to active catalog",
)
async def restore_shop_product(
    product_id: str,
    admin: AdminUser = None,
) -> ApiResponse[ProductOut]:
    product = await shop_admin.restore_product(product_id)
    return ApiResponse.ok(data=product, message="Product restored successfully.")


@router.post(
    "/cleanup-orphaned-images",
    response_model=ApiResponse[CloudinaryOrphanCleanupReport],
    summary="Purge orphaned Cloudinary images in products/ folder",
)
async def cleanup_orphaned_shop_images(
    dry_run: bool = Query(default=False, description="Simulate without actually deleting"),
    admin: AdminUser = None,
) -> ApiResponse[CloudinaryOrphanCleanupReport]:
    report = await shop_admin.purge_unreferenced_cloudinary_shop_images(dry_run=dry_run)
    return ApiResponse.ok(data=report, message="Cloudinary image garbage collection completed.")


# ===========================================================================
# Inventory Dashboard & 1-Click Stock Updates
# ===========================================================================


@router.get(
    "/inventory",
    response_model=ApiResponse[InventorySummaryResponse],
    summary="Get warehouse metrics, valuation, and stock alerts",
)
async def get_shop_inventory_summary(
    admin: AdminUser = None,
) -> ApiResponse[InventorySummaryResponse]:
    metrics = await shop_admin.get_inventory_summary()
    return ApiResponse.ok(data=metrics)


@router.patch(
    "/products/{product_id}/stock",
    response_model=ApiResponse[ProductOut],
    summary="Quick inline stock update (+, -, or absolute set)",
)
async def quick_update_product_stock(
    product_id: str,
    payload: StockUpdatePayload,
    admin: AdminUser = None,
) -> ApiResponse[ProductOut]:
    product = await shop_admin.update_stock(product_id, payload)
    return ApiResponse.ok(data=product, message="Stock updated successfully.")


# ===========================================================================
# Store Banners & Hero Offers CMS
# ===========================================================================


@router.get(
    "/banners",
    response_model=ApiResponse[ShopBannerSettingsOut],
    summary="Get store hero carousel banners & announcement bar",
)
async def get_store_banner_settings(
    admin: AdminUser = None,
) -> ApiResponse[ShopBannerSettingsOut]:
    settings = await shop_admin.get_shop_banner_settings()
    return ApiResponse.ok(data=settings)


@router.put(
    "/banners",
    response_model=ApiResponse[ShopBannerSettingsOut],
    summary="Update store hero banners and promotional announcement",
)
async def update_store_banner_settings(
    payload: ShopBannerSettingsUpdate,
    admin: AdminUser = None,
) -> ApiResponse[ShopBannerSettingsOut]:
    settings = await shop_admin.update_shop_banner_settings(payload)
    return ApiResponse.ok(data=settings, message="Store banners updated successfully.")


# ===========================================================================
# Remedy Orders Fulfillment Management
# ===========================================================================


@router.get(
    "/orders",
    response_model=ApiResponse[ShopOrderListResponse],
    summary="List all remedy store orders with status and search filtering",
)
async def admin_list_shop_orders(
    admin: AdminUser = None,
    status: str | None = Query(default=None),
    payment_status: ShopPaymentStatus | None = Query(default=None),
    refund_status: ShopRefundStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[ShopOrderListResponse]:
    result = await ShopOrderService.list_admin_orders(
        status=status,
        payment_status=payment_status,
        refund_status=refund_status,
        search=search,
        page=page,
        limit=limit,
    )
    return ApiResponse.ok(data=result)


@router.get(
    "/orders/{order_id}",
    response_model=ApiResponse[ShopOrderOut],
    summary="Get single order details including devotee Sankalpa for temple puja printing",
)
async def admin_get_shop_order(
    order_id: str,
    admin: AdminUser = None,
) -> ApiResponse[ShopOrderOut]:
    order = await ShopOrderService.get_order_by_number_or_id(order_key=order_id)
    return ApiResponse.ok(data=order)


@router.patch(
    "/orders/{order_id}",
    response_model=ApiResponse[ShopOrderOut],
    summary="Update order fulfillment status, courier AWB tracking, and trigger COD cashback upon delivery",
)
async def admin_update_shop_order(
    order_id: str,
    payload: ShopAdminOrderUpdate,
    admin: AdminUser = None,
) -> ApiResponse[ShopOrderOut]:
    order = await ShopOrderService.update_order_by_admin(
        order_id=order_id,
        payload=payload,
        admin_id=admin.id,
    )
    return ApiResponse.ok(data=order, message="Order updated successfully.")


@router.post(
    "/orders/{order_id}/cancel",
    response_model=ApiResponse[ShopOrderOut],
    summary="Cancel order by admin with automatic stock replenishment and cashback claw-back",
)
async def admin_cancel_shop_order(
    order_id: str,
    reason: str | None = Query(default="Cancelled by store administrator"),
    admin: AdminUser = None,
) -> ApiResponse[ShopOrderOut]:
    order = await ShopOrderService.cancel_order(
        order_id=order_id,
        user_id=None,
        reason=reason,
    )
    return ApiResponse.ok(data=order, message="Order cancelled successfully.")


@router.post(
    "/orders/{order_id}/complete-refund",
    response_model=ApiResponse[ShopOrderOut],
    summary="Admin marks manual UPI/QR refund as completed, purges QR asset from Cloudinary, and notifies devotee",
)
async def admin_complete_shop_order_refund(
    order_id: str,
    payload: ShopAdminCompleteRefundPayload = Body(default_factory=ShopAdminCompleteRefundPayload),
    admin: AdminUser = None,
) -> ApiResponse[ShopOrderOut]:
    order = await ShopOrderService.complete_refund_by_admin(
        order_id=order_id,
        admin_id=admin.id,
        payload=payload,
    )
    return ApiResponse.ok(data=order, message="Refund marked as completed and notification email sent to customer.")


@router.post(
    "/inventory/sweep-abandoned",
    response_model=ApiResponse[dict],
    summary="Manually sweep expired abandoned checkouts and restore reserved stock to inventory",
)
async def admin_sweep_abandoned_inventory(
    admin: AdminUser = None,
) -> ApiResponse[dict]:
    from app.services.shop_inventory_worker import sweep_abandoned_shop_checkouts

    restored_count = await sweep_abandoned_shop_checkouts()
    return ApiResponse.ok(
        data={"restored_orders_count": restored_count},
        message=f"Swept abandoned checkouts: {restored_count} expired order(s) processed and stock safely restored.",
    )


# ===========================================================================
# Coupon Management Endpoints
# ===========================================================================


@router.get(
    "/coupons",
    response_model=ApiResponse[ShopCouponListResponse],
    summary="List all promotional discount coupons with search and active filtering",
)
async def admin_list_coupons(
    admin: AdminUser = None,
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[ShopCouponListResponse]:
    result = await shop_admin.list_coupons(
        search=search,
        is_active=is_active,
        page=page,
        limit=limit,
    )
    return ApiResponse.ok(data=result)


@router.post(
    "/coupons",
    response_model=ApiResponse[ShopCouponOut],
    summary="Create a new promotional discount coupon",
)
async def admin_create_coupon(
    payload: ShopCouponCreate,
    admin: AdminUser = None,
) -> ApiResponse[ShopCouponOut]:
    coupon = await shop_admin.create_coupon(payload)
    return ApiResponse.ok(data=coupon, message=f"Coupon '{coupon.code}' created successfully.")


@router.get(
    "/coupons/{coupon_id}",
    response_model=ApiResponse[ShopCouponOut],
    summary="Get single coupon details",
)
async def admin_get_coupon(
    coupon_id: str,
    admin: AdminUser = None,
) -> ApiResponse[ShopCouponOut]:
    coupon = await shop_admin.get_coupon(coupon_id)
    return ApiResponse.ok(data=coupon)


@router.put(
    "/coupons/{coupon_id}",
    response_model=ApiResponse[ShopCouponOut],
    summary="Update an existing discount coupon",
)
async def admin_update_coupon(
    coupon_id: str,
    payload: ShopCouponUpdate,
    admin: AdminUser = None,
) -> ApiResponse[ShopCouponOut]:
    coupon = await shop_admin.update_coupon(coupon_id, payload)
    return ApiResponse.ok(data=coupon, message=f"Coupon '{coupon.code}' updated successfully.")


@router.delete(
    "/coupons/{coupon_id}",
    response_model=ApiResponse[dict],
    summary="Delete a discount coupon",
)
async def admin_delete_coupon(
    coupon_id: str,
    admin: AdminUser = None,
) -> ApiResponse[dict]:
    await shop_admin.delete_coupon(coupon_id)
    return ApiResponse.ok(data={"deleted": True}, message="Coupon deleted successfully.")


@router.patch(
    "/coupons/{coupon_id}/toggle-active",
    response_model=ApiResponse[ShopCouponOut],
    summary="Quick 1-click active/inactive toggle for a coupon",
)
async def admin_toggle_coupon_active(
    coupon_id: str,
    admin: AdminUser = None,
) -> ApiResponse[ShopCouponOut]:
    coupon = await shop_admin.toggle_coupon_active(coupon_id)
    state = "activated" if coupon.is_active else "deactivated"
    return ApiResponse.ok(data=coupon, message=f"Coupon '{coupon.code}' {state} successfully.")


# ===========================================================================
# 7. Devotee Product Reviews & Moderation
# ===========================================================================


@router.get(
    "/reviews",
    response_model=ApiResponse[AdminProductReviewListResponse],
    summary="Admin list of customer product reviews with filtering and pagination",
)
async def admin_list_reviews(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    rating: int | None = Query(default=None, ge=1, le=5),
    is_hidden: bool | None = Query(default=None),
    product_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    admin: AdminUser = None,
) -> ApiResponse[AdminProductReviewListResponse]:
    res = await shop_review_service.admin_list_reviews(
        page=page,
        limit=limit,
        rating=rating,
        is_hidden=is_hidden,
        product_id=product_id,
        search=search,
    )
    return ApiResponse.ok(data=res)


@router.patch(
    "/reviews/{review_id}/moderate",
    response_model=ApiResponse[ProductReviewOut],
    summary="Admin hide or unhide a product review",
)
async def admin_moderate_review(
    review_id: str,
    payload: AdminReviewModerationUpdate,
    admin: AdminUser = None,
) -> ApiResponse[ProductReviewOut]:
    res = await shop_review_service.admin_moderate_review(
        review_id=review_id,
        payload=payload,
    )
    action = "hidden" if payload.is_hidden else "restored"
    return ApiResponse.ok(data=res, message=f"Review successfully {action}.")


@router.delete(
    "/reviews/{review_id}",
    response_model=ApiResponse[dict],
    summary="Admin permanently delete a product review and recalculate ratings",
)
async def admin_delete_review(
    review_id: str,
    admin: AdminUser = None,
) -> ApiResponse[dict]:
    await shop_review_service.admin_delete_review(review_id)
    return ApiResponse.ok(data={"deleted": True}, message="Review deleted successfully.")


# ===========================================================================
# 8. Order Invoices & Printable Packing Slips (Admin)
# ===========================================================================


@router.get(
    "/orders/{order_id}/invoice",
    response_model=ApiResponse[InvoiceDataOut],
    summary="Admin get order invoice data (JSON)",
)
async def admin_get_order_invoice(
    order_id: str,
    admin: AdminUser = None,
) -> ApiResponse[InvoiceDataOut]:
    data = await shop_invoice_service.get_or_create_invoice_data(
        order_key=order_id,
        is_admin=True,
    )
    return ApiResponse.ok(data=data)


@router.get(
    "/orders/{order_id}/invoice/html",
    response_class=HTMLResponse,
    summary="Admin get standalone printable HTML invoice & packing slip",
)
async def admin_get_order_invoice_html(
    order_id: str,
    auto_print: bool = Query(default=False, alias="print"),
    admin: AdminUser = None,
) -> HTMLResponse:
    data = await shop_invoice_service.get_or_create_invoice_data(
        order_key=order_id,
        is_admin=True,
    )
    html_content = shop_invoice_service.generate_invoice_html(data, auto_print=auto_print)
    return HTMLResponse(content=html_content)




