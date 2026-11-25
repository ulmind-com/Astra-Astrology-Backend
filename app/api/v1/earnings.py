"""Earnings & Payouts — Financial Operations Ledger.

Supports both Vedic Astrologers and Vedic Purohits (Pandit Ji).
An astrologer/purohit sees their credited net earnings, with live withdrawable
balances, bank details, and Cloudinary-managed UPI QR code lifecycle.
An admin manages payouts separated into Astrologer and Purohit desks,
scans uploaded UPI QR codes, settles payouts with UTR references, and analyzes financial flows.
"""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from app.api.dependencies import AdminUser, CurrentUser, ProfessionalUser
from app.core.exceptions import BadRequestError, NotFoundError
from app.core.security import safe_regex_pattern
from app.models.astrologer import Astrologer
from app.models.enums import ConsultationMode, PujaBookingStatus, PujaPaymentStatus, UserRole
from app.models.payout import PayoutMethod, PayoutStatus
from app.models.purohit import PujaBooking, Purohit
from app.models.user import User
from app.schemas.common import ApiResponse, Paginated, build_page
from app.schemas.wallet import (
    AdminEarningRow,
    AdminEarningsSummary,
    AstrologerEarningsBalanceOut,
    BankDetailsUpdateIn,
    BeneficiaryBreakdownResponse,
    EarningRow,
    EarningsBucket,
    EarningsSummary,
    PayoutAnalyticsOut,
    PayoutOut,
    PayoutRequestIn,
    RejectPayoutIn,
    SettlePayoutIn,
)
from app.services import earnings as earnings_service
from app.services import payout as payout_service
from app.services.storage import ALLOWED_IMAGE_TYPES, safe_delete_cloudinary_image, upload_file

router = APIRouter(prefix="/astrologers/me/earnings", tags=["astrologer: earnings"])
unified_router = APIRouter(prefix="/earnings", tags=["earnings"])


# ====================================================================
# User-Facing Handlers (Astrologers & Purohits)
# ====================================================================

async def _get_profile_for_user(user: User) -> tuple[Astrologer | Purohit, str]:
    """Resolves whether current user is an Astrologer or Purohit."""
    astrologer = await Astrologer.find_one({"user_id": user.id})
    if astrologer:
        return astrologer, "astrologer"
    purohit = await Purohit.find_one({"user_id": user.id})
    if purohit:
        return purohit, "purohit"
    raise NotFoundError("Professional profile (Astrologer or Purohit) not found.")


@router.get("", response_model=ApiResponse[EarningsSummary], summary="What I have earned")
@unified_router.get("/summary", response_model=ApiResponse[EarningsSummary], summary="What I have earned summary")
async def my_earnings(user: ProfessionalUser) -> ApiResponse[EarningsSummary]:
    profile, b_type = await _get_profile_for_user(user)

    if b_type == "purohit":
        # For Purohit: aggregate completed pujas
        bookings = await PujaBooking.find({
            "purohit_user_id": user.id,
            "payment_status": PujaPaymentStatus.PAID,
            "status": {"$ne": PujaBookingStatus.CANCELLED},
        }).to_list()
        total_paise = sum(int(round(b.amount_inr * 100)) for b in bookings)
        total_mins = sum(b.puja_duration_minutes for b in bookings)
        count = len(bookings)
        bucket = EarningsBucket(earning_paise=total_paise, minutes=total_mins, sessions=count)
        return ApiResponse(
            message="Earnings fetched.",
            data=EarningsSummary(today=bucket, this_week=bucket, this_month=bucket, all_time=bucket),
        )

    totals = await earnings_service.for_astrologer(user.id)

    def bucket_fn(name: str) -> EarningsBucket:
        row = totals[name]
        return EarningsBucket(
            earning_paise=row["earning_paise"],
            minutes=row["minutes"],
            sessions=row["sessions"],
        )

    return ApiResponse(
        message="Earnings fetched.",
        data=EarningsSummary(
            today=bucket_fn("today"),
            this_week=bucket_fn("this_week"),
            this_month=bucket_fn("this_month"),
            all_time=bucket_fn("all_time"),
        ),
    )


