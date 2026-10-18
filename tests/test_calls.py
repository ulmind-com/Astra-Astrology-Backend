"""One-to-one video calls.

The tests that matter are the ones about who is allowed to do what, and about
calls nobody closes: a tab that disappears mid-call must not leave two people
marked busy forever.
"""

import pytest
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


async def signed_in(client: AsyncClient, email: str = "caller@test.dev") -> dict:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": "secret123", "first_name": "Caller"},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    assert created.status_code == 201, created.text
    return {"Authorization": f"Bearer {created.json()['data']['tokens']['access_token']}"}


async def make_astrologer(
    client: AsyncClient,
    admin: dict,
    mail: list,
    *,
    email: str = "ravi.astro@test.dev",
    online: bool = True,
    video: bool = True,
) -> tuple[dict, dict]:
    """Creates an astrologer, signs them in, and sets them up to take calls."""
    modes = ["chat", "call"] + (["video"] if video else [])
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


async def ring(client: AsyncClient, caller: dict, astrologer_id: str):
    return await client.post(
        f"{P}/calls", headers=caller, json={"astrologer_id": astrologer_id, "mode": "video"}
    )


# ------------------------------------------------------------- the happy path
async def test_a_call_rings_connects_and_ends(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    started = await ring(client, caller, profile["id"])
    assert started.status_code == 201, started.text
    data = started.json()["data"]
    assert data["call"]["status"] == "ringing"
    assert data["call"]["started_at"] is None, "ringing is not talking"

    creds = data["credentials"]
    assert creds["app_id"] == settings.ZEGO_APP_ID
    assert creds["room_id"] == data["call"]["room_id"]
    assert creds["token"].startswith("04")
    assert "secret" not in str(creds).lower(), "the server secret must never ship"

    call_id = data["call"]["id"]

    # The astrologer sees it waiting.
    incoming = (await client.get(f"{P}/calls/active", headers=astro)).json()["data"]
    assert incoming["call"]["id"] == call_id
    assert incoming["call"]["peer"]["name"] == "Caller"

    accepted = await client.post(f"{P}/calls/{call_id}/accept", headers=astro)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["data"]["call"]["status"] == "active"
    assert accepted.json()["data"]["call"]["started_at"] is not None
    assert accepted.json()["data"]["credentials"]["token"].startswith("04")

    ended = await client.post(f"{P}/calls/{call_id}/end", headers=caller)
    assert ended.status_code == 200, ended.text
    assert ended.json()["data"]["status"] == "ended"
    assert ended.json()["data"]["ended_by"] == "user"


async def test_each_side_gets_its_own_token_for_the_same_room(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    started = (await ring(client, caller, profile["id"])).json()["data"]
    accepted = (
        await client.post(f"{P}/calls/{started['call']['id']}/accept", headers=astro)
    ).json()["data"]

    from app.services.zego import decode_token

    mine = decode_token(started["credentials"]["token"])
    theirs = decode_token(accepted["credentials"]["token"])

    assert mine["payload"]["room_id"] == theirs["payload"]["room_id"]
    assert mine["user_id"] != theirs["user_id"], "a token is per person"
    assert mine["user_id"] == started["call"]["user_id"]


# ----------------------------------------------------------- who may do what
async def test_only_the_astrologer_can_answer(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]

    # The caller answering their own call would let them start the clock.
    assert (await client.post(f"{P}/calls/{call_id}/accept", headers=caller)).status_code == 403
    assert (await client.post(f"{P}/calls/{call_id}/decline", headers=caller)).status_code == 403


async def test_a_stranger_cannot_see_or_join_the_call(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)
    stranger = await signed_in(client, "stranger@test.dev")

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]

    assert (await client.get(f"{P}/calls/{call_id}", headers=stranger)).status_code == 403
    assert (await client.post(f"{P}/calls/{call_id}/end", headers=stranger)).status_code == 403


async def test_a_call_needs_a_signed_in_user(client: AsyncClient) -> None:
    assert (await client.post(f"{P}/calls", json={"astrologer_id": "x"})).status_code == 401


# ------------------------------------------------------ when calling is refused
async def test_an_offline_astrologer_cannot_be_called(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail, online=False)
    caller = await signed_in(client)

    response = await ring(client, caller, profile["id"])
    assert response.status_code == 400
    assert response.json()["error_code"] == "astrologer_offline"


async def test_a_voice_call_uses_the_same_flow_as_video(
    client: AsyncClient, sent_mail: list
) -> None:
    """Voice and video are one session down one room; only the camera differs,
    and that is the client's choice, not the server's."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    started = await client.post(
        f"{P}/calls", headers=caller, json={"astrologer_id": profile["id"], "mode": "call"}
    )
    assert started.status_code == 201, started.text
    data = started.json()["data"]
    assert data["call"]["mode"] == "call"
    assert data["credentials"]["token"].startswith("04")

    call_id = data["call"]["id"]
    accepted = await client.post(f"{P}/calls/{call_id}/accept", headers=astro)
    assert accepted.json()["data"]["call"]["status"] == "active"

    ended = await client.post(f"{P}/calls/{call_id}/end", headers=caller)
    assert ended.json()["data"]["status"] == "ended"


async def test_a_voice_call_is_refused_when_calls_are_paused(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    await client.patch(
        f"{P}/astrologers/me/availability", headers=astro, json={"is_available_for_call": False}
    )

    response = await client.post(
        f"{P}/calls", headers=caller, json={"astrologer_id": profile["id"], "mode": "call"}
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "mode_paused"

    # Video is a separate switch and still works.
    assert (await ring(client, caller, profile["id"])).status_code == 201


async def test_chat_cannot_be_dialled(client: AsyncClient, sent_mail: list) -> None:
    """Chat is a conversation, not a call, so it does not open a room."""
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    response = await client.post(
        f"{P}/calls", headers=caller, json={"astrologer_id": profile["id"], "mode": "chat"}
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "mode_unavailable"


async def test_an_astrologer_who_does_not_do_video_cannot_be_called(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail, video=False)
    caller = await signed_in(client)

    response = await ring(client, caller, profile["id"])
    assert response.status_code == 400
    assert response.json()["error_code"] == "mode_not_offered"


async def test_a_second_call_is_refused_while_one_is_live(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    assert (await ring(client, caller, profile["id"])).status_code == 201
    second = await ring(client, caller, profile["id"])
    assert second.status_code == 409
    assert second.json()["error_code"] == "already_in_call"


async def test_a_busy_astrologer_cannot_be_called_by_someone_else(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    first = await signed_in(client, "first@test.dev")
    second = await signed_in(client, "second@test.dev")

    assert (await ring(client, first, profile["id"])).status_code == 201

    response = await ring(client, second, profile["id"])
    assert response.status_code == 409
    assert response.json()["error_code"] == "astrologer_busy"


# ------------------------------------------------------------- the other ends
async def test_the_astrologer_can_decline(client: AsyncClient, sent_mail: list) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]
    declined = await client.post(f"{P}/calls/{call_id}/decline", headers=astro)

    assert declined.json()["data"]["status"] == "declined"
    assert declined.json()["data"]["duration_seconds"] == 0

    # And both are free to call again.
    assert (await ring(client, caller, profile["id"])).status_code == 201


async def test_hanging_up_while_ringing_is_a_cancel_not_a_call(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]
    ended = await client.post(f"{P}/calls/{call_id}/end", headers=caller)

    assert ended.json()["data"]["status"] == "cancelled"


async def test_ending_twice_is_not_an_error(client: AsyncClient, sent_mail: list) -> None:
    """Both sides press the red button at once."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    first = await client.post(f"{P}/calls/{call_id}/end", headers=caller)
    second = await client.post(f"{P}/calls/{call_id}/end", headers=astro)

    assert first.status_code == 200 and second.status_code == 200
    assert second.json()["data"]["ended_by"] == "user", "the first hang-up stands"


async def test_a_finished_call_hands_out_no_token(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)
    await client.post(f"{P}/calls/{call_id}/end", headers=caller)

    after = (await client.get(f"{P}/calls/{call_id}", headers=caller)).json()["data"]
    assert after["call"]["status"] == "ended"
    assert after["credentials"] is None, "no way back into a closed room"


# ---------------------------------------------------- calls nobody closes
async def test_an_unanswered_call_becomes_missed(
    client: AsyncClient, sent_mail: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]

    monkeypatch.setattr(settings, "CALL_RING_TIMEOUT_SECONDS", 0)
    from app.services import call as call_service

    assert (await call_service.sweep())["missed"] == 1

    after = (await client.get(f"{P}/calls/{call_id}", headers=caller)).json()["data"]["call"]
    assert after["status"] == "missed"
    assert after["ended_by"] == "system"


async def test_a_call_both_sides_abandoned_is_closed(
    client: AsyncClient, sent_mail: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A closed laptop sends no "end" — without this the pair stay busy forever."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    monkeypatch.setattr(settings, "CALL_HEARTBEAT_GRACE_SECONDS", 0)
    from app.services import call as call_service

    assert (await call_service.sweep())["dropped"] == 1

    after = (await client.get(f"{P}/calls/{call_id}", headers=caller)).json()["data"]["call"]
    assert after["status"] == "ended"
    assert after["ended_by"] == "system"

    # And the astrologer is reachable again.
    assert (await ring(client, caller, profile["id"])).status_code == 201


async def test_a_heartbeat_keeps_a_call_alive(
    client: AsyncClient, sent_mail: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)
    await client.post(f"{P}/calls/{call_id}/heartbeat", headers=caller)

    monkeypatch.setattr(settings, "CALL_HEARTBEAT_GRACE_SECONDS", 600)
    from app.services import call as call_service

    assert (await call_service.sweep())["dropped"] == 0

    after = (await client.get(f"{P}/calls/{call_id}", headers=caller)).json()["data"]["call"]
    assert after["status"] == "active"


async def test_a_call_cannot_run_past_the_maximum(
    client: AsyncClient, sent_mail: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    monkeypatch.setattr(settings, "CALL_MAX_DURATION_SECONDS", 0)
    from app.services import call as call_service

    assert (await call_service.sweep())["capped"] == 1

    after = (await client.get(f"{P}/calls/{call_id}", headers=caller)).json()["data"]["call"]
    assert after["status"] == "ended"
    assert "maximum" in (after["end_reason"] or "")


async def test_the_sweeper_is_not_open_to_the_public(client: AsyncClient) -> None:
    assert (await client.post(f"{P}/internal/calls/sweep")).status_code == 403
    assert (
        await client.post(f"{P}/internal/calls/sweep", headers={"X-Internal-Key": "guess"})
    ).status_code == 403
    allowed = await client.post(
        f"{P}/internal/calls/sweep", headers={"X-Internal-Key": settings.SECRET_KEY}
    )
    assert allowed.status_code == 200


# ----------------------------------------------------------------- history
async def test_history_shows_both_sides_their_own_calls(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    caller = await signed_in(client)

    call_id = (await ring(client, caller, profile["id"])).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)
    await client.post(f"{P}/calls/{call_id}/end", headers=caller)

    mine = (await client.get(f"{P}/calls/history", headers=caller)).json()["data"]
    theirs = (await client.get(f"{P}/calls/history", headers=astro)).json()["data"]

    assert mine["meta"]["total"] == 1
    assert theirs["meta"]["total"] == 1
    assert mine["items"][0]["id"] == theirs["items"][0]["id"]
    # Each sees the other person.
    assert mine["items"][0]["peer"]["name"] == "Ravi Sharma"
    assert theirs["items"][0]["peer"]["name"] == "Caller"
