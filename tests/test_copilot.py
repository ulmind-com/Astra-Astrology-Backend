"""The astrologer's live Co-Pilot.

Two things matter here. The panel must never show a chart to anyone but the
astrologer on that live call, and it must never show a chart the client's own
birth details cannot support — a confident dasha read out from a placeholder
birth date is worse than an empty panel.
"""

from datetime import date

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.test_astrologer import make_admin
from tests.test_calls import make_astrologer, ring, signed_in

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")

@pytest.fixture
def sent_mail(monkeypatch: pytest.MonkeyPatch) -> list:
    """Catches the generated password instead of emailing it.

    Defined here rather than imported: importing the fixture would shadow the
    `sent_mail` argument every test below takes.
    """
    captured: list = []
    import app.services.astrologer as astrologer_service

    async def fake_send(to: str, name: str, password: str) -> bool:
        captured.append({"to": to, "password": password})
        return True

    monkeypatch.setattr(astrologer_service, "send_astrologer_welcome_email", fake_send)
    return captured


KOLKATA = {
    "latitude": 22.5726,
    "longitude": 88.3639,
    "timezone": "Asia/Kolkata",
    "timezone_offset": 5.5,
    "place": "Kolkata, West Bengal, India",
}


async def _give_birth_details(
    headers: dict,
    *,
    time_of_birth: str | None = "14:30",
    is_time_known: bool = True,
) -> None:
    """Saves birth details on the signed-in user, as the profile screen would."""
    from beanie import PydanticObjectId

    from app.core.security import decode_token
    from app.models.profile import BirthDetails

    token = headers["Authorization"].removeprefix("Bearer ")
    user = await User.get(PydanticObjectId(decode_token(token)["sub"]))
    assert user is not None
    user.birth = BirthDetails(
        date_of_birth=date(1995, 5, 12),
        time_of_birth=time_of_birth,
        is_time_known=is_time_known,
        **KOLKATA,
    )
    await user.save()


async def _ringing_call(client: AsyncClient, mail: list) -> tuple[dict, dict, str]:
    """A caller, their astrologer, and a call ringing between them."""
    admin = await make_admin(client)
    profile, astro = await make_astrologer(client, admin, mail)
    caller = await signed_in(client)

    started = await ring(client, caller, profile["id"])
    assert started.status_code == 201, started.text
    return caller, astro, started.json()["data"]["call"]["id"]


# ------------------------------------------------------------- who may look
async def test_only_the_astrologer_on_the_call_can_open_it(
    client: AsyncClient, sent_mail: list
) -> None:
    caller, astro, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller)

    theirs = await client.get(f"{P}/calls/{call_id}/copilot", headers=astro)
    assert theirs.status_code == 200, theirs.text

    # The client is in the same call and still must not see their own chart
    # through the astrologer's panel.
    mine = await client.get(f"{P}/calls/{call_id}/copilot", headers=caller)
    assert mine.status_code == 403, mine.text
    assert mine.json()["error_code"] == "not_your_call"


async def test_another_astrologer_cannot_open_someone_elses_call(
    client: AsyncClient, sent_mail: list
) -> None:
    caller, _, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller)

    admin = await make_admin(client, email="copilotadmin2@test.dev")
    _, outsider = await make_astrologer(
        client, admin, sent_mail, email="nosy.astro@test.dev", online=False
    )

    resp = await client.get(f"{P}/calls/{call_id}/copilot", headers=outsider)
    assert resp.status_code == 403, resp.text
    assert resp.json()["error_code"] == "not_your_call"


async def test_signing_in_is_required(client: AsyncClient, sent_mail: list) -> None:
    _, _, call_id = await _ringing_call(client, sent_mail)
    resp = await client.get(f"{P}/calls/{call_id}/copilot")
    assert resp.status_code == 401, resp.text


async def test_a_call_that_does_not_exist_is_not_found(
    client: AsyncClient, sent_mail: list
) -> None:
    admin = await make_admin(client)
    _, astro = await make_astrologer(client, admin, sent_mail)

    resp = await client.get(
        f"{P}/calls/6000000000000000000000aa/copilot", headers=astro
    )
    assert resp.status_code == 404, resp.text


async def test_the_panel_closes_when_the_session_is_over(
    client: AsyncClient, sent_mail: list
) -> None:
    """A finished call must not keep the client's chart open indefinitely."""
    caller, astro, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller)

    accepted = await client.post(f"{P}/calls/{call_id}/accept", headers=astro)
    assert accepted.status_code == 200, accepted.text
    live = await client.get(f"{P}/calls/{call_id}/copilot", headers=astro)
    assert live.status_code == 200, live.text

    ended = await client.post(
        f"{P}/calls/{call_id}/end", headers=astro, json={"reason": "done"}
    )
    assert ended.status_code == 200, ended.text

    after = await client.get(f"{P}/calls/{call_id}/copilot", headers=astro)
    assert after.status_code == 403, after.text
    assert after.json()["error_code"] == "call_not_live"


