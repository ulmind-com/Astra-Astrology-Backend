"""Beanie document registry — every model listed here is registered on startup."""

from beanie import Document

from app.models.astrologer import Astrologer
from app.models.call import CallSession, ZegoCallbackEvent
from app.models.chat import ChatSession
from app.models.otp import OtpCode
from app.models.pending_registration import PendingRegistration
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
    ChatSession,
]

__all__ = [
    "DOCUMENT_MODELS",
    "Astrologer",
    "CallSession",
    "ChatSession",
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