@router.get(
    "/balance",
    response_model=ApiResponse[AstrologerEarningsBalanceOut],
    summary="My live financial balances & withdrawable amount",
)
@unified_router.get(
    "/balance",
    response_model=ApiResponse[AstrologerEarningsBalanceOut],
    summary="My live financial balances & withdrawable amount",
)
async def my_earnings_balance(user: ProfessionalUser) -> ApiResponse[AstrologerEarningsBalanceOut]:
    data = await payout_service.get_astrologer_earnings_balance(user.id)
    return ApiResponse(
        message="Earnings balance calculated successfully.",
        data=AstrologerEarningsBalanceOut(**data),
    )


@router.get(
    "/recent", response_model=ApiResponse[list[EarningRow]], summary="My recent earnings"
)
@unified_router.get(
    "/recent", response_model=ApiResponse[list[EarningRow]], summary="My recent earnings"
)
async def my_recent_earnings(
    user: ProfessionalUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    skip: Annotated[int, Query(ge=0)] = 0,
    mode: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[EarningRow]]:
    profile, b_type = await _get_profile_for_user(user)

    if b_type == "purohit":
        bookings = (
            await PujaBooking.find({"purohit_user_id": user.id})
            .sort([("created_at", -1)])
            .skip(skip)
            .limit(limit)
            .to_list()
        )
        data = [
            EarningRow(
                id=str(b.id),
                mode=ConsultationMode.APPOINTMENT,
                minutes=b.puja_duration_minutes,
                earning_paise=int(round(b.amount_inr * 100)),
                created_at=b.created_at,
                user_id=str(b.user_id),
                user_name=f"{b.user_name} ({b.puja_name})",
                user_avatar=None,
                user_image_url=None,
                coins_charged=int(round(b.amount_inr * 100)),
                gross_paise=int(round(b.amount_inr * 100)),
            )
            for b in bookings
        ]
        return ApiResponse(message=f"{len(data)} puja earnings record(s).", data=data)

    rows = await earnings_service.recent_for_astrologer(
        user.id, limit=limit, skip=skip, mode=mode, search=search
    )
    user_ids = [r["user_id"] for r in rows if r.get("user_id")]
    user_map = {}
    if user_ids:
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        user_map = {u.id: u for u in users}

    data: list[EarningRow] = []
    for r in rows:
        uid = r.get("user_id")
        u = user_map.get(uid) if uid else None
        uname = u.full_name if u else None
        uavatar = u.avatar_url if u else None

        data.append(
            EarningRow(
                id=str(r["_id"]),
                mode=r["mode"],
                minutes=r["minutes"],
                earning_paise=r["earning_paise"],
                created_at=r["created_at"],
                user_id=str(uid) if uid else None,
                user_name=uname,
                user_avatar=uavatar,
                user_image_url=uavatar,
                coins_charged=r.get("coins_charged"),
                gross_paise=r.get("gross_paise"),
            )
        )

    return ApiResponse(
        message=f"{len(rows)} consultation{'' if len(rows) == 1 else 's'}.",
        data=data,
    )


