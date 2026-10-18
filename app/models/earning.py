"""What an astrologer has earned.

Kept apart from the wallet on purpose. A user's wallet holds coins they spend;
an astrologer is owed **money** they withdraw. Putting earnings in a coin wallet
would invite an astrologer to spend their income on consultations, and would
make a payout a transfer between two things that are not the same kind.

Append-only, like the ledger it sits beside: one row per minute charged.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument
from app.models.enums import ConsultationMode


class EarningEntry(TimestampedDocument):
    astrologer_id: PydanticObjectId
    astrologer_user_id: PydanticObjectId
    user_id: PydanticObjectId

    mode: ConsultationMode
    session_id: PydanticObjectId
    # Which minute of the session this paid for, so a row is traceable.
    minute_index: int = Field(ge=1)

    # What the user was charged, and what that was worth in money at the time.
    coins_charged: int = Field(gt=0)
    gross_paise: int = Field(ge=0)

    commission_percent: float = Field(ge=0, le=100)
    commission_paise: int = Field(ge=0)
    # What the astrologer actually earned. The only figure they are shown.
    earning_paise: int = Field(ge=0)

    class Settings:
        name = "earnings"
        indexes = [
            # The earnings screen: this astrologer, newest first, over a window.
            pymongo.IndexModel(
                [
                    ("astrologer_user_id", pymongo.ASCENDING),
                    ("created_at", pymongo.DESCENDING),
                ],
                name="earning_astrologer_recent",
            ),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)], name="earning_recent"),
            pymongo.IndexModel([("session_id", pymongo.ASCENDING)], name="earning_session"),
        ]
