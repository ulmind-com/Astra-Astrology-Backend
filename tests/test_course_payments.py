"""Buying a course: the order, the signature, and the webhook.

Three separate ways money used to go missing or courses used to be given
away, and each gets its own test here:

* the browser never came back from checkout, so the payment settled with
  Razorpay and nothing was ever enrolled;
* a signature was the only check, so any real payment on the account could be
  replayed against any course;
* both paths could enroll the same student twice.
"""

from datetime import datetime
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.config import settings as app_settings
from app.models.course import Course, CourseEnrollment, CourseOrder
from app.models.enums import PaymentOrderStatus
from app.models.user import User
from tests.test_calls import signed_in

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")

PRICE = 1999.0
PRICE_PAISE = 199900
TEST_KEY_SECRET = "test_course_key_secret"
TEST_WEBHOOK_SECRET = "test_course_webhook_secret"


@pytest.fixture(autouse=True)
def _razorpay_test_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_settings, "RAZORPAY_KEY_ID", "rzp_test_fake")
    monkeypatch.setattr(app_settings, "RAZORPAY_KEY_SECRET", TEST_KEY_SECRET)
    monkeypatch.setattr(app_settings, "RAZORPAY_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET)


async def _user_for(headers: dict) -> User:
    from beanie import PydanticObjectId

    from app.core.security import decode_token

    token = headers["Authorization"].removeprefix("Bearer ")
    user = await User.get(PydanticObjectId(decode_token(token)["sub"]))
    assert user is not None
    return user


async def _course(price: float = PRICE) -> Course:
    return await Course(
        title="Paid Masterclass",
        slug=f"paid-{datetime.now().timestamp()}",
        price=price,
        mrp=price * 2,
    ).insert()


def _captured(order_id: str, payment_id: str, amount: int = PRICE_PAISE) -> dict:
    """What Razorpay returns for a payment that actually went through."""
    return {
        "id": payment_id,
        "order_id": order_id,
        "status": "captured",
        "amount": amount,
        "method": "upi",
    }


async def _open_order(client: AsyncClient, headers: dict, course: Course) -> str:
    """Starts a checkout and returns our Razorpay order id."""
    fake = {"id": f"order_{course.id}"}
    with patch(
        "app.services.course_service.asyncio.to_thread",
        new=AsyncMock(return_value=fake),
    ):
        resp = await client.post(f"{P}/courses/{course.id}/order", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()["data"]
    assert body["free_enrolled"] is False
    return body["order_id"]


def _signature(order_id: str, payment_id: str) -> str:
    import hashlib
    import hmac

    from app.core.config import settings as app_settings

    return hmac.new(
        app_settings.RAZORPAY_KEY_SECRET.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()


# ------------------------------------------------------------- the order
async def test_starting_a_checkout_writes_the_order_down(
    client: AsyncClient,
) -> None:
    """Without this record a payment could never be traced to a course."""
    headers = await signed_in(client, "buyer1@test.dev")
    user = await _user_for(headers)
    course = await _course()

    order_id = await _open_order(client, headers, course)

    stored = await CourseOrder.find_one(CourseOrder.razorpay_order_id == order_id)
    assert stored is not None, "the order was not persisted"
    assert stored.user_id == user.id
    assert stored.course_id == course.id
    assert stored.amount_paise == PRICE_PAISE
    assert stored.status is PaymentOrderStatus.CREATED


# ------------------------------------------------------- the browser path
async def test_a_real_payment_enrolls_the_student(client: AsyncClient) -> None:
    headers = await signed_in(client, "buyer2@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)
    payment_id = "pay_real_1"

    with patch.object(
        __import__("app.services.course_service", fromlist=["CourseService"]).CourseService,
        "_fetch_course_payment",
        new=AsyncMock(return_value=_captured(order_id, payment_id)),
    ):
        resp = await client.post(
            f"{P}/courses/{course.id}/verify-payment",
            headers=headers,
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": _signature(order_id, payment_id),
            },
        )
    assert resp.status_code == 200, resp.text

    enrollment = await CourseEnrollment.find_one(
        CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
    )
    assert enrollment is not None
    assert enrollment.amount_paid == PRICE
    assert enrollment.payment_id == payment_id

    stored = await CourseOrder.find_one(CourseOrder.razorpay_order_id == order_id)
    assert stored is not None
    assert stored.status is PaymentOrderStatus.PAID
    assert stored.verified_via == "callback"

    refreshed = await Course.get(course.id)
    assert refreshed is not None
    assert refreshed.total_students == 1


async def test_a_payment_for_another_course_cannot_open_this_one(
    client: AsyncClient,
) -> None:
    """The ten-rupee hole: a real, correctly signed payment for something
    cheap used to unlock anything it was pointed at."""
    headers = await signed_in(client, "buyer3@test.dev")
    user = await _user_for(headers)
    cheap = await _course(price=10.0)
    expensive = await _course(price=PRICE)

    order_id = await _open_order(client, headers, cheap)
    payment_id = "pay_cheap_1"

    resp = await client.post(
        f"{P}/courses/{expensive.id}/verify-payment",
        headers=headers,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            # A genuine signature — this is what made it work before.
            "razorpay_signature": _signature(order_id, payment_id),
        },
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["error_code"] == "order_not_found"

    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == expensive.id,
        )
        is None
    ), "an unpaid course was opened"


async def test_another_students_order_cannot_be_used(client: AsyncClient) -> None:
    buyer = await signed_in(client, "buyer4@test.dev")
    thief = await signed_in(client, "thief@test.dev")
    thief_user = await _user_for(thief)
    course = await _course()

    order_id = await _open_order(client, buyer, course)
    payment_id = "pay_someone_elses"

    resp = await client.post(
        f"{P}/courses/{course.id}/verify-payment",
        headers=thief,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": _signature(order_id, payment_id),
        },
    )
    assert resp.status_code == 404, resp.text
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == thief_user.id,
            CourseEnrollment.course_id == course.id,
        )
        is None
    )


