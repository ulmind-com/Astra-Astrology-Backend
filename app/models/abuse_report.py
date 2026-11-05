"""Abuse & Misconduct incident reports logged by astrologers."""

from datetime import datetime
import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument


class AbuseReport(TimestampedDocument):
    """An incident report logged when an astrologer flags a client for misconduct or abuse."""

    astrologer_id: PydanticObjectId
    astrologer_user_id: PydanticObjectId
    client_user_id: PydanticObjectId
    appointment_id: PydanticObjectId | None = None
    call_id: PydanticObjectId | None = None

    reason: str = Field(max_length=200)
    notes: str | None = Field(default=None, max_length=2000)

    action_taken: str = Field(default="blacklisted", max_length=50)  # "blacklisted", "flagged_only"
    status: str = Field(default="pending", max_length=50)  # "pending", "reviewed", "resolved", "dismissed"

    reviewed_by: PydanticObjectId | None = None
    reviewed_at: datetime | None = None
    admin_notes: str | None = Field(default=None, max_length=2000)

    class Settings(TimestampedDocument.Settings):
        name = "abuse_reports"
        indexes = [
            pymongo.IndexModel([("astrologer_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("client_user_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("status", pymongo.ASCENDING)]),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)]),
        ]

