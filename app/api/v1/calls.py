"""One-to-one calls between a user and an astrologer."""

from typing import Annotated, Any

from beanie import PydanticObjectId
from fastapi import APIRouter, Header, Query, Request, status
from loguru import logger

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.models.astrologer import Astrologer
from app.models.call import CallSession
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.call import (
    CallCredentials,
    CallOut,
    CallPeer,
    CallSessionOut,
    EndCallRequest,
    StartCallRequest,
    SweepResult,
)
from app.schemas.common import ApiResponse, Paginated, build_page
from app.services import call as call_service
from app.services import zego

router = APIRouter(prefix="/calls", tags=["calls"])


async def _peer_for(session: CallSession, viewer: User) -> CallPeer | None:
    """The other person, as the viewer should see them."""
    if viewer.id == session.user_id:
        profile = await Astrologer.get(session.astrologer_id)
        if profile is None:
            return None
        return CallPeer(name=profile.display_name, avatar_url=profile.profile_image_url)

    caller = await User.get(session.user_id)
    if caller is None:
        return None
    return CallPeer(name=caller.full_name, avatar_url=caller.avatar_url)


async def to_call(session: CallSession, viewer: User | None = None) -> CallOut:
    return CallOut(
        id=str(session.id),
        room_id=session.room_id,
        mode=session.mode,
        status=session.status,
        user_id=str(session.user_id),
        astrologer_id=str(session.astrologer_id),
        astrologer_user_id=str(session.astrologer_user_id),
        peer=await _peer_for(session, viewer) if viewer else None,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        ended_by=session.ended_by,
        end_reason=session.end_reason,
        created_at=session.created_at,
    )


def _credentials(session: CallSession, user: User, token: str) -> CallCredentials:
    return CallCredentials(
        app_id=settings.ZEGO_APP_ID,
        token=token,
        room_id=session.room_id,
        user_id=str(user.id),
        user_name=user.full_name,
        server_url=settings.ZEGO_SERVER_URL or None,
        server_url_backup=settings.ZEGO_SERVER_URL_BACKUP or None,
    )


# -------------------------------------------------------------------- start
@router.post(
    "",
    response_model=ApiResponse[CallSessionOut],
    status_code=status.HTTP_201_CREATED,
    summary="Ring an astrologer",
)
async def start_call(payload: StartCallRequest, user: CurrentUser) -> ApiResponse[CallSessionOut]:
    session, token = await call_service.start_call(
        user=user, astrologer_id=PydanticObjectId(payload.astrologer_id), mode=payload.mode
    )
    return ApiResponse(
        message="Calling…",
        data=CallSessionOut(
            call=await to_call(session, user), credentials=_credentials(session, user, token)
        ),
    )


# ------------------------------------------------------------------- state
@router.get(
    "/active",
    response_model=ApiResponse[CallSessionOut | None],
    summary="The call I am on, if any — for both sides",
)
async def my_active_call(user: CurrentUser) -> ApiResponse[CallSessionOut | None]:
    session = (
        await call_service.incoming_for_astrologer(user)
        if user.role is UserRole.ASTROLOGER
        else await call_service.active_for_user(user)
    )
    if session is None:
        return ApiResponse(message="No active call.", data=None)

    # A ringing astrologer has not joined the room yet, so no token for them.
    credentials = None
    if session.status.value == "active" or user.id == session.user_id:
        credentials = _credentials(
            session, user, await call_service.token_for(session, user)
        )
    return ApiResponse(
        message="Active call.",
        data=CallSessionOut(call=await to_call(session, user), credentials=credentials),
    )


