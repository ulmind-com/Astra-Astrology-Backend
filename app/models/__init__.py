"""Beanie document registry — every model listed here is registered on startup."""

from beanie import Document

from app.models.astrologer import Astrologer
from app.models.otp import OtpCode
from app.models.pending_registration import PendingRegistration
from app.models.user import User

DOCUMENT_MODELS: list[type[Document]] = [
    User,
    Astrologer,
    OtpCode,
    PendingRegistration,
]

__all__ = ["DOCUMENT_MODELS", "Astrologer", "OtpCode", "PendingRegistration", "User"]
