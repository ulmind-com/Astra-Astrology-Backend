"""User favorites for astrologers.

Tracks which client has added which astrologer to their sacred favorites.
The combination of (user_id, astrologer_id) is unique so a client cannot
favorite the same astrologer multiple times.
"""

import pymongo
from beanie import PydanticObjectId

from app.models.base import TimestampedDocument


class AstrologerFavorite(TimestampedDocument):
    user_id: PydanticObjectId
    astrologer_id: PydanticObjectId

    class Settings(TimestampedDocument.Settings):
        name = "astrologer_favorites"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("astrologer_id", pymongo.ASCENDING)],
                name="user_astrologer_favorite_unique",
                unique=True,
            ),
            [("astrologer_id", pymongo.ASCENDING)],
            [("user_id", pymongo.ASCENDING)],
        ]
