"""The signed-in user's wallet, and the Razorpay webhook."""

from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Request, status
from loguru import logger

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.models.astrologer import Astrologer
from app.models.call import CallSession
from app.models.chat import ChatSession
from app.models.enums import PaymentOrderStatus, TransactionReason
from app.models.wallet import WalletTransaction
from app.schemas.common import ApiResponse, Paginated, build_page
from app.schemas.wallet import (
    CreateOrderRequest,
    CreateOrderResponse,
    RechargeOptions,
    RechargePack,
    TransactionOut,
    TransactionRefOut,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    WalletBalance,
    WalletSummary,
)
from app.services import payments as payment_service
from app.services import settings as settings_service
from app.services import wallet as wallet_service

router = APIRouter(prefix="/wallet", tags=["wallet"])


def to_transaction(
    txn: WalletTransaction,
    astro_info: dict[str, Any] | None = None,
) -> TransactionOut:
    info = astro_info or {}
    astro_id = (
        str(txn.ref.astrologer_id)
        if txn.ref.astrologer_id
        else info.get("astrologer_id")
    )
    astro_name = txn.ref.astrologer_name or info.get("astrologer_name")
    astro_img = txn.ref.astrologer_image_url or info.get("astrologer_image_url")
    mode = txn.ref.consultation_mode or info.get("consultation_mode")

    return TransactionOut(
        id=str(txn.id),
        direction=txn.direction,
        reason=txn.reason,
        amount_coins=txn.amount_coins,
        balance_after_coins=txn.balance_after_coins,
        note=txn.note,
        amount_paise=txn.amount_paise,
        coins_per_rupee=txn.coins_per_rupee,
        ref=TransactionRefOut(
            razorpay_order_id=txn.ref.razorpay_order_id,
            razorpay_payment_id=txn.ref.razorpay_payment_id,
            razorpay_refund_id=txn.ref.razorpay_refund_id,
            session_id=str(txn.ref.session_id) if txn.ref.session_id else None,
            astrologer_id=astro_id,
            astrologer_name=astro_name,
            astrologer_image_url=astro_img,
            consultation_mode=mode,
        ),
        created_at=txn.created_at,
        astrologer_id=astro_id,
        astrologer_name=astro_name,
        astrologer_image_url=astro_img,
        consultation_mode=mode,
    )


async def enrich_transactions(items: list[WalletTransaction]) -> list[TransactionOut]:
    """Batch resolves astrologer info for consultation transactions, including historical ones."""
    needed_sessions = [
        t.ref.session_id
        for t in items
        if t.ref.session_id and not t.ref.astrologer_name
    ]

    session_map: dict[str, dict[str, Any]] = {}
    if needed_sessions:
        chats = await ChatSession.find({"_id": {"$in": needed_sessions}}).to_list()
        calls = await CallSession.find({"_id": {"$in": needed_sessions}}).to_list()

        astro_ids = set()
        for c in chats:
            astro_ids.add(c.astrologer_id)
        for cl in calls:
            astro_ids.add(cl.astrologer_id)

        astros = (
            await Astrologer.find({"_id": {"$in": list(astro_ids)}}).to_list()
            if astro_ids
            else []
        )
        astro_dict = {a.id: a for a in astros}

        for c in chats:
            a = astro_dict.get(c.astrologer_id)
            session_map[str(c.id)] = {
                "astrologer_id": str(c.astrologer_id),
                "astrologer_name": a.display_name if a else None,
                "astrologer_image_url": a.profile_image_url if a else None,
                "consultation_mode": "chat",
            }
        for cl in calls:
            a = astro_dict.get(cl.astrologer_id)
            session_map[str(cl.id)] = {
                "astrologer_id": str(cl.astrologer_id),
                "astrologer_name": a.display_name if a else None,
                "astrologer_image_url": a.profile_image_url if a else None,
                "consultation_mode": cl.mode.value if hasattr(cl.mode, "value") else str(cl.mode),
            }

    return [
        to_transaction(
            t,
            astro_info=session_map.get(str(t.ref.session_id)) if t.ref.session_id else None,
        )
        for t in items
    ]


def to_balance(wallet: Any) -> WalletBalance:
    return WalletBalance(
        balance_coins=wallet.balance_coins,
        is_frozen=wallet.is_frozen,
        frozen_reason=wallet.frozen_reason,
        last_transaction_at=wallet.last_transaction_at,
    )


