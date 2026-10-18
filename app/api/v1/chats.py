"""One-to-one chats between a user and an astrologer."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Header, Query, status

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.models.astrologer import Astrologer
from app.models.chat import ChatSession
from app.models.enums import ChatStatus, UserRole
from app.models.user import User
from app.schemas.call import CallPeer, ExtendRequest, SessionBilling
from app.schemas.chat import (
    ChatOut,
    ChatSessionOut,
    ChatSweepResult,
    EndChatRequest,
    MarkProgressRequest,
    MessageOut,
    ReadMarkerOut,
    SendMessageRequest,
    StartChatRequest,
    TranscriptOut,
)
from app.schemas.common import ApiResponse, Paginated, build_page
from app.services import billing
from app.services import chat as chat_service
from app.services import settings as settings_service
from app.services import wallet as wallet_service

router = APIRouter(prefix="/chats", tags=["chat"])

LIVE = {ChatStatus.REQUESTED, ChatStatus.ACTIVE}


async def _peer_for(session: ChatSession, viewer: User) -> CallPeer | None:
    if viewer.id == session.user_id:
        profile = await Astrologer.get(session.astrologer_id)
        if profile is None:
            return None
        return CallPeer(name=profile.display_name, avatar_url=profile.profile_image_url)

    asker = await User.get(session.user_id)
    if asker is None:
        return None
    return CallPeer(name=asker.full_name, avatar_url=asker.avatar_url)


async def _billing_of(session: ChatSession) -> SessionBilling:
    wallet = await wallet_service.get_or_create_wallet(session.user_id)
    affordable = billing.affordable_minutes(wallet.balance_coins, session.coins_per_minute)

    # Minutes already paid for that have not been used yet.
    remaining = max(0, session.requested_minutes - session.minutes_charged)
    settings_doc = await settings_service.get_settings()
    room = max(0, settings_doc.max_session_minutes - session.requested_minutes)

    return SessionBilling(
        coins_per_minute=session.coins_per_minute,
        requested_minutes=session.requested_minutes,
        minutes_charged=session.minutes_charged,
        coins_charged=session.coins_charged,
        minutes_remaining=remaining,
        balance_coins=wallet.balance_coins,
        minutes_left=affordable,
        can_extend=affordable >= 1 and room >= 1,
        max_extend_minutes=min(affordable, room),
    )


async def to_chat(session: ChatSession, viewer: User | None = None) -> ChatOut:
    return ChatOut(
        id=str(session.id),
        conversation_id=session.conversation_id,
        status=session.status,
        user_id=str(session.user_id),
        astrologer_id=str(session.astrologer_id),
        astrologer_user_id=str(session.astrologer_user_id),
        peer=await _peer_for(session, viewer) if viewer else None,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        message_count=session.message_count,
        ended_by=session.ended_by,
        end_reason=session.end_reason,
        created_at=session.created_at,
        billing=await _billing_of(session),
    )


async def _session_out(session: ChatSession, user: User) -> ChatSessionOut:
    return ChatSessionOut(chat=await to_chat(session, user))


# -------------------------------------------------------------------- start
@router.post(
    "",
    response_model=ApiResponse[ChatSessionOut],
    status_code=status.HTTP_201_CREATED,
    summary="Ask an astrologer for a chat",
)
async def start_chat(payload: StartChatRequest, user: CurrentUser) -> ApiResponse[ChatSessionOut]:
    session = await chat_service.start_chat(
        user=user,
        astrologer_id=PydanticObjectId(payload.astrologer_id),
        requested_minutes=payload.requested_minutes,
    )
    return ApiResponse(
        message="Waiting for the astrologer…", data=await _session_out(session, user)
    )


# -------------------------------------------------------------------- state
@router.get(
    "/active",
    response_model=ApiResponse[ChatSessionOut | None],
    summary="The chat I am in, if any",
)
async def my_active_chat(user: CurrentUser) -> ApiResponse[ChatSessionOut | None]:
    session = (
        await chat_service.incoming_for_astrologer(user)
        if user.role is UserRole.ASTROLOGER
        else await chat_service.active_for_user(user)
    )
    if session is None:
        return ApiResponse(message="No active chat.", data=None)
    return ApiResponse(message="Active chat.", data=await _session_out(session, user))


@router.get("/history", response_model=ApiResponse[Paginated[ChatOut]], summary="My chats")
async def chat_history(
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[Paginated[ChatOut]]:
    items, total = await chat_service.history(
        user=user, as_astrologer=user.role is UserRole.ASTROLOGER, page=page, limit=limit
    )
    chats = [await to_chat(s, user) for s in items]
    return ApiResponse(message=f"{total} chat(s).", data=build_page(chats, total, page, limit))


@router.get("/{session_id}", response_model=ApiResponse[ChatSessionOut], summary="One chat")
async def get_chat(session_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[ChatSessionOut]:
    session, _ = await chat_service.load_for(session_id, user)
    return ApiResponse(message="Chat fetched.", data=await _session_out(session, user))


# ------------------------------------------------------------------ actions
@router.post(
    "/{session_id}/accept",
    response_model=ApiResponse[ChatSessionOut],
    summary="Accept (astrologer)",
)
async def accept_chat(
    session_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[ChatSessionOut]:
    session = await chat_service.accept_chat(session_id=session_id, user=user)
    return ApiResponse(message="Chat started.", data=await _session_out(session, user))


@router.post(
    "/{session_id}/decline", response_model=ApiResponse[ChatOut], summary="Decline (astrologer)"
)
async def decline_chat(session_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[ChatOut]:
    session = await chat_service.decline_chat(session_id=session_id, user=user)
    return ApiResponse(message="Chat declined.", data=await to_chat(session, user))


@router.post("/{session_id}/end", response_model=ApiResponse[ChatOut], summary="End the chat")
async def end_chat(
    session_id: PydanticObjectId, user: CurrentUser, payload: EndChatRequest | None = None
) -> ApiResponse[ChatOut]:
    session = await chat_service.end_chat(
        session_id=session_id, user=user, reason=payload.reason if payload else None
    )
    return ApiResponse(message="Chat ended.", data=await to_chat(session, user))


@router.post(
    "/{session_id}/extend",
    response_model=ApiResponse[ChatOut],
    summary="Buy more time on a chat that is running",
)
async def extend_chat(
    session_id: PydanticObjectId, payload: ExtendRequest, user: CurrentUser
) -> ApiResponse[ChatOut]:
    session = await chat_service.extend_chat(
        session_id=session_id, user=user, extra_minutes=payload.extra_minutes
    )
    return ApiResponse(
        message=f"{payload.extra_minutes} more minute"
        f"{'s' if payload.extra_minutes != 1 else ''} added.",
        data=await to_chat(session, user),
    )


@router.post(
    "/{session_id}/heartbeat", response_model=ApiResponse[ChatOut], summary="I am still here"
)
async def heartbeat(session_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[ChatOut]:
    session = await chat_service.heartbeat(session_id=session_id, user=user)
    return ApiResponse(message="Noted.", data=await to_chat(session, user))



# ----------------------------------------------------------------- messages
@router.get(
    "/{session_id}/messages",
    response_model=ApiResponse[TranscriptOut],
    summary="The conversation so far",
)
async def get_messages(
    session_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[TranscriptOut]:
    """Loads a chat window from cold.

    Messages are removed some time after a chat ends — how long is the admin's
    to set — so an old conversation may legitimately come back empty. The
    session itself, and what it cost, is kept either way.
    """
    from app.services import messages as message_service

    session = await chat_service.get_session(session_id)
    history = await message_service.history(session=session, viewer=user)
    markers = await message_service.markers(session)

    return ApiResponse(
        message="Messages fetched.",
        data=TranscriptOut(
            messages=[MessageOut(**message_service.to_public(m)) for m in history],
            reads=[ReadMarkerOut(**message_service.marker_to_public(m)) for m in markers],
        ),
    )


@router.post(
    "/{session_id}/messages",
    response_model=ApiResponse[MessageOut],
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
)
async def send_message(
    session_id: PydanticObjectId, payload: SendMessageRequest, user: CurrentUser
) -> ApiResponse[MessageOut]:
    """Refused once the chat has ended — the check is here, not in the browser."""
    from app.services import messages as message_service

    session = await chat_service.get_session(session_id)
    message = await message_service.send(session=session, sender=user, text=payload.text)
    return ApiResponse(
        message="Sent.", data=MessageOut(**message_service.to_public(message))
    )


@router.post(
    "/{session_id}/read",
    response_model=ApiResponse[ReadMarkerOut],
    summary="Mark how far I have got",
)
async def mark_read(
    session_id: PydanticObjectId, payload: MarkProgressRequest, user: CurrentUser
) -> ApiResponse[ReadMarkerOut]:
    """What draws the second tick, and then the blue one."""
    from app.services import messages as message_service

    session = await chat_service.get_session(session_id)
    marker = await message_service.mark_progress(
        session=session, viewer=user, level=payload.level
    )
    return ApiResponse(
        message="Noted.", data=ReadMarkerOut(**message_service.marker_to_public(marker))
    )


# -------------------------------------------------------------- maintenance
maintenance_router = APIRouter(prefix="/internal", tags=["internal"])


@maintenance_router.post(
    "/chats/sweep",
    response_model=ApiResponse[ChatSweepResult],
    summary="Close chats nobody ended (for a scheduled ping)",
    include_in_schema=False,
)
async def sweep_chats(
    x_internal_key: Annotated[str | None, Header()] = None,
) -> ApiResponse[ChatSweepResult]:
    import hmac

    if not x_internal_key or not hmac.compare_digest(x_internal_key, settings.SECRET_KEY):
        raise ForbiddenError("Not allowed.", error_code="forbidden")

    result = await chat_service.sweep()
    return ApiResponse(message="Swept.", data=ChatSweepResult(**result))
