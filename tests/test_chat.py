"""Chats.

Messages live in MongoDB with the session, so these cover the whole thing: who
may open a chat, who may accept it, that a closed chat refuses new messages —
the one that matters most, since it is all that stands between a finished
session and two people still talking — and that the transcript is cleared up
afterwards on the schedule an admin chose.
"""

import pytest
from beanie import PydanticObjectId
from httpx import AsyncClient

from app.core.config import settings
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
        f"{P}/admin/astrologers",
        headers=admin,
        json={**BASE, "email": email, "modes_enabled": modes},
    )
    assert created.status_code == 201, created.text
    profile = created.json()["data"]["astrologer"]

    logged = await client.post(
        f"{P}/auth/login", json={"email": email, "password": mail[-1]["password"]}
    )
    auth = {"Authorization": f"Bearer {logged.json()['data']['tokens']['access_token']}"}
    if online:
        await client.patch(
            f"{P}/astrologers/me/availability", headers=auth, json={"is_online": True}
        )
    return profile, auth


async def _top_up(user: dict, coins: int = 10_000) -> None:
    """Puts coins in the asker's wallet.

    A chat is booked for a number of minutes and refused if the wallet cannot
    cover them, so every test that expects a chat to open has to be able to
    pay for it. Credited through the service rather than the admin API to keep
    this out of the way of what each test is actually about.
    """
    import uuid

    from app.core.security import decode_token
    from app.models.enums import TransactionReason
    from app.services import wallet as wallet_service

    token = user["Authorization"].removeprefix("Bearer ")
    user_id = decode_token(token)["sub"]
    await wallet_service.credit(
        user_id=PydanticObjectId(user_id),
        amount_coins=coins,
        reason=TransactionReason.ADJUSTMENT,
        idempotency_key=f"test-float:{uuid.uuid4()}",
    )


async def ask(client: AsyncClient, user: dict, astrologer_id: str, minutes: int = 5):
    """Books a chat, having first made sure the asker can afford it."""
    await _top_up(user)
    return await client.post(
        f"{P}/chats",
        headers=user,
        json={"astrologer_id": astrologer_id, "requested_minutes": minutes},
    )


