"""Forgot password: email a code, then set a new password with it."""

import json

import pytest
from httpx import AsyncClient

from tests.conftest import FakeFirebase

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


async def register(
    client: AsyncClient, email: str = "ravi@test.dev", password: str = "secret123"
) -> dict:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": password, "first_name": "Ravi"},
    )
    assert started.status_code == 200, started.text
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    assert created.status_code == 201, created.text
    return created.json()["data"]["user"]


async def forgot(client: AsyncClient, email: str):
    return await client.post(f"{P}/auth/password/forgot", json={"email": email})


async def reset(client: AsyncClient, email: str, code: str, new_password: str):
    return await client.post(
        f"{P}/auth/password/reset",
        json={"email": email, "code": code, "new_password": new_password},
    )


async def login(client: AsyncClient, email: str, password: str):
    return await client.post(f"{P}/auth/login", json={"email": email, "password": password})


# --------------------------------------------------------- the happy path
async def test_full_reset_then_sign_in_with_the_new_password(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    created = await register(client, email="ravi@test.dev", password="oldpassword")

    sent = await forgot(client, "ravi@test.dev")
    assert sent.status_code == 200, sent.text
    code = sent.json()["data"]["dev_code"]
    assert sent.json()["data"]["email"] == "ravi@test.dev"

    done = await reset(client, "ravi@test.dev", code, "newpassword")
    assert done.status_code == 200, done.text
    assert done.json()["success"] is True

    # The new password works...
    assert (await login(client, "ravi@test.dev", "newpassword")).status_code == 200
    # ...and the old one does not.
    stale = await login(client, "ravi@test.dev", "oldpassword")
    assert stale.status_code == 401
    assert stale.json()["error_code"] == "invalid_password"

    # Firebase got the new password too.
    twin = fake_firebase.users[created["firebase_uid"]]
    assert twin.email == "ravi@test.dev"


async def test_email_is_normalised(client: AsyncClient) -> None:
    await register(client, email="case@test.dev", password="oldpassword")

    sent = await forgot(client, "  CASE@Test.Dev  ")
    assert sent.status_code == 200, sent.text

    done = await reset(client, "CASE@TEST.DEV", sent.json()["data"]["dev_code"], "newpassword")
    assert done.status_code == 200, done.text
    assert (await login(client, "case@test.dev", "newpassword")).status_code == 200


# ------------------------------------------------------------- no account
async def test_unknown_email_is_rejected(client: AsyncClient) -> None:
    response = await forgot(client, "nobody@test.dev")

    assert response.status_code == 404
    assert response.json()["error_code"] == "user_not_found"
    assert "no account" in response.json()["message"].lower()


async def test_half_finished_signup_has_no_account_to_reset(client: AsyncClient) -> None:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": "halfway@test.dev", "password": "secret123", "first_name": "Half"},
    )
    assert started.status_code == 200

    response = await forgot(client, "halfway@test.dev")
    assert response.status_code == 404
    assert response.json()["error_code"] == "user_not_found"


async def test_reset_without_asking_for_a_code(client: AsyncClient) -> None:
    await register(client, email="nocode@test.dev", password="oldpassword")

    response = await reset(client, "nocode@test.dev", "123456", "newpassword")
    assert response.status_code == 400
    assert response.json()["error_code"] == "otp_not_found"


# ----------------------------------------------------------------- the OTP
async def test_wrong_code_counts_down_then_locks(client: AsyncClient) -> None:
    await register(client, email="brute@test.dev", password="oldpassword")
    await forgot(client, "brute@test.dev")

    for expected_left in (4, 3, 2, 1, 0):
        response = await reset(client, "brute@test.dev", "000000", "newpassword")
        assert response.status_code == 400
        assert response.json()["error_code"] == "otp_invalid"
        assert response.json()["details"]["attempts_left"] == expected_left

    locked = await reset(client, "brute@test.dev", "000000", "newpassword")
    assert locked.status_code == 429
    assert locked.json()["error_code"] == "otp_attempts_exceeded"

    # The old password still works — nothing was changed.
    assert (await login(client, "brute@test.dev", "oldpassword")).status_code == 200


async def test_code_cannot_be_reused(client: AsyncClient) -> None:
    await register(client, email="replay@test.dev", password="oldpassword")
    code = (await forgot(client, "replay@test.dev")).json()["data"]["dev_code"]

    assert (await reset(client, "replay@test.dev", code, "newpassword")).status_code == 200

    again = await reset(client, "replay@test.dev", code, "thirdpassword")
    assert again.status_code == 400
    assert again.json()["error_code"] == "otp_already_used"
    # The second attempt changed nothing.
    assert (await login(client, "replay@test.dev", "newpassword")).status_code == 200


async def test_asking_again_is_rate_limited(client: AsyncClient) -> None:
    await register(client, email="cooldown@test.dev", password="oldpassword")
    await forgot(client, "cooldown@test.dev")

    response = await forgot(client, "cooldown@test.dev")
    assert response.status_code == 429
    assert response.json()["error_code"] == "otp_cooldown"
    assert response.json()["details"]["retry_after_seconds"] > 0


async def test_a_signup_code_cannot_reset_a_password(client: AsyncClient) -> None:
    """Codes are scoped to their purpose."""
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": "purpose@test.dev", "password": "secret123", "first_name": "P"},
    )
    signup_code = started.json()["data"]["dev_code"]
    await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": "purpose@test.dev", "code": signup_code},
    )

    response = await reset(client, "purpose@test.dev", signup_code, "newpassword")
    assert response.status_code == 400
    assert response.json()["error_code"] == "otp_not_found"


# ------------------------------------------------------------- validation
@pytest.mark.parametrize("password", ["", "short"])
async def test_new_password_must_clear_the_firebase_minimum(
    client: AsyncClient, password: str
) -> None:
    await register(client, email="weak@test.dev", password="oldpassword")
    code = (await forgot(client, "weak@test.dev")).json()["data"]["dev_code"]

    response = await reset(client, "weak@test.dev", code, password)
    assert response.status_code == 422
    assert any(d["field"] == "new_password" for d in response.json()["details"])


async def test_suspended_account_cannot_reset(client: AsyncClient) -> None:
    await register(client, email="banned@test.dev", password="oldpassword")

    from app.models.enums import AccountStatus
    from app.models.user import User

    user = await User.find_one(User.email == "banned@test.dev")
    user.status = AccountStatus.SUSPENDED
    await user.save()

    response = await forgot(client, "banned@test.dev")
    assert response.status_code == 403
    assert response.json()["error_code"] == "account_suspended"


# ------------------------------------------------------- google-only account
async def test_google_only_account_can_set_a_password(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    """The code proves they own the address, so this is how they gain a password."""
    claims = fake_firebase.seed_google_user("googler@test.dev", name="Google User")
    created = await client.post(f"{P}/auth/google", json={"id_token": json.dumps(claims)})
    assert created.json()["data"]["user"]["auth_providers"] == ["google"]

    # Password sign-in is refused until one is set.
    refused = await login(client, "googler@test.dev", "anything")
    assert refused.json()["error_code"] == "password_not_set"

    code = (await forgot(client, "googler@test.dev")).json()["data"]["dev_code"]
    assert (await reset(client, "googler@test.dev", code, "brandnew1")).status_code == 200

    signed_in = await login(client, "googler@test.dev", "brandnew1")
    assert signed_in.status_code == 200, signed_in.text
    assert sorted(signed_in.json()["data"]["user"]["auth_providers"]) == ["google", "password"]
