"""Contact support and ticket management endpoints."""

from datetime import UTC, datetime
import secrets
from typing import Annotated
from beanie import PydanticObjectId
from fastapi import APIRouter, Query, status

from app.api.dependencies import AdminUser, CurrentUser, OptionalUser
from app.core.exceptions import NotFoundError
from app.models.support import SupportTicket
from app.schemas.common import ApiResponse, MessageResponse, Paginated, build_page
from app.schemas.support import (
    SupportTicketCreate,
    SupportTicketOut,
    SupportTicketStats,
    SupportTicketUpdateAdmin,
)

router = APIRouter(prefix="/support", tags=["support"])
admin_router = APIRouter(prefix="/admin/support", tags=["admin: support"])


def _to_out(t: SupportTicket) -> SupportTicketOut:
    return SupportTicketOut(
        id=str(t.id),
        ticket_number=t.ticket_number,
        user_id=str(t.user_id) if t.user_id else None,
        name=t.name,
        email=t.email,
        phone=t.phone,
        category=t.category,
        subject=t.subject,
        message=t.message,
        priority=t.priority,
        status=t.status,
        source=t.source,
        device_info=t.device_info,
        admin_notes=t.admin_notes,
        admin_id=str(t.admin_id) if t.admin_id else None,
        resolved_at=t.resolved_at,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.post(
    "/contact",
    response_model=ApiResponse[SupportTicketOut],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a contact support inquiry or ticket",
)
async def submit_contact_support(
    payload: SupportTicketCreate,
    user: OptionalUser = None,
) -> ApiResponse[SupportTicketOut]:
    """Allows any client (guest or logged-in) to submit a contact support inquiry."""
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    random_part = secrets.token_hex(3).upper()
    ticket_num = f"TK-{date_part}-{random_part}"

    ticket = SupportTicket(
        ticket_number=ticket_num,
        user_id=user.id if user else None,
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        phone=payload.phone.strip() if payload.phone else None,
        category=payload.category or "general",
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        priority=payload.priority or "medium",
        status="open",
        source=payload.source or "mobile",
        device_info=payload.device_info,
    )
    await ticket.insert()

    return ApiResponse(
        message=f"Support ticket {ticket.ticket_number} created successfully.",
        data=_to_out(ticket),
    )


@router.get(
    "/mine",
    response_model=ApiResponse[list[SupportTicketOut]],
    summary="List my submitted support tickets",
)
async def get_my_tickets(
    user: CurrentUser,
) -> ApiResponse[list[SupportTicketOut]]:
    """Retrieves tickets created by the currently authenticated user."""
    tickets = (
        await SupportTicket.find(SupportTicket.user_id == user.id)
        .sort(-SupportTicket.created_at)
        .to_list()
    )
    return ApiResponse(
        message=f"Retrieved {len(tickets)} support tickets.",
        data=[_to_out(t) for t in tickets],
    )


# =========================================================================
# Admin Endpoints
# =========================================================================


@admin_router.get(
    "/stats",
    response_model=ApiResponse[SupportTicketStats],
    summary="Get support ticket statistics for admin dashboard",
)
async def get_ticket_stats(
    admin: AdminUser,
) -> ApiResponse[SupportTicketStats]:
    total = await SupportTicket.count()
    open_count = await SupportTicket.find(SupportTicket.status == "open").count()
    in_progress = await SupportTicket.find(SupportTicket.status == "in_progress").count()
    resolved = await SupportTicket.find(SupportTicket.status == "resolved").count()
    closed = await SupportTicket.find(SupportTicket.status == "closed").count()

    return ApiResponse(
        message="Support ticket stats calculated.",
        data=SupportTicketStats(
            total=total,
            open=open_count,
            in_progress=in_progress,
            resolved=resolved,
            closed=closed,
        ),
    )


@admin_router.get(
    "",
    response_model=ApiResponse[Paginated[SupportTicketOut]],
    summary="List and filter support tickets (admin)",
)
async def list_admin_tickets(
    admin: AdminUser,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    category: str | None = None,
    search: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[Paginated[SupportTicketOut]]:
    query: dict = {}

    if status_filter and status_filter != "all":
        query["status"] = status_filter

    if category and category != "all":
        query["category"] = category

    if search:
        s = search.strip()
        query["$or"] = [
            {"ticket_number": {"$regex": s, "$options": "i"}},
            {"name": {"$regex": s, "$options": "i"}},
            {"email": {"$regex": s, "$options": "i"}},
            {"subject": {"$regex": s, "$options": "i"}},
        ]

    total = await SupportTicket.find(query).count()
    skip = (page - 1) * limit
    tickets = (
        await SupportTicket.find(query)
        .sort(-SupportTicket.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    out_items = [_to_out(t) for t in tickets]
    return ApiResponse(
        message=f"{total} ticket(s) found.",
        data=build_page(out_items, total, page, limit),
    )


@admin_router.get(
    "/{ticket_id}",
    response_model=ApiResponse[SupportTicketOut],
    summary="Get single support ticket detail (admin)",
)
async def get_admin_ticket_detail(
    ticket_id: PydanticObjectId,
    admin: AdminUser,
) -> ApiResponse[SupportTicketOut]:
    ticket = await SupportTicket.get(ticket_id)
    if not ticket:
        raise NotFoundError("Support ticket not found.", error_code="ticket_not_found")
    return ApiResponse(message="Ticket fetched.", data=_to_out(ticket))


@admin_router.patch(
    "/{ticket_id}",
    response_model=ApiResponse[SupportTicketOut],
    summary="Update support ticket status, priority or admin notes (admin)",
)
async def update_admin_ticket(
    ticket_id: PydanticObjectId,
    payload: SupportTicketUpdateAdmin,
    admin: AdminUser,
) -> ApiResponse[SupportTicketOut]:
    ticket = await SupportTicket.get(ticket_id)
    if not ticket:
        raise NotFoundError("Support ticket not found.", error_code="ticket_not_found")

    if payload.status is not None:
        ticket.status = payload.status
        if payload.status in ("resolved", "closed") and not ticket.resolved_at:
            ticket.resolved_at = datetime.now(UTC)
            ticket.admin_id = admin.id
        elif payload.status in ("open", "in_progress"):
            ticket.resolved_at = None

    if payload.priority is not None:
        ticket.priority = payload.priority

    if payload.admin_notes is not None:
        ticket.admin_notes = payload.admin_notes
        ticket.admin_id = admin.id

    await ticket.save()
    return ApiResponse(message="Ticket updated.", data=_to_out(ticket))


@admin_router.delete(
    "/{ticket_id}",
    response_model=MessageResponse,
    summary="Delete support ticket (admin)",
)
async def delete_admin_ticket(
    ticket_id: PydanticObjectId,
    admin: AdminUser,
) -> MessageResponse:
    ticket = await SupportTicket.get(ticket_id)
    if not ticket:
        raise NotFoundError("Support ticket not found.", error_code="ticket_not_found")
    await ticket.delete()
    return MessageResponse(message=f"Ticket {ticket.ticket_number} deleted successfully.")

