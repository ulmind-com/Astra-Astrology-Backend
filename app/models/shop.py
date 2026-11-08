"""Astra AstroStore / Remedy E-Commerce Beanie Document Models.

Covers:
- ProductCategory: Categories and subcategories with icons, banners, and hierarchy.
- Product: Comprehensive Vedic remedy product catalog with pricing, stock, media, and astrological metadata.
- Cart & CartItem: Persistent shopping cart for authenticated users.
- UserAddress: Saved shipping addresses with pincode, phone, and landmark.
- ShopOrder: Full order cycle with snapshots, INR financials, Razorpay metadata, Vedic Sankalpa, and tracking.
- ShopCoupon: Promotional discount vouchers for marketing campaigns.
"""

from datetime import UTC, datetime
from typing import Any

import pymongo
from beanie import Indexed, PydanticObjectId
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument, utcnow
from app.models.enums import (
    AddressType,
    CouponDiscountType,
    ProductCategoryType,
    ShopOrderStatus,
    ShopPaymentStatus,
)


# ===========================================================================
# 1. Product Category & Hierarchy Model
# ===========================================================================


class ProductCategory(TimestampedDocument):
    """Categorisation for remedy store items (e.g. Rudraksha, Gemstones, Yantras)."""

    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100)
    description: str | None = None
    icon_url: str | None = None
    banner_url: str | None = None
    category_type: ProductCategoryType = ProductCategoryType.OTHER
    parent_id: PydanticObjectId | None = None  # None indicates top-level category
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True
    seo_title: str | None = None
    seo_description: str | None = None

    class Settings:
        name = "product_categories"
        indexes = [
            pymongo.IndexModel([("slug", pymongo.ASCENDING)], name="category_slug_unique", unique=True),
            pymongo.IndexModel([("category_type", pymongo.ASCENDING)], name="category_type_idx"),
            pymongo.IndexModel([("parent_id", pymongo.ASCENDING)], name="category_parent_idx"),
            pymongo.IndexModel([("is_active", pymongo.ASCENDING), ("display_order", pymongo.ASCENDING)], name="category_active_order"),
        ]


# ===========================================================================
# 2. Product Model (Catalog, Stock, Astrology Metadata & Media)
# ===========================================================================


class Product(TimestampedDocument):
    """Core product entity for physical remedy items with Vedic provenance."""

    # General Information
    title: str = Field(min_length=3, max_length=255)
    slug: str = Field(min_length=3, max_length=255)
    sku: str = Field(min_length=3, max_length=100)
    short_description: str = Field(max_length=500)
    detailed_description: str = Field(description="Full rich-text or markdown product details")

    # Category Link
    category_id: PydanticObjectId
    category_slug: str
    category_type: ProductCategoryType = ProductCategoryType.OTHER

    # Astrological Metadata
    ruling_planet: str | None = Field(default=None, description="e.g. Saturn, Sun, Jupiter, Rahu")
    deity: str | None = Field(default=None, description="e.g. Lord Shiva, Goddess Lakshmi, Lord Ganesha")
    benefits: list[str] = Field(default_factory=list, description="Target benefits e.g. Career, Wealth, Health, Marriage")
    life_pillars: list[str] = Field(default_factory=list, description="Pillars e.g. career, finance, health, love, family, luck")
    recommended_for_rashis: list[str] = Field(default_factory=list, description="Beneficial zodiac signs e.g. Leo, Capricorn")
    beej_mantra: str | None = Field(default=None, description="Consecrated chanting mantra for wearing")
    wear_instructions: str | None = Field(default=None, description="Auspicious day, direction, and wearing protocol")

    # Pricing & Inventory (Strictly in INR ₹)
    mrp: float = Field(gt=0, description="Maximum Retail Price (Original / Strike-through Price in ₹)")
    sale_price: float = Field(gt=0, description="Selling Price (Active Offer Price in ₹)")
    cost_price: float | None = Field(default=None, description="Internal procurement cost for margin tracking")
    stock_quantity: int = Field(default=0, ge=0, description="Available inventory units in warehouse")
    low_stock_threshold: int = Field(default=5, ge=1, description="Trigger alert when stock falls below this level")
    weight_grams: float = Field(default=100.0, gt=0, description="Physical item weight for logistics computation")

    # Media Assets
    images: list[str] = Field(default_factory=list, description="High-resolution image URLs")
    featured_image: str = Field(description="Primary card thumbnail image URL")
    video_url: str | None = Field(default=None, description="Product demonstration or lab test video URL")
    certificate_image_url: str | None = Field(default=None, description="Government or Gemological lab authenticity certificate")

    # Status & Visibility Flags
    is_active: bool = Field(default=True, description="Whether visible in public user store")
    is_featured: bool = Field(default=False, description="Whether highlighted on AstroStore front carousel")
    is_energized: bool = Field(default=True, description="Whether product comes consecrated with Vedic rituals")
    average_rating: float = Field(default=5.0, ge=1.0, le=5.0)
    review_count: int = Field(default=0, ge=0)

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def is_low_stock(self) -> bool:
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def discount_percent(self) -> int:
        if self.mrp > self.sale_price:
            return round(((self.mrp - self.sale_price) / self.mrp) * 100)
        return 0

    class Settings:
        name = "products"
        indexes = [
            pymongo.IndexModel([("slug", pymongo.ASCENDING)], name="product_slug_unique", unique=True),
            pymongo.IndexModel([("sku", pymongo.ASCENDING)], name="product_sku_unique", unique=True),
            pymongo.IndexModel([("category_id", pymongo.ASCENDING)], name="product_category_idx"),
            pymongo.IndexModel([("category_slug", pymongo.ASCENDING)], name="product_category_slug_idx"),
            pymongo.IndexModel([("category_type", pymongo.ASCENDING)], name="product_category_type_idx"),
            pymongo.IndexModel([("is_active", pymongo.ASCENDING), ("is_featured", pymongo.ASCENDING)], name="product_active_featured"),
            pymongo.IndexModel([("sale_price", pymongo.ASCENDING)], name="product_price_idx"),
            pymongo.IndexModel([("ruling_planet", pymongo.ASCENDING)], name="product_planet_idx"),
            pymongo.IndexModel([("benefits", pymongo.ASCENDING)], name="product_benefits_idx"),
            pymongo.IndexModel([("life_pillars", pymongo.ASCENDING)], name="product_pillars_idx"),
            pymongo.IndexModel([("stock_quantity", pymongo.ASCENDING)], name="product_stock_idx"),
            pymongo.IndexModel(
                [
                    ("title", pymongo.TEXT),
                    ("short_description", pymongo.TEXT),
                    ("detailed_description", pymongo.TEXT),
                    ("benefits", pymongo.TEXT),
                ],
                name="product_text_search",
            ),
        ]


