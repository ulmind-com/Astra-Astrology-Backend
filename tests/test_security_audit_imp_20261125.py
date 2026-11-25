"""Comprehensive offline regression suite for AUD-001 through AUD-019 remediations."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from beanie import PydanticObjectId
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.ai_astrologer import _assert_session_access
from app.api.v1.astrology import download_kundli_pdf
from app.api.v1.purohits import _booking_to_out
from app.api.v1.ws import _verify_whiteboard_peer
from app.core.config import Settings
from app.core.exceptions import ForbiddenError, ServiceUnavailableError, UnauthorizedError
from app.core.rate_limit import ROUTE_RULES, rate_limiter
from app.core.security import create_application_upload_token, safe_regex_pattern, verify_application_upload_token
from app.main import app
from app.models.enums import PujaBookingStatus, PujaPaymentStatus, ShopPaymentStatus, TransactionReason, UserRole
from app.schemas.astrology import DailyHoroscopeRequest, KundliCalculateRequest, KundliMatchingPersonInput, KundliMatchingRequest
from app.schemas.purohit import PujaPaymentVerifyRequest
from app.schemas.shop import CartItemOut, CartOut, ShopPaymentVerifyRequest
from app.services import payout as payout_service
from app.services.purohit_service import verify_puja_payment
from app.services.shop_order_service import ShopOrderService


def test_aud005_no_hardcoded_secret_defaults():
    """Verify AUD-005: Fresh Settings contains no hardcoded provider credentials."""
    clean = Settings(_env_file=None)
    assert clean.RAZORPAY_KEY_ID == ""
    assert clean.BUNNY_STREAM_API_KEY == ""
    assert clean.BUNNY_STREAM_READONLY_API_KEY == ""
    assert clean.BUNNY_STREAM_TOKEN_KEY == ""
    assert clean.BUNNY_ACCOUNT_API_KEY == ""


@pytest.mark.asyncio
async def test_aud001_rate_limit_paths_and_no_bypass_header():
    """Verify AUD-001: Auth/onboarding rules match actual routes and reject spoofed bypass header."""
    assert "/api/v1/auth/password/forgot" in ROUTE_RULES
    assert "/api/v1/auth/password/reset" in ROUTE_RULES
    assert "/api/v1/astrologers/applications/send-otp" in ROUTE_RULES
    assert "/api/v1/purohits/applications/upload-document" in ROUTE_RULES

    test_ip = "198.51.100.77"
    rate_limiter.reset_for_ip(test_ip)

    now = datetime.now(UTC)
    fake_otp = SimpleNamespace(
        identifier="nonexistent@example.com",
        expires_at=now,
        resend_available_at=now,
    )
    transport = ASGITransport(app=app)
    with patch(
        "app.api.v1.auth.auth_service.request_password_reset",
        AsyncMock(return_value=(fake_otp, "123456")),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            statuses = []
            for _ in range(7):
                resp = await client.post(
                    "/api/v1/auth/password/forgot",
                    json={"email": "nonexistent@example.com"},
                    headers={"x-forwarded-for": test_ip, "x-bypass-rate-limit": "true"},
                )
                statuses.append(resp.status_code)
    assert 429 in statuses, f"Spoofed bypass header must not disable rate limiting, got {statuses}"


def test_aud002_ai_session_ownership_enforced():
    """Verify AUD-002: Owned AI sessions reject anonymous and third-party callers."""
    owner_id = PydanticObjectId()
    other_id = PydanticObjectId()
    owned_session = SimpleNamespace(user_id=owner_id)
    guest_session = SimpleNamespace(user_id=None)

    # Guest session allowed for anonymous callers
    _assert_session_access(guest_session, None)

    # Owner and admin allowed on owned session
    _assert_session_access(owned_session, SimpleNamespace(id=owner_id, role=UserRole.USER))
    _assert_session_access(owned_session, SimpleNamespace(id=other_id, role=UserRole.ADMIN))

    # Anonymous and different user rejected
    with pytest.raises(ForbiddenError):
        _assert_session_access(owned_session, None)
    with pytest.raises(ForbiddenError):
        _assert_session_access(owned_session, SimpleNamespace(id=other_id, role=UserRole.USER))


@pytest.mark.asyncio
async def test_aud003_puja_payment_verification_and_token_gate(monkeypatch):
    """Verify AUD-003: Unpaid puja bookings omit live token and Razorpay HMAC gates confirmation."""
    import hashlib
    import hmac

    booking = MagicMock()
    booking.id = PydanticObjectId()
    booking.booking_number = "PUJ-TEST-1"
    booking.user_id = PydanticObjectId()
    booking.user_name = "Devotee"
    booking.user_phone = "9876543210"
    booking.purohit_id = PydanticObjectId()
    booking.purohit_name = "Acharya"
    booking.puja_item_id = "item-1"
    booking.puja_name = "Rudrabhishek"
    booking.puja_duration_minutes = 45
    booking.amount_inr = 501.0
    booking.sankalpa_name = "Seeker"
    booking.sankalpa_gotra = "Kashyapa"
    booking.sankalpa_nakshatra = None
    booking.sankalpa_wish = None
    booking.room_id = "puja_room_1"
    booking.razorpay_order_id = "order_rzp_123"
    booking.status = PujaBookingStatus.PENDING
    booking.payment_status = PujaPaymentStatus.PENDING
    booking.started_at = None
    booking.completed_at = None
    booking.created_at = "2026-11-25T10:00:00Z"
    booking.save = AsyncMock()

    out_pending = _booking_to_out(booking, token=None)
    assert out_pending.zego_token is None
    assert out_pending.razorpay_order_id == "order_rzp_123"

    # Verify HMAC signature enforcement
    monkeypatch.setattr("app.services.purohit_service.settings.RAZORPAY_KEY_ID", "rzp_test_pub")
    monkeypatch.setattr("app.services.purohit_service.settings.RAZORPAY_KEY_SECRET", "rzp_test_secret")

    caller = SimpleNamespace(id=booking.user_id, role=UserRole.USER)
    with patch("app.services.purohit_service.PujaBooking.get", AsyncMock(return_value=booking)):
        # Invalid signature rejected
        with pytest.raises(Exception) as exc_info:
            await verify_puja_payment(
                booking_id=str(booking.id),
                user=caller,
                payload=PujaPaymentVerifyRequest(
                    razorpay_order_id="order_rzp_123",
                    razorpay_payment_id="pay_123",
                    razorpay_signature="bad_sig",
                ),
            )
        assert "signature" in str(exc_info.value).lower()

        # Valid signature promotes booking to PAID/CONFIRMED and returns Zego token
        good_sig = hmac.new(
            b"rzp_test_secret",
            b"order_rzp_123|pay_123",
            hashlib.sha256,
        ).hexdigest()
        paid_booking = MagicMock()
        paid_booking.id = booking.id
        paid_booking.booking_number = booking.booking_number
        paid_booking.room_id = booking.room_id
        paid_booking.payment_status = PujaPaymentStatus.PAID
        paid_booking.status = PujaBookingStatus.CONFIRMED

        fake_booking_col = MagicMock()
        fake_booking_col.find_one_and_update = AsyncMock(return_value={"_id": booking.id})
        fake_purohit_col = MagicMock()
        fake_purohit_col.update_one = AsyncMock()
        with (
            patch(
                "app.services.purohit_service.PujaBooking.get",
                AsyncMock(side_effect=[booking, paid_booking]),
            ),
            patch(
                "app.services.purohit_service.PujaBooking.get_pymongo_collection",
                return_value=fake_booking_col,
            ),
            patch(
                "app.services.purohit_service.Purohit.get_pymongo_collection",
                return_value=fake_purohit_col,
            ),
            patch(
                "app.services.purohit_service.zego.generate_token",
                return_value="zego_tok_verified",
            ),
        ):
            verified, token = await verify_puja_payment(
                booking_id=str(booking.id),
                user=caller,
                payload=PujaPaymentVerifyRequest(
                    razorpay_order_id="order_rzp_123",
                    razorpay_payment_id="pay_123",
                    razorpay_signature=good_sig,
                ),
            )
            assert verified.payment_status == PujaPaymentStatus.PAID
            assert verified.status == PujaBookingStatus.CONFIRMED
            assert token == "zego_tok_verified"


@pytest.mark.asyncio
async def test_aud004_stock_mutation_requires_admin():
    """Verify AUD-004: Shop stock reserve/release endpoints reject unauthenticated callers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/api/v1/shop/reserve-stock", json={"items": []})
        r2 = await client.post("/api/v1/shop/release-stock", json={"items": []})
    assert r1.status_code in (401, 403)
    assert r2.status_code in (401, 403)


