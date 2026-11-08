"""Unit tests for Astra AstroStore Phase 1 Models & Schemas."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest
from beanie import PydanticObjectId, init_beanie

from app.models.enums import (
    AddressType,
    CouponDiscountType,
    ProductCategoryType,
    ShopOrderStatus,
    ShopPaymentStatus,
)
from app.models.shop import (
    Cart,
    CartItem,
    OrderItemSnapshot,
    OrderStatusLog,
    Product,
    ProductCategory,
    SankalpaDetails,
    ShippingAddressSnapshot,
    ShopCoupon,
    ShopOrder,
    UserAddress,
)


@pytest.fixture(autouse=True)
async def init_mock_beanie():
    """Initializes Beanie DocumentSettings in memory for standalone unit testing."""
    mock_db = MagicMock()
    mock_db.command = AsyncMock(return_value={"version": "6.0.0", "versionArray": [6, 0, 0]})
    mock_db.list_collection_names = AsyncMock(return_value=[])

    mock_coll = MagicMock()
    mock_coll.create_index = AsyncMock()
    mock_coll.create_indexes = AsyncMock()
    mock_coll.index_information = AsyncMock(return_value={})
    mock_db.__getitem__.return_value = mock_coll

    await init_beanie(
        database=mock_db,
        document_models=[
            Product,
            ProductCategory,
            UserAddress,
            Cart,
            ShopOrder,
            ShopCoupon,
        ],
    )


def test_product_category_model():
    """Verify ProductCategory schema attributes and hierarchy."""
    parent = ProductCategory(
        name="Sacred Rudraksha",
        slug="rudraksha",
        description="Authentic certified Himalayan and Nepali Rudraksha beads",
        category_type=ProductCategoryType.RUDRAKSHA,
        display_order=1,
    )
    assert parent.name == "Sacred Rudraksha"
    assert parent.slug == "rudraksha"
    assert parent.category_type == ProductCategoryType.RUDRAKSHA
    assert parent.parent_id is None
    assert parent.is_active is True

    parent_id = PydanticObjectId()
    sub = ProductCategory(
        name="7 Mukhi Rudraksha",
        slug="7-mukhi-rudraksha",
        description="Ruled by Goddess Mahalakshmi and Saturn",
        category_type=ProductCategoryType.RUDRAKSHA,
        parent_id=parent_id,
        display_order=2,
    )
    assert sub.parent_id == parent_id


def test_product_model_attributes_and_pricing():
    """Verify Product schema, Vedic attributes, and discount computations."""
    cat_id = PydanticObjectId()
    product = Product(
        title="7 Mukhi Sacred Nepali Rudraksha (Mahalakshmi Siddha)",
        slug="7-mukhi-sacred-nepali-rudraksha",
        sku="ASTRA-RUD-7M-001",
        short_description="Consecrated 7 Mukhi Rudraksha for immense financial abundance and Saturn mitigation.",
        detailed_description="Harvested from high-altitude trees in Nepal. Consecrated with sacred Vedic Pran-Pratishtha.",
        category_id=cat_id,
        category_slug="rudraksha",
        category_type=ProductCategoryType.RUDRAKSHA,
        ruling_planet="Saturn",
        deity="Goddess Mahalakshmi",
        benefits=["Wealth & Prosperity", "Debt Removal", "Saturn Sade Sati Relief"],
        life_pillars=["finance", "career", "luck"],
        recommended_for_rashis=["Capricorn", "Aquarius", "Taurus"],
        beej_mantra="ॐ হ্রীং নমঃ",
        wear_instructions="Wear on Friday or Monday morning in silver or red thread facing East.",
        mrp=3499.0,
        sale_price=1999.0,
        cost_price=750.0,
        stock_quantity=25,
        low_stock_threshold=5,
        weight_grams=15.0,
        images=["https://assets.astra.com/rudraksha-1.jpg", "https://assets.astra.com/rudraksha-2.jpg"],
        featured_image="https://assets.astra.com/rudraksha-featured.jpg",
        is_active=True,
        is_featured=True,
        is_energized=True,
    )

    assert product.in_stock is True
    assert product.is_low_stock is False
    assert product.discount_percent == 43  # ((3499 - 1999) / 3499) * 100 = 42.86 -> 43%
    assert product.mrp == 3499.0
    assert product.sale_price == 1999.0
    assert product.cost_price == 750.0
    assert len(product.benefits) == 3
    assert product.ruling_planet == "Saturn"
    assert product.is_energized is True

    # Low stock test
    product.stock_quantity = 3
    assert product.is_low_stock is True
    assert product.in_stock is True

    # Out of stock test
    product.stock_quantity = 0
    assert product.in_stock is False


def test_user_address_model():
    """Verify customer shipping address validation."""
    user_id = PydanticObjectId()
    address = UserAddress(
        user_id=user_id,
        recipient_name="Samiran Samanta",
        phone_number="9876543210",
        address_line1="42 Cosmic Tower, Flat 5B",
        address_line2="Salt Lake Sector 5",
        landmark="Near Webel Bhavan",
        city="Kolkata",
        state="West Bengal",
        pincode="700091",
        country="India",
        address_type=AddressType.HOME,
        is_default=True,
    )
    assert address.user_id == user_id
    assert address.recipient_name == "Samiran Samanta"
    assert address.pincode == "700091"
    assert address.is_default is True


def test_cart_and_cart_items():
    """Verify shopping cart and persistent user binding."""
    user_id = PydanticObjectId()
    prod_id_1 = PydanticObjectId()
    prod_id_2 = PydanticObjectId()

    cart = Cart(
        user_id=user_id,
        items=[
            CartItem(product_id=prod_id_1, quantity=2),
            CartItem(product_id=prod_id_2, quantity=1),
        ],
        coupon_code="SHIVA10",
    )
    assert cart.user_id == user_id
    assert len(cart.items) == 2
    assert cart.items[0].quantity == 2
    assert cart.coupon_code == "SHIVA10"


def test_shop_coupon_model_and_validity():
    """Verify coupon discounts and validity windows."""
    now = datetime.now(UTC)
    active_coupon = ShopCoupon(
        code="ASTRA10",
        discount_type=CouponDiscountType.PERCENTAGE,
        discount_value=10.0,
        min_order_amount=999.0,
        max_discount_amount=300.0,
        usage_limit=100,
        usage_count=5,
        start_date=now - timedelta(days=1),
        expiry_date=now + timedelta(days=10),
        is_active=True,
    )
    assert active_coupon.is_valid_now is True

    expired_coupon = ShopCoupon(
        code="EXPIRED",
        discount_type=CouponDiscountType.FLAT,
        discount_value=200.0,
        expiry_date=now - timedelta(days=1),
        is_active=True,
    )
    assert expired_coupon.is_valid_now is False


def test_shop_order_full_cycle_model():
    """Verify ShopOrder model, embedded snapshots, Sankalpa, and financials."""
    user_id = PydanticObjectId()
    prod_id = PydanticObjectId()

    shipping_snapshot = ShippingAddressSnapshot(
        recipient_name="Samiran Samanta",
        phone_number="9876543210",
        address_line1="42 Cosmic Tower",
        city="Kolkata",
        state="West Bengal",
        pincode="700091",
        country="India",
        address_type="home",
    )

    item_snapshot = OrderItemSnapshot(
        product_id=prod_id,
        title="7 Mukhi Sacred Nepali Rudraksha",
        slug="7-mukhi-sacred-nepali-rudraksha",
        sku="ASTRA-RUD-7M-001",
        category_name="Rudraksha",
        featured_image="https://assets.astra.com/rudraksha-featured.jpg",
        unit_mrp=3499.0,
        unit_sale_price=1999.0,
        quantity=2,
        line_total=3998.0,
        weight_grams=15.0,
    )

    sankalpa = SankalpaDetails(
        devotee_name="Samiran Samanta",
        gotra="Kashyapa",
        date_of_birth="2004-03-15",
        special_prayer_wish="Overcoming obstacle and achieving supreme prosperity in software ventures",
    )

    order = ShopOrder(
        order_number="ASTRA-ORD-2026-A1B2C3D4",
        user_id=user_id,
        user_email="samiran@example.com",
        user_phone="9876543210",
        shipping_address=shipping_snapshot,
        items=[item_snapshot],
        sankalpa=sankalpa,
        subtotal=3998.0,
        discount_amount=399.8,
        coupon_code="ASTRA10",
        shipping_fee=0.0,  # Free delivery
        tax_amount=0.0,
        grand_total=3598.2,
        payment_gateway="razorpay",
        razorpay_order_id="order_QwertYuiOp12345",
        payment_status=ShopPaymentStatus.PAID,
        paid_at=datetime.now(UTC),
        order_status=ShopOrderStatus.SANCTIFYING,
        status_history=[
            OrderStatusLog(status=ShopOrderStatus.PLACED, notes="Customer placed order via Razorpay"),
            OrderStatusLog(status=ShopOrderStatus.CONFIRMED, notes="Payment captured successfully"),
            OrderStatusLog(status=ShopOrderStatus.SANCTIFYING, notes="Item undergoing Vedic consecration in Temple sanctum"),
        ],
        courier_partner="BlueDart",
        tracking_id="BD882710394IN",
        tracking_url="https://bluedart.com/track?ref=BD882710394IN",
    )

    assert order.order_number == "ASTRA-ORD-2026-A1B2C3D4"
    assert order.grand_total == 3598.2
    assert order.payment_status == ShopPaymentStatus.PAID
    assert order.order_status == ShopOrderStatus.SANCTIFYING
    assert len(order.status_history) == 3
    assert order.sankalpa.gotra == "Kashyapa"
    assert order.courier_partner == "BlueDart"
    assert order.tracking_id == "BD882710394IN"
