"""The public astrologer directory, and astrologer images."""

import pytest
from httpx import AsyncClient

from tests.test_astrologer import BASE, make_admin

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


@pytest.fixture
def sent_mail(monkeypatch: pytest.MonkeyPatch) -> list:
    captured: list = []

    import app.services.astrologer as astrologer_service

    async def fake_send(to: str, name: str, password: str) -> bool:
        captured.append({"to": to, "password": password})
        return True

    monkeypatch.setattr(astrologer_service, "send_astrologer_welcome_email", fake_send)
    return captured


async def add_astrologer(client: AsyncClient, admin: dict, **overrides) -> dict:
    response = await client.post(
        f"{P}/admin/astrologers", headers=admin, json={**BASE, **overrides}
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["astrologer"]


async def listing(client: AsyncClient, **params) -> dict:
    response = await client.get(f"{P}/astrologers", params=params)
    assert response.status_code == 200, response.text
    return response.json()["data"]


# ------------------------------------------------------------- the directory
async def test_directory_is_public_and_hides_private_fields(
    client: AsyncClient, sent_mail: list
) -> None:
    """Anyone can read it, so it must not leak contact or commercial details."""
    admin = await make_admin(client)
    await add_astrologer(client, admin, email="ravi.astro@test.dev")

    data = await listing(client)  # no Authorization header at all
    assert data["meta"]["total"] == 1

    entry = data["items"][0]
    assert entry["display_name"] == "Ravi Sharma"
    for leaked in ("email", "phone", "bank", "commission_percent", "user_id", "status"):
        assert leaked not in entry, f"{leaked} must not be public"


async def test_online_comes_first_then_featured(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)

    await add_astrologer(client, admin, email="plain@test.dev", first_name="Plain")
    featured = await add_astrologer(
        client, admin, email="star@test.dev", first_name="Star", is_featured=True
    )
    online = await add_astrologer(client, admin, email="live@test.dev", first_name="Live")

    # Put the third one online.
    signed_in = await client.post(
        f"{P}/auth/login",
        json={"email": "live@test.dev", "password": sent_mail[-1]["password"]},
    )
    token = signed_in.json()["data"]["tokens"]["access_token"]
    await client.patch(
        f"{P}/astrologers/me/availability",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_online": True},
    )

    order = [item["id"] for item in (await listing(client))["items"]]
    assert order[0] == online["id"], "online should lead"
    assert order[1] == featured["id"], "featured should follow"


async def test_unlisted_and_suspended_astrologers_are_hidden(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    visible = await add_astrologer(client, admin, email="seen@test.dev", first_name="Seen")
    hidden = await add_astrologer(
        client, admin, email="hidden@test.dev", first_name="Hidden", is_listed=False
    )
    suspended = await add_astrologer(client, admin, email="gone@test.dev", first_name="Gone")

    # Suspending through the admin patch must also pull them from the directory.
    await client.patch(
        f"{P}/admin/astrologers/{suspended['id']}", headers=admin, json={"status": "suspended"}
    )

    ids = [item["id"] for item in (await listing(client))["items"]]
    assert ids == [visible["id"]]

    for gone in (hidden["id"], suspended["id"]):
        assert (await client.get(f"{P}/astrologers/{gone}")).status_code == 404


async def test_deactivating_also_hides(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    astrologer = await add_astrologer(client, admin, email="bye@test.dev")

    await client.delete(f"{P}/admin/astrologers/{astrologer['id']}", headers=admin)
    assert (await listing(client))["meta"]["total"] == 0


# ------------------------------------------------------------------ filters
async def test_search_matches_name_and_speciality(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    await add_astrologer(client, admin, email="a@test.dev", first_name="Ravi")
    await add_astrologer(
        client,
        admin,
        email="b@test.dev",
        first_name="Meera",
        specialisations=["Marriage matching"],
    )

    assert (await listing(client, search="ravi"))["meta"]["total"] == 1
    assert (await listing(client, search="RAVI"))["meta"]["total"] == 1  # case-insensitive
    assert (await listing(client, search="marriage"))["meta"]["total"] == 1
    assert (await listing(client, search="nobody"))["meta"]["total"] == 0


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"skill": "tarot"}, 1),
        ({"skill": "vedic_astrology"}, 1),
        ({"language": "Bengali"}, 1),
        ({"language": "Hindi"}, 2),
        ({"min_experience": 15}, 1),
        ({"max_rate": 25}, 1),
        ({"featured_only": True}, 1),
        ({"online_only": True}, 0),
    ],
)
async def test_filters(client: AsyncClient, sent_mail: list, params: dict, expected: int) -> None:
    admin = await make_admin(client)
    await add_astrologer(
        client,
        admin,
        email="vedic@test.dev",
        first_name="Vedic",
        skills=["vedic_astrology"],
        languages=["Hindi"],
        experience_years=20,
        rates={"chat_coins_per_minute": 50},
        is_featured=True,
    )
    await add_astrologer(
        client,
        admin,
        email="tarot@test.dev",
        first_name="Tarot",
        skills=["tarot"],
        languages=["Hindi", "Bengali"],
        experience_years=5,
        rates={"chat_coins_per_minute": 20},
    )

    assert (await listing(client, **params))["meta"]["total"] == expected


