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

# One booked appointment each, from this many different clients.
CLIENTS = 7
# Past appointments the signed-in client also has with that astrologer.
HISTORY = 6
# What the astrologer's own schedule therefore holds.
SCHEDULE_TOTAL = CLIENTS + HISTORY
# What the signed-in client's own list holds: their one booked, plus history.
MY_TOTAL = 1 + HISTORY


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
    """An astrologer with a full schedule, and one signed-in client.

    A user may hold only one *booked* appointment at a time — the
    `unique_active_user_booking` partial index enforces it — so the
    astrologer's bookings come from CLIENTS different clients, which is the
    shape Sentry caught: one `find users` per booking, each a different user.
    The signed-in client's own list is one booked plus a run of completed
    ones, all with the same astrologer.
    """
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

    async def book(user_id, hour: int, status: AppointmentStatus) -> None:
        await Appointment(
            user_id=user_id,
            astrologer_id=profile.id,
            astrologer_user_id=astro_user.id,
            starts_at=start + timedelta(hours=hour),
            ends_at=start + timedelta(hours=hour, minutes=30),
            minutes=30,
            price_paise=500_00,
            status=status,
        ).insert()

    # The astrologer's schedule: CLIENTS clients, one booking each. The
    # signed-in client is the first of them, so their own list starts with a
    # booked appointment.
    await book(client_user.id, 0, AppointmentStatus.BOOKED)
    for i in range(1, CLIENTS):
        other = await User(
            email=f"n1peer{i}@test.dev",
            first_name="Ananya",
            last_name=None,
        ).insert()
        await book(other.id, i, AppointmentStatus.BOOKED)

    # ...and enough history on the signed-in client to make their own list
    # worth batching too.
    for i in range(HISTORY):
        await book(client_user.id, 100 + i, AppointmentStatus.COMPLETED)

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
    assert len(resp.json()["data"]) == SCHEDULE_TOTAL

    # CLIENTS different clients, resolved in a single `find users` with an
    # $in. Auth looks the astrologer up as well, hence the small allowance.
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
    assert len(resp.json()["data"]) == MY_TOTAL

    # Same again from the other side: one `find astrologers` for all of them,
    # even though every booking names the same astrologer.
    assert COUNTER.counts.get("astrologers", 0) <= 1, COUNTER.counts


async def test_every_booking_still_names_the_other_person(client: AsyncClient) -> None:
    """The batched lookup must not quietly drop the peer it used to fetch."""
    client_headers, astro_headers = await _seed(client)

    schedule = await client.get(
        f"{P}/appointments/me/schedule?upcoming_only=false", headers=astro_headers
    )
    # Every booking is a different client, and all of them are named.
    names = [a["peer"]["name"] for a in schedule.json()["data"]]
    assert len(names) == SCHEDULE_TOTAL
    assert all(name == "Ananya" for name in names), names

    mine = await client.get(f"{P}/appointments/mine?upcoming_only=false", headers=client_headers)
    assert [a["peer"]["name"] for a in mine.json()["data"]] == ["Pt. Ramesh"] * MY_TOTAL
