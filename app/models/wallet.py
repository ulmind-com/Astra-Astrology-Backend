"""The money layer.

Two rules shape every document here:

1. **The ledger is the truth.** `WalletTransaction` is append-only — a mistake
   is corrected with a reversing row, never by editing or deleting one. The
   wallet's `balance_paise` is a cache of that ledger and can be rebuilt from
   it, so a lost write can always be proven and repaired.

2. **The wallet holds coins, not money.** An admin sets how many coins a rupee
   buys, and that rate can change. Storing rupees and multiplying at display
   time would make every existing balance jump the moment the rate moved, so
   coins people already bought are stored as coins and keep their value.
   Rupees survive only where money actually changed hands: on a recharge row
   and on the payment order.

3. **Everything is an integer.** Coins are whole, and the rupee side is whole
   paise. Floats cannot hold 0.1 exactly, and a balance debited per minute
   would drift away from its own ledger within a day.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument
from app.models.enums import (
    PaymentOrderStatus,
    TransactionDirection,
    TransactionReason,
)


class Wallet(TimestampedDocument):
    """One per user. `balance_coins` is derived from the ledger, never authored."""

    user_id: PydanticObjectId
    balance_coins: int = Field(default=0, ge=0)

    # Set by an admin when something looks wrong. A frozen wallet refuses both
    # credits and debits, so the balance cannot move while it is investigated.
    is_frozen: bool = False
    frozen_reason: str | None = None

    last_transaction_at: datetime | None = None

    class Settings:
        name = "wallets"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING)], name="wallet_user_unique", unique=True
            ),
        ]


class TransactionRef(BaseModel):
    """What a movement points at, so history can be traced back to its cause."""

    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_refund_id: str | None = None
    session_id: PydanticObjectId | None = None
    reverses_transaction_id: PydanticObjectId | None = None


class WalletTransaction(TimestampedDocument):
    """One movement of money. Append-only."""

    wallet_id: PydanticObjectId
    user_id: PydanticObjectId

    direction: TransactionDirection
    reason: TransactionReason
    # Always positive — `direction` carries the sign. Storing signed amounts
    # invites a missing abs() somewhere to silently flip a debit into a credit.
    amount_coins: int = Field(gt=0)

    # Snapshot taken when the row was written, so a statement renders without
    # re-summing the whole ledger.
    balance_after_coins: int = Field(ge=0)

    # Only on rows where money changed hands (a recharge, or a refund of one):
    # what was actually paid, and the rate that was honoured. Kept so a
    # statement can show "₹100 → 1000 coins" years after the rate has moved on.
    amount_paise: int | None = Field(default=None, ge=0)
    coins_per_rupee: int | None = Field(default=None, ge=1)

    # The guard against double credit. For a recharge this is the Razorpay
    # payment id, so the browser callback and the webhook — which both describe
    # the same payment — can only ever insert one row.
    idempotency_key: str

    ref: TransactionRef = Field(default_factory=TransactionRef)
    note: str | None = Field(default=None, max_length=300)
    # Set when an admin moved the money by hand.
    created_by: PydanticObjectId | None = None

    class Settings:
        name = "wallet_transactions"
        indexes = [
            pymongo.IndexModel(
                [("idempotency_key", pymongo.ASCENDING)],
                name="txn_idempotency_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="txn_user_recent",
            ),
            pymongo.IndexModel([("wallet_id", pymongo.ASCENDING)], name="txn_wallet"),
            pymongo.IndexModel([("reason", pymongo.ASCENDING)], name="txn_reason"),
            pymongo.IndexModel(
                [("ref.razorpay_payment_id", pymongo.ASCENDING)], name="txn_payment"
            ),
        ]


class PaymentOrder(TimestampedDocument):
    """One recharge attempt.

    Attempts that never completed are kept on purpose: when a user says the
    money left their bank but the wallet stayed empty, this is the only record
    that the attempt happened at all.
    """

    user_id: PydanticObjectId
    razorpay_order_id: str
    receipt: str

    amount_paise: int = Field(gt=0)
    currency: str = "INR"

    # Frozen when the order is opened. The user was shown this many coins before
    # they paid, so this is what gets credited even if an admin changes the rate
    # while the checkout window is still open.
    coins_per_rupee: int = Field(ge=1)
    coins: int = Field(gt=0)

    status: PaymentOrderStatus = PaymentOrderStatus.CREATED

    razorpay_payment_id: str | None = None
    method: str | None = None  # upi / card / netbanking …
    failure_reason: str | None = None
    # Which path confirmed it: the browser callback, or the webhook.
    verified_via: str | None = None
    paid_at: datetime | None = None

    class Settings:
        name = "payment_orders"
        indexes = [
            pymongo.IndexModel(
                [("razorpay_order_id", pymongo.ASCENDING)],
                name="order_razorpay_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="order_user_recent",
            ),
            pymongo.IndexModel([("status", pymongo.ASCENDING)], name="order_status"),
        ]


class WebhookEvent(TimestampedDocument):
    """Replay guard. Razorpay retries until it gets a 2xx, so the same event
    arrives more than once and must only ever be acted on once."""

    event_id: str
    event: str
    payload: dict = Field(default_factory=dict)
    processed_at: datetime | None = None
    result: str | None = None

    class Settings:
        name = "webhook_events"
        indexes = [
            pymongo.IndexModel(
                [("event_id", pymongo.ASCENDING)], name="webhook_event_unique", unique=True
            ),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)], name="webhook_recent"),
        ]
