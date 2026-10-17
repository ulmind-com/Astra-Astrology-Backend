"""Admin view of the money: balances, every movement, and manual corrections.

A manual adjustment is the one place money moves without a payment behind it,
so it always records who did it and why.
"""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Query

from app.api.dependencies import AdminUser
from app.api.v1.wallet import to_balance, to_transaction
from app.core.exceptions import NotFoundError
from app.models.enums import (
    PaymentOrderStatus,
    TransactionDirection,
    TransactionReason,
)
from app.models.user import User
from app.models.wallet import PaymentOrder, Wallet, WalletTransaction
from app.schemas.common import ApiResponse, Paginated, build_page
from app.schemas.wallet import (
    AdjustWalletRequest,
    AdminTransactionOut,
    AdminWalletOut,
    FreezeWalletRequest,
    PaymentOrderOut,
    ReconcileResult,
    WalletBalance,
)
from app.services import payments as payment_service
from app.services import wallet as wallet_service

router = APIRouter(prefix="/admin/wallets", tags=["admin: wallets"])


async def _require_user(user_id: PydanticObjectId) -> User:
    user = await User.get(user_id)
    if user is None:
        raise NotFoundError("User not found.", error_code="user_not_found")
    return user


# ------------------------------------------------------------------ listing
@router.get("", response_model=ApiResponse[Paginated[AdminWalletOut]], summary="All wallets")
async def list_wallets(
    _: AdminUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=120)] = None,
    frozen: bool | None = None,
) -> ApiResponse[Paginated[AdminWalletOut]]:
    query = Wallet.find()
    if frozen is not None:
        query = query.find(Wallet.is_frozen == frozen)

    if search:
        matches = await User.find(
            {
                "$or": [
                    {"email": {"$regex": search, "$options": "i"}},
                    {"first_name": {"$regex": search, "$options": "i"}},
                    {"last_name": {"$regex": search, "$options": "i"}},
                ]
            }
        ).to_list()
        query = query.find({"user_id": {"$in": [u.id for u in matches]}})

    total = await query.count()
    wallets = (
        await query.sort(-Wallet.balance_coins).skip((page - 1) * limit).limit(limit).to_list()
    )

    owners = {
        u.id: u for u in await User.find({"_id": {"$in": [w.user_id for w in wallets]}}).to_list()
    }
    items = [
        AdminWalletOut(
            user_id=str(w.user_id),
            name=owners[w.user_id].full_name if w.user_id in owners else "(deleted user)",
            email=owners[w.user_id].email if w.user_id in owners else "—",
            balance_coins=w.balance_coins,
            is_frozen=w.is_frozen,
            frozen_reason=w.frozen_reason,
            last_transaction_at=w.last_transaction_at,
            created_at=w.created_at,
        )
        for w in wallets
    ]
    return ApiResponse(message=f"{total} wallet(s).", data=build_page(items, total, page, limit))


@router.get(
    "/transactions",
    response_model=ApiResponse[Paginated[AdminTransactionOut]],
    summary="Every movement across all wallets",
)
async def list_all_transactions(
    _: AdminUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    user_id: PydanticObjectId | None = None,
    reason: TransactionReason | None = None,
    direction: TransactionDirection | None = None,
) -> ApiResponse[Paginated[AdminTransactionOut]]:
    query = WalletTransaction.find()
    if user_id is not None:
        query = query.find(WalletTransaction.user_id == user_id)
    if reason is not None:
        query = query.find(WalletTransaction.reason == reason)
    if direction is not None:
        query = query.find(WalletTransaction.direction == direction)

    total = await query.count()
    rows = (
        await query.sort(-WalletTransaction.created_at)
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list()
    )
    owners = {
        u.id: u for u in await User.find({"_id": {"$in": [r.user_id for r in rows]}}).to_list()
    }

    items = [
        AdminTransactionOut(
            **to_transaction(r).model_dump(),
            user_id=str(r.user_id),
            user_email=owners[r.user_id].email if r.user_id in owners else None,
            created_by=str(r.created_by) if r.created_by else None,
        )
        for r in rows
    ]
    return ApiResponse(
        message=f"{total} transaction(s).", data=build_page(items, total, page, limit)
    )


