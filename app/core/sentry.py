"""Production-grade Sentry integration for FastAPI, Starlette, PyMongo, and Loguru."""

from typing import Any

import sentry_sdk
from loguru import logger
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration
from sentry_sdk.integrations.pymongo import PyMongoIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import settings


def _traces_sampler(sampling_context: dict[str, Any]) -> float:
    """Smart sampler to prevent exhausting Sentry's free tier quotas.

    Filters out noisy health checks, static documentation, and schema routes.
    """
    asgi_scope = sampling_context.get("asgi_scope", {})
    path: str = asgi_scope.get("path", "")

    # Exclude health check and docs from APM transactions (0% sample)
    if path in ("/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json", "/"):
        return 0.0

    # If traces_sample_rate is configured, use it (1.0 in dev, 0.2 in prod)
    if not settings.is_production:
        return 1.0

    return settings.SENTRY_TRACES_SAMPLE_RATE


def _before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Sanitizes sensitive information before sending error events to Sentry."""
    request = event.get("request", {})
    headers = request.get("headers", {})
    if isinstance(headers, dict):
        for sensitive_header in ("authorization", "x-otp", "cookie"):
            if sensitive_header in headers:
                headers[sensitive_header] = "[REDACTED]"

    return event


def init_sentry() -> bool:
    """Initializes Sentry if SENTRY_DSN is configured.

    Returns True if initialized, False otherwise.
    """
    if not settings.sentry_configured:
        logger.debug("Sentry DSN is not set; error tracking is disabled.")
        return False

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        release=f"{settings.APP_NAME.lower()}@{settings.APP_VERSION}",
        traces_sampler=_traces_sampler,
        profile_session_sample_rate=(
            1.0 if not settings.is_production else settings.SENTRY_PROFILES_SAMPLE_RATE
        ),
        profile_lifecycle="trace",
        send_default_pii=False,
        before_send=_before_send,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            PyMongoIntegration(),
            LoguruIntegration(),
        ],
    )
    logger.info("Sentry initialized for environment: {}", settings.APP_ENV)
    return True
