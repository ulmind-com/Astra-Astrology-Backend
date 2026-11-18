"""Schemas for Purohit profile, personal puja catalog, and live puja booking."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.config import settings
from app.models.enums import PujaBookingStatus, PujaPaymentStatus


class PurohitPujaItemCreate(BaseModel):
    puja_name: str = Field(..., min_length=2, max_length=150, description="Name of the Puja, e.g. Lakshmi Puja")
    description: str = Field(default="", max_length=1000, description="Puja spiritual significance and procedure")
    duration_minutes: int = Field(default=45, ge=10, le=480, description="Estimated duration in minutes")
    price_inr: float = Field(default=100.0, ge=1.0, description="Dakshina / Fee for this Puja in INR")
    samagri_notes: str | None = Field(default=None, max_length=1500, description="Items devotee should arrange at home")
    is_active: bool = True


class PurohitPujaItemUpdate(BaseModel):
    puja_name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int | None = Field(default=None, ge=10, le=480)
    price_inr: float | None = Field(default=None, ge=1.0)
    samagri_notes: str | None = None
    is_active: bool | None = None


class PurohitPujaItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    puja_name: str
    description: str
    duration_minutes: int
    price_inr: float
    samagri_notes: str | None = None
    is_active: bool
    created_at: datetime


class PurohitCreate(BaseModel):
    """Admin payload to onboard a new verified Purohit."""

    first_name: str = Field(..., min_length=1, max_length=50)
    middle_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)
    display_name: str | None = Field(default=None, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    title: str = Field(default="Vedic Acharya", max_length=100)
    bio: str | None = Field(default=None, max_length=2500)
    avatar_url: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    experience_years: int = Field(default=5, ge=0, le=70)
    languages: list[str] = Field(default_factory=lambda: ["Bengali", "Sanskrit"])


class PurohitUpdate(BaseModel):
    display_name: str | None = None
    title: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    experience_years: int | None = None
    languages: list[str] | None = None


class PurohitAvailabilityUpdate(BaseModel):
    """Purohit dashboard toggle to switch online/offline availability for live pujas."""

    is_online: bool


class PurohitOut(BaseModel):
    """Publicly visible Purohit profile for devotees."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    display_name: str
    slug: str
    title: str
    bio: str | None = None
    avatar_url: str | None = None
    city: str | None = None
    state: str | None = None
    experience_years: int
    languages: list[str]
    is_online: bool
    is_verified: bool
    pujas: list[PurohitPujaItemOut] = []
    rating: float
    total_pujas_performed: int
    starting_price_inr: float = 100.0


class PurohitAdminOut(PurohitOut):
    """Admin view of Purohit with contact details."""

    phone: str
    email: str
    address: str | None = None
    pincode: str | None = None
    created_at: datetime


class PujaBookingCreate(BaseModel):
    """Devotee payload to book an online puja with a Purohit."""

    purohit_id: str
    puja_item_id: str
    sankalpa_name: str = Field(..., min_length=2, max_length=100, description="Name for Vedic Sankalpa")
    sankalpa_gotra: str = Field(default="Kashyapa", min_length=2, max_length=50)
    sankalpa_wish: str | None = Field(default=None, max_length=500, description="Special prayer wish or reason for puja")


class PujaBookingOut(BaseModel):
    """Booking details returned to devotee and purohit, including video room access."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_number: str
    user_id: str
    user_name: str
    user_phone: str
    purohit_id: str
    purohit_name: str
    puja_item_id: str
    puja_name: str
    puja_duration_minutes: int
    amount_inr: float
    sankalpa_name: str
    sankalpa_gotra: str
    sankalpa_wish: str | None = None
    room_id: str
    zego_app_id: int = Field(default_factory=lambda: settings.ZEGOCLOUD_APP_ID)
    zego_token: str | None = None
    status: PujaBookingStatus
    payment_status: PujaPaymentStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
