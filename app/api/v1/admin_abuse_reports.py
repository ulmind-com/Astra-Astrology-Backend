"""Admin-only trust & safety dashboard for AbuseReport incidents.

Central screen for platform administrators to view every red-flag report
filed by astrologers against clients, investigate each incident, change the
review status, and unblock clients from an astrologer's personal blacklist.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from beanie import PydanticObjectId
from beanie.operators import And, In
from fastapi import APIRouter, Query, status
from loguru import logger

from app.api.dependencies import AdminUser
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.abuse_report import AbuseReport
from app.models.astrologer import Astrologer
from app.models.user import User
from app.schemas.abuse_report import (
    AbuseReportListItem,
    AbuseReportOut,
    AbuseReportReviewRequest,
    AbuseReportStats,
    AbuseReportUnblockRequest,
    AbuseReportUnblockResponse,
    PaginatedAbuseReports,
)
from app.schemas.common import ApiResponse, build_page

router = APIRouter(prefix="/admin/abuse-reports", tags=["admin: abuse reports"])


def _mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, domain = email.rsplit("@", 1)
    return f"{local[:3]}***@{domain}"


async def _load_user_name(user_id: PydanticObjectId) -> tuple[str | None, str | None]:
    user = await User.get(user_id)
    if user is None:
        return None, None
    return user.full_name, user.email


async def _load_astrologer_name(astrologer_id: PydanticObjectId) -> tuple[str | None, str | None]:
    profile = await Astrologer.get(astrologer_id)
    if profile is None:
        return None, None
    user = await User.get(profile.user_id) if profile.user_id else None
    return profile.display_name, user.email if user else None


@router.get(
    "",
    response_model=ApiResponse[PaginatedAbuseReports],
    summary="List all abuse reports with filtering and pagination",
)
async def list_abuse_reports(
    admin: AdminUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    status: Annotated[str | None, Query(description="pending | reviewed | resolved | dismissed")] = None,
    astrologer_id: Annotated[str | None, Query(description="Filter by astrologer id")] = None,
    client_user_id: Annotated[str | None, Query(description="Filter by client user id")] = None,
    search: Annotated[str | None, Query(description="Search astrologer or client name")] = None,
    from_date: Annotated[str | None, Query(description="ISO date, inclusive")] = None,
    to_date: Annotated[str | None, Query(description="ISO date, inclusive")] = None,
) -> ApiResponse[PaginatedAbuseReports]:
    filters: list[Any] = []

    if status:
        filters.append(AbuseReport.status == status)
    if astrologer_id and PydanticObjectId.is_valid(astrologer_id):
        filters.append(AbuseReport.astrologer_id == PydanticObjectId(astrologer_id))
    if client_user_id and PydanticObjectId.is_valid(client_user_id):
        filters.append(AbuseReport.client_user_id == PydanticObjectId(client_user_id))

    if from_date:
        try:
            filters.append(AbuseReport.created_at >= datetime.fromisoformat(from_date))
        except ValueError:
            pass
    if to_date:
        try:
            filters.append(AbuseReport.created_at <= datetime.fromisoformat(to_date))
        except ValueError:
            pass

    query = AbuseReport.find(And(*filters)) if filters else AbuseReport.find_all()

    total = await query.count()
    reports = (
        await query.sort(-AbuseReport.created_at)
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list()
    )

    astrologer_ids = {r.astrologer_id for r in reports}
    client_ids = {r.client_user_id for r in reports}

    astrologers: dict[PydanticObjectId, Astrologer] = {}
    if astrologer_ids:
        found_astros = await Astrologer.find(In(Astrologer.id, list(astrologer_ids))).to_list()
        astrologers = {a.id: a for a in found_astros if a.id is not None}

    astro_user_ids = {a.user_id for a in astrologers.values() if a.user_id}
    users: dict[PydanticObjectId, User] = {}
    if astro_user_ids:
        found_users = await User.find(In(User.id, list(astro_user_ids))).to_list()
        users = {u.id: u for u in found_users if u.id is not None}

    client_users: dict[PydanticObjectId, User] = {}
    if client_ids:
        found_clients = await User.find(In(User.id, list(client_ids))).to_list()
        client_users = {u.id: u for u in found_clients if u.id is not None}

    items: list[AbuseReportListItem] = []
    for r in reports:
        astro = astrologers.get(r.astrologer_id)
        astro_name = astro.display_name if astro else None
        astro_user_email = users.get(astro.user_id).email if astro and astro.user_id in users else None

        client = client_users.get(r.client_user_id)
        client_name = client.full_name if client else None
        client_email_masked = _mask_email(client.email) if client else None

        if search:
            q = search.lower()
            haystack = " ".join(
                part for part in (astro_name or "", client_name or "", astro_user_email or "") if part
            ).lower()
            if q not in haystack:
                continue

        items.append(
            AbuseReportListItem(
                id=str(r.id),
                astrologer_id=str(r.astrologer_id),
                astrologer_name=astro_name,
                client_user_id=str(r.client_user_id),
                client_name=client_name,
                client_email_masked=client_email_masked,
                reason=r.reason,
                action_taken=r.action_taken,
                status=r.status,
                created_at=r.created_at,
            )
        )

    page_obj = build_page(items, total, page, limit)
    return ApiResponse(
        message=f"{total} abuse report(s).",
        data=PaginatedAbuseReports(items=items, meta=page_obj.meta.model_dump()),
    )


@router.get(
    "/{report_id}",
    response_model=ApiResponse[AbuseReportOut],
    summary="Get one abuse report with full context",
)
async def get_abuse_report(
    report_id: str,
    admin: AdminUser,
) -> ApiResponse[AbuseReportOut]:
    if not PydanticObjectId.is_valid(report_id):
        raise NotFoundError("Abuse report not found.", error_code="abuse_report_not_found")

    report = await AbuseReport.get(PydanticObjectId(report_id))
    if report is None:
        raise NotFoundError("Abuse report not found.", error_code="abuse_report_not_found")

    astro_name, astro_email = await _load_astrologer_name(report.astrologer_id)
    client_name, client_email = await _load_user_name(report.client_user_id)

    return ApiResponse(
        message="Abuse report fetched.",
        data=AbuseReportOut(
            id=str(report.id),
            astrologer_id=str(report.astrologer_id),
            astrologer_name=astro_name,
            astrologer_email=astro_email,
            client_user_id=str(report.client_user_id),
            client_name=client_name,
            client_email_masked=_mask_email(client_email),
            appointment_id=str(report.appointment_id) if report.appointment_id else None,
            call_id=str(report.call_id) if report.call_id else None,
            reason=report.reason,
            notes=report.notes,
            action_taken=report.action_taken,
            status=report.status,
            reviewed_by=str(report.reviewed_by) if report.reviewed_by else None,
            reviewed_at=report.reviewed_at,
            admin_notes=report.admin_notes,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ),
    )


@router.patch(
    "/{report_id}/review",
    response_model=ApiResponse[AbuseReportOut],
    summary="Review, resolve or dismiss an abuse report",
)
async def review_abuse_report(
    report_id: str,
    payload: AbuseReportReviewRequest,
    admin: AdminUser,
) -> ApiResponse[AbuseReportOut]:
    if not PydanticObjectId.is_valid(report_id):
        raise NotFoundError("Abuse report not found.", error_code="abuse_report_not_found")

    report = await AbuseReport.get(PydanticObjectId(report_id))
    if report is None:
        raise NotFoundError("Abuse report not found.", error_code="abuse_report_not_found")

    allowed_statuses = {"pending", "reviewed", "resolved", "dismissed"}
    new_status = payload.status.strip().lower()
    if new_status not in allowed_statuses:
        raise BadRequestError(
            f"Status must be one of {sorted(allowed_statuses)}.",
            error_code="invalid_status",
        )

    report.status = new_status
    report.reviewed_by = admin.id
    report.reviewed_at = datetime.now(UTC)
    report.admin_notes = payload.admin_notes
    await report.save()

    logger.info(
        "Abuse report {} reviewed by admin {}: status={}",
        report.id,
        admin.id,
        new_status,
    )

    astro_name, astro_email = await _load_astrologer_name(report.astrologer_id)
    client_name, client_email = await _load_user_name(report.client_user_id)

    return ApiResponse(
        message=f"Abuse report marked as {new_status}.",
        data=AbuseReportOut(
            id=str(report.id),
            astrologer_id=str(report.astrologer_id),
            astrologer_name=astro_name,
            astrologer_email=astro_email,
            client_user_id=str(report.client_user_id),
            client_name=client_name,
            client_email_masked=_mask_email(client_email),
            appointment_id=str(report.appointment_id) if report.appointment_id else None,
            call_id=str(report.call_id) if report.call_id else None,
            reason=report.reason,
            notes=report.notes,
            action_taken=report.action_taken,
            status=report.status,
            reviewed_by=str(report.reviewed_by) if report.reviewed_by else None,
            reviewed_at=report.reviewed_at,
            admin_notes=report.admin_notes,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ),
    )




@router.post(
    "/{report_id}/unblock-client",
    response_model=ApiResponse[AbuseReportUnblockResponse],
    summary="Remove a client from the reporting astrologer's personal blacklist",
)
async def unblock_client_from_report(
    report_id: str,
    payload: AbuseReportUnblockRequest,
    admin: AdminUser,
) -> ApiResponse[AbuseReportUnblockResponse]:
    if not PydanticObjectId.is_valid(report_id):
        raise NotFoundError("Abuse report not found.", error_code="abuse_report_not_found")

    report = await AbuseReport.get(PydanticObjectId(report_id))
    if report is None:
        raise NotFoundError("Abuse report not found.", error_code="abuse_report_not_found")

    target_client_id = payload.client_user_id
    if PydanticObjectId.is_valid(target_client_id):
        target_client_id = PydanticObjectId(target_client_id)
    else:
        raise BadRequestError("Invalid client user id.", error_code="invalid_client_id")

    if target_client_id != report.client_user_id:
        raise ForbiddenError(
            "You can only unblock the client named in this report.",
            error_code="client_not_in_report",
        )

    astro = await Astrologer.get(report.astrologer_id)
    if astro is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    existing = getattr(astro, "blacklisted_user_ids", None) or []
    if report.client_user_id in existing:
        astro.blacklisted_user_ids = [uid for uid in existing if uid != report.client_user_id]
        await astro.save()
        logger.info(
            "Admin {} unblocked client {} from astrologer {}'s blacklist",
            admin.id,
            report.client_user_id,
            astro.id,
        )
        return ApiResponse(
            message="Client removed from the astrologer's blacklist.",
            data=AbuseReportUnblockResponse(
                unblocked=True,
                client_user_id=str(report.client_user_id),
            ),
        )

    return ApiResponse(
        message="Client was not on this astrologer's blacklist.",
        data=AbuseReportUnblockResponse(
            unblocked=False,
            client_user_id=str(report.client_user_id),
        ),
    )


@router.get(
    "/stats",
    response_model=ApiResponse[AbuseReportStats],
    summary="Aggregate safety dashboard metrics",
)
async def abuse_report_stats(admin: AdminUser) -> ApiResponse[AbuseReportStats]:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    total = await AbuseReport.find_all().count()
    pending = await AbuseReport.find(AbuseReport.status == "pending").count()
    reviewed = await AbuseReport.find(AbuseReport.status == "reviewed").count()
    resolved = await AbuseReport.find(AbuseReport.status == "resolved").count()
    dismissed = await AbuseReport.find(AbuseReport.status == "dismissed").count()

    reports_today = await AbuseReport.find(AbuseReport.created_at >= today_start).count()
    reports_this_week = await AbuseReport.find(AbuseReport.created_at >= week_start).count()
    reports_this_month = await AbuseReport.find(AbuseReport.created_at >= month_start).count()

    pipeline_top_clients = [
        {"$group": {"_id": "$client_user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top_clients_raw = await AbuseReport.aggregate(pipeline_top_clients).to_list()
    top_flagged_clients = []
    for entry in top_clients_raw:
        cid = entry["_id"]
        user = await User.get(cid) if PydanticObjectId.is_valid(str(cid)) else None
        top_flagged_clients.append(
            {
                "client_user_id": str(cid),
                "client_name": user.full_name if user else "Unknown",
                "client_email_masked": _mask_email(user.email) if user else None,
                "report_count": entry["count"],
            }
        )

    pipeline_top_astros = [
        {"$group": {"_id": "$astrologer_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top_astros_raw = await AbuseReport.aggregate(pipeline_top_astros).to_list()
    top_flagging_astrologers = []
    for entry in top_astros_raw:
        aid = entry["_id"]
        profile = await Astrologer.get(aid) if PydanticObjectId.is_valid(str(aid)) else None
        astro_name = profile.display_name if profile else "Unknown"
        top_flagging_astrologers.append(
            {
                "astrologer_id": str(aid),
                "astrologer_name": astro_name,
                "report_count": entry["count"],
            }
        )

    by_status: dict[str, int] = {
        "pending": pending,
        "reviewed": reviewed,
        "resolved": resolved,
        "dismissed": dismissed,
    }
    by_action: dict[str, int] = {
        "blacklisted": await AbuseReport.find(AbuseReport.action_taken == "blacklisted").count(),
        "flagged_only": await AbuseReport.find(AbuseReport.action_taken == "flagged_only").count(),
    }

    return ApiResponse(
        message="Safety dashboard stats computed.",
        data=AbuseReportStats(
            total_reports=total,
            pending_reports=pending,
            reviewed_reports=reviewed,
            resolved_reports=resolved,
            dismissed_reports=dismissed,
            reports_today=reports_today,
            reports_this_week=reports_this_week,
            reports_this_month=reports_this_month,
            top_flagged_clients=top_flagged_clients,
            top_flagging_astrologers=top_flagging_astrologers,
            reports_by_status=by_status,
            reports_by_action=by_action,
        ),
    )
