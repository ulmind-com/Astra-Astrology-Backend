"""Pydantic schemas for Astra AstroStore / Remedy E-Commerce APIs."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.models.enums import ProductCategoryType, ShopOrderStatus, ShopPaymentStatus


# ===========================================================================
# Category Schemas
# ===========================================================================


class ProductCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    icon_url: str | None = None
    banner_url: str | None = None
    category_type: ProductCategoryType = ProductCategoryType.OTHER
    parent_id: str | None = None
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True
    seo_title: str | None = None
    seo_description: str | None = None


class ProductCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    icon_url: str | None = None
    banner_url: str | None = None
    category_type: ProductCategoryType | None = None
    parent_id: str | None = None
    display_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    seo_title: str | None = None
    seo_description: str | None = None


class ProductCategoryOut(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    icon_url: str | None = None
    banner_url: str | None = None
    category_type: ProductCategoryType
    parent_id: str | None = None
    display_order: int
    is_active: bool
    is_deleted: bool = False
    seo_title: str | None = None
    seo_description: str | None = None
    product_count: int = 0
    created_at: datetime
    updated_at: datetime


# ===========================================================================
# Product Schemas
# ===========================================================================


class ProductCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    slug: str | None = Field(default=None, min_length=3, max_length=255)
    sku: str | None = Field(default=None, min_length=3, max_length=100)
    short_description: str = Field(max_length=500)
    detailed_description: str
    category_id: str
    category_slug: str | None = None
    category_type: ProductCategoryType = ProductCategoryType.OTHER

    # Astrological Metadata
    ruling_planet: str | None = None
    deity: str | None = None
    benefits: list[str] = Field(default_factory=list)
    life_pillars: list[str] = Field(default_factory=list)
    recommended_for_rashis: list[str] = Field(default_factory=list)
    beej_mantra: str | None = None
    wear_instructions: str | None = None

    # Pricing & Inventory (INR ₹)
    mrp: float = Field(gt=0, description="Original Strike-through MRP in ₹")
    sale_price: float = Field(gt=0, description="Active Selling Price in ₹")
    cost_price: float | None = None
    stock_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=1)
    weight_grams: float = Field(default=100.0, gt=0)

    # Media
    images: list[str] = Field(default_factory=list)
    featured_image: str
    video_url: str | None = None
    certificate_image_url: str | None = None

    # Status Flags
    is_active: bool = True
    is_featured: bool = False
    is_energized: bool = True


class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    slug: str | None = Field(default=None, min_length=3, max_length=255)
    sku: str | None = Field(default=None, min_length=3, max_length=100)
    short_description: str | None = Field(default=None, max_length=500)
    detailed_description: str | None = None
    category_id: str | None = None
    category_slug: str | None = None
    category_type: ProductCategoryType | None = None

    ruling_planet: str | None = None
    deity: str | None = None
    benefits: list[str] | None = None
    life_pillars: list[str] | None = None
    recommended_for_rashis: list[str] | None = None
    beej_mantra: str | None = None
    wear_instructions: str | None = None

    mrp: float | None = Field(default=None, gt=0)
    sale_price: float | None = Field(default=None, gt=0)
    cost_price: float | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    low_stock_threshold: int | None = Field(default=None, ge=1)
    weight_grams: float | None = Field(default=None, gt=0)

    images: list[str] | None = None
    featured_image: str | None = None
    video_url: str | None = None
    certificate_image_url: str | None = None

    is_active: bool | None = None
    is_featured: bool | None = None
    is_energized: bool | None = None


class ProductOut(BaseModel):
    id: str
    title: str
    slug: str
    sku: str
    short_description: str
    detailed_description: str
    category_id: str
    category_slug: str
    category_type: ProductCategoryType

    ruling_planet: str | None = None
    deity: str | None = None
    benefits: list[str] = Field(default_factory=list)
    life_pillars: list[str] = Field(default_factory=list)
    recommended_for_rashis: list[str] = Field(default_factory=list)
    beej_mantra: str | None = None
    wear_instructions: str | None = None

    mrp: float
    sale_price: float
    cost_price: float | None = None
    discount_percent: int = 0
    stock_quantity: int
    low_stock_threshold: int
    weight_grams: float
    in_stock: bool = True
    is_low_stock: bool = False

    images: list[str] = Field(default_factory=list)
    featured_image: str
    video_url: str | None = None
    certificate_image_url: str | None = None

    is_active: bool
    is_featured: bool
    is_energized: bool
    is_deleted: bool = False
    average_rating: float
    review_count: int

    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    limit: int
    has_more: bool


# ===========================================================================
# Inventory & Stock Schemas
# ===========================================================================


class StockUpdatePayload(BaseModel):
    """Payload to modify stock by increment, decrement, or absolute set."""
    quantity: int = Field(description="Amount to add, subtract, or set")
    mode: str = Field(default="set", description="'set', 'add', or 'subtract'")
    reason: str | None = Field(default=None, description="Note e.g. 'Warehouse Restock #102'")


class InventorySummaryResponse(BaseModel):
    total_products: int
    out_of_stock_count: int
    low_stock_count: int
    healthy_stock_count: int
    total_stock_units: int
    total_inventory_valuation_mrp: float
    total_inventory_valuation_cost: float


# ===========================================================================
# Store Banner Settings Schemas
# ===========================================================================


class ShopHeroBannerItem(BaseModel):
    id: str
    title: str
    subtitle: str
    cta_text: str
    cta_link: str
    badge_text: str | None = None
    image_url: str
    is_active: bool = True


class ShopBannerSettingsUpdate(BaseModel):
    announcement_bar_text: str | None = None
    announcement_bar_link: str | None = None
    announcement_bar_active: bool = True
    hero_banners: list[ShopHeroBannerItem] = Field(default_factory=list)


class ShopBannerSettingsOut(BaseModel):
    announcement_bar_text: str | None = None
    announcement_bar_link: str | None = None
    announcement_bar_active: bool = True
    hero_banners: list[ShopHeroBannerItem] = Field(default_factory=list)


# ===========================================================================
# Astrological Dynamic Upsell & Cloudinary Cleanup Schemas
# ===========================================================================


class ShopProductRecommendationOut(BaseModel):
    id: str
    title: str
    slug: str
    sku: str
    short_description: str
    sale_price: float
    mrp: float
    discount_percent: int
    featured_image: str
    category_slug: str
    category_type: ProductCategoryType
    ruling_planet: str | None = None
    deity: str | None = None
    in_stock: bool = True
    sacred_reason: str | None = None  # e.g. "Prescribed for Shani Sade Sati pacification"
    store_url: str


class CloudinaryOrphanCleanupReport(BaseModel):
    scanned_count: int
    referenced_count: int
    orphaned_found_count: int
    purged_count: int
    failed_count: int
    dry_run: bool
    purged_public_ids: list[str] = Field(default_factory=list)


# ===========================================================================
# Concurrency Stock Reservation Schemas (Phase 4 & 5 Protection)
# ===========================================================================


class StockReservationRequest(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, le=50)


class StockReservationResponse(BaseModel):
    success: bool
    reserved: bool
    product_id: str
    quantity: int
    message: str



