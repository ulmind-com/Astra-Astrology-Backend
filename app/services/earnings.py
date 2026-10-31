"""Reading back what was earned.

Two audiences, two truths from one ledger: an astrologer is shown what they
were credited, and nothing about the commission that was taken — the client was
explicit about that. An admin sees the whole split.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from beanie import PydanticObjectId

from app.models.earning import EarningEntry


def _windows(now: datetime | None = None) -> dict[str, datetime]:
    now = now or datetime.now(UTC)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        # The week starts on Monday, which is how most people read "this week".
        "today": midnight,
        "this_week": midnight - timedelta(days=midnight.weekday()),
        "this_month": midnight.replace(day=1),
        "all_time": datetime(1970, 1, 1, tzinfo=UTC),
    }


async def _totals(match: dict[str, Any]) -> dict[str, int]:
    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": None,
                "earning_paise": {"$sum": "$earning_paise"},
                "gross_paise": {"$sum": "$gross_paise"},
                "commission_paise": {"$sum": "$commission_paise"},
                "coins_charged": {"$sum": "$coins_charged"},
                "minutes": {"$sum": 1},
                "sessions": {"$addToSet": "$session_id"},
            }
        },
    ]
    cursor = await EarningEntry.get_pymongo_collection().aggregate(pipeline)
    rows = [row async for row in cursor]
    if not rows:
        return {
            "earning_paise": 0, "gross_paise": 0, "commission_paise": 0,
            "coins_charged": 0, "minutes": 0, "sessions": 0,
        }
    row = rows[0]
    row["sessions"] = len(row.get("sessions") or [])
    row.pop("_id", None)
    return row


async def for_astrologer(astrologer_user_id: PydanticObjectId) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for name, since in _windows().items():
        out[name] = await _totals(
            {"astrologer_user_id": astrologer_user_id, "created_at": {"$gte": since}}
        )
    return out


# The ledger holds one row per minute, because that is what makes a charge
# impossible to apply twice. Nobody wants to read it that way: a five-minute
# call should be one line saying five minutes, not five lines saying one.
_SESSION_GROUP = {
    "_id": "$session_id",
    "mode": {"$first": "$mode"},
    "astrologer_id": {"$first": "$astrologer_id"},
    "user_id": {"$first": "$user_id"},
    "minutes": {"$sum": 1},
    "coins_charged": {"$sum": "$coins_charged"},
    "gross_paise": {"$sum": "$gross_paise"},
    "commission_paise": {"$sum": "$commission_paise"},
    "earning_paise": {"$sum": "$earning_paise"},
    "commission_percent": {"$first": "$commission_percent"},
    # When the session started, so the list reads in the order things happened.
    "created_at": {"$min": "$created_at"},
}


async def _grouped(match: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": match},
        {"$group": _SESSION_GROUP},
        {"$sort": {"created_at": -1}},
        {"$limit": limit},
    ]
    cursor = await EarningEntry.get_pymongo_collection().aggregate(pipeline)
    return [row async for row in cursor]


async def recent_for_astrologer(
    astrologer_user_id: PydanticObjectId, limit: int = 50
) -> list[dict[str, Any]]:
    """One row per consultation, not per minute."""
    return await _grouped({"astrologer_user_id": astrologer_user_id}, limit)


async def platform_totals(since: datetime | None = None) -> dict[str, int]:
    match: dict[str, Any] = {}
    if since is not None:
        match["created_at"] = {"$gte": since}
    return await _totals(match)


async def recent_all(limit: int = 100) -> list[dict[str, Any]]:
    return await _grouped({}, limit)
