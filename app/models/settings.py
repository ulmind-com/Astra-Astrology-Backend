"""Platform-wide settings an admin can change at runtime.

The coin rate lives here rather than in the environment because the client has
to be able to change it from the panel. It decides how much a person gets for
their money, so every change is recorded with the admin who made it.
"""

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument

SETTINGS_KEY = "platform"


class PlatformSettings(TimestampedDocument):
    """A singleton. The unique index on `key` makes a second row impossible."""

    key: str = SETTINGS_KEY

    # How many coins one rupee buys. An integer, so that a whole-rupee recharge
    # can never produce a fractional coin.
    coins_per_rupee: int = Field(default=1, ge=1, le=10_000)

    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "platform_settings"
        indexes = [
            pymongo.IndexModel(
                [("key", pymongo.ASCENDING)], name="settings_key_unique", unique=True
            ),
        ]


class CoinRateChange(TimestampedDocument):
    """One row per change to the coin rate. Append-only, like the ledger."""

    from_rate: int
    to_rate: int
    changed_by: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=300)

    class Settings:
        name = "coin_rate_changes"
        indexes = [
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)], name="rate_change_recent"),
        ]
