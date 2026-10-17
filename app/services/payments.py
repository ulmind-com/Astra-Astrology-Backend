"""Razorpay recharges.

The one rule here: **the browser never decides that money arrived.** A wallet is
credited only after a signature made with our secret checks out, and the amount
credited is read from Razorpay's own record of the payment — never from the
request body, which the user controls.

Two independent paths confirm a payment:

* the browser callback, which is instant but is lost whenever the user's app
  switches away to a UPI app and does not come back;
* the webhook, which always arrives (Razorpay retries) but can be delayed.

Both call the same credit, and the idempotency key makes the second one a no-op.
"""

import asyncio
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import razorpay
from loguru import logger

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    NotFoundError,
    ServiceUnavailableError,
    TooManyRequestsError,
    UnauthorizedError,
)
from app.models.enums import PaymentOrderStatus, TransactionReason
from app.models.user import User
from app.models.wallet import PaymentOrder, TransactionRef, WebhookEvent
from app.services import wallet as wallet_service

_client: razorpay.Client | None = None


def is_enabled() -> bool:
    return settings.razorpay_configured


def _razorpay() -> razorpay.Client:
    global _client
    if not is_enabled():
        raise ServiceUnavailableError(
            "Payments are not configured yet. Please try again later.",
            error_code="payments_unavailable",
        )
    if _client is None:
        _client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    return _client


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


# ------------------------------------------------------------------ order


async def create_order(user: User, amount_paise: int) -> PaymentOrder:
    """Opens a Razorpay order for a recharge."""
    if amount_paise < settings.WALLET_MIN_RECHARGE_PAISE:
        raise BadRequestError(
            f"The smallest recharge is ₹{settings.WALLET_MIN_RECHARGE_PAISE // 100}.",
            error_code="amount_too_small",
        )
    if amount_paise > settings.WALLET_MAX_RECHARGE_PAISE:
        raise BadRequestError(
            f"The largest recharge is ₹{settings.WALLET_MAX_RECHARGE_PAISE // 100}.",
            error_code="amount_too_large",
        )

    wallet = await wallet_service.get_or_create_wallet(user.id)
    if wallet.is_frozen:
        raise BadRequestError(
            "This wallet is frozen. Please contact support.", error_code="wallet_frozen"
        )

    # Stops the endpoint being used to hammer Razorpay with orders.
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    recent = await PaymentOrder.find(
        PaymentOrder.user_id == user.id,
        PaymentOrder.created_at > one_hour_ago,
    ).count()
    if recent >= settings.RECHARGE_ORDERS_PER_HOUR:
        raise TooManyRequestsError(
            "Too many recharge attempts. Please wait a while and try again.",
            error_code="too_many_orders",
        )

    receipt = f"rcg_{secrets.token_hex(8)}"
    try:
        created: dict[str, Any] = await asyncio.to_thread(
            _razorpay().order.create,
            {
                "amount": amount_paise,
                "currency": settings.WALLET_CURRENCY,
                "receipt": receipt,
                "notes": {"user_id": str(user.id), "purpose": "wallet_recharge"},
            },
        )
    except Exception as exc:  # noqa: BLE001 - surfaced as 503
        logger.opt(exception=exc).error("Razorpay order creation failed for {}", user.email)
        raise ServiceUnavailableError(
            "Could not start the payment. Please try again.",
            error_code="order_failed",
        ) from exc

    order = PaymentOrder(
        user_id=user.id,
        razorpay_order_id=created["id"],
        receipt=receipt,
        amount_paise=amount_paise,
        currency=settings.WALLET_CURRENCY,
    )
    await order.insert()
    logger.info("Recharge order {} opened for {} ({} paise)", order.razorpay_order_id, user.email, amount_paise)
    return order


# --------------------------------------------------------------- crediting


async def _fetch_payment(payment_id: str) -> dict[str, Any]:
    try:
        return await asyncio.to_thread(_razorpay().payment.fetch, payment_id)
    except Exception as exc:  # noqa: BLE001
        logger.opt(exception=exc).error("Could not fetch Razorpay payment {}", payment_id)
        raise ServiceUnavailableError(
            "Could not confirm the payment with the gateway. If money was debited it "
            "will be credited automatically.",
            error_code="payment_fetch_failed",
        ) from exc