async def test_a_forged_signature_is_refused(client: AsyncClient) -> None:
    headers = await signed_in(client, "buyer5@test.dev")
    course = await _course()
    order_id = await _open_order(client, headers, course)

    resp = await client.post(
        f"{P}/courses/{course.id}/verify-payment",
        headers=headers,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_x",
            "razorpay_signature": "0" * 64,
        },
    )
    assert resp.status_code == 400, resp.text
    assert resp.json()["error_code"] == "invalid_signature"


async def test_paying_less_than_the_order_does_not_enroll(
    client: AsyncClient,
) -> None:
    """The amount comes from Razorpay, and has to match what was quoted."""
    headers = await signed_in(client, "buyer6@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)
    payment_id = "pay_short"

    with patch.object(
        __import__("app.services.course_service", fromlist=["CourseService"]).CourseService,
        "_fetch_course_payment",
        new=AsyncMock(return_value=_captured(order_id, payment_id, amount=100)),
    ):
        resp = await client.post(
            f"{P}/courses/{course.id}/verify-payment",
            headers=headers,
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": _signature(order_id, payment_id),
            },
        )
    assert resp.status_code == 400, resp.text
    assert resp.json()["error_code"] == "amount_mismatch"
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
        )
        is None
    )


async def test_an_authorised_but_uncaptured_payment_does_not_enroll(
    client: AsyncClient,
) -> None:
    """The bank is holding the money, not paying it. That hold can be voided."""
    headers = await signed_in(client, "buyer7@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)
    payment_id = "pay_held"
    held = _captured(order_id, payment_id) | {"status": "authorized"}

    with patch.object(
        __import__("app.services.course_service", fromlist=["CourseService"]).CourseService,
        "_fetch_course_payment",
        new=AsyncMock(return_value=held),
    ):
        resp = await client.post(
            f"{P}/courses/{course.id}/verify-payment",
            headers=headers,
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": _signature(order_id, payment_id),
            },
        )
    assert resp.status_code == 400, resp.text
    assert resp.json()["error_code"] == "payment_not_captured"
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
        )
        is None
    )


