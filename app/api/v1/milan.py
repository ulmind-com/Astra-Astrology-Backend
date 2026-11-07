"""The multi-party Vedic chamber — groom, bride, guardians and the astrologer.

Guests arrive with an invitation code and no account, so the guest routes
take no bearer token and treat the code as the credential. Everything a
guest can reach is scoped to their own seat.
"""

from typing import Annotated, Any

from beanie import PydanticObjectId
from fastapi import APIRouter, Header, Query, status

from app.api.dependencies import AstrologerUser, CurrentUser, OptionalUser
from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.models.astrologer import Astrologer
from app.models.milan import MilanRoom, MilanSeat
from app.models.user import User
from app.schemas.call import CallCredentials
from app.schemas.common import ApiResponse, MessageResponse
from app.schemas.milan import (
    AddSeatRequest,
    CreateMilanRoomRequest,
    JoinAsGuestRequest,
    MilanBilling,
    MilanOccupantOut,
    MilanRoomOut,
    MilanRoomSession,
    MilanSeatOut,
    MilanSweepResult,
)
from app.services import milan as milan_service

router = APIRouter(prefix="/milan", tags=["milan"])


def _credentials(room: MilanRoom, *, user_id: str, user_name: str, token: str) -> CallCredentials:
    return CallCredentials(
        app_id=settings.ZEGO_APP_ID,
        token=token,
        room_id=room.room_id,
        user_id=user_id,
        user_name=user_name,
        server_url=settings.ZEGO_SERVER_URL or None,
        server_url_backup=settings.ZEGO_SERVER_URL_BACKUP or None,
    )


async def to_room(
    room: MilanRoom,
    *,
    viewer: User | None = None,
    guest_seat: MilanSeat | None = None,
) -> MilanRoomOut:
    """The room as this reader is allowed to see it.

    Join codes and billing are the host's; the astrologer sees the billing
    because it is their earning; a guest sees neither. Everyone sees who is
    in the room, which is the point of the room.
    """
    is_host = viewer is not None and viewer.id == room.host_user_id
    is_astrologer = viewer is not None and viewer.id == room.astrologer_user_id
    is_guest = guest_seat is not None

    profile = await Astrologer.get(room.astrologer_id)
    host = await User.get(room.host_user_id)

    occupants = [
        MilanOccupantOut(
            seat_id=seat.seat_id,
            label=seat.label,
            display_name=seat.display_name,
            is_present=milan_service._is_present(seat),
            joined_at=seat.joined_at,
        )
        for seat in room.seats
        if not seat.is_revoked
    ]

    seats: list[MilanSeatOut] = []
    if is_host:
        seats = [
            MilanSeatOut(
                seat_id=seat.seat_id,
                label=seat.label,
                display_name=seat.display_name,
                is_present=milan_service._is_present(seat),
                joined_at=seat.joined_at,
                join_code=seat.join_code,
                is_revoked=seat.is_revoked,
            )
            for seat in room.seats
        ]

    billing = None
    if is_host or is_astrologer:
        billing = MilanBilling(
            coins_per_minute=room.coins_per_minute,
            minutes_booked=room.requested_minutes,
            minutes_charged=room.minutes_charged,
            coins_charged=room.coins_charged,
        )

    return MilanRoomOut(
        id=str(room.id),
        purpose=room.purpose,
        mode=room.mode,
        status=room.status,
        astrologer_id=str(room.astrologer_id),
        astrologer_name=profile.display_name if profile else None,
        astrologer_avatar_url=profile.profile_image_url if profile else None,
        host_name=host.full_name if host else None,
        viewer_is_host=is_host,
        viewer_is_astrologer=is_astrologer,
        viewer_is_guest=is_guest,
        started_at=room.started_at,
        ended_at=room.ended_at,
        duration_seconds=room.duration_seconds,
        end_reason=room.end_reason,
        ended_by=room.ended_by,
        max_guests=room.max_guests,
        seats_taken=sum(1 for s in room.seats if not s.is_revoked),
        occupants=occupants,
        seats=seats,
        billing=billing,
    )


