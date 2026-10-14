"""MongoDB connection lifecycle and Beanie initialisation."""

from beanie import init_beanie
from loguru import logger
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings
from app.models import DOCUMENT_MODELS

_client: AsyncMongoClient | None = None
_database: AsyncDatabase | None = None


def get_client() -> AsyncMongoClient:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialised. Call connect_to_mongo() first.")
    return _client


def get_database() -> AsyncDatabase:
    if _database is None:
        raise RuntimeError("MongoDB is not initialised. Call connect_to_mongo() first.")
    return _database


async def connect_to_mongo() -> None:
    """Opens the connection pool, verifies it, then registers the Beanie models."""
    global _client, _database

    logger.info("Connecting to MongoDB database '{}'...", settings.MONGODB_DB_NAME)
    _client = AsyncMongoClient(
        settings.MONGODB_URI,
        maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
        minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
        serverSelectionTimeoutMS=10_000,
        tz_aware=True,
        uuidRepresentation="standard",
    )
    await _client.admin.command("ping")
    _database = _client[settings.MONGODB_DB_NAME]

    await init_beanie(database=_database, document_models=DOCUMENT_MODELS)
    logger.success("MongoDB connected — {} document models registered.", len(DOCUMENT_MODELS))


async def close_mongo_connection() -> None:
    global _client, _database

    if _client is not None:
        await _client.close()
        logger.info("MongoDB connection closed.")
    _client = None
    _database = None


async def ping() -> bool:
    try:
        await get_client().admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001 - health check must never raise
        logger.warning("MongoDB ping failed: {}", exc)
        return False
