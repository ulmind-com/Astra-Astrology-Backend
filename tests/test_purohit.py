"""Tests for Purohit Live Presence, Catalog Management, Busy Locks, and Timed Puja Booking."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from beanie import PydanticObjectId

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError
from app.models.enums import PujaBookingStatus, PujaPaymentStatus, UserRole
from app.models.purohit import PujaBooking, Purohit, PurohitPujaItem
from app.models.user import User
from app.schemas.purohit import PujaBookingCreate
from app.services import purohit_presence, purohit_service


def test_generate_initial_password():
    pwd = purohit_service.generate_initial_password(12)
    assert len(pwd) == 12
    assert any(c.isdigit() for c in pwd) or any(c.isalpha() for c in pwd)


def test_purohit_starting_price():
    p = Purohit.model_construct(
        display_name="Acharya Sharma",
        slug="acharya-sharma",
        phone="9876543210",
        email="sharma@example.com",
        pujas=[
            PurohitPujaItem(puja_name="Lakshmi Puja", description="", price_inr=150.0, is_active=True),
            PurohitPujaItem(puja_name="Satyanarayan", description="", price_inr=500.0, is_active=True),
            PurohitPujaItem(puja_name="Inactive Puja", description="", price_inr=50.0, is_active=False),
        ],
    )
    price = purohit_service._get_starting_price(p)
    assert price == 150.0


def test_purohit_default_starting_price_when_empty():
    p = Purohit.model_construct(
        display_name="Acharya Sharma",
        slug="acharya-sharma",
        phone="9876543210",
        email="sharma@example.com",
        pujas=[],
    )
    price = purohit_service._get_starting_price(p)
    assert price == 0.0


def test_purohit_presence_ttl_and_busy_rules():
    now = datetime.now(UTC)
    fresh = Purohit.model_construct(
        id=PydanticObjectId(),
        user_id=PydanticObjectId(),
        display_name="Pandit Ji",
        slug="pandit-ji",
        phone="9876543210",
        email="pandit@example.com",
        is_online=True,
        is_verified=True,
        is_busy=False,
        last_seen_at=now - timedelta(seconds=10),
    )
    assert purohit_presence.is_effectively_online(fresh) is True
    assert purohit_presence.is_available_for_live_puja(fresh) is True

    # Stale heartbeat (>50s) -> treated offline immediately at read time
    fresh.last_seen_at = now - timedelta(seconds=90)
    assert purohit_presence.is_effectively_online(fresh) is False
    assert purohit_presence.is_available_for_live_puja(fresh) is False

    # Busy lock excludes from live puja search
    fresh.last_seen_at = now
    fresh.is_busy = True
    assert purohit_presence.is_effectively_online(fresh) is True
    assert purohit_presence.is_available_for_live_puja(fresh) is False


@pytest.mark.asyncio
async def test_book_puja_rejects_offline_or_busy_purohit():
    now = datetime.now(UTC)
    devotee = User.model_construct(
        id=PydanticObjectId(),
        email="devotee@example.com",
        first_name="Ayan",
        last_name="Roy",
        role=UserRole.USER,
    )
    puja = PurohitPujaItem(id="p1", puja_name="Lakshmi Puja", description="Prosperity", duration_minutes=30, price_inr=500.0)
    offline_purohit = Purohit.model_construct(
        id=PydanticObjectId(),
        user_id=PydanticObjectId(),
        display_name="Pandit A",
        slug="pandit-a",
        phone="9999999999",
        email="a@example.com",
        is_verified=True,
        is_online=False,
        is_busy=False,
        pujas=[puja],
    )
    payload = PujaBookingCreate(
        purohit_id=str(offline_purohit.id),
        puja_item_id="p1",
        sankalpa_name="Ayan Roy",
        sankalpa_gotra="Bharadwaj",
        payment_method="wallet",
    )

    with patch("app.services.purohit_service.Purohit.get", new=AsyncMock(return_value=offline_purohit)):
        with pytest.raises(BadRequestError) as exc:
            await purohit_service.book_puja(devotee, payload)
        assert exc.value.error_code == "purohit_offline"

    offline_purohit.is_online = True
    offline_purohit.last_seen_at = now
    offline_purohit.is_busy = True
    with patch("app.services.purohit_service.Purohit.get", new=AsyncMock(return_value=offline_purohit)):
        with pytest.raises(ConflictError) as exc2:
            await purohit_service.book_puja(devotee, payload)
        assert exc2.value.error_code == "purohit_busy"


@pytest.mark.asyncio
async def test_accept_puja_sets_exact_expires_at_and_expired_token_is_blocked():
    now = datetime.now(UTC)
    purohit_uid = PydanticObjectId()
    purohit_id = PydanticObjectId()
    devotee_uid = PydanticObjectId()
    booking_id = PydanticObjectId()

    purohit_user = User.model_construct(id=purohit_uid, role=UserRole.PUROHIT, email="p@example.com")
    devotee_user = User.model_construct(id=devotee_uid, role=UserRole.USER, email="u@example.com")

    confirmed_booking = PujaBooking.model_construct(
        id=booking_id,
        booking_number="PUJA-TEST-001",
        user_id=devotee_uid,
        user_name="Devotee",
        user_phone="9999999999",
        user_email="u@example.com",
        purohit_id=purohit_id,
        purohit_user_id=purohit_uid,
        purohit_name="Pandit",
        puja_item_id="p1",
        puja_name="Lakshmi Puja",
        puja_duration_minutes=30,
        amount_inr=500.0,
        sankalpa_name="Devotee",
        sankalpa_gotra="Kashyapa",
        room_id="puja_room_test",
        status=PujaBookingStatus.CONFIRMED,
        payment_status=PujaPaymentStatus.PAID,
        started_at=now,
        created_at=now,
    )

    accepted_booking = PujaBooking.model_construct(
        **{
            **confirmed_booking.model_dump(),
            "id": booking_id,
            "status": PujaBookingStatus.IN_PROGRESS,
            "accepted_at": now,
            "expires_at": now + timedelta(minutes=30),
        }
    )

    fake_col = MagicMock()
    fake_col.find_one_and_update = AsyncMock(return_value={"_id": booking_id})
    fake_purohit_col = MagicMock()
    fake_purohit_col.update_one = AsyncMock(return_value=None)

    with (
        patch("app.services.purohit_service.PujaBooking.get", new=AsyncMock(side_effect=[confirmed_booking, accepted_booking])),
        patch("app.services.purohit_service.PujaBooking.get_pymongo_collection", return_value=fake_col),
        patch("app.services.purohit_service.Purohit.get_pymongo_collection", return_value=fake_purohit_col),
        patch("app.services.purohit_service.Purohit.get", new=AsyncMock(return_value=None)),
        patch("app.services.purohit_service.realtime.publish_puja_event", new=AsyncMock()),
        patch("app.services.purohit_service.zego.generate_token", return_value="zego-tok-123"),
    ):
        res, tok = await purohit_service.accept_puja_booking(str(booking_id), purohit_user)
        assert res.status == PujaBookingStatus.IN_PROGRESS
        assert tok == "zego-tok-123"
        assert res.expires_at is not None
        diff_mins = round((res.expires_at - res.accepted_at).total_seconds() / 60)
        assert diff_mins == 30

    # Expired IN_PROGRESS session must block room entry and finalize
    expired_booking = PujaBooking.model_construct(
        **{
            **confirmed_booking.model_dump(),
            "id": booking_id,
            "status": PujaBookingStatus.IN_PROGRESS,
            "accepted_at": now - timedelta(minutes=35),
            "expires_at": now - timedelta(minutes=5),
        }
    )
    with (
        patch("app.services.purohit_service.PujaBooking.get", new=AsyncMock(return_value=expired_booking)),
        patch("app.services.purohit_service._reconcile_booking_state", new=AsyncMock(return_value=expired_booking)),
        patch("app.services.purohit_service._finalize_puja_session", new=AsyncMock(return_value=expired_booking)) as fin,
    ):
        with pytest.raises(ForbiddenError) as exc:
            await purohit_service.get_booking_token(str(booking_id), devotee_user)
        assert exc.value.error_code == "puja_expired"
        fin.assert_awaited_once()


@pytest.mark.asyncio
async def test_decline_puja_releases_lock_and_refunds():
    now = datetime.now(UTC)
    purohit_uid = PydanticObjectId()
    purohit_id = PydanticObjectId()
    booking_id = PydanticObjectId()
    purohit_user = User.model_construct(id=purohit_uid, role=UserRole.PUROHIT, email="p@example.com")

    confirmed = PujaBooking.model_construct(
        id=booking_id,
        booking_number="PUJA-DEC-1",
        user_id=PydanticObjectId(),
        user_name="User",
        user_phone="8888888888",
        user_email="u@example.com",
        purohit_id=purohit_id,
        purohit_user_id=purohit_uid,
        purohit_name="Pandit",
        puja_item_id="p1",
        puja_name="Durga Puja",
        puja_duration_minutes=60,
        amount_inr=1000.0,
        sankalpa_name="User",
        sankalpa_gotra="Kashyapa",
        room_id="puja_room_dec",
        status=PujaBookingStatus.CONFIRMED,
        payment_status=PujaPaymentStatus.PAID,
        started_at=now,
        created_at=now,
    )
    declined = PujaBooking.model_construct(
        **{
            **confirmed.model_dump(),
            "id": booking_id,
            "status": PujaBookingStatus.DECLINED,
            "payment_status": PujaPaymentStatus.REFUNDED,
            "cancel_reason": "Busy right now",
        }
    )
    fake_col = MagicMock()
    fake_col.find_one_and_update = AsyncMock(return_value={"_id": booking_id})

    with (
        patch("app.services.purohit_service.PujaBooking.get", new=AsyncMock(side_effect=[confirmed, declined])),
        patch("app.services.purohit_service.PujaBooking.get_pymongo_collection", return_value=fake_col),
        patch("app.services.purohit_service._release_purohit_busy_lock", new=AsyncMock()) as unlock,
        patch("app.services.purohit_service._refund_booking", new=AsyncMock(return_value=declined)) as refund,
        patch("app.services.purohit_service.realtime.publish_puja_event", new=AsyncMock()) as pub,
    ):
        res = await purohit_service.decline_puja_booking(str(booking_id), purohit_user, reason="Busy right now")
        assert res.status == PujaBookingStatus.DECLINED
        assert res.payment_status == PujaPaymentStatus.REFUNDED
        unlock.assert_awaited_once_with(purohit_id, booking_id)
        refund.assert_awaited_once()
        pub.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_purohit_catalog_endpoint_reads_pujas_field():
    from app.api.v1.purohits import get_purohit_catalog

    now_iso = datetime.now(UTC).isoformat()
    mock_data = {
        "pujas": [
            {
                "id": "lakshmi-1",
                "puja_name": "Lakshmi Puja",
                "description": "Home puja",
                "duration_minutes": 30,
                "price_inr": 500.0,
                "samagri_notes": None,
                "is_active": True,
                "created_at": now_iso,
            },
            {
                "id": "hidden-2",
                "puja_name": "Paused Puja",
                "description": "Hidden",
                "duration_minutes": 60,
                "price_inr": 1000.0,
                "samagri_notes": None,
                "is_active": False,
                "created_at": now_iso,
            },
        ]
    }
    with patch("app.services.purohit_service.get_purohit_by_id_or_slug", new=AsyncMock(return_value=mock_data)):
        resp = await get_purohit_catalog("pandit-ji")
        assert len(resp.data) == 1
        assert resp.data[0].puja_name == "Lakshmi Puja"


@pytest.mark.asyncio
async def test_pay_after_accept_request_and_griefing_guards():
    now = datetime.now(UTC)
    purohit_uid = PydanticObjectId()
    purohit_id = PydanticObjectId()
    devotee_uid = PydanticObjectId()

    devotee = User.model_construct(
        id=devotee_uid,
        email="devotee@example.com",
        first_name="Ayan",
        last_name="Roy",
        role=UserRole.USER,
    )
    puja = PurohitPujaItem(id="p1", puja_name="Lakshmi Puja", description="Prosperity", duration_minutes=30, price_inr=500.0)
    online_purohit = Purohit.model_construct(
        id=purohit_id,
        user_id=purohit_uid,
        display_name="Pandit A",
        slug="pandit-a",
        phone="9999999999",
        email="a@example.com",
        is_verified=True,
        is_online=True,
        is_busy=False,
        last_seen_at=now,
        pujas=[puja],
    )
    payload = PujaBookingCreate(
        purohit_id=str(purohit_id),
        puja_item_id="p1",
        sankalpa_name="Ayan Roy",
        sankalpa_gotra="Bharadwaj",
    )

    active_unpaid = PujaBooking.model_construct(
        id=PydanticObjectId(),
        user_id=devotee_uid,
        purohit_id=purohit_id,
        purohit_user_id=purohit_uid,
        status=PujaBookingStatus.AWAITING_ACCEPTANCE,
        payment_status=PujaPaymentStatus.PENDING,
        accept_expires_at=now + timedelta(seconds=30),
    )

    # Active unpaid request blocks sending a second parallel request
    stale_q = MagicMock()
    stale_q.to_list = AsyncMock(return_value=[active_unpaid])
    with (
        patch("app.services.purohit_service.Purohit.get", new=AsyncMock(return_value=online_purohit)),
        patch("app.services.purohit_service.PujaBooking.find", return_value=stale_q),
    ):
        with pytest.raises(ConflictError) as exc:
            await purohit_service.book_puja(devotee, payload)
        assert exc.value.error_code == "active_unpaid_request_exists"

    # When clear of unpaid requests & cooldown, book_puja succeeds with AWAITING_ACCEPTANCE & PENDING (0 INR charged)
    empty_q = MagicMock()
    empty_q.to_list = AsyncMock(return_value=[])
    empty_q.sort = MagicMock(return_value=empty_q)
    with (
        patch("app.services.purohit_service.Purohit.get", new=AsyncMock(return_value=online_purohit)),
        patch("app.services.purohit_service.PujaBooking.find", return_value=empty_q),
        patch("app.services.purohit_service.PujaBooking.get_pymongo_collection", return_value=MagicMock()),
        patch("app.services.purohit_service._acquire_purohit_busy_lock", new=AsyncMock(return_value={"_id": purohit_id})),
        patch("app.services.purohit_service.PujaBooking.insert", new=AsyncMock()),
        patch("app.services.purohit_service.realtime.publish_purohit", new=AsyncMock()),
        patch("app.services.purohit_service.realtime.publish_puja_event", new=AsyncMock()) as pub,
    ):
        booking, token = await purohit_service.book_puja(devotee, payload)
        assert booking.status == PujaBookingStatus.AWAITING_ACCEPTANCE
        assert booking.payment_status == PujaPaymentStatus.PENDING
        assert booking.accept_expires_at is not None
        assert token is None
        pub.assert_awaited_once()


@pytest.mark.asyncio
async def test_accept_transitions_to_awaiting_payment_and_late_payment_refunds():
    now = datetime.now(UTC)
    purohit_uid = PydanticObjectId()
    purohit_id = PydanticObjectId()
    devotee_uid = PydanticObjectId()
    booking_id = PydanticObjectId()
    purohit_user = User.model_construct(id=purohit_uid, role=UserRole.PUROHIT, email="p@example.com")

    awaiting_accept = PujaBooking.model_construct(
        id=booking_id,
        booking_number="PUJA-PAA-1",
        user_id=devotee_uid,
        user_name="User",
        user_phone="8888888888",
        user_email="u@example.com",
        purohit_id=purohit_id,
        purohit_user_id=purohit_uid,
        purohit_name="Pandit",
        puja_item_id="p1",
        puja_name="Lakshmi Puja",
        puja_duration_minutes=30,
        amount_inr=500.0,
        sankalpa_name="User",
        sankalpa_gotra="Kashyapa",
        room_id="puja_room_paa",
        status=PujaBookingStatus.AWAITING_ACCEPTANCE,
        payment_status=PujaPaymentStatus.PENDING,
        accept_expires_at=now + timedelta(seconds=35),
        created_at=now,
    )
    awaiting_pay = PujaBooking.model_construct(
        **{
            **awaiting_accept.model_dump(),
            "id": booking_id,
            "status": PujaBookingStatus.AWAITING_PAYMENT,
            "accepted_at": now,
            "payment_expires_at": now + timedelta(seconds=90),
        }
    )

    fake_col = MagicMock()
    fake_col.find_one_and_update = AsyncMock(return_value={"_id": booking_id})
    fake_purohit_col = MagicMock()
    fake_purohit_col.update_one = AsyncMock()

    with (
        patch("app.services.purohit_service.PujaBooking.get", new=AsyncMock(side_effect=[awaiting_accept, awaiting_pay])),
        patch("app.services.purohit_service.PujaBooking.get_pymongo_collection", return_value=fake_col),
        patch("app.services.purohit_service.Purohit.get_pymongo_collection", return_value=fake_purohit_col),
        patch("app.services.purohit_service.Purohit.get", new=AsyncMock(return_value=None)),
        patch("app.services.purohit_service.realtime.publish_puja_event", new=AsyncMock()) as pub,
    ):
        res, tok = await purohit_service.accept_puja_booking(str(booking_id), purohit_user)
        assert res.status == PujaBookingStatus.AWAITING_PAYMENT
        assert tok == ""
        assert pub.await_args.args[2] == "puja_accepted_for_payment"

    # Expired 90s payment arriving via webhook/callback must auto-refund 100%
    expired_pay = PujaBooking.model_construct(
        **{
            **awaiting_pay.model_dump(),
            "id": booking_id,
            "payment_expires_at": now - timedelta(seconds=45),
        }
    )
    refunded_doc = PujaBooking.model_construct(
        **{
            **expired_pay.model_dump(),
            "id": booking_id,
            "status": PujaBookingStatus.CANCELLED,
            "payment_status": PujaPaymentStatus.REFUNDED,
        }
    )
    fake_col2 = MagicMock()
    fake_col2.update_one = AsyncMock()
    with (
        patch("app.services.purohit_service.Purohit.get", new=AsyncMock(return_value=None)),
        patch("app.services.purohit_service.PujaBooking.get_pymongo_collection", return_value=fake_col2),
        patch("app.services.purohit_service.PujaBooking.get", new=AsyncMock(return_value=expired_pay)),
        patch("app.services.purohit_service._refund_booking", new=AsyncMock(return_value=refunded_doc)) as ref,
        patch("app.services.purohit_service.realtime.publish_puja_event", new=AsyncMock()),
    ):
        activated, out_tok = await purohit_service._activate_paid_puja_session(
            expired_pay, payment_method="razorpay", razorpay_payment_id="pay_123"
        )
        assert activated.payment_status == PujaPaymentStatus.REFUNDED
        assert out_tok == ""
        ref.assert_awaited_once()


@pytest.mark.asyncio
async def test_ghost_purohit_60s_join_sla_refunds_and_offlines():
    now = datetime.now(UTC)
    purohit_id = PydanticObjectId()
    purohit_uid = PydanticObjectId()
    booking_id = PydanticObjectId()

    ghosted = PujaBooking.model_construct(
        id=booking_id,
        booking_number="PUJA-GHOST-1",
        user_id=PydanticObjectId(),
        user_name="User",
        user_phone="9999999999",
        user_email="u@example.com",
        purohit_id=purohit_id,
        purohit_user_id=purohit_uid,
        purohit_name="Pandit",
        puja_item_id="p1",
        puja_name="Griha Pravesh",
        puja_duration_minutes=45,
        amount_inr=1000.0,
        sankalpa_name="User",
        sankalpa_gotra="Kashyapa",
        room_id="puja_room_ghost",
        status=PujaBookingStatus.IN_PROGRESS,
        payment_status=PujaPaymentStatus.PAID,
        purohit_join_deadline_at=now - timedelta(seconds=5),
        purohit_joined_at=None,
        expires_at=now + timedelta(minutes=44),
        created_at=now,
    )
    refunded = PujaBooking.model_construct(
        **{
            **ghosted.model_dump(),
            "id": booking_id,
            "status": PujaBookingStatus.DECLINED,
            "payment_status": PujaPaymentStatus.REFUNDED,
        }
    )

    b_col = MagicMock()
    b_col.find_one_and_update = AsyncMock(return_value={"_id": booking_id})
    p_col = MagicMock()
    p_col.find_one_and_update = AsyncMock(return_value={"_id": purohit_id, "consecutive_missed_pujas": 2})
    p_col.update_one = AsyncMock()

    with (
        patch("app.services.purohit_service.PujaBooking.get_pymongo_collection", return_value=b_col),
        patch("app.services.purohit_service.Purohit.get_pymongo_collection", return_value=p_col),
        patch("app.services.purohit_service._release_purohit_busy_lock", new=AsyncMock()),
        patch("app.services.purohit_service.PujaBooking.get", new=AsyncMock(return_value=ghosted)),
        patch("app.services.purohit_service.Purohit.get", new=AsyncMock(return_value=None)),
        patch("app.services.purohit_service._refund_booking", new=AsyncMock(return_value=refunded)) as ref,
        patch("app.services.purohit_service.realtime.publish_puja_event", new=AsyncMock()),
    ):
        res = await purohit_service._reconcile_booking_state(ghosted)
        assert res.payment_status == PujaPaymentStatus.REFUNDED
        assert p_col.update_one.await_count == 1
        ref.assert_awaited_once()
