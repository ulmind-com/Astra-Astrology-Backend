"""Force every astrologer online for local demos.

Presence needs is_online=True AND a fresh last_seen_at (<=50s). Seed accounts
have no live panel, so they never go green. For a localhost demo we set a
far-future last_seen_at so is_fresh() stays true without a heartbeat.

    uv run python scripts/force_online.py --db astra_astrology
    uv run python scripts/force_online.py --db astra_astrology --offline   # revert
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from pymongo import AsyncMongoClient  # noqa: E402


async def main(db_name: str, offline: bool) -> int:
    client = AsyncMongoClient(settings.MONGODB_URI)
    db = client[db_name]

    if offline:
        update = {"$set": {"availability.is_online": False}}
    else:
        future = datetime.now(timezone.utc) + timedelta(days=3650)
        update = {
            "$set": {
                "availability.is_online": True,
                "availability.is_busy": False,
                "availability.last_seen_at": future,
            }
        }

    result = await db.astrologers.update_many({}, update)
    state = "offline" if offline else "online (demo)"
    print(f"{db_name}: set {result.modified_count} astrologers {state}.")
    await client.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=settings.MONGODB_DB_NAME)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.db, args.offline)))
