"""Astra Astrology API — application factory and entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import register_middleware
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.services.storage import configure_cloudinary

DESCRIPTION = """
Backend for the **Astra Astrology** platform — astrology, numerology and
astrologer consultations.

Only `/health` is exposed so far; feature routers get added under
`app/api/v1/` as they are built.
"""


def _warn_on_insecure_config() -> None:
    if settings.is_production:
        if settings.SECRET_KEY == "change-me":
            logger.error("SECRET_KEY is still the default value — set it in .env!")
        if "*" in settings.ALLOWED_ORIGINS:
            logger.warning("ALLOWED_ORIGINS is '*' in production.")
    if not settings.resend_configured:
        logger.warning("RESEND_API_KEY is not set — emails will not be delivered.")
    if not settings.cloudinary_configured:
        logger.warning("Cloudinary is not configured — uploads will fail.")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info("Starting {} ({})", settings.APP_NAME, settings.APP_ENV)
    _warn_on_insecure_config()

    await connect_to_mongo()
    configure_cloudinary()

    logger.success("{} is ready on port {}.", settings.APP_NAME, settings.PORT)
    yield

    logger.info("Shutting down...")
    await close_mongo_connection()


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.APP_NAME} API",
        description=DESCRIPTION,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        swagger_ui_parameters={"persistAuthorization": True},
    )

    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": f"{settings.APP_NAME} API",
            "version": "0.1.0",
            "environment": settings.APP_ENV,
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
