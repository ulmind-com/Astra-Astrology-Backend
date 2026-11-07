"""Appointment request and response shapes."""

from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AppointmentStatus


# ------------------------------------------------- the astrologer's calendar
class WindowInput(BaseModel):
    """One stretch of a day the astrologer will take bookings in."""

    starts_at: datetime
    ends_at: datetime
    day: date_type | None = None
    timezone: str | None = None
    is_tatkal: bool = False
    tatkal_multiplier: float = 1.5
    tatkal_fixed_paise: int | None = None
    custom_title: str | None = None
    is_private: bool = False


class WindowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    day: date_type
    starts_at: datetime
    ends_at: datetime
    is_tatkal: bool = False
    tatkal_multiplier: float = 1.5
    tatkal_fixed_paise: int | None = None
    custom_title: str | None = None
    is_private: bool = False


class AppointmentCardUpdate(BaseModel):
    """What the astrologer charges, quoted per block."""

    enabled: bool | None = None
    price_paise: int | None = Field(default=None, ge=0, le=100_000_00)
    block_minutes: int | None = Field(default=None, ge=5, le=600)
    cancellation_window_minutes: int | None = Field(default=None, ge=0, le=1440)
    buffer_minutes: int | None = Field(default=None, ge=0, le=60)
    follow_up_enabled: bool | None = None
    follow_up_window_days: int | None = Field(default=None, ge=1, le=30)
    follow_up_max_messages: int | None = Field(default=None, ge=1, le=20)
    tatkal_enabled: bool | None = None
    tatkal_default_multiplier: float | None = Field(default=None, ge=1.0, le=5.0)


class AppointmentCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    price_paise: int
    block_minutes: int
    cancellation_window_minutes: int = 30
    buffer_minutes: int = 10
    follow_up_enabled: bool = True
    follow_up_window_days: int = 7
    follow_up_max_messages: int = 3
    tatkal_enabled: bool = True
    tatkal_default_multiplier: float = 1.5


# ------------------------------------------------------------- what is free
class Range(BaseModel):
    starts_at: datetime
    ends_at: datetime
    is_tatkal: bool = False
    tatkal_multiplier: float = 1.5
    tatkal_fixed_paise: int | None = None
    custom_title: str | None = None
    is_private: bool = False


class DayView(BaseModel):
    """Open hours and what is already gone, so a chooser can see both."""

    windows: list[Range]
    booked: list[Range]
    slot_minutes: int
    min_minutes: int
    max_minutes: int
    muhurat_ratings: dict[str, dict] | None = None


# ------------------------------------------------------------------ booking
class BookRequest(BaseModel):
    astrologer_id: str
    starts_at: datetime
    minutes: int = Field(ge=5, le=600)
    note: str | None = Field(default=None, max_length=1000)
    consultation_pillar: str | None = Field(default=None, max_length=50)
    kundli_id: str | None = None
    birth_details: dict | None = None
    invite_code: str | None = None
    invite_passcode: str | None = None


class QuoteRequest(BaseModel):
    astrologer_id: str
    minutes: int = Field(ge=5, le=600)
    starts_at: datetime | None = None
    invite_code: str | None = None
    invite_passcode: str | None = None


class AppointmentQuote(BaseModel):
    """What a booking of this length would cost, before committing to it."""

    minutes: int
    price_paise: int
    commission_percent: float
    deposit_paise: int
    deposit_coins: int
    balance_due_paise: int
    balance_due_coins: int = 0
    total_coins: int = 0
    # Available wallet balance that can be used for booking
    available_coins: int = 0
    # Total wallet balance
    balance_coins: int
    # True only if user's available_coins >= total_coins needed for the consultation
    can_afford: bool
    is_tatkal: bool = False
    tatkal_multiplier: float = 1.0
    tatkal_premium_paise: int = 0
    tatkal_premium_coins: int = 0
    is_private: bool = False


