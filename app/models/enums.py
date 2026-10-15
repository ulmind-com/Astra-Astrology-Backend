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


class OtpPurpose(StrEnum):
    SIGNUP = "signup"
    LOGIN = "login"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class OtpChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
