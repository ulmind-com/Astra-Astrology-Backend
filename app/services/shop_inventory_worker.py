"""Automated background worker for shop inventory TTL & abandoned checkout stock reversion.

Periodically sweeps uncompleted/abandoned Razorpay checkouts where payment was not
completed within the reservation window (e.g. 20 minutes) and safely restores reserved
product stock back into active store inventory.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from loguru import logger
from pymongo.errors import PyMongoError

from app.models.cms import CMS_KEY_SHOP, ShopCMS
from app.models.enums import ShopOrderStatus, ShopPaymentMethod, ShopPaymentStatus
from app.models.shop import Product, ShopOrder


async def sweep_abandoned_shop_checkouts() -> int:
    """Finds all expired abandoned Razorpay checkouts, releases stock atomically, and marks them EXPIRED.

    Returns the count of orders whose inventory was successfully restored.
    """
    now = datetime.now(UTC)

    # Fetch configured reservation window from CMS (default 20 mins)
    default_reservation_mins = 20
    try:
        cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
        if cms:
            default_reservation_mins = getattr(cms, "checkout_reservation_minutes", 20) or 20
    except Exception as e:
        logger.debug("Could not read ShopCMS reservation config, using fallback {}m: {}", default_reservation_mins, e)

    fallback_threshold = now - timedelta(minutes=default_reservation_mins)

    # Query criteria:
    # 1. Payment method is Razorpay (online gateway)
    # 2. Payment status is PENDING (user has not paid)
    # 3. Order status is PLACED (not confirmed, shipped, or delivered)
    # 4. Stock has not already been restored
    # 5. EITHER stock_reserved_until <= now, OR created_at <= fallback_threshold
    query = {
        "payment_method": ShopPaymentMethod.RAZORPAY.value,
        "payment_status": ShopPaymentStatus.PENDING.value,
        "order_status": ShopOrderStatus.PLACED.value,
        "is_stock_restored": {"$ne": True},
        "$or": [
            {"stock_reserved_until": {"$lte": now}},
            {
                "stock_reserved_until": None,
                "created_at": {"$lte": fallback_threshold},
            },
        ],
    }

    try:
        expired_orders = await ShopOrder.find(query).to_list()
    except PyMongoError as db_err:
        logger.warning(
            "Shop inventory sweep skipped (MongoDB replica set failover or transient timeout): {}",
            db_err,
        )
        return 0
    except Exception as exc:
        logger.opt(exception=exc).error("Failed to query expired abandoned orders: {}", exc)
        return 0

    if not expired_orders:
        return 0

    restored_count = 0
    for order in expired_orders:
        try:
            # Atomically lock and update this order to avoid race conditions with payment webhook or concurrent sweeps
            updated_doc = await ShopOrder.get_pymongo_collection().find_one_and_update(
                {
                    "_id": order.id,
                    "payment_status": ShopPaymentStatus.PENDING,
                    "order_status": ShopOrderStatus.PLACED,
                    "is_stock_restored": {"$ne": True},
                },
                {
                    "$set": {
                        "order_status": ShopOrderStatus.EXPIRED,
                        "payment_status": ShopPaymentStatus.EXPIRED,
                        "is_stock_restored": True,
                        "stock_restored_at": now,
                        "cancellation_reason": "Checkout expired: online payment was not completed within the reservation window.",
                        "updated_at": now,
                    },
                    "$push": {
                        "status_history": {
                            "status": ShopOrderStatus.EXPIRED,
                            "changed_at": now,
                            "notes": f"Checkout automatically expired after {default_reservation_mins} mins. Reserved inventory restored to store catalog.",
                        }
                    },
                },
                return_document=False,  # Returns doc before update
            )

            if not updated_doc:
                # Order was already modified by payment or another process; skip
                continue

            # Safely restore inventory for all items in this order
            for it in order.items:
                await Product.get_pymongo_collection().update_one(
                    {"_id": it.product_id},
                    {"$inc": {"stock_quantity": it.quantity}},
                )

            restored_count += 1
            logger.info(
                "Restored inventory for expired abandoned order '{}' ({} items restored).",
                order.order_number,
                len(order.items),
            )
        except PyMongoError as db_err:
            logger.warning(
                "Database error releasing inventory for expired order {} (will retry next sweep): {}",
                order.order_number,
                db_err,
            )
        except Exception as exc:
            logger.opt(exception=exc).error(
                "Error releasing inventory for expired order {}: {}", order.order_number, exc
            )

    if restored_count > 0:
        logger.success(
            "Shop Inventory TTL Sweep completed: {} abandoned order(s) expired and stock restored.",
            restored_count,
        )

    return restored_count


async def periodic_shop_inventory_cleanup_loop(interval_seconds: int = 300) -> None:
    """Runs a periodic background worker (every 5 mins by default) to expire abandoned checkouts.

    Initial grace sleep of 30 seconds ensures DB connection and server bootstrap are ready.
    """
    logger.info(
        "Periodic Shop Inventory TTL cleaner loop started (interval: {} seconds).",
        interval_seconds,
    )
    try:
        await asyncio.sleep(30)
    except asyncio.CancelledError:
        logger.info("Shop inventory TTL cleaner initial wait cancelled.")
        return

    while True:
        try:
            await sweep_abandoned_shop_checkouts()
        except asyncio.CancelledError:
            logger.info("Shop inventory TTL cleaner received cancellation signal. Stopping.")
            break
        except PyMongoError as db_err:
            logger.warning(
                "MongoDB temporarily unavailable in shop inventory cleaner loop (will retry next cycle): {}",
                db_err,
            )
        except Exception as exc:
            logger.opt(exception=exc).error("Unexpected error in shop inventory cleaner loop: {}", exc)

        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Shop inventory TTL cleaner sleep cancelled. Exiting.")
            break
