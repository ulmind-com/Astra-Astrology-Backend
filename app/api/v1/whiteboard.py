"""API router for in-chamber Interactive Cosmic Whiteboard."""

from beanie import PydanticObjectId
from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.models.whiteboard import CallWhiteboard
from app.schemas.common import ApiResponse
from app.schemas.whiteboard import LoadChartRequest, WhiteboardOut, WhiteboardSyncRequest
from app.services import whiteboard as service

router = APIRouter(prefix="/calls/{call_id}/whiteboard", tags=["whiteboard"])


def _to_out(wb: CallWhiteboard) -> WhiteboardOut:
    return WhiteboardOut(
        id=str(wb.id),
        call_id=str(wb.call_id),
        appointment_id=str(wb.appointment_id) if wb.appointment_id else None,
        is_open=wb.is_open,
        chart_style=wb.chart_style,
        active_tab=wb.active_tab,
        client_name=wb.client_name,
        birth_date=wb.birth_date,
        birth_time=wb.birth_time,
        birth_place=wb.birth_place,
        asc_sign_num=wb.asc_sign_num,
        planets=wb.planets,
        transit_planets=wb.transit_planets,
        drishti=wb.drishti,
        highlighted_houses=wb.highlighted_houses,
        strokes=wb.strokes,
        version=wb.version,
    )


@router.get(
    "",
    response_model=ApiResponse[WhiteboardOut],
    summary="Get or initialize live Cosmic Whiteboard for a call chamber",
)
async def get_whiteboard(
    call_id: PydanticObjectId,
    user: CurrentUser,
) -> ApiResponse[WhiteboardOut]:
    wb = await service.get_or_create_whiteboard(call_id, user)
    return ApiResponse(message="Whiteboard loaded.", data=_to_out(wb))


@router.post(
    "/sync",
    response_model=ApiResponse[WhiteboardOut],
    summary="Synchronize annotations, active tab, Drishti or drawings on Cosmic Whiteboard",
)
async def sync_whiteboard(
    call_id: PydanticObjectId,
    payload: WhiteboardSyncRequest,
    user: CurrentUser,
) -> ApiResponse[WhiteboardOut]:
    wb = await service.sync_whiteboard(call_id, user, payload)
    return ApiResponse(message="Whiteboard synced.", data=_to_out(wb))


@router.post(
    "/clear",
    response_model=ApiResponse[WhiteboardOut],
    summary="Clear drawings and highlighted markings from Cosmic Whiteboard",
)
async def clear_whiteboard(
    call_id: PydanticObjectId,
    user: CurrentUser,
) -> ApiResponse[WhiteboardOut]:
    wb = await service.clear_whiteboard(call_id, user)
    return ApiResponse(message="Whiteboard cleared.", data=_to_out(wb))


@router.post(
    "/load-chart",
    response_model=ApiResponse[WhiteboardOut],
    summary="Load or recalculate Vedic chart for specific birth details on Cosmic Whiteboard",
)
async def load_custom_chart(
    call_id: PydanticObjectId,
    payload: LoadChartRequest,
    user: CurrentUser,
) -> ApiResponse[WhiteboardOut]:
    wb = await service.load_custom_chart(call_id, user, payload)
    return ApiResponse(message="Chart reloaded.", data=_to_out(wb))


@router.post(
    "/toggle",
    response_model=ApiResponse[WhiteboardOut],
    summary="Toggle Cosmic Whiteboard open or closed in chamber",
)
async def toggle_whiteboard(
    call_id: PydanticObjectId,
    user: CurrentUser,
) -> ApiResponse[WhiteboardOut]:
    current = await service.get_or_create_whiteboard(call_id, user)
    wb = await service.sync_whiteboard(call_id, user, WhiteboardSyncRequest(is_open=not current.is_open))
    return ApiResponse(message="Whiteboard toggled.", data=_to_out(wb))