async def _credit_for_payment(
    *, order: PaymentOrder, payment: dict[str, Any], via: str
) -> tuple[bool, int]:
    """Credits the wallet for a captured payment. Returns (was_new, amount)."""
    payment_id = payment["id"]
    status = payment.get("status")

    # Only `captured` credits. `authorized` means the bank is holding the money
    # but Razorpay has not taken it — that hold can still be voided or expire,
    # and a wallet credited from it could be spent on money that never settles.
    # Checkout auto-captures, so `payment.captured` follows within moments.
    if status != "captured":
        logger.info("Payment {} is '{}', not crediting yet.", payment_id, status)
        return False, 0

    # The amount is Razorpay's, not the caller's. It must also match what we
    # asked for, or something has been tampered with.
    amount_paise = int(payment["amount"])
    if amount_paise != order.amount_paise:
        logger.error(
            "Payment {} is {} paise but order {} was for {} — refusing to credit.",
            payment_id,
            amount_paise,
            order.razorpay_order_id,
            order.amount_paise,
        )
        raise BadRequestError(
            "The payment does not match the order.", error_code="amount_mismatch"
        )

    _, was_new = await wallet_service.credit(
        user_id=order.user_id,
        amount_paise=amount_paise,
        reason=TransactionReason.RECHARGE,
        # The payment id, so the callback and the webhook collapse into one row.
        idempotency_key=f"rzp_payment:{payment_id}",
        ref=TransactionRef(
            razorpay_order_id=order.razorpay_order_id, razorpay_payment_id=payment_id
        ),
        note=f"Wallet recharge of ₹{amount_paise // 100}",
    )

    if order.status is not PaymentOrderStatus.PAID:
        order.status = PaymentOrderStatus.PAID
        order.razorpay_payment_id = payment_id
        order.method = payment.get("method")
        order.verified_via = via
        order.paid_at = datetime.now(UTC)
        await order.save()

    return was_new, amount_paise


# ------------------------------------------------------- browser callback


async def verify_callback(
    *, user: User, order_id: str, payment_id: str, signature: str
) -> tuple[PaymentOrder, bool]:
    """Confirms the payment the browser just reported."""
    expected = _sign(f"{order_id}|{payment_id}", settings.RAZORPAY_KEY_SECRET)
    if not hmac.compare_digest(expected, signature):
        logger.warning("Bad payment signature from user {} for order {}", user.email, order_id)
        raise UnauthorizedError(
            "This payment could not be verified.", error_code="invalid_signature"
        )

    order = await PaymentOrder.find_one(PaymentOrder.razorpay_order_id == order_id)
    if order is None:
        raise NotFoundError("Payment order not found.", error_code="order_not_found")
    if order.user_id != user.id:
        raise NotFoundError("Payment order not found.", error_code="order_not_found")

    payment = await _fetch_payment(payment_id)
    was_new, _ = await _credit_for_payment(order=order, payment=payment, via="callback")
    return order, was_new


# ------------------------------------------------------------------ webhook


def verify_webhook_signature(raw_body: bytes, signature: str | None) -> None:
    """Checks the signature over the *raw* bytes.

    Re-serialising the JSON first would change the bytes and break the digest,
    so the body must never be parsed before this runs.
    """
    if not settings.razorpay_webhook_configured:
        # Processing an unverifiable webhook would let anyone credit any wallet.
        logger.error("Razorpay webhook received but RAZORPAY_WEBHOOK_SECRET is not set.")
        raise UnauthorizedError(
            "Webhooks are not configured.", error_code="webhook_not_configured"
        )
    if not signature:
        raise UnauthorizedError("Missing signature.", error_code="missing_signature")

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        logger.warning("Rejected a Razorpay webhook with a bad signature.")
        raise UnauthorizedError("Invalid signature.", error_code="invalid_signature")


# Razorpay lets an account subscribe to every event it emits. Recording the
# ones we do nothing with would fill the collection with noise, so unknown
# events are acknowledged and dropped without a write.
HANDLED_EVENTS = frozenset(
    {"payment.captured", "payment.authorized", "payment.failed", "refund.processed"}
)


