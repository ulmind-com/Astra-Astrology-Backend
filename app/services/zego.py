"""ZEGOCLOUD room tokens.

A client cannot join a call room without a token signed with our ServerSecret,
and that secret never leaves this server — ZEGOCLOUD's own guidance is that a
production app must not mint tokens in the browser, because anyone who has the
secret can join any room on the account.

The format is ZEGOCLOUD's Token04, ported from their official Python sample onto
`cryptography` (already a dependency) rather than pulling in pycryptodome:

    "04" + base64( expire(8) | iv_len(2) | iv(16) | cipher_len(2) | cipher )

where `cipher` is the JSON claim set encrypted AES-256-CBC with the 32-byte
ServerSecret as key.
"""

import base64
import json
import os
import secrets
import struct
import time
from typing import Any

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from loguru import logger

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

# Privilege keys as ZEGOCLOUD defines them.
PRIVILEGE_LOGIN_ROOM = 1
PRIVILEGE_PUBLISH_STREAM = 2

_IV_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def is_enabled() -> bool:
    return settings.zego_configured


def _require_config() -> None:
    if not is_enabled():
        raise ServiceUnavailableError(
            "Calling is not configured yet. Please try again later.",
            error_code="calls_unavailable",
        )


def _random_iv() -> str:
    """16 ASCII characters, matching ZEGOCLOUD's own sample.

    The IV goes into the token in the clear, so it only has to be unique per
    token, not secret — but it is drawn from `secrets` rather than `random`
    anyway, since this sits next to a signing key.
    """
    return "".join(secrets.choice(_IV_ALPHABET) for _ in range(16))


def _encrypt(plaintext: str, key: str, iv: str) -> bytes:
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded = padder.update(plaintext.encode()) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key.encode()), modes.CBC(iv.encode())).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def generate_token(
    *,
    user_id: str,
    room_id: str,
    can_publish: bool = True,
    ttl_seconds: int | None = None,
) -> str:
    """Mints a room token for one user joining one room."""
    _require_config()

    ttl = ttl_seconds or settings.ZEGO_TOKEN_TTL_SECONDS
    created = int(time.time())
    expires = created + ttl

    payload = {
        "room_id": room_id,
        "privilege": {
            PRIVILEGE_LOGIN_ROOM: 1,
            PRIVILEGE_PUBLISH_STREAM: 1 if can_publish else 0,
        },
        # None means any stream id. Pinning the list buys nothing here because
        # the room id is already scoped to this one call.
        "stream_id_list": None,
    }

    claims = {
        "app_id": settings.ZEGO_APP_ID,
        "user_id": user_id,
        # 31 bits, as the reference implementation uses.
        "nonce": int.from_bytes(os.urandom(4), "big") >> 1,
        "ctime": created,
        "expire": expires,
        "payload": json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
    }
    plaintext = json.dumps(claims, separators=(",", ":"), ensure_ascii=False)

    iv = _random_iv()
    cipher = _encrypt(plaintext, settings.ZEGO_SERVER_SECRET, iv)

    packed = (
        struct.pack("!q", expires)
        + struct.pack("!h", len(iv))
        + iv.encode()
        + struct.pack("!h", len(cipher))
        + cipher
    )
    return "04" + base64.b64encode(packed).decode()


def decode_token(token: str) -> dict[str, Any]:
    """Reads a token back. Used by the tests, and when a token looks wrong."""
    raw = base64.b64decode(token[2:])
    expires = struct.unpack("!q", raw[0:8])[0]
    iv_len = struct.unpack("!h", raw[8:10])[0]
    iv = raw[10 : 10 + iv_len]
    cipher_len = struct.unpack("!h", raw[10 + iv_len : 12 + iv_len])[0]
    cipher = raw[12 + iv_len : 12 + iv_len + cipher_len]

    decryptor = Cipher(
        algorithms.AES(settings.ZEGO_SERVER_SECRET.encode()), modes.CBC(iv)
    ).decryptor()
    padded = decryptor.update(cipher) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    claims = json.loads((unpadder.update(padded) + unpadder.finalize()).decode())
    claims["payload"] = json.loads(claims["payload"])
    claims["_expire_header"] = expires
    return claims


def verify_callback_signature(
    *, signature: str | None, nonce: str | None, timestamp: str | None
) -> None:
    """Checks a room callback really came from ZEGOCLOUD.

    ZEGOCLOUD signs with md5(AppSecret + Nonce + Timestamp). Without the secret
    configured the callback cannot be trusted at all, so it is refused rather
    than acted on.
    """
    import hashlib
    import hmac as hmac_mod

    from app.core.exceptions import UnauthorizedError

    if not settings.ZEGO_CALLBACK_SECRET:
        logger.error("ZEGOCLOUD callback received but ZEGO_CALLBACK_SECRET is not set.")
        raise UnauthorizedError(
            "Callbacks are not configured.", error_code="callback_not_configured"
        )
    if not (signature and nonce and timestamp):
        raise UnauthorizedError("Missing signature.", error_code="missing_signature")

    expected = hashlib.md5(
        f"{settings.ZEGO_CALLBACK_SECRET}{nonce}{timestamp}".encode()
    ).hexdigest()
    if not hmac_mod.compare_digest(expected, signature):
        logger.warning("Rejected a ZEGOCLOUD callback with a bad signature.")
        raise UnauthorizedError("Invalid signature.", error_code="invalid_signature")
