"""The appointment lists must not query the database once per booking.

Sentry caught `my_schedule` firing one `find users` per appointment — seven
bookings meant seven extra round-trips, about 80ms each against a remote
MongoDB. These tests count the real round-trips, so the N+1 cannot come back
unnoticed.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from pymongo import monitoring

from app.models.appointment import Appointment, AppointmentStatus
from app.models.astrologer import Astrologer
from app.models.enums import Skill, UserRole
from app.models.user import User

P = "/api/v1"
pytestmark = pytest.mark.usefixtures("fake_firebase")

BOOKINGS = 7


class _FindCounter(monitoring.CommandListener):
    """Counts `find` commands per collection while it is switched on."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.watching = False

    def started(self, event: monitoring.CommandStartedEvent) -> None:
        if not self.watching or event.command_name != "find":
            return
        collection = event.command.get("find", "?")
        self.counts[collection] = self.counts.get(collection, 0) + 1

    def succeeded(self, event: monitoring.CommandSucceededEvent) -> None:
        pass

    def failed(self, event: monitoring.CommandFailedEvent) -> None:
        pass


# A listener can only be registered before a client is built, so it is global
# and stays dormant until a test switches it on.
COUNTER = _FindCounter()
monitoring.register(COUNTER)


async def _signed_in(client: AsyncClient, email: str, name: str) -> dict:
    started = await client.post(
        f"{P}/auth/register/email",
        json={"email": email, "password": "secret123", "first_name": name},
    )
    created = await client.post(
        f"{P}/auth/register/email/verify",
        json={"email": email, "code": started.json()["data"]["dev_code"]},
    )
    assert created.status_code == 201, created.text
    return {"Authorization": f"Bearer {created.json()['data']['tokens']['access_token']}"}


async def _seed(client: AsyncClient) -> tuple[dict, dict]:
    """One astrologer, one client, and BOOKINGS appointments between them."""
    client_headers = await _signed_in(client, "n1client@test.dev", "Ananya")
    astro_headers = await _signed_in(client, "n1astro@test.dev", "Ramesh")

    client_user = await User.find_one(User.email == "n1client@test.dev")
    astro_user = await User.find_one(User.email == "n1astro@test.dev")
    astro_user.role = UserRole.ASTROLOGER
    await astro_user.save()

    profile = await Astrologer(
        user_id=astro_user.id,
        slug="n1-ramesh",
        display_name="Pt. Ramesh",
        experience_years=10,
        skills=[Skill.VEDIC_ASTROLOGY],
        languages=["Bengali"],
        is_listed=True,
    ).insert()

    start = (datetime.now(UTC) + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
    for i in range(BOOKINGS):
        await Appointment(
            user_id=client_user.id,
            astrologer_id=profile.id,
            astrologer_user_id=astro_user.id,
            starts_at=start + timedelta(hours=i),
            ends_at=start + timedelta(hours=i, minutes=30),
            minutes=30,
            price_paise=500_00,
            status=AppointmentStatus.BOOKED,
        ).insert()

    return client_headers, astro_headers


async def test_the_astrologers_schedule_does_not_query_per_booking(
    client: AsyncClient,
) -> None:
    _, astro_headers = await _seed(client)

    COUNTER.counts = {}
    COUNTER.watching = True
    try:
        resp = await client.get(
            f"{P}/appointments/me/schedule?upcoming_only=false", headers=astro_headers
        )
    finally:
        COUNTER.watching = False

    assert resp.status_code == 200, resp.text
    assert len(resp.json()["data"]) == BOOKINGS

    # The peer of every booking is the same client, so one `find users` covers
    # the lot. Auth looks the astrologer up as well, hence the small allowance.
    assert COUNTER.counts.get("users", 0) <= 2, COUNTER.counts


async def test_the_clients_list_does_not_query_per_booking(client: AsyncClient) -> None:
    client_headers, _ = await _seed(client)

    COUNTER.counts = {}
    COUNTER.watching = True
    try:
        resp = await client.get(
            f"{P}/appointments/mine?upcoming_only=false", headers=client_headers
        )
    finally:
        COUNTER.watching = False

    assert resp.status_code == 200, resp.text
    assert len(resp.json()["data"]) == BOOKINGS

    # Same again from the other side: one `find astrologers` for all of them.
    assert COUNTER.counts.get("astrologers", 0) <= 1, COUNTER.counts


async def test_every_booking_still_names_the_other_person(client: AsyncClient) -> None:
    """The batched lookup must not quietly drop the peer it used to fetch."""
    client_headers, astro_headers = await _seed(client)

    schedule = await client.get(
        f"{P}/appointments/me/schedule?upcoming_only=false", headers=astro_headers
    )
    assert [a["peer"]["name"] for a in schedule.json()["data"]] == ["Ananya"] * BOOKINGS

    mine = await client.get(f"{P}/appointments/mine?upcoming_only=false", headers=client_headers)
    assert [a["peer"]["name"] for a in mine.json()["data"]] == ["Pt. Ramesh"] * BOOKINGS