# ----------------------------------------------------------- the webhook
async def test_the_webhook_enrolls_when_the_browser_never_came_back(
    client: AsyncClient,
) -> None:
    """The bug that was losing people the course they had just paid for."""
    from app.services.course_service import CourseService

    headers = await signed_in(client, "buyer8@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)

    # No verify-payment call at all: the tab was closed on the bank's page.
    result = await CourseService.enroll_from_webhook(
        razorpay_order_id=order_id,
        payment=_captured(order_id, "pay_webhook_1"),
    )
    assert result == "enrolled"

    enrollment = await CourseEnrollment.find_one(
        CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
    )
    assert enrollment is not None, "the student paid and got nothing"

    stored = await CourseOrder.find_one(CourseOrder.razorpay_order_id == order_id)
    assert stored is not None
    assert stored.status is PaymentOrderStatus.PAID
    assert stored.verified_via == "webhook"


async def test_the_callback_and_the_webhook_together_enroll_once(
    client: AsyncClient,
) -> None:
    """Both paths fire for the same payment. One enrollment, one student."""
    from app.services.course_service import CourseService

    headers = await signed_in(client, "buyer9@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)
    payment_id = "pay_both"
    payment = _captured(order_id, payment_id)

    with patch.object(
        CourseService, "_fetch_course_payment", new=AsyncMock(return_value=payment)
    ):
        first = await client.post(
            f"{P}/courses/{course.id}/verify-payment",
            headers=headers,
            json={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": _signature(order_id, payment_id),
            },
        )
    assert first.status_code == 200, first.text

    second = await CourseService.enroll_from_webhook(
        razorpay_order_id=order_id, payment=payment
    )
    assert second == "already_enrolled"

    rows = await CourseEnrollment.find(
        CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
    ).to_list()
    assert len(rows) == 1, f"{len(rows)} enrollments for one purchase"

    refreshed = await Course.get(course.id)
    assert refreshed is not None
    assert refreshed.total_students == 1, "the student was counted twice"


async def test_a_replayed_webhook_changes_nothing(client: AsyncClient) -> None:
    from app.services.course_service import CourseService

    headers = await signed_in(client, "buyer10@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)
    payment = _captured(order_id, "pay_replay")

    await CourseService.enroll_from_webhook(razorpay_order_id=order_id, payment=payment)
    again = await CourseService.enroll_from_webhook(
        razorpay_order_id=order_id, payment=payment
    )
    assert again == "already_enrolled"

    rows = await CourseEnrollment.find(
        CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
    ).to_list()
    assert len(rows) == 1


async def test_a_webhook_for_a_wallet_recharge_is_left_alone(
    client: AsyncClient,
) -> None:
    """Courses must not try to settle someone else's order."""
    from app.services.course_service import CourseService

    result = await CourseService.enroll_from_webhook(
        razorpay_order_id="order_some_wallet_recharge",
        payment=_captured("order_some_wallet_recharge", "pay_w"),
    )
    assert result == "not_a_course_order"


async def test_a_failed_payment_is_recorded(client: AsyncClient) -> None:
    from app.services.course_service import CourseService

    headers = await signed_in(client, "buyer11@test.dev")
    course = await _course()
    order_id = await _open_order(client, headers, course)

    result = await CourseService.fail_course_order(
        razorpay_order_id=order_id,
        payment={"id": "pay_failed", "error_description": "Insufficient funds"},
    )
    assert result == "marked_failed"

    stored = await CourseOrder.find_one(CourseOrder.razorpay_order_id == order_id)
    assert stored is not None
    assert stored.status is PaymentOrderStatus.FAILED
    assert stored.failure_reason == "Insufficient funds"


def _webhook_payload(event: str, payload: dict, created_at: int = 1731312000) -> tuple[bytes, str]:
    body = json.dumps({"event": event, "payload": payload, "created_at": created_at}).encode()
    signature = hmac.new(TEST_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return body, signature


async def test_webhook_endpoint_payment_captured_enrolls_student(
    client: AsyncClient,
) -> None:
    """Real HTTP POST /api/v1/webhooks/razorpay settles a course order cleanly."""
    headers = await signed_in(client, "buyer_http_1@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)

    body, sig = _webhook_payload(
        "payment.captured",
        {"payment": {"entity": _captured(order_id, "pay_http_cap_1")}},
    )
    resp = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_course_cap_1",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == "enrolled"
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
        )
        is not None
    )


async def test_webhook_endpoint_order_paid_enrolls_student(
    client: AsyncClient,
) -> None:
    """Razorpay dashboards subscribed only to `order.paid` also settle course orders."""
    headers = await signed_in(client, "buyer_http_2@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)

    body, sig = _webhook_payload(
        "order.paid",
        {
            "payment": {"entity": _captured(order_id, "pay_order_paid_1")},
            "order": {
                "entity": {
                    "id": order_id,
                    "status": "paid",
                    "amount": PRICE_PAISE,
                    "amount_paid": PRICE_PAISE,
                    "currency": "INR",
                }
            },
        },
    )
    resp = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": "evt_course_order_paid_1",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"] == "enrolled"
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
        )
        is not None
    )


async def test_webhook_without_event_id_in_same_second_does_not_collide(
    client: AsyncClient,
) -> None:
    """Two separate payments arriving in the same Unix second without X-Razorpay-Event-Id must both enroll."""
    h1 = await signed_in(client, "buyer_same_sec_1@test.dev")
    h2 = await signed_in(client, "buyer_same_sec_2@test.dev")
    u1, u2 = await _user_for(h1), await _user_for(h2)
    c1, c2 = await _course(), await _course()
    o1 = await _open_order(client, h1, c1)
    o2 = await _open_order(client, h2, c2)

    b1, s1 = _webhook_payload(
        "payment.captured",
        {"payment": {"entity": _captured(o1, "pay_sec_1")}},
        created_at=1731319999,
    )
    b2, s2 = _webhook_payload(
        "payment.captured",
        {"payment": {"entity": _captured(o2, "pay_sec_2")}},
        created_at=1731319999,
    )

    r1 = await client.post(
        f"{P}/webhooks/razorpay",
        content=b1,
        headers={"X-Razorpay-Signature": s1, "Content-Type": "application/json"},
    )
    r2 = await client.post(
        f"{P}/webhooks/razorpay",
        content=b2,
        headers={"X-Razorpay-Signature": s2, "Content-Type": "application/json"},
    )
    assert r1.status_code == 200 and r1.json()["result"] == "enrolled"
    assert r2.status_code == 200 and r2.json()["result"] == "enrolled"
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == u1.id, CourseEnrollment.course_id == c1.id
        )
        is not None
    )
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == u2.id, CourseEnrollment.course_id == c2.id
        )
        is not None
    )


