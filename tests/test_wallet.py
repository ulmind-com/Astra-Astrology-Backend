"""The money layer.

The tests that matter most here are the ones about *not* crediting: a forged
signature, a replayed webhook, the same payment arriving down two paths. A
wallet that credits twice is worse than one that fails loudly.
"""

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient

from app.core.config import settings

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")

KEY_SECRET = "test_key_secret"
WEBHOOK_SECRET = "test_webhook_secret"


# ------------------------------------------------------------------ helpers
async def signed_in(client: AsyncClient, email: str = "wallet@test.dev") -> dict:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": "secret123", "first_name": "Wally"},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    assert created.status_code == 201, created.text
    return {"Authorization": f"Bearer {created.json()['data']['tokens']['access_token']}"}


async def make_admin(client: AsyncClient, email: str = "walletadmin@test.dev") -> dict:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": "adminpass", "first_name": "Admin"},
    )
    await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    from app.models.enums import UserRole
    from app.models.user import User

    user = await User.find_one(User.email == email)
    user.role = UserRole.SUPER_ADMIN
    await user.save()

    logged = await client.post(f"{P}/auth/login", json={"email": email, "password": "adminpass"})
    return {"Authorization": f"Bearer {logged.json()['data']['tokens']['access_token']}"}


async def user_id_for(email: str):
    from app.models.user import User

    user = await User.find_one(User.email == email)
    return user.id


