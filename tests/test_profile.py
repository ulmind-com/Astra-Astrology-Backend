"""Profile: reading, partial updates, clearing fields, and addresses."""

import pytest
from httpx import AsyncClient

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


async def signed_in(client: AsyncClient, email: str = "ravi@test.dev") -> dict:
    """Registers a user and returns auth headers."""
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": "secret123", "first_name": "Ravi"},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    assert created.status_code == 201, created.text
    token = created.json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def get_profile(client: AsyncClient, auth: dict):
    return await client.get(f"{P}/users/me", headers=auth)


async def patch_profile(client: AsyncClient, auth: dict, body: dict):
    return await client.patch(f"{P}/users/me", headers=auth, json=body)


# ------------------------------------------------------------------ reading
async def test_profile_starts_mostly_empty(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await get_profile(client, auth)
    assert response.status_code == 200, response.text
    data = response.json()["data"]

    assert data["first_name"] == "Ravi"
    assert data["gender"] == "undisclosed"
    assert data["birth"]["date_of_birth"] is None
    assert data["addresses"] == []
    assert data["completeness"]["chart_ready"] is False
    assert data["completeness"]["numerology_ready"] is False
    assert "birth.date_of_birth" in data["completeness"]["missing"]


async def test_profile_requires_a_token(client: AsyncClient) -> None:
    response = await client.get(f"{P}/users/me")
    assert response.status_code == 401


# ------------------------------------------------------------------ editing
async def test_full_birth_details_make_the_chart_ready(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await patch_profile(
        client,
        auth,
        {
            "birth": {
                "date_of_birth": "1995-08-21",
                "time_of_birth": "14:35",
                "is_time_known": True,
                "place": "Kolkata, West Bengal, India",
                "city": "Kolkata",
                "state": "West Bengal",
                "country": "India",
                "latitude": 22.5726,
                "longitude": 88.3639,
                "timezone": "Asia/Kolkata",
                "timezone_offset": 5.5,
            }
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]

    assert data["birth"]["date_of_birth"] == "1995-08-21"
    assert data["birth"]["time_of_birth"] == "14:35"
    assert data["birth"]["latitude"] == 22.5726
    assert data["completeness"]["chart_ready"] is True
    assert data["completeness"]["numerology_ready"] is True


async def test_patch_only_touches_the_fields_sent(client: AsyncClient) -> None:
    auth = await signed_in(client)
    await patch_profile(client, auth, {"birth": {"date_of_birth": "1990-01-03", "city": "Delhi"}})

    # A second patch of one nested field must not wipe the others.
    response = await patch_profile(client, auth, {"birth": {"timezone": "Asia/Kolkata"}})
    birth = response.json()["data"]["birth"]

    assert birth["date_of_birth"] == "1990-01-03"
    assert birth["city"] == "Delhi"
    assert birth["timezone"] == "Asia/Kolkata"


async def test_explicit_null_clears_a_field(client: AsyncClient) -> None:
    auth = await signed_in(client)
    await patch_profile(client, auth, {"occupation": "Engineer", "middle_name": "Kumar"})

    response = await patch_profile(client, auth, {"occupation": None})
    data = response.json()["data"]

    assert data["occupation"] is None
    assert data["middle_name"] == "Kumar"  # untouched


async def test_null_clears_a_nested_field_too(client: AsyncClient) -> None:
    auth = await signed_in(client)
    await patch_profile(
        client, auth, {"birth": {"date_of_birth": "1990-01-03", "time_of_birth": "10:00"}}
    )

    response = await patch_profile(client, auth, {"birth": {"time_of_birth": None}})
    birth = response.json()["data"]["birth"]

    assert birth["time_of_birth"] is None
    assert birth["date_of_birth"] == "1990-01-03"


async def test_null_resets_a_whole_block(client: AsyncClient) -> None:
    auth = await signed_in(client)
    await patch_profile(client, auth, {"birth": {"date_of_birth": "1990-01-03", "city": "Delhi"}})

    response = await patch_profile(client, auth, {"birth": None})
    birth = response.json()["data"]["birth"]

    assert birth["date_of_birth"] is None
    assert birth["city"] is None


async def test_first_name_cannot_be_removed(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await patch_profile(client, auth, {"first_name": None})
    assert response.status_code == 400
    assert response.json()["error_code"] == "field_not_clearable"


async def test_names_are_trimmed(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await patch_profile(
        client, auth, {"first_name": "  Ravi  ", "last_name": "  Sharma  "}
    )
    data = response.json()["data"]

    assert data["first_name"] == "Ravi"
    assert data["full_name"] == "Ravi Sharma"


# ------------------------------------------------------- astrology validation
@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"birth": {"timezone": "Mars/Olympus"}}, "birth.timezone"),
        ({"birth": {"time_of_birth": "25:00"}}, "birth.time_of_birth"),
        ({"birth": {"time_of_birth": "9:5"}}, "birth.time_of_birth"),
        ({"birth": {"latitude": 120}}, "birth.latitude"),
        ({"birth": {"longitude": -200}}, "birth.longitude"),
        ({"birth": {"date_of_birth": "2099-01-01"}}, "birth.date_of_birth"),
        ({"birth": {"date_of_birth": "1850-01-01"}}, "birth.date_of_birth"),
        ({"current_location": {"timezone": "Not/AZone"}}, "current_location.timezone"),
    ],
)
async def test_bad_astrology_input_is_rejected(client: AsyncClient, body: dict, field: str) -> None:
    """A bad timezone or time produces a silently wrong chart, so reject it here."""
    auth = await signed_in(client)

    response = await patch_profile(client, auth, body)
    assert response.status_code == 422, response.text
    assert any(detail["field"] == field for detail in response.json()["details"])


async def test_a_real_timezone_is_accepted(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await patch_profile(client, auth, {"birth": {"timezone": "America/New_York"}})
    assert response.status_code == 200
    assert response.json()["data"]["birth"]["timezone"] == "America/New_York"


# ------------------------------------------------------- numerology fields
async def test_numerology_name_falls_back_to_the_legal_name(client: AsyncClient) -> None:
    auth = await signed_in(client)
    await patch_profile(client, auth, {"last_name": "Sharma"})

    data = (await get_profile(client, auth)).json()["data"]
    assert data["numerology_name"] is None
    assert data["name_for_numerology"] == "Ravi Sharma"

    await patch_profile(client, auth, {"numerology_name": "Ravee Sharmaa"})
    data = (await get_profile(client, auth)).json()["data"]
    assert data["name_for_numerology"] == "Ravee Sharmaa"


async def test_call_names_are_deduplicated_and_trimmed(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await patch_profile(
        client, auth, {"call_names": ["  Ravi  ", "Rav", "Ravi", "   ", "Bapu"]}
    )
    assert response.json()["data"]["call_names"] == ["Ravi", "Rav", "Bapu"]


# ------------------------------------------------------------------- phone
async def test_setting_a_phone_marks_it_unverified(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await patch_profile(client, auth, {"phone": "+91 98300-12345"})
    data = response.json()["data"]

    assert data["phone"] == "919830012345"  # punctuation stripped
    assert data["is_phone_verified"] is False


async def test_phone_cannot_be_taken_twice(client: AsyncClient) -> None:
    first = await signed_in(client, "first@test.dev")
    second = await signed_in(client, "second@test.dev")

    assert (await patch_profile(client, first, {"phone": "9830012345"})).status_code == 200

    clash = await patch_profile(client, second, {"phone": "9830012345"})
    assert clash.status_code == 409
    assert clash.json()["error_code"] == "phone_already_registered"


# --------------------------------------------------------------- addresses
async def test_address_lifecycle(client: AsyncClient) -> None:
    auth = await signed_in(client)
    body = {
        "label": "Home",
        "full_name": "Ravi Sharma",
        "phone": "9830012345",
        "line1": "12 Park Street",
        "city": "Kolkata",
        "state": "West Bengal",
        "postal_code": "700016",
    }

    created = await client.post(f"{P}/users/me/addresses", headers=auth, json=body)
    assert created.status_code == 201, created.text
    address = created.json()["data"]
    assert address["is_default"] is True  # the first one always is
    address_id = address["id"]

    updated = await client.patch(
        f"{P}/users/me/addresses/{address_id}", headers=auth, json={"line2": "Flat 4B"}
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["line2"] == "Flat 4B"
    assert updated.json()["data"]["line1"] == "12 Park Street"

    listed = await client.get(f"{P}/users/me/addresses", headers=auth)
    assert len(listed.json()["data"]) == 1

    deleted = await client.delete(f"{P}/users/me/addresses/{address_id}", headers=auth)
    assert deleted.status_code == 200
    assert (await client.get(f"{P}/users/me/addresses", headers=auth)).json()["data"] == []


async def test_only_one_address_is_default(client: AsyncClient) -> None:
    auth = await signed_in(client)
    body = {
        "full_name": "Ravi",
        "phone": "9830012345",
        "line1": "A",
        "city": "Kolkata",
        "state": "WB",
        "postal_code": "700016",
    }

    first = (await client.post(f"{P}/users/me/addresses", headers=auth, json=body)).json()["data"]
    second = (
        await client.post(
            f"{P}/users/me/addresses", headers=auth, json={**body, "line1": "B", "is_default": True}
        )
    ).json()["data"]

    addresses = (await client.get(f"{P}/users/me/addresses", headers=auth)).json()["data"]
    by_id = {a["id"]: a for a in addresses}

    assert by_id[second["id"]]["is_default"] is True
    assert by_id[first["id"]]["is_default"] is False


async def test_deleting_the_default_promotes_another(client: AsyncClient) -> None:
    auth = await signed_in(client)
    body = {
        "full_name": "Ravi",
        "phone": "9830012345",
        "line1": "A",
        "city": "Kolkata",
        "state": "WB",
        "postal_code": "700016",
    }

    first = (await client.post(f"{P}/users/me/addresses", headers=auth, json=body)).json()["data"]
    await client.post(f"{P}/users/me/addresses", headers=auth, json={**body, "line1": "B"})

    await client.delete(f"{P}/users/me/addresses/{first['id']}", headers=auth)

    remaining = (await client.get(f"{P}/users/me/addresses", headers=auth)).json()["data"]
    assert len(remaining) == 1
    assert remaining[0]["is_default"] is True


async def test_unknown_address_is_a_404(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await client.delete(f"{P}/users/me/addresses/does-not-exist", headers=auth)
    assert response.status_code == 404
    assert response.json()["error_code"] == "address_not_found"


# ----------------------------------------------------------- notifications
async def test_notification_preferences_can_be_changed(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await patch_profile(
        client,
        auth,
        {"notifications": {"push": False, "marketing": False, "remedy_reminders": True}},
    )
    prefs = response.json()["data"]["notifications"]

    assert prefs["push"] is False
    assert prefs["marketing"] is False
    assert prefs["remedy_reminders"] is True


# ---------------------------------------------------------------- avatar
async def test_removing_a_missing_avatar_is_a_404(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await client.delete(f"{P}/users/me/avatar", headers=auth)
    assert response.status_code == 404
    assert response.json()["error_code"] == "no_avatar"


# ------------------------------------------------------- email is not editable
async def test_email_cannot_be_changed(client: AsyncClient) -> None:
    """The email is the sign-in identity, so it is rejected outright."""
    auth = await signed_in(client, "fixed@test.dev")

    response = await patch_profile(client, auth, {"email": "someone.else@test.dev"})
    assert response.status_code == 422
    assert any(d["field"] == "email" for d in response.json()["details"])

    unchanged = await get_profile(client, auth)
    assert unchanged.json()["data"]["email"] == "fixed@test.dev"


async def test_a_misspelt_field_is_an_error_not_a_silent_no_op(client: AsyncClient) -> None:
    auth = await signed_in(client)

    response = await patch_profile(client, auth, {"firstname": "Ravi"})
    assert response.status_code == 422
    assert any(d["field"] == "firstname" for d in response.json()["details"])


# ----------------------------------------------------------------- avatar
async def test_avatar_is_compressed_and_replaces_the_previous_one(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cloudinary is stubbed; what matters is the options sent and the cleanup."""
    from app.core.config import settings
    from app.services import storage
    from app.services.storage import UploadResult

    uploads: list[dict] = []
    deleted: list[str] = []
    counter = {"n": 0}

    async def fake_upload(file, folder="misc", **kwargs):  # noqa: ANN001, ANN003
        counter["n"] += 1
        uploads.append({"folder": folder, **kwargs})
        return UploadResult(
            url=f"https://cdn.test/avatar-{counter['n']}.webp",
            public_id=f"avatars/pic-{counter['n']}",
            resource_type="image",
            format="webp",
            bytes=20_000,
            width=512,
            height=512,
            folder=folder,
        )

    async def fake_delete(public_id, resource_type="image"):  # noqa: ANN001
        deleted.append(public_id)
        return True

    monkeypatch.setattr(storage, "upload_file", fake_upload)
    monkeypatch.setattr(storage, "delete_file", fake_delete)

    auth = await signed_in(client)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64

    first = await client.post(
        f"{P}/users/me/avatar", headers=auth, files={"file": ("a.png", png, "image/png")}
    )
    assert first.status_code == 200, first.text
    assert first.json()["data"]["avatar_url"] == "https://cdn.test/avatar-1.webp"

    # It was asked to shrink and re-encode before storing.
    options = uploads[0]
    assert options["folder"] == "avatars"
    assert options["image_format"] == settings.AVATAR_FORMAT
    assert options["transformation"][0] == {
        "width": settings.AVATAR_MAX_DIMENSION,
        "height": settings.AVATAR_MAX_DIMENSION,
        "crop": "limit",
    }
    assert options["transformation"][1] == {"quality": settings.AVATAR_QUALITY}
    assert deleted == []  # nothing to replace yet

    # Uploading again replaces the stored file and removes the old one.
    second = await client.post(
        f"{P}/users/me/avatar", headers=auth, files={"file": ("b.png", png, "image/png")}
    )
    assert second.status_code == 200
    assert second.json()["data"]["avatar_url"] == "https://cdn.test/avatar-2.webp"
    assert deleted == ["avatars/pic-1"]

    # Removing it deletes the current file too.
    removed = await client.delete(f"{P}/users/me/avatar", headers=auth)
    assert removed.status_code == 200
    assert removed.json()["data"]["avatar_url"] is None
    assert deleted == ["avatars/pic-1", "avatars/pic-2"]
