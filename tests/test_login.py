"""Login: email + password, and Google (which registers on first use)."""

import json

import pytest
from httpx import AsyncClient

from tests.conftest import FakeFirebase

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


async def register(
    client: AsyncClient,
    email: str = "ravi@test.dev",
    password: str = "secret123",
    first_name: str = "Ravi",
) -> dict:
    """Completes a manual sign-up and returns the created user."""
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": password, "first_name": first_name},
    )
    assert started.status_code == 200, started.text
    code = started.json()["data"]["dev_code"]

    created = await client.post(
        f"{P}/auth/register/email/verify", json={"email": email, "code": code}
    )
    assert created.status_code == 201, created.text
    return created.json()["data"]["user"]


async def login(client: AsyncClient, email: str, password: str):
    return await client.post(f"{P}/auth/login", json={"email": email, "password": password})


# ------------------------------------------------------ password login
async def test_registered_user_can_sign_in(client: AsyncClient) -> None:
    created = await register(client, email="ravi@test.dev", password="secret123")

    response = await login(client, "ravi@test.dev", "secret123")
    assert response.status_code == 200, response.text
    body = response.json()["data"]

    assert body["is_new_user"] is False
    assert body["user"]["id"] == created["id"]
    assert body["user"]["email"] == "ravi@test.dev"
    assert body["tokens"]["access_token"]

    me = await client.get(
        f"{P}/auth/me", headers={"Authorization": f"Bearer {body['tokens']['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "ravi@test.dev"


async def test_login_is_case_insensitive(client: AsyncClient) -> None:
    await register(client, email="case@test.dev", password="secret123")

    response = await login(client, "  CASE@Test.Dev  ", "secret123")
    assert response.status_code == 200, response.text


async def test_login_records_last_login(client: AsyncClient) -> None:
    await register(client, email="stamp@test.dev", password="secret123")

    response = await login(client, "stamp@test.dev", "secret123")
    assert response.json()["data"]["user"]["last_login_at"] is not None


async def test_unknown_email_is_told_to_register(client: AsyncClient) -> None:
    response = await login(client, "nobody@test.dev", "secret123")

    assert response.status_code == 404
    assert response.json()["error_code"] == "user_not_found"
    assert "register" in response.json()["message"].lower()


async def test_wrong_password_is_rejected(client: AsyncClient) -> None:
    await register(client, email="wrong@test.dev", password="secret123")

    response = await login(client, "wrong@test.dev", "not-the-password")
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_password"


async def test_half_finished_signup_is_told_to_finish(client: AsyncClient) -> None:
    """Started a sign-up but never entered the OTP."""
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": "halfway@test.dev", "password": "secret123", "first_name": "Half"},
    )
    assert started.status_code == 200

    response = await login(client, "halfway@test.dev", "secret123")
    assert response.status_code == 404
    assert response.json()["error_code"] == "registration_incomplete"


async def test_google_only_account_cannot_use_a_password(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    claims = fake_firebase.seed_google_user("googler@test.dev", name="Google User")
    created = await client.post(f"{P}/auth/google", json={"id_token": json.dumps(claims)})
    assert created.status_code == 200
    assert created.json()["data"]["user"]["auth_providers"] == ["google"]

    response = await login(client, "googler@test.dev", "any-password")
    assert response.status_code == 401
    assert response.json()["error_code"] == "password_not_set"
    assert response.json()["details"]["providers"] == ["google"]


async def test_suspended_account_cannot_sign_in(client: AsyncClient) -> None:
    await register(client, email="banned@test.dev", password="secret123")

    from app.models.enums import AccountStatus
    from app.models.user import User

    user = await User.find_one(User.email == "banned@test.dev")
    user.status = AccountStatus.SUSPENDED
    await user.save()

    response = await login(client, "banned@test.dev", "secret123")
    assert response.status_code == 403
    assert response.json()["error_code"] == "account_suspended"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"email": "not-an-email", "password": "secret123"}, "email"),
        ({"email": "a@test.dev", "password": ""}, "password"),
    ],
)
async def test_invalid_login_input_is_rejected(
    client: AsyncClient, payload: dict, field: str
) -> None:
    response = await client.post(f"{P}/auth/login", json=payload)
    assert response.status_code == 422
    assert any(detail["field"] == field for detail in response.json()["details"])


# -------------------------------------------------------- google login
async def test_google_registers_when_there_is_no_account(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    claims = fake_firebase.seed_google_user("fresh@test.dev", name="Fresh User")

    response = await client.post(f"{P}/auth/google", json={"id_token": json.dumps(claims)})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["is_new_user"] is True


async def test_google_signs_in_when_the_account_exists(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    claims = fake_firebase.seed_google_user("again@test.dev", name="Again User")

    first = await client.post(f"{P}/auth/google", json={"id_token": json.dumps(claims)})
    second = await client.post(f"{P}/auth/google", json={"id_token": json.dumps(claims)})

    assert second.status_code == 200
    assert second.json()["data"]["is_new_user"] is False
    assert second.json()["data"]["user"]["id"] == first.json()["data"]["user"]["id"]


async def test_password_user_can_also_sign_in_with_google(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    created = await register(client, email="both@test.dev", password="secret123")

    claims = {
        "uid": created["firebase_uid"],
        "email": "both@test.dev",
        "name": "Both Ways",
        "email_verified": True,
    }
    response = await client.post(f"{P}/auth/google", json={"id_token": json.dumps(claims)})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["user"]["id"] == created["id"]
    assert sorted(response.json()["data"]["user"]["auth_providers"]) == ["google", "password"]

    # ...and the password still works afterwards.
    assert (await login(client, "both@test.dev", "secret123")).status_code == 200