@pytest.fixture
def fake_razorpay(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Stands in for Razorpay. `state` lets a test shape what the gateway says."""
    import app.services.payments as payments

    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_test_fake")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", KEY_SECRET)
    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", WEBHOOK_SECRET)

    state: dict = {"orders": {}, "payments": {}, "next_order_id": 1}

    class FakeOrder:
        def create(self, data):
            oid = f"order_fake{state['next_order_id']}"
            state["next_order_id"] += 1
            state["orders"][oid] = {**data, "id": oid}
            return state["orders"][oid]

        def payments(self, order_id):
            items = [p for p in state["payments"].values() if p.get("order_id") == order_id]
            return {"items": items}

    class FakePayment:
        def fetch(self, payment_id):
            if payment_id not in state["payments"]:
                raise RuntimeError("no such payment")
            return state["payments"][payment_id]

    class FakeClient:
        order = FakeOrder()
        payment = FakePayment()

    monkeypatch.setattr(payments, "_client", FakeClient())
    monkeypatch.setattr(payments, "_razorpay", lambda: FakeClient())
    return state


def sign_callback(order_id: str, payment_id: str, secret: str = KEY_SECRET) -> str:
    return hmac.new(
        secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256
    ).hexdigest()


def webhook_body(event: str, payload: dict) -> tuple[bytes, str]:
    body = json.dumps({"event": event, "payload": payload, "created_at": 1}).encode()
    signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return body, signature


async def open_order(client: AsyncClient, auth: dict, amount_paise: int = 50_000):
    return await client.post(
        f"{P}/wallet/recharge/order", headers=auth, json={"amount_paise": amount_paise}
    )


def capture(state: dict, order_id: str, amount_paise: int, payment_id: str = "pay_fake1") -> dict:
    """Makes the fake gateway report a captured payment."""
    payment = {
        "id": payment_id,
        "order_id": order_id,
        "amount": amount_paise,
        "status": "captured",
        "method": "upi",
    }
    state["payments"][payment_id] = payment
    return payment


# ------------------------------------------------------------- empty wallet
async def test_wallet_starts_at_zero(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await client.get(f"{P}/wallet", headers=auth)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["wallet"]["balance_coins"] == 0
    assert data["wallet"]["balance_coins"] == 0
    assert data["recent"] == []


async def test_wallet_needs_a_signed_in_user(client: AsyncClient) -> None:
    assert (await client.get(f"{P}/wallet")).status_code == 401


# ----------------------------------------------------------------- amounts
async def test_amount_below_the_minimum_is_rejected(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)

    response = await open_order(client, auth, amount_paise=500)  # Rs 5
    assert response.status_code == 400
    assert response.json()["error_code"] == "amount_too_small"


async def test_amount_above_the_maximum_is_rejected(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)

    response = await open_order(client, auth, amount_paise=99_999_999)
    assert response.status_code == 400
    assert response.json()["error_code"] == "amount_too_large"


async def test_order_is_opened_for_a_valid_amount(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)

    response = await open_order(client, auth, amount_paise=50_000)
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["amount_paise"] == 50_000
    assert data["razorpay_order_id"].startswith("order_")
    assert data["key_id"] == "rzp_test_fake"


# ------------------------------------------------------------- the happy path
async def test_a_verified_payment_credits_the_wallet(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]
    capture(fake_razorpay, order_id, 50_000)

    response = await client.post(
        f"{P}/wallet/recharge/verify",
        headers=auth,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_fake1",
            "razorpay_signature": sign_callback(order_id, "pay_fake1"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["credited"] is True
    assert data["balance_coins"] == 500

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 500
    assert wallet["recent"][0]["reason"] == "recharge"
    assert wallet["recent"][0]["balance_after_coins"] == 500


# ------------------------------------------------------------------ attacks
async def test_a_forged_signature_credits_nothing(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]
    capture(fake_razorpay, order_id, 50_000)

    response = await client.post(
        f"{P}/wallet/recharge/verify",
        headers=auth,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_fake1",
            "razorpay_signature": "0" * 64,
        },
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_signature"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 0


async def test_a_payment_worth_less_than_the_order_is_refused(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """The amount is Razorpay's, and it has to match what was asked for."""
    auth = await signed_in(client)
    order_id = (await open_order(client, auth, amount_paise=50_000)).json()["data"][
        "razorpay_order_id"
    ]
    capture(fake_razorpay, order_id, 100)  # paid Re 1 against a Rs 500 order

    response = await client.post(
        f"{P}/wallet/recharge/verify",
        headers=auth,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_fake1",
            "razorpay_signature": sign_callback(order_id, "pay_fake1"),
        },
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "amount_mismatch"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 0


async def test_another_users_order_cannot_be_claimed(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    victim = await signed_in(client, "victim@test.dev")
    attacker = await signed_in(client, "attacker@test.dev")

    order_id = (await open_order(client, victim)).json()["data"]["razorpay_order_id"]
    capture(fake_razorpay, order_id, 50_000)

    response = await client.post(
        f"{P}/wallet/recharge/verify",
        headers=attacker,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_fake1",
            "razorpay_signature": sign_callback(order_id, "pay_fake1"),
        },
    )
    assert response.status_code == 404

    stolen = (await client.get(f"{P}/wallet", headers=attacker)).json()["data"]
    assert stolen["wallet"]["balance_coins"] == 0


# ------------------------------------------------------------- idempotency
async def test_the_same_payment_credits_only_once(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]
    capture(fake_razorpay, order_id, 50_000)

    body = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": "pay_fake1",
        "razorpay_signature": sign_callback(order_id, "pay_fake1"),
    }
    first = await client.post(f"{P}/wallet/recharge/verify", headers=auth, json=body)
    second = await client.post(f"{P}/wallet/recharge/verify", headers=auth, json=body)

    assert first.json()["data"]["credited"] is True
    assert second.status_code == 200
    assert second.json()["data"]["credited"] is False

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 500

    history = (await client.get(f"{P}/wallet/transactions", headers=auth)).json()["data"]
    assert history["meta"]["total"] == 1


