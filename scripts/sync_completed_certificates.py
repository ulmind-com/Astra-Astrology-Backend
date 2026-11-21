"""Standalone migration & reconciliation script for completed course certificates.

Scans all course enrollments in the database, identifies any users who completed
their course (100% progress or all lessons completed), and ensures their certificate
records, cryptographic signatures, canonical hashes, and verification URLs are
synchronized with the latest DivinLink specifications.
"""

import asyncio
from loguru import logger

from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.services.course_service import CourseService


async def main() -> None:
    logger.info("Connecting to MongoDB to reconcile completed course certificates...")
    connected = await connect_to_mongo()
    if not connected:
        logger.error("Failed to connect to MongoDB.")
        return

    try:
        result = await CourseService.reconcile_all_completed_certificates()
        logger.success(
            "Reconciliation complete: checked={}, completed={}, updated={}",
            result["total_enrollments_checked"],
            result["completed_enrollments"],
            result["certificates_reconciled_and_updated"],
        )
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
