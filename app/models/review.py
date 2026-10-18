"""What a user thought of a consultation.

One review per session, and only from the person who was in it. Both of those
are enforced by the database rather than by a check in the handler: the unique
index on (kind, session_id) is what makes a second review impossible even if
two requests arrive at once, and the user id is copied in so ownership is not
something a later edit could quietly change.

The astrologer's average is **recomputed from these rows**, never adjusted in
place. An incremental average drifts the moment anything is deleted or a write
is retried, and a rating people choose an astrologer by is not a number worth
letting drift.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument
from app.models.enums import ReviewKind


class Review(TimestampedDocument):
    astrologer_id: PydanticObjectId
    user_id: PydanticObjectId

    # Which consultation this is about. The pair is unique, so the same chat
    # cannot be reviewed twice — and a call and a chat can share an id without
    # colliding.
    kind: ReviewKind
    session_id: PydanticObjectId

    stars: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)

    # The reviewer's name as it was when they wrote it. Copied rather than
    # looked up, so a review does not silently change attribution if they
    # rename themselves later.
    author_name: str | None = Field(default=None, max_length=120)

    # An admin can take a review down without deleting it — the row is still
    # evidence of what was said, but it stops counting and stops showing.
    is_hidden: bool = False
    hidden_reason: str | None = Field(default=None, max_length=300)
    hidden_at: datetime | None = None

    class Settings:
        name = "reviews"
        indexes = [
            pymongo.IndexModel(
                [("kind", pymongo.ASCENDING), ("session_id", pymongo.ASCENDING)],
                name="review_session_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("astrologer_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="review_astrologer_recent",
            ),
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="review_user_recent",
            ),
        ]
