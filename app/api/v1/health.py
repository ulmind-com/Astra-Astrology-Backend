"""Liveness / readiness endpoints.

These are what uptime monitors (UptimeRobot, cron-job.org, Render's own health
check) hit, so they follow three rules:

* `GET` **and** `HEAD` are both allowed — UptimeRobot sends HEAD by default, and
  FastAPI's router does not add it automatically.
* They always answer `200`. A database problem shows up as
  `data.status == "degraded"`, not as an HTTP error, so a monitor doesn't page
  for something a retry would fix. Point a keyword monitor at `"status":"ok"` if
  you do want alerting on that.
* They never block for long: the database ping is bounded by
  `HEALTH_DB_TIMEOUT_SECONDS`.
"""

from fastapi import APIRouter, Response

from app.core.config import settings
from app.db import mongodb
from app.schemas.common import ApiResponse, HealthStatus
from app.services import firebase

router = APIRouter(tags=["health"])

# Monitors must reach the app itself, not a CDN cache, or the instance could
# still go to sleep behind a cached 200.
NO_STORE = "no-store, no-cache, must-revalidate, max-age=0"


# HEAD is registered separately and kept out of the schema, so it doesn't
# collide with the GET operation's id.
@router.head("/health", include_in_schema=False)
@router.get(
    "/health",
    response_model=ApiResponse[HealthStatus],
    summary="Service health",
)
async def health(response: Response) -> ApiResponse[HealthStatus]:
    db_ok = await mongodb.ping()
    response.headers["Cache-Control"] = NO_STORE

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
                "firebase": firebase.is_enabled(),
                "cloudinary": settings.cloudinary_configured,
                "resend": settings.resend_configured,
            },
        ),
    )


@router.head("/ping", include_in_schema=False)
@router.get("/ping", summary="Lightweight liveness probe (no database call)")
async def ping(response: Response) -> dict[str, str]:
    """The cheapest endpoint to use as a keep-alive target."""
    response.headers["Cache-Control"] = NO_STORE
    return {"ping": "pong"}
