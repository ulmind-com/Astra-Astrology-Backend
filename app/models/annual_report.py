"""Model for persisting and cryptographically verifying 1-Year Annual Horoscope & Lal Kitab Varshphal Reports.

Records are created when a seeker generates an Annual Horoscope Report.
Each record carries a unique report_id, target year, seeker details, cryptographic digital seal,
and overall cosmic resilience score.
"""

from __future__ import annotations

from typing import Any
import pymongo
from pydantic import Field

from app.models.base import TimestampedDocument


class AnnualReportRecord(TimestampedDocument):
    """Immutable audit record for 1-Year Lal Kitab Varshphal Report and Consecrated Seal."""

    report_id: str = Field(..., index=True, unique=True)
    user_id: str | None = Field(default=None, index=True)
    client_name: str = "Seeker"
    date_of_birth: str
    time_of_birth: str
    city_name: str
    target_year: int = Field(..., index=True)
    language: str = "en"
    natal_lagna: str | None = None
    moon_rashi: str | None = None
    varshphal_lagna: str | None = None
    overall_score: int = 75
    consecration_date: str | None = None
    digital_seal: dict[str, Any] = Field(default_factory=dict)
    summary_text: str = ""
    curated_remedies_count: int = 0
    is_valid: bool = True

    class Settings:
        name = "annual_reports"
        indexes = [
            pymongo.IndexModel([("report_id", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)]),
            pymongo.IndexModel([("target_year", pymongo.ASCENDING)]),
        ]