class AppointmentPeer(BaseModel):
    id: str | None = None
    name: str | None = None
    avatar_url: str | None = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: AppointmentStatus
    starts_at: datetime
    ends_at: datetime
    minutes: int

    price_paise: int
    commission_percent: float
    deposit_paise: int
    deposit_coins: int
    balance_due_paise: int
    balance_due_coins: int = 0
    held_coins: int = 0
    held_status: str = "none"

    cancellation_window_minutes: int = 30
    cancel_deadline: datetime | None = None
    can_cancel: bool = False
    completed_at: datetime | None = None

    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
    user_note: str | None = None

    consultation_pillar: str | None = None
    kundli_id: str | None = None
    birth_details: dict | None = None
    prescription: dict | None = None
    muhurat_type: str | None = None
    preflight_dossier: dict | None = None
    cosmic_synergy_score: int | None = None
    certificate_data: dict | None = None

    rescheduled_count: int = 0
    rescheduled_at: datetime | None = None
    previous_starts_at: datetime | None = None
    reschedule_reason: str | None = None
    is_no_show: bool = False
    no_show_marked_at: datetime | None = None
    call_session_id: str | None = None

    # Brahma Pause Seeker Auto-Rescue Engine
    brahma_pause_affected: bool = False
    brahma_pause_reason: str | None = None
    brahma_pause_until: datetime | None = None
    rescue_deadline: datetime | None = None

    # Client Screening & Abuse Shield
    abuse_flagged: bool = False
    abuse_reason: str | None = None
    abuse_flagged_at: datetime | None = None

    # Birth Time Rectification (BTR) Authority
    btr_requested: bool = False
    btr_request_note: str | None = None
    btr_requested_at: datetime | None = None
    btr_fulfilled: bool = False
    btr_updated_at: datetime | None = None

    # In-Chamber Consultation Extension
    extension_offered: bool = False
    extension_offered_minutes: int | None = None
    extension_cost_coins: int = 0
    extension_cost_paise: int = 0
    extension_offered_at: datetime | None = None
    extension_status: str = "none"
    extension_total_extended_minutes: int = 0

    # Complimentary Follow-up Pass
    follow_up_pass_enabled: bool = False
    follow_up_window_days: int = 7
    follow_up_expires_at: datetime | None = None
    follow_up_max_messages: int = 3
    follow_up_messages_used: int = 0
    follow_up_granted_at: datetime | None = None
    follow_up_notes: str | None = None
    follow_up_thread: list[dict] = Field(default_factory=list)

    # VIP Tatkal & Private Invite Link Authority
    is_tatkal: bool = False
    tatkal_multiplier: float | None = None
    tatkal_premium_paise: int = 0
    tatkal_premium_coins: int = 0
    is_private: bool = False
    invite_code: str | None = None

    # Private Astrological Dossier / Vault (Strictly Astrologer & Admin view only)
    astrologer_private_notes: str | None = None
    astrologer_private_notes_updated_at: datetime | None = None

    peer: AppointmentPeer | None = None


class CancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=300)


class RescheduleRequest(BaseModel):
    new_starts_at: datetime
    reason: str | None = Field(default=None, max_length=500)


class NoShowRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class BrahmaPauseRequest(BaseModel):
    duration_hours: int = Field(default=3, ge=1, le=48)
    reason: str | None = Field(default=None, max_length=200)


class BrahmaPauseActionRequest(BaseModel):
    action: str = Field(description="'reschedule' or 'refund'")
    new_starts_at: datetime | None = None
    reason: str | None = None


class PrescriptionUpdateRequest(BaseModel):
    gemstone: str | None = Field(default=None, max_length=200)
    rudraksha: str | None = Field(default=None, max_length=200)
    mantra: str | None = Field(default=None, max_length=500)
    mantra_count: int | None = Field(default=108, ge=1)
    daan_remedy: str | None = Field(default=None, max_length=300)
    astrologer_notes: str | None = Field(default=None, max_length=2000)


class RedFlagRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=150)
    notes: str | None = Field(default=None, max_length=1000)
    blacklist_client: bool = True
    terminate_call: bool = True


class RequestBTRRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class UpdateBTRRequest(BaseModel):
    birth_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    birth_time: str = Field(min_length=4, max_length=15)
    birth_place: str = Field(min_length=2, max_length=150)
    latitude: float | None = None
    longitude: float | None = None
    timezone_offset: float | None = None
    notes: str | None = Field(default=None, max_length=500)


class BlacklistedClientOut(BaseModel):
    user_id: str
    name: str
    email_masked: str | None = None
    phone_masked: str | None = None
    avatar_url: str | None = None
    blacklisted_at: datetime | None = None
    last_reason: str | None = None
    notes: str | None = None
    total_reports: int = 1


class AbuseReportOut(BaseModel):
    id: str
    astrologer_id: str
    astrologer_name: str | None = None
    client_user_id: str
    client_name: str | None = None
    appointment_id: str | None = None
    reason: str
    notes: str | None = None
    action_taken: str
    status: str
    created_at: datetime


class OfferExtensionRequest(BaseModel):
    extra_minutes: int = Field(default=10, ge=5, le=30)


class ExtensionActionRequest(BaseModel):
    action: str = Field(description="'accept' or 'decline'")


class IssueFollowUpPassRequest(BaseModel):
    window_days: int = Field(default=7, ge=1, le=30)
    max_messages: int = Field(default=3, ge=1, le=20)
    notes: str | None = Field(default=None, max_length=500)


class SendFollowUpMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


# ------------------------------------------------------------- VIP & Private Links
class CreatePrivateInviteLinkRequest(BaseModel):
    title: str = Field(default="VIP Private Consultation", min_length=2, max_length=100)
    client_name: str | None = Field(default=None, max_length=100)
    client_email: str | None = Field(default=None, max_length=150)
    passcode: str | None = Field(default=None, max_length=50)
    custom_price_paise: int | None = Field(default=None, ge=0, le=100_000_00)
    discount_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    is_tatkal: bool = False
    max_uses: int = Field(default=1, ge=1, le=1000)
    expires_in_hours: int | None = Field(default=48, ge=1, le=8760)
    notes: str | None = Field(default=None, max_length=500)


class PrivateInviteLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    astrologer_id: str
    invite_code: str
    title: str
    client_name: str | None = None
    client_email: str | None = None
    has_passcode: bool = False
    custom_price_paise: int | None = None
    discount_percent: float | None = None
    is_tatkal: bool = False
    max_uses: int = 1
    uses_count: int = 0
    expires_at: datetime | None = None
    is_active: bool = True
    created_at: datetime
    notes: str | None = None


class ValidatePrivateInviteResponse(BaseModel):
    invite_code: str
    title: str
    astrologer_id: str
    astrologer_name: str
    astrologer_avatar: str | None = None
    astrologer_slug: str | None = None
    has_passcode: bool = False
    is_active: bool = True
    is_expired: bool = False
    custom_price_paise: int | None = None
    discount_percent: float | None = None
    is_tatkal: bool = False
    standard_price_paise: int
    block_minutes: int


class VerifyPasscodeRequest(BaseModel):
    passcode: str


class QuickTatkalWindowRequest(BaseModel):
    starts_at: datetime
    minutes: int = Field(default=30, ge=15, le=180)
    multiplier: float = Field(default=1.5, ge=1.0, le=5.0)
    fixed_paise: int | None = Field(default=None, ge=0, le=100_000_00)
    custom_title: str | None = Field(default="VIP Emergency Tatkal Slot", max_length=100)
    is_private: bool = False


# ------------------------------------------------------------- Private Vault Notes
class UpdatePrivateNotesRequest(BaseModel):
    notes: str = Field(default="", max_length=5000)