async def test_webhook_retry_succeeds_after_transient_dispatch_failure(
    client: AsyncClient,
) -> None:
    """A transient failure must not poison WebhookEvent with a phantom duplicate."""
    from app.services.course_service import CourseService

    headers = await signed_in(client, "buyer_retry@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)

    body, sig = _webhook_payload(
        "payment.captured",
        {"payment": {"entity": _captured(order_id, "pay_retry_1")}},
    )
    req_headers = {
        "X-Razorpay-Signature": sig,
        "X-Razorpay-Event-Id": "evt_course_retry_1",
        "Content-Type": "application/json",
    }

    with patch.object(
        CourseService, "enroll_from_webhook", new=AsyncMock(side_effect=RuntimeError("db blip"))
    ):
        with pytest.raises(RuntimeError, match="db blip"):
            await client.post(f"{P}/webhooks/razorpay", content=body, headers=req_headers)

    retry = await client.post(f"{P}/webhooks/razorpay", content=body, headers=req_headers)
    assert retry.status_code == 200, retry.text
    assert retry.json()["result"] == "enrolled"
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
        )
        is not None
    )


async def test_webhook_refund_processed_revokes_course_enrollment(
    client: AsyncClient,
) -> None:
    headers = await signed_in(client, "buyer_refund@test.dev")
    user = await _user_for(headers)
    course = await _course()
    order_id = await _open_order(client, headers, course)

    b1, s1 = _webhook_payload(
        "payment.captured",
        {"payment": {"entity": _captured(order_id, "pay_refund_1")}},
    )
    cap_resp = await client.post(
        f"{P}/webhooks/razorpay",
        content=b1,
        headers={
            "X-Razorpay-Signature": s1,
            "X-Razorpay-Event-Id": "evt_course_ref_cap",
            "Content-Type": "application/json",
        },
    )
    assert cap_resp.status_code == 200 and cap_resp.json()["result"] == "enrolled"

    b2, s2 = _webhook_payload(
        "refund.processed",
        {
            "refund": {
                "entity": {
                    "id": "rfnd_course_1",
                    "payment_id": "pay_refund_1",
                    "amount": PRICE_PAISE,
                }
            }
        },
    )
    ref_resp = await client.post(
        f"{P}/webhooks/razorpay",
        content=b2,
        headers={
            "X-Razorpay-Signature": s2,
            "X-Razorpay-Event-Id": "evt_course_ref_1",
            "Content-Type": "application/json",
        },
    )
    assert ref_resp.status_code == 200 and ref_resp.json()["result"] == "refunded"
    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
        )
        is None
    )
    stored = await CourseOrder.find_one(CourseOrder.razorpay_order_id == order_id)
    assert stored is not None and stored.status is PaymentOrderStatus.REFUNDED


# --------------------------------------------------------- free courses
async def test_a_free_course_still_enrolls_in_one_tap(client: AsyncClient) -> None:
    headers = await signed_in(client, "buyer12@test.dev")
    user = await _user_for(headers)
    course = await _course(price=0.0)

    resp = await client.post(f"{P}/courses/{course.id}/order", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["free_enrolled"] is True

    assert (
        await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
        )
        is not None
    )


async def test_tapping_enroll_twice_does_not_enroll_twice(
    client: AsyncClient,
) -> None:
    headers = await signed_in(client, "buyer13@test.dev")
    user = await _user_for(headers)
    course = await _course(price=0.0)

    await client.post(f"{P}/courses/{course.id}/order", headers=headers)
    await client.post(f"{P}/courses/{course.id}/order", headers=headers)

    rows = await CourseEnrollment.find(
        CourseEnrollment.user_id == user.id, CourseEnrollment.course_id == course.id
    ).to_list()
    assert len(rows) == 1