# ------------------------------------------------------------- the happy path
async def test_a_chat_is_asked_for_accepted_and_ended(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    started = await ask(client, user, profile["id"])
    assert started.status_code == 201, started.text
    data = started.json()["data"]
    assert data["chat"]["status"] == "requested"
    assert data["chat"]["started_at"] is None

    chat_id = data["chat"]["id"]

    # Shut to messages until the astrologer says yes.
    too_early = await client.post(
        f"{P}/chats/{chat_id}/messages", headers=user, json={"text": "hello?"}
    )
    assert too_early.status_code == 400
    assert too_early.json()["error_code"] == "chat_not_active"
    incoming = (await client.get(f"{P}/chats/active", headers=astro)).json()["data"]
    assert incoming["chat"]["id"] == chat_id
    assert incoming["chat"]["peer"]["name"] == "Asker"

    accepted = await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    assert accepted.json()["data"]["chat"]["status"] == "active"

    # Now messages may flow, both ways.
    sent = await client.post(
        f"{P}/chats/{chat_id}/messages", headers=user, json={"text": "What does my chart say?"}
    )
    assert sent.status_code == 201, sent.text
    await client.post(
        f"{P}/chats/{chat_id}/messages", headers=astro, json={"text": "Let me look."}
    )

    transcript = (await client.get(f"{P}/chats/{chat_id}/messages", headers=user)).json()["data"]
    assert [m["text"] for m in transcript["messages"]] == [
        "What does my chart say?",
        "Let me look.",
    ]

    ended = await client.post(f"{P}/chats/{chat_id}/end", headers=user)
    assert ended.json()["data"]["status"] == "ended"

    # And now they may not — the refusal is the server's, not the browser's.
    after = await client.post(
        f"{P}/chats/{chat_id}/messages", headers=user, json={"text": "one more"}
    )
    assert after.status_code == 400
    assert after.json()["error_code"] == "chat_not_active"


async def test_a_stranger_cannot_read_or_write_the_transcript(
    client: AsyncClient, sent_mail: list
) -> None:
    """The only gate is this server, so it has to hold on every route."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)
    stranger = await signed_in(client, "nosy@test.dev")

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)

    peeked = await client.get(f"{P}/chats/{chat_id}/messages", headers=stranger)
    assert peeked.status_code == 403
    posted = await client.post(
        f"{P}/chats/{chat_id}/messages", headers=stranger, json={"text": "hi"}
    )
    assert posted.status_code == 403


async def test_ticks_follow_the_other_side(client: AsyncClient, sent_mail: list) -> None:
    """One marker per reader is what the double and blue ticks are drawn from."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    await client.post(f"{P}/chats/{chat_id}/messages", headers=user, json={"text": "hello"})

    await client.post(f"{P}/chats/{chat_id}/read", headers=astro, json={"level": "delivered"})
    transcript = (await client.get(f"{P}/chats/{chat_id}/messages", headers=user)).json()
    reads = transcript["data"]["reads"]
    assert len(reads) == 1 and reads[0]["delivered_at"] and reads[0]["read_at"] is None

    await client.post(f"{P}/chats/{chat_id}/read", headers=astro, json={"level": "read"})
    transcript = (await client.get(f"{P}/chats/{chat_id}/messages", headers=user)).json()
    reads = transcript["data"]["reads"]
    assert reads[0]["read_at"], "reading implies delivery, and moves the tick to blue"


# ------------------------------------------------------------ who may do what
async def test_only_the_astrologer_can_accept_or_decline(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    assert (await client.post(f"{P}/chats/{chat_id}/accept", headers=user)).status_code == 403
    assert (await client.post(f"{P}/chats/{chat_id}/decline", headers=user)).status_code == 403


async def test_a_stranger_cannot_see_the_chat(
    client: AsyncClient, sent_mail: list
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
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail, online=False)
    user = await signed_in(client)

    response = await ask(client, user, profile["id"])
    assert response.status_code == 400
    assert response.json()["error_code"] == "astrologer_offline"


async def test_an_astrologer_who_does_not_chat_cannot_be_asked(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail, chat=False)
    user = await signed_in(client)

    response = await ask(client, user, profile["id"])
    assert response.status_code == 400
    assert response.json()["error_code"] == "mode_not_offered"


async def test_a_paused_astrologer_cannot_be_asked(
    client: AsyncClient, sent_mail: list
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
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)
    other = await signed_in(client, "other@test.dev")

    assert (await ask(client, user, profile["id"])).status_code == 201
    assert (await ask(client, user, profile["id"])).json()["error_code"] == "already_in_chat"
    assert (await ask(client, other, profile["id"])).json()["error_code"] == "astrologer_busy"


# ------------------------------------------------------------- the other ends
async def test_declining_frees_both_sides(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    declined = await client.post(f"{P}/chats/{chat_id}/decline", headers=astro)

    assert declined.json()["data"]["status"] == "declined"
    assert (await ask(client, user, profile["id"])).status_code == 201


async def test_backing_out_before_it_starts_is_a_cancel(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    ended = await client.post(f"{P}/chats/{chat_id}/end", headers=user)
    assert ended.json()["data"]["status"] == "cancelled"


async def test_ending_a_chat_schedules_its_messages_for_removal(
    client: AsyncClient, sent_mail: list
) -> None:
    """Kept for the retention the admin set, then removed by MongoDB itself."""
    from app.models.chat import ChatMessage
    from app.services import settings as settings_service

    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    await client.post(f"{P}/chats/{chat_id}/messages", headers=user, json={"text": "hello"})

    # While it is open, nothing is dated to disappear.
    live = await ChatMessage.find_one(ChatMessage.session_id == PydanticObjectId(chat_id))
    assert live is not None and live.expires_at is None

    await client.post(f"{P}/chats/{chat_id}/end", headers=user)

    stored = await ChatMessage.find_one(ChatMessage.session_id == PydanticObjectId(chat_id))
    assert stored is not None, "still there — the retention has not passed"
    retention = (await settings_service.get_settings()).chat_retention_days
    assert stored.expires_at is not None
    assert (stored.expires_at - stored.sent_at).days >= retention - 1

    # The session keeps the count even once the messages are gone.
    after = (await client.get(f"{P}/chats/{chat_id}", headers=user)).json()["data"]["chat"]
    assert after["status"] == "ended"
    assert after["message_count"] == 1


async def test_zero_retention_deletes_the_transcript_at_once(
    client: AsyncClient, sent_mail: list
) -> None:
    """What an admin gets when they set the retention to nothing."""
    from app.models.chat import ChatMessage
    from app.services import settings as settings_service

    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    await settings_service.set_consultation_defaults(
        changes={"chat_retention_days": 0}, admin_id=None
    )

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    await client.post(f"{P}/chats/{chat_id}/messages", headers=user, json={"text": "hello"})
    await client.post(f"{P}/chats/{chat_id}/end", headers=user)

    left = await ChatMessage.find(ChatMessage.session_id == PydanticObjectId(chat_id)).count()
    assert left == 0


# -------------------------------------------------- chats nobody closes
async def test_an_unanswered_chat_becomes_missed(
    client: AsyncClient, sent_mail: list,
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


async def test_an_abandoned_chat_stops_accepting_messages(
    client: AsyncClient, sent_mail: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A chat nobody closed must not stay writable, or it would keep charging."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    user = await signed_in(client)

    chat_id = (await ask(client, user, profile["id"])).json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    assert (
        await client.post(f"{P}/chats/{chat_id}/messages", headers=user, json={"text": "hi"})
    ).status_code == 201

    monkeypatch.setattr(settings, "CHAT_IDLE_GRACE_SECONDS", 0)
    from app.services import chat as chat_service

    assert (await chat_service.sweep())["dropped"] == 1
    refused = await client.post(
        f"{P}/chats/{chat_id}/messages", headers=user, json={"text": "still here?"}
    )
    assert refused.status_code == 400


async def test_a_heartbeat_keeps_a_chat_open(
    client: AsyncClient, sent_mail: list,
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
    client: AsyncClient, sent_mail: list
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