async def test_callback_and_webhook_together_credit_once(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """The real-world race: both confirmations describe the same payment."""
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]
    payment = capture(fake_razorpay, order_id, 50_000)

    await client.post(
        f"{P}/wallet/recharge/verify",
        headers=auth,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_fake1",
            "razorpay_signature": sign_callback(order_id, "pay_fake1"),
        },
    )
    body, signature = webhook_body("payment.captured", {"payment": {"entity": payment}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "X-Razorpay-Event-Id": "evt_1",
            "Content-Type": "application/json",
        },
    )
    assert hook.status_code == 200
    assert hook.json()["result"] == "already_credited"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 500


# ------------------------------------------------------------------ webhook
async def test_webhook_alone_credits_when_the_browser_never_came_back(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """The UPI case: the app switched away and the callback was lost."""
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]
    payment = capture(fake_razorpay, order_id, 50_000)

    body, signature = webhook_body("payment.captured", {"payment": {"entity": payment}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "X-Razorpay-Event-Id": "evt_solo",
            "Content-Type": "application/json",
        },
    )
    assert hook.status_code == 200, hook.text
    assert hook.json()["result"] == "credited"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 500


async def test_a_webhook_with_a_bad_signature_is_refused(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]
    payment = capture(fake_razorpay, order_id, 50_000)

    body, _ = webhook_body("payment.captured", {"payment": {"entity": payment}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": "deadbeef",
            "X-Razorpay-Event-Id": "evt_bad",
            "Content-Type": "application/json",
        },
    )
    assert hook.status_code == 401

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 0


async def test_a_replayed_webhook_does_nothing(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """Razorpay retries until it gets a 2xx."""
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]
    payment = capture(fake_razorpay, order_id, 50_000)
    body, signature = webhook_body("payment.captured", {"payment": {"entity": payment}})
    headers = {
        "X-Razorpay-Signature": signature,
        "X-Razorpay-Event-Id": "evt_same",
        "Content-Type": "application/json",
    }

    first = await client.post(f"{P}/webhooks/razorpay", content=body, headers=headers)
    second = await client.post(f"{P}/webhooks/razorpay", content=body, headers=headers)

    assert first.json()["result"] == "credited"
    assert second.json()["result"] == "duplicate"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 500


async def test_a_failed_payment_leaves_the_balance_alone(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]

    failed = {
        "id": "pay_dead",
        "order_id": order_id,
        "amount": 50_000,
        "status": "failed",
        "error_description": "Payment was not completed",
    }
    body, signature = webhook_body("payment.failed", {"payment": {"entity": failed}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "X-Razorpay-Event-Id": "evt_failed",
            "Content-Type": "application/json",
        },
    )
    assert hook.json()["result"] == "marked_failed"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 0


