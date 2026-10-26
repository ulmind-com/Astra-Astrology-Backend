"""Domain exceptions + the handlers that turn them into a uniform JSON shape."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings


class AppError(Exception):
    """Base class for every expected (handled) application error."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "bad_request"
    message: str = "Something went wrong."

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        self.details = details
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "bad_request"
    message = "Invalid request."


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "unauthorized"
    message = "Authentication required."


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"
    message = "You do not have permission to perform this action."


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    message = "Resource not found."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"
    message = "Resource already exists."


class TooManyRequestsError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "too_many_requests"
    message = "Too many requests. Please try again later."


class ServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "service_unavailable"
    message = "Service temporarily unavailable."


def _error_body(message: str, error_code: str, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"success": False, "message": message, "error_code": error_code}
    if details is not None:
        body["details"] = details
    return body


def _cors_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    origin = request.headers.get("origin")
    if origin and (origin in settings.ALLOWED_ORIGINS or "*" in settings.ALLOWED_ORIGINS):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
    return headers


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.message, exc.error_code, exc.details),
            headers=_cors_headers(request),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        headers = _cors_headers(request)
        if getattr(exc, "headers", None):
            headers.update(exc.headers)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(str(exc.detail), f"http_{exc.status_code}"),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in err["loc"][1:]) or "body",
                "message": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body("Validation failed.", "validation_error", details),
            headers=_cors_headers(request),
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.opt(exception=exc).error(
            "Unhandled error on {} {}", request.method, request.url.path
        )
        message = str(exc) if settings.DEBUG else "Internal server error."
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(message, "internal_server_error"),
            headers=_cors_headers(request),
        )
