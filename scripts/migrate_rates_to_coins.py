"""Converts astrologer rates from rupees to coins per minute.

The old `RateCard` held rupees as floats; it now holds whole coins. This
rewrites what is there, at the coin rate currently in force, and drops the
offer fields that no longer exist.

    uv run python scripts/migrate_rates_to_coins.py
    uv run python scripts/migrate_rates_to_coins.py --apply

Anything that converts to less than one coin is left unset, which means "use
the platform default" — better than pricing somebody at zero.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from pymongo import AsyncMongoClient  # noqa: E402

OLD = ("chat_per_minute", "call_per_minute", "video_per_minute")
OFFERS = ("offer_chat_per_minute", "offer_call_per_minute", "offer_video_per_minute")


async def main(apply: bool) -> int:
    client = AsyncMongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    rate = (await db.platform_settings.find_one({"key": "platform"}) or {}).get(
        "coins_per_rupee", 1
    )
    print(f"database : {settings.MONGODB_DB_NAME}")
    print(f"rate     : {rate} coin(s) per rupee\n")

    stale = await db.astrologers.find({"rates.chat_per_minute": {"$exists": True}}).to_list(None)
    if not stale:
        print("Nothing to convert.")
        await client.close()
        return 0

    for a in stale:
        rates = a.get("rates") or {}
        line = [a.get("display_name", "?")]
        update_set, update_unset = {}, {}
        for old, new in zip(OLD, ("chat", "call", "video"), strict=True):
            rupees = float(rates.get(old) or 0)
            coins = int(round(rupees * rate))
            field = f"rates.{new}_coins_per_minute"
            if coins >= 1:
                update_set[field] = coins
                line.append(f"{new} ₹{rupees:g} -> {coins} coins")
            else:
                update_unset[field] = ""
                line.append(f"{new} ₹{rupees:g} -> default")
        for field in OLD + OFFERS + ("currency",):
            update_unset[f"rates.{field}"] = ""

        print("  " + " | ".join(line))
        if apply:
            ops = {}
            if update_set:
                ops["$set"] = update_set
            if update_unset:
                ops["$unset"] = update_unset
            await db.astrologers.update_one({"_id": a["_id"]}, ops)

    print(f"\n{len(stale)} astrologer(s)" + ("" if apply else " — dry run, pass --apply"))
    await client.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.apply)))