async def test_pagination(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    for n in range(3):
        await add_astrologer(client, admin, email=f"p{n}@test.dev", first_name=f"Astro{n}")

    first = await listing(client, page=1, limit=2)
    assert len(first["items"]) == 2
    assert first["meta"] == {
        "page": 1,
        "limit": 2,
        "total": 3,
        "total_pages": 2,
        "has_next": True,
        "has_prev": False,
    }

    second = await listing(client, page=2, limit=2)
    assert len(second["items"]) == 1
    assert second["meta"]["has_next"] is False
    assert second["meta"]["has_prev"] is True


# ------------------------------------------------------------------- detail
async def test_detail_by_slug_and_by_id(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    astrologer = await add_astrologer(client, admin, email="ravi.astro@test.dev")

    by_slug = await client.get(f"{P}/astrologers/ravi-sharma")
    assert by_slug.status_code == 200, by_slug.text
    assert by_slug.json()["data"]["id"] == astrologer["id"]

    by_id = await client.get(f"{P}/astrologers/{astrologer['id']}")
    assert by_id.status_code == 200
    assert by_id.json()["data"]["slug"] == "ravi-sharma"


async def test_me_is_not_treated_as_a_slug(client: AsyncClient) -> None:
    """`/astrologers/me` must reach the profile route, not the slug lookup."""
    response = await client.get(f"{P}/astrologers/me")
    assert response.status_code == 401  # missing token, not 404
    assert response.json()["error_code"] == "missing_token"


async def test_unknown_slug_is_a_404(client: AsyncClient) -> None:
    response = await client.get(f"{P}/astrologers/no-such-person")
    assert response.status_code == 404
    assert response.json()["error_code"] == "astrologer_not_found"


# ------------------------------------------------------------------- images
async def test_photo_and_gallery(
    client: AsyncClient, sent_mail: list, monkeypatch: pytest.MonkeyPatch
) -> None:
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
            url=f"https://cdn.test/img-{counter['n']}.webp",
            public_id=f"astro/pic-{counter['n']}",
            resource_type="image",
            format="webp",
            bytes=15_000,
            width=512,
            height=512,
            folder=folder,
        )

    async def fake_delete(public_id, resource_type="image"):  # noqa: ANN001
        deleted.append(public_id)
        return True

    monkeypatch.setattr(storage, "upload_file", fake_upload)
    monkeypatch.setattr(storage, "delete_file", fake_delete)

    admin = await make_admin(client)
    await add_astrologer(client, admin, email="ravi.astro@test.dev")
    signed_in = await client.post(
        f"{P}/auth/login",
        json={"email": "ravi.astro@test.dev", "password": sent_mail[-1]["password"]},
    )
    auth = {"Authorization": f"Bearer {signed_in.json()['data']['tokens']['access_token']}"}
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64

    # --- photo, compressed like a user avatar ---------------------------
    first = await client.post(
        f"{P}/astrologers/me/image", headers=auth, files={"file": ("a.png", png, "image/png")}
    )
    assert first.status_code == 200, first.text
    assert first.json()["data"]["profile_image_url"] == "https://cdn.test/img-1.webp"

    options = uploads[0]
    assert options["folder"] == "astrologers"
    assert options["image_format"] == settings.AVATAR_FORMAT
    assert options["transformation"][0]["crop"] == "limit"

    # Replacing deletes the old file.
    await client.post(
        f"{P}/astrologers/me/image", headers=auth, files={"file": ("b.png", png, "image/png")}
    )
    assert deleted == ["astro/pic-1"]

    removed = await client.delete(f"{P}/astrologers/me/image", headers=auth)
    assert removed.status_code == 200
    assert removed.json()["data"]["profile_image_url"] is None
    assert deleted == ["astro/pic-1", "astro/pic-2"]

    # --- gallery --------------------------------------------------------
    added = await client.post(
        f"{P}/astrologers/me/gallery", headers=auth, files={"file": ("g.png", png, "image/png")}
    )
    assert added.status_code == 201, added.text
    image = added.json()["data"]["image"]
    assert image["public_id"] == "astro/pic-3"
    assert len(added.json()["data"]["gallery"]) == 1

    gone = await client.delete(f"{P}/astrologers/me/gallery/{image['public_id']}", headers=auth)
    assert gone.status_code == 200
    assert "astro/pic-3" in deleted

    profile = await client.get(f"{P}/astrologers/me", headers=auth)
    assert profile.json()["data"]["gallery"] == []


async def test_removing_a_missing_photo_is_a_404(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    await add_astrologer(client, admin, email="ravi.astro@test.dev")
    signed_in = await client.post(
        f"{P}/auth/login",
        json={"email": "ravi.astro@test.dev", "password": sent_mail[-1]["password"]},
    )
    auth = {"Authorization": f"Bearer {signed_in.json()['data']['tokens']['access_token']}"}

    response = await client.delete(f"{P}/astrologers/me/image", headers=auth)
    assert response.status_code == 404
    assert response.json()["error_code"] == "no_profile_image"
