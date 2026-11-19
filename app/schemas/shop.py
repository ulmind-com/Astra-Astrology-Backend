"""Pydantic schemas for Astra AstroStore / Remedy E-Commerce APIs."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.models.enums import (
    CouponDiscountType,
    ProductCategoryType,
    ShopOrderStatus,
    ShopPaymentMethod,
    ShopPaymentStatus,
    ShopRefundStatus,
)


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
    purpose_tags: list[str] = Field(default_factory=list)
    recommended_for_rashis: list[str] = Field(default_factory=list)
    crystal_type: str | None = None
    beej_mantra: str | None = None
    wear_instructions: str | None = None

    # High-Value Free Gift Bundling
    free_gift_title: str | None = None
    free_gift_value: float | None = None
    free_gift_badge: str | None = None
    free_gift_image_url: str | None = None

    # 100% Wallet Cashback Override
    cashback_percent: int | None = Field(default=None, ge=0, le=200)

    # Government / Lab Certification
    lab_certified: bool = True
    lab_certificate_name: str | None = "Govt. Approved Gemological Lab"
    lab_certificate_number: str | None = None

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
    purpose_tags: list[str] | None = None
    recommended_for_rashis: list[str] | None = None
    crystal_type: str | None = None
    beej_mantra: str | None = None
    wear_instructions: str | None = None

    free_gift_title: str | None = None
    free_gift_value: float | None = None
    free_gift_badge: str | None = None
    free_gift_image_url: str | None = None

    cashback_percent: int | None = Field(default=None, ge=0, le=200)

    lab_certified: bool | None = None
    lab_certificate_name: str | None = None
    lab_certificate_number: str | None = None

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
    purpose_tags: list[str] = Field(default_factory=list)
    recommended_for_rashis: list[str] = Field(default_factory=list)
    crystal_type: str | None = None
    beej_mantra: str | None = None
    wear_instructions: str | None = None

    free_gift_title: str | None = None
    free_gift_value: float | None = None
    free_gift_badge: str | None = None
    free_gift_image_url: str | None = None

    cashback_percent: int | None = None

    lab_certified: bool = True
    lab_certificate_name: str | None = "Govt. Approved Gemological Lab"
    lab_certificate_number: str | None = None

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


class ShopStoreReelItem(BaseModel):
    id: str
    user_handle: str
    user_name: str | None = None
    rating: int = 5
    quote: str
    thumbnail_url: str
    video_url: str | None = None
    likes_count: str = "3.8k"
    tagged_product_title: str | None = None
    tagged_product_price: int | None = None
    tagged_product_slug: str | None = None
    is_active: bool = True


class ShopBannerSettingsUpdate(BaseModel):
    announcement_bar_text: str | None = None
    announcement_bar_link: str | None = None
    announcement_bar_active: bool = True
    marquee_items: list[str] = Field(default_factory=list)
    hero_banners: list[ShopHeroBannerItem] = Field(default_factory=list)
    reels: list[ShopStoreReelItem] = Field(default_factory=list)

    # 100% Wallet Cashback Controls
    cashback_enabled: bool = True
    cashback_percent: int = Field(default=100, ge=0, le=200)
    cashback_max_cap_inr: float | None = None
    cashback_credit_timing: str = "on_delivery"

    # Customer Order Cancellation & Anti-Fraud Policy Controls
    allow_user_cancellation: bool = True
    cancellation_grace_hours: int = Field(default=24, ge=1, le=168)
    refund_sla_days: int = Field(default=3, ge=1, le=14)

    # Free Gift Defaults
    free_gift_default_title: str = "Raw Selenite Charging Plate"
    free_gift_default_value: float = 729.0
    free_gift_default_badge: str = "FREE Raw Selenite Plate worth ₹729"
    free_gift_default_image_url: str | None = None

    # Logistics
    free_shipping_threshold: float = 499.0
    standard_shipping_fee: float = 70.0
    cod_enabled: bool = True
    cod_extra_charge: float = 0.0
    checkout_reservation_minutes: int = Field(default=20, ge=5, le=120)
    cod_max_rto_allowed: int = Field(default=2, ge=1, le=10)
    cod_blacklisted_phones: list[str] = Field(default_factory=list)


class ShopBannerSettingsOut(BaseModel):
    announcement_bar_text: str | None = None
    announcement_bar_link: str | None = None
    announcement_bar_active: bool = True
    marquee_items: list[str] = Field(default_factory=list)
    hero_banners: list[ShopHeroBannerItem] = Field(default_factory=list)
    reels: list[ShopStoreReelItem] = Field(default_factory=list)

    # 100% Wallet Cashback Controls
    cashback_enabled: bool = True
    cashback_percent: int = 100
    cashback_max_cap_inr: float | None = None
    cashback_credit_timing: str = "on_delivery"

    # Customer Order Cancellation & Anti-Fraud Policy Controls
    allow_user_cancellation: bool = True
    cancellation_grace_hours: int = 24
    refund_sla_days: int = 3

    # Free Gift Defaults
    free_gift_default_title: str = "Raw Selenite Charging Plate"
    free_gift_default_value: float = 729.0
    free_gift_default_badge: str = "FREE Raw Selenite Plate worth ₹729"
    free_gift_default_image_url: str | None = None

    # Logistics & Anti-Abuse
    free_shipping_threshold: float = 499.0
    standard_shipping_fee: float = 70.0
    cod_enabled: bool = True
    cod_extra_charge: float = 0.0
    checkout_reservation_minutes: int = 20
    cod_max_rto_allowed: int = 2
    cod_blacklisted_phones: list[str] = Field(default_factory=list)


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


# ===========================================================================
# Cart, Checkout & Order Schemas
# ===========================================================================


class CartItemInput(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, le=50)


class CartItemOut(BaseModel):
    product_id: str
    title: str
    slug: str
    sku: str
    featured_image: str
    unit_mrp: float
    unit_sale_price: float
    quantity: int
    line_total: float
    in_stock: bool
    stock_quantity: int
    free_gift_title: str | None = None
    free_gift_value: float | None = None
    free_gift_badge: str | None = None
    cashback_percent: int = 100


class CartOut(BaseModel):
    items: list[CartItemOut] = Field(default_factory=list)
    subtotal: float = 0.0
    discount_amount: float = 0.0
    coupon_code: str | None = None
    shipping_fee: float = 0.0
    free_shipping_threshold: float = 499.0
    free_shipping_remaining: float = 0.0
    grand_total: float = 0.0
    total_cashback_coins: int = 0
    bundled_free_gifts: list[dict] = Field(default_factory=list)


class CheckoutAddressInput(BaseModel):
    recipient_name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(min_length=10, max_length=15)
    alternate_phone: str | None = None
    address_line1: str = Field(min_length=5, max_length=255)
    address_line2: str | None = None
    landmark: str | None = None
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pincode: str = Field(min_length=6, max_length=10)
    address_type: str = "home"


class CheckoutSankalpaInput(BaseModel):
    devotee_name: str | None = None
    gotra: str | None = None
    date_of_birth: str | None = None
    birth_time: str | None = None
    birth_place: str | None = None
    special_prayer_wish: str | None = None


class ShopCheckoutRequest(BaseModel):
    items: list[CartItemInput] = Field(min_length=1)
    shipping_address: CheckoutAddressInput
    sankalpa: CheckoutSankalpaInput | None = None
    payment_method: ShopPaymentMethod = ShopPaymentMethod.RAZORPAY
    coupon_code: str | None = None


class ShopCheckoutResponse(BaseModel):
    order_id: str
    order_number: str
    subtotal: float
    discount_amount: float
    shipping_fee: float
    grand_total: float
    payment_method: ShopPaymentMethod
    payment_status: ShopPaymentStatus
    order_status: ShopOrderStatus
    razorpay_order_id: str | None = None
    razorpay_key_id: str | None = None
    cashback_percent: int = 100
    cashback_coins_eligible: int = 0
    free_gifts: list[dict] = Field(default_factory=list)


class ShopPaymentVerifyRequest(BaseModel):
    order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class ShopOrderItemOut(BaseModel):
    product_id: str
    title: str
    slug: str
    sku: str
    category_name: str
    featured_image: str
    unit_mrp: float
    unit_sale_price: float
    quantity: int
    line_total: float
    free_gift_title: str | None = None
    free_gift_value: float | None = None
    lab_certified: bool = True
    lab_certificate_number: str | None = None


class ShopOrderStatusLogOut(BaseModel):
    status: ShopOrderStatus
    changed_at: datetime
    notes: str | None = None


class ShopOrderOut(BaseModel):
    id: str
    order_number: str
    user_id: str
    user_email: str
    user_phone: str
    shipping_address: dict
    items: list[ShopOrderItemOut]
    sankalpa: dict | None = None
    subtotal: float
    discount_amount: float
    coupon_code: str | None = None
    shipping_fee: float
    tax_amount: float
    grand_total: float
    payment_method: ShopPaymentMethod
    payment_status: ShopPaymentStatus
    order_status: ShopOrderStatus
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    cashback_percent: int = 100
    cashback_coins_eligible: int = 0
    cashback_coins_credited: int = 0
    cashback_credited_at: datetime | None = None
    free_gifts: list[dict] = Field(default_factory=list)
    courier_partner: str | None = None
    tracking_id: str | None = None
    tracking_url: str | None = None
    estimated_delivery_date: datetime | None = None
    delivered_at: datetime | None = None
    consecration_certificate_url: str | None = None
    stock_reserved_until: datetime | None = None
    is_stock_restored: bool = False
    rto_at: datetime | None = None
    rto_reason: str | None = None
    cancellation_reason: str | None = None
    refund_status: ShopRefundStatus | None = None
    refund_amount: float | None = None
    refund_upi_id: str | None = None
    refund_qr_code_url: str | None = None
    refund_requested_at: datetime | None = None
    refund_sla_days: int | None = None
    refund_completed_at: datetime | None = None
    refund_transaction_id: str | None = None
    refund_notes: str | None = None
    status_history: list[ShopOrderStatusLogOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ShopCancelOrderPayload(BaseModel):
    """Customer-initiated order cancellation payload with UPI/QR payout details."""

    reason: str | None = Field(default=None, max_length=500, description="Reason for cancellation")
    upi_id: str | None = Field(default=None, max_length=100, description="Customer UPI VPA ID (e.g. name@upi)")
    qr_code_url: str | None = Field(default=None, description="Uploaded UPI QR Code image URL on Cloudinary")
    qr_code_public_id: str | None = Field(default=None, description="Cloudinary public ID of uploaded QR Code")


class ShopAdminCompleteRefundPayload(BaseModel):
    """Admin completes refund payout and triggers customer notification."""

    transaction_id: str | None = Field(default=None, max_length=100, description="Bank/UPI UTR or Reference Number")
    notes: str | None = Field(default=None, max_length=500, description="Internal admin notes")


class ShopOrderListResponse(BaseModel):
    items: list[ShopOrderOut]
    total: int
    page: int
    limit: int
    pages: int


class ShopAdminOrderUpdate(BaseModel):
    order_status: ShopOrderStatus | None = None
    courier_partner: str | None = None
    tracking_id: str | None = None
    tracking_url: str | None = None
    estimated_delivery_date: datetime | None = None
    notes: str | None = None
    consecration_certificate_url: str | None = None
    rto_reason: str | None = None


class PincodeCheckResponse(BaseModel):
    pincode: str
    city: str
    state: str
    is_serviceable: bool = True
    cod_available: bool = True
    cod_disabled_reason: str | None = None
    estimated_delivery_days: int = 4
    estimated_delivery_date: str


# ===========================================================================
# Coupon & Promotional Discount Schemas
# ===========================================================================


class ShopCouponCreate(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    title: str = Field(min_length=2, max_length=120)
    description: str | None = None
    discount_type: CouponDiscountType = CouponDiscountType.PERCENTAGE
    discount_value: float = Field(gt=0, description="Percentage (e.g. 10 for 10%) or Flat amount in ₹")
    min_order_amount: float = Field(default=0.0, ge=0)
    max_discount_amount: float | None = None
    usage_limit: int | None = None
    per_user_limit: int = Field(default=1, ge=1)
    first_order_only: bool = False
    is_highlighted: bool = False
    start_date: datetime | None = None
    expiry_date: datetime | None = None
    is_active: bool = True


class ShopCouponUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    discount_type: CouponDiscountType | None = None
    discount_value: float | None = Field(default=None, gt=0)
    min_order_amount: float | None = Field(default=None, ge=0)
    max_discount_amount: float | None = None
    usage_limit: int | None = None
    per_user_limit: int | None = Field(default=None, ge=1)
    first_order_only: bool | None = None
    is_highlighted: bool | None = None
    start_date: datetime | None = None
    expiry_date: datetime | None = None
    is_active: bool | None = None


class ShopCouponOut(BaseModel):
    id: str
    code: str
    title: str
    description: str | None = None
    discount_type: CouponDiscountType
    discount_value: float
    min_order_amount: float
    max_discount_amount: float | None = None
    usage_limit: int | None = None
    usage_count: int = 0
    per_user_limit: int = 1
    first_order_only: bool = False
    is_highlighted: bool = False
    start_date: datetime | None = None
    expiry_date: datetime | None = None
    is_active: bool
    is_valid_now: bool
    created_at: datetime
    updated_at: datetime


class ShopCouponListResponse(BaseModel):
    items: list[ShopCouponOut]
    total: int
    page: int
    limit: int
    pages: int


class ShopCouponValidateRequest(BaseModel):
    code: str
    subtotal: float = Field(ge=0)


class ShopCouponValidateResponse(BaseModel):
    is_valid: bool
    code: str
    discount_amount: float
    new_subtotal: float
    message: str
    coupon: ShopCouponOut | None = None


class ShopCouponRecommendationOut(BaseModel):
    code: str
    title: str
    description: str | None = None
    discount_type: str
    discount_value: float
    min_order_amount: float
    max_discount_amount: float | None = None
    discount_amount: float
    is_applicable: bool
    reason_if_inapplicable: str | None = None
    is_best_offer: bool = False
    is_first_order_deal: bool = False
    expiry_date: datetime | None = None


class ShopCouponRecommendationsResponse(BaseModel):
    items: list[ShopCouponRecommendationOut]
    best_coupon_code: str | None = None
    max_savings: float = 0.0
    user_orders_count: int = 0


# ===========================================================================
# 11. Product Review & Verified Buyer Rating Schemas
# ===========================================================================


class ProductReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5, description="Devotee rating from 1 to 5 stars")
    title: str | None = Field(default=None, max_length=150, description="Short headline")
    comment: str = Field(min_length=5, max_length=3000, description="Detailed review text")
    images: list[str] = Field(default_factory=list, max_length=5, description="Image URLs of delivered remedy/prasadi")


class ProductReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, max_length=150)
    comment: str | None = Field(default=None, min_length=5, max_length=3000)
    images: list[str] | None = Field(default=None, max_length=5)


class ProductReviewOut(BaseModel):
    id: str
    product_id: str
    product_slug: str
    user_id: str
    order_id: str
    rating: int
    title: str | None = None
    comment: str
    images: list[str] = Field(default_factory=list)
    is_verified_buyer: bool = True
    author_name: str
    author_avatar: str | None = None
    helpful_count: int = 0
    is_helpful_by_me: bool = False
    is_hidden: bool = False
    created_at: datetime
    updated_at: datetime


class ProductRatingBreakdown(BaseModel):
    stars_5: int = 0
    stars_4: int = 0
    stars_3: int = 0
    stars_2: int = 0
    stars_1: int = 0
    stars_5_pct: int = 0
    stars_4_pct: int = 0
    stars_3_pct: int = 0
    stars_2_pct: int = 0
    stars_1_pct: int = 0


class ProductReviewsResponse(BaseModel):
    items: list[ProductReviewOut]
    total: int
    average_rating: float
    breakdown: ProductRatingBreakdown
    page: int
    limit: int
    pages: int


class ReviewEligibilityResponse(BaseModel):
    can_review: bool
    already_reviewed: bool
    is_delivered_buyer: bool
    reason: str | None = None
    existing_review: ProductReviewOut | None = None
    order_id: str | None = None


class AdminReviewModerationUpdate(BaseModel):
    is_hidden: bool
    hidden_reason: str | None = None


class AdminProductReviewListResponse(BaseModel):
    items: list[ProductReviewOut]
    total: int
    page: int
    limit: int
    pages: int





