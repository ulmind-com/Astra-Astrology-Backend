"""Admin API endpoints for Astra AstroStore / Remedy E-Commerce.

Covers:
- Image uploads with automatic bounded WebP compression (preserves Cloudinary quotas & bandwidth).
- Category CRUD with product assignment checks and asset cleanup.
- Product CRUD with automatic orphaned Cloudinary asset deletion upon replacement/deletion.
- Real-time inventory overview and quick 1-click stock adjustments.
- Store Hero Carousel & Announcement Bar CMS customization.
"""

from typing import Annotated
from fastapi import APIRouter, File, Query, UploadFile

from app.api.dependencies import AdminUser
from app.schemas.common import ApiResponse
from app.schemas.shop import (
    InventorySummaryResponse,
    ProductCategoryCreate,
    ProductCategoryOut,
    ProductCategoryUpdate,
    ProductCreate,
    ProductListResponse,
    ProductOut,
    ProductUpdate,
    ShopBannerSettingsOut,
    ShopBannerSettingsUpdate,
    StockUpdatePayload,
)
from app.services import shop_admin
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
    response_model=ApiResponse[dict[str, bool]],
    summary="Delete product and purge all associated images from Cloudinary",
)
async def delete_shop_product(
    product_id: str,
    admin: AdminUser = None,
) -> ApiResponse[dict[str, bool]]:
    await shop_admin.delete_product(product_id)
    return ApiResponse.ok(data={"deleted": True}, message="Product deleted successfully.")


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
