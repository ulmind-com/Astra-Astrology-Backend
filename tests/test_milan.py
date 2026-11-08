"""The multi-party Vedic chamber.

The tests that matter here are the ones about money and about who gets in.
A guest must never be charged, never be able to spend the host's coins, and
never be able to pass their invitation around; and a chamber nobody is left
in must not keep billing the person who opened it.
"""

import pytest
from httpx import AsyncClient

from app.models.milan import MilanRoom
from tests.test_astrologer import make_admin
from tests.test_calls import make_astrologer, signed_in, top_up

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")


@pytest.fixture
def sent_mail(monkeypatch: pytest.MonkeyPatch) -> list:
    """Catches the generated password instead of emailing it."""
    captured: list = []
    import app.services.astrologer as astrologer_service

    async def fake_send(to: str, name: str, password: str) -> bool:
        captured.append({"to": to, "password": password})
        return True

    monkeypatch.setattr(astrologer_service, "send_astrologer_welcome_email", fake_send)
    return captured


async def open_chamber(
    client: AsyncClient,
    host: dict,
    astrologer_id: str,
    *,
    guests: list[str] | None = None,
    minutes: int = 10,
):
    await top_up(host)
    return await client.post(
        f"{P}/milan",
        headers=host,
        json={
            "astrologer_id": astrologer_id,
            "mode": "video",
            "purpose": "kundali_matching",
            "requested_minutes": minutes,
            "guests": guests if guests is not None else ["Bride", "Bride's father"],
        },
    )


