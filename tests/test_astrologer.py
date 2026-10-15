"""Astrologer accounts: admin creates them, the astrologer signs in and edits."""

import pytest
from httpx import AsyncClient

from tests.conftest import FakeFirebase

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


async def make_admin(client: AsyncClient, email: str = "admin@test.dev") -> dict:
    """Registers an account and promotes it, since there is no admin sign-up route."""
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": "adminpass", "first_name": "Admin"},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    assert created.status_code == 201, created.text

    from app.models.enums import UserRole
    from app.models.user import User

    user = await User.find_one(User.email == email)
    user.role = UserRole.SUPER_ADMIN
    await user.save()

    signed_in = await client.post(f"{P}/auth/login", json={"email": email, "password": "adminpass"})
    token = signed_in.json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


BASE = {
    "email": "ravi.astro@test.dev",
    "first_name": "Ravi",
    "last_name": "Sharma",
    "skills": ["vedic_astrology", "numerology"],
    "languages": ["Hindi", "English"],
    "experience_years": 12,
}


async def create_astrologer(client: AsyncClient, admin: dict, **overrides):
    return await client.post(f"{P}/admin/astrologers", headers=admin, json={**BASE, **overrides})


def password_from_mail(fake_mail: list) -> str:
    """The generated password is only ever in the email."""
    assert fake_mail, "no email was sent"
    return fake_mail[-1]["password"]


@pytest.fixture
def sent_mail(monkeypatch: pytest.MonkeyPatch) -> list:
    """Captures the welcome email instead of sending it."""
    captured: list = []

    import app.services.astrologer as astrologer_service

    async def fake_send(to: str, name: str, password: str) -> None:
        captured.append({"to": to, "name": name, "password": password})

    monkeypatch.setattr(astrologer_service, "send_astrologer_welcome_email", fake_send)
    return captured


# ------------------------------------------------- astrologers cannot self-register
async def test_self_signup_never_produces_an_astrologer(client: AsyncClient) -> None:
    """The public sign-up route only ever creates an ordinary user."""
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": "wannabe@test.dev", "password": "secret123", "first_name": "Wannabe"},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": "wannabe@test.dev", "code": started.json()["data"]["dev_code"]},
    )
    assert created.json()["data"]["user"]["role"] == "user"

    token = created.json()["data"]["tokens"]["access_token"]
    refused = await client.get(f"{P}/astrologers/me", headers={"Authorization": f"Bearer {token}"})
    assert refused.status_code == 403
    assert refused.json()["error_code"] == "insufficient_role"


async def test_only_an_admin_can_create_one(client: AsyncClient) -> None:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": "plain@test.dev", "password": "secret123", "first_name": "Plain"},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": "plain@test.dev", "code": started.json()["data"]["dev_code"]},
    )
    token = created.json()["data"]["tokens"]["access_token"]

    refused = await client.post(
        f"{P}/admin/astrologers", headers={"Authorization": f"Bearer {token}"}, json=BASE
    )
    assert refused.status_code == 403
    assert refused.json()["error_code"] == "insufficient_role"


# --------------------------------------------------------------- admin creates
async def test_admin_creates_an_account_and_the_password_is_emailed(
    client: AsyncClient, fake_firebase: FakeFirebase, sent_mail: list
) -> None:
    admin = await make_admin(client)

    response = await create_astrologer(client, admin)
    assert response.status_code == 201, response.text
    body = response.json()["data"]

    assert body["welcome_email_sent"] is True
    # The password is not in the response when the email went out.
    assert body["initial_password"] is None

    profile = body["astrologer"]
    assert profile["email"] == "ravi.astro@test.dev"
    assert profile["full_name"] == "Ravi Sharma"
    assert profile["display_name"] == "Ravi Sharma"
    assert profile["slug"] == "ravi-sharma"
    assert profile["skills"] == ["vedic_astrology", "numerology"]
    assert profile["experience_years"] == 12
    assert profile["must_change_password"] is True

    # Emailed to the astrologer, and long enough for Firebase.
    assert sent_mail[-1]["to"] == "ravi.astro@test.dev"
    assert len(sent_mail[-1]["password"]) >= 6

    # The Firebase twin exists, as for any other account.
    assert len(fake_firebase.users) == 2  # the admin and the astrologer


