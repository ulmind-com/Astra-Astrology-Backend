"""Purohit (Vedic Priest) & Online Puja Booking Models."""

import uuid
from datetime import UTC, datetime
from typing import ClassVar

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.astrologer import BankDetails
from app.models.base import TimestampedDocument
from app.models.enums import PujaBookingStatus, PujaPaymentStatus


class PurohitPujaItem(BaseModel):
    """A customizable puja offering within a Purohit's personal price catalog."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    puja_name: str = Field(..., min_length=2, max_length=150)
    description: str = Field(default="", max_length=1000)
    duration_minutes: int = Field(default=45, ge=10, le=480)
    price_inr: float = Field(default=100.0, ge=1.0)
    samagri_notes: str | None = Field(default=None, max_length=1500)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Purohit(TimestampedDocument):
    """The professional Vedic profile of a Purohit."""

    user_id: PydanticObjectId
    display_name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=120)
    title: str = Field(default="Vedic Acharya", max_length=100)
    bio: str | None = Field(default=None, max_length=2500)
    avatar_url: str | None = None
    phone: str = Field(..., max_length=20)
    email: str = Field(..., max_length=150)
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    experience_years: int = Field(default=5, ge=0, le=70)
    languages: list[str] = Field(default_factory=lambda: ["Bengali", "Sanskrit"])
    
    # Toggle availability: when True, devotee can see the Purohit online & available for immediate puja
    is_online: bool = False
    is_verified: bool = True

    # Weekly auspicious days and time slot configurations for Live Puja
    available_days: list[str] = Field(
        default_factory=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    )
    available_slots: list[str] = Field(
        default_factory=lambda: ["brahma_muhurat", "morning", "afternoon", "evening"]
    )
    weekly_schedule: dict[str, list[str]] = Field(default_factory=dict)

    # Purohit's personal customizable puja & price catalog
    pujas: list[PurohitPujaItem] = Field(default_factory=list)

    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    total_pujas_performed: int = Field(default=0, ge=0)
    bank: BankDetails = Field(default_factory=BankDetails)

    class Settings:
        name = "purohits"
        indexes: ClassVar[list] = [
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)], unique=True, name="purohit_user_id_uniq"),
            pymongo.IndexModel([("slug", pymongo.ASCENDING)], unique=True, name="purohit_slug_uniq"),
            pymongo.IndexModel([("is_online", pymongo.ASCENDING), ("is_verified", pymongo.ASCENDING)], name="purohit_avail_idx"),
            pymongo.IndexModel([("city", pymongo.ASCENDING)], name="purohit_city_idx"),
        ]


class PujaBooking(TimestampedDocument):
    """A sacred puja booking between a devotee and a Purohit."""

    booking_number: str = Field(..., max_length=32)
    user_id: PydanticObjectId
    user_name: str
    user_phone: str
    user_email: str

    purohit_id: PydanticObjectId
    purohit_user_id: PydanticObjectId
    purohit_name: str

    puja_item_id: str
    puja_name: str
    puja_duration_minutes: int = 45
    amount_inr: float = 100.0

    # Vedic Sankalpa
    sankalpa_name: str
    sankalpa_gotra: str = "Kashyapa"
    sankalpa_nakshatra: str | None = None
    sankalpa_wish: str | None = None

    # ZEGOCLOUD Video Room ID
    room_id: str

    status: PujaBookingStatus = PujaBookingStatus.CONFIRMED
    payment_status: PujaPaymentStatus = PujaPaymentStatus.PAID
    payment_method: str = "online"

    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None

    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Settings:
        name = "puja_bookings"
        indexes: ClassVar[list] = [
            pymongo.IndexModel([("booking_number", pymongo.ASCENDING)], unique=True, name="puja_booking_num_uniq"),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)], name="puja_user_idx"),
            pymongo.IndexModel([("purohit_id", pymongo.ASCENDING)], name="puja_purohit_idx"),
            pymongo.IndexModel([("purohit_user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)], name="puja_purohit_user_created_idx"),
            pymongo.IndexModel([("status", pymongo.ASCENDING)], name="puja_status_idx"),
            pymongo.IndexModel([("room_id", pymongo.ASCENDING)], name="puja_room_idx"),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)], name="puja_created_idx"),
        ]
