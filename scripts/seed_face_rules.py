"""Loads the starting face-reading rule set.

    uv run python -m scripts.seed_face_rules           # add what is missing
    uv run python -m scripts.seed_face_rules --force   # overwrite edits too

Without `--force` an existing rule is left exactly as it is, so re-running
this after the client's astrologer has corrected a threshold does not quietly
undo their work.
"""

import asyncio
import sys

from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.services import face_reading


async def main() -> None:
    force = "--force" in sys.argv
    await connect_to_mongo()
    result = await face_reading.seed(force=force)
    print(
        f"created {result['created']} · updated {result['updated']} · "
        f"left alone {result['skipped']}"
    )
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
