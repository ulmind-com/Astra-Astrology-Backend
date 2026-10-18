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
from app.schemas.call import CallPeer
from app.schemas.chat import (
    ChatOut,
    ChatSessionOut,
    ChatSweepResult,
    EndChatRequest,
    FirebaseCredentials,
    StartChatRequest,
)
from app.schemas.common import ApiResponse, Paginated, build_page
from app.services import chat as chat_service
from app.services import firestore

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
    )


async def _firebase_for(user: User) -> FirebaseCredentials | None:
    """A fresh custom token, minted per request rather than stored."""
    if not user.firebase_uid:
        return None
    return FirebaseCredentials(
        custom_token=await firestore.mint_token(user.firebase_uid),
        uid=user.firebase_uid,
        project_id=settings.FIREBASE_PROJECT_ID,
    )


async def _session_out(session: ChatSession, user: User) -> ChatSessionOut:
    firebase = await _firebase_for(user) if session.status in LIVE else None
    return ChatSessionOut(chat=await to_chat(session, user), firebase=firebase)


# -------------------------------------------------------------------- start
@router.post(
    "",
    response_model=ApiResponse[ChatSessionOut],
    status_code=status.HTTP_201_CREATED,
    summary="Ask an astrologer for a chat",
)
async def start_chat(payload: StartChatRequest, user: CurrentUser) -> ApiResponse[ChatSessionOut]:
    session = await chat_service.start_chat(
        user=user, astrologer_id=PydanticObjectId(payload.astrologer_id)
    )
    return ApiResponse(message="Waiting for the astrologer…", data=await _session_out(session, user))


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
    "/{session_id}/heartbeat", response_model=ApiResponse[ChatOut], summary="I am still here"
)
async def heartbeat(session_id: PydanticObjectId, user: CurrentUser) -> ApiResponse[ChatOut]:
    session = await chat_service.heartbeat(session_id=session_id, user=user)
    return ApiResponse(message="Noted.", data=await to_chat(session, user))


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
