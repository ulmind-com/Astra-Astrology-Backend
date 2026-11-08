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
from typing import Any
from beanie import PydanticObjectId
from beanie.operators import In, RegEx
from loguru import logger

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.cms import CMS_KEY_SHOP, ShopCMS
from app.models.shop import Product, ProductCategory, ShopOrder
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
        recommended_for_rashis=p.recommended_for_rashis or [],
        beej_mantra=p.beej_mantra,
        wear_instructions=p.wear_instructions,
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


async def list_categories(include_inactive: bool = True) -> list[ProductCategoryOut]:
    """Returns all categories with accurate product counts, excluding soft-deleted ones."""
    query: dict[str, Any] = {"is_deleted": False}
    if not include_inactive:
        query["is_active"] = True
    cats = await ProductCategory.find(query).sort("+display_order", "+name").to_list()

    # Aggregate product counts per category in one query (excluding soft-deleted products)
    counts_cursor = Product.aggregate([
        {"$match": {"is_deleted": False}},
        {"$group": {"_id": "$category_id", "count": {"$sum": 1}}}
    ])
    counts_map: dict[str, int] = {}
    async for row in counts_cursor:
        if row.get("_id"):
            counts_map[str(row["_id"])] = row["count"]

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
        filters.append(RegEx(Product.ruling_planet, f"^{ruling_planet}$", "i"))

    if stock_status == "out_of_stock":
        filters.append(Product.stock_quantity == 0)
    elif stock_status == "low_stock":
        # stock_quantity > 0 and <= low_stock_threshold
        filters.append({"stock_quantity": {"$gt": 0, "$lte": 5}})
    elif stock_status == "in_stock":
        filters.append(Product.stock_quantity > 0)

    if search and search.strip():
        term = search.strip()
        regex_filter = {
            "$or": [
                {"title": {"$regex": term, "$options": "i"}},
                {"sku": {"$regex": term, "$options": "i"}},
                {"short_description": {"$regex": term, "$options": "i"}},
                {"benefits": {"$regex": term, "$options": "i"}},
            ]
        }
        filters.append(regex_filter)

    query = Product.find(*filters) if filters else Product.find_all()
    total = await query.count()
    items = await query.sort(sort_by).skip(skip).limit(limit).to_list()

    return ProductListResponse(
        items=[_product_out(p) for p in items],
        total=total,
        page=page,
        limit=limit,
        has_more=(skip + len(items)) < total,
    )


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
        recommended_for_rashis=payload.recommended_for_rashis,
        beej_mantra=payload.beej_mantra,
        wear_instructions=payload.wear_instructions,
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
    if payload.recommended_for_rashis is not None:
        product.recommended_for_rashis = payload.recommended_for_rashis
    if payload.beej_mantra is not None:
        product.beej_mantra = payload.beej_mantra
    if payload.wear_instructions is not None:
        product.wear_instructions = payload.wear_instructions
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
    """Computes real-time warehouse metrics, stock-out counts, and valuations for active inventory."""
    all_prods = await Product.find({"is_deleted": False}).to_list()
    total_products = len(all_prods)
    out_of_stock = sum(1 for p in all_prods if p.stock_quantity == 0)
    low_stock = sum(1 for p in all_prods if 0 < p.stock_quantity <= p.low_stock_threshold)
    healthy_stock = sum(1 for p in all_prods if p.stock_quantity > p.low_stock_threshold)
    total_units = sum(p.stock_quantity for p in all_prods)
    valuation_mrp = sum(p.stock_quantity * p.mrp for p in all_prods)
    valuation_cost = sum(p.stock_quantity * (p.cost_price or (p.sale_price * 0.6)) for p in all_prods)

    return InventorySummaryResponse(
        total_products=total_products,
        out_of_stock_count=out_of_stock,
        low_stock_count=low_stock,
        healthy_stock_count=healthy_stock,
        total_stock_units=total_units,
        total_inventory_valuation_mrp=round(valuation_mrp, 2),
        total_inventory_valuation_cost=round(valuation_cost, 2),
    )


# ===========================================================================
# Store Banners & Hero Offers CMS
# ===========================================================================


async def get_shop_banner_settings() -> ShopBannerSettingsOut:
    """Returns store announcement bar & hero carousel configurations."""
    cms = await ShopCMS.find_one(ShopCMS.key == CMS_KEY_SHOP)
    if not cms:
        cms = ShopCMS(key=CMS_KEY_SHOP)
        await cms.insert()

    return ShopBannerSettingsOut(
        announcement_bar_text=cms.announcement_bar_text,
        announcement_bar_link=cms.announcement_bar_link,
        announcement_bar_active=cms.announcement_bar_active,
        hero_banners=cms.hero_banners or [],
    )


async def update_shop_banner_settings(payload: ShopBannerSettingsUpdate) -> ShopBannerSettingsOut:
    """Saves updated store promotional banners and announcement headline."""
    cms = await ShopCMS.find_one(ShopCMS.key == CMS_KEY_SHOP)
    if not cms:
        cms = ShopCMS(key=CMS_KEY_SHOP)

    cms.announcement_bar_text = payload.announcement_bar_text
    cms.announcement_bar_link = payload.announcement_bar_link
    cms.announcement_bar_active = payload.announcement_bar_active
    cms.hero_banners = [b.model_dump() for b in payload.hero_banners]

    await cms.save()
    logger.info("Updated Shop CMS banner settings")
    return ShopBannerSettingsOut(
        announcement_bar_text=cms.announcement_bar_text,
        announcement_bar_link=cms.announcement_bar_link,
        announcement_bar_active=cms.announcement_bar_active,
        hero_banners=cms.hero_banners,
    )


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

