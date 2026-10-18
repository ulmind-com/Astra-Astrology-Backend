"""Per-minute billing.

The tests that matter are the ones about money leaving a wallet when it should
and never when it should not: the client's own "15 coins, 10 a minute" case,
the race where both sides heartbeat at once, and a price that changes while a
session is already running.
"""

from datetime import UTC, datetime, timedelta

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


async def signed_in(client: AsyncClient, email: str = "payer@test.dev") -> dict:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": "secret123", "first_name": "Payer"},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    assert created.status_code == 201, created.text
    return {"Authorization": f"Bearer {created.json()['data']['tokens']['access_token']}"}


async def user_id_for(email: str):
    from app.models.user import User

    return (await User.find_one(User.email == email)).id


async def make_astrologer(
    client: AsyncClient, admin: dict, mail: list, *, email: str = "ravi.astro@test.dev", **over
) -> tuple[dict, dict]:
    created = await client.post(
        f"{P}/admin/astrologers",
        headers=admin,
        json={**BASE, "email": email, "modes_enabled": ["chat", "call", "video"], **over},
    )
    assert created.status_code == 201, created.text
    profile = created.json()["data"]["astrologer"]

    logged = await client.post(
        f"{P}/auth/login", json={"email": email, "password": mail[-1]["password"]}
    )
    auth = {"Authorization": f"Bearer {logged.json()['data']['tokens']['access_token']}"}
    await client.patch(f"{P}/astrologers/me/availability", headers=auth, json={"is_online": True})
    return profile, auth


async def give_coins(client: AsyncClient, admin: dict, email: str, coins: int) -> None:
    uid = await user_id_for(email)
    r = await client.post(
        f"{P}/admin/wallets/{uid}/adjust",
        headers=admin,
        json={"direction": "credit", "amount_coins": coins, "reason": "Test float"},
    )
    assert r.status_code == 200, r.text


async def set_defaults(client: AsyncClient, admin: dict, **body):
    return await client.patch(f"{P}/admin/settings/consultation", headers=admin, json=body)


async def balance(client: AsyncClient, auth: dict) -> int:
    return (await client.get(f"{P}/wallet", headers=auth)).json()["data"]["wallet"][
        "balance_coins"
    ]


async def ring(client: AsyncClient, auth: dict, astrologer_id: str, minutes: int, mode="video"):
    return await client.post(
        f"{P}/calls",
        headers=auth,
        json={"astrologer_id": astrologer_id, "mode": mode, "requested_minutes": minutes},
    )


# ------------------------------------------------------------------- quote
async def test_the_quote_says_what_a_minute_costs_and_what_i_can_afford(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=8)
    await give_coins(client, admin, "payer@test.dev", 100)

    quote = (
        await client.get(f"{P}/astrologers/{profile['id']}/quote?mode=video", headers=auth)
    ).json()["data"]

    assert quote["coins_per_minute"] == 8
    assert quote["balance_coins"] == 100
    assert quote["affordable_minutes"] == 12  # 100 // 8


async def test_an_astrologers_own_rate_beats_the_default(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=8)
    await client.patch(
        f"{P}/admin/astrologers/{profile['id']}",
        headers=admin,
        json={"rates": {"video_coins_per_minute": 20}},
    )
    await give_coins(client, admin, "payer@test.dev", 100)

    quote = (
        await client.get(f"{P}/astrologers/{profile['id']}/quote?mode=video", headers=auth)
    ).json()["data"]
    assert quote["coins_per_minute"] == 20
    assert quote["affordable_minutes"] == 5


