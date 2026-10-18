"""Chats.

Messages live in Firestore, so these tests cover everything *around* them: who
may open a chat, who may accept it, and — the one that matters most — that
ending a chat closes the Firestore conversation, because that is the only thing
standing between a finished session and two browsers that can still talk.
"""

import pytest
from httpx import AsyncClient

from app.core.config import settings
from tests.test_astrologer import BASE, make_admin

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


class FakeFirestore:
    """Stands in for Firestore. Records what the server told it to do."""

    def __init__(self) -> None:
        self.conversations: dict[str, dict] = {}
        self.tokens: list[str] = []

    async def create_conversation(self, *, conversation_id, participants, session_id):
        self.conversations[conversation_id] = {
            "participants": participants,
            "sessionId": session_id,
            "status": "pending",
        }

    async def set_status(self, conversation_id, status):
        self.conversations[conversation_id]["status"] = status

    async def count_messages(self, conversation_id):
        return 0

    async def delete_conversation(self, conversation_id):
        self.conversations.pop(conversation_id, None)

    async def mint_token(self, uid):
        self.tokens.append(uid)
        return f"custom-token-for-{uid}"

    def is_enabled(self):
        return True


@pytest.fixture
def fake_firestore(monkeypatch: pytest.MonkeyPatch) -> FakeFirestore:
    fake = FakeFirestore()
    import app.api.v1.chats as chats_api
    import app.services.chat as chat_service

    for module in (chat_service, chats_api):
        monkeypatch.setattr(module, "firestore", fake)
    return fake


@pytest.fixture
def sent_mail(monkeypatch: pytest.MonkeyPatch) -> list:
    captured: list = []
    import app.services.astrologer as astrologer_service

    async def fake_send(to: str, name: str, password: str) -> bool:
        captured.append({"to": to, "password": password})
        return True

    monkeypatch.setattr(astrologer_service, "send_astrologer_welcome_email", fake_send)
    return captured


async def signed_in(client: AsyncClient, email: str = "asker@test.dev") -> dict:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": "secret123", "first_name": "Asker"},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    assert created.status_code == 201, created.text
    return {"Authorization": f"Bearer {created.json()['data']['tokens']['access_token']}"}


async def make_astrologer(
    client: AsyncClient, admin: dict, mail: list, *, email: str = "ravi.astro@test.dev",
    online: bool = True, chat: bool = True,
) -> tuple[dict, dict]:
    modes = (["chat"] if chat else []) + ["call", "video"]
    created = await client.post(
        f"{P}/admin/astrologers", headers=admin, json={**BASE, "email": email, "modes_enabled": modes}
    )
    assert created.status_code == 201, created.text
    profile = created.json()["data"]["astrologer"]

    logged = await client.post(
        f"{P}/auth/login", json={"email": email, "password": mail[-1]["password"]}
    )
    auth = {"Authorization": f"Bearer {logged.json()['data']['tokens']['access_token']}"}
    if online:
        await client.patch(f"{P}/astrologers/me/availability", headers=auth, json={"is_online": True})
    return profile, auth


async def ask(client: AsyncClient, user: dict, astrologer_id: str):
    return await client.post(f"{P}/chats", headers=user, json={"astrologer_id": astrologer_id})