@router.get(
    "/payments",
    response_model=ApiResponse[Paginated[PaymentOrderOut]],
    summary="Recharge attempts, including the ones that never completed",
)
async def list_payments(
    _: AdminUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    status_filter: Annotated[PaymentOrderStatus | None, Query(alias="status")] = None,
) -> ApiResponse[Paginated[PaymentOrderOut]]:
    query = PaymentOrder.find()
    if status_filter is not None:
        query = query.find(PaymentOrder.status == status_filter)

    total = await query.count()
    orders = (
        await query.sort(-PaymentOrder.created_at)
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list()
    )
    items = [
        PaymentOrderOut(
            id=str(o.id),
            user_id=str(o.user_id),
            razorpay_order_id=o.razorpay_order_id,
            razorpay_payment_id=o.razorpay_payment_id,
            receipt=o.receipt,
            amount_paise=o.amount_paise,
            coins=o.coins,
            coins_per_rupee=o.coins_per_rupee,
            currency=o.currency,
            status=o.status,
            method=o.method,
            failure_reason=o.failure_reason,
            verified_via=o.verified_via,
            paid_at=o.paid_at,
            created_at=o.created_at,
        )
        for o in orders
    ]
    return ApiResponse(message=f"{total} payment(s).", data=build_page(items, total, page, limit))


@router.post(
    "/payments/{order_id}/reconcile",
    response_model=ApiResponse[PaymentOrderOut],
    summary="Ask Razorpay what happened to a stuck order",
)
async def reconcile_payment(order_id: PydanticObjectId, _: AdminUser) -> ApiResponse[PaymentOrderOut]:
    order = await PaymentOrder.get(order_id)
    if order is None:
        raise NotFoundError("Payment order not found.", error_code="order_not_found")

    order = await payment_service.reconcile_order(order)
    return ApiResponse(
        message=f"Order is {order.status.value}.",
        data=PaymentOrderOut(
            id=str(order.id),
            user_id=str(order.user_id),
            razorpay_order_id=order.razorpay_order_id,
            razorpay_payment_id=order.razorpay_payment_id,
            receipt=order.receipt,
            amount_paise=order.amount_paise,
            currency=order.currency,
            status=order.status,
            method=order.method,
            failure_reason=order.failure_reason,
            verified_via=order.verified_via,
            paid_at=order.paid_at,
            created_at=order.created_at,
        ),
    )


# ------------------------------------------------------------- one wallet
@router.get(
    "/{user_id}", response_model=ApiResponse[WalletBalance], summary="One user's wallet"
)
async def get_wallet(user_id: PydanticObjectId, _: AdminUser) -> ApiResponse[WalletBalance]:
    await _require_user(user_id)
    wallet = await wallet_service.get_or_create_wallet(user_id)
    return ApiResponse(message="Wallet fetched.", data=to_balance(wallet))


@router.post(
    "/{user_id}/adjust",
    response_model=ApiResponse[WalletBalance],
    summary="Move money by hand — recorded with the admin who did it",
)
async def adjust_wallet(
    user_id: PydanticObjectId, payload: AdjustWalletRequest, admin: AdminUser
) -> ApiResponse[WalletBalance]:
    await _require_user(user_id)

    mover = (
        wallet_service.credit
        if payload.direction is TransactionDirection.CREDIT
        else wallet_service.debit
    )
    # Unique per adjustment: an admin may legitimately make the same correction
    # twice, so the key cannot be derived from the amount alone.
    txn, _created = await mover(
        user_id=user_id,
        amount_coins=payload.amount_coins,
        reason=TransactionReason.ADJUSTMENT,
        idempotency_key=f"admin_adjust:{PydanticObjectId()}",
        note=payload.reason,
        created_by=admin.id,
        allow_when_frozen=True,
    )

    wallet = await wallet_service.get_or_create_wallet(user_id)
    return ApiResponse(
        message=f"Wallet adjusted by {txn.amount_coins} coins.", data=to_balance(wallet)
    )


@router.post(
    "/{user_id}/freeze",
    response_model=ApiResponse[WalletBalance],
    summary="Freeze or unfreeze a wallet",
)
async def freeze_wallet(
    user_id: PydanticObjectId, payload: FreezeWalletRequest, _: AdminUser
) -> ApiResponse[WalletBalance]:
    await _require_user(user_id)
    wallet = await wallet_service.set_frozen(
        user_id, frozen=payload.frozen, reason=payload.reason
    )
    return ApiResponse(
        message="Wallet frozen." if payload.frozen else "Wallet unfrozen.",
        data=to_balance(wallet),
    )


@router.post(
    "/{user_id}/reconcile",
    response_model=ApiResponse[ReconcileResult],
    summary="Rebuild the balance from the ledger and report any drift",
)
async def reconcile_wallet(
    user_id: PydanticObjectId, _: AdminUser
) -> ApiResponse[ReconcileResult]:
    await _require_user(user_id)
    result = await wallet_service.recalculate_balance(user_id)
    drift = result["drift_coins"]
    return ApiResponse(
        message="Balance matches the ledger." if drift == 0 else f"Repaired a drift of {drift} coins.",
        data=ReconcileResult(**result),
    )
