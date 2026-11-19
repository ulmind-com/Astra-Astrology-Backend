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
from app.models.astrologer_application import AstrologerApplication
from app.models.user import User
from app.schemas.astrologer import (
    AstrologerAdminUpdate,
    AstrologerCreate,
    AstrologerCreated,
    AstrologerProfile,
)
from app.schemas.astrologer_application import (
    AstrologerApplicationApprovalResultOut,
    AstrologerApplicationOut,
    AstrologerApplicationRejectIn,
)
from app.schemas.common import ApiResponse, MessageResponse
from app.services import astrologer as astrologer_service
from app.services import astrologer_application_service

router = APIRouter(prefix="/admin/astrologers", tags=["admin: astrologers"])


def _app_to_out(app: AstrologerApplication) -> AstrologerApplicationOut:
    return AstrologerApplicationOut(
        id=str(app.id),
        application_number=app.application_number,
        full_name=app.full_name,
        email=app.email,
        phone=app.phone,
        gender=app.gender,
        age=app.age,
        address=app.address,
        city=app.city,
        state=app.state,
        pincode=app.pincode,
        skills=app.skills,
        specialisations=app.specialisations,
        experience_years=app.experience_years,
        languages=app.languages,
        qualifications=app.qualifications,
        bio=app.bio,
        avatar_url=app.avatar_url,
        identity_proof_url=app.identity_proof_url,
        bank_account_number=app.bank_account_number,
        bank_ifsc=app.bank_ifsc,
        bank_account_holder=app.bank_account_holder,
        bank_name=app.bank_name,
        upi_id=app.upi_id,
        pan_card=app.pan_card,
        status=app.status,
        rejection_reason=app.rejection_reason,
        reviewed_at=app.reviewed_at,
        approved_user_id=str(app.approved_user_id) if app.approved_user_id else None,
        approved_astrologer_id=str(app.approved_astrologer_id) if app.approved_astrologer_id else None,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


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


# ======================================================== Astrologer Applications (Admin)
@router.get(
    "/applications",
    response_model=ApiResponse[list[AstrologerApplicationOut]],
    summary="List Astrologer onboarding applications with filtering",
)
async def list_astrologer_applications(
    admin: AdminUser,
    status: Annotated[str | None, Query(description="pending, approved, rejected, or all")] = None,
    search: Annotated[str | None, Query(description="Search by name, email, phone, city, application_number")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[list[AstrologerApplicationOut]]:
    items, total = await astrologer_application_service.list_applications(
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=[_app_to_out(it) for it in items],
        meta={"total": total, "limit": limit, "offset": offset},
    )


@router.get(
    "/applications/{app_id}",
    response_model=ApiResponse[AstrologerApplicationOut],
    summary="Get detail of an Astrologer application",
)
async def get_astrologer_application_detail(
    app_id: str,
    admin: AdminUser,
) -> ApiResponse[AstrologerApplicationOut]:
    app = await astrologer_application_service.get_application(app_id)
    return ApiResponse(data=_app_to_out(app))


@router.post(
    "/applications/{app_id}/approve",
    response_model=ApiResponse[AstrologerApplicationApprovalResultOut],
    summary="Approve Astrologer application, create account & profile, email credentials",
)
async def approve_astrologer_application(
    app_id: str,
    admin: AdminUser,
) -> ApiResponse[AstrologerApplicationApprovalResultOut]:
    user, profile, temp_pass, email_sent, dashboard_url = (
        await astrologer_application_service.approve_application(
            app_id=app_id,
            admin_user=admin,
        )
    )
    out = AstrologerApplicationApprovalResultOut(
        application_id=app_id,
        user_id=str(user.id),
        astrologer_id=str(profile.id),
        display_name=profile.display_name,
        email=user.email,
        temporary_password=temp_pass,
        email_sent=email_sent,
        dashboard_url=dashboard_url,
        message=(
            f"Astrologer {profile.display_name} approved successfully! Welcome email sent to {user.email}."
            if email_sent
            else f"Astrologer {profile.display_name} approved successfully! Temporary credentials generated."
        ),
    )
    return ApiResponse(data=out, message=out.message)


@router.post(
    "/applications/{app_id}/reject",
    response_model=ApiResponse[AstrologerApplicationOut],
    summary="Reject Astrologer application with reason",
)
async def reject_astrologer_application(
    app_id: str,
    payload: AstrologerApplicationRejectIn,
    admin: AdminUser,
) -> ApiResponse[AstrologerApplicationOut]:
    app = await astrologer_application_service.reject_application(
        app_id=app_id,
        reason=payload.reason,
        admin_user=admin,
    )
    return ApiResponse(
        data=_app_to_out(app), message="Astrologer application has been marked as rejected."
    )


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
    from app.models.enums import AccountStatus
    from app.services import appointments as appointment_service

    user, profile = await _load(astrologer_id)
    user, profile = await astrologer_service.update_profile(user, profile, payload, by_admin=True)

    if user.status != AccountStatus.ACTIVE:
        await appointment_service.cancel_active_for_astrologer(
            profile.id,
            by=admin,
            reason="Astrologer account suspended by administration",
        )

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
    from app.services import appointments as appointment_service

    user.status = AccountStatus.SUSPENDED
    await user.save()
    profile.is_listed = False
    profile.availability.is_online = False
    # Clearing the stamp as well, so a panel still open in another tab cannot
    # keep them looking present until its heartbeat lapses.
    profile.availability.last_seen_at = None
    await profile.save()

    # Cancel active bookings and auto-refund seekers
    await appointment_service.cancel_active_for_astrologer(
        profile.id,
        by=admin,
        reason="Astrologer account deactivated by administration",
    )

    # Taken off the live directory at once, not at the next poll.
    from app.services import realtime

    await realtime.publish_astrologer(profile)

    return MessageResponse(message="Astrologer deactivated and removed from the directory.")
