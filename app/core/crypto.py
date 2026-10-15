"""Reversible encryption for short-lived secrets.

Only used for the password of a signup that is waiting on its OTP: the password
must reach Firebase in plaintext when the account is finally created, but it
must not sit in the database in plaintext while it waits. The record is
encrypted, short-lived (TTL) and deleted the moment it is used.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.exceptions import BadRequestError


def _fernet() -> Fernet:
    # Fernet needs a 32-byte urlsafe-base64 key; derive one from the app secret.
    digest = hashlib.sha256(f"pending-registration:{settings.SECRET_KEY}".encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Happens if SECRET_KEY changed after the record was written.
        raise BadRequestError(
            "This signup could not be completed. Please start again.",
            error_code="pending_registration_unreadable",
        )