# ===========================================================================
# 3. User Shipping Address Model
# ===========================================================================


class UserAddress(TimestampedDocument):
    """Saved delivery destinations for customer physical orders."""

    user_id: PydanticObjectId = Field(index=True)
    recipient_name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(min_length=10, max_length=15)
    alternate_phone: str | None = None
    address_line1: str = Field(min_length=5, max_length=255, description="Flat/House No, Building, Street")
    address_line2: str | None = Field(default=None, max_length=255, description="Area, Colony, Sector")
    landmark: str | None = Field(default=None, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pincode: str = Field(min_length=6, max_length=10)
    country: str = Field(default="India")
    address_type: AddressType = AddressType.HOME
    is_default: bool = False

    class Settings:
        name = "user_addresses"
        indexes = [
            pymongo.IndexModel([("user_id", pymongo.ASCENDING), ("is_default", pymongo.DESCENDING)], name="addr_user_default"),
            pymongo.IndexModel([("pincode", pymongo.ASCENDING)], name="addr_pincode_idx"),
        ]


# ===========================================================================
# 4. Shopping Cart & Item Embedded Models
# ===========================================================================


class CartItem(BaseModel):
    """An individual product line item inside the user's persistent cart."""

    product_id: PydanticObjectId
    quantity: int = Field(default=1, ge=1, le=50)
    added_at: datetime = Field(default_factory=utcnow)


class Cart(TimestampedDocument):
    """Persistent server-side shopping cart bound to an authenticated user."""

    user_id: PydanticObjectId = Field(index=True)
    items: list[CartItem] = Field(default_factory=list)
    coupon_code: str | None = None
    last_activity_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "carts"
        indexes = [
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)], name="cart_user_unique", unique=True),
            pymongo.IndexModel([("last_activity_at", pymongo.DESCENDING)], name="cart_activity_idx"),
        ]


# ===========================================================================
# 5. Promotional Coupon Model
# ===========================================================================


class ShopCoupon(TimestampedDocument):
    """Voucher discount coupons for Astra AstroStore marketing campaigns."""

    code: str = Field(min_length=3, max_length=30)
    description: str | None = None
    discount_type: CouponDiscountType = CouponDiscountType.PERCENTAGE
    discount_value: float = Field(gt=0, description="Percentage (e.g. 10 for 10%) or Flat amount in ₹")
    min_order_amount: float = Field(default=0.0, ge=0, description="Minimum subtotal required to apply")
    max_discount_amount: float | None = Field(default=None, description="Cap on percentage discounts in ₹")
    usage_limit: int | None = Field(default=None, description="Max total redemptions across all users")
    usage_count: int = Field(default=0, ge=0)
    start_date: datetime | None = None
    expiry_date: datetime | None = None
    is_active: bool = True

    @property
    def is_valid_now(self) -> bool:
        if not self.is_active:
            return False
        now = utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.expiry_date and now > self.expiry_date:
            return False
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return False
        return True

    class Settings:
        name = "shop_coupons"
        indexes = [
            pymongo.IndexModel([("code", pymongo.ASCENDING)], name="coupon_code_unique", unique=True),
            pymongo.IndexModel([("is_active", pymongo.ASCENDING), ("expiry_date", pymongo.ASCENDING)], name="coupon_active_expiry"),
        ]


