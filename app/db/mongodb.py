"""MongoDB connection lifecycle and Beanie initialisation.

Connecting is deliberately non-fatal: if Mongo is unreachable at startup the app
still boots and serves `/health` (reporting `database: disconnected`) instead of
crashing, which would make the host return 502 and trip uptime monitors. The
next successful `ping()` finishes the Beanie setup.
"""

import asyncio

from beanie import init_beanie
from loguru import logger
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings
from app.models import DOCUMENT_MODELS

_client: AsyncMongoClient | None = None
_database: AsyncDatabase | None = None
_beanie_ready = False


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
            "Standard index creation failed ({}); re-initializing with skip_indexes=True to ensure uninterrupted service...",
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
        _client = AsyncMongoClient(
            settings.MONGODB_URI,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            serverSelectionTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
            connectTimeoutMS=settings.MONGODB_CONNECT_TIMEOUT_MS,
            tz_aware=True,
            uuidRepresentation="standard",
        )
        _database = _client[settings.MONGODB_DB_NAME]

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
        return False

    budget = timeout if timeout is not None else settings.HEALTH_DB_TIMEOUT_SECONDS
    try:
        await asyncio.wait_for(_client.admin.command("ping"), timeout=budget)
    except TimeoutError:
        logger.warning("MongoDB ping timed out after {}s.", budget)
        return False
    except Exception as exc:  # noqa: BLE001 - health checks must never raise
        logger.warning("MongoDB ping failed: {}", exc)
        return False

    # Recover from a startup where the database wasn't up yet.
    if not _beanie_ready:
        try:
            await _init_models()
        except Exception as exc:  # noqa: BLE001 - reported as degraded, not fatal
            logger.warning("Deferred Beanie initialisation failed: {}", exc)

    return True