@router.get("/history", response_model=ApiResponse[Paginated[CallOut]], summary="My calls")
async def call_history(
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[Paginated[CallOut]]:
    items, total = await call_service.history(
        user=user, as_astrologer=user.role is UserRole.ASTROLOGER, page=page, limit=limit
    )
    calls = [await to_call(s, user) for s in items]
    return ApiResponse(message=f"{total} call(s).", data=build_page(calls, total, page, limit))


@router.get("/{session_id}", response_model=ApiResponse[CallSessionOut], summary="One call")
async def get_call(session_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[CallSessionOut]:
    session, _ = await call_service.load_for(session_id, user)
    credentials = None
    if session.status.value in {"ringing", "active"}:
        credentials = _credentials(session, user, await call_service.token_for(session, user))
    return ApiResponse(
        message="Call fetched.",
        data=CallSessionOut(call=await to_call(session, user), credentials=credentials),
    )


# ------------------------------------------------------------------ actions
@router.post(
    "/{session_id}/accept",
    response_model=ApiResponse[CallSessionOut],
    summary="Answer (astrologer)",
)
async def accept_call(
    session_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[CallSessionOut]:
    session, token = await call_service.accept_call(session_id=session_id, user=user)
    return ApiResponse(
        message="Call connected.",
        data=CallSessionOut(
            call=await to_call(session, user), credentials=_credentials(session, user, token)
        ),
    )


@router.post(
    "/{session_id}/decline",
    response_model=ApiResponse[CallOut],
    summary="Decline (astrologer)",
)
async def decline_call(session_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[CallOut]:
    session = await call_service.decline_call(session_id=session_id, user=user)
    return ApiResponse(message="Call declined.", data=await to_call(session, user))


@router.post("/{session_id}/end", response_model=ApiResponse[CallOut], summary="Hang up")
async def end_call(
    session_id: PydanticObjectId, user: CurrentUser, payload: EndCallRequest | None = None
) -> ApiResponse[CallOut]:
    session = await call_service.end_call(
        session_id=session_id, user=user, reason=payload.reason if payload else None
    )
    return ApiResponse(message="Call ended.", data=await to_call(session, user))


@router.post(
    "/{session_id}/heartbeat",
    response_model=ApiResponse[CallOut],
    summary="I am still on this call",
)
async def heartbeat(session_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[CallOut]:
    session = await call_service.heartbeat(session_id=session_id, user=user)
    return ApiResponse(message="Noted.", data=await to_call(session, user))


# ------------------------------------------------------- maintenance + hooks
maintenance_router = APIRouter(prefix="/internal", tags=["internal"])


@maintenance_router.post(
    "/calls/sweep",
    response_model=ApiResponse[SweepResult],
    summary="Close calls nobody ended (for a scheduled ping)",
    include_in_schema=False,
)
async def sweep_calls(
    x_internal_key: Annotated[str | None, Header()] = None,
) -> ApiResponse[SweepResult]:
    # Shares the app's own secret rather than introducing another one.
    import hmac

    if not x_internal_key or not hmac.compare_digest(x_internal_key, settings.SECRET_KEY):
        raise ForbiddenError("Not allowed.", error_code="forbidden")

    result = await call_service.sweep()
    return ApiResponse(message="Swept.", data=SweepResult(**result))


webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@webhook_router.post(
    "/zego",
    summary="ZEGOCLOUD room callbacks (signature-authenticated)",
    include_in_schema=False,
)
async def zego_callback(
    request: Request,
    signature: Annotated[str | None, Header(alias="Signature")] = None,
    nonce: Annotated[str | None, Header(alias="Nonce")] = None,
    timestamp: Annotated[str | None, Header(alias="Timestamp")] = None,
) -> dict[str, Any]:
    zego.verify_callback_signature(signature=signature, nonce=nonce, timestamp=timestamp)

    body = await request.json()
    result = await call_service_handle_callback(body, nonce)
    logger.info("ZEGOCLOUD callback '{}' -> {}", body.get("event"), result)
    # ZEGOCLOUD retries anything that is not 2xx.
    return {"success": True, "result": result}


async def call_service_handle_callback(body: dict[str, Any], nonce: str | None) -> str:
    """Records the event, then lets it inform the session.

    This is a safety net rather than the mechanism: ZEGOCLOUD's own docs say a
    callback can be dropped after its retries, so the heartbeat sweep remains
    the thing that guarantees a call is closed.
    """
    from app.models.call import ZegoCallbackEvent

    event = str(body.get("event", ""))
    key = f"{event}:{nonce or body.get('timestamp') or ''}"

    record = ZegoCallbackEvent(event_key=key, event=event, payload=body)
    try:
        await record.insert()
    except Exception as exc:  # DuplicateKeyError - a retry
        if type(exc).__name__ != "DuplicateKeyError":
            raise
        return "duplicate"

    room_id = body.get("room_id") or body.get("roomId")
    if not room_id:
        record.result = "ignored"
        await record.save()
        return "ignored"

    session = await CallSession.find_one(CallSession.room_id == room_id)
    if session is None:
        record.result = "unknown_room"
        await record.save()
        return "unknown_room"

    result = "noted"
    if event in {"room_logout", "room_exit", "user_left", "participant_left"}:
        # Somebody really left the room. If the call is still marked live, the
        # sweeper will close it; this just stops the clock sooner.
        if session.status.value in {"ringing", "active"}:
            from app.models.enums import CallParty, CallStatus

            await call_service._close(
                session,
                status=CallStatus.ENDED if session.started_at else CallStatus.MISSED,
                by=CallParty.SYSTEM,
                reason="A participant left the room",
            )
            result = "closed"

    record.result = result
    await record.save()
    return result