# ------------------------------------------------------------- the host's
@router.post(
    "",
    response_model=ApiResponse[MilanRoomSession],
    status_code=status.HTTP_201_CREATED,
    summary="Open a multi-party chamber and ring the astrologer",
)
async def create_room(
    payload: CreateMilanRoomRequest, user: CurrentUser
) -> ApiResponse[MilanRoomSession]:
    room, token = await milan_service.create_room(
        host=user,
        astrologer_id=PydanticObjectId(payload.astrologer_id),
        mode=payload.mode,
        purpose=payload.purpose,
        requested_minutes=payload.requested_minutes,
        guest_labels=payload.guests,
    )
    return ApiResponse(
        message="Chamber opened.",
        data=MilanRoomSession(
            room=await to_room(room, viewer=user),
            credentials=_credentials(
                room, user_id=str(user.id), user_name=user.full_name, token=token
            ),
        ),
    )


@router.get(
    "/active",
    response_model=ApiResponse[MilanRoomSession | None],
    summary="The chamber I am hosting or taking, if any",
)
async def my_active_room(user: CurrentUser) -> ApiResponse[MilanRoomSession | None]:
    room = await milan_service.live_room_for(user.id)
    if room is None:
        return ApiResponse(message="No chamber.", data=None)
    token = await milan_service_token(room, user)
    return ApiResponse(
        message="Chamber fetched.",
        data=MilanRoomSession(
            room=await to_room(room, viewer=user),
            credentials=_credentials(
                room, user_id=str(user.id), user_name=user.full_name, token=token
            ),
        ),
    )


async def milan_service_token(room: MilanRoom, user: User) -> str:
    """A fresh room token for the host or the astrologer, e.g. after a reload."""
    from app.services import zego

    milan_service.party_of(room, user)
    return zego.generate_token(user_id=str(user.id), room_id=room.room_id)


