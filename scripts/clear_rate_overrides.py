"""Clears per-astrologer rate and commission overrides.

The rupee-to-coin migration wrote an explicit rate onto every astrologer it
converted. That was heavy-handed: an explicit rate is a *decision* — it pins
that astrologer to a price and makes them ignore the platform default forever.
Most of those were never deliberate, so this puts them back on the default.

    uv run python scripts/clear_rate_overrides.py
    uv run python scripts/clear_rate_overrides.py --apply

Use --keep to leave one astrologer's own pricing alone.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from pymongo import AsyncMongoClient  # noqa: E402

FIELDS = (
    "rates.chat_coins_per_minute",
    "rates.call_coins_per_minute",
    "rates.video_coins_per_minute",
)


async def main(apply: bool, keep: list[str], rates_only: bool) -> int:
    client = AsyncMongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    platform = await db.platform_settings.find_one({"key": "platform"}) or {}
    print(f"database : {settings.MONGODB_DB_NAME}")
    print(
        f"defaults : chat {platform.get('default_chat_coins_per_minute')} | "
        f"call {platform.get('default_call_coins_per_minute')} | "
        f"video {platform.get('default_video_coins_per_minute')} | "
        f"commission {platform.get('default_commission_percent')}%\n"
    )

    keep_lower = {k.lower() for k in keep}
    touched = 0

    async for a in db.astrologers.find({}):
        name = a.get("display_name", "?")
        if name.lower() in keep_lower:
            print(f"  keeping  {name}")
            continue

        rates = a.get("rates") or {}
        own = {k.split(".")[-1]: rates.get(k.split(".")[-1]) for k in FIELDS}
        commission = a.get("commission_percent")
        if all(v is None for v in own.values()) and (rates_only or commission is None):
            continue

        bits = [f"{k.replace('_coins_per_minute', '')}={v}" for k, v in own.items() if v is not None]
        if not rates_only and commission is not None:
            bits.append(f"commission={commission}")
        print(f"  {name}: {', '.join(bits)} -> platform default")
        touched += 1

        if apply:
            unset = {f: "" for f in FIELDS}
            if not rates_only:
                unset["commission_percent"] = ""
            await db.astrologers.update_one({"_id": a["_id"]}, {"$unset": unset})

    print(f"\n{touched} astrologer(s)" + ("" if apply else " — dry run, pass --apply"))
    await client.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--keep", action="append", default=[], help="display name to spare")
    parser.add_argument("--rates-only", action="store_true", help="leave commission alone")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.apply, args.keep, args.rates_only)))