# ===========================================================================
# 6. Order Snapshots & Lifecycle Models
# ===========================================================================


class ShippingAddressSnapshot(BaseModel):
    """Immutable copy of recipient and address data at the moment of checkout."""

    recipient_name: str
    phone_number: str
    alternate_phone: str | None = None
    address_line1: str
    address_line2: str | None = None
    landmark: str | None = None
    city: str
    state: str
    pincode: str
    country: str = "India"
    address_type: str = "home"


class OrderItemSnapshot(BaseModel):
    """Frozen snapshot of product details, pricing, and quantities when order was placed."""

    product_id: PydanticObjectId
    title: str
    slug: str
    sku: str
    category_name: str
    featured_image: str
    unit_mrp: float
    unit_sale_price: float
    quantity: int
    line_total: float
    weight_grams: float = 100.0


class SankalpaDetails(BaseModel):
    """Devotee sacred information for Vedic Pran-Pratishtha & energization ritual."""

    devotee_name: str | None = None
    gotra: str | None = None
    date_of_birth: str | None = None
    birth_time: str | None = None
    birth_place: str | None = None
    special_prayer_wish: str | None = None  # e.g. "Overcoming Saturn Sade Sati / Business Growth"


class OrderStatusLog(BaseModel):
    """Audit log entry for order state transitions."""

    status: ShopOrderStatus
    changed_at: datetime = Field(default_factory=utcnow)
    notes: str | None = None
    updated_by: PydanticObjectId | None = None  # Admin who triggered change


class ShopOrder(TimestampedDocument):
    """Complete physical e-commerce order record with Razorpay direct INR payments."""

    # Unique Reference
    order_number: str = Field(min_length=10, max_length=50, description="e.g. ASTRA-ORD-2026-A1B2C3D4")
    user_id: PydanticObjectId = Field(index=True)
    user_email: str
    user_phone: str

    # Snapshots
    shipping_address: ShippingAddressSnapshot
    items: list[OrderItemSnapshot] = Field(min_length=1)
    sankalpa: SankalpaDetails | None = None

    # Financial Breakdown (INR ₹)
    subtotal: float = Field(ge=0, description="Sum of line item totals in ₹")
    discount_amount: float = Field(default=0.0, ge=0, description="Discount deducted via coupon in ₹")
    coupon_code: str | None = None
    shipping_fee: float = Field(default=0.0, ge=0, description="Delivery shipping cost in ₹")
    tax_amount: float = Field(default=0.0, ge=0, description="Applicable taxes/GST in ₹")
    grand_total: float = Field(gt=0, description="Total INR amount charged to customer")

    # Payment Gateway Metadata (Razorpay Direct INR)
    payment_gateway: str = "razorpay"
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None
    payment_status: ShopPaymentStatus = ShopPaymentStatus.PENDING
    paid_at: datetime | None = None

    # Fulfillment & Delivery State
    order_status: ShopOrderStatus = ShopOrderStatus.PLACED
    status_history: list[OrderStatusLog] = Field(default_factory=list)

    # Logistics & Courier Tracking
    courier_partner: str | None = Field(default=None, description="e.g. BlueDart, Delhivery, IndiaPost, Shiprocket")
    tracking_id: str | None = Field(default=None, description="Courier AWB or Consignment Number")
    tracking_url: str | None = Field(default=None, description="Direct URL to courier tracking page")
    estimated_delivery_date: datetime | None = None
    delivered_at: datetime | None = None
    cancellation_reason: str | None = None

    # Consecration & Invoice
    invoice_number: str | None = None
    consecration_certificate_id: str | None = None

    class Settings:
        name = "shop_orders"
        indexes = [
            pymongo.IndexModel([("order_number", pymongo.ASCENDING)], name="order_number_unique", unique=True),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)], name="order_user_recent"),
            pymongo.IndexModel([("razorpay_order_id", pymongo.ASCENDING)], name="order_rzp_order_idx"),
            pymongo.IndexModel([("razorpay_payment_id", pymongo.ASCENDING)], name="order_rzp_payment_idx"),
            pymongo.IndexModel([("order_status", pymongo.ASCENDING)], name="order_status_idx"),
            pymongo.IndexModel([("payment_status", pymongo.ASCENDING)], name="order_payment_status_idx"),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)], name="order_created_recent"),
        ]
