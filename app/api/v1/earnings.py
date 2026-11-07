"""Earnings — one ledger, two views.

An astrologer sees what they were credited. An admin sees the split. The client
was explicit that an astrologer should not be shown the commission being taken,
so that figure is simply absent from their response rather than hidden in the UI.
"""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query

from app.api.dependencies import AdminUser, CurrentAstrologer, CurrentUser
from app.models.astrologer import Astrologer
from app.models.payout import PayoutMethod, PayoutStatus
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.wallet import (
    AdminEarningRow,
    AdminEarningsSummary,
    AstrologerEarningsBalanceOut,
    BankDetailsUpdateIn,
    EarningRow,
    EarningsBucket,
    EarningsSummary,
    PayoutOut,
    PayoutRequestIn,
    RejectPayoutIn,
    SettlePayoutIn,
)
from app.services import earnings as earnings_service
from app.services import payout as payout_service

router = APIRouter(prefix="/astrologers/me/earnings", tags=["astrologer: earnings"])


@router.get("", response_model=ApiResponse[EarningsSummary], summary="What I have earned")
async def my_earnings(
    _: CurrentAstrologer, user: CurrentUser
) -> ApiResponse[EarningsSummary]:
    totals = await earnings_service.for_astrologer(user.id)

    def bucket(name: str) -> EarningsBucket:
        row = totals[name]
        return EarningsBucket(
            earning_paise=row["earning_paise"],
            minutes=row["minutes"],
            sessions=row["sessions"],
        )

    return ApiResponse(
        message="Earnings fetched.",
        data=EarningsSummary(
            today=bucket("today"),
            this_week=bucket("this_week"),
            this_month=bucket("this_month"),
            all_time=bucket("all_time"),
        ),
    )


@router.get(
    "/balance",
    response_model=ApiResponse[AstrologerEarningsBalanceOut],
    summary="My live financial balances & withdrawable amount",
)
async def my_earnings_balance(
    _: CurrentAstrologer, user: CurrentUser
) -> ApiResponse[AstrologerEarningsBalanceOut]:
    data = await payout_service.get_astrologer_earnings_balance(user.id)
    return ApiResponse(
        message="Earnings balance calculated successfully.",
        data=AstrologerEarningsBalanceOut(**data),
    )


@router.get(
    "/recent", response_model=ApiResponse[list[EarningRow]], summary="My recent earnings"
)
async def my_recent_earnings(
    _: CurrentAstrologer,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    skip: Annotated[int, Query(ge=0)] = 0,
    mode: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[EarningRow]]:
    rows = await earnings_service.recent_for_astrologer(user.id, limit=limit, skip=skip, mode=mode)
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


@router.post(
    "/payout-request",
    response_model=ApiResponse[PayoutOut],
    summary="Request a withdrawal/payout to bank or UPI",
)
async def request_payout(
    body: PayoutRequestIn,
    _: CurrentAstrologer,
    user: CurrentUser,
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
            astrologer_id=str(payout.astrologer_id),
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
async def my_payouts(
    _: CurrentAstrologer,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ApiResponse[list[PayoutOut]]:
    payouts = await payout_service.list_payouts_for_astrologer(user.id, limit)
    data = [
        PayoutOut(
            id=str(p.id),
            astrologer_id=str(p.astrologer_id),
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
async def update_bank_details(
    body: BankDetailsUpdateIn,
    _: CurrentAstrologer,
    user: CurrentUser,
) -> ApiResponse[dict]:
    astrologer = await Astrologer.find_one({"user_id": user.id})
    if not astrologer:
        raise NotFoundError("Astrologer not found.")

    bank = astrologer.bank
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

    await astrologer.save()
    return ApiResponse(message="Bank details updated successfully.", data={"saved": True})


# ------------------------------------------------------------------- admin
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
    _: AdminUser, limit: Annotated[int, Query(ge=1, le=200)] = 100
) -> ApiResponse[list[AdminEarningRow]]:
    rows = await earnings_service.recent_all(limit)
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
    "/payouts",
    response_model=ApiResponse[list[PayoutOut]],
    summary="List all astrologer payout/withdrawal requests",
)
async def list_admin_payouts(
    _: AdminUser,
    status: Annotated[PayoutStatus | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> ApiResponse[list[PayoutOut]]:
    data = await payout_service.list_all_payouts_for_admin(status=status, limit=limit)
    return ApiResponse(
        message=f"{len(data)} payout requests found.",
        data=[PayoutOut(**d) for d in data],
    )


@admin_router.post(
    "/payouts/{id}/settle",
    response_model=ApiResponse[PayoutOut],
    summary="Mark an astrologer payout request as settled with UTR reference",
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
            astrologer_id=str(p.astrologer_id),
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
    summary="Reject an astrologer payout request and refund to available balance",
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
            astrologer_id=str(p.astrologer_id),
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