async def _chamber(client: AsyncClient, mail: list, **kwargs):
    """A host, an astrologer and an open chamber between them."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, mail)
    host = await signed_in(client, "milanhost@test.dev")

    opened = await open_chamber(client, host, profile["id"], **kwargs)
    assert opened.status_code == 201, opened.text
    return host, astro, opened.json()["data"]


# --------------------------------------------------------- opening a room
async def test_a_chamber_opens_with_a_seat_for_every_guest(
    client: AsyncClient, sent_mail: list
) -> None:
    host, _, data = await _chamber(client, sent_mail)
    room = data["room"]

    assert room["status"] == "ringing"
    assert room["purpose"] == "kundali_matching"
    assert room["viewer_is_host"] is True
    assert room["seats_taken"] == 2
    assert [s["label"] for s in room["seats"]] == ["Bride", "Bride's father"]
    # Every seat carries its own invitation, and no two are the same.
    codes = [s["join_code"] for s in room["seats"]]
    assert all(len(c) >= 24 for c in codes), "an invitation is the whole credential"
    assert len(set(codes)) == 2

    creds = data["credentials"]
    assert creds["room_id"].startswith("milan_")
    assert creds["token"].startswith("04")
    assert "secret" not in str(creds).lower(), "the server secret must never ship"


async def test_more_guests_than_the_chamber_seats_is_refused(
    client: AsyncClient, sent_mail: list
) -> None:
    """Two limits, and both have to hold.

    The configured limit is what an admin sets and the service enforces; the
    ceiling in the schema is the absurd-input guard that stops a request
    from ever reaching it.
    """
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    host = await signed_in(client, "milanhost@test.dev")

    # One past the configured limit of three.
    over = await open_chamber(
        client, host, profile["id"], guests=[f"Guest {i}" for i in range(4)]
    )
    assert over.status_code == 400, over.text
    assert over.json()["error_code"] == "too_many_guests"

    # Well past the hard ceiling: refused before any of that runs.
    absurd = await open_chamber(
        client, host, profile["id"], guests=[f"Guest {i}" for i in range(9)]
    )
    assert absurd.status_code == 422, absurd.text


async def test_an_empty_wallet_cannot_open_a_chamber(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    host = await signed_in(client, "milanbroke@test.dev")

    # Deliberately not topped up.
    resp = await client.post(
        f"{P}/milan",
        headers=host,
        json={
            "astrologer_id": profile["id"],
            "mode": "video",
            "purpose": "kundali_matching",
            "requested_minutes": 10,
            "guests": ["Bride"],
        },
    )
    assert resp.status_code == 400, resp.text


async def test_nobody_is_in_two_consultations_at_once(
    client: AsyncClient, sent_mail: list
) -> None:
    """A chamber and a 1:1 call must block each other, both ways."""
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)
    host = await signed_in(client, "milanhost@test.dev")

    opened = await open_chamber(client, host, profile["id"])
    assert opened.status_code == 201, opened.text

    # The host cannot now ring the same astrologer 1:1 ...
    rung = await client.post(
        f"{P}/calls",
        headers=host,
        json={"astrologer_id": profile["id"], "mode": "video", "requested_minutes": 5},
    )
    assert rung.status_code == 409, rung.text
    assert rung.json()["error_code"] in ("already_in_room", "astrologer_busy")

    # ... nor open a second chamber.
    again = await open_chamber(client, host, profile["id"])
    assert again.status_code == 409, again.text


# ------------------------------------------------------------- the guests
async def test_a_guest_joins_with_their_invitation_and_no_account(
    client: AsyncClient, sent_mail: list
) -> None:
    host, astro, data = await _chamber(client, sent_mail)
    room_id = data["room"]["id"]
    code = data["room"]["seats"][0]["join_code"]

    accepted = await client.post(f"{P}/milan/{room_id}/accept", headers=astro)
    assert accepted.status_code == 200, accepted.text

    # No Authorization header at all: this is the bride's father on a link.
    joined = await client.post(
        f"{P}/milan/guest/join", json={"join_code": code, "display_name": "Sujata"}
    )
    assert joined.status_code == 200, joined.text
    body = joined.json()["data"]

    assert body["room"]["viewer_is_guest"] is True
    assert body["credentials"]["token"].startswith("04")
    assert body["credentials"]["room_id"] == data["credentials"]["room_id"], (
        "a guest must land in the host's room, not a new one"
    )
    assert body["credentials"]["user_id"] != str(room_id)
    occupant = next(o for o in body["room"]["occupants"] if o["label"] == "Bride")
    assert occupant["display_name"] == "Sujata"
    assert occupant["is_present"] is True


async def test_a_guest_never_sees_the_invitations_or_the_bill(
    client: AsyncClient, sent_mail: list
) -> None:
    host, astro, data = await _chamber(client, sent_mail)
    code = data["room"]["seats"][0]["join_code"]
    await client.post(f"{P}/milan/{data['room']['id']}/accept", headers=astro)

    joined = await client.post(f"{P}/milan/guest/join", json={"join_code": code})
    room = joined.json()["data"]["room"]

    assert room["seats"] == [], "codes belong to the host alone"
    assert room["billing"] is None, "a guest is not the one paying"
    assert code not in joined.text


async def test_one_invitation_admits_one_person(
    client: AsyncClient, sent_mail: list
) -> None:
    """A forwarded link must not multiply the room."""
    host, astro, data = await _chamber(client, sent_mail)
    code = data["room"]["seats"][0]["join_code"]
    await client.post(f"{P}/milan/{data['room']['id']}/accept", headers=astro)

    first = await client.post(f"{P}/milan/guest/join", json={"join_code": code})
    assert first.status_code == 200, first.text

    second = await client.post(
        f"{P}/milan/guest/join", json={"join_code": code, "display_name": "Someone else"}
    )
    assert second.status_code == 409, second.text
    assert second.json()["error_code"] == "seat_taken"


async def test_a_seat_frees_up_when_its_guest_leaves(
    client: AsyncClient, sent_mail: list
) -> None:
    host, astro, data = await _chamber(client, sent_mail)
    code = data["room"]["seats"][0]["join_code"]
    await client.post(f"{P}/milan/{data['room']['id']}/accept", headers=astro)

    await client.post(f"{P}/milan/guest/join", json={"join_code": code})
    left = await client.post(f"{P}/milan/guest/leave", json={"join_code": code})
    assert left.status_code == 200, left.text

    again = await client.post(f"{P}/milan/guest/join", json={"join_code": code})
    assert again.status_code == 200, again.text


async def test_a_cancelled_invitation_stops_working(
    client: AsyncClient, sent_mail: list
) -> None:
    host, astro, data = await _chamber(client, sent_mail)
    room_id = data["room"]["id"]
    seat = data["room"]["seats"][0]
    await client.post(f"{P}/milan/{room_id}/accept", headers=astro)

    revoked = await client.delete(
        f"{P}/milan/{room_id}/seats/{seat['seat_id']}", headers=host
    )
    assert revoked.status_code == 200, revoked.text

    blocked = await client.post(
        f"{P}/milan/guest/join", json={"join_code": seat["join_code"]}
    )
    assert blocked.status_code == 403, blocked.text
    assert blocked.json()["error_code"] == "invite_revoked"


async def test_an_invitation_dies_with_the_chamber(
    client: AsyncClient, sent_mail: list
) -> None:
    """A link in a family group must not reopen last week's consultation."""
    host, astro, data = await _chamber(client, sent_mail)
    room_id = data["room"]["id"]
    code = data["room"]["seats"][0]["join_code"]

    await client.post(f"{P}/milan/{room_id}/accept", headers=astro)
    ended = await client.post(f"{P}/milan/{room_id}/end", headers=host)
    assert ended.status_code == 200, ended.text

    blocked = await client.post(f"{P}/milan/guest/join", json={"join_code": code})
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["error_code"] == "milan_over"


