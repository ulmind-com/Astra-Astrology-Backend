"""Live presence and availability state for Purohits (Uber-style online + busy lock)."""

from datetime import UTC, datetime, timedelta

from beanie.operators import GT, LT, And, Or
from loguru import logger

from app.models.purohit import Purohit

# Panel sends heartbeat every ~20s via WebSocket; two missed beats plus slack = 50s TTL.
BEAT_SECONDS = 20
TTL_SECONDS = 50


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def is_fresh(purohit: Purohit) -> bool:
    """Has this Purohit's dashboard/desk reported in recently enough to count as live?"""
    seen = _as_utc(getattr(purohit, "last_seen_at", None))
    if seen is None:
        return False
    diff = (_utcnow() - seen).total_seconds()
    return -5 <= diff <= TTL_SECONDS


def is_effectively_online(purohit: Purohit) -> bool:
    """True only when the Purohit is online AND their session heartbeat is fresh."""
    return bool(purohit.is_online) and is_fresh(purohit)


def is_available_for_live_puja(purohit: Purohit) -> bool:
    """Online, verified, and not currently busy in another puja."""
    return bool(purohit.is_verified) and is_effectively_online(purohit) and not bool(purohit.is_busy)


def stale_before() -> datetime:
    """Cutoff `last_seen_at` must meet or exceed to count as connected."""
    return _utcnow() - timedelta(seconds=TTL_SECONDS)


async def beat(purohit: Purohit, *, force_online: bool = False) -> Purohit:
    """Refresh Purohit heartbeat timestamp.

    `force_online=True` is used on dashboard login/WebSocket connect so simply opening the
    Purohit desk brings them live immediately. Routine keep-alive pings pass
    `force_online=False` so a Purohit who manually switched offline stays offline.
    """
    now = _utcnow()
    was_effectively_online = is_effectively_online(purohit)
    should_be_online = True if force_online else bool(purohit.is_online)

    purohit.last_seen_at = now
    status_changed = False
    if should_be_online and not purohit.is_online:
        purohit.is_online = True
        purohit.last_online_at = now
        status_changed = True
    elif should_be_online and purohit.last_online_at is None:
        purohit.last_online_at = now

    update_fields: dict = {
        "last_seen_at": now,
        "updated_at": now,
    }
    if should_be_online:
        update_fields["is_online"] = True
        if purohit.last_online_at:
            update_fields["last_online_at"] = purohit.last_online_at

    await Purohit.get_pymongo_collection().update_one(
        {"_id": purohit.id},
        {"$set": update_fields},
    )

    if should_be_online and (not was_effectively_online or status_changed):
        logger.info("Purohit {} is live online.", purohit.display_name)
        await _publish(purohit)

    return purohit


async def go_offline(purohit: Purohit, *, reason: str = "closed") -> Purohit:
    """Mark Purohit offline and clear `last_seen_at` so stale clients cannot revive them."""
    if not purohit.is_online and purohit.last_seen_at is None:
        return purohit

    now = _utcnow()
    purohit.is_online = False
    purohit.last_seen_at = None

    await Purohit.get_pymongo_collection().update_one(
        {"_id": purohit.id},
        {
            "$set": {
                "is_online": False,
                "last_seen_at": None,
                "updated_at": now,
            }
        },
    )

    logger.info("Purohit {} is offline ({}).", purohit.display_name, reason)
    await _publish(purohit)
    return purohit


async def sweep() -> dict[str, int]:
    """Settle `is_online` for Purohits whose dashboard heartbeat stopped arriving."""
    now = _utcnow()
    cutoff = stale_before()
    future_cutoff = now + timedelta(seconds=5)

    stale = await Purohit.find(
        And(
            Purohit.is_online == True,  # noqa: E712
            Or(
                LT(Purohit.last_seen_at, cutoff),
                GT(Purohit.last_seen_at, future_cutoff),
            ),
        )
    ).to_list()

    never_seen = await Purohit.find(
        And(
            Purohit.is_online == True,  # noqa: E712
            Purohit.last_seen_at == None,  # noqa: E711
        )
    ).to_list()

    count = 0
    for profile in [*stale, *never_seen]:
        await go_offline(profile, reason="heartbeat stopped")
        count += 1

    return {"marked_offline": count}


async def _publish(purohit: Purohit) -> None:
    """Broadcast updated Purohit card over the live WebSocket."""
    from app.services import realtime

    await realtime.publish_purohit(purohit)


__all__ = [
    "BEAT_SECONDS",
    "TTL_SECONDS",
    "beat",
    "go_offline",
    "is_available_for_live_puja",
    "is_effectively_online",
    "is_fresh",
    "stale_before",
    "sweep",
]