async def test_the_astrologer_can_sign_in_with_the_emailed_password(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    await create_astrologer(client, admin)
    password = password_from_mail(sent_mail)

    signed_in = await client.post(
        f"{P}/auth/login", json={"email": "ravi.astro@test.dev", "password": password}
    )
    assert signed_in.status_code == 200, signed_in.text
    assert signed_in.json()["data"]["user"]["role"] == "astrologer"


async def test_a_duplicate_email_is_refused(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    assert (await create_astrologer(client, admin)).status_code == 201

    again = await create_astrologer(client, admin)
    assert again.status_code == 409
    assert again.json()["error_code"] == "email_already_registered"


async def test_a_failed_welcome_email_still_returns_the_password(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The admin must still have a way to pass the password on."""
    admin = await make_admin(client)

    import app.services.astrologer as astrologer_service

    async def boom(to: str, name: str, password: str) -> None:
        raise RuntimeError("smtp down")

    monkeypatch.setattr(astrologer_service, "send_astrologer_welcome_email", boom)

    response = await create_astrologer(client, admin)
    assert response.status_code == 201, response.text
    body = response.json()["data"]

    assert body["welcome_email_sent"] is False
    assert body["initial_password"]  # the fallback

    # And it really works.
    signed_in = await client.post(
        f"{P}/auth/login",
        json={"email": "ravi.astro@test.dev", "password": body["initial_password"]},
    )
    assert signed_in.status_code == 200


async def test_firebase_failure_creates_no_account(
    client: AsyncClient, fake_firebase: FakeFirebase, sent_mail: list
) -> None:
    admin = await make_admin(client)
    fake_firebase.fail_next_create = True

    response = await create_astrologer(client, admin)
    assert response.status_code == 503

    available = await client.get(
        f"{P}/auth/email/available", params={"email": "ravi.astro@test.dev"}
    )
    assert available.json()["data"]["available"] is True
    assert sent_mail == []


# ------------------------------------------------ astrologer edits themselves
async def astrologer_token(client: AsyncClient, sent_mail: list) -> dict:
    admin = await make_admin(client)
    await create_astrologer(client, admin)
    signed_in = await client.post(
        f"{P}/auth/login",
        json={"email": "ravi.astro@test.dev", "password": password_from_mail(sent_mail)},
    )
    token = signed_in.json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_astrologer_updates_their_own_details(client: AsyncClient, sent_mail: list) -> None:
    auth = await astrologer_token(client, sent_mail)

    response = await client.patch(
        f"{P}/astrologers/me",
        headers=auth,
        json={
            "display_name": "Acharya Ravi",
            "tagline": "Vedic astrologer since 2012",
            "bio": "Twelve years of practice.",
            "languages": ["Hindi", "English", "Bengali"],
            "qualifications": ["Jyotish Acharya"],
            "experience_years": 13,
        },
    )
    assert response.status_code == 200, response.text
    profile = response.json()["data"]

    assert profile["display_name"] == "Acharya Ravi"
    assert profile["slug"] == "acharya-ravi"  # renaming re-slugs
    assert profile["languages"] == ["Hindi", "English", "Bengali"]
    assert profile["experience_years"] == 13


async def test_astrologer_can_clear_a_field(client: AsyncClient, sent_mail: list) -> None:
    auth = await astrologer_token(client, sent_mail)
    await client.patch(f"{P}/astrologers/me", headers=auth, json={"tagline": "Something"})

    response = await client.patch(f"{P}/astrologers/me", headers=auth, json={"tagline": None})
    assert response.json()["data"]["tagline"] is None


async def test_astrologer_cannot_remove_their_display_name(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await astrologer_token(client, sent_mail)

    response = await client.patch(f"{P}/astrologers/me", headers=auth, json={"display_name": None})
    assert response.status_code == 403
    assert response.json()["error_code"] == "field_not_clearable"


@pytest.mark.parametrize(
    "body",
    [
        {"rates": {"chat_per_minute": 1}},
        {"commission_percent": 10},
        {"is_featured": True},
        {"status": "active"},
    ],
)
async def test_astrologer_cannot_set_platform_fields(
    client: AsyncClient, sent_mail: list, body: dict
) -> None:
    """Rates, commission and curation belong to the platform, not the astrologer."""
    auth = await astrologer_token(client, sent_mail)

    response = await client.patch(f"{P}/astrologers/me", headers=auth, json=body)
    assert response.status_code == 422
    assert response.json()["error_code"] == "validation_error"


async def test_astrologer_goes_online(client: AsyncClient, sent_mail: list) -> None:
    auth = await astrologer_token(client, sent_mail)

    response = await client.patch(
        f"{P}/astrologers/me/availability", headers=auth, json={"is_online": True}
    )
    assert response.status_code == 200
    availability = response.json()["data"]["availability"]
    assert availability["is_online"] is True
    assert availability["last_online_at"] is not None


# ------------------------------------------------------------ password change
async def test_astrologer_changes_the_emailed_password(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await astrologer_token(client, sent_mail)
    emailed = password_from_mail(sent_mail)

    changed = await client.post(
        f"{P}/auth/password/change",
        headers=auth,
        json={"current_password": emailed, "new_password": "my-own-password"},
    )
    assert changed.status_code == 200, changed.text

    # The new one works, the emailed one no longer does.
    assert (
        await client.post(
            f"{P}/auth/login",
            json={"email": "ravi.astro@test.dev", "password": "my-own-password"},
        )
    ).status_code == 200
    assert (
        await client.post(
            f"{P}/auth/login", json={"email": "ravi.astro@test.dev", "password": emailed}
        )
    ).status_code == 401

    # ...and the prompt to change it is gone.
    profile = await client.get(f"{P}/astrologers/me", headers=auth)
    assert profile.json()["data"]["must_change_password"] is False


async def test_the_wrong_current_password_is_refused(client: AsyncClient, sent_mail: list) -> None:
    auth = await astrologer_token(client, sent_mail)

    response = await client.post(
        f"{P}/auth/password/change",
        headers=auth,
        json={"current_password": "not-it", "new_password": "something-else"},
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "invalid_password"


async def test_the_new_password_must_differ(client: AsyncClient, sent_mail: list) -> None:
    auth = await astrologer_token(client, sent_mail)
    emailed = password_from_mail(sent_mail)

    response = await client.post(
        f"{P}/auth/password/change",
        headers=auth,
        json={"current_password": emailed, "new_password": emailed},
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "password_unchanged"


# ------------------------------------------------------------ admin manages
async def test_admin_sets_rates_and_lists(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    created = await create_astrologer(client, admin)
    astrologer_id = created.json()["data"]["astrologer"]["id"]

    updated = await client.patch(
        f"{P}/admin/astrologers/{astrologer_id}",
        headers=admin,
        json={
            "rates": {"chat_per_minute": 30, "call_per_minute": 45, "offer_chat_per_minute": 20},
            "commission_percent": 40,
            "is_featured": True,
        },
    )
    assert updated.status_code == 200, updated.text
    profile = updated.json()["data"]
    assert profile["rates"]["chat_per_minute"] == 30
    assert profile["rates"]["offer_chat_per_minute"] == 20
    assert profile["commission_percent"] == 40
    assert profile["is_featured"] is True

    listed = await client.get(f"{P}/admin/astrologers", headers=admin)
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1


async def test_admin_deactivates(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    created = await create_astrologer(client, admin)
    astrologer_id = created.json()["data"]["astrologer"]["id"]
    password = password_from_mail(sent_mail)

    removed = await client.delete(f"{P}/admin/astrologers/{astrologer_id}", headers=admin)
    assert removed.status_code == 200

    # Suspended, so they can no longer sign in.
    refused = await client.post(
        f"{P}/auth/login", json={"email": "ravi.astro@test.dev", "password": password}
    )
    assert refused.status_code == 403
    assert refused.json()["error_code"] == "account_suspended"

    fetched = await client.get(f"{P}/admin/astrologers/{astrologer_id}", headers=admin)
    assert fetched.json()["data"]["is_listed"] is False


async def test_unknown_astrologer_is_a_404(client: AsyncClient) -> None:
    admin = await make_admin(client)

    response = await client.get(f"{P}/admin/astrologers/507f1f77bcf86cd799439011", headers=admin)
    assert response.status_code == 404
    assert response.json()["error_code"] == "astrologer_not_found"


# ------------------------------------------------------- forgot password
async def test_astrologer_can_reset_a_forgotten_password(
    client: AsyncClient, sent_mail: list
) -> None:
    """The flow is the same as for a user — role is not checked anywhere in it."""
    admin = await make_admin(client)
    await create_astrologer(client, admin)
    emailed = password_from_mail(sent_mail)

    asked = await client.post(f"{P}/auth/password/forgot", json={"email": "ravi.astro@test.dev"})
    assert asked.status_code == 200, asked.text
    code = asked.json()["data"]["dev_code"]

    done = await client.post(
        f"{P}/auth/password/reset",
        json={"email": "ravi.astro@test.dev", "code": code, "new_password": "chosen-by-me"},
    )
    assert done.status_code == 200, done.text

    signed_in = await client.post(
        f"{P}/auth/login", json={"email": "ravi.astro@test.dev", "password": "chosen-by-me"}
    )
    assert signed_in.status_code == 200
    assert signed_in.json()["data"]["user"]["role"] == "astrologer"

    # The emailed password is dead.
    stale = await client.post(
        f"{P}/auth/login", json={"email": "ravi.astro@test.dev", "password": emailed}
    )
    assert stale.status_code == 401

    # And they are no longer told to change a password they just chose.
    auth = {"Authorization": f"Bearer {signed_in.json()['data']['tokens']['access_token']}"}
    profile = await client.get(f"{P}/astrologers/me", headers=auth)
    assert profile.json()["data"]["must_change_password"] is False


async def test_a_suspended_astrologer_cannot_reset(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    created = await create_astrologer(client, admin)
    await client.delete(
        f"{P}/admin/astrologers/{created.json()['data']['astrologer']['id']}", headers=admin
    )

    response = await client.post(f"{P}/auth/password/forgot", json={"email": "ravi.astro@test.dev"})
    assert response.status_code == 403
    assert response.json()["error_code"] == "account_suspended"
