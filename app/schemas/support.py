"""Pydantic schemas for contact support and ticket management."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field


class SupportTicketCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    category: str = Field(
        default="general",
        description="wallet_billing, consultation, readings, account, technical, general",
    )
    subject: str = Field(..., min_length=3, max_length=250)
    message: str = Field(..., min_length=10, max_length=5000)
    priority: str = Field(default="medium", description="low, medium, high, urgent")
    source: str = Field(default="mobile", description="mobile, web, admin")
    device_info: dict[str, Any] | None = None


class SupportTicketOut(BaseModel):
    id: str
    ticket_number: str
    user_id: str | None = None
    name: str
    email: str
    phone: str | None = None
    category: str
    subject: str
    message: str
    priority: str
    status: str
    source: str
    device_info: dict[str, Any] | None = None
    admin_notes: str | None = None
    admin_id: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SupportTicketUpdateAdmin(BaseModel):
    status: str | None = Field(default=None, description="open, in_progress, resolved, closed")
    priority: str | None = Field(default=None, description="low, medium, high, urgent")
    admin_notes: str | None = Field(default=None, max_length=5000)


class SupportTicketStats(BaseModel):
    total: int = 0
    open: int = 0
    in_progress: int = 0
    resolved: int = 0
    closed: int = 0

