"""Earnings — one ledger, two views.

An astrologer sees what they were credited. An admin sees the split. The client
was explicit that an astrologer should not be shown the commission being taken,
so that figure is simply absent from their response rather than hidden in the UI.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import AdminUser, CurrentAstrologer, CurrentUser
from app.models.astrologer import Astrologer
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.wallet import (
    AdminEarningRow,
    AdminEarningsSummary,
    EarningRow,
    EarningsBucket,
    EarningsSummary,
)
from app.services import earnings as earnings_service

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
    "/recent", response_model=ApiResponse[list[EarningRow]], summary="My recent earnings"
)
async def my_recent_earnings(
    _: CurrentAstrologer,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> ApiResponse[list[EarningRow]]:
    rows = await earnings_service.recent_for_astrologer(user.id, limit)
    user_ids = [r["user_id"] for r in rows if r.get("user_id")]
    user_map = {}
    if user_ids:
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        user_map = {u.id: u for u in users}

    data: list[EarningRow] = []
    for r in rows:
        uid = r.get("user_id")
        u = user_map.get(uid) if uid else None
        uname = f"{u.first_name} {u.last_name or ''}".strip() if u else None
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
                coins_charged=r.get("coins_charged"),
                gross_paise=r.get("gross_paise"),
            )
        )

    return ApiResponse(
        message=f"{len(rows)} consultation{'' if len(rows) == 1 else 's'}.",
        data=data,
    )


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
        uname = f"{u.first_name} {u.last_name or ''}".strip() if u else None
        uavatar = u.avatar_url if u else None
        admin_data.append(
            AdminEarningRow(
                id=str(r["_id"]),
                mode=r["mode"],
                minutes=r["minutes"],
                earning_paise=r["earning_paise"],
                created_at=r["created_at"],
                user_id=str(uid) if uid else None,
                user_name=uname,
                user_avatar=uavatar,
                astrologer_id=str(r["astrologer_id"]),
                astrologer_name=names.get(r["astrologer_id"]),
                coins_charged=r["coins_charged"],
                gross_paise=r["gross_paise"],
                commission_percent=r["commission_percent"],
                commission_paise=r["commission_paise"],
            )
        )

    return ApiResponse(
        message=f"{len(rows)} consultation{'' if len(rows) == 1 else 's'}.",
        data=admin_data,
    )
