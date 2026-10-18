"""Admin management of astrologer accounts.

Astrologers cannot sign themselves up — an admin opens the account here, and the
astrologer is emailed a generated password.
"""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query, status

from app.api.dependencies import AdminUser
from app.core.exceptions import NotFoundError
from app.models.astrologer import Astrologer
from app.models.user import User
from app.schemas.astrologer import (
    AstrologerAdminUpdate,
    AstrologerCreate,
    AstrologerCreated,
    AstrologerProfile,
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services import astrologer as astrologer_service

router = APIRouter(prefix="/admin/astrologers", tags=["admin: astrologers"])


async def _load(astrologer_id: PydanticObjectId) -> tuple[User, Astrologer]:
    profile = await Astrologer.get(astrologer_id)
    if profile is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")
    user = await User.get(profile.user_id)
    if user is None:
        raise NotFoundError(
            "The account behind this astrologer is missing.",
            error_code="astrologer_account_missing",
        )
    return user, profile


@router.post(
    "",
    response_model=ApiResponse[AstrologerCreated],
    status_code=status.HTTP_201_CREATED,
    summary="Create an astrologer account and email them their password",
)
async def create_astrologer(
    payload: AstrologerCreate, admin: AdminUser
) -> ApiResponse[AstrologerCreated]:
    user, profile, password, email_sent = await astrologer_service.create_astrologer(payload)

    return ApiResponse(
        message=(
            f"Astrologer created. Sign-in details emailed to {user.email}."
            if email_sent
            else (
                "Astrologer created, but the welcome email could not be sent. "
                "Pass the password on yourself — it is not shown again."
            )
        ),
        data=AstrologerCreated(
            astrologer=astrologer_service.to_profile(user, profile),
            welcome_email_sent=email_sent,
            # Only surfaced when the email failed, so there is still a way through.
            initial_password=None if email_sent else password,
        ),
    )


@router.get(
    "",
    response_model=ApiResponse[list[AstrologerProfile]],
    summary="List astrologers",
)
async def list_astrologers(
    admin: AdminUser,
    search: Annotated[str | None, Query(description="Name match")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[list[AstrologerProfile]]:
    query = Astrologer.find_all()
    if search:
        from beanie.operators import RegEx

        query = Astrologer.find(RegEx(Astrologer.display_name, search, options="i"))

    total = await query.count()
    profiles = await query.sort(-Astrologer.created_at).skip(skip).limit(limit).to_list()

    items = []
    for profile in profiles:
        user = await User.get(profile.user_id)
        if user is not None:
            items.append(astrologer_service.to_profile(user, profile))

    return ApiResponse(message=f"{total} astrologer(s).", data=items)


@router.get(
    "/{astrologer_id}",
    response_model=ApiResponse[AstrologerProfile],
    summary="Get one astrologer",
)
async def get_astrologer(
    astrologer_id: PydanticObjectId, admin: AdminUser
) -> ApiResponse[AstrologerProfile]:
    user, profile = await _load(astrologer_id)
    return ApiResponse(
        message="Astrologer fetched.", data=astrologer_service.to_profile(user, profile)
    )


@router.patch(
    "/{astrologer_id}",
    response_model=ApiResponse[AstrologerProfile],
    summary="Update an astrologer — including rates, commission and status",
)
async def update_astrologer(
    astrologer_id: PydanticObjectId, payload: AstrologerAdminUpdate, admin: AdminUser
) -> ApiResponse[AstrologerProfile]:
    user, profile = await _load(astrologer_id)
    user, profile = await astrologer_service.update_profile(user, profile, payload, by_admin=True)
    return ApiResponse(
        message="Astrologer updated.", data=astrologer_service.to_profile(user, profile)
    )


@router.delete(
    "/{astrologer_id}",
    response_model=MessageResponse,
    summary="Deactivate an astrologer account",
)
async def deactivate_astrologer(
    astrologer_id: PydanticObjectId, admin: AdminUser
) -> MessageResponse:
    user, profile = await _load(astrologer_id)

    # The account is suspended and the listing hidden, rather than deleted — the
    # consultation history behind it has to stay.
    from app.models.enums import AccountStatus

    user.status = AccountStatus.SUSPENDED
    await user.save()
    profile.is_listed = False
    profile.availability.is_online = False
    # Clearing the stamp as well, so a panel still open in another tab cannot
    # keep them looking present until its heartbeat lapses.
    profile.availability.last_seen_at = None
    await profile.save()

    # Taken off the live directory at once, not at the next poll.
    from app.services import realtime

    await realtime.publish_astrologer(profile)

    return MessageResponse(message="Astrologer deactivated and removed from the directory.")