@pytest.mark.asyncio
async def test_aud006_payout_analytics_awaits_aggregate():
    """Verify AUD-006: Payout analytics awaits Motor AsyncCollection.aggregate() coroutines."""

    class _EmptyAsyncCursor:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    fake_col = MagicMock()
    fake_col.aggregate = AsyncMock(return_value=_EmptyAsyncCursor())

    with (
        patch("app.models.payout.AstrologerPayout.get_pymongo_collection", return_value=fake_col),
        patch("app.models.earning.EarningEntry.get_pymongo_collection", return_value=fake_col),
        patch("app.models.purohit.PujaBooking.get_pymongo_collection", return_value=fake_col),
    ):
        result = await payout_service.get_payout_analytics_for_admin()
        assert result["total_settled_volume_paise"] == 0
        assert fake_col.aggregate.await_count >= 1


@pytest.mark.asyncio
async def test_aud007_whiteboard_peer_relationship_verified():
    """Verify AUD-007: Whiteboard relay checks active call, chat, or appointment relationships."""
    u1 = PydanticObjectId()
    u2 = PydanticObjectId()

    with (
        patch("app.models.call.CallSession.find_one", AsyncMock(return_value=None)),
        patch("app.models.chat.ChatSession.find_one", AsyncMock(return_value=None)),
        patch("app.models.appointment.Appointment.find_one", AsyncMock(return_value=None)),
    ):
        assert await _verify_whiteboard_peer(u1, str(u2), call_id=None) is False

    with patch("app.models.call.CallSession.find_one", AsyncMock(return_value=MagicMock())):
        assert await _verify_whiteboard_peer(u1, str(u2), call_id=None) is True


