"""Who is actually at their desk.

An astrologer's `is_online` flag says what they *intended*. It cannot say
whether their browser is still open: a closed tab, a crash, a dead laptop and a
lost connection all look identical from here — the panel simply stops talking.
If the flag were trusted on its own, every astrologer who ever went online
would stay online for ever, and users would queue for people who left hours ago.

So availability is two facts read together:

    is_online     they switched themselves on, and have not switched off
    last_seen_at  their panel said hello within the last `TTL` seconds

The panel beats every `BEAT_SECONDS`; `TTL` allows two beats to go missing
before anyone is declared offline, which covers an ordinary network hiccup
without leaving a ghost on the directory for long.

Staleness is evaluated **when the data is read**, never only by a sweeper. That
matters: it means presence is correct even if no sweep has run, if the process
restarted, or if a cron was never set up. `sweep()` exists to settle the stored
flag so that anything reading MongoDB directly agrees with what the site shows
— nothing depends on it for correctness.
"""

from datetime import timedelta

from beanie.operators import LT, And
from loguru import logger

from app.models.astrologer import Astrologer, Availability
from app.models.base import utcnow

# How often an open panel reports in.
BEAT_SECONDS = 20

# How long a report stays good for. Two missed beats plus a little slack, so an
# ordinary hiccup does not flicker the directory.
TTL_SECONDS = 50


def is_fresh(availability: Availability) -> bool:
    """Has this astrologer's panel reported in recently enough to count?"""
    seen = availability.last_seen_at
    if seen is None:
        return False
    return (utcnow() - seen).total_seconds() <= TTL_SECONDS


def is_effectively_online(availability: Availability) -> bool:
    """The only definition of "online" anything should use.

    Both halves must hold: they meant to be available, and they are still here.
    """
    return bool(availability.is_online) and is_fresh(availability)


def can_take(availability: Availability, mode_field: str) -> bool:
    """Online, not already in a session, and open to this kind of consultation."""
    return (
        is_effectively_online(availability)
        and not availability.is_busy
        and bool(getattr(availability, mode_field))
    )


def stale_before():
    """The cutoff a `last_seen_at` must be at or after to still count."""
    return utcnow() - timedelta(seconds=TTL_SECONDS)


# --------------------------------------------------------------- writes
async def beat(profile: Astrologer) -> Astrologer:
    """An open panel saying it is still there.

    Also flips `is_online` on, so that simply opening the panel is what puts an
    astrologer on the directory — they do not have to remember a switch.
    """
    now = utcnow()
    was_online = is_effectively_online(profile.availability)

    profile.availability.last_seen_at = now
    if not profile.availability.is_online:
        profile.availability.is_online = True
        profile.availability.last_online_at = now

    await profile.save()

    if not was_online:
        logger.info("Astrologer {} is online.", profile.display_name)
    await _publish(profile)
    return profile


async def go_offline(profile: Astrologer, *, reason: str = "closed") -> Astrologer:
    """The panel is closing, or the astrologer switched themselves off.

    `last_seen_at` is cleared as well as the flag. Leaving a fresh timestamp
    behind would make the astrologer look merely switched-off rather than gone,
    and a later `is_online` write from a stale tab could revive them.
    """
    if not profile.availability.is_online and profile.availability.last_seen_at is None:
        return profile

    profile.availability.is_online = False
    profile.availability.last_seen_at = None
    await profile.save()

    logger.info("Astrologer {} is offline ({}).", profile.display_name, reason)
    await _publish(profile)
    return profile


async def sweep() -> dict[str, int]:
    """Settle the stored flag for anyone who stopped reporting in.

    Correctness does not depend on this — every read applies the TTL itself —
    but it keeps MongoDB agreeing with the site, and it pushes one last update
    to anyone subscribed to the live mirror.
    """
    cutoff = stale_before()
    stale = await Astrologer.find(
        And(
            Astrologer.availability.is_online == True,  # noqa: E712
            # `$lt` against a date never matches null, so this finds only those
            # who heartbeated at some point and then stopped. The ones who
            # never heartbeated at all are collected separately below.
            LT(Astrologer.availability.last_seen_at, cutoff),
        )
    ).to_list()

    never_seen = await Astrologer.find(
        And(
            Astrologer.availability.is_online == True,  # noqa: E712
            Astrologer.availability.last_seen_at == None,  # noqa: E711
        )
    ).to_list()

    for profile in [*stale, *never_seen]:
        await go_offline(profile, reason="heartbeat stopped")

    return {"marked_offline": len(stale) + len(never_seen)}


async def _publish(profile: Astrologer) -> None:
    """Push the change to anyone watching, without ever failing the request."""
    from app.services import realtime

    await realtime.publish_astrologer(profile)


__all__ = [
    "BEAT_SECONDS",
    "TTL_SECONDS",
    "beat",
    "can_take",
    "go_offline",
    "is_effectively_online",
    "is_fresh",
    "stale_before",
    "sweep",
]
