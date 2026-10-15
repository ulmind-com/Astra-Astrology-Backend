"""Registration: manual email+password (OTP verified) and Google sign-in."""

import json

import pytest
from httpx import AsyncClient

from tests.conftest import FakeFirebase

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


# ----------------------------------------------------------------- helpers
async def start_signup(
    client: AsyncClient,
    email: str = "ravi@test.dev",
    password: str = "secret123",
    first_name: str = "Ravi",
    middle_name: str | None = "Shankar",
    last_name: str | None = "Sharma",
) -> str:
    """Starts a manual sign-up and returns the OTP."""
    response = await client.post(
        f"{P}/auth/register/email",
        json={
            "email": email,
            "password": password,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["dev_code"]


async def complete_signup(client: AsyncClient, email: str, code: str):
    return await client.post(f"{P}/auth/register/email/verify", json={"email": email, "code": code})


def google_token(claims: dict) -> str:
    """The Firebase double treats the token as its own JSON claims."""
    return json.dumps(claims)


# ------------------------------------------------------- manual registration
async def test_email_signup_creates_user_in_both_stores(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    code = await start_signup(client)

    # Nothing exists until the OTP is verified.
    assert fake_firebase.users == {}
    available = await client.get(f"{P}/auth/email/available", params={"email": "ravi@test.dev"})
    assert available.json()["data"]["available"] is True

    response = await complete_signup(client, "ravi@test.dev", code)
    assert response.status_code == 201, response.text
    body = response.json()["data"]

    assert body["is_new_user"] is True
    user = body["user"]
    assert user["email"] == "ravi@test.dev"
    assert (user["first_name"], user["middle_name"], user["last_name"]) == (
        "Ravi",
        "Shankar",
        "Sharma",
    )
    assert user["full_name"] == "Ravi Shankar Sharma"
    assert user["is_email_verified"] is True
    assert user["auth_providers"] == ["password"]
    assert user["role"] == "user"
    assert user["firebase_uid"] is not None

    # ...and the Firebase twin exists, with the same uid and display name.
    assert len(fake_firebase.users) == 1
    twin = fake_firebase.users[user["firebase_uid"]]
    assert twin.email == "ravi@test.dev"
    assert twin.display_name == "Ravi Shankar Sharma"
    assert twin.email_verified is True

    # The tokens work.
    me = await client.get(
        f"{P}/auth/me",
        headers={"Authorization": f"Bearer {body['tokens']['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["full_name"] == "Ravi Shankar Sharma"


async def test_email_is_normalised_and_names_trimmed(client: AsyncClient) -> None:
    code = await start_signup(
        client, email="  MiXeD@Test.Dev  ", first_name="  Priya  ", middle_name="  ", last_name=None
    )
    response = await complete_signup(client, "mixed@test.dev", code)
    assert response.status_code == 201, response.text

    user = response.json()["data"]["user"]
    assert user["email"] == "mixed@test.dev"
    assert user["first_name"] == "Priya"
    assert user["middle_name"] is None
    assert user["last_name"] is None
    assert user["full_name"] == "Priya"


async def test_duplicate_email_is_rejected_case_insensitively(client: AsyncClient) -> None:
    code = await start_signup(client, email="dup@test.dev")
    assert (await complete_signup(client, "dup@test.dev", code)).status_code == 201

    response = await client.post(
        f"{P}/auth/register/email",
        json={"email": "DUP@TEST.DEV", "password": "secret123", "first_name": "Other"},
    )
    assert response.status_code == 409
    assert response.json()["error_code"] == "email_already_registered"
    assert response.json()["details"]["providers"] == ["password"]


async def test_wrong_otp_counts_down_then_locks(client: AsyncClient) -> None:
    await start_signup(client, email="brute@test.dev")

    for expected_left in (4, 3, 2, 1, 0):
        response = await complete_signup(client, "brute@test.dev", "000000")
        assert response.status_code == 400
        assert response.json()["error_code"] == "otp_invalid"
        assert response.json()["details"]["attempts_left"] == expected_left

    locked = await complete_signup(client, "brute@test.dev", "000000")
    assert locked.status_code == 429
    assert locked.json()["error_code"] == "otp_attempts_exceeded"


async def test_otp_cannot_be_reused(client: AsyncClient) -> None:
    code = await start_signup(client, email="replay@test.dev")
    assert (await complete_signup(client, "replay@test.dev", code)).status_code == 201

    again = await complete_signup(client, "replay@test.dev", code)
    assert again.status_code in (400, 409)
    assert again.json()["success"] is False


async def test_resend_is_rate_limited(client: AsyncClient) -> None:
    await start_signup(client, email="cooldown@test.dev")

    response = await client.post(
        f"{P}/auth/register/email/resend", json={"email": "cooldown@test.dev"}
    )
    assert response.status_code == 429
    assert response.json()["error_code"] == "otp_cooldown"
    assert response.json()["details"]["retry_after_seconds"] > 0


async def test_resend_requires_a_signup_in_progress(client: AsyncClient) -> None:
    response = await client.post(
        f"{P}/auth/register/email/resend", json={"email": "nobody@test.dev"}
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "pending_registration_not_found"


async def test_verify_without_a_signup_in_progress(client: AsyncClient) -> None:
    response = await complete_signup(client, "nobody@test.dev", "123456")
    assert response.status_code == 400
    assert response.json()["error_code"] == "pending_registration_not_found"


async def test_restarting_a_signup_invalidates_the_previous_code(client: AsyncClient) -> None:
    first_code = await start_signup(client, email="restart@test.dev")

    # A second attempt for the same email supersedes the first.
    import app.services.otp as otp_service

    original_cooldown = otp_service.settings.OTP_RESEND_COOLDOWN_SECONDS
    otp_service.settings.OTP_RESEND_COOLDOWN_SECONDS = 0
    try:
        second_code = await start_signup(client, email="restart@test.dev", first_name="Restarted")
    finally:
        otp_service.settings.OTP_RESEND_COOLDOWN_SECONDS = original_cooldown

    assert first_code != second_code

    stale = await complete_signup(client, "restart@test.dev", first_code)
    assert stale.status_code == 400

    fresh = await complete_signup(client, "restart@test.dev", second_code)
    assert fresh.status_code == 201
    assert fresh.json()["data"]["user"]["first_name"] == "Restarted"


# ------------------------------------------------------- validation of input
@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"email": "not-an-email", "password": "secret123", "first_name": "A"}, "email"),
        ({"email": "a@test.dev", "password": "", "first_name": "A"}, "password"),
        # Firebase Auth refuses anything under 6 characters.
        ({"email": "a@test.dev", "password": "short", "first_name": "A"}, "password"),
        ({"email": "a@test.dev", "password": "x" * 73, "first_name": "A"}, "password"),
        ({"email": "a@test.dev", "password": "secret123", "first_name": ""}, "first_name"),
    ],
)
async def test_invalid_input_is_rejected(client: AsyncClient, payload: dict, field: str) -> None:
    response = await client.post(f"{P}/auth/register/email", json=payload)
    assert response.status_code == 422
    assert response.json()["error_code"] == "validation_error"
    assert any(detail["field"] == field for detail in response.json()["details"])


@pytest.mark.parametrize("length", [6, 72])
async def test_password_length_boundaries_are_accepted(client: AsyncClient, length: int) -> None:
    """6 is Firebase's floor, 72 is bcrypt's ceiling; both ends must work."""
    code = await start_signup(client, email="bounds@test.dev", password="x" * length)
    assert (await complete_signup(client, "bounds@test.dev", code)).status_code == 201


# --------------------------------------------------------------- consistency
async def test_mongo_failure_rolls_back_the_firebase_user(
    client: AsyncClient, fake_firebase: FakeFirebase, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The invariant: never leave a Firebase user without a MongoDB twin.

    Driven through the service rather than HTTP, because the point is the
    rollback, not the status code an unhandled error produces.
    """
    code = await start_signup(client, email="rollback@test.dev")

    from app.models.user import User
    from app.services import registration

    async def explode(self, *args, **kwargs):  # noqa: ANN001, ANN202
        raise RuntimeError("mongo is down")

    monkeypatch.setattr(User, "insert", explode)

    with pytest.raises(RuntimeError, match="mongo is down"):
        await registration.complete_email_registration("rollback@test.dev", code)

    # The Firebase user was created, then deleted again.
    assert fake_firebase.created_uids, "expected a Firebase user to have been created"
    assert fake_firebase.deleted_uids == fake_firebase.created_uids
    assert fake_firebase.users == {}

    # And MongoDB has nothing, so the email is free to try again.
    monkeypatch.undo()
    available = await client.get(f"{P}/auth/email/available", params={"email": "rollback@test.dev"})
    assert available.json()["data"]["available"] is True
    assert available.json()["data"]["exists_in"] == []


async def test_firebase_failure_creates_nothing(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    code = await start_signup(client, email="fbfail@test.dev")
    fake_firebase.fail_next_create = True

    response = await complete_signup(client, "fbfail@test.dev", code)
    assert response.status_code == 503
    assert response.json()["error_code"] == "firebase_unavailable"

    assert fake_firebase.users == {}
    available = await client.get(f"{P}/auth/email/available", params={"email": "fbfail@test.dev"})
    assert available.json()["data"]["available"] is True


async def test_orphaned_firebase_user_is_adopted(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    """A previous attempt died after Firebase but before MongoDB."""
    orphan = await fake_firebase.create_user(email="orphan@test.dev", password="old")
    assert len(fake_firebase.users) == 1

    # The email still reads as available, because MongoDB has no record.
    available = await client.get(f"{P}/auth/email/available", params={"email": "orphan@test.dev"})
    assert available.json()["data"]["available"] is True
    assert available.json()["data"]["exists_in"] == ["firebase"]

    code = await start_signup(client, email="orphan@test.dev", first_name="Adopted")
    response = await complete_signup(client, "orphan@test.dev", code)
    assert response.status_code == 201, response.text

    # Reused, not duplicated.
    assert len(fake_firebase.users) == 1
    assert response.json()["data"]["user"]["firebase_uid"] == orphan.uid


async def test_signup_is_refused_while_firebase_is_down(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    fake_firebase.enabled = False

    response = await client.post(
        f"{P}/auth/register/email",
        json={"email": "down@test.dev", "password": "secret123", "first_name": "A"},
    )
    assert response.status_code == 503
    assert response.json()["error_code"] == "firebase_not_configured"


# ------------------------------------------------------------- google sign-in
async def test_google_registers_on_first_use(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    claims = fake_firebase.seed_google_user(
        "Gita@Test.Dev", name="Gita Devi Patel", picture="https://example.com/a.jpg"
    )

    response = await client.post(f"{P}/auth/google", json={"id_token": google_token(claims)})
    assert response.status_code == 200, response.text
    body = response.json()["data"]

    assert body["is_new_user"] is True
    user = body["user"]
    assert user["email"] == "gita@test.dev"
    # The name is pulled from Google and split across the three fields.
    assert (user["first_name"], user["middle_name"], user["last_name"]) == (
        "Gita",
        "Devi",
        "Patel",
    )
    assert user["auth_providers"] == ["google"]
    assert user["is_email_verified"] is True
    assert user["avatar_url"] == "https://example.com/a.jpg"
    assert user["firebase_uid"] == claims["uid"]


async def test_google_signs_in_on_later_use(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    claims = fake_firebase.seed_google_user("repeat@test.dev", name="Repeat User")

    first = await client.post(f"{P}/auth/google", json={"id_token": google_token(claims)})
    assert first.json()["data"]["is_new_user"] is True
    user_id = first.json()["data"]["user"]["id"]

    second = await client.post(f"{P}/auth/google", json={"id_token": google_token(claims)})
    assert second.status_code == 200
    assert second.json()["data"]["is_new_user"] is False
    assert second.json()["data"]["user"]["id"] == user_id  # same account, not a duplicate


@pytest.mark.parametrize(
    ("display_name", "expected"),
    [
        ("Madonna", ("Madonna", None, None)),
        ("Ravi Sharma", ("Ravi", None, "Sharma")),
        ("Ravi Shankar Sharma", ("Ravi", "Shankar", "Sharma")),
        ("A B C D", ("A", "B C", "D")),
        (None, ("User", None, None)),
    ],
)
async def test_google_name_is_split_across_fields(
    client: AsyncClient,
    fake_firebase: FakeFirebase,
    display_name: str | None,
    expected: tuple[str, str | None, str | None],
) -> None:
    claims = fake_firebase.seed_google_user("split@test.dev", name=display_name)
    response = await client.post(f"{P}/auth/google", json={"id_token": google_token(claims)})
    assert response.status_code == 200, response.text

    user = response.json()["data"]["user"]
    assert (user["first_name"], user["middle_name"], user["last_name"]) == expected


async def test_google_links_to_an_account_registered_with_a_password(
    client: AsyncClient, fake_firebase: FakeFirebase
) -> None:
    code = await start_signup(client, email="both@test.dev", first_name="Both")
    created = await complete_signup(client, "both@test.dev", code)
    assert created.status_code == 201
    user_id = created.json()["data"]["user"]["id"]
    firebase_uid = created.json()["data"]["user"]["firebase_uid"]

    # Firebase links Google to the existing email, so the uid is the same one.
    claims = {
        "uid": firebase_uid,
        "email": "both@test.dev",
        "name": "Both Ways",
        "email_verified": True,
        "picture": "https://example.com/b.jpg",
    }
    response = await client.post(f"{P}/auth/google", json={"id_token": google_token(claims)})
    assert response.status_code == 200, response.text
    body = response.json()["data"]

    assert body["is_new_user"] is False
    assert body["user"]["id"] == user_id
    assert sorted(body["user"]["auth_providers"]) == ["google", "password"]
    # The existing name is kept; Google does not overwrite it.
    assert body["user"]["first_name"] == "Both"


async def test_google_token_without_an_email_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        f"{P}/auth/google",
        json={"id_token": google_token({"uid": "fb-123", "name": "No Email"})},
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "google_email_missing"


async def test_invalid_google_token_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        f"{P}/auth/google", json={"id_token": "this-is-not-a-valid-firebase-id-token"}
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_id_token"


async def test_short_google_token_fails_validation(client: AsyncClient) -> None:
    response = await client.post(f"{P}/auth/google", json={"id_token": "tiny"})
    assert response.status_code == 422
    assert response.json()["error_code"] == "validation_error"


# ------------------------------------------------------------------- /auth/me
async def test_me_requires_a_token(client: AsyncClient) -> None:
    response = await client.get(f"{P}/auth/me")
    assert response.status_code == 401
    assert response.json()["error_code"] == "missing_token"


async def test_me_rejects_a_refresh_token(client: AsyncClient) -> None:
    code = await start_signup(client, email="tokentype@test.dev")
    created = await complete_signup(client, "tokentype@test.dev", code)
    refresh = created.json()["data"]["tokens"]["refresh_token"]

    response = await client.get(f"{P}/auth/me", headers={"Authorization": f"Bearer {refresh}"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_token_type"