def test_aud009_and_aud010_schemas_aligned():
    """Verify AUD-009 & AUD-010: Canonical CartOut/CartItemOut and Astrology request schemas instantiate cleanly."""
    item = CartItemOut(
        id="p1",
        slug="rudraksha",
        sku="SKU1",
        title="Rudraksha",
        price=501.0,
        mrp=999.0,
        image="https://example.com/a.jpg",
        quantity=1,
        stock_quantity=10,
        is_in_stock=True,
        line_total=501.0,
    )
    cart = CartOut(items=[item], subtotal=501.0, grand_total=501.0)
    assert cart.items[0].price == 501.0

    k_req = KundliCalculateRequest(
        name="Test",
        gender="male",
        day=15,
        month=5,
        year=1992,
        hour=10,
        minute=30,
        latitude=22.5726,
        longitude=88.3639,
        timezone=5.5,
        place="Kolkata",
    )
    d_req = DailyHoroscopeRequest(birth_rashi_index=0, birth_nakshatra_index=1, language="bn")
    m_req = KundliMatchingRequest(
        groom=KundliMatchingPersonInput(name="A", day=1, month=1, year=1990, hour=10, minute=0),
        bride=KundliMatchingPersonInput(name="B", day=2, month=2, year=1992, hour=11, minute=0),
    )
    assert k_req.latitude == 22.5726
    assert d_req.language == "bn"
    assert m_req.groom.name == "A"


@pytest.mark.asyncio
async def test_aud012_kundli_pdf_failure_refunds_coins():
    """Verify AUD-012: Failed Kundli PDF generation refunds debited coins automatically."""
    user = SimpleNamespace(id=PydanticObjectId())
    payload = KundliCalculateRequest(
        name="Seeker",
        gender="male",
        day=15,
        month=5,
        year=1992,
        hour=10,
        minute=30,
        latitude=22.5726,
        longitude=88.3639,
        timezone=5.5,
        place="Kolkata",
    )
    with (
        patch("app.api.v1.astrology._charge_feature", AsyncMock(return_value=(49, 100))),
        patch(
            "app.api.v1.astrology.generate_comprehensive_kundli_pdf",
            side_effect=RuntimeError("boom"),
        ),
        patch("app.services.wallet.credit", AsyncMock()) as mock_credit,
    ):
        with pytest.raises(Exception):
            await download_kundli_pdf(payload=payload, user=user)
        mock_credit.assert_awaited_once()
        assert mock_credit.call_args.kwargs["amount_coins"] == 49
        assert mock_credit.call_args.kwargs["reason"] == TransactionReason.REFUND


@pytest.mark.asyncio
async def test_aud013_shop_verify_rejects_unconfigured_razorpay(monkeypatch):
    """Verify AUD-013: Unconfigured Razorpay refuses order payment verification instead of passing."""
    monkeypatch.setattr("app.services.shop_order_service.settings.RAZORPAY_KEY_ID", "")
    monkeypatch.setattr("app.services.shop_order_service.settings.RAZORPAY_KEY_SECRET", "")

    order = SimpleNamespace(
        id=PydanticObjectId(),
        user_id=PydanticObjectId(),
        order_number="ORD-1",
        payment_status=ShopPaymentStatus.PENDING,
        razorpay_order_id="order_123",
    )
    with patch("app.services.shop_order_service.ShopOrder.get", AsyncMock(return_value=order)):
        with pytest.raises(ServiceUnavailableError):
            await ShopOrderService.verify_razorpay_payment(
                user_id=order.user_id,
                payload=ShopPaymentVerifyRequest(
                    order_id=str(order.id),
                    razorpay_order_id="",
                    razorpay_payment_id="pay_123",
                    razorpay_signature="x" * 64,
                ),
            )


@pytest.mark.asyncio
async def test_aud017_onboarding_upload_requires_verified_token():
    """Verify AUD-017: Onboarding upload endpoints require a valid signed X-Upload-Token."""
    tok = create_application_upload_token("applicant@example.com")
    assert verify_application_upload_token(tok) == "applicant@example.com"
    with pytest.raises(UnauthorizedError):
        verify_application_upload_token("invalid.jwt.token")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r_astro = await client.post(
            "/api/v1/astrologers/applications/upload-document",
            files={"file": ("doc.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )
        r_purohit = await client.post(
            "/api/v1/purohits/applications/upload-document",
            files={"file": ("doc.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )
    assert r_astro.status_code == 401
    assert r_purohit.status_code == 401


def test_aud018_safe_regex_pattern_escapes_metacharacters():
    """Verify AUD-018: Untrusted search strings are escaped and bounded against ReDoS/OperationFailure."""
    pat = safe_regex_pattern("  hello(world)[test.*+?$^\\  ")
    assert pat["$options"] == "i"
    assert "\\(" in pat["$regex"]
    assert "\\[" in pat["$regex"]
    assert len(pat["$regex"]) <= 250
