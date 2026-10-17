"""Converts wallets written before coins existed.

Older rows stored `balance_paise` / `amount_paise`; the wallet now holds coins.
This rewrites them at a rate you choose, defaulting to 1 coin per rupee so
nobody's balance changes value unless you ask for it.

    uv run python scripts/migrate_wallet_to_coins.py --rate 1
    uv run python scripts/migrate_wallet_to_coins.py --rate 10 --apply

Without --apply it only reports what it would do.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from pymongo import AsyncMongoClient  # noqa: E402


async def main(rate: int, apply: bool) -> int:
    client = AsyncMongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    wallets = db["wallets"]
    txns = db["wallet_transactions"]
    orders = db["payment_orders"]

    stale_wallets = await wallets.count_documents({"balance_paise": {"$exists": True}})
    stale_txns = await txns.count_documents({"amount_paise": {"$exists": True}, "amount_coins": {"$exists": False}})
    stale_orders = await orders.count_documents({"coins": {"$exists": False}})

    print(f"database : {settings.MONGODB_DB_NAME}")
    print(f"rate     : {rate} coin(s) per rupee")
    print(f"wallets  : {stale_wallets} to convert")
    print(f"ledger   : {stale_txns} row(s) to convert")
    print(f"orders   : {stale_orders} to backfill")

    if not (stale_wallets or stale_txns or stale_orders):
        print("\nNothing to do.")
        await client.close()
        return 0

    if not apply:
        print("\nDry run — pass --apply to write.")
        await client.close()
        return 0

    # paise -> coins, using integer arithmetic so nothing is rounded away.
    async for w in wallets.find({"balance_paise": {"$exists": True}}):
        coins = (w["balance_paise"] // 100) * rate
        await wallets.update_one(
            {"_id": w["_id"]},
            {"$set": {"balance_coins": coins}, "$unset": {"balance_paise": "", "currency": ""}},
        )

    async for t in txns.find({"amount_paise": {"$exists": True}, "amount_coins": {"$exists": False}}):
        amount_coins = (t["amount_paise"] // 100) * rate
        after_coins = (t.get("balance_after_paise", 0) // 100) * rate
        update: dict = {
            "$set": {
                "amount_coins": amount_coins,
                "balance_after_coins": after_coins,
                "coins_per_rupee": rate,
            },
            "$unset": {"balance_after_paise": "", "currency": ""},
        }
        # `amount_paise` stays on recharge rows (it is what was actually paid)
        # and is dropped everywhere else, where it never meant money.
        if t.get("reason") not in {"recharge", "refund"}:
            update["$unset"]["amount_paise"] = ""
            update["$set"]["coins_per_rupee"] = None
        await txns.update_one({"_id": t["_id"]}, update)

    async for o in orders.find({"coins": {"$exists": False}}):
        await orders.update_one(
            {"_id": o["_id"]},
            {"$set": {"coins_per_rupee": rate, "coins": (o["amount_paise"] // 100) * rate}},
        )

    print("\nDone. Re-run with the reconcile endpoint to confirm each balance "
          "still matches its ledger.")
    await client.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rate", type=int, default=1, help="coins per rupee (default 1)")
    parser.add_argument("--apply", action="store_true", help="actually write the changes")
    args = parser.parse_args()
    if args.rate < 1:
        parser.error("--rate must be 1 or more")
    raise SystemExit(asyncio.run(main(args.rate, args.apply)))
