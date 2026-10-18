"""Shared enums."""

from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ASTROLOGER = "astrologer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class AuthProvider(StrEnum):
    """How an account can be signed in to. A user may have more than one."""

    PASSWORD = "password"
    GOOGLE = "google"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNDISCLOSED = "undisclosed"


class MaritalStatus(StrEnum):
    SINGLE = "single"
    ENGAGED = "engaged"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    UNDISCLOSED = "undisclosed"


class OtpPurpose(StrEnum):
    SIGNUP = "signup"
    LOGIN = "login"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class Skill(StrEnum):
    """Services an astrologer can offer, from the client's spec."""

    VEDIC_ASTROLOGY = "vedic_astrology"
    NUMEROLOGY = "numerology"
    TAROT = "tarot"
    VASTU = "vastu"
    PALMISTRY = "palmistry"
    FACE_READING = "face_reading"
    KP_ASTROLOGY = "kp_astrology"
    LAL_KITAB = "lal_kitab"
    NADI = "nadi"
    PRASHNA = "prashna"
    LOVE_RELATIONSHIP = "love_relationship"
    CAREER_BUSINESS = "career_business"
    FINANCE_WEALTH = "finance_wealth"


class ConsultationMode(StrEnum):
    CHAT = "chat"
    CALL = "call"
    VIDEO = "video"


class OtpChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class TransactionDirection(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionReason(StrEnum):
    """Why money moved. Every future money feature already has its slot here,
    so adding payouts or coupons later needs no schema change."""

    RECHARGE = "recharge"
    CONSULTATION = "consultation"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"  # an admin moved it by hand
    BONUS = "bonus"
    PAYOUT = "payout"
    REVERSAL = "reversal"


class PaymentOrderStatus(StrEnum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"


class CallStatus(StrEnum):
    """Where a call is in its life.

    Every path out of `RINGING` is recorded separately, because "the astrologer
    said no" and "the astrologer never picked up" mean different things to the
    person waiting, and later to whoever is paid.
    """

    RINGING = "ringing"
    ACTIVE = "active"
    ENDED = "ended"
    DECLINED = "declined"  # the astrologer said no
    MISSED = "missed"  # nobody answered before the ring timed out
    CANCELLED = "cancelled"  # the caller hung up first
    FAILED = "failed"


class CallParty(StrEnum):
    USER = "user"
    ASTROLOGER = "astrologer"
    SYSTEM = "system"


class ChatStatus(StrEnum):
    """Where a chat is in its life.

    Mirrors a call's states but with names that read right for a conversation:
    nothing "rings", it waits to be picked up.
    """

    REQUESTED = "requested"
    ACTIVE = "active"
    ENDED = "ended"
    DECLINED = "declined"
    MISSED = "missed"  # the astrologer never picked it up
    CANCELLED = "cancelled"  # the person who asked backed out first
