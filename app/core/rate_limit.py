"""In-memory sliding window rate limiter for public and authentication endpoints."""

import time
from collections import defaultdict
from typing import NamedTuple

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.config import settings


class WindowRule(NamedTuple):
    max_requests: int
    window_seconds: int


# Strict limits for sensitive authentication endpoints
ROUTE_RULES: dict[str, WindowRule] = {
    "/api/v1/auth/login": WindowRule(max_requests=15, window_seconds=60),
    "/api/v1/auth/register": WindowRule(max_requests=10, window_seconds=60),
    "/api/v1/auth/forgot-password": WindowRule(max_requests=5, window_seconds=60),
    "/api/v1/auth/reset-password": WindowRule(max_requests=5, window_seconds=60),
    "/api/v1/auth/otp": WindowRule(max_requests=5, window_seconds=60),
}

DEFAULT_AUTH_RULE = WindowRule(max_requests=30, window_seconds=60)
DEFAULT_SCAN_RULE = WindowRule(max_requests=60, window_seconds=60)


class InMemoryRateLimiter:
    """Sliding-window request counter per (client_ip, route_prefix)."""

    def __init__(self) -> None:
        self._history: dict[tuple[str, str], list[float]] = defaultdict(list)
        self._last_cleanup: float = time.time()

    def _cleanup_old_entries(self, now: float) -> None:
        if now - self._last_cleanup < 300:  # Clean every 5 minutes
            return
        self._last_cleanup = now
        stale_keys = []
        for key, timestamps in self._history.items():
            valid = [t for t in timestamps if now - t < 120]
            if valid:
                self._history[key] = valid
            else:
                stale_keys.append(key)
        for k in stale_keys:
            self._history.pop(k, None)

    def check_rate_limit(self, client_ip: str, path: str) -> tuple[bool, int, int]:
        """Check whether a request from client_ip to path is permitted.

        Returns:
            (is_allowed: bool, retry_after_seconds: int, remaining_requests: int)
        """
        now = time.time()
        self._cleanup_old_entries(now)

        # Match route rule
        rule: WindowRule | None = None
        matched_prefix = path
        for route_prefix, r in ROUTE_RULES.items():
            if path.startswith(route_prefix):
                rule = r
                matched_prefix = route_prefix
                break

        if rule is None:
            if "/api/v1/auth/" in path:
                rule = DEFAULT_AUTH_RULE
                matched_prefix = "/api/v1/auth/"
            elif any(s in path for s in ["/scan", "/dual-match", "/couple-match"]):
                rule = DEFAULT_SCAN_RULE
                matched_prefix = "scan_endpoints"
            else:
                return True, 0, 999

        bucket_key = (client_ip, matched_prefix)
        timestamps = self._history[bucket_key]
        cutoff = now - rule.window_seconds
        valid_timestamps = [t for t in timestamps if t > cutoff]
        self._history[bucket_key] = valid_timestamps

        if len(valid_timestamps) >= rule.max_requests:
            oldest = valid_timestamps[0]
            retry_after = max(1, int(rule.window_seconds - (now - oldest)))
            return False, retry_after, 0

        valid_timestamps.append(now)
        remaining = rule.max_requests - len(valid_timestamps)
        return True, 0, remaining

    def reset_for_ip(self, client_ip: str) -> None:
        """Helper to clear history for tests."""
        keys = [k for k in self._history if k[0] == client_ip]
        for k in keys:
            self._history.pop(k, None)


rate_limiter = InMemoryRateLimiter()


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Starlette middleware intercepting requests to enforce rate limits."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check if globally enabled
        if not getattr(settings, "RATE_LIMIT_ENABLED", True):
            return await call_next(request)

        # Allow test client or internal microservices to bypass via header
        if request.headers.get("x-bypass-rate-limit") == "true":
            return await call_next(request)

        client_ip = getattr(request.state, "client_ip", None)
        if not client_ip:
            client_ip = (
                request.headers.get("cf-connecting-ip")
                or request.headers.get("x-real-ip")
                or (request.headers.get("x-forwarded-for", "").split(",")[0].strip())
                or (request.client.host if request.client else "127.0.0.1")
            )

        allowed, retry_after, remaining = rate_limiter.check_rate_limit(client_ip, request.url.path)
        if not allowed:
            logger.warning(
                "Rate limit exceeded for IP {} on route {}. Retry after {}s",
                client_ip,
                request.url.path,
                retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error_code": "rate_limit_exceeded",
                    "message": f"Too many requests. Please wait {retry_after} seconds before trying again.",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