async def test_a_made_up_invitation_is_not_found(client: AsyncClient) -> None:
    resp = await client.post(
        f"{P}/milan/guest/join", json={"join_code": "definitely-not-a-real-code"}
    )
    assert resp.status_code == 404, resp.text


async def test_a_guest_can_check_in_without_a_bearer_token(
    client: AsyncClient, sent_mail: list
) -> None:
    """Regression: /milan/guest/heartbeat was being captured by
    /milan/{room_id}/heartbeat, so a guest's seat expired mid-consultation."""
    host, astro, data = await _chamber(client, sent_mail)
    code = data["room"]["seats"][0]["join_code"]
    await client.post(f"{P}/milan/{data['room']['id']}/accept", headers=astro)
    await client.post(f"{P}/milan/guest/join", json={"join_code": code})

    beat = await client.post(f"{P}/milan/guest/heartbeat", json={"join_code": code})
    assert beat.status_code == 200, beat.text


# -------------------------------------------------------------- authority
async def test_only_the_host_invites_and_cancels(
    client: AsyncClient, sent_mail: list
) -> None:
    host, astro, data = await _chamber(client, sent_mail)
    room_id = data["room"]["id"]
    seat_id = data["room"]["seats"][0]["seat_id"]

    added = await client.post(
        f"{P}/milan/{room_id}/seats", headers=astro, json={"label": "Nobody"}
    )
    assert added.status_code == 403, added.text
    assert added.json()["error_code"] == "not_the_host"

    revoked = await client.delete(f"{P}/milan/{room_id}/seats/{seat_id}", headers=astro)
    assert revoked.status_code == 403, revoked.text


async def test_only_the_host_can_spend_more(
    client: AsyncClient, sent_mail: list
) -> None:
    host, astro, data = await _chamber(client, sent_mail)
    room_id = data["room"]["id"]
    await client.post(f"{P}/milan/{room_id}/accept", headers=astro)

    theirs = await client.post(
        f"{P}/milan/{room_id}/extend?extra_minutes=5", headers=astro
    )
    assert theirs.status_code == 403, theirs.text

    mine = await client.post(f"{P}/milan/{room_id}/extend?extra_minutes=5", headers=host)
    assert mine.status_code == 200, mine.text
    assert mine.json()["data"]["billing"]["minutes_booked"] == 15


async def test_an_outsider_cannot_read_the_chamber(
    client: AsyncClient, sent_mail: list
) -> None:
    host, astro, data = await _chamber(client, sent_mail)
    outsider = await signed_in(client, "nosy@test.dev")

    resp = await client.get(f"{P}/milan/{data['room']['id']}", headers=outsider)
    assert resp.status_code == 403, resp.text
    assert resp.json()["error_code"] == "not_your_milan"


async def test_the_host_cannot_accept_their_own_chamber(
    client: AsyncClient, sent_mail: list
) -> None:
    host, _, data = await _chamber(client, sent_mail)
    resp = await client.post(f"{P}/milan/{data['room']['id']}/accept", headers=host)
    assert resp.status_code == 403, resp.text


async def test_a_seat_can_be_added_up_to_the_limit(
    client: AsyncClient, sent_mail: list
) -> None:
    host, _, data = await _chamber(client, sent_mail, guests=["Bride"])
    room_id = data["room"]["id"]

    for label in ("Groom's mother", "Bride's father"):
        added = await client.post(
            f"{P}/milan/{room_id}/seats", headers=host, json={"label": label}
        )
        assert added.status_code == 201, added.text

    full = await client.post(
        f"{P}/milan/{room_id}/seats", headers=host, json={"label": "One too many"}
    )
    assert full.status_code == 400, full.text
    assert full.json()["error_code"] == "chamber_full"


