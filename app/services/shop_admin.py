"""Astra AstroStore Admin & Inventory Service Layer.

Handles:
- Product and Category CRUD.
- Automatic Cloudinary cleanup on image replacement and product deletion.
- Quick inline stock updates and inventory valuation calculations.
- Store hero banner & announcement CMS customization.
"""

import asyncio
from datetime import UTC, datetime, timedelta
import re
import time
from typing import Any
from beanie import PydanticObjectId
from beanie.operators import In, RegEx
from loguru import logger

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import safe_regex_pattern
from app.models.enums import CouponDiscountType
from app.models.cms import (
    CMS_KEY_SHOP,
    ShopCMS,
    default_shop_hero_banners,
    default_shop_reels,
)
from app.models.shop import Product, ProductCategory, ShopCoupon, ShopOrder
from app.schemas.shop import (
    CloudinaryOrphanCleanupReport,
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
    ShopCouponCreate,
    ShopCouponListResponse,
    ShopCouponOut,
    ShopCouponUpdate,
    StockUpdatePayload,
)
from app.services.storage import extract_public_id_from_url, safe_delete_cloudinary_image


def slugify(text: str) -> str:
    """Generates a URL-friendly slug from string."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def _product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=str(p.id),
        title=p.title,
        slug=p.slug,
        sku=p.sku,
        short_description=p.short_description,
        detailed_description=p.detailed_description,
        category_id=str(p.category_id),
        category_slug=p.category_slug,
        category_type=p.category_type,
        ruling_planet=p.ruling_planet,
        deity=p.deity,
        benefits=p.benefits or [],
        life_pillars=p.life_pillars or [],
        purpose_tags=getattr(p, "purpose_tags", []) or [],
        recommended_for_rashis=p.recommended_for_rashis or [],
        crystal_type=getattr(p, "crystal_type", None),
        beej_mantra=p.beej_mantra,
        wear_instructions=p.wear_instructions,
        free_gift_title=getattr(p, "free_gift_title", None),
        free_gift_value=getattr(p, "free_gift_value", None),
        free_gift_badge=getattr(p, "free_gift_badge", None),
        free_gift_image_url=getattr(p, "free_gift_image_url", None),
        cashback_percent=getattr(p, "cashback_percent", None),
        lab_certified=getattr(p, "lab_certified", True),
        lab_certificate_name=getattr(p, "lab_certificate_name", "Govt. Approved Gemological Lab"),
        lab_certificate_number=getattr(p, "lab_certificate_number", None),
        mrp=p.mrp,
        sale_price=p.sale_price,
        cost_price=p.cost_price,
        discount_percent=p.discount_percent,
        stock_quantity=p.stock_quantity,
        low_stock_threshold=p.low_stock_threshold,
        weight_grams=p.weight_grams,
        in_stock=p.in_stock,
        is_low_stock=p.is_low_stock,
        images=p.images or [],
        featured_image=p.featured_image,
        video_url=p.video_url,
        certificate_image_url=p.certificate_image_url,
        is_active=p.is_active,
        is_featured=p.is_featured,
        is_energized=p.is_energized,
        is_deleted=getattr(p, "is_deleted", False),
        average_rating=p.average_rating,
        review_count=p.review_count,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


# ===========================================================================
# Category Management
# ===========================================================================

_CATEGORIES_CACHE: dict[bool, tuple[float, list[ProductCategoryOut]]] = {}
_PUBLIC_PRODUCTS_CACHE: dict[tuple[Any, ...], tuple[float, ProductListResponse]] = {}
_SHOP_CATALOG_CACHE_TTL_SECONDS = 25.0


def invalidate_shop_catalog_cache() -> None:
    """Invalidates cached category & product lists upon admin or inventory updates."""
    _CATEGORIES_CACHE.clear()
    _PUBLIC_PRODUCTS_CACHE.clear()


async def list_categories(include_inactive: bool = True) -> list[ProductCategoryOut]:
    """Returns all categories with accurate product counts, excluding soft-deleted ones."""
    now = time.monotonic()
    cached = _CATEGORIES_CACHE.get(include_inactive)
    if cached is not None and (now - cached[0]) < _SHOP_CATALOG_CACHE_TTL_SECONDS:
        return cached[1]

    query: dict[str, Any] = {"is_deleted": False}
    if not include_inactive:
        query["is_active"] = True

    async def _fetch_counts() -> dict[str, int]:
        counts_cursor = Product.aggregate([
            {"$match": {"is_deleted": False}},
            {"$group": {"_id": "$category_id", "count": {"$sum": 1}}},
        ])
        counts_map: dict[str, int] = {}
        async for row in counts_cursor:
            if row.get("_id"):
                counts_map[str(row["_id"])] = row["count"]
        return counts_map

    cats, counts_map = await asyncio.gather(
        ProductCategory.find(query).sort("+display_order", "+name").to_list(),
        _fetch_counts(),
    )

    res = []
    for c in cats:
        cid = str(c.id)
        res.append(
            ProductCategoryOut(
                id=cid,
                name=c.name,
                slug=c.slug,
                description=c.description,
                icon_url=c.icon_url,
                banner_url=c.banner_url,
                category_type=c.category_type,
                parent_id=str(c.parent_id) if c.parent_id else None,
                display_order=c.display_order,
                is_active=c.is_active,
                seo_title=c.seo_title,
                seo_description=c.seo_description,
                product_count=counts_map.get(cid, 0),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    _CATEGORIES_CACHE[include_inactive] = (now, res)
    return res


async def create_category(payload: ProductCategoryCreate) -> ProductCategoryOut:
    """Creates a new remedy product category."""
    slug = slugify(payload.slug or payload.name)
    existing = await ProductCategory.find_one(ProductCategory.slug == slug)
    if existing:
        slug = f"{slug}-{PydanticObjectId()[:4]}"

    parent_oid = PydanticObjectId(payload.parent_id) if payload.parent_id else None

    cat = ProductCategory(
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        icon_url=payload.icon_url,
        banner_url=payload.banner_url,
        category_type=payload.category_type,
        parent_id=parent_oid,
        display_order=payload.display_order,
        is_active=payload.is_active,
        seo_title=payload.seo_title,
        seo_description=payload.seo_description,
    )
    await cat.insert()
    invalidate_shop_catalog_cache()
    logger.info("Created product category '{}' (id={})", cat.name, cat.id)
    return ProductCategoryOut(
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


async def update_category(cat_id: str, payload: ProductCategoryUpdate) -> ProductCategory:
    """Updates category details and cleans up replaced media assets."""
    try:
        oid = PydanticObjectId(cat_id)
    except Exception:
        raise BadRequestError("Invalid category ID format.")

    cat = await ProductCategory.get(oid)
    if not cat:
        raise NotFoundError("Category not found.", error_code="category_not_found")

    old_banner = cat.banner_url
    old_icon = cat.icon_url

    if payload.name is not None:
        cat.name = payload.name.strip()
    if payload.slug is not None:
        cat.slug = slugify(payload.slug)
    if payload.description is not None:
        cat.description = payload.description
    if payload.icon_url is not None:
        if old_icon and old_icon != payload.icon_url:
            await safe_delete_cloudinary_image(old_icon)
        cat.icon_url = payload.icon_url
    if payload.banner_url is not None:
        if old_banner and old_banner != payload.banner_url:
            await safe_delete_cloudinary_image(old_banner)
        cat.banner_url = payload.banner_url
    if payload.category_type is not None:
        cat.category_type = payload.category_type
    if payload.parent_id is not None:
        cat.parent_id = PydanticObjectId(payload.parent_id) if payload.parent_id else None
    if payload.display_order is not None:
        cat.display_order = payload.display_order
    if payload.is_active is not None:
        cat.is_active = payload.is_active
    if payload.seo_title is not None:
        cat.seo_title = payload.seo_title
    if payload.seo_description is not None:
        cat.seo_description = payload.seo_description

    await cat.save()
    invalidate_shop_catalog_cache()
    return cat


async def delete_category(cat_id: str) -> bool:
    """Soft-deletes category if no active products are assigned to it."""
    try:
        oid = PydanticObjectId(cat_id)
    except Exception:
        raise BadRequestError("Invalid category ID format.")

    cat = await ProductCategory.get(oid)
    if not cat:
        raise NotFoundError("Category not found.")

    assigned_count = await Product.find(Product.category_id == oid, Product.is_deleted == False).count()
    if assigned_count > 0:
        raise BadRequestError(
            f"Cannot delete category with {assigned_count} active products. Reassign or delete products first."
        )

    # Clean up associated assets from Cloudinary
    if cat.banner_url:
        await safe_delete_cloudinary_image(cat.banner_url)
    if cat.icon_url:
        await safe_delete_cloudinary_image(cat.icon_url)

    cat.is_deleted = True
    cat.is_active = False
    cat.deleted_at = datetime.now(UTC)
    await cat.save()
    invalidate_shop_catalog_cache()
    logger.info("Soft-deleted category '{}' (id={})", cat.name, cat.id)
    return True


# ===========================================================================
# Product Management & Old Image Purging
# ===========================================================================


async def list_products(
    search: str | None = None,
    category_id: str | None = None,
    ruling_planet: str | None = None,
    stock_status: str | None = None,  # 'in_stock', 'low_stock', 'out_of_stock'
    is_active: bool | None = None,
    is_featured: bool | None = None,
    include_deleted: bool = False,
    archived_only: bool = False,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "-created_at",
) -> ProductListResponse:
    """Lists products with comprehensive search, filters, and pagination."""
    skip = (page - 1) * limit
    filters: list[Any] = []

    if archived_only:
        filters.append(Product.is_deleted == True)
    elif not include_deleted:
        filters.append(Product.is_deleted == False)
    if is_active is not None:
        filters.append(Product.is_active == is_active)
    if is_featured is not None:
        filters.append(Product.is_featured == is_featured)
    if category_id:
        try:
            filters.append(Product.category_id == PydanticObjectId(category_id))
        except Exception:
            pass
    if ruling_planet:
        filters.append(RegEx(Product.ruling_planet, f"^{re.escape(ruling_planet.strip())}$", "i"))

    if stock_status == "out_of_stock":
        filters.append(Product.stock_quantity == 0)
    elif stock_status == "low_stock":
        # stock_quantity > 0 and <= low_stock_threshold
        filters.append({"stock_quantity": {"$gt": 0, "$lte": 5}})
    elif stock_status == "in_stock":
        filters.append(Product.stock_quantity > 0)

    if search and search.strip():
        pat = safe_regex_pattern(search)
        regex_filter = {
            "$or": [
                {"title": pat},
                {"sku": pat},
                {"short_description": pat},
                {"benefits": pat},
            ]
        }
        filters.append(regex_filter)

    is_public_catalog = is_active is True and not include_deleted and not archived_only
    cache_key = (
        search or "",
        category_id or "",
        ruling_planet or "",
        stock_status or "",
        is_featured,
        page,
        limit,
        sort_by,
    )
    now = time.monotonic()
    if is_public_catalog:
        cached = _PUBLIC_PRODUCTS_CACHE.get(cache_key)
        if cached is not None and (now - cached[0]) < _SHOP_CATALOG_CACHE_TTL_SECONDS:
            return cached[1]

    query = Product.find(*filters) if filters else Product.find_all()
    total, items = await asyncio.gather(
        query.count(),
        query.sort(sort_by).skip(skip).limit(limit).to_list(),
    )

    result = ProductListResponse(
        items=[_product_out(p) for p in items],
        total=total,
        page=page,
        limit=limit,
        has_more=(skip + len(items)) < total,
    )
    if is_public_catalog:
        if len(_PUBLIC_PRODUCTS_CACHE) >= 100:
            _PUBLIC_PRODUCTS_CACHE.clear()
        _PUBLIC_PRODUCTS_CACHE[cache_key] = (now, result)
    return result


async def get_product_by_id_or_slug(id_or_slug: str) -> ProductOut:
    """Retrieves product by ObjectId or SEO slug."""
    product = None
    try:
        oid = PydanticObjectId(id_or_slug)
        product = await Product.get(oid)
    except Exception:
        pass

    if not product:
        product = await Product.find_one(Product.slug == id_or_slug)

    if not product:
        raise NotFoundError("Product not found.", error_code="product_not_found")

    return _product_out(product)


async def create_product(payload: ProductCreate) -> ProductOut:
    """Creates a new remedy product with unique slug, SKU, and category link."""
    try:
        cat_oid = PydanticObjectId(payload.category_id)
    except Exception:
        raise BadRequestError("Invalid category ID format.")

    category = await ProductCategory.get(cat_oid)
    if not category:
        raise NotFoundError("Category not found.", error_code="category_not_found")

    slug = slugify(payload.slug or payload.title)
    existing_slug = await Product.find_one(Product.slug == slug)
    if existing_slug:
        slug = f"{slug}-{str(PydanticObjectId())[:6]}"

    sku = (payload.sku or f"ASTRA-{slug[:8].upper()}-{str(PydanticObjectId())[:4].upper()}").strip()
    existing_sku = await Product.find_one(Product.sku == sku)
    if existing_sku:
        sku = f"{sku}-{str(PydanticObjectId())[:4].upper()}"

    product = Product(
        title=payload.title.strip(),
        slug=slug,
        sku=sku,
        short_description=payload.short_description.strip(),
        detailed_description=payload.detailed_description.strip(),
        category_id=cat_oid,
        category_slug=category.slug,
        category_type=payload.category_type or category.category_type,
        ruling_planet=payload.ruling_planet,
        deity=payload.deity,
        benefits=payload.benefits,
        life_pillars=payload.life_pillars,
        purpose_tags=payload.purpose_tags or [],
        recommended_for_rashis=payload.recommended_for_rashis,
        crystal_type=payload.crystal_type,
        beej_mantra=payload.beej_mantra,
        wear_instructions=payload.wear_instructions,
        free_gift_title=payload.free_gift_title,
        free_gift_value=payload.free_gift_value,
        free_gift_badge=payload.free_gift_badge,
        free_gift_image_url=payload.free_gift_image_url,
        cashback_percent=payload.cashback_percent,
        lab_certified=payload.lab_certified if payload.lab_certified is not None else True,
        lab_certificate_name=payload.lab_certificate_name,
        lab_certificate_number=payload.lab_certificate_number,
        mrp=payload.mrp,
        sale_price=payload.sale_price,
        cost_price=payload.cost_price,
        stock_quantity=payload.stock_quantity,
        low_stock_threshold=payload.low_stock_threshold,
        weight_grams=payload.weight_grams,
        images=payload.images or ([payload.featured_image] if payload.featured_image else []),
        featured_image=payload.featured_image,
        video_url=payload.video_url,
        certificate_image_url=payload.certificate_image_url,
        is_active=payload.is_active,
        is_featured=payload.is_featured,
        is_energized=payload.is_energized,
    )
    await product.insert()
    invalidate_shop_catalog_cache()
    logger.info("Created remedy product '{}' (SKU={}, id={})", product.title, product.sku, product.id)
    return _product_out(product)


async def update_product(prod_id: str, payload: ProductUpdate) -> ProductOut:
    """Updates product and automatically cleans up discarded images from Cloudinary."""
    try:
        oid = PydanticObjectId(prod_id)
    except Exception:
        raise BadRequestError("Invalid product ID format.")

    product = await Product.get(oid)
    if not product:
        raise NotFoundError("Product not found.", error_code="product_not_found")

    old_images = set(product.images or [])
    if product.featured_image:
        old_images.add(product.featured_image)
    if product.certificate_image_url:
        old_images.add(product.certificate_image_url)

    fields_set = payload.model_fields_set

    if payload.category_id is not None:
        cat_oid = PydanticObjectId(payload.category_id)
        cat = await ProductCategory.get(cat_oid)
        if cat:
            product.category_id = cat_oid
            product.category_slug = cat.slug
            if payload.category_type is None:
                product.category_type = cat.category_type

    if payload.title is not None:
        product.title = payload.title.strip()
    if payload.slug is not None:
        product.slug = slugify(payload.slug)
    if payload.sku is not None:
        product.sku = payload.sku.strip()
    if payload.short_description is not None:
        product.short_description = payload.short_description.strip()
    if payload.detailed_description is not None:
        product.detailed_description = payload.detailed_description.strip()
    if payload.category_type is not None:
        product.category_type = payload.category_type
    if payload.ruling_planet is not None:
        product.ruling_planet = payload.ruling_planet
    if payload.deity is not None:
        product.deity = payload.deity
    if payload.benefits is not None:
        product.benefits = payload.benefits
    if payload.life_pillars is not None:
        product.life_pillars = payload.life_pillars
    if payload.purpose_tags is not None:
        product.purpose_tags = payload.purpose_tags
    if payload.recommended_for_rashis is not None:
        product.recommended_for_rashis = payload.recommended_for_rashis
    if payload.crystal_type is not None:
        product.crystal_type = payload.crystal_type
    if payload.beej_mantra is not None:
        product.beej_mantra = payload.beej_mantra
    if payload.wear_instructions is not None:
        product.wear_instructions = payload.wear_instructions
    if "free_gift_title" in fields_set:
        product.free_gift_title = payload.free_gift_title
    if "free_gift_value" in fields_set:
        product.free_gift_value = payload.free_gift_value
    if "free_gift_badge" in fields_set:
        product.free_gift_badge = payload.free_gift_badge
    if "free_gift_image_url" in fields_set:
        product.free_gift_image_url = payload.free_gift_image_url
    if "cashback_percent" in fields_set:
        product.cashback_percent = payload.cashback_percent
    if payload.lab_certified is not None:
        product.lab_certified = payload.lab_certified
    if payload.lab_certificate_name is not None:
        product.lab_certificate_name = payload.lab_certificate_name
    if "lab_certificate_number" in fields_set:
        product.lab_certificate_number = payload.lab_certificate_number
    if payload.mrp is not None:
        product.mrp = payload.mrp
    if payload.sale_price is not None:
        product.sale_price = payload.sale_price
    if payload.cost_price is not None:
        product.cost_price = payload.cost_price
    if payload.stock_quantity is not None:
        product.stock_quantity = payload.stock_quantity
    if payload.low_stock_threshold is not None:
        product.low_stock_threshold = payload.low_stock_threshold
    if payload.weight_grams is not None:
        product.weight_grams = payload.weight_grams
    if payload.images is not None:
        product.images = payload.images
    if payload.featured_image is not None:
        product.featured_image = payload.featured_image
    if "video_url" in fields_set:
        product.video_url = payload.video_url
    if "certificate_image_url" in fields_set:
        product.certificate_image_url = payload.certificate_image_url
    if payload.is_active is not None:
        product.is_active = payload.is_active
    if payload.is_featured is not None:
        product.is_featured = payload.is_featured
    if payload.is_energized is not None:
        product.is_energized = payload.is_energized

    await product.save()
    invalidate_shop_catalog_cache()

    # Determine orphaned images that are no longer part of this product
    new_images = set(product.images or [])
    if product.featured_image:
        new_images.add(product.featured_image)
    if product.certificate_image_url:
        new_images.add(product.certificate_image_url)

    orphaned_images = old_images - new_images
    for orphan_url in orphaned_images:
        logger.info("Purging orphaned Cloudinary image on product update: {}", orphan_url)
        await safe_delete_cloudinary_image(orphan_url)

    return _product_out(product)


async def delete_product(prod_id: str, hard_delete: bool = False) -> dict[str, Any]:
    """Deletes or soft-deletes product.
    If the product has ever been ordered, soft-deletes it to preserve customer order
    history and invoice audits while hiding it from the public store.
    """
    try:
        oid = PydanticObjectId(prod_id)
    except Exception:
        raise BadRequestError("Invalid product ID format.")

    product = await Product.get(oid)
    if not product:
        raise NotFoundError("Product not found.")

    # Check if this product was ever part of any order
    order_count = await ShopOrder.find({"items.product_id": oid}).count()

    if order_count > 0 or not hard_delete:
        # SOFT DELETE: preserves tax invoices, historical orders, and avoids data corruption
        product.is_deleted = True
        product.is_active = False
        product.deleted_at = datetime.now(UTC)
        await product.save()
        invalidate_shop_catalog_cache()
        logger.info(
            "Soft-deleted product '{}' (id={}, had {} orders). Preserving Cloudinary images for order history.",
            product.title,
            product.id,
            order_count,
        )
        return {
            "deleted": True,
            "mode": "soft_delete",
            "message": "Product soft-deleted and archived to preserve order history.",
        }

    # If NEVER ordered and hard_delete explicitly requested:
    all_images = set(product.images or [])
    if product.featured_image:
        all_images.add(product.featured_image)
    if product.certificate_image_url:
        all_images.add(product.certificate_image_url)

    for img_url in all_images:
        await safe_delete_cloudinary_image(img_url)

    await product.delete()
    invalidate_shop_catalog_cache()
    logger.info("Hard-deleted product '{}' and purged {} Cloudinary images", product.title, len(all_images))
    return {
        "deleted": True,
        "mode": "hard_delete",
        "message": f"Product permanently deleted and {len(all_images)} Cloudinary images purged.",
    }


async def restore_product(prod_id: str) -> ProductOut:
    """Restores a soft-deleted product back to the active catalog."""
    try:
        oid = PydanticObjectId(prod_id)
    except Exception:
        raise BadRequestError("Invalid product ID format.")

    product = await Product.get(oid)
    if not product:
        raise NotFoundError("Product not found.")

    product.is_deleted = False
    product.deleted_at = None
    product.is_active = True
    await product.save()
    invalidate_shop_catalog_cache()
    logger.info("Restored product '{}' (id={})", product.title, product.id)
    return _product_out(product)


# ===========================================================================
# Concurrency & Atomic Stock Reservation Helpers
# ===========================================================================


async def atomic_reserve_stock(prod_id: str | PydanticObjectId, quantity: int) -> bool:
    """Atomically decrements stock if sufficient quantity exists using MongoDB's $inc.
    Prevents race conditions where two simultaneous checkouts exceed available stock.
    Returns True if successfully reserved, False if out-of-stock or concurrent conflict.
    """
    if quantity <= 0:
        return False
    oid = PydanticObjectId(prod_id) if isinstance(prod_id, str) else prod_id
    collection = Product.get_pymongo_collection()
    res = await collection.update_one(
        {
            "_id": oid,
            "stock_quantity": {"$gte": quantity},
            "is_deleted": False,
            "is_active": True,
        },
        {"$inc": {"stock_quantity": -quantity}},
    )
    if res.modified_count > 0:
        invalidate_shop_catalog_cache()
    return res.modified_count > 0


async def atomic_release_stock(prod_id: str | PydanticObjectId, quantity: int) -> bool:
    """Atomically releases reserved stock back to warehouse (e.g. upon payment failure or order cancellation)."""
    if quantity <= 0:
        return False
    oid = PydanticObjectId(prod_id) if isinstance(prod_id, str) else prod_id
    collection = Product.get_pymongo_collection()
    res = await collection.update_one(
        {"_id": oid},
        {"$inc": {"stock_quantity": quantity}},
    )
    if res.modified_count > 0:
        invalidate_shop_catalog_cache()
    return res.modified_count > 0


async def update_stock(prod_id: str, payload: StockUpdatePayload) -> ProductOut:
    """Modifies inventory count inline (mode='set', 'add', 'subtract') atomically."""
    try:
        oid = PydanticObjectId(prod_id)
    except Exception:
        raise BadRequestError("Invalid product ID format.")

    product = await Product.get(oid)
    if not product:
        raise NotFoundError("Product not found.")

    old_stock = product.stock_quantity
    collection = Product.get_pymongo_collection()

    if payload.mode == "add":
        await collection.update_one({"_id": oid}, {"$inc": {"stock_quantity": payload.quantity}})
    elif payload.mode == "subtract":
        new_val = max(0, product.stock_quantity - payload.quantity)
        await collection.update_one({"_id": oid}, {"$set": {"stock_quantity": new_val}})
    else:  # set
        await collection.update_one({"_id": oid}, {"$set": {"stock_quantity": max(0, payload.quantity)}})

    updated_product = await Product.get(oid)
    if not updated_product:
        raise NotFoundError("Product not found.")

    invalidate_shop_catalog_cache()
    logger.info(
        "Stock updated for '{}' (SKU={}): {} -> {} (reason: {})",
        updated_product.title,
        updated_product.sku,
        old_stock,
        updated_product.stock_quantity,
        payload.reason or "Admin manual update",
    )
    return _product_out(updated_product)


async def get_inventory_summary() -> InventorySummaryResponse:
    """Computes real-time warehouse metrics, stock-out counts, and valuations via DB aggregation."""
    col = Product.get_pymongo_collection()
    cursor = await col.aggregate([
        {"$match": {"is_deleted": False}},
        {
            "$group": {
                "_id": None,
                "total_products": {"$sum": 1},
                "out_of_stock": {"$sum": {"$cond": [{"$eq": ["$stock_quantity", 0]}, 1, 0]}},
                "low_stock": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$gt": ["$stock_quantity", 0]},
                                    {"$lte": ["$stock_quantity", {"$ifNull": ["$low_stock_threshold", 5]}]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "healthy_stock": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$stock_quantity", {"$ifNull": ["$low_stock_threshold", 5]}]},
                            1,
                            0,
                        ]
                    }
                },
                "total_units": {"$sum": "$stock_quantity"},
                "valuation_mrp": {"$sum": {"$multiply": ["$stock_quantity", {"$ifNull": ["$mrp", 0]}]}},
                "valuation_cost": {
                    "$sum": {
                        "$multiply": [
                            "$stock_quantity",
                            {"$ifNull": ["$cost_price", {"$multiply": [{"$ifNull": ["$sale_price", 0]}, 0.6]}]},
                        ]
                    }
                },
            }
        },
    ])
    rows = [r async for r in cursor]
    row = rows[0] if rows else {}
    return InventorySummaryResponse(
        total_products=int(row.get("total_products", 0) or 0),
        out_of_stock_count=int(row.get("out_of_stock", 0) or 0),
        low_stock_count=int(row.get("low_stock", 0) or 0),
        healthy_stock_count=int(row.get("healthy_stock", 0) or 0),
        total_stock_units=int(row.get("total_units", 0) or 0),
        total_inventory_valuation_mrp=round(float(row.get("valuation_mrp", 0.0) or 0.0), 2),
        total_inventory_valuation_cost=round(float(row.get("valuation_cost", 0.0) or 0.0), 2),
    )


# ===========================================================================
# Store Banners & Hero Offers CMS
# ===========================================================================

import time

_cached_shop_banner_settings: ShopBannerSettingsOut | None = None
_cached_shop_banner_time: float = 0.0
_SHOP_BANNER_CACHE_TTL: float = 120.0  # Cache in memory for 2 minutes


def invalidate_shop_banner_cache() -> None:
    """Invalidates the in-memory cache for Shop CMS banner settings."""
    global _cached_shop_banner_settings, _cached_shop_banner_time
    _cached_shop_banner_settings = None
    _cached_shop_banner_time = 0.0


async def get_shop_banner_settings(force_refresh: bool = False) -> ShopBannerSettingsOut:
    """Returns store announcement bar, marquee, cashback, free gift, and hero carousel configurations.
    Uses in-memory caching (120s TTL) for lightning-fast (<1ms) response times.
    """
    global _cached_shop_banner_settings, _cached_shop_banner_time
    now = time.monotonic()
    if not force_refresh and _cached_shop_banner_settings is not None and (now - _cached_shop_banner_time) < _SHOP_BANNER_CACHE_TTL:
        return _cached_shop_banner_settings

    cms = None
    try:
        cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
    except Exception as exc:
        logger.warning("Could not read ShopCMS from DB: {}", exc)

    if not cms:
        cms = ShopCMS(key=CMS_KEY_SHOP)
        try:
            await cms.insert()
        except Exception:
            pass

    banners = cms.hero_banners if cms.hero_banners else default_shop_hero_banners()
    reels = getattr(cms, "reels", None)
    if not reels:
        reels = default_shop_reels()

    result = ShopBannerSettingsOut(
        announcement_bar_text=cms.announcement_bar_text,
        announcement_bar_link=cms.announcement_bar_link,
        announcement_bar_active=cms.announcement_bar_active,
        marquee_items=getattr(cms, "marquee_items", []) or [],
        hero_banners=banners,
        cashback_enabled=getattr(cms, "cashback_enabled", True),
        cashback_percent=getattr(cms, "cashback_percent", 100),
        cashback_max_cap_inr=getattr(cms, "cashback_max_cap_inr", None),
        cashback_credit_timing=getattr(cms, "cashback_credit_timing", "on_delivery") or "on_delivery",
        allow_user_cancellation=getattr(cms, "allow_user_cancellation", True),
        cancellation_grace_hours=getattr(cms, "cancellation_grace_hours", 24),
        refund_sla_days=getattr(cms, "refund_sla_days", 3),
        free_gift_enabled=getattr(cms, "free_gift_enabled", False),
        free_gift_min_cart_value=getattr(cms, "free_gift_min_cart_value", 0.0),
        free_gift_default_title=getattr(cms, "free_gift_default_title", None),
        free_gift_default_value=getattr(cms, "free_gift_default_value", 0.0),
        free_gift_default_badge=getattr(cms, "free_gift_default_badge", None),
        free_gift_default_image_url=getattr(cms, "free_gift_default_image_url", None),
        free_shipping_threshold=getattr(cms, "free_shipping_threshold", 499.0),
        standard_shipping_fee=getattr(cms, "standard_shipping_fee", 70.0),
        cod_enabled=getattr(cms, "cod_enabled", True),
        cod_extra_charge=getattr(cms, "cod_extra_charge", 0.0),
        checkout_reservation_minutes=getattr(cms, "checkout_reservation_minutes", 20) or 20,
        cod_max_rto_allowed=getattr(cms, "cod_max_rto_allowed", 2) or 2,
        cod_blacklisted_phones=getattr(cms, "cod_blacklisted_phones", []) or [],
        reels=reels,
        company_legal_name=getattr(cms, "company_legal_name", "DivinLink Spiritual Technologies Pvt. Ltd."),
        company_trade_name=getattr(cms, "company_trade_name", "DivinLink / Astra AstroStore"),
        company_address=getattr(cms, "company_address", "Kashi Vishwanath Temple Corridor, Dashashwamedh Ghat, Varanasi, Uttar Pradesh - 221001, India"),
        company_state=getattr(cms, "company_state", "Uttar Pradesh"),
        company_state_code=getattr(cms, "company_state_code", "09"),
        company_phone=getattr(cms, "company_phone", "+91 91530 08182"),
        company_email=getattr(cms, "company_email", "support@divinlink.com"),
        company_website=getattr(cms, "company_website", "https://www.divinlink.com"),
        company_pan=getattr(cms, "company_pan", None),
        company_gstin=getattr(cms, "company_gstin", None),
        invoice_prefix=getattr(cms, "invoice_prefix", "DIVIN-INV"),
        invoice_footer_notes=getattr(cms, "invoice_footer_notes", "Thank you for welcoming divine vibrations into your sacred home! May Lord Shiva and the Navagrahas bestow eternal peace, health, and prosperity."),
    )
    _cached_shop_banner_settings = result
    _cached_shop_banner_time = now
    return result


async def update_shop_banner_settings(payload: ShopBannerSettingsUpdate) -> ShopBannerSettingsOut:
    """Saves updated store promotional banners, 100% cashback rules, free gift defaults, and logistics settings."""
    cms = await ShopCMS.find_one(ShopCMS.key == CMS_KEY_SHOP)
    if not cms:
        cms = ShopCMS(key=CMS_KEY_SHOP)

    cms.announcement_bar_text = payload.announcement_bar_text
    cms.announcement_bar_link = payload.announcement_bar_link
    cms.announcement_bar_active = payload.announcement_bar_active
    cms.marquee_items = payload.marquee_items
    cms.hero_banners = [b.model_dump() for b in payload.hero_banners]
    cms.cashback_enabled = payload.cashback_enabled
    cms.cashback_percent = payload.cashback_percent
    cms.cashback_max_cap_inr = payload.cashback_max_cap_inr
    cms.cashback_credit_timing = payload.cashback_credit_timing or "on_delivery"
    cms.allow_user_cancellation = payload.allow_user_cancellation
    cms.cancellation_grace_hours = payload.cancellation_grace_hours
    cms.refund_sla_days = payload.refund_sla_days
    cms.free_gift_enabled = payload.free_gift_enabled
    cms.free_gift_min_cart_value = payload.free_gift_min_cart_value
    cms.free_gift_default_title = payload.free_gift_default_title
    cms.free_gift_default_value = payload.free_gift_default_value
    cms.free_gift_default_badge = payload.free_gift_default_badge
    cms.free_gift_default_image_url = payload.free_gift_default_image_url
    cms.free_shipping_threshold = payload.free_shipping_threshold
    cms.standard_shipping_fee = payload.standard_shipping_fee
    cms.cod_enabled = payload.cod_enabled
    cms.cod_extra_charge = payload.cod_extra_charge
    cms.checkout_reservation_minutes = payload.checkout_reservation_minutes or 20
    cms.cod_max_rto_allowed = payload.cod_max_rto_allowed or 2
    cms.cod_blacklisted_phones = [p.strip() for p in payload.cod_blacklisted_phones if p.strip()]
    cms.reels = [r.model_dump() for r in payload.reels]
    cms.company_legal_name = payload.company_legal_name
    cms.company_trade_name = payload.company_trade_name
    cms.company_address = payload.company_address
    cms.company_state = payload.company_state
    cms.company_state_code = payload.company_state_code
    cms.company_phone = payload.company_phone
    cms.company_email = payload.company_email
    cms.company_website = payload.company_website
    cms.company_pan = payload.company_pan.strip() if payload.company_pan else None
    cms.company_gstin = payload.company_gstin.strip().upper() if payload.company_gstin else None
    cms.invoice_prefix = payload.invoice_prefix.strip().upper() if payload.invoice_prefix else "DIVIN-INV"
    cms.invoice_footer_notes = payload.invoice_footer_notes

    await cms.save()
    invalidate_shop_banner_cache()
    logger.info("Updated Shop CMS store settings (cashback_percent={}%, free_shipping_threshold={})", cms.cashback_percent, cms.free_shipping_threshold)
    return await get_shop_banner_settings(force_refresh=True)


# ===========================================================================
# Cloudinary Orphan Asset Garbage Collection
# ===========================================================================


async def purge_unreferenced_cloudinary_shop_images(dry_run: bool = False) -> CloudinaryOrphanCleanupReport:
    """Discovers and purges orphaned Cloudinary image assets created in 'products/' folder
    that are not referenced by any Product, Category, or Store CMS banner.
    Protects storage quota from abandoned uploads and cancelled form edits.
    """
    import cloudinary.api

    # 1. Gather all referenced Cloudinary public IDs across database
    referenced_ids: set[str] = set()

    # Active and archived products (we do NOT purge images of soft-deleted products since past orders need them)
    prods = await Product.find_all().to_list()
    for p in prods:
        all_imgs = list(p.images or [])
        if p.featured_image:
            all_imgs.append(p.featured_image)
        if p.certificate_image_url:
            all_imgs.append(p.certificate_image_url)
        for u in all_imgs:
            pid = extract_public_id_from_url(u)
            if pid:
                referenced_ids.add(pid)

    # Categories
    cats = await ProductCategory.find_all().to_list()
    for c in cats:
        for u in [c.icon_url, c.banner_url]:
            pid = extract_public_id_from_url(u)
            if pid:
                referenced_ids.add(pid)

    # Store CMS Banners
    cms = await ShopCMS.find_one(ShopCMS.key == CMS_KEY_SHOP)
    if cms and cms.hero_banners:
        for b in cms.hero_banners:
            u = b.get("image_url") if isinstance(b, dict) else getattr(b, "image_url", None)
            pid = extract_public_id_from_url(u)
            if pid:
                referenced_ids.add(pid)

    # 2. Query Cloudinary assets in 'products/' folder
    scanned_count = 0
    orphaned_ids: list[str] = []
    cutoff_time = datetime.now(UTC) - timedelta(hours=2)  # safety buffer for in-flight uploads

    try:
        response = await asyncio.to_thread(
            cloudinary.api.resources,
            type="upload",
            prefix="products/",
            max_results=500,
        )
        resources = response.get("resources", [])
        scanned_count = len(resources)

        for res in resources:
            public_id = res.get("public_id")
            created_at_str = res.get("created_at")
            if not public_id:
                continue

            # Check if referenced
            if public_id not in referenced_ids:
                try:
                    # Cloudinary created_at format: '2026-11-08T07:12:34Z'
                    created_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    if created_dt < cutoff_time:
                        orphaned_ids.append(public_id)
                except Exception:
                    orphaned_ids.append(public_id)

    except Exception as exc:
        logger.warning("Cloudinary API search exception (likely mock or network): {}", exc)

    purged_count = 0
    failed_count = 0
    purged_list: list[str] = []

    if not dry_run:
        import cloudinary.uploader

        for pid in orphaned_ids:
            try:
                res = await asyncio.to_thread(cloudinary.uploader.destroy, pid, invalidate=True)
                if res.get("result") in ["ok", "not found"]:
                    purged_count += 1
                    purged_list.append(pid)
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
    else:
        purged_list = orphaned_ids

    logger.info(
        "Cloudinary Shop Image GC: scanned={}, referenced={}, orphaned={}, purged={}, dry_run={}",
        scanned_count,
        len(referenced_ids),
        len(orphaned_ids),
        purged_count,
        dry_run,
    )

    return CloudinaryOrphanCleanupReport(
        scanned_count=scanned_count,
        referenced_count=len(referenced_ids),
        orphaned_found_count=len(orphaned_ids),
        purged_count=purged_count if not dry_run else 0,
        failed_count=failed_count,
        dry_run=dry_run,
        purged_public_ids=purged_list,
    )


# ===========================================================================
# Coupon & Promotional Offer Management (CRUD)
# ===========================================================================


def _coupon_to_out(coupon: ShopCoupon) -> ShopCouponOut:
    return ShopCouponOut(
        id=str(coupon.id),
        code=coupon.code,
        title=coupon.title or coupon.code,
        description=coupon.description,
        discount_type=coupon.discount_type,
        discount_value=coupon.discount_value,
        min_order_amount=coupon.min_order_amount,
        max_discount_amount=coupon.max_discount_amount,
        usage_limit=coupon.usage_limit,
        usage_count=coupon.usage_count,
        per_user_limit=coupon.per_user_limit,
        first_order_only=coupon.first_order_only,
        is_highlighted=coupon.is_highlighted,
        start_date=coupon.start_date,
        expiry_date=coupon.expiry_date,
        is_active=coupon.is_active,
        is_valid_now=coupon.is_valid_now,
        created_at=coupon.created_at,
        updated_at=coupon.updated_at,
    )


async def create_coupon(payload: ShopCouponCreate) -> ShopCouponOut:
    """Creates a new promotional discount coupon code."""
    code = payload.code.strip().upper()
    if not code:
        raise BadRequestError("Coupon code cannot be empty.")

    existing = await ShopCoupon.find_one(ShopCoupon.code == code)
    if existing:
        raise BadRequestError(
            f"A coupon with code '{code}' already exists.",
            error_code="coupon_already_exists",
        )

    if payload.start_date and payload.expiry_date and payload.start_date > payload.expiry_date:
        raise BadRequestError("Start date cannot be after expiry date.")

    if payload.discount_type == CouponDiscountType.PERCENTAGE and payload.discount_value > 100:
        raise BadRequestError("Percentage discount cannot exceed 100%.")

    coupon = ShopCoupon(
        code=code,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        min_order_amount=payload.min_order_amount,
        max_discount_amount=payload.max_discount_amount,
        usage_limit=payload.usage_limit,
        usage_count=0,
        per_user_limit=payload.per_user_limit,
        first_order_only=payload.first_order_only,
        is_highlighted=payload.is_highlighted,
        start_date=payload.start_date,
        expiry_date=payload.expiry_date,
        is_active=payload.is_active,
    )
    await coupon.save()
    logger.info("Admin created new coupon code: {} (Type: {}, Value: {})", code, payload.discount_type, payload.discount_value)
    return _coupon_to_out(coupon)


async def list_coupons(
    search: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    limit: int = 20,
) -> ShopCouponListResponse:
    """Lists store coupons with search and active filtering."""
    skip = (page - 1) * limit
    filters: list[Any] = []

    if is_active is not None:
        filters.append(ShopCoupon.is_active == is_active)

    if search and search.strip():
        pat = safe_regex_pattern(search)
        filters.append({
            "$or": [
                {"code": pat},
                {"title": pat},
                {"description": pat},
            ]
        })

    query = ShopCoupon.find(*filters) if filters else ShopCoupon.find_all()
    total = await query.count()
    coupons = await query.sort("-created_at").skip(skip).limit(limit).to_list()
    pages = (total + limit - 1) // limit if total > 0 else 1

    return ShopCouponListResponse(
        items=[_coupon_to_out(c) for c in coupons],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


async def get_coupon(coupon_id: str) -> ShopCouponOut:
    """Retrieves single coupon by ObjectId or Code."""
    coupon = None
    try:
        coupon = await ShopCoupon.get(PydanticObjectId(coupon_id))
    except Exception:
        pass

    if not coupon:
        coupon = await ShopCoupon.find_one(ShopCoupon.code == coupon_id.strip().upper())

    if not coupon:
        raise NotFoundError("Coupon not found.")

    return _coupon_to_out(coupon)


async def update_coupon(coupon_id: str, payload: ShopCouponUpdate) -> ShopCouponOut:
    """Updates an existing discount coupon."""
    try:
        coupon = await ShopCoupon.get(PydanticObjectId(coupon_id))
    except Exception:
        coupon = None

    if not coupon:
        raise NotFoundError("Coupon not found.")

    if payload.title is not None:
        coupon.title = payload.title.strip()
    if payload.description is not None:
        coupon.description = payload.description.strip() if payload.description else None
    if payload.discount_type is not None:
        coupon.discount_type = payload.discount_type
    if payload.discount_value is not None:
        if (payload.discount_type or coupon.discount_type) == CouponDiscountType.PERCENTAGE and payload.discount_value > 100:
            raise BadRequestError("Percentage discount cannot exceed 100%.")
        coupon.discount_value = payload.discount_value
    if payload.min_order_amount is not None:
        coupon.min_order_amount = payload.min_order_amount
    if payload.max_discount_amount is not None:
        coupon.max_discount_amount = payload.max_discount_amount
    if payload.usage_limit is not None:
        coupon.usage_limit = payload.usage_limit
    if payload.per_user_limit is not None:
        coupon.per_user_limit = payload.per_user_limit
    if payload.first_order_only is not None:
        coupon.first_order_only = payload.first_order_only
    if payload.is_highlighted is not None:
        coupon.is_highlighted = payload.is_highlighted
    if payload.start_date is not None:
        coupon.start_date = payload.start_date
    if payload.expiry_date is not None:
        coupon.expiry_date = payload.expiry_date
    if payload.is_active is not None:
        coupon.is_active = payload.is_active

    if coupon.start_date and coupon.expiry_date and coupon.start_date > coupon.expiry_date:
        raise BadRequestError("Start date cannot be after expiry date.")

    coupon.updated_at = datetime.now(UTC)
    await coupon.save()
    logger.info("Admin updated coupon: {} ({})", coupon.code, coupon.id)
    return _coupon_to_out(coupon)


async def delete_coupon(coupon_id: str) -> bool:
    """Deletes a promotional coupon."""
    try:
        coupon = await ShopCoupon.get(PydanticObjectId(coupon_id))
    except Exception:
        coupon = None

    if not coupon:
        raise NotFoundError("Coupon not found.")

    await coupon.delete()
    logger.info("Admin deleted coupon: {} ({})", coupon.code, coupon_id)
    return True


async def toggle_coupon_active(coupon_id: str) -> ShopCouponOut:
    """Toggles coupon active/inactive state in 1 click."""
    try:
        coupon = await ShopCoupon.get(PydanticObjectId(coupon_id))
    except Exception:
        coupon = None

    if not coupon:
        raise NotFoundError("Coupon not found.")

    coupon.is_active = not coupon.is_active
    coupon.updated_at = datetime.now(UTC)
    await coupon.save()
    logger.info("Admin toggled coupon {} active state to: {}", coupon.code, coupon.is_active)
    return _coupon_to_out(coupon)


