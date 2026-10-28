"""Request-id tagging, access logging and CORS."""

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attaches an `X-Request-ID` and logs each request with its duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        if settings.sentry_configured:
            import sentry_sdk

            sentry_sdk.set_tag("request_id", request_id)

        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = f"{duration_ms:.1f}"

        log = logger.bind(request_id=request_id)
        message = "{} {} -> {} in {:.1f}ms"
        args = (request.method, request.url.path, response.status_code, duration_ms)
        if response.status_code >= 500:
            log.error(message, *args)
        elif response.status_code >= 400:
            log.warning(message, *args)
        else:
            log.info(message, *args)

        return response


def register_middleware(app: FastAPI) -> None:
    # Added last = outermost, so CORS headers apply to every response.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-ms"],
    )