# -------------------------------------------------------------------- admin
async def test_admin_can_adjust_a_wallet_and_it_is_attributed(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    uid = await user_id_for("wallet@test.dev")

    response = await client.post(
        f"{P}/admin/wallets/{uid}/adjust",
        headers=admin,
        json={"direction": "credit", "amount_coins": 250, "reason": "Goodwill for a bad call"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["data"]["balance_coins"] == 250

    rows = (
        await client.get(f"{P}/admin/wallets/transactions?user_id={uid}", headers=admin)
    ).json()["data"]["items"]
    assert rows[0]["reason"] == "adjustment"
    assert rows[0]["created_by"] is not None
    assert rows[0]["note"] == "Goodwill for a bad call"

    mine = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert mine["wallet"]["balance_coins"] == 250


async def test_an_adjustment_must_say_why(client: AsyncClient) -> None:
    await signed_in(client)
    admin = await make_admin(client)
    uid = await user_id_for("wallet@test.dev")

    response = await client.post(
        f"{P}/admin/wallets/{uid}/adjust",
        headers=admin,
        json={"direction": "credit", "amount_coins": 500, "reason": ""},
    )
    assert response.status_code == 422


async def test_a_user_cannot_reach_the_admin_wallet_routes(client: AsyncClient) -> None:
    auth = await signed_in(client)
    uid = await user_id_for("wallet@test.dev")

    assert (await client.get(f"{P}/admin/wallets", headers=auth)).status_code == 403
    assert (
        await client.post(
            f"{P}/admin/wallets/{uid}/adjust",
            headers=auth,
            json={"direction": "credit", "amount_coins": 1000, "reason": "mine now"},
        )
    ).status_code == 403


async def test_a_frozen_wallet_refuses_to_move(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    uid = await user_id_for("wallet@test.dev")

    await client.post(
        f"{P}/admin/wallets/{uid}/freeze",
        headers=admin,
        json={"frozen": True, "reason": "Suspicious recharges"},
    )

    blocked = await open_order(client, auth)
    assert blocked.status_code == 400
    assert blocked.json()["error_code"] == "wallet_frozen"

    mine = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert mine["wallet"]["is_frozen"] is True
    assert mine["wallet"]["frozen_reason"] == "Suspicious recharges"


# ------------------------------------------------------------- the invariant
async def test_the_balance_always_equals_the_ledger(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    uid = await user_id_for("wallet@test.dev")

    order_id = (await open_order(client, auth, 100_000)).json()["data"]["razorpay_order_id"]
    capture(fake_razorpay, order_id, 100_000)
    await client.post(
        f"{P}/wallet/recharge/verify",
        headers=auth,
        json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_fake1",
            "razorpay_signature": sign_callback(order_id, "pay_fake1"),
        },
    )
    await client.post(
        f"{P}/admin/wallets/{uid}/adjust",
        headers=admin,
        json={"direction": "debit", "amount_coins": 300, "reason": "Correction"},
    )

    result = (
        await client.post(f"{P}/admin/wallets/{uid}/reconcile", headers=admin)
    ).json()["data"]
    assert result["credited_coins"] == 1000
    assert result["debited_coins"] == 300
    assert result["ledger_balance_coins"] == 700
    assert result["drift_coins"] == 0


async def test_a_debit_cannot_go_below_zero(client: AsyncClient) -> None:
    await signed_in(client)
    admin = await make_admin(client)
    uid = await user_id_for("wallet@test.dev")

    response = await client.post(
        f"{P}/admin/wallets/{uid}/adjust",
        headers=admin,
        json={"direction": "debit", "amount_coins": 100, "reason": "Take what is not there"},
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "insufficient_balance"


# -------------------------------------------------- only captured money counts
async def test_an_authorised_payment_does_not_credit_yet(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """Authorised means the bank is holding the money, not that Razorpay took
    it. That hold can be voided, so crediting it would let someone spend money
    that never settles."""
    auth = await signed_in(client)
    order_id = (await open_order(client, auth)).json()["data"]["razorpay_order_id"]

    held = {
        "id": "pay_held",
        "order_id": order_id,
        "amount": 50_000,
        "status": "authorized",
        "method": "card",
    }
    body, signature = webhook_body("payment.authorized", {"payment": {"entity": held}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "X-Razorpay-Event-Id": "evt_authorised",
            "Content-Type": "application/json",
        },
    )
    assert hook.json()["result"] == "awaiting_capture"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 0

    # Capture arrives moments later, and *that* credits.
    captured = {**held, "status": "captured"}
    body, signature = webhook_body("payment.captured", {"payment": {"entity": captured}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "X-Razorpay-Event-Id": "evt_captured",
            "Content-Type": "application/json",
        },
    )
    assert hook.json()["result"] == "credited"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 500


async def test_an_event_we_do_not_handle_is_dropped_without_a_record(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """The account subscribes to 55 event types. Storing the ones we ignore
    would fill the collection with noise."""
    from app.models.wallet import WebhookEvent

    body, signature = webhook_body("settlement.processed", {"settlement": {"entity": {}}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "X-Razorpay-Event-Id": "evt_settlement",
            "Content-Type": "application/json",
        },
    )
    assert hook.status_code == 200
    assert hook.json()["result"] == "ignored"
    assert await WebhookEvent.find(WebhookEvent.event_id == "evt_settlement").count() == 0


async def test_an_unhandled_event_with_a_bad_signature_is_still_refused(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """Signature first, event filtering second — never the other way round."""
    body, _ = webhook_body("settlement.processed", {"settlement": {"entity": {}}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": "nope",
            "X-Razorpay-Event-Id": "evt_bad_settlement",
            "Content-Type": "application/json",
        },
    )
    assert hook.status_code == 401


# ===========================================================================
# Coins — the rate an admin sets, and the three ways it can go wrong
# ===========================================================================


async def set_rate(client: AsyncClient, admin: dict, rate: int):
    return await client.patch(
        f"{P}/admin/settings", headers=admin, json={"coins_per_rupee": rate}
    )


async def recharge(client: AsyncClient, auth: dict, rupees: int, state: dict, payment_id: str):
    """Opens an order, captures it, and confirms it through the callback."""
    order = (await open_order(client, auth, rupees * 100)).json()["data"]
    capture(state, order["razorpay_order_id"], rupees * 100, payment_id)
    await client.post(
        f"{P}/wallet/recharge/verify",
        headers=auth,
        json={
            "razorpay_order_id": order["razorpay_order_id"],
            "razorpay_payment_id": payment_id,
            "razorpay_signature": sign_callback(order["razorpay_order_id"], payment_id),
        },
    )
    return order


# ------------------------------------------------------ the client's example
async def test_rate_of_ten_turns_a_hundred_rupees_into_a_thousand_coins(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    await set_rate(client, admin, 10)

    order = (await open_order(client, auth, 10_000)).json()["data"]
    assert order["coins"] == 1000
    assert order["coins_per_rupee"] == 10

    capture(fake_razorpay, order["razorpay_order_id"], 10_000, "pay_c1")
    result = await client.post(
        f"{P}/wallet/recharge/verify",
        headers=auth,
        json={
            "razorpay_order_id": order["razorpay_order_id"],
            "razorpay_payment_id": "pay_c1",
            "razorpay_signature": sign_callback(order["razorpay_order_id"], "pay_c1"),
        },
    )
    assert result.status_code == 200, result.text
    assert result.json()["data"]["coins"] == 1000
    assert result.json()["data"]["balance_coins"] == 1000

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 1000
    row = wallet["recent"][0]
    assert row["amount_coins"] == 1000
    assert row["amount_paise"] == 10_000  # what was actually paid
    assert row["coins_per_rupee"] == 10


async def test_coins_add_to_what_is_already_there(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """The client's second example: 100 already held + 1000 bought = 1100."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    uid = await user_id_for("wallet@test.dev")

    await client.post(
        f"{P}/admin/wallets/{uid}/adjust",
        headers=admin,
        json={"direction": "credit", "amount_coins": 100, "reason": "Opening balance"},
    )
    await set_rate(client, admin, 10)
    await recharge(client, auth, 100, fake_razorpay, "pay_c2")

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 1100


# --------------------------------------------- the rate changing mid-payment
async def test_the_quoted_rate_is_honoured_even_if_it_changes_mid_checkout(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """The user was shown 1000 coins before paying. An admin halving the rate
    while the checkout window is open must not halve what they get."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    await set_rate(client, admin, 10)

    order = (await open_order(client, auth, 10_000)).json()["data"]
    assert order["coins"] == 1000

    # The admin changes the rate while the user is still on the payment screen.
    await set_rate(client, admin, 5)

    capture(fake_razorpay, order["razorpay_order_id"], 10_000, "pay_c3")
    await client.post(
        f"{P}/wallet/recharge/verify",
        headers=auth,
        json={
            "razorpay_order_id": order["razorpay_order_id"],
            "razorpay_payment_id": "pay_c3",
            "razorpay_signature": sign_callback(order["razorpay_order_id"], "pay_c3"),
        },
    )

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 1000, "the promised coins, not the new rate"

    # And the next recharge does use the new rate.
    nxt = (await open_order(client, auth, 10_000)).json()["data"]
    assert nxt["coins"] == 500


# ------------------------------------------------- refunds after a rate change
async def test_a_refund_takes_back_the_coins_that_recharge_gave(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """Recomputing at today's rate would take back 500 and leave the user 500
    coins they no longer paid for."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    await set_rate(client, admin, 10)
    await recharge(client, auth, 100, fake_razorpay, "pay_c4")

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 1000

    await set_rate(client, admin, 5)

    refund = {"id": "rfnd_1", "payment_id": "pay_c4", "amount": 10_000}
    body, signature = webhook_body("refund.processed", {"refund": {"entity": refund}})
    hook = await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "X-Razorpay-Event-Id": "evt_refund",
            "Content-Type": "application/json",
        },
    )
    assert hook.json()["result"] == "refunded"

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 0, "all 1000 back, not 500"


async def test_a_partial_refund_takes_back_the_same_share_of_coins(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    await set_rate(client, admin, 10)
    await recharge(client, auth, 100, fake_razorpay, "pay_c5")

    # Half the money back, so half the coins.
    refund = {"id": "rfnd_half", "payment_id": "pay_c5", "amount": 5_000}
    body, signature = webhook_body("refund.processed", {"refund": {"entity": refund}})
    await client.post(
        f"{P}/webhooks/razorpay",
        content=body,
        headers={
            "X-Razorpay-Signature": signature,
            "X-Razorpay-Event-Id": "evt_refund_half",
            "Content-Type": "application/json",
        },
    )

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 500


# ----------------------------------------------------------- no half coins
async def test_an_amount_that_is_not_whole_rupees_is_rejected(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """Rs 99.55 at 10 coins/rupee would be 995.5 coins."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    await set_rate(client, admin, 10)

    response = await open_order(client, auth, 9_955)
    assert response.status_code == 400
    assert response.json()["error_code"] == "not_whole_rupees"


async def test_a_rate_below_one_is_rejected(client: AsyncClient) -> None:
    admin = await make_admin(client)
    for bad in (0, -5):
        response = await set_rate(client, admin, bad)
        assert response.status_code == 422, bad


# -------------------------------------------------------------------- audit
async def test_a_rate_change_records_who_made_it(client: AsyncClient) -> None:
    admin = await make_admin(client)

    await set_rate(client, admin, 10)
    await set_rate(client, admin, 25)

    history = (
        await client.get(f"{P}/admin/settings/coin-rate-history", headers=admin)
    ).json()["data"]
    assert [(h["from_rate"], h["to_rate"]) for h in history] == [(10, 25), (1, 10)]
    assert history[0]["changed_by_email"] == "walletadmin@test.dev"


async def test_setting_the_same_rate_again_is_not_recorded(client: AsyncClient) -> None:
    admin = await make_admin(client)

    await set_rate(client, admin, 10)
    await set_rate(client, admin, 10)

    history = (
        await client.get(f"{P}/admin/settings/coin-rate-history", headers=admin)
    ).json()["data"]
    assert len(history) == 1


async def test_a_user_cannot_change_the_coin_rate(client: AsyncClient) -> None:
    auth = await signed_in(client)

    assert (await client.get(f"{P}/admin/settings", headers=auth)).status_code == 403
    assert (await set_rate(client, auth, 1000)).status_code == 403


async def test_the_recharge_screen_quotes_coins_for_every_pack(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    await set_rate(client, admin, 10)

    options = (await client.get(f"{P}/wallet/recharge/options", headers=auth)).json()["data"]
    assert options["coins_per_rupee"] == 10
    assert [p["coins"] for p in options["packs"]] == [
        p["amount_rupees"] * 10 for p in options["packs"]
    ]


# ================= the minimum an admin sets, and the client's example ======


async def set_limits(client: AsyncClient, admin: dict, *, minimum=None, maximum=None):
    body = {}
    if minimum is not None:
        body["min_recharge_paise"] = minimum
    if maximum is not None:
        body["max_recharge_paise"] = maximum
    return await client.patch(f"{P}/admin/settings/recharge-limits", headers=admin, json=body)


async def test_the_client_example_end_to_end(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """₹1 = 5 coins, 50 coins already held, ₹100 recharged → 550."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    uid = await user_id_for("wallet@test.dev")

    await set_rate(client, admin, 5)
    await client.post(
        f"{P}/admin/wallets/{uid}/adjust",
        headers=admin,
        json={"direction": "credit", "amount_coins": 50, "reason": "Opening balance"},
    )

    options = (await client.get(f"{P}/wallet/recharge/options", headers=auth)).json()["data"]
    assert options["coins_per_rupee"] == 5

    await recharge(client, auth, 100, fake_razorpay, "pay_example")

    wallet = (await client.get(f"{P}/wallet", headers=auth)).json()["data"]
    assert wallet["wallet"]["balance_coins"] == 550, "50 held + 100 x 5 bought"


async def test_an_admin_sets_the_minimum_recharge(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)

    await set_limits(client, admin, minimum=20_000)  # Rs 200

    # The user is told before they try.
    options = (await client.get(f"{P}/wallet/recharge/options", headers=auth)).json()["data"]
    assert options["min_paise"] == 20_000

    too_small = await open_order(client, auth, 10_000)  # Rs 100
    assert too_small.status_code == 400
    assert too_small.json()["error_code"] == "amount_too_small"
    assert "₹200" in too_small.json()["message"]

    assert (await open_order(client, auth, 20_000)).status_code == 201


async def test_presets_below_the_minimum_are_not_offered(
    client: AsyncClient, fake_razorpay: dict
) -> None:
    """A button that can only be refused is worse than no button."""
    auth = await signed_in(client)
    admin = await make_admin(client)

    await set_limits(client, admin, minimum=50_000)  # Rs 500

    options = (await client.get(f"{P}/wallet/recharge/options", headers=auth)).json()["data"]
    assert options["packs"], "some presets should survive"
    assert all(p["amount_paise"] >= 50_000 for p in options["packs"])


async def test_the_maximum_can_be_set_too(client: AsyncClient, fake_razorpay: dict) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)

    await set_limits(client, admin, maximum=100_000)  # Rs 1,000

    too_big = await open_order(client, auth, 200_000)
    assert too_big.status_code == 400
    assert too_big.json()["error_code"] == "amount_too_large"


async def test_a_minimum_above_the_maximum_is_refused(client: AsyncClient) -> None:
    """Otherwise there would be no amount anyone could pay."""
    admin = await make_admin(client)

    response = await set_limits(client, admin, minimum=500_000, maximum=10_000)
    assert response.status_code == 400
    assert response.json()["error_code"] == "invalid_recharge_limits"


async def test_recharge_limits_must_be_whole_rupees(client: AsyncClient) -> None:
    admin = await make_admin(client)

    response = await set_limits(client, admin, minimum=10_050)
    assert response.status_code == 400
    assert response.json()["error_code"] == "not_whole_rupees"


async def test_only_an_admin_can_change_the_limits(client: AsyncClient) -> None:
    auth = await signed_in(client)
    assert (await set_limits(client, auth, minimum=100_000)).status_code == 403


async def test_changing_one_limit_leaves_the_other_alone(client: AsyncClient) -> None:
    admin = await make_admin(client)

    await set_limits(client, admin, minimum=20_000, maximum=300_000)
    await set_limits(client, admin, minimum=30_000)

    settings_now = (await client.get(f"{P}/admin/settings", headers=admin)).json()["data"]
    assert settings_now["min_recharge_paise"] == 30_000
    assert settings_now["max_recharge_paise"] == 300_000
