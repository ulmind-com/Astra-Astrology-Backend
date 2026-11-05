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

    Filters out noisy health checks, static documentation, schema routes,
    and persistent WebSocket streams (which span hours and falsely flag N+1 queries).
    """
    asgi_scope = sampling_context.get("asgi_scope", {})
    path: str = asgi_scope.get("path", "")
    scope_type: str = asgi_scope.get("type", "")

    # Exclude long-lived persistent websockets from APM HTTP transactions
    if scope_type == "websocket" or path.startswith("/api/v1/live"):
        return 0.0

    # Exclude health check and docs from APM transactions (0% sample)
    if path in ("/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json", "/", "/sentry-debug"):
        return 0.0

    # If traces_sample_rate is configured, use it (1.0 in dev, 0.2 in prod)
    if not settings.is_production:
        return 1.0

    return settings.SENTRY_TRACES_SAMPLE_RATE


def _before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Sanitizes sensitive information and discards non-actionable background noise."""
    # 1. Ignore normal expected WebSocket disconnection events
    exc_info = hint.get("exc_info")
    if exc_info:
        exc_type, exc_val, _ = exc_info
        if exc_type and exc_type.__name__ in ("WebSocketDisconnect", "ClientDisconnected"):
            return None
        if exc_val and "connection is closing" in str(exc_val).lower():
            return None

    # 2. Ignore OpenTelemetry exporter shutdown/timeout batch warnings
    logger_name = event.get("logger", "")
    if "opentelemetry" in logger_name or "metric_exporter" in logger_name:
        return None

    log_entry = event.get("logentry", {})
    message = log_entry.get("message", "") or log_entry.get("formatted", "") or ""
    if "Failed to export metrics batch" in message:
        return None

    # 3. Sanitize sensitive headers
    request = event.get("request", {})
    headers = request.get("headers", {})
    if isinstance(headers, dict):
        for sensitive_header in ("authorization", "x-otp", "cookie"):
            if sensitive_header in headers:
                headers[sensitive_header] = "[REDACTED]"

    return event


def _before_send_transaction(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Discards persistent WebSocket transactions so Sentry APM never generates N+1 Query issues for live sockets.

    WebSockets stay open for hours as a bi-directional continuous stream. Sentry's transaction
    profiler treats the entire open connection as a single HTTP request lifecycle and accumulates
    all heartbeat intervals into an artificial 'N+1 Query' issue. Dropping the WebSocket transaction
    prevents these false positive alerts while keeping standard HTTP APM transactions active.
    """
    txn = event.get("transaction", "")
    op = event.get("contexts", {}).get("trace", {}).get("op", "")
    asgi_type = event.get("tags", {}).get("asgi.type", "")

    if (
        "live" in txn
        or txn == "app.api.v1.ws.live"
        or op == "websocket.server"
        or asgi_type == "websocket"
    ):
        return None

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
        before_send_transaction=_before_send_transaction,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            PyMongoIntegration(),
            LoguruIntegration(),
        ],
    )
    logger.info("Sentry initialized for environment: {}", settings.APP_ENV)
    return True
