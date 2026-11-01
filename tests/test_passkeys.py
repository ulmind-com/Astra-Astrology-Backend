"""Tests for Passkey models, schemas, and helper functions."""

from app.schemas.passkey import (
    PasskeyAuthenticationOptionsIn,
    PasskeyAuthenticationVerifyIn,
    PasskeyInfoOut,
    PasskeyRegistrationVerifyIn,
)
from app.services.passkey import resolve_rp_info


def test_resolve_rp_info():
    # Test localhost
    origin, rp_id = resolve_rp_info("http://localhost:3000", "localhost:3000")
    assert origin == "http://localhost:3000"
    assert rp_id == "localhost"

    # Test vercel production domain
    origin, rp_id = resolve_rp_info(
        "https://astra-astrology-admin-five.vercel.app/",
        "astra-astrology-admin-five.vercel.app",
    )
    assert origin == "https://astra-astrology-admin-five.vercel.app"
    assert rp_id == "astra-astrology-admin-five.vercel.app"

    # Test custom domain
    origin, rp_id = resolve_rp_info("https://admin.astra.com", "admin.astra.com")
    assert origin == "https://admin.astra.com"
    assert rp_id == "admin.astra.com"


def test_passkey_schemas():
    reg_in = PasskeyRegistrationVerifyIn(
        credential={"id": "test_cred_id", "response": {}},
        device_name="MacBook Touch ID",
    )
    assert reg_in.device_name == "MacBook Touch ID"
    assert reg_in.credential["id"] == "test_cred_id"

    auth_in = PasskeyAuthenticationOptionsIn(email="admin@astra.com")
    assert auth_in.email == "admin@astra.com"
