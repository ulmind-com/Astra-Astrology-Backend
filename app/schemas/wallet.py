"""Wallet request and response shapes.

Amounts cross the wire as integer paise, with a rupee mirror on responses so
the UI never does the division (and never does it differently in two places).
"""

from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.models.enums import (
    PaymentOrderStatus,
    TransactionDirection,
    TransactionReason,
)


class WalletBalance(BaseModel):
    balance_paise: int
    currency: str
    is_frozen: bool
    frozen_reason: str | None = None
    last_transaction_at: datetime | None = None

    @computed_field
    @property
    def balance_rupees(self) -> float:
        return self.balance_paise / 100


class TransactionRefOut(BaseModel):
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_refund_id: str | None = None
    session_id: str | None = None


class TransactionOut(BaseModel):
    id: str
    direction: TransactionDirection
    reason: TransactionReason
    amount_paise: int
    balance_after_paise: int
    currency: str
    note: str | None = None
    ref: TransactionRefOut = Field(default_factory=TransactionRefOut)
    created_at: datetime

    @computed_field
    @property
    def amount_rupees(self) -> float:
        return self.amount_paise / 100


class WalletSummary(BaseModel):
    """What the wallet screen needs in one call."""

    wallet: WalletBalance
    recent: list[TransactionOut]


class RechargePack(BaseModel):
    amount_paise: int
    amount_rupees: int


class RechargeOptions(BaseModel):
    packs: list[RechargePack]
    min_paise: int
    max_paise: int
    currency: str
    # Public by design — it identifies the merchant in Razorpay Checkout.
    key_id: str
    enabled: bool


class CreateOrderRequest(BaseModel):
    amount_paise: int = Field(gt=0, description="Amount in paise. ₹500 is 50000.")


class CreateOrderResponse(BaseModel):
    razorpay_order_id: str
    amount_paise: int
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
    balance_paise: int


class PaymentOrderOut(BaseModel):
    id: str
    user_id: str
    razorpay_order_id: str
    razorpay_payment_id: str | None = None
    receipt: str
    amount_paise: int
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
    balance_paise: int
    currency: str
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
    amount_paise: int = Field(gt=0)
    # Required: a manual money movement with no stated reason is unauditable.
    reason: str = Field(min_length=3, max_length=300)


class FreezeWalletRequest(BaseModel):
    frozen: bool
    reason: str | None = Field(default=None, max_length=300)


class ReconcileResult(BaseModel):
    credited_paise: int
    debited_paise: int
    ledger_balance_paise: int
    drift_paise: int
