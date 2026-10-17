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
from app.services.firebase import init_firebase
from app.services.storage import configure_cloudinary

DESCRIPTION = """
Backend for the **Astra Astrology** platform — astrology, numerology and
astrologer consultations.

* `auth` — registration via email+password (OTP verified) and Google sign-in,
  kept in sync between MongoDB and Firebase Auth
* `health` — liveness and readiness
"""


def _check_config() -> None:
    """Refuses to start a production deploy that is misconfigured.

    These are failures that are silent and expensive in production — leaked
    OTPs, forgeable tokens — so the deploy stops rather than serving traffic
    with them.
    """
    problems: list[str] = []
    warnings: list[str] = []

    # Wrong in every environment: the app cannot do anything without a database,
    # and an empty or malformed URI is always a mistake rather than an outage.
    # Failing here means the host keeps the last working deploy running.
    uri = settings.MONGODB_URI.strip()
    if not uri:
        problems.append(
            "MONGODB_URI is empty. Set it to your connection string "
            "(mongodb+srv://... from Atlas > Connect > Drivers)."
        )
    elif not uri.startswith(("mongodb://", "mongodb+srv://")):
        problems.append(
            "MONGODB_URI must start with 'mongodb://' or 'mongodb+srv://' — "
            f"got '{uri.split(':')[0]}...'."
        )

    if settings.is_production:
        if settings.OTP_DEV_MODE:
            problems.append(
                "OTP_DEV_MODE is true — verification codes would be returned in API "
                "responses, letting anyone register as anyone. Set it to false."
            )
        if settings.SECRET_KEY == "change-me":
            problems.append("SECRET_KEY is still the default value.")
        if settings.JWT_SECRET_KEY == "change-me":
            problems.append("JWT_SECRET_KEY is still the default value.")
        if len(settings.JWT_SECRET_KEY) < 32:
            problems.append(
                "JWT_SECRET_KEY is shorter than 32 characters, which weakens every "
                'access token. Generate one with: python -c "import secrets; '
                'print(secrets.token_urlsafe(48))"'
            )
        if settings.DEBUG:
            warnings.append("DEBUG is true in production — error responses leak internals.")
        if "*" in settings.ALLOWED_ORIGINS:
            warnings.append("ALLOWED_ORIGINS is '*' in production.")
        if settings.FIREBASE_REQUIRED and not settings.firebase_configured:
            problems.append(
                "FIREBASE_REQUIRED is true but no Firebase credentials are set, so "
                "nobody would be able to register."
            )
        if not settings.resend_configured:
            problems.append("RESEND_API_KEY is not set, so sign-up codes could not be delivered.")
        if settings.razorpay_is_test_key:
            problems.append(
                "RAZORPAY_KEY_ID is a test key (rzp_test_). Real recharges would never "
                "reach the account. Use the live key."
            )
        if settings.razorpay_configured and not settings.razorpay_webhook_configured:
            warnings.append(
                "RAZORPAY_WEBHOOK_SECRET is not set — webhooks will be rejected, so a "
                "recharge whose browser callback is lost (common on UPI) never credits."
            )

    if not settings.resend_configured:
        warnings.append("RESEND_API_KEY is not set — emails will not be delivered.")
    if not settings.cloudinary_configured:
        warnings.append("Cloudinary is not configured — uploads will fail.")
    if not settings.firebase_configured:
        warnings.append(
            "Firebase is not configured — registration is refused while FIREBASE_REQUIRED is true."
        )

    for warning in warnings:
        logger.warning(warning)

    if problems:
        for problem in problems:
            logger.error("CONFIG: {}", problem)
        raise RuntimeError(
            f"Refusing to start: {len(problems)} bad configuration value(s). "
            "See the CONFIG errors above."
        )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info("Starting {} ({})", settings.APP_NAME, settings.APP_ENV)
    _check_config()

    await connect_to_mongo()
    init_firebase()
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