# ------------------------------------------------------------- what it shows
async def test_it_summarises_the_running_dasha_sade_sati_and_one_remedy(
    client: AsyncClient, sent_mail: list
) -> None:
    caller, astro, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller)

    resp = await client.get(f"{P}/calls/{call_id}/copilot?language=en", headers=astro)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    assert data["is_ready"] is True
    assert data["unavailable_reason"] == ""
    assert data["is_birth_time_known"] is True
    assert data["accuracy_note"] == ""
    assert data["moon_sign"] == "Virgo"
    assert data["nakshatra"] == "Hasta"

    # Born 12 May 1995: Moon late in Hasta, so the Moon mahadasha is nearly
    # spent at birth and the chain runs Mars, Rahu, then Jupiter from 2020.
    md = data["mahadasha"]
    assert md["lord"] == "Jupiter"
    assert md["starts_on"].endswith("-2020")
    assert md["ends_on"].endswith("-2036")
    assert 0 <= md["percent_complete"] <= 100
    assert md["days_remaining"] > 0

    ad = data["antardasha"]
    assert ad["lord"] in (
        "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
    )
    assert 0 <= ad["percent_complete"] <= 100

    sade = data["sade_sati"]
    assert sade["phase_code"] in ("rising", "peak", "setting", "kantaka", "ashtama", "none")
    assert 1 <= sade["saturn_house_from_moon"] <= 12
    assert sade["remedy_summary"]

    remedy = data["remedy_focus"]
    assert remedy["planet"]
    assert remedy["reason"]
    assert remedy["remedies"], "every dasha lord must carry a remedy, nodes included"
    assert remedy["beej_mantra"]


async def test_the_remedy_follows_saturn_while_sade_sati_runs(
    client: AsyncClient, sent_mail: list
) -> None:
    """An active Sade Sati outranks the running antardasha."""
    caller, astro, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller)

    resp = await client.get(f"{P}/calls/{call_id}/copilot", headers=astro)
    data = resp.json()["data"]
    if data["sade_sati"]["is_active"]:
        assert data["remedy_focus"]["planet"] == "Saturn"
    else:
        assert data["remedy_focus"]["planet"] == data["antardasha"]["lord"]


async def test_nothing_is_guessed_when_the_client_saved_no_birth_details(
    client: AsyncClient, sent_mail: list
) -> None:
    _, astro, call_id = await _ringing_call(client, sent_mail)

    resp = await client.get(f"{P}/calls/{call_id}/copilot", headers=astro)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    assert data["is_ready"] is False
    assert data["unavailable_reason"], "the astrologer must be told why it is empty"
    assert data["mahadasha"] is None
    assert data["antardasha"] is None
    assert data["sade_sati"] is None
    assert data["remedy_focus"] is None


async def test_a_missing_birth_time_is_flagged_as_approximate(
    client: AsyncClient, sent_mail: list
) -> None:
    """The Moon moves half a degree an hour, so this changes the dasha."""
    caller, astro, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller, time_of_birth=None, is_time_known=False)

    resp = await client.get(f"{P}/calls/{call_id}/copilot?language=en", headers=astro)
    data = resp.json()["data"]

    assert data["is_ready"] is True
    assert data["is_birth_time_known"] is False
    assert data["accuracy_note"], "the panel must say the dasha is only indicative"
    assert data["mahadasha"] is not None


async def test_an_unparseable_stored_birth_time_is_treated_as_unknown(
    client: AsyncClient, sent_mail: list
) -> None:
    caller, astro, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller, time_of_birth="not-a-time")

    resp = await client.get(f"{P}/calls/{call_id}/copilot", headers=astro)
    data = resp.json()["data"]
    assert data["is_ready"] is True
    assert data["is_birth_time_known"] is False
    assert data["accuracy_note"]


# ------------------------------------------------------------------ language
async def test_it_answers_in_the_language_asked_for(
    client: AsyncClient, sent_mail: list
) -> None:
    caller, astro, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller)

    bengali = await client.get(f"{P}/calls/{call_id}/copilot?language=bn", headers=astro)
    hindi = await client.get(f"{P}/calls/{call_id}/copilot?language=hi", headers=astro)
    english = await client.get(f"{P}/calls/{call_id}/copilot?language=en", headers=astro)

    bn, hi, en = (r.json()["data"] for r in (bengali, hindi, english))
    assert (bn["language"], hi["language"], en["language"]) == ("bn", "hi", "en")
    assert bn["moon_sign"] == "কন্যা"
    assert hi["moon_sign"] == "कन्या"
    assert en["moon_sign"] == "Virgo"
    # The dasha itself is astronomy and must not move with the language.
    assert bn["mahadasha"]["lord"] == hi["mahadasha"]["lord"] == en["mahadasha"]["lord"]
    assert bn["mahadasha"]["lord_label"] != en["mahadasha"]["lord_label"]


async def test_an_unknown_language_falls_back_to_english(
    client: AsyncClient, sent_mail: list
) -> None:
    caller, astro, call_id = await _ringing_call(client, sent_mail)
    await _give_birth_details(caller)

    resp = await client.get(f"{P}/calls/{call_id}/copilot?language=klingon", headers=astro)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["language"] == "en"