# ------------------------------------------------------------- the happy path
async def test_a_chat_is_asked_for_accepted_and_ended(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    started = await ask(client, user, profile["id"])
    assert started.status_code == 201, started.text
    data = started.json()["data"]
    assert data["chat"]["status"] == "requested"
    assert data["chat"]["started_at"] is None

    convo = data["chat"]["conversation_id"]
    # Opened, but shut to messages until the astrologer says yes.
    assert fake_firestore.conversations[convo]["status"] == "pending"
    assert len(fake_firestore.conversations[convo]["participants"]) == 2

    # The browser gets what it needs to reach Firestore as itself.
    assert data["firebase"]["custom_token"].startswith("custom-token-for-")
    assert data["firebase"]["uid"]

    chat_id = data["chat"]["id"]
    incoming = (await client.get(f"{P}/chats/active", headers=astro)).json()["data"]
    assert incoming["chat"]["id"] == chat_id
    assert incoming["chat"]["peer"]["name"] == "Asker"

    accepted = await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    assert accepted.json()["data"]["chat"]["status"] == "active"
    assert fake_firestore.conversations[convo]["status"] == "active", "now messages may flow"

    ended = await client.post(f"{P}/chats/{chat_id}/end", headers=user)
    assert ended.json()["data"]["status"] == "ended"
    assert fake_firestore.conversations[convo]["status"] == "ended", "and now they may not"


async def test_each_side_is_given_its_own_firebase_identity(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    mine = (await ask(client, user, profile["id"])).json()["data"]
    theirs = (await client.get(f"{P}/chats/active", headers=astro)).json()["data"]

    assert mine["firebase"]["uid"] != theirs["firebase"]["uid"]
    assert mine["firebase"]["custom_token"] != theirs["firebase"]["custom_token"]


# ------------------------------------------------------------ who may do what
async def test_only_the_astrologer_can_accept_or_decline(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    assert (await client.post(f"{P}/chats/{chat_id}/accept", headers=user)).status_code == 403
    assert (await client.post(f"{P}/chats/{chat_id}/decline", headers=user)).status_code == 403


async def test_a_stranger_cannot_see_the_chat(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)
    stranger = await signed_in(client, "stranger@test.dev")

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    assert (await client.get(f"{P}/chats/{chat_id}", headers=stranger)).status_code == 403
    assert (await client.post(f"{P}/chats/{chat_id}/end", headers=stranger)).status_code == 403


async def test_a_chat_needs_a_signed_in_user(client: AsyncClient) -> None:
    assert (await client.post(f"{P}/chats", json={"astrologer_id": "x"})).status_code == 401


# --------------------------------------------------------- when it is refused
async def test_an_offline_astrologer_cannot_be_asked(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail, online=False)
    user = await signed_in(client)

    response = await ask(client, user, profile["id"])
    assert response.status_code == 400
    assert response.json()["error_code"] == "astrologer_offline"


async def test_an_astrologer_who_does_not_chat_cannot_be_asked(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail, chat=False)
    user = await signed_in(client)

    response = await ask(client, user, profile["id"])
    assert response.status_code == 400
    assert response.json()["error_code"] == "mode_not_offered"


async def test_a_paused_astrologer_cannot_be_asked(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    await client.patch(
        f"{P}/astrologers/me/availability", headers=astro, json={"is_available_for_chat": False}
    )
    response = await ask(client, user, profile["id"])
    assert response.status_code == 400
    assert response.json()["error_code"] == "mode_paused"


async def test_only_one_chat_at_a_time(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)
    other = await signed_in(client, "other@test.dev")

    assert (await ask(client, user, profile["id"])).status_code == 201
    assert (await ask(client, user, profile["id"])).json()["error_code"] == "already_in_chat"
    assert (await ask(client, other, profile["id"])).json()["error_code"] == "astrologer_busy"


async def test_a_failed_conversation_leaves_no_session_behind(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore, monkeypatch
) -> None:
    """Otherwise both people would look busy over a chat that never existed."""
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    async def boom(**kwargs):
        raise RuntimeError("firestore down")

    monkeypatch.setattr(fake_firestore, "create_conversation", boom)
    refused = await ask(client, user, profile["id"])
    assert refused.status_code == 503
    assert refused.json()["error_code"] == "chat_unavailable"

    monkeypatch.undo()
    # Nothing is stuck: a fresh attempt works.
    assert (await ask(client, user, profile["id"])).status_code == 201


# ------------------------------------------------------------- the other ends
async def test_declining_frees_both_sides(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    declined = await client.post(f"{P}/chats/{chat_id}/decline", headers=astro)

    assert declined.json()["data"]["status"] == "declined"
    assert (await ask(client, user, profile["id"])).status_code == 201


async def test_backing_out_before_it_starts_is_a_cancel(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    ended = await client.post(f"{P}/chats/{chat_id}/end", headers=user)
    assert ended.json()["data"]["status"] == "cancelled"


async def test_a_finished_chat_hands_out_no_firebase_token(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    """No token means the browser cannot even sign in to read the room again."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    await client.post(f"{P}/chats/{chat_id}/end", headers=user)

    after = (await client.get(f"{P}/chats/{chat_id}", headers=user)).json()["data"]
    assert after["chat"]["status"] == "ended"
    assert after["firebase"] is None


# -------------------------------------------------- chats nobody closes
async def test_an_unanswered_chat_becomes_missed(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    monkeypatch.setattr(settings, "CHAT_REQUEST_TIMEOUT_SECONDS", 0)

    from app.services import chat as chat_service

    assert (await chat_service.sweep())["missed"] == 1
    after = (await client.get(f"{P}/chats/{chat_id}", headers=user)).json()["data"]["chat"]
    assert after["status"] == "missed"


async def test_an_abandoned_chat_is_closed_in_firestore_too(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Closing it only in MongoDB would leave two browsers still able to talk."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    data = (await ask(client, user, profile["id"])).json()["data"]
    chat_id, convo = data["chat"]["id"], data["chat"]["conversation_id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    assert fake_firestore.conversations[convo]["status"] == "active"

    monkeypatch.setattr(settings, "CHAT_IDLE_GRACE_SECONDS", 0)
    from app.services import chat as chat_service

    assert (await chat_service.sweep())["dropped"] == 1
    assert fake_firestore.conversations[convo]["status"] == "ended"


async def test_a_heartbeat_keeps_a_chat_open(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    await client.post(f"{P}/chats/{chat_id}/heartbeat", headers=user)

    monkeypatch.setattr(settings, "CHAT_IDLE_GRACE_SECONDS", 600)
    from app.services import chat as chat_service

    assert (await chat_service.sweep())["dropped"] == 0


async def test_the_chat_sweeper_is_not_public(client: AsyncClient) -> None:
    assert (await client.post(f"{P}/internal/chats/sweep")).status_code == 403
    allowed = await client.post(
        f"{P}/internal/chats/sweep", headers={"X-Internal-Key": settings.SECRET_KEY}
    )
    assert allowed.status_code == 200


async def test_history_shows_both_sides_their_chats(
    client: AsyncClient, sent_mail: list, fake_firestore: FakeFirestore
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    await client.post(f"{P}/chats/{chat_id}/end", headers=user)

    mine = (await client.get(f"{P}/chats/history", headers=user)).json()["data"]
    theirs = (await client.get(f"{P}/chats/history", headers=astro)).json()["data"]
    assert mine["meta"]["total"] == 1 and theirs["meta"]["total"] == 1
    assert mine["items"][0]["peer"]["name"] == "Ravi Sharma"
    assert theirs["items"][0]["peer"]["name"] == "Asker"
