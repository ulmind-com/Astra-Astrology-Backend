"""Payout & Withdrawal service for Astrologers.

Handles calculation of available withdrawable balance, payout requests,
validation against bank/UPI details, and administrative settlement.
"""

from datetime import UTC, datetime
from typing import Any

from beanie import PydanticObjectId
from loguru import logger

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.astrologer import Astrologer
from app.models.earning import EarningEntry
from app.models.payout import AstrologerPayout, PayoutMethod, PayoutStatus


MIN_PAYOUT_AMOUNT_PAISE = 100000  # ₹1,000


async def get_astrologer_earnings_balance(
    astrologer_user_id: PydanticObjectId,
) -> dict[str, Any]:
    """Computes exact live balances: total earned, settled, pending, and withdrawable."""
    astrologer = await Astrologer.find_one({"user_id": astrologer_user_id})
    if not astrologer:
        raise NotFoundError("Astrologer profile not found.", error_code="astrologer_not_found")

    # 1. Total earned from EarningEntry ledger
    earn_pipeline = [
        {"$match": {"astrologer_user_id": astrologer_user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$earning_paise"}}},
    ]
    earn_res = [r async for r in EarningEntry.get_pymongo_collection().aggregate(earn_pipeline)]
    total_earned = earn_res[0]["total"] if earn_res else 0

    # 2. Total settled payouts
    settled_pipeline = [
        {"$match": {"astrologer_user_id": astrologer_user_id, "status": PayoutStatus.SETTLED}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_paise"}}},
    ]
    settled_res = [r async for r in AstrologerPayout.get_pymongo_collection().aggregate(settled_pipeline)]
    total_settled = settled_res[0]["total"] if settled_res else 0

    # 3. Total pending/approved payouts (funds temporarily locked in transit)
    pending_pipeline = [
        {
            "$match": {
                "astrologer_user_id": astrologer_user_id,
                "status": {"$in": [PayoutStatus.PENDING, PayoutStatus.APPROVED]},
            }
        },
        {"$group": {"_id": None, "total": {"$sum": "$amount_paise"}}},
    ]
    pending_res = [r async for r in AstrologerPayout.get_pymongo_collection().aggregate(pending_pipeline)]
    total_pending = pending_res[0]["total"] if pending_res else 0

    withdrawable = max(0, total_earned - total_settled - total_pending)

    bank = getattr(astrologer, "bank", None)
    has_bank = bool(
        bank
        and (
            (bank.account_number and bank.ifsc)
            or (bank.account_number_last4 and bank.ifsc)
            or bank.upi_id
        )
    )

    return {
        "total_earned_paise": total_earned,
        "total_settled_paise": total_settled,
        "total_pending_paise": total_pending,
        "withdrawable_balance_paise": withdrawable,
        "min_payout_amount_paise": MIN_PAYOUT_AMOUNT_PAISE,
        "bank_name": getattr(bank, "bank_name", None),
        "account_holder_name": getattr(bank, "account_holder_name", None),
        "account_number_last4": getattr(bank, "account_number_last4", None),
        "ifsc": getattr(bank, "ifsc", None),
        "upi_id": getattr(bank, "upi_id", None),
        "pan_card": getattr(bank, "pan_card", None),
        "has_bank_details": has_bank,
    }


async def request_payout(
    astrologer_user_id: PydanticObjectId,
    amount_paise: int,
    payout_method: PayoutMethod = PayoutMethod.BANK_TRANSFER,
    custom_details: dict[str, Any] | None = None,
) -> AstrologerPayout:
    """Submits a new withdrawal request after strict balance & account validation."""
    if amount_paise < 50000:
        raise BadRequestError("Minimum withdrawal request is ₹500 (50,000 paise).", error_code="min_payout_limit")

    astrologer = await Astrologer.find_one({"user_id": astrologer_user_id})
    if not astrologer:
        raise NotFoundError("Astrologer profile not found.", error_code="astrologer_not_found")

    bal = await get_astrologer_earnings_balance(astrologer_user_id)
    withdrawable = bal["withdrawable_balance_paise"]

    if amount_paise > withdrawable:
        raise BadRequestError(
            f"Insufficient withdrawable balance. Available: ₹{withdrawable / 100:.2f}, Requested: ₹{amount_paise / 100:.2f}.",
            error_code="insufficient_withdrawable_balance",
        )

    bank = astrologer.bank
    custom = custom_details or {}

    b_name = custom.get("bank_name") or getattr(bank, "bank_name", None)
    holder_name = custom.get("account_holder_name") or getattr(bank, "account_holder_name", None) or astrologer.display_name
    acc_num = custom.get("account_number") or getattr(bank, "account_number", None)
    ifsc = custom.get("ifsc") or getattr(bank, "ifsc", None)
    upi = custom.get("upi_id") or getattr(bank, "upi_id", None)

    if payout_method == PayoutMethod.UPI:
        if not upi or "@" not in upi:
            raise BadRequestError("A valid UPI ID (e.g. yourname@upi) is required for UPI payout.", error_code="invalid_upi")
    else:
        if not acc_num or not ifsc:
            if not getattr(bank, "account_number_last4", None) or not ifsc:
                raise BadRequestError("Bank account number and IFSC code are required for bank transfer.", error_code="missing_bank_details")

    acc_last4 = acc_num[-4:] if acc_num and len(acc_num) >= 4 else getattr(bank, "account_number_last4", None)
    acc_masked = f"••••••••{acc_last4}" if acc_last4 else None

    # Update bank details on profile if new details provided
    if custom.get("account_number") or custom.get("ifsc") or custom.get("upi_id"):
        if custom.get("account_number"):
            bank.account_number = custom["account_number"]
            bank.account_number_last4 = acc_last4
        if custom.get("ifsc"):
            bank.ifsc = custom["ifsc"].strip().upper()
        if custom.get("bank_name"):
            bank.bank_name = custom["bank_name"].strip()
        if custom.get("account_holder_name"):
            bank.account_holder_name = custom["account_holder_name"].strip()
        if custom.get("upi_id"):
            bank.upi_id = custom["upi_id"].strip()
        await astrologer.save()

    now = datetime.now(UTC)
    tds_percent = 0.0
    tds_paise = round(amount_paise * (tds_percent / 100))
    net_payable = amount_paise - tds_paise

    payout = AstrologerPayout(
        astrologer_id=astrologer.id,
        astrologer_user_id=astrologer_user_id,
        amount_paise=amount_paise,
        tds_percent=tds_percent,
        tds_paise=tds_paise,
        net_payable_paise=net_payable,
        payout_method=payout_method,
        bank_name=b_name,
        account_holder_name=holder_name,
        account_number_last4=acc_last4,
        account_number_masked=acc_masked,
        ifsc=ifsc,
        upi_id=upi,
        status=PayoutStatus.PENDING,
        requested_at=now,
    )
    await payout.insert()
    logger.info("Astrologer {} requested payout of {} paise ({})", astrologer_user_id, amount_paise, payout_method)
    return payout


async def list_payouts_for_astrologer(
    astrologer_user_id: PydanticObjectId, limit: int = 50
) -> list[AstrologerPayout]:
    return (
        await AstrologerPayout.find({"astrologer_user_id": astrologer_user_id})
        .sort([("created_at", -1)])
        .limit(limit)
        .to_list()
    )


async def list_all_payouts_for_admin(
    status: PayoutStatus | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    q: dict[str, Any] = {}
    if status:
        q["status"] = status

    payouts = (
        await AstrologerPayout.find(q)
        .sort([("created_at", -1)])
        .limit(limit)
        .to_list()
    )

    astrologer_ids = [p.astrologer_id for p in payouts]
    astrologers = await Astrologer.find({"_id": {"$in": astrologer_ids}}).to_list()
    astro_map = {a.id: a.display_name for a in astrologers}

    out = []
    for p in payouts:
        d = p.model_dump()
        d["id"] = str(p.id)
        d["astrologer_id"] = str(p.astrologer_id)
        d["astrologer_name"] = astro_map.get(p.astrologer_id, "Astrologer")
        out.append(d)
    return out


async def settle_payout(
    payout_id: PydanticObjectId,
    admin_user_id: PydanticObjectId,
    utr_number: str,
    admin_notes: str | None = None,
) -> AstrologerPayout:
    payout = await AstrologerPayout.get(payout_id)
    if not payout:
        raise NotFoundError("Payout request not found.", error_code="payout_not_found")
    if payout.status not in (PayoutStatus.PENDING, PayoutStatus.APPROVED):
        raise BadRequestError(f"Cannot settle payout with status '{payout.status}'.", error_code="invalid_payout_status")

    now = datetime.now(UTC)
    payout.status = PayoutStatus.SETTLED
    payout.utr_number = utr_number.strip()
    payout.admin_notes = admin_notes.strip() if admin_notes else None
    payout.settled_at = now
    payout.settled_by = admin_user_id
    await payout.save()
    logger.info("Admin {} settled payout {} with UTR {}", admin_user_id, payout_id, utr_number)
    return payout


async def reject_payout(
    payout_id: PydanticObjectId,
    admin_user_id: PydanticObjectId,
    rejection_reason: str,
) -> AstrologerPayout:
    payout = await AstrologerPayout.get(payout_id)
    if not payout:
        raise NotFoundError("Payout request not found.", error_code="payout_not_found")
    if payout.status not in (PayoutStatus.PENDING, PayoutStatus.APPROVED):
        raise BadRequestError(f"Cannot reject payout with status '{payout.status}'.", error_code="invalid_payout_status")

    now = datetime.now(UTC)
    payout.status = PayoutStatus.REJECTED
    payout.rejection_reason = rejection_reason.strip()
    payout.rejected_at = now
    payout.rejected_by = admin_user_id
    await payout.save()
    logger.info("Admin {} rejected payout {}: {}", admin_user_id, payout_id, rejection_reason)
    return payout
