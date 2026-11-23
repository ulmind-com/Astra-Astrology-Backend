"""Schemas for the AbuseReport trust & safety admin dashboard."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class AbuseReportOut(BaseModel):
    """Public read shape of a single abuse report (astrologer + admin view)."""

    id: str
    astrologer_id: str
    astrologer_name: Optional[str] = None
    astrologer_email: Optional[str] = None
    client_user_id: str
    client_name: Optional[str] = None
    client_email_masked: Optional[str] = None
    appointment_id: Optional[str] = None
    call_id: Optional[str] = None
    reason: str
    notes: Optional[str] = None
    action_taken: str  # "blacklisted" | "flagged_only"
    status: str  # "pending" | "reviewed" | "resolved" | "dismissed"
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AbuseReportListItem(BaseModel):
    """Compact row for the admin abuse-reports table."""

    id: str
    astrologer_id: str
    astrologer_name: Optional[str] = None
    client_user_id: str
    client_name: Optional[str] = None
    client_email_masked: Optional[str] = None
    reason: str
    action_taken: str
    status: str
    created_at: datetime


class AbuseReportReviewRequest(BaseModel):
    """Admin review decision on a single abuse report."""

    status: str = Field(
        description="'reviewed', 'resolved' or 'dismissed'",
        min_length=1,
        max_length=50,
    )
    admin_notes: Optional[str] = Field(
        default=None,
        description="Admin investigation notes",
        max_length=2000,
    )


class AbuseReportUnblockRequest(BaseModel):
    """Admin request to unblock a client from an astrologer's personal blacklist."""

    client_user_id: str = Field(description="User id of the client to unblock")


class AbuseReportStats(BaseModel):
    """Aggregate safety dashboard metrics."""

    total_reports: int
    pending_reports: int
    reviewed_reports: int
    resolved_reports: int
    dismissed_reports: int
    reports_today: int
    reports_this_week: int
    reports_this_month: int
    top_flagged_clients: list[dict] = Field(default_factory=list)
    top_flagging_astrologers: list[dict] = Field(default_factory=list)
    reports_by_status: dict[str, int] = Field(default_factory=dict)
    reports_by_action: dict[str, int] = Field(default_factory=dict)


class PaginatedAbuseReports(BaseModel):
    items: list[AbuseReportListItem]
    meta: dict

    model_config = ConfigDict(from_attributes=True)
