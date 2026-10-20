"""Loads the starting palm-reading rule set.

    uv run python -m scripts.seed_palm_rules           # add what is missing
    uv run python -m scripts.seed_palm_rules --force   # overwrite edits too
"""

import asyncio
import sys

from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.services import palm_reading


async def main() -> None:
    force = "--force" in sys.argv
    await connect_to_mongo()
    result = await palm_reading.seed(force=force)
    print(
        f"created {result['created']} · updated {result['updated']} · "
        f"left alone {result['skipped']}"
    )
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