# -------------------------------------------------------------- starting
async def test_a_booking_the_wallet_cannot_cover_is_refused_with_the_numbers(
    client: AsyncClient, sent_mail: list
) -> None:
    """The client asked for the message to say how many more coins are needed."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=8)
    await give_coins(client, admin, "payer@test.dev", 25)

    refused = await ring(client, auth, profile["id"], 5)  # needs 40
    assert refused.status_code == 400
    body = refused.json()
    assert body["error_code"] == "insufficient_coins"
    assert body["details"]["needed_coins"] == 40
    assert body["details"]["short_by_coins"] == 15
    assert body["details"]["affordable_minutes"] == 3
    assert "15 more" in body["message"]

    # Nothing was taken for a session that never started.
    assert await balance(client, auth) == 25


async def test_a_booking_within_the_balance_starts(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=8)
    await give_coins(client, admin, "payer@test.dev", 100)

    started = await ring(client, auth, profile["id"], 5)
    assert started.status_code == 201, started.text
    call = started.json()["data"]["call"]
    assert call["billing"]["coins_per_minute"] == 8
    assert call["billing"]["requested_minutes"] == 5

    # Ringing is free — nothing is charged until someone answers.
    assert await balance(client, auth) == 100


async def test_a_duration_outside_the_allowed_range_is_refused(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, _ = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, min_session_minutes=2, max_session_minutes=10)
    await give_coins(client, admin, "payer@test.dev", 10_000)

    assert (await ring(client, auth, profile["id"], 1)).json()["error_code"] == "invalid_duration"
    assert (await ring(client, auth, profile["id"], 11)).json()["error_code"] == "invalid_duration"
    assert (await ring(client, auth, profile["id"], 5)).status_code == 201


# --------------------------------------------------------------- charging
async def test_the_first_minute_is_paid_for_when_the_call_is_answered(
    client: AsyncClient, sent_mail: list
) -> None:
    """Pre-paid: never hand over a minute that might be unaffordable."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=8)
    await give_coins(client, admin, "payer@test.dev", 100)

    call_id = (await ring(client, auth, profile["id"], 5)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    assert await balance(client, auth) == 92, "one minute taken on answer"


async def test_the_same_minute_is_never_charged_twice(
    client: AsyncClient, sent_mail: list
) -> None:
    """Both sides heartbeat, and the two can land together."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=8)
    await give_coins(client, admin, "payer@test.dev", 100)

    call_id = (await ring(client, auth, profile["id"], 5)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    for _ in range(4):
        await client.post(f"{P}/calls/{call_id}/heartbeat", headers=auth)
        await client.post(f"{P}/calls/{call_id}/heartbeat", headers=astro)

    assert await balance(client, auth) == 92, "still just the one minute"


async def test_later_minutes_are_charged_as_they_start(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=8)
    await give_coins(client, admin, "payer@test.dev", 100)

    call_id = (await ring(client, auth, profile["id"], 5)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    # Wind the start back so three minutes have begun.
    from beanie import PydanticObjectId

    from app.models.call import CallSession

    session = await CallSession.get(PydanticObjectId(call_id))
    session.started_at = datetime.now(UTC) - timedelta(seconds=125)
    await session.save()

    await client.post(f"{P}/calls/{call_id}/heartbeat", headers=auth)
    assert await balance(client, auth) == 100 - 24, "minutes 1, 2 and 3"


# ------------------------------------------------ the client's own example
async def test_fifteen_coins_at_ten_a_minute_buys_one_more_then_stops(
    client: AsyncClient, sent_mail: list
) -> None:
    """15 coins left, 10 a minute: one more minute runs, then it ends itself."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=10)
    await give_coins(client, admin, "payer@test.dev", 15)

    call_id = (await ring(client, auth, profile["id"], 1)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    # Minute one taken; 5 coins left, which buys nothing.
    assert await balance(client, auth) == 5
    state = (await client.get(f"{P}/calls/{call_id}", headers=auth)).json()["data"]["call"]
    assert state["billing"]["minutes_left"] == 0, "the UI can warn on this"

    # The next minute begins and cannot be paid for.
    from beanie import PydanticObjectId

    from app.models.call import CallSession

    session = await CallSession.get(PydanticObjectId(call_id))
    session.started_at = datetime.now(UTC) - timedelta(seconds=70)
    session.requested_minutes = 10  # not the cap that stops it — the wallet is
    await session.save()

    await client.post(f"{P}/calls/{call_id}/heartbeat", headers=auth)

    after = (await client.get(f"{P}/calls/{call_id}", headers=auth)).json()["data"]["call"]
    assert after["status"] == "ended"
    assert after["end_reason"] == "Ran out of coins"
    assert await balance(client, auth) == 5, "the unaffordable minute was not given away"


async def test_the_booked_time_is_a_hard_stop(
    client: AsyncClient, sent_mail: list
) -> None:
    """They asked for two minutes, so it ends at two — even with coins left."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=5)
    await give_coins(client, admin, "payer@test.dev", 500)

    call_id = (await ring(client, auth, profile["id"], 2)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    from beanie import PydanticObjectId

    from app.models.call import CallSession

    session = await CallSession.get(PydanticObjectId(call_id))
    session.started_at = datetime.now(UTC) - timedelta(seconds=130)
    await session.save()

    await client.post(f"{P}/calls/{call_id}/heartbeat", headers=auth)

    after = (await client.get(f"{P}/calls/{call_id}", headers=auth)).json()["data"]["call"]
    assert after["status"] == "ended"
    assert after["end_reason"] == "The booked time is over"
    assert await balance(client, auth) == 490, "exactly the two minutes booked"


async def test_a_price_change_does_not_touch_a_session_already_running(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=5)
    await give_coins(client, admin, "payer@test.dev", 200)

    call_id = (await ring(client, auth, profile["id"], 5)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)
    assert await balance(client, auth) == 195

    # The admin triples the price mid-call.
    await set_defaults(client, admin, default_video_coins_per_minute=15)

    from beanie import PydanticObjectId

    from app.models.call import CallSession

    session = await CallSession.get(PydanticObjectId(call_id))
    session.started_at = datetime.now(UTC) - timedelta(seconds=65)
    await session.save()
    await client.post(f"{P}/calls/{call_id}/heartbeat", headers=auth)

    assert await balance(client, auth) == 190, "minute two at the quoted 5, not 15"


# --------------------------------------------------------------- earnings
async def test_the_astrologer_is_credited_and_never_shown_the_commission(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    # 5 coins per rupee -> a coin is worth 20 paise.
    await client.patch(f"{P}/admin/settings", headers=admin, json={"coins_per_rupee": 5})
    await set_defaults(
        client, admin, default_video_coins_per_minute=10, default_commission_percent=20
    )
    await give_coins(client, admin, "payer@test.dev", 100)

    call_id = (await ring(client, auth, profile["id"], 1)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    mine = (await client.get(f"{P}/astrologers/me/earnings", headers=astro)).json()["data"]
    # 10 coins x 20 paise = 200 paise gross; 20% commission -> 160 paise.
    assert mine["today"]["earning_paise"] == 160
    assert mine["all_time"]["minutes"] == 1
    assert "commission" not in str(mine), "astrologers are not shown the cut"

    # The admin sees the whole split.
    totals = (await client.get(f"{P}/admin/earnings", headers=admin)).json()["data"]
    assert totals["gross_paise"] == 200
    assert totals["commission_paise"] == 40
    assert totals["payout_paise"] == 160


async def test_one_astrologer_can_have_their_own_commission(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await client.patch(f"{P}/admin/settings", headers=admin, json={"coins_per_rupee": 5})
    await set_defaults(
        client, admin, default_video_coins_per_minute=10, default_commission_percent=20
    )
    # This one keeps more.
    await client.patch(
        f"{P}/admin/astrologers/{profile['id']}", headers=admin, json={"commission_percent": 50}
    )
    await give_coins(client, admin, "payer@test.dev", 100)

    call_id = (await ring(client, auth, profile["id"], 1)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    mine = (await client.get(f"{P}/astrologers/me/earnings", headers=astro)).json()["data"]
    assert mine["today"]["earning_paise"] == 100, "half of 200 paise"


async def test_a_user_cannot_read_the_platform_earnings(client: AsyncClient) -> None:
    auth = await signed_in(client)
    assert (await client.get(f"{P}/admin/earnings", headers=auth)).status_code == 403


# ------------------------------------------------------------------- chat
async def test_chat_is_billed_the_same_way(
    client: AsyncClient, sent_mail: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_chat import FakeFirestore

    fake = FakeFirestore()
    import app.api.v1.chats as chats_api
    import app.services.chat as chat_service

    for module in (chat_service, chats_api):
        monkeypatch.setattr(module, "firestore", fake)

    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_chat_coins_per_minute=3)
    await give_coins(client, admin, "payer@test.dev", 20)

    started = await client.post(
        f"{P}/chats", headers=auth, json={"astrologer_id": profile["id"], "requested_minutes": 5}
    )
    assert started.status_code == 201, started.text
    chat_id = started.json()["data"]["chat"]["id"]

    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    assert await balance(client, auth) == 17, "three coins for minute one"


async def test_a_chat_that_runs_out_is_closed_in_firestore_too(
    client: AsyncClient, sent_mail: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Closing it only in MongoDB would leave two browsers still able to talk."""
    from tests.test_chat import FakeFirestore

    fake = FakeFirestore()
    import app.api.v1.chats as chats_api
    import app.services.chat as chat_service

    for module in (chat_service, chats_api):
        monkeypatch.setattr(module, "firestore", fake)

    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_chat_coins_per_minute=10)
    await give_coins(client, admin, "payer@test.dev", 12)

    started = await client.post(
        f"{P}/chats", headers=auth, json={"astrologer_id": profile["id"], "requested_minutes": 1}
    )
    chat_id = started.json()["data"]["chat"]["id"]
    convo = started.json()["data"]["chat"]["conversation_id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)
    assert fake.conversations[convo]["status"] == "active"

    from beanie import PydanticObjectId

    from app.models.chat import ChatSession

    session = await ChatSession.get(PydanticObjectId(chat_id))
    session.started_at = datetime.now(UTC) - timedelta(seconds=70)
    session.requested_minutes = 10
    await session.save()

    await client.post(f"{P}/chats/{chat_id}/heartbeat", headers=auth)

    assert fake.conversations[convo]["status"] == "ended"


# ------------------------------------------------------------ the invariant
async def test_the_ledger_still_adds_up_after_a_billed_session(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)
    uid = await user_id_for("payer@test.dev")

    await set_defaults(client, admin, default_video_coins_per_minute=7)
    await give_coins(client, admin, "payer@test.dev", 100)

    call_id = (await ring(client, auth, profile["id"], 3)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)
    await client.post(f"{P}/calls/{call_id}/heartbeat", headers=auth)

    result = (
        await client.post(f"{P}/admin/wallets/{uid}/reconcile", headers=admin)
    ).json()["data"]
    assert result["drift_coins"] == 0
    assert result["debited_coins"] == 7


# ---------------------------------------------------------------- extending
async def test_a_call_can_be_extended_and_the_cap_moves(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=5)
    await give_coins(client, admin, "payer@test.dev", 100)

    call_id = (await ring(client, auth, profile["id"], 2)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    extended = await client.post(
        f"{P}/calls/{call_id}/extend", headers=auth, json={"extra_minutes": 3}
    )
    assert extended.status_code == 200, extended.text
    assert extended.json()["data"]["billing"]["requested_minutes"] == 5

    # The hard stop moved with it: three minutes in, it is still going.
    from beanie import PydanticObjectId

    from app.models.call import CallSession

    session = await CallSession.get(PydanticObjectId(call_id))
    session.started_at = datetime.now(UTC) - timedelta(seconds=185)
    await session.save()
    await client.post(f"{P}/calls/{call_id}/heartbeat", headers=auth)

    after = (await client.get(f"{P}/calls/{call_id}", headers=auth)).json()["data"]["call"]
    assert after["status"] == "active"
    assert await balance(client, auth) == 80, "four minutes at five coins"


async def test_an_extension_the_wallet_cannot_cover_is_refused(
    client: AsyncClient, sent_mail: list
) -> None:
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=10)
    await give_coins(client, admin, "payer@test.dev", 30)

    call_id = (await ring(client, auth, profile["id"], 2)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    # 20 coins left, one minute still owed on the booking, so only one more.
    refused = await client.post(
        f"{P}/calls/{call_id}/extend", headers=auth, json={"extra_minutes": 10}
    )
    assert refused.status_code == 400
    assert refused.json()["error_code"] == "insufficient_coins"

    assert (
        await client.post(
            f"{P}/calls/{call_id}/extend", headers=auth, json={"extra_minutes": 1}
        )
    ).status_code == 200


async def test_only_the_payer_can_extend(client: AsyncClient, sent_mail: list) -> None:
    """An astrologer lengthening a call would be spending someone else's coins."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=5)
    await give_coins(client, admin, "payer@test.dev", 500)

    call_id = (await ring(client, auth, profile["id"], 2)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    refused = await client.post(
        f"{P}/calls/{call_id}/extend", headers=astro, json={"extra_minutes": 5}
    )
    assert refused.status_code == 403
    assert refused.json()["error_code"] == "not_the_payer"


async def test_the_session_screen_knows_what_it_can_offer(
    client: AsyncClient, sent_mail: list
) -> None:
    """The extend prompt is driven by these, so they have to be right."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=10, max_session_minutes=30)
    await give_coins(client, admin, "payer@test.dev", 100)

    call_id = (await ring(client, auth, profile["id"], 2)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    billing = (await client.get(f"{P}/calls/{call_id}", headers=auth)).json()["data"]["call"][
        "billing"
    ]
    assert billing["requested_minutes"] == 2
    assert billing["minutes_charged"] == 1
    assert billing["minutes_remaining"] == 1, "one of the two booked minutes is left"
    assert billing["coins_charged"] == 10
    assert billing["balance_coins"] == 90
    assert billing["can_extend"] is True
    assert billing["max_extend_minutes"] == 9, "90 coins at 10 a minute"


async def test_nothing_is_offered_when_the_wallet_is_empty(
    client: AsyncClient, sent_mail: list
) -> None:
    """Offering an extension nobody can pay for is just bad news with buttons."""
    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_video_coins_per_minute=10)
    await give_coins(client, admin, "payer@test.dev", 10)

    call_id = (await ring(client, auth, profile["id"], 1)).json()["data"]["call"]["id"]
    await client.post(f"{P}/calls/{call_id}/accept", headers=astro)

    billing = (await client.get(f"{P}/calls/{call_id}", headers=auth)).json()["data"]["call"][
        "billing"
    ]
    assert billing["balance_coins"] == 0
    assert billing["can_extend"] is False
    assert billing["max_extend_minutes"] == 0


async def test_a_chat_can_be_extended_too(
    client: AsyncClient, sent_mail: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_chat import FakeFirestore

    fake = FakeFirestore()
    import app.api.v1.chats as chats_api
    import app.services.chat as chat_service

    for module in (chat_service, chats_api):
        monkeypatch.setattr(module, "firestore", fake)

    auth = await signed_in(client)
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, sent_mail)

    await set_defaults(client, admin, default_chat_coins_per_minute=3)
    await give_coins(client, admin, "payer@test.dev", 100)

    started = await client.post(
        f"{P}/chats", headers=auth, json={"astrologer_id": profile["id"], "requested_minutes": 2}
    )
    chat_id = started.json()["data"]["chat"]["id"]
    await client.post(f"{P}/chats/{chat_id}/accept", headers=astro)

    extended = await client.post(
        f"{P}/chats/{chat_id}/extend", headers=auth, json={"extra_minutes": 5}
    )
    assert extended.status_code == 200
    assert extended.json()["data"]["billing"]["requested_minutes"] == 7