# ------------------------------------------------------------------ money
async def test_the_clock_starts_only_when_the_astrologer_joins(
    client: AsyncClient, sent_mail: list
) -> None:
    host, astro, data = await _chamber(client, sent_mail)
    room_id = data["room"]["id"]

    assert data["room"]["started_at"] is None
    beat = await client.post(f"{P}/milan/{room_id}/heartbeat", headers=host)
    assert beat.json()["data"]["billing"]["coins_charged"] == 0, (
        "nobody pays while the chamber is still ringing"
    )

    accepted = await client.post(f"{P}/milan/{room_id}/accept", headers=astro)
    assert accepted.json()["data"]["room"]["started_at"] is not None


async def test_guests_are_never_charged_and_the_host_pays_one_rate(
    client: AsyncClient, sent_mail: list
) -> None:
    """Three people in the room, one bill, and it is the host's."""
    from beanie import PydanticObjectId

    from app.core.security import decode_token
    from app.services import wallet as wallet_service

    host, astro, data = await _chamber(client, sent_mail)
    room_id = data["room"]["id"]
    codes = [s["join_code"] for s in data["room"]["seats"]]

    await client.post(f"{P}/milan/{room_id}/accept", headers=astro)
    for code in codes:
        joined = await client.post(f"{P}/milan/guest/join", json={"join_code": code})
        assert joined.status_code == 200, joined.text

    host_id = PydanticObjectId(decode_token(host["Authorization"].removeprefix("Bearer "))["sub"])
    before = (await wallet_service.get_or_create_wallet(host_id)).balance_coins

    # Guests checking in must not move any money.
    for code in codes:
        await client.post(f"{P}/milan/guest/heartbeat", json={"join_code": code})

    after = (await wallet_service.get_or_create_wallet(host_id)).balance_coins
    assert after == before, "a guest's check-in is not a billable event"

    room = await MilanRoom.get(PydanticObjectId(room_id))
    assert room is not None
    assert room.coins_charged == 0, "no whole minute has passed yet"
    assert room.host_user_id == host_id


async def test_the_chamber_closes_when_the_host_stops_responding(
    client: AsyncClient, sent_mail: list
) -> None:
    """Guests sitting on alone must not keep spending the host's coins."""
    from datetime import UTC, datetime, timedelta

    from beanie import PydanticObjectId

    from app.core.config import settings as app_settings
    from app.services import milan as milan_service

    host, astro, data = await _chamber(client, sent_mail)
    room_id = PydanticObjectId(data["room"]["id"])
    code = data["room"]["seats"][0]["join_code"]

    await client.post(f"{P}/milan/{data['room']['id']}/accept", headers=astro)
    await client.post(f"{P}/milan/guest/join", json={"join_code": code})

    # The host and the astrologer both went quiet a long time ago; the guest
    # is still checking in.
    stale = datetime.now(UTC) - timedelta(
        seconds=app_settings.CALL_HEARTBEAT_GRACE_SECONDS + 60
    )
    room = await MilanRoom.get(room_id)
    assert room is not None
    room.host_seen_at = stale
    room.astrologer_seen_at = stale
    room.started_at = stale
    await room.save()
    await client.post(f"{P}/milan/guest/heartbeat", json={"join_code": code})

    swept = await milan_service.sweep()
    assert swept["dropped"] >= 1, swept

    closed = await MilanRoom.get(room_id)
    assert closed is not None
    assert closed.status.value == "ended"
    # And every invitation went with it.
    blocked = await client.post(f"{P}/milan/guest/join", json={"join_code": code})
    assert blocked.status_code == 409, blocked.text


async def test_a_chamber_nobody_answers_is_marked_missed(
    client: AsyncClient, sent_mail: list
) -> None:
    from datetime import UTC, datetime, timedelta

    from beanie import PydanticObjectId

    from app.core.config import settings as app_settings
    from app.services import milan as milan_service

    host, _, data = await _chamber(client, sent_mail)
    room_id = PydanticObjectId(data["room"]["id"])

    room = await MilanRoom.get(room_id)
    assert room is not None
    room.created_at = datetime.now(UTC) - timedelta(
        seconds=app_settings.CALL_RING_TIMEOUT_SECONDS + 30
    )
    await room.save()

    swept = await milan_service.sweep()
    assert swept["missed"] >= 1, swept

    missed = await MilanRoom.get(room_id)
    assert missed is not None
    assert missed.status.value == "missed"