async def handle_webhook(*, event_id: str | None, body: dict[str, Any]) -> str:
    """Processes one verified webhook. Safe to call twice with the same event."""
    event = body.get("event", "")

    if event not in HANDLED_EVENTS:
        logger.debug("Ignoring Razorpay event '{}'.", event)
        return "ignored"

    key = event_id or f"{event}:{body.get('created_at')}"

    record = WebhookEvent(event_id=key, event=event, payload=body)
    try:
        await record.insert()
    except Exception as exc:  # DuplicateKeyError - Razorpay retried
        if type(exc).__name__ != "DuplicateKeyError":
            raise
        logger.info("Razorpay webhook {} already handled.", key)
        return "duplicate"

    result = await _dispatch(event, body)

    record.processed_at = datetime.now(UTC)
    record.result = result
    await record.save()
    return result


async def _dispatch(event: str, body: dict[str, Any]) -> str:
    payload = body.get("payload", {})

    if event in {"payment.captured", "payment.authorized"}:
        payment = payload.get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        if not order_id:
            return "ignored_no_order"
        order = await PaymentOrder.find_one(PaymentOrder.razorpay_order_id == order_id)
        if order is None:
            logger.warning("Webhook for unknown order {}", order_id)
            return "unknown_order"
        if payment.get("status") != "captured":
            # Authorised only: the money is held, not taken. `payment.captured`
            # follows, and that is what credits.
            return "awaiting_capture"
        was_new, _ = await _credit_for_payment(order=order, payment=payment, via="webhook")
        return "credited" if was_new else "already_credited"

    if event == "payment.failed":
        payment = payload.get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        order = (
            await PaymentOrder.find_one(PaymentOrder.razorpay_order_id == order_id)
            if order_id
            else None
        )
        if order is not None and order.status is PaymentOrderStatus.CREATED:
            order.status = PaymentOrderStatus.FAILED
            order.razorpay_payment_id = payment.get("id")
            order.failure_reason = payment.get("error_description") or payment.get(
                "error_reason"
            )
            await order.save()
        return "marked_failed"

    if event == "refund.processed":
        refund = payload.get("refund", {}).get("entity", {})
        payment_id = refund.get("payment_id")
        amount_paise = int(refund.get("amount") or 0)
        order = (
            await PaymentOrder.find_one(PaymentOrder.razorpay_payment_id == payment_id)
            if payment_id
            else None
        )
        if order is None or amount_paise <= 0:
            return "unknown_refund"
        # Take the money back out. A refund can leave the balance short if it
        # was already spent, so this is allowed to be refused.
        try:
            await wallet_service.debit(
                user_id=order.user_id,
                amount_paise=amount_paise,
                reason=TransactionReason.REFUND,
                idempotency_key=f"rzp_refund:{refund.get('id')}",
                ref=TransactionRef(
                    razorpay_order_id=order.razorpay_order_id,
                    razorpay_payment_id=payment_id,
                    razorpay_refund_id=refund.get("id"),
                ),
                note=f"Refund of ₹{amount_paise // 100}",
                allow_when_frozen=True,
            )
        except BadRequestError:
            logger.error(
                "Refund {} could not be taken back from wallet {} — balance already spent.",
                refund.get("id"),
                order.user_id,
            )
            return "refund_unrecoverable"
        return "refunded"

    return "ignored"


# ------------------------------------------------------------- reconcile


async def reconcile_order(order: PaymentOrder) -> PaymentOrder:
    """Asks Razorpay what actually happened to an order still sitting at
    `created` — the repair path when both confirmations were lost."""
    try:
        payments = await asyncio.to_thread(
            _razorpay().order.payments, order.razorpay_order_id
        )
    except Exception as exc:  # noqa: BLE001
        raise ServiceUnavailableError(
            "Could not reach the payment gateway.", error_code="gateway_unavailable"
        ) from exc

    for payment in payments.get("items", []):
        if payment.get("status") == "captured":
            await _credit_for_payment(order=order, payment=payment, via="reconcile")
            break
    else:
        if order.status is PaymentOrderStatus.CREATED:
            order.status = PaymentOrderStatus.FAILED
            order.failure_reason = "No successful payment found for this order."
            await order.save()

    return order
