"""Astrologer Payouts & Withdrawals.

Represents an astrologer's withdrawal request from their earned balance,
its approval and settlement workflow with transaction references (UTR),
and audit trail.
"""

from datetime import datetime
from enum import StrEnum

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument


class PayoutStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    SETTLED = "settled"
    REJECTED = "rejected"


class PayoutMethod(StrEnum):
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"


class AstrologerPayout(TimestampedDocument):
    astrologer_id: PydanticObjectId
    astrologer_user_id: PydanticObjectId

    amount_paise: int = Field(gt=0)
    tds_percent: float = Field(default=0.0, ge=0, le=100)
    tds_paise: int = Field(default=0, ge=0)
    net_payable_paise: int = Field(gt=0)

    payout_method: PayoutMethod = PayoutMethod.BANK_TRANSFER
    bank_name: str | None = None
    account_holder_name: str | None = None
    account_number_last4: str | None = None
    account_number_masked: str | None = None
    ifsc: str | None = None
    upi_id: str | None = None

    status: PayoutStatus = PayoutStatus.PENDING
    utr_number: str | None = None
    admin_notes: str | None = None
    rejection_reason: str | None = None

    requested_at: datetime
    approved_at: datetime | None = None
    settled_at: datetime | None = None
    settled_by: PydanticObjectId | None = None
    rejected_at: datetime | None = None
    rejected_by: PydanticObjectId | None = None

    class Settings:
        name = "astrologer_payouts"
        indexes = [
            pymongo.IndexModel(
                [("astrologer_user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="payout_astrologer_recent",
            ),
            pymongo.IndexModel(
                [("status", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="payout_status_recent",
            ),
        ]

