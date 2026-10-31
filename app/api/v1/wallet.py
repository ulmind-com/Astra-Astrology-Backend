"""The signed-in user's wallet, and the Razorpay webhook."""

from typing import Annotated, Any

from beanie import PydanticObjectId
from fastapi import APIRouter, Header, Query, Request, status
from loguru import logger

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.models.appointment import Appointment
from app.models.astrologer import Astrologer
from app.models.call import CallSession
from app.models.chat import ChatSession
from app.models.enums import TransactionReason
from app.models.wallet import WalletTransaction
from app.schemas.common import ApiResponse, Paginated, build_page
from app.schemas.wallet import (
    ConsultationMetadataOut,
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


async def enrich_consultations(
    transactions: list[WalletTransaction],
) -> dict[str, ConsultationMetadataOut]:
    session_ids: list[PydanticObjectId] = []
    for t in transactions:
        if t.ref and t.ref.session_id and isinstance(t.ref.session_id, PydanticObjectId):
            session_ids.append(t.ref.session_id)

    if not session_ids:
        return {}

    unique_session_ids = list(set(session_ids))
    chats = await ChatSession.find({"_id": {"$in": unique_session_ids}}).to_list()
    calls = await CallSession.find({"_id": {"$in": unique_session_ids}}).to_list()
    appts = await Appointment.find({"_id": {"$in": unique_session_ids}}).to_list()

    astro_ids: set[PydanticObjectId] = set()
    for c in chats:
        astro_ids.add(c.astrologer_id)
    for c in calls:
        astro_ids.add(c.astrologer_id)
    for a in appts:
        astro_ids.add(a.astrologer_id)

    astro_map: dict[str, Astrologer] = {}
    if astro_ids:
        astros = await Astrologer.find({"_id": {"$in": list(astro_ids)}}).to_list()
        astro_map = {str(a.id): a for a in astros}

    out: dict[str, ConsultationMetadataOut] = {}
    for c in chats:
        astro = astro_map.get(str(c.astrologer_id))
        out[str(c.id)] = ConsultationMetadataOut(
            session_id=str(c.id),
            astrologer_id=str(c.astrologer_id),
            astrologer_name=astro.display_name if astro else None,
            astrologer_avatar=astro.profile_image_url if astro else None,
            mode="chat",
            duration_seconds=c.duration_seconds,
        )

    for c in calls:
        astro = astro_map.get(str(c.astrologer_id))
        mode_val = c.mode.value if hasattr(c.mode, "value") else str(c.mode)
        out[str(c.id)] = ConsultationMetadataOut(
            session_id=str(c.id),
            astrologer_id=str(c.astrologer_id),
            astrologer_name=astro.display_name if astro else None,
            astrologer_avatar=astro.profile_image_url if astro else None,
            mode=mode_val,
            duration_seconds=c.duration_seconds,
        )

    for a in appts:
        astro = astro_map.get(str(a.astrologer_id))
        out[str(a.id)] = ConsultationMetadataOut(
            session_id=str(a.id),
            astrologer_id=str(a.astrologer_id),
            astrologer_name=astro.display_name if astro else None,
            astrologer_avatar=astro.profile_image_url if astro else None,
            mode="appointment",
            duration_seconds=a.minutes * 60,
        )

    return out


def to_transaction(
    txn: WalletTransaction,
    consultations: dict[str, ConsultationMetadataOut] | None = None,
) -> TransactionOut:
    session_id_str = str(txn.ref.session_id) if txn.ref and txn.ref.session_id else None
    consultation = (
        consultations.get(session_id_str) if (consultations and session_id_str) else None
    )

    note = txn.note
    if consultation and consultation.astrologer_name and note:
        lower_note = note.lower()
        if (
            lower_note.startswith("chat")
            or lower_note.startswith("call")
            or lower_note.startswith("video")
        ):
            mode_display = (consultation.mode or "Consultation").capitalize()
            if " · " in note:
                rest = note.split(" · ", 1)[1]
                note = f"{mode_display} with {consultation.astrologer_name} · {rest}"
            else:
                note = f"{mode_display} with {consultation.astrologer_name}"

    return TransactionOut(
        id=str(txn.id),
        direction=txn.direction,
        reason=txn.reason,
        amount_coins=txn.amount_coins,
        balance_after_coins=txn.balance_after_coins,
        note=note,
        amount_paise=txn.amount_paise,
        coins_per_rupee=txn.coins_per_rupee,
        ref=TransactionRefOut(
            razorpay_order_id=txn.ref.razorpay_order_id,
            razorpay_payment_id=txn.ref.razorpay_payment_id,
            razorpay_refund_id=txn.ref.razorpay_refund_id,
            session_id=session_id_str,
        ),
        consultation=consultation,
        created_at=txn.created_at,
    )


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
    consultations = await enrich_consultations(recent)
    return ApiResponse(
        message="Wallet fetched.",
        data=WalletSummary(
            wallet=to_balance(wallet),
            recent=[to_transaction(t, consultations) for t in recent],
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
    consultations = await enrich_consultations(items)
    return ApiResponse(
        message=f"{total} transaction(s).",
        data=build_page(
            [to_transaction(t, consultations) for t in items], total, page, limit
        ),
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
