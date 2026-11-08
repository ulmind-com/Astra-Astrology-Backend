"""Automated background worker for periodic Cloudinary phantom image cleanup.

Runs in the background every 24 hours (or configured interval), safely scanning
the 'products/' Cloudinary directory and purging unreferenced draft images
older than 2 hours to avoid accumulating storage quota waste.
"""

import asyncio
from loguru import logger

from app.services.shop_admin import purge_unreferenced_cloudinary_shop_images


async def periodic_cloudinary_orphan_cleaner_loop(interval_seconds: int = 86400) -> None:
    """Runs a periodic garbage collection sweep of unreferenced Cloudinary product images.

    Default interval is 24 hours (86,400 seconds). The worker sleeps for 10 minutes
    initially so server bootstrap and health checks complete cleanly.
    """
    logger.info(
        "Periodic Cloudinary orphan cleaner loop started (interval: {} seconds).",
        interval_seconds,
    )
    # Initial sleep of 10 minutes after application startup
    try:
        await asyncio.sleep(600)
    except asyncio.CancelledError:
        logger.info("Cloudinary orphan cleaner initial wait cancelled.")
        return

    while True:
        try:
            logger.info("Starting automated sweep of unreferenced Cloudinary shop images...")
            report = await purge_unreferenced_cloudinary_shop_images(dry_run=False)
            logger.info(
                "Automated Cloudinary orphan sweep completed: scanned={}, referenced={}, orphaned={}, purged={}, failed={}",
                report.scanned_count,
                report.referenced_count,
                report.orphaned_found_count,
                report.purged_count,
                report.failed_count,
            )
        except asyncio.CancelledError:
            logger.info("Cloudinary orphan cleaner loop stopped gracefully.")
            break
        except Exception as exc:
            logger.error("Error in automated Cloudinary orphan cleaner sweep: {}", exc)

        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Cloudinary orphan cleaner sleep cancelled.")
            break