@router.get(
    "/paginated",
    response_model=ApiResponse[Paginated[EarningRow]],
    summary="Paginated consultation/puja history with search and mode filters",
)
@unified_router.get(
    "/paginated",
    response_model=ApiResponse[Paginated[EarningRow]],
    summary="Paginated consultation/puja history with search and mode filters",
)
async def my_paginated_earnings(
    user: ProfessionalUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    mode: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    window: Annotated[str | None, Query()] = None,
) -> ApiResponse[Paginated[EarningRow]]:
    profile, b_type = await _get_profile_for_user(user)

    if b_type == "purohit":
        query_filter: dict = {"purohit_user_id": user.id}
        if search and search.strip():
            pat = safe_regex_pattern(search)
            query_filter["$or"] = [
                {"puja_name": pat},
                {"user_name": pat},
            ]
        total = await PujaBooking.find(query_filter).count()
        bookings = (
            await PujaBooking.find(query_filter)
            .sort([("created_at", -1)])
            .skip((page - 1) * limit)
            .limit(limit)
            .to_list()
        )
        data = [
            EarningRow(
                id=str(b.id),
                mode=ConsultationMode.APPOINTMENT,
                minutes=b.puja_duration_minutes,
                earning_paise=int(round(b.amount_inr * 100)),
                created_at=b.created_at,
                user_id=str(b.user_id),
                user_name=f"{b.user_name} ({b.puja_name})",
                user_avatar=None,
                user_image_url=None,
                coins_charged=int(round(b.amount_inr * 100)),
                gross_paise=int(round(b.amount_inr * 100)),
            )
            for b in bookings
        ]
        return ApiResponse(
            message=f"Page {page} of {build_page(data, total, page, limit).meta.total_pages} puja offerings.",
            data=build_page(data, total, page, limit),
        )

    since = None
    if window:
        windows = earnings_service._windows()
        since = windows.get(window)

    rows, total = await earnings_service.paginated_for_astrologer(
        astrologer_user_id=user.id,
        page=page,
        limit=limit,
        mode=mode,
        search=search,
        since=since,
    )
    user_ids = [r["user_id"] for r in rows if r.get("user_id")]
    user_map = {}
    if user_ids:
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        user_map = {u.id: u for u in users}

    data: list[EarningRow] = []
    for r in rows:
        uid = r.get("user_id")
        u = user_map.get(uid) if uid else None
        uname = u.full_name if u else None
        uavatar = u.avatar_url if u else None

        data.append(
            EarningRow(
                id=str(r["_id"]),
                mode=r["mode"],
                minutes=r["minutes"],
                earning_paise=r["earning_paise"],
                created_at=r["created_at"],
                user_id=str(uid) if uid else None,
                user_name=uname,
                user_avatar=uavatar,
                user_image_url=uavatar,
                coins_charged=r.get("coins_charged"),
                gross_paise=r.get("gross_paise"),
            )
        )

    return ApiResponse(
        message=f"Page {page} of {build_page(data, total, page, limit).meta.total_pages} consultations.",
        data=build_page(data, total, page, limit),
    )


@router.post(
    "/payout-request",
    response_model=ApiResponse[PayoutOut],
    summary="Request a withdrawal/payout to bank or UPI",
)
@unified_router.post(
    "/payout-request",
    response_model=ApiResponse[PayoutOut],
    summary="Request a withdrawal/payout to bank or UPI",
)
async def request_payout(
    body: PayoutRequestIn,
    user: ProfessionalUser,
) -> ApiResponse[PayoutOut]:
    method = PayoutMethod(body.payout_method)
    payout = await payout_service.request_payout(
        astrologer_user_id=user.id,
        amount_paise=body.amount_paise,
        payout_method=method,
        custom_details=body.model_dump(),
    )
    return ApiResponse(
        message=f"Withdrawal request of ₹{payout.amount_paise / 100:.2f} submitted successfully.",
        data=PayoutOut(
            id=str(payout.id),
            astrologer_id=str(payout.astrologer_id) if payout.astrologer_id else None,
            purohit_id=str(payout.purohit_id) if payout.purohit_id else None,
            beneficiary_type=payout.beneficiary_type,
            beneficiary_name=payout.beneficiary_name,
            astrologer_name=payout.beneficiary_name,
            amount_paise=payout.amount_paise,
            tds_percent=payout.tds_percent,
            tds_paise=payout.tds_paise,
            net_payable_paise=payout.net_payable_paise,
            payout_method=payout.payout_method,
            bank_name=payout.bank_name,
            account_holder_name=payout.account_holder_name,
            account_number_last4=payout.account_number_last4,
            account_number_masked=payout.account_number_masked,
            ifsc=payout.ifsc,
            upi_id=payout.upi_id,
            upi_qr_url=payout.upi_qr_url,
            status=payout.status,
            utr_number=payout.utr_number,
            admin_notes=payout.admin_notes,
            rejection_reason=payout.rejection_reason,
            requested_at=payout.requested_at,
            approved_at=payout.approved_at,
            settled_at=payout.settled_at,
            rejected_at=payout.rejected_at,
        ),
    )