# ------------------------------------------------------------------ balance
@router.get("", response_model=ApiResponse[WalletSummary], summary="My balance and recent activity")
async def my_wallet(user: CurrentUser) -> ApiResponse[WalletSummary]:
    wallet = await wallet_service.get_or_create_wallet(user.id)
    recent, _ = await wallet_service.list_transactions(user.id, page=1, limit=5)
    enriched_recent = await enrich_transactions(recent)
    return ApiResponse(
        message="Wallet fetched.",
        data=WalletSummary(
            wallet=to_balance(wallet), recent=enriched_recent
        ),
    )


@router.get(
    "/transactions",
    response_model=ApiResponse[Paginated[TransactionOut]],
    summary="My transaction history",
)
async def my_transactions(
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    reason: TransactionReason | None = None,
) -> ApiResponse[Paginated[TransactionOut]]:
    items, total = await wallet_service.list_transactions(
        user.id, page=page, limit=limit, reason=reason
    )
    enriched_items = await enrich_transactions(items)
    return ApiResponse(
        message=f"{total} transaction(s).",
        data=build_page(enriched_items, total, page, limit),
    )


# ----------------------------------------------------------------- recharge
@router.get(
    "/recharge/options",
    response_model=ApiResponse[RechargeOptions],
    summary="Preset amounts, limits and the public checkout key",
)
async def recharge_options() -> ApiResponse[RechargeOptions]:
    platform = await settings_service.get_settings()
    coins_per_rupee = platform.coins_per_rupee
    return ApiResponse(
        message="Recharge options.",
        data=RechargeOptions(
            # A preset below the minimum is a button that cannot be pressed,
            # so it is left out rather than shown and refused.
            packs=[
                RechargePack(
                    amount_paise=p,
                    amount_rupees=p // 100,
                    coins=settings_service.coins_for(p, coins_per_rupee),
                )
                for p in settings.RECHARGE_PACKS_PAISE
                if platform.min_recharge_paise <= p <= platform.max_recharge_paise
            ],
            coins_per_rupee=coins_per_rupee,
            min_paise=platform.min_recharge_paise,
            max_paise=platform.max_recharge_paise,
            currency=settings.WALLET_CURRENCY,
            key_id=settings.RAZORPAY_KEY_ID,
            enabled=payment_service.is_enabled(),
        ),
    )


@router.post(
    "/recharge/order",
    response_model=ApiResponse[CreateOrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Open a Razorpay order for a recharge",
)
async def create_recharge_order(
    payload: CreateOrderRequest, user: CurrentUser
) -> ApiResponse[CreateOrderResponse]:
    order = await payment_service.create_order(user, payload.amount_paise)
    return ApiResponse(
        message="Order created.",
        data=CreateOrderResponse(
            razorpay_order_id=order.razorpay_order_id,
            amount_paise=order.amount_paise,
            coins=order.coins,
            coins_per_rupee=order.coins_per_rupee,
            currency=order.currency,
            key_id=settings.RAZORPAY_KEY_ID,
            receipt=order.receipt,
            name=user.full_name,
            email=user.email,
            contact=user.phone,
        ),
    )


@router.post(
    "/recharge/verify",
    response_model=ApiResponse[VerifyPaymentResponse],
    summary="Confirm a payment the browser just completed",
)
async def verify_recharge(
    payload: VerifyPaymentRequest, user: CurrentUser
) -> ApiResponse[VerifyPaymentResponse]:
    order, credited = await payment_service.verify_callback(
        user=user,
        order_id=payload.razorpay_order_id,
        payment_id=payload.razorpay_payment_id,
        signature=payload.razorpay_signature,
    )
    wallet = await wallet_service.get_or_create_wallet(user.id)
    return ApiResponse(
        message=(
            f"{order.coins} coins added."
            if credited
            else "This payment was already credited."
        ),
        data=VerifyPaymentResponse(
            status=order.status,
            credited=credited,
            amount_paise=order.amount_paise,
            coins=order.coins,
            balance_coins=wallet.balance_coins,
        ),
    )


# ------------------------------------------------------------------ webhook
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@webhook_router.post(
    "/razorpay",
    summary="Razorpay webhook (signature-authenticated, not a user endpoint)",
    include_in_schema=False,
)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Annotated[str | None, Header()] = None,
    x_razorpay_event_id: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    # Raw bytes, before any parsing: the signature is over exactly what was
    # sent, and re-serialising the JSON would change it.
    raw = await request.body()
    payment_service.verify_webhook_signature(raw, x_razorpay_signature)

    body = await request.json()
    result = await payment_service.handle_webhook(event_id=x_razorpay_event_id, body=body)
    logger.info("Razorpay webhook '{}' -> {}", body.get("event"), result)

    # Razorpay retries anything that is not 2xx, so a handled event must answer 200.
    return {"success": True, "result": result}
