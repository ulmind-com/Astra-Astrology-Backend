"""Wallet request and response shapes.

Balances are in **coins**. Rupees appear only where money actually changed
hands — on a recharge row and on a payment order — because once an admin can
change the coin rate there is no single rupee value for a coin balance, and
printing one would be a lie.
"""

from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.models.enums import (
    ConsultationMode,
    PaymentOrderStatus,
    TransactionDirection,
    TransactionReason,
)


class WalletBalance(BaseModel):
    balance_coins: int
    is_frozen: bool
    frozen_reason: str | None = None
    last_transaction_at: datetime | None = None


class TransactionRefOut(BaseModel):
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_refund_id: str | None = None
    session_id: str | None = None


class TransactionOut(BaseModel):
    id: str
    direction: TransactionDirection
    reason: TransactionReason
    amount_coins: int
    balance_after_coins: int
    note: str | None = None
    # Set only on rows where money moved, so a statement can still show what
    # was paid and the rate that was honoured at the time.
    amount_paise: int | None = None
    coins_per_rupee: int | None = None
    ref: TransactionRefOut = Field(default_factory=TransactionRefOut)
    created_at: datetime


class WalletSummary(BaseModel):
    """What the wallet screen needs in one call."""

    wallet: WalletBalance
    recent: list[TransactionOut]


class RechargePack(BaseModel):
    amount_paise: int
    amount_rupees: int
    coins: int


class RechargeOptions(BaseModel):
    packs: list[RechargePack]
    min_paise: int
    max_paise: int
    currency: str
    coins_per_rupee: int
    # Public by design — it identifies the merchant in Razorpay Checkout.
    key_id: str
    enabled: bool


class CreateOrderRequest(BaseModel):
    amount_paise: int = Field(gt=0, description="Amount in paise. ₹500 is 50000.")


class CreateOrderResponse(BaseModel):
    razorpay_order_id: str
    amount_paise: int
    # What the user is promised before paying, and what will be credited even
    # if the rate changes while the checkout window is open.
    coins: int
    coins_per_rupee: int
    currency: str
    key_id: str
    receipt: str
    # Prefilled into Razorpay Checkout.
    name: str
    email: str
    contact: str | None = None


class VerifyPaymentRequest(BaseModel):
    """Exactly the three fields Razorpay Checkout hands back."""

    razorpay_order_id: str = Field(min_length=4, max_length=64)
    razorpay_payment_id: str = Field(min_length=4, max_length=64)
    razorpay_signature: str = Field(min_length=16, max_length=256)


class VerifyPaymentResponse(BaseModel):
    status: PaymentOrderStatus
    credited: bool
    amount_paise: int
    coins: int
    balance_coins: int


class PaymentOrderOut(BaseModel):
    id: str
    user_id: str
    razorpay_order_id: str
    razorpay_payment_id: str | None = None
    receipt: str
    amount_paise: int
    coins: int
    coins_per_rupee: int
    currency: str
    status: PaymentOrderStatus
    method: str | None = None
    failure_reason: str | None = None
    verified_via: str | None = None
    paid_at: datetime | None = None
    created_at: datetime


# ------------------------------------------------------------------- admin


class AdminWalletOut(BaseModel):
    user_id: str
    name: str
    email: str
    balance_coins: int
    is_frozen: bool
    frozen_reason: str | None = None
    last_transaction_at: datetime | None = None
    created_at: datetime


class AdminTransactionOut(TransactionOut):
    user_id: str
    user_email: str | None = None
    created_by: str | None = None


class AdjustWalletRequest(BaseModel):
    direction: TransactionDirection
    amount_coins: int = Field(gt=0)
    # Required: a manual money movement with no stated reason is unauditable.
    reason: str = Field(min_length=3, max_length=300)


class FreezeWalletRequest(BaseModel):
    frozen: bool
    reason: str | None = Field(default=None, max_length=300)


class ReconcileResult(BaseModel):
    credited_coins: int
    debited_coins: int
    ledger_balance_coins: int
    drift_coins: int


# ---------------------------------------------------------------- settings
class PlatformSettingsOut(BaseModel):
    coins_per_rupee: int
    min_recharge_paise: int
    max_recharge_paise: int

    default_chat_coins_per_minute: int
    default_call_coins_per_minute: int
    default_video_coins_per_minute: int
    default_commission_percent: float

    min_session_minutes: int
    max_session_minutes: int

    updated_at: datetime


class ConsultationDefaultsUpdate(BaseModel):
    """Any field may be sent on its own; the rest keep their value."""

    default_chat_coins_per_minute: int | None = Field(default=None, ge=1, le=100_000)
    default_call_coins_per_minute: int | None = Field(default=None, ge=1, le=100_000)
    default_video_coins_per_minute: int | None = Field(default=None, ge=1, le=100_000)
    default_commission_percent: float | None = Field(default=None, ge=0, le=100)
    min_session_minutes: int | None = Field(default=None, ge=1, le=600)
    max_session_minutes: int | None = Field(default=None, ge=1, le=600)


class CoinRateUpdate(BaseModel):
    coins_per_rupee: int = Field(
        ge=1,
        le=10_000,
        description="How many coins one rupee buys. A whole number, so a "
        "whole-rupee recharge can never produce a fractional coin.",
    )
    note: str | None = Field(default=None, max_length=300)


class RechargeLimitsUpdate(BaseModel):
    """Either may be sent on its own; the other keeps its current value."""

    min_recharge_paise: int | None = Field(default=None, ge=100)
    max_recharge_paise: int | None = Field(default=None, ge=100)


class CoinRateChangeOut(BaseModel):
    from_rate: int
    to_rate: int
    changed_by: str | None = None
    changed_by_email: str | None = None
    note: str | None = None
    created_at: datetime


# ------------------------------------------------------------- consultation
class ConsultationQuote(BaseModel):
    """What a session with this astrologer costs me, right now."""

    mode: ConsultationMode
    coins_per_minute: int
    balance_coins: int
    affordable_minutes: int
    min_minutes: int
    max_minutes: int
    # What the longest affordable booking would cost, for the picker.
    currency: str = "INR"


class EarningsBucket(BaseModel):
    earning_paise: int
    minutes: int
    sessions: int


class EarningsSummary(BaseModel):
    """An astrologer sees money, never the commission that was taken."""

    today: EarningsBucket
    this_week: EarningsBucket
    this_month: EarningsBucket
    all_time: EarningsBucket


class EarningRow(BaseModel):
    """One consultation, not one minute."""

    id: str
    mode: ConsultationMode
    minutes: int
    earning_paise: int
    created_at: datetime


class AdminEarningRow(EarningRow):
    """The admin sees the whole split."""

    astrologer_id: str
    astrologer_name: str | None = None
    coins_charged: int
    gross_paise: int
    commission_percent: float
    commission_paise: int


class AdminEarningsSummary(BaseModel):
    gross_paise: int
    commission_paise: int
    payout_paise: int
    coins_charged: int
    sessions: int
