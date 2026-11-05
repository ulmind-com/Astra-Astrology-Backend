"""Support tickets and client contact requests."""

from datetime import datetime
from typing import Any
import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument


class SupportTicket(TimestampedDocument):
    """A client contact inquiry or support ticket submitted from mobile or web."""

    ticket_number: str = Field(..., max_length=64, description="Human readable unique ticket ID e.g. TK-20261105-ABCD")
    user_id: PydanticObjectId | None = Field(default=None, description="The user account ID if authenticated")
    name: str = Field(..., max_length=150)
    email: str = Field(..., max_length=255)
    phone: str | None = Field(default=None, max_length=50)

    category: str = Field(
        default="general",
        max_length=50,
        description="Category: wallet_billing, consultation, readings, account, technical, general",
    )
    subject: str = Field(..., max_length=250)
    message: str = Field(..., max_length=5000)

    priority: str = Field(
        default="medium",
        max_length=20,
        description="Priority: low, medium, high, urgent",
    )
    status: str = Field(
        default="open",
        max_length=20,
        description="Status: open, in_progress, resolved, closed",
    )
    source: str = Field(
        default="mobile",
        max_length=20,
        description="Platform source: mobile, web, admin",
    )
    device_info: dict[str, Any] | None = Field(default=None)

    admin_notes: str | None = Field(default=None, max_length=5000)
    admin_id: PydanticObjectId | None = Field(default=None, description="Admin handling or resolving the ticket")
    resolved_at: datetime | None = Field(default=None)

    class Settings:
        name = "support_tickets"
        use_state_management = True
        indexes = [
            pymongo.IndexModel([("ticket_number", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("status", pymongo.ASCENDING)]),
            pymongo.IndexModel([("category", pymongo.ASCENDING)]),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)]),
        ]
