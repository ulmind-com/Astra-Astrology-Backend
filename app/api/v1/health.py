"""Liveness / readiness endpoints."""

from fastapi import APIRouter

from app.core.config import settings
from app.db import mongodb
from app.schemas.common import ApiResponse, HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[HealthStatus], summary="Service health")
async def health() -> ApiResponse[HealthStatus]:
    db_ok = await mongodb.ping()
    return ApiResponse(
        message="Service is healthy" if db_ok else "Database unreachable",
        data=HealthStatus(
            status="ok" if db_ok else "degraded",
            app=settings.APP_NAME,
            environment=settings.APP_ENV,
            version="0.1.0",
            database="connected" if db_ok else "disconnected",
            services={
                "mongodb": db_ok,
                "cloudinary": settings.cloudinary_configured,
                "resend": settings.resend_configured,
            },
        ),
    )


@router.get("/ping", summary="Lightweight liveness probe")
async def ping() -> dict[str, str]:
    return {"ping": "pong"}
