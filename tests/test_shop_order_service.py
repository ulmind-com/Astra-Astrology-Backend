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