@router.get(
    "/{room_id}",
    response_model=ApiResponse[MilanRoomSession],
    summary="One chamber",
)
async def get_room(
    room_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[MilanRoomSession]:
    room, _ = await milan_service.load_for(room_id, user)
    credentials = None
    if room.status in milan_service.LIVE_STATUSES:
        credentials = _credentials(
            room,
            user_id=str(user.id),
            user_name=user.full_name,
            token=await milan_service_token(room, user),
        )
    return ApiResponse(
        message="Chamber fetched.",
        data=MilanRoomSession(room=await to_room(room, viewer=user), credentials=credentials),
    )


@router.post(
    "/{room_id}/seats",
    response_model=ApiResponse[MilanRoomOut],
    status_code=status.HTTP_201_CREATED,
    summary="Open one more place in the chamber",
)
async def add_seat(
    room_id: PydanticObjectId, payload: AddSeatRequest, user: CurrentUser
) -> ApiResponse[MilanRoomOut]:
    room = await milan_service.add_seat(room_id=room_id, user=user, label=payload.label)
    return ApiResponse(message="Seat added.", data=await to_room(room, viewer=user))


@router.delete(
    "/{room_id}/seats/{seat_id}",
    response_model=ApiResponse[MilanRoomOut],
    summary="Cancel an invitation",
)
async def revoke_seat(
    room_id: PydanticObjectId, seat_id: str, user: CurrentUser
) -> ApiResponse[MilanRoomOut]:
    room = await milan_service.revoke_seat(room_id=room_id, user=user, seat_id=seat_id)
    return ApiResponse(message="Invitation cancelled.", data=await to_room(room, viewer=user))


@router.post(
    "/{room_id}/extend",
    response_model=ApiResponse[MilanRoomOut],
    summary="Buy more time",
)
async def extend_room(
    room_id: PydanticObjectId,
    user: CurrentUser,
    extra_minutes: Annotated[int, Query(ge=1, le=600)],
) -> ApiResponse[MilanRoomOut]:
    room = await milan_service.extend(
        room_id=room_id, user=user, extra_minutes=extra_minutes
    )
    return ApiResponse(message="Time added.", data=await to_room(room, viewer=user))


# ------------------------------------------------------ the astrologer's
@router.get(
    "/incoming/mine",
    response_model=ApiResponse[MilanRoomOut | None],
    summary="A chamber waiting for me",
)
async def incoming(user: AstrologerUser) -> ApiResponse[MilanRoomOut | None]:
    room = await MilanRoom.find_one(
        {
            "astrologer_user_id": user.id,
            "status": {"$in": [s.value for s in milan_service.LIVE_STATUSES]},
        }
    )
    if room is None:
        return ApiResponse(message="Nothing waiting.", data=None)
    return ApiResponse(message="Chamber waiting.", data=await to_room(room, viewer=user))


@router.post(
    "/{room_id}/accept",
    response_model=ApiResponse[MilanRoomSession],
    summary="Join the chamber (astrologer)",
)
async def accept(
    room_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[MilanRoomSession]:
    room, token = await milan_service.accept(room_id=room_id, user=user)
    return ApiResponse(
        message="Joined.",
        data=MilanRoomSession(
            room=await to_room(room, viewer=user),
            credentials=_credentials(
                room, user_id=str(user.id), user_name=user.full_name, token=token
            ),
        ),
    )


@router.post(
    "/{room_id}/decline",
    response_model=ApiResponse[MilanRoomOut],
    summary="Decline the chamber (astrologer)",
)
async def decline(
    room_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[MilanRoomOut]:
    room = await milan_service.decline(room_id=room_id, user=user)
    return ApiResponse(message="Declined.", data=await to_room(room, viewer=user))


# -------------------------------------------------------- both accounts
@router.post(
    "/{room_id}/heartbeat",
    response_model=ApiResponse[MilanRoomOut],
    summary="I am still in this chamber",
)
async def heartbeat(
    room_id: PydanticObjectId, user: CurrentUser
) -> ApiResponse[MilanRoomOut]:
    room = await milan_service.heartbeat(room_id=room_id, user=user)
    return ApiResponse(message="Noted.", data=await to_room(room, viewer=user))


@router.post(
    "/{room_id}/end",
    response_model=ApiResponse[MilanRoomOut],
    summary="Close the chamber for everyone",
)
async def end_room(
    room_id: PydanticObjectId,
    user: CurrentUser,
    reason: Annotated[str | None, Query(max_length=200)] = None,
) -> ApiResponse[MilanRoomOut]:
    room = await milan_service.end_room(room_id=room_id, user=user, reason=reason)
    return ApiResponse(message="Chamber closed.", data=await to_room(room, viewer=user))


# --------------------------------------------------------------- guests
# No bearer token: a guest has no account. The invitation code is the whole
# credential, so each of these resolves the seat from the code and never
# trusts a room id the caller supplies.
guest_router = APIRouter(prefix="/milan/guest", tags=["milan"])


@guest_router.post(
    "/join",
    response_model=ApiResponse[MilanRoomSession],
    summary="Take a seat with an invitation",
)
async def join_as_guest(
    payload: JoinAsGuestRequest, viewer: OptionalUser
) -> ApiResponse[MilanRoomSession]:
    room, seat, token = await milan_service.join_as_guest(
        join_code=payload.join_code,
        display_name=payload.display_name,
        viewer=viewer,
    )
    return ApiResponse(
        message="Joined the chamber.",
        data=MilanRoomSession(
            room=await to_room(room, guest_seat=seat),
            credentials=_credentials(
                room,
                user_id=f"guest_{seat.seat_id}",
                user_name=seat.display_name or seat.label,
                token=token,
            ),
        ),
    )


@guest_router.post(
    "/heartbeat",
    response_model=ApiResponse[MilanRoomOut],
    summary="A guest is still here",
)
async def guest_heartbeat(payload: JoinAsGuestRequest) -> ApiResponse[MilanRoomOut]:
    room, seat = await milan_service.guest_heartbeat(join_code=payload.join_code)
    return ApiResponse(message="Noted.", data=await to_room(room, guest_seat=seat))


@guest_router.post(
    "/leave",
    response_model=ApiResponse[MessageResponse],
    summary="A guest steps out",
)
async def guest_leave(payload: JoinAsGuestRequest) -> ApiResponse[MessageResponse]:
    await milan_service.leave_seat(join_code=payload.join_code)
    return ApiResponse(
        message="Left the chamber.", data=MessageResponse(message="Left the chamber.")
    )


# ------------------------------------------------------------ maintenance
maintenance_router = APIRouter(prefix="/internal", tags=["internal"])


@maintenance_router.post(
    "/milan/sweep",
    response_model=ApiResponse[MilanSweepResult],
    summary="Close chambers nobody ended (for a scheduled ping)",
    include_in_schema=False,
)
async def sweep_rooms(
    x_internal_key: Annotated[str | None, Header()] = None,
) -> ApiResponse[MilanSweepResult]:
    # Shares the app's own secret rather than introducing another one.
    import hmac

    if not x_internal_key or not hmac.compare_digest(x_internal_key, settings.SECRET_KEY):
        raise ForbiddenError("Not allowed.", error_code="forbidden")

    result: dict[str, Any] = await milan_service.sweep()
    return ApiResponse(message="Swept.", data=MilanSweepResult(**result))
