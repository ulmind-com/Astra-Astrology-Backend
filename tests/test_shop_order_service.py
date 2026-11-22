import pytest
from app.services.shop_order_service import ShopOrderService
from app.models.enums import ShopPaymentMethod, ShopOrderStatus, ShopPaymentStatus


@pytest.mark.asyncio
async def test_pincode_validator_known_cities():
    # Delhi
    delhi = await ShopOrderService.check_pincode("110001")
    assert delhi.city == "New Delhi"
    assert delhi.state == "Delhi"
    assert delhi.is_serviceable is True
    assert delhi.cod_available is True
    assert delhi.estimated_delivery_days == 3

    # Kolkata
    kolkata = await ShopOrderService.check_pincode("700001")
    assert kolkata.city == "Kolkata"
    assert kolkata.state == "West Bengal"
    assert kolkata.estimated_delivery_days == 3

    # Mumbai
    mumbai = await ShopOrderService.check_pincode("400001")
    assert mumbai.city == "Mumbai"
    assert mumbai.state == "Maharashtra"

    # Varanasi
    varanasi = await ShopOrderService.check_pincode("221001")
    assert "Varanasi" in varanasi.city or "Uttar Pradesh" in varanasi.state


@pytest.mark.asyncio
async def test_pincode_validator_invalid():
    with pytest.raises(Exception):
        await ShopOrderService.check_pincode("abc123")
    with pytest.raises(Exception):
        await ShopOrderService.check_pincode("1100")


def test_shop_order_invoice_email_template_generation():
    from app.services.email_templates import shop_order_invoice_email_html

    html = shop_order_invoice_email_html(
        user_name="Rahul Sharma",
        user_email="rahul@example.com",
        order_number="ASTRA-ORD-2026-TEST99",
        invoice_number="DIVIN-INV-2026-TEST99",
        payment_id="pay_test_123456",
        amount_inr=2499.0,
        payment_method="Online / Razorpay",
        purchase_date="22 November 2026",
        items=[
            {
                "title": "Natural 5 Mukhi Rudraksha Mala",
                "sku": "RUD-5M-108",
                "category_name": "Sacred Rudraksha",
                "quantity": 1,
                "unit_sale_price": 2499.0,
                "line_total": 2499.0,
                "free_gift_title": "Raw Selenite Crystal Plate",
            }
        ],
        free_gifts=[{"title": "Raw Selenite Crystal Plate", "value": 729}],
        subtotal=2499.0,
        discount_amount=0.0,
        shipping_fee=0.0,
        tax_amount=0.0,
        is_tax_invoice=False,
        shipping_address={
            "recipient_name": "Rahul Sharma",
            "phone_number": "9876543210",
            "address_line1": "Flat 402, Shanti Kunj",
            "city": "Varanasi",
            "state": "Uttar Pradesh",
            "pincode": "221001",
        },
        sankalpa={
            "devotee_name": "Rahul Sharma",
            "gotra": "Kashyap",
        },
        cashback_coins=2499,
        order_url="https://astra.ulmind.com/account/orders",
        invoice_url="https://api.astra.ulmind.com/api/v1/shop/orders/ASTRA-ORD-2026-TEST99/invoice/html",
    )

    assert "DIVIN-INV-2026-TEST99" in html
    assert "ASTRA-ORD-2026-TEST99" in html
    assert "Natural 5 Mukhi Rudraksha Mala" in html
    assert "pay_test_123456" in html
    assert "Rahul Sharma" in html
    assert "221001" in html
    assert "Kashyap" in html
    assert "2,499" in html

