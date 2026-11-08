"""Reading back what was earned.

Two audiences, two truths from one ledger: an astrologer is shown what they
were credited, and nothing about the commission that was taken — the client was
explicit about that. An admin sees the whole split.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId

from app.models.earning import EarningEntry

IST = ZoneInfo("Asia/Kolkata")


def _windows(now: datetime | None = None) -> dict[str, datetime]:
    """Calculate date windows strictly based on Indian Standard Time (IST, UTC+5:30).

    MongoDB stores timestamps in UTC. To calculate:
    - Today: Starts at 00:00:00 IST of today, converted to UTC.
      (e.g., Nov 8 00:00 IST is Nov 7 18:30 UTC).
      Any consultation at 01:00 AM IST on Nov 8 (Nov 7 19:30 UTC) is correctly >= Nov 7 18:30 UTC.
    - This Week: Starts on Monday at 00:00:00 IST, converted to UTC.
    - This Month: Starts on the 1st of the month at 00:00:00 IST, converted to UTC.
    """
    if now is None:
        now_utc = datetime.now(UTC)
    elif now.tzinfo is None:
        now_utc = now.replace(tzinfo=UTC)
    else:
        now_utc = now.astimezone(UTC)

    now_ist = now_utc.astimezone(IST)

    # Midnight in IST, converted back to UTC for exact timestamp comparison
    midnight_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    today_utc = midnight_ist.astimezone(UTC)

    # The week starts on Monday in IST
    week_start_ist = midnight_ist - timedelta(days=midnight_ist.weekday())
    this_week_utc = week_start_ist.astimezone(UTC)

    # Start of month in IST
    month_start_ist = midnight_ist.replace(day=1)
    this_month_utc = month_start_ist.astimezone(UTC)

    return {
        "today": today_utc,
        "this_week": this_week_utc,
        "this_month": this_month_utc,
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
    cursor = await EarningEntry.get_pymongo_collection().aggregate(pipeline, allowDiskUse=True)
    rows = [row async for row in cursor]
    if not rows:
        return {
            "earning_paise": 0,
            "gross_paise": 0,
            "commission_paise": 0,
            "coins_charged": 0,
            "minutes": 0,
            "sessions": 0,
        }
    row = rows[0]
    row["sessions"] = len(row.get("sessions") or [])
    row.pop("_id", None)
    return row


async def for_astrologer(astrologer_user_id: PydanticObjectId) -> dict[str, dict[str, int]]:
    # Sync any completed appointments not yet in ledger
    try:
        from app.services.appointments import backfill_completed_appointment_earnings

        await backfill_completed_appointment_earnings(astrologer_user_id)
    except Exception:
        pass

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


async def _build_search_match(search: str | None) -> dict[str, Any]:
    """Helper to convert a search term into indexed MongoDB query criteria."""
    if not search or not search.strip():
        return {}
    q = search.strip()
    or_clauses: list[dict[str, Any]] = []

    # Check if search string is a valid 24-char hex ObjectId
    if PydanticObjectId.is_valid(q):
        oid = PydanticObjectId(q)
        or_clauses.append({"session_id": oid})
        or_clauses.append({"user_id": oid})

    # Search User collection by name or email
    try:
        from app.models.user import User

        matched_users = await User.find(
            {
                "$or": [
                    {"first_name": {"$regex": q, "$options": "i"}},
                    {"last_name": {"$regex": q, "$options": "i"}},
                    {"email": {"$regex": q, "$options": "i"}},
                ]
            }
        ).limit(100).to_list()

        if matched_users:
            uids = [u.id for u in matched_users]
            or_clauses.append({"user_id": {"$in": uids}})
    except Exception:
        pass

    if or_clauses:
        return {"$or": or_clauses}
    # If a search term was provided but matched no users and wasn't an ObjectId, match nothing
    return {"user_id": PydanticObjectId("000000000000000000000000")}


async def _grouped(match: dict[str, Any], limit: int, skip: int = 0) -> list[dict[str, Any]]:
    pipeline: list[dict[str, Any]] = [
        {"$match": match},
        {
            "$project": {
                "session_id": 1,
                "mode": 1,
                "astrologer_id": 1,
                "astrologer_user_id": 1,
                "user_id": 1,
                "coins_charged": 1,
                "gross_paise": 1,
                "commission_paise": 1,
                "earning_paise": 1,
                "commission_percent": 1,
                "created_at": 1,
            }
        },
        {"$group": _SESSION_GROUP},
        {"$sort": {"created_at": -1}},
    ]
    if skip > 0:
        pipeline.append({"$skip": skip})
    pipeline.append({"$limit": limit})
    cursor = await EarningEntry.get_pymongo_collection().aggregate(pipeline, allowDiskUse=True)
    return [row async for row in cursor]


async def count_sessions(match: dict[str, Any]) -> int:
    """Count unique consultation sessions matching criteria using index-friendly pipeline."""
    pipeline: list[dict[str, Any]] = [
        {"$match": match},
        {"$group": {"_id": "$session_id"}},
        {"$count": "total"},
    ]
    cursor = await EarningEntry.get_pymongo_collection().aggregate(pipeline, allowDiskUse=True)
    rows = [row async for row in cursor]
    return rows[0]["total"] if rows else 0


async def recent_for_astrologer(
    astrologer_user_id: PydanticObjectId,
    limit: int = 50,
    skip: int = 0,
    mode: str | None = None,
    search: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[dict[str, Any]]:
    """One row per consultation, not per minute."""
    match: dict[str, Any] = {"astrologer_user_id": astrologer_user_id}
    if mode:
        match["mode"] = mode
    if since is not None or until is not None:
        created_match: dict[str, Any] = {}
        if since is not None:
            created_match["$gte"] = since
        if until is not None:
            created_match["$lte"] = until
        match["created_at"] = created_match

    if search:
        search_filter = await _build_search_match(search)
        if search_filter:
            match.update(search_filter)

    return await _grouped(match, limit, skip)


async def paginated_for_astrologer(
    astrologer_user_id: PydanticObjectId,
    page: int = 1,
    limit: int = 10,
    mode: str | None = None,
    search: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Return paginated sessions and exact total count for an astrologer."""
    page = max(1, page)
    limit = max(1, min(limit, 200))
    skip = (page - 1) * limit

    match: dict[str, Any] = {"astrologer_user_id": astrologer_user_id}
    if mode:
        match["mode"] = mode
    if since is not None or until is not None:
        created_match: dict[str, Any] = {}
        if since is not None:
            created_match["$gte"] = since
        if until is not None:
            created_match["$lte"] = until
        match["created_at"] = created_match

    if search:
        search_filter = await _build_search_match(search)
        if search_filter:
            match.update(search_filter)

    rows = await _grouped(match, limit=limit, skip=skip)
    total = await count_sessions(match)
    return rows, total


async def platform_totals(since: datetime | None = None) -> dict[str, int]:
    match: dict[str, Any] = {}
    if since is not None:
        match["created_at"] = {"$gte": since}
    return await _totals(match)


async def recent_all(
    limit: int = 100,
    skip: int = 0,
    mode: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    match: dict[str, Any] = {}
    if mode:
        match["mode"] = mode
    if search:
        search_filter = await _build_search_match(search)
        if search_filter:
            match.update(search_filter)
    return await _grouped(match, limit, skip)


async def paginated_all(
    page: int = 1,
    limit: int = 20,
    mode: str | None = None,
    search: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Return paginated consultation ledger sessions for admin."""
    page = max(1, page)
    limit = max(1, min(limit, 200))
    skip = (page - 1) * limit

    match: dict[str, Any] = {}
    if mode:
        match["mode"] = mode
    if search:
        search_filter = await _build_search_match(search)
        if search_filter:
            match.update(search_filter)

    rows = await _grouped(match, limit=limit, skip=skip)
    total = await count_sessions(match)
    return rows, total
