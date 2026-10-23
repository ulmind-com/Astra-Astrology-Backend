"""Beanie document registry — every model listed here is registered on startup."""

from beanie import Document

from app.models.appointment import Appointment, AppointmentSlot, AvailabilityWindow
from app.models.astrologer import Astrologer
from app.models.call import CallSession, ZegoCallbackEvent
from app.models.chat import ChatMessage, ChatRead, ChatSession
from app.models.earning import EarningEntry
from app.models.otp import OtpCode
from app.models.pending_registration import PendingRegistration
from app.models.face_reading import FaceReading, FaceRule
from app.models.palm_reading import PalmReading, PalmRule
from app.models.review import Review
from app.models.settings import CoinRateChange, PlatformSettings
from app.models.user import User
from app.models.wallet import (
    PaymentOrder,
    Wallet,
    WalletTransaction,
    WebhookEvent,
)

DOCUMENT_MODELS: list[type[Document]] = [
    User,
    Astrologer,
    OtpCode,
    PendingRegistration,
    PlatformSettings,
    CoinRateChange,
    Wallet,
    WalletTransaction,
    PaymentOrder,
    WebhookEvent,
    CallSession,
    ZegoCallbackEvent,
    Appointment,
    AppointmentSlot,
    AvailabilityWindow,
    ChatMessage,
    ChatRead,
    ChatSession,
    FaceReading,
    FaceRule,
    PalmReading,
    PalmRule,
    Review,
    EarningEntry,
]

__all__ = [
    "DOCUMENT_MODELS",
    "Astrologer",
    "CallSession",
    "Appointment",
    "AppointmentSlot",
    "AvailabilityWindow",
    "ChatMessage",
    "ChatRead",
    "ChatSession",
    "FaceReading",
    "FaceRule",
    "PalmReading",
    "PalmRule",
    "Review",
    "EarningEntry",
    "CoinRateChange",
    "OtpCode",
    "PaymentOrder",
    "PendingRegistration",
    "PlatformSettings",
    "User",
    "Wallet",
    "WalletTransaction",
    "WebhookEvent",
    "ZegoCallbackEvent",
]