@router.get(
    "/payouts",
    response_model=ApiResponse[list[PayoutOut]],
    summary="List my past withdrawal/payout requests",
)
@unified_router.get(
    "/payouts",
    response_model=ApiResponse[list[PayoutOut]],
    summary="List my past withdrawal/payout requests",
)
async def my_payouts(
    user: ProfessionalUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ApiResponse[list[PayoutOut]]:
    payouts = await payout_service.list_payouts_for_astrologer(user.id, limit)
    data = [
        PayoutOut(
            id=str(p.id),
            astrologer_id=str(p.astrologer_id) if p.astrologer_id else None,
            purohit_id=str(p.purohit_id) if p.purohit_id else None,
            beneficiary_type=p.beneficiary_type,
            beneficiary_name=p.beneficiary_name,
            astrologer_name=p.beneficiary_name,
            amount_paise=p.amount_paise,
            tds_percent=p.tds_percent,
            tds_paise=p.tds_paise,
            net_payable_paise=p.net_payable_paise,
            payout_method=p.payout_method,
            bank_name=p.bank_name,
            account_holder_name=p.account_holder_name,
            account_number_last4=p.account_number_last4,
            account_number_masked=p.account_number_masked,
            ifsc=p.ifsc,
            upi_id=p.upi_id,
            upi_qr_url=p.upi_qr_url,
            status=p.status,
            utr_number=p.utr_number,
            admin_notes=p.admin_notes,
            rejection_reason=p.rejection_reason,
            requested_at=p.requested_at,
            approved_at=p.approved_at,
            settled_at=p.settled_at,
            rejected_at=p.rejected_at,
        )
        for p in payouts
    ]
    return ApiResponse(message=f"{len(payouts)} payout records found.", data=data)


@router.patch(
    "/bank-details",
    response_model=ApiResponse[dict],
    summary="Update bank account and UPI details for payouts",
)
@unified_router.patch(
    "/bank-details",
    response_model=ApiResponse[dict],
    summary="Update bank account and UPI details for payouts",
)
async def update_bank_details(
    body: BankDetailsUpdateIn,
    user: ProfessionalUser,
) -> ApiResponse[dict]:
    profile, b_type = await _get_profile_for_user(user)
    bank = profile.bank

    if body.account_holder_name is not None:
        bank.account_holder_name = body.account_holder_name.strip()
    if body.account_number is not None:
        bank.account_number = body.account_number.strip()
        if len(bank.account_number) >= 4:
            bank.account_number_last4 = bank.account_number[-4:]
    if body.ifsc is not None:
        bank.ifsc = body.ifsc.strip().upper()
    if body.bank_name is not None:
        bank.bank_name = body.bank_name.strip()
    if body.upi_id is not None:
        bank.upi_id = body.upi_id.strip()
    if body.pan_card is not None:
        bank.pan_card = body.pan_card.strip().upper()

    await profile.save()
    return ApiResponse(
        message="Bank and UPI details updated successfully.",
        data={
            "saved": True,
            "bank_name": bank.bank_name,
            "account_holder_name": bank.account_holder_name,
            "account_number_last4": bank.account_number_last4,
            "ifsc": bank.ifsc,
            "upi_id": bank.upi_id,
            "upi_qr_url": bank.upi_qr_url,
        },
    )


# ====================================================================
# UPI QR Code Lifecycle Handlers (Cloudinary Storage Optimized)
# ====================================================================

@router.post(
    "/upi-qr",
    response_model=ApiResponse[dict],
    summary="Upload or update UPI QR Code image (auto-cleans old Cloudinary asset)",
)
@unified_router.post(
    "/upi-qr",
    response_model=ApiResponse[dict],
    summary="Upload or update UPI QR Code image (auto-cleans old Cloudinary asset)",
)
async def upload_upi_qr(
    file: UploadFile = File(...),
    user: ProfessionalUser = ...,
) -> ApiResponse[dict]:
    """Uploads a new UPI QR code image and permanently purges the previous Cloudinary file."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{file.content_type}'. Please upload PNG, JPG, or WEBP.",
        )

    profile, b_type = await _get_profile_for_user(user)
    old_qr_url = getattr(profile.bank, "upi_qr_url", None)

    # 1. Safely remove existing QR from Cloudinary to prevent orphaned storage
    if old_qr_url and "cloudinary.com" in old_qr_url:
        await safe_delete_cloudinary_image(old_qr_url)

    # 2. Upload new QR to Cloudinary under 'upi_qr_codes' folder
    res = await upload_file(
        file=file,
        folder="upi_qr_codes",
        allowed_types=ALLOWED_IMAGE_TYPES,
    )

    profile.bank.upi_qr_url = res.secure_url
    profile.bank.upi_qr_public_id = res.public_id
    await profile.save()

    return ApiResponse(
        message="UPI QR code uploaded and linked successfully.",
        data={
            "upi_qr_url": res.secure_url,
            "upi_qr_public_id": res.public_id,
        },
    )


@router.delete(
    "/upi-qr",
    response_model=ApiResponse[dict],
    summary="Delete UPI QR Code (purges Cloudinary asset permanently)",
)
@unified_router.delete(
    "/upi-qr",
    response_model=ApiResponse[dict],
    summary="Delete UPI QR Code (purges Cloudinary asset permanently)",
)
async def delete_upi_qr(user: ProfessionalUser) -> ApiResponse[dict]:
    """Deletes the current UPI QR code from Cloudinary and clears it from the profile."""
    profile, b_type = await _get_profile_for_user(user)
    old_qr_url = getattr(profile.bank, "upi_qr_url", None)

    if old_qr_url and "cloudinary.com" in old_qr_url:
        await safe_delete_cloudinary_image(old_qr_url)

    profile.bank.upi_qr_url = None
    profile.bank.upi_qr_public_id = None
    await profile.save()

    return ApiResponse(
        message="UPI QR code deleted successfully.",
        data={"deleted": True},
    )


# ====================================================================
# Admin Financial Management & Payout Desks
# ====================================================================
admin_router = APIRouter(prefix="/admin/earnings", tags=["admin: earnings"])


@admin_router.get(
    "", response_model=ApiResponse[AdminEarningsSummary], summary="Platform earnings"
)
async def platform_earnings(_: AdminUser) -> ApiResponse[AdminEarningsSummary]:
    totals = await earnings_service.platform_totals()
    return ApiResponse(
        message="Earnings fetched.",
        data=AdminEarningsSummary(
            gross_paise=totals["gross_paise"],
            commission_paise=totals["commission_paise"],
            payout_paise=totals["earning_paise"],
            coins_charged=totals["coins_charged"],
            sessions=totals["sessions"],
        ),
    )


@admin_router.get(
    "/recent",
    response_model=ApiResponse[list[AdminEarningRow]],
    summary="Recent earnings, with the split",
)
async def recent_platform_earnings(
    _: AdminUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    skip: Annotated[int, Query(ge=0)] = 0,
    mode: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[AdminEarningRow]]:
    rows = await earnings_service.recent_all(limit=limit, skip=skip, mode=mode, search=search)
    names = {
        a.id: a.display_name
        for a in await Astrologer.find(
            {"_id": {"$in": [r["astrologer_id"] for r in rows]}}
        ).to_list()
    }
    user_ids = [r["user_id"] for r in rows if r.get("user_id")]
    user_map = {}
    if user_ids:
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        user_map = {u.id: u for u in users}

    admin_data: list[AdminEarningRow] = []
    for r in rows:
        uid = r.get("user_id")
        u = user_map.get(uid) if uid else None
        uname = u.full_name if u else None
        uavatar = u.avatar_url if u else None
        admin_data.append(
            AdminEarningRow(
                id=str(r["_id"]),
                mode=r["mode"],
                minutes=r["minutes"],
                earning_paise=r["earning_paise"],
                created_at=r["created_at"],
                astrologer_id=str(r["astrologer_id"]),
                astrologer_name=names.get(r["astrologer_id"]),
                coins_charged=r["coins_charged"],
                gross_paise=r["gross_paise"],
                commission_percent=r["commission_percent"],
                commission_paise=r["commission_paise"],
                user_id=str(uid) if uid else None,
                user_name=uname,
                user_avatar=uavatar,
                user_image_url=uavatar,
            )
        )

    return ApiResponse(
        message=f"{len(rows)} consultation{'' if len(rows) == 1 else 's'}.",
        data=admin_data,
    )


@admin_router.get(
    "/paginated",
    response_model=ApiResponse[Paginated[AdminEarningRow]],
    summary="Paginated platform consultation earnings split",
)
async def paginated_platform_earnings(
    _: AdminUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=200)] = 20,
    mode: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> ApiResponse[Paginated[AdminEarningRow]]:
    rows, total = await earnings_service.paginated_all(
        page=page, limit=limit, mode=mode, search=search
    )
    names = {
        a.id: a.display_name
        for a in await Astrologer.find(
            {"_id": {"$in": [r["astrologer_id"] for r in rows]}}
        ).to_list()
    }
    user_ids = [r["user_id"] for r in rows if r.get("user_id")]
    user_map = {}
    if user_ids:
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        user_map = {u.id: u for u in users}

    admin_data: list[AdminEarningRow] = []
    for r in rows:
        uid = r.get("user_id")
        u = user_map.get(uid) if uid else None
        uname = u.full_name if u else None
        uavatar = u.avatar_url if u else None
        admin_data.append(
            AdminEarningRow(
                id=str(r["_id"]),
                mode=r["mode"],
                minutes=r["minutes"],
                earning_paise=r["earning_paise"],
                created_at=r["created_at"],
                astrologer_id=str(r["astrologer_id"]),
                astrologer_name=names.get(r["astrologer_id"]),
                coins_charged=r["coins_charged"],
                gross_paise=r["gross_paise"],
                commission_percent=r["commission_percent"],
                commission_paise=r["commission_paise"],
                user_id=str(uid) if uid else None,
                user_name=uname,
                user_avatar=uavatar,
                user_image_url=uavatar,
            )
        )

    return ApiResponse(
        message=f"Page {page} of {build_page(admin_data, total, page, limit).meta.total_pages} consultations.",
        data=build_page(admin_data, total, page, limit),
    )


@admin_router.get(
    "/payouts",
    response_model=ApiResponse[list[PayoutOut]],
    summary="List all payout requests with optional beneficiary_type and status filter",
)
async def list_admin_payouts(
    _: AdminUser,
    status: Annotated[PayoutStatus | None, Query()] = None,
    beneficiary_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> ApiResponse[list[PayoutOut]]:
    data = await payout_service.list_all_payouts_for_admin(
        status=status,
        beneficiary_type=beneficiary_type,
        limit=limit,
    )
    return ApiResponse(
        message=f"{len(data)} payout requests found.",
        data=[PayoutOut(**d) for d in data],
    )


@admin_router.get(
    "/payout-analytics",
    response_model=ApiResponse[PayoutAnalyticsOut],
    summary="Get aggregated payout analytics for Astrologers vs Purohits",
)
async def get_admin_payout_analytics(_: AdminUser) -> ApiResponse[PayoutAnalyticsOut]:
    data = await payout_service.get_payout_analytics_for_admin()
    return ApiResponse(
        message="Payout analytics computed successfully.",
        data=PayoutAnalyticsOut(**data),
    )


@admin_router.get(
    "/beneficiary/{user_id}/breakdown",
    response_model=ApiResponse[BeneficiaryBreakdownResponse],
    summary="Get granular earnings breakdown for a specific astrologer or purohit",
)
async def get_admin_beneficiary_breakdown(
    user_id: str,
    _: AdminUser,
) -> ApiResponse[BeneficiaryBreakdownResponse]:
    data = await payout_service.get_beneficiary_breakdown_for_admin(PydanticObjectId(user_id))
    return ApiResponse(
        message="Beneficiary breakdown retrieved successfully.",
        data=BeneficiaryBreakdownResponse(**data),
    )


@admin_router.post(
    "/payouts/{id}/settle",
    response_model=ApiResponse[PayoutOut],
    summary="Mark an astrologer or purohit payout request as settled with UTR reference",
)
async def settle_admin_payout(
    id: str,
    body: SettlePayoutIn,
    admin: AdminUser,
) -> ApiResponse[PayoutOut]:
    p = await payout_service.settle_payout(
        payout_id=PydanticObjectId(id),
        admin_user_id=admin.id,
        utr_number=body.utr_number,
        admin_notes=body.admin_notes,
    )
    return ApiResponse(
        message=f"Payout of ₹{p.amount_paise / 100:.2f} marked settled with UTR {p.utr_number}.",
        data=PayoutOut(
            id=str(p.id),
            astrologer_id=str(p.astrologer_id) if p.astrologer_id else None,
            purohit_id=str(p.purohit_id) if p.purohit_id else None,
            beneficiary_type=p.beneficiary_type,
            beneficiary_name=p.beneficiary_name,
            astrologer_name=p.beneficiary_name,
            amount_paise=p.amount_paise,
            tds_percent=p.tds_percent,
            tds_paise=p.tds_paise,
            net_payable_paise=p.net_payable_paise,
            payout_method=p.payout_method,
            bank_name=p.bank_name,
            account_holder_name=p.account_holder_name,
            account_number_last4=p.account_number_last4,
            account_number_masked=p.account_number_masked,
            ifsc=p.ifsc,
            upi_id=p.upi_id,
            upi_qr_url=p.upi_qr_url,
            status=p.status,
            utr_number=p.utr_number,
            admin_notes=p.admin_notes,
            rejection_reason=p.rejection_reason,
            requested_at=p.requested_at,
            approved_at=p.approved_at,
            settled_at=p.settled_at,
            rejected_at=p.rejected_at,
        ),
    )


@admin_router.post(
    "/payouts/{id}/reject",
    response_model=ApiResponse[PayoutOut],
    summary="Reject a payout request and restore available balance",
)
async def reject_admin_payout(
    id: str,
    body: RejectPayoutIn,
    admin: AdminUser,
) -> ApiResponse[PayoutOut]:
    p = await payout_service.reject_payout(
        payout_id=PydanticObjectId(id),
        admin_user_id=admin.id,
        rejection_reason=body.rejection_reason,
    )
    return ApiResponse(
        message=f"Payout request rejected: {p.rejection_reason}.",
        data=PayoutOut(
            id=str(p.id),
            astrologer_id=str(p.astrologer_id) if p.astrologer_id else None,
            purohit_id=str(p.purohit_id) if p.purohit_id else None,
            beneficiary_type=p.beneficiary_type,
            beneficiary_name=p.beneficiary_name,
            astrologer_name=p.beneficiary_name,
            amount_paise=p.amount_paise,
            tds_percent=p.tds_percent,
            tds_paise=p.tds_paise,
            net_payable_paise=p.net_payable_paise,
            payout_method=p.payout_method,
            bank_name=p.bank_name,
            account_holder_name=p.account_holder_name,
            account_number_last4=p.account_number_last4,
            account_number_masked=p.account_number_masked,
            ifsc=p.ifsc,
            upi_id=p.upi_id,
            upi_qr_url=p.upi_qr_url,
            status=p.status,
            utr_number=p.utr_number,
            admin_notes=p.admin_notes,
            rejection_reason=p.rejection_reason,
            requested_at=p.requested_at,
            approved_at=p.approved_at,
            settled_at=p.settled_at,
            rejected_at=p.rejected_at,
        ),
    )
