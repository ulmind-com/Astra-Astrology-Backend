"""MongoDB connection lifecycle and Beanie initialisation.

Connecting is deliberately non-fatal: if Mongo is unreachable at startup the app
still boots and serves `/health` (reporting `database: disconnected`) instead of
crashing, which would make the host return 502 and trip uptime monitors. The
next successful `ping()` finishes the Beanie setup.
"""

import asyncio
import random
import time
from collections.abc import Callable, Coroutine
from typing import Any

from beanie import init_beanie
from loguru import logger
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    NetworkTimeout,
    ServerSelectionTimeoutError,
    WaitQueueTimeoutError,
)

from app.core.config import settings
from app.models import DOCUMENT_MODELS

_client: AsyncMongoClient | None = None
_database: AsyncDatabase | None = None
_beanie_ready = False
_last_heal_time: float = 0.0
_background_tasks: set[asyncio.Task[Any]] = set()


def _track_task(coro: Coroutine[Any, Any, Any]) -> None:
    """Schedule a background coroutine cleanly and retain a strong ref until completion."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _async_heal_topology(client: AsyncMongoClient) -> None:
    """Safely triggers PyMongo SDAM checks while respecting topology._lock."""
    try:
        topology = getattr(client, "_topology", None)
        if topology is None:
            return
        lock = getattr(topology, "_lock", None)
        if lock is not None and hasattr(topology, "_request_check_all"):
            async with lock:
                topology._request_check_all()
        elif hasattr(topology, "request_check_all"):
            await topology.request_check_all(wait_time=1)
    except (asyncio.CancelledError, Exception):
        pass


def heal_connection() -> None:
    """Schedules a lock-safe PyMongo SDAM topology refresh (debounced every 10s)."""
    global _client, _last_heal_time

    now = time.monotonic()
    if now - _last_heal_time < 10.0:
        return
    _last_heal_time = now

    client = _client
    if client is None:
        return
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    _track_task(_async_heal_topology(client))


async def with_mongo_retry[T](
    coro_fn: Callable[[], Coroutine[Any, Any, T]],
    max_retries: int = 2,
    delay: float = 0.35,
    total_budget: float = 8.0,
) -> T:
    """Executes an async DB operation with bounded-budget jittered retry on transient failures."""
    transient_errors = (
        ConnectionFailure,
        AutoReconnect,
        ServerSelectionTimeoutError,
        NetworkTimeout,
        WaitQueueTimeoutError,
        TimeoutError,
        OSError,
    )
    started = time.monotonic()
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except transient_errors as exc:
            heal_connection()
            elapsed = time.monotonic() - started
            # Fail fast if we already burned the retry budget (prevents 80-210s cascading stalls).
            if attempt >= max_retries or elapsed >= total_budget:
                raise
            backoff = min(1.5, delay * (2**attempt)) + random.uniform(0.0, 0.2)
            logger.warning(
                "Transient MongoDB disconnect attempt {}/{} ({:.2f}s elapsed), retry {:.2f}s: {}",
                attempt + 1,
                max_retries + 1,
                elapsed,
                backoff,
                exc,
            )
            await asyncio.sleep(backoff)
    raise RuntimeError("Unreachable")


def get_client() -> AsyncMongoClient:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialised. Call connect_to_mongo() first.")
    return _client


def get_database() -> AsyncDatabase:
    if _database is None:
        raise RuntimeError("MongoDB is not initialised. Call connect_to_mongo() first.")
    return _database


def is_ready() -> bool:
    """True once the models have been registered against a reachable database."""
    return _beanie_ready


async def _init_models() -> None:
    global _beanie_ready

    try:
        await init_beanie(
            database=get_database(),
            document_models=DOCUMENT_MODELS,
            allow_index_dropping=True,
        )
    except Exception as exc:
        logger.warning(
            "Standard index creation failed ({}); re-initializing with skip_indexes=True...",
            exc,
        )
        await init_beanie(
            database=get_database(),
            document_models=DOCUMENT_MODELS,
            skip_indexes=True,
        )

    _beanie_ready = True
    logger.success("MongoDB ready — {} document models registered.", len(DOCUMENT_MODELS))


async def connect_to_mongo() -> bool:
    """Opens the pool and registers the models. Returns False instead of raising."""
    global _client, _database

    logger.info("Connecting to MongoDB database '{}'...", settings.MONGODB_DB_NAME)

    # Building the client is inside the try as well: a malformed URI raises here,
    # not on the first query, and that must not take the whole app down.
    try:
        from pymongo import ReadPreference

        connect_timeout = min(int(getattr(settings, "MONGODB_CONNECT_TIMEOUT_MS", 5_000)), 6_000)
        server_sel_timeout = min(
            int(getattr(settings, "MONGODB_SERVER_SELECTION_TIMEOUT_MS", 5_000)), 5_000
        )
        socket_timeout = min(int(getattr(settings, "MONGODB_SOCKET_TIMEOUT_MS", 12_000)), 15_000)
        max_idle_time = min(int(getattr(settings, "MONGODB_MAX_IDLE_TIME_MS", 45_000)), 60_000)
        heartbeat_freq = int(getattr(settings, "MONGODB_HEARTBEAT_FREQUENCY_MS", 10_000))
        wait_queue_timeout = min(
            int(getattr(settings, "MONGODB_WAIT_QUEUE_TIMEOUT_MS", 5_000)), 5_000
        )
        # Keep minPoolSize at 0 by default so Render sleep/NAT never keeps half-open sockets
        # or triggers PyMongo background remove_stale_sockets -> _OperationCancelled errors.
        min_pool_size = max(0, int(getattr(settings, "MONGODB_MIN_POOL_SIZE", 0)))
        max_pool_size = min(max(10, int(getattr(settings, "MONGODB_MAX_POOL_SIZE", 50))), 50)

        _client = AsyncMongoClient(
            settings.MONGODB_URI,
            readPreference="primary",
            maxPoolSize=max_pool_size,
            minPoolSize=min_pool_size,
            maxIdleTimeMS=max_idle_time,
            socketTimeoutMS=socket_timeout,
            serverSelectionTimeoutMS=server_sel_timeout,
            connectTimeoutMS=connect_timeout,
            waitQueueTimeoutMS=wait_queue_timeout,
            heartbeatFrequencyMS=heartbeat_freq,
            retryWrites=True,
            retryReads=True,
            tz_aware=True,
            uuidRepresentation="standard",
        )
        _database = _client.get_database(
            settings.MONGODB_DB_NAME,
            read_preference=ReadPreference.PRIMARY,
        )

        await _client.admin.command("ping")
        await _init_models()
        return True
    except Exception as exc:  # noqa: BLE001 - startup must not fail on a DB hiccup
        logger.opt(exception=settings.DEBUG).error(
            "MongoDB is unavailable at startup ({}). The app will keep serving and "
            "retry on the next health check.",
            exc,
        )
        return False


async def close_mongo_connection() -> None:
    global _client, _database, _beanie_ready

    if _client is not None:
        await _client.close()
        logger.info("MongoDB connection closed.")
    _client = None
    _database = None
    _beanie_ready = False


async def ping(timeout: float | None = None) -> bool:
    """Bounded liveness check. Never raises, so a health check can't hang."""
    if _client is None:
        try:
            await connect_to_mongo()
        except Exception:
            return False
        if _client is None:
            return False

    budget = timeout if timeout is not None else settings.HEALTH_DB_TIMEOUT_SECONDS
    try:
        await asyncio.wait_for(_client.admin.command("ping"), timeout=budget)
    except TimeoutError:
        logger.warning("MongoDB ping timed out after {}s.", budget)
        heal_connection()
        return False
    except Exception as exc:  # noqa: BLE001 - health checks must never raise
        logger.warning("MongoDB ping failed: {}", exc)
        heal_connection()
        return False

    # Recover from a startup where the database wasn't up yet.
    if not _beanie_ready:
        try:
            await _init_models()
        except Exception as exc:  # noqa: BLE001 - reported as degraded, not fatal
            logger.warning("Deferred Beanie initialisation failed: {}", exc)

    return True
