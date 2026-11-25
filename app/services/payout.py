"""Payout & Withdrawal service for Astrologers and Vedic Purohits.

Handles calculation of available withdrawable balance, payout requests,
validation against bank/UPI details, administrative settlement, email notifications,
and financial analytics.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from beanie import PydanticObjectId
from loguru import logger

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.astrologer import Astrologer
from app.models.earning import EarningEntry
from app.models.enums import PujaBookingStatus, PujaPaymentStatus
from app.models.payout import AstrologerPayout, PayoutMethod, PayoutStatus
from app.models.purohit import PujaBooking, Purohit
from app.models.user import User
from app.services.email import send_payout_settlement_email

MIN_PAYOUT_AMOUNT_PAISE = 50000  # ₹500 minimum withdrawal


async def get_astrologer_earnings_balance(
    astrologer_user_id: PydanticObjectId,
) -> dict[str, Any]:
    """Computes exact live balances: total earned, settled, pending, and withdrawable for Astrologer or Purohit."""
    astrologer = await Astrologer.find_one({"user_id": astrologer_user_id})
    purohit = await Purohit.find_one({"user_id": astrologer_user_id}) if not astrologer else None

    if not astrologer and not purohit:
        raise NotFoundError(
            "Astrologer or Purohit professional profile not found.",
            error_code="professional_profile_not_found",
        )

    beneficiary_type = "purohit" if purohit else "astrologer"
    display_name = purohit.display_name if purohit else astrologer.display_name
    profile = purohit if purohit else astrologer

    # 1. Total earned calculation
    if purohit:
        # Purohit earnings from paid & non-cancelled puja bookings
        earn_pipeline = [
            {
                "$match": {
                    "purohit_user_id": astrologer_user_id,
                    "payment_status": PujaPaymentStatus.PAID,
                    "status": {"$ne": PujaBookingStatus.CANCELLED},
                }
            },
            {"$group": {"_id": None, "total_inr": {"$sum": "$amount_inr"}}},
        ]
        earn_cursor = await PujaBooking.get_pymongo_collection().aggregate(earn_pipeline)
        earn_res = [r async for r in earn_cursor]
        total_earned = int(round(earn_res[0]["total_inr"] * 100)) if earn_res else 0
    else:
        # Astrologer earnings from EarningEntry ledger
        earn_pipeline = [
            {"$match": {"astrologer_user_id": astrologer_user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$earning_paise"}}},
        ]
        earn_cursor = await EarningEntry.get_pymongo_collection().aggregate(earn_pipeline)
        earn_res = [r async for r in earn_cursor]
        total_earned = earn_res[0]["total"] if earn_res else 0

    # 2. Total settled payouts
    settled_pipeline = [
        {"$match": {"astrologer_user_id": astrologer_user_id, "status": PayoutStatus.SETTLED}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_paise"}}},
    ]
    settled_cursor = await AstrologerPayout.get_pymongo_collection().aggregate(settled_pipeline)
    settled_res = [r async for r in settled_cursor]
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
    pending_cursor = await AstrologerPayout.get_pymongo_collection().aggregate(pending_pipeline)
    pending_res = [r async for r in pending_cursor]
    total_pending = pending_res[0]["total"] if pending_res else 0

    withdrawable = max(0, total_earned - total_settled - total_pending)

    bank = getattr(profile, "bank", None)
    has_bank = bool(
        bank
        and (
            (bank.account_number and bank.ifsc)
            or (bank.account_number_last4 and bank.ifsc)
            or bank.upi_id
            or bank.upi_qr_url
        )
    )

    return {
        "total_earned_paise": total_earned,
        "total_settled_paise": total_settled,
        "total_pending_paise": total_pending,
        "withdrawable_balance_paise": withdrawable,
        "min_payout_amount_paise": MIN_PAYOUT_AMOUNT_PAISE,
        "bank_name": getattr(bank, "bank_name", None),
        "account_holder_name": getattr(bank, "account_holder_name", None) or display_name,
        "account_number_last4": getattr(bank, "account_number_last4", None),
        "ifsc": getattr(bank, "ifsc", None),
        "upi_id": getattr(bank, "upi_id", None),
        "upi_qr_url": getattr(bank, "upi_qr_url", None),
        "upi_qr_public_id": getattr(bank, "upi_qr_public_id", None),
        "pan_card": getattr(bank, "pan_card", None),
        "has_bank_details": has_bank,
        "beneficiary_type": beneficiary_type,
        "beneficiary_name": display_name,
    }


async def request_payout(
    astrologer_user_id: PydanticObjectId,
    amount_paise: int,
    payout_method: PayoutMethod = PayoutMethod.BANK_TRANSFER,
    custom_details: dict[str, Any] | None = None,
) -> AstrologerPayout:
    """Submits a new withdrawal request after strict balance & account validation."""
    if amount_paise < MIN_PAYOUT_AMOUNT_PAISE:
        raise BadRequestError(
            f"Minimum withdrawal request is ₹{MIN_PAYOUT_AMOUNT_PAISE / 100:.2f} ({MIN_PAYOUT_AMOUNT_PAISE} paise).",
            error_code="min_payout_limit",
        )

    astrologer = await Astrologer.find_one({"user_id": astrologer_user_id})
    purohit = await Purohit.find_one({"user_id": astrologer_user_id}) if not astrologer else None

    if not astrologer and not purohit:
        raise NotFoundError("Professional profile not found.", error_code="professional_profile_not_found")

    beneficiary_type = "purohit" if purohit else "astrologer"
    profile = purohit if purohit else astrologer
    display_name = profile.display_name

    bal = await get_astrologer_earnings_balance(astrologer_user_id)
    withdrawable = bal["withdrawable_balance_paise"]

    if amount_paise > withdrawable:
        raise BadRequestError(
            f"Insufficient withdrawable balance. Available: ₹{withdrawable / 100:.2f}, Requested: ₹{amount_paise / 100:.2f}.",
            error_code="insufficient_withdrawable_balance",
        )

    bank = profile.bank
    custom = custom_details or {}

    b_name = custom.get("bank_name") or getattr(bank, "bank_name", None)
    holder_name = custom.get("account_holder_name") or getattr(bank, "account_holder_name", None) or display_name
    acc_num = custom.get("account_number") or getattr(bank, "account_number", None)
    ifsc = custom.get("ifsc") or getattr(bank, "ifsc", None)
    upi = custom.get("upi_id") or getattr(bank, "upi_id", None)
    qr_url = custom.get("upi_qr_url") or getattr(bank, "upi_qr_url", None)

    if payout_method == PayoutMethod.UPI:
        if (not upi or "@" not in upi) and not qr_url:
            raise BadRequestError(
                "A valid UPI ID (e.g. yourname@upi) or uploaded UPI QR code is required for UPI payout.",
                error_code="invalid_upi",
            )
    else:
        if not acc_num or not ifsc:
            if not getattr(bank, "account_number_last4", None) or not ifsc:
                raise BadRequestError(
                    "Bank account number and IFSC code are required for bank transfer.",
                    error_code="missing_bank_details",
                )

    acc_last4 = acc_num[-4:] if acc_num and len(acc_num) >= 4 else getattr(bank, "account_number_last4", None)
    acc_masked = f"••••••••{acc_last4}" if acc_last4 else None

    # Update bank details on profile if new details provided
    updated = False
    if custom.get("account_number"):
        bank.account_number = custom["account_number"].strip()
        bank.account_number_last4 = acc_last4
        updated = True
    if custom.get("ifsc"):
        bank.ifsc = custom["ifsc"].strip().upper()
        updated = True
    if custom.get("bank_name"):
        bank.bank_name = custom["bank_name"].strip()
        updated = True
    if custom.get("account_holder_name"):
        bank.account_holder_name = custom["account_holder_name"].strip()
        updated = True
    if custom.get("upi_id"):
        bank.upi_id = custom["upi_id"].strip()
        updated = True
    if custom.get("pan_card"):
        bank.pan_card = custom["pan_card"].strip().upper()
        updated = True

    if updated:
        await profile.save()

    now = datetime.now(UTC)
    tds_percent = 0.0
    tds_paise = round(amount_paise * (tds_percent / 100))
    net_payable = amount_paise - tds_paise

    payout = AstrologerPayout(
        beneficiary_type=beneficiary_type,
        astrologer_id=astrologer.id if astrologer else None,
        purohit_id=purohit.id if purohit else None,
        beneficiary_name=display_name,
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
        upi_qr_url=qr_url,
        status=PayoutStatus.PENDING,
        requested_at=now,
    )
    await payout.insert()
    logger.info(
        "{} {} requested payout of {} paise ({})",
        beneficiary_type.capitalize(),
        astrologer_user_id,
        amount_paise,
        payout_method,
    )
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
    status: PayoutStatus | None = None,
    beneficiary_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    q: dict[str, Any] = {}
    if status:
        q["status"] = status
    if beneficiary_type:
        q["beneficiary_type"] = beneficiary_type

    payouts = (
        await AstrologerPayout.find(q)
        .sort([("created_at", -1)])
        .limit(limit)
        .to_list()
    )

    astrologer_ids = [p.astrologer_id for p in payouts if p.astrologer_id]
    purohit_ids = [p.purohit_id for p in payouts if p.purohit_id]

    astrologers = await Astrologer.find({"_id": {"$in": astrologer_ids}}).to_list() if astrologer_ids else []
    astro_map = {a.id: (a.display_name, getattr(a.bank, "upi_qr_url", None)) for a in astrologers}

    purohits = await Purohit.find({"_id": {"$in": purohit_ids}}).to_list() if purohit_ids else []
    purohit_map = {p.id: (p.display_name, getattr(p.bank, "upi_qr_url", None)) for p in purohits}

    out = []
    for p in payouts:
        d = p.model_dump()
        d["id"] = str(p.id)
        d["astrologer_id"] = str(p.astrologer_id) if p.astrologer_id else None
        d["purohit_id"] = str(p.purohit_id) if p.purohit_id else None

        # Resolve live beneficiary name and latest QR code
        qr = p.upi_qr_url
        if p.beneficiary_type == "purohit" and p.purohit_id in purohit_map:
            name, pqr = purohit_map[p.purohit_id]
            d["beneficiary_name"] = name
            d["astrologer_name"] = name
            if not qr:
                qr = pqr
        elif p.astrologer_id in astro_map:
            name, aqr = astro_map[p.astrologer_id]
            d["beneficiary_name"] = name
            d["astrologer_name"] = name
            if not qr:
                qr = aqr

        d["upi_qr_url"] = qr
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

    # Automated live email notification to the beneficiary
    try:
        user = await User.get(payout.astrologer_user_id)
        if user and user.email:
            beneficiary_name = payout.beneficiary_name or user.full_name or "Partner"
            amount_inr = payout.amount_paise / 100.0
            asyncio.create_task(
                send_payout_settlement_email(
                    to=user.email,
                    beneficiary_name=beneficiary_name,
                    amount_inr=amount_inr,
                    utr_number=payout.utr_number,
                    payment_method=payout.payout_method,
                    beneficiary_type=payout.beneficiary_type,
                )
            )
            logger.info("Triggered settlement notification email to {}", user.email)
    except Exception as exc:
        logger.warning("Could not dispatch settlement email for payout {}: {}", payout_id, exc)

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


async def get_payout_analytics_for_admin() -> dict[str, Any]:
    """Computes comprehensive payout analytics for Admin dashboard."""
    pipeline = [
        {
            "$group": {
                "_id": {"status": "$status", "beneficiary_type": "$beneficiary_type"},
                "total_amount": {"$sum": "$amount_paise"},
                "count": {"$sum": 1},
            }
        }
    ]
    cursor = await AstrologerPayout.get_pymongo_collection().aggregate(pipeline)
    rows = [r async for r in cursor]

    total_volume = 0
    total_settled = 0
    total_pending = 0
    astro_settled = 0
    purohit_settled = 0
    pending_cnt = 0
    settled_cnt = 0
    rejected_cnt = 0

    for r in rows:
        st = r["_id"].get("status")
        btype = r["_id"].get("beneficiary_type") or "astrologer"
        amt = r.get("total_amount", 0)
        cnt = r.get("count", 0)

        total_volume += amt
        if st == PayoutStatus.SETTLED:
            total_settled += amt
            settled_cnt += cnt
            if btype == "purohit":
                purohit_settled += amt
            else:
                astro_settled += amt
        elif st in (PayoutStatus.PENDING, PayoutStatus.APPROVED):
            total_pending += amt
            pending_cnt += cnt
        elif st == PayoutStatus.REJECTED:
            rejected_cnt += cnt

    return {
        "total_payouts_volume_paise": total_volume,
        "total_settled_volume_paise": total_settled,
        "total_pending_volume_paise": total_pending,
        "astrologer_settled_volume_paise": astro_settled,
        "purohit_settled_volume_paise": purohit_settled,
        "pending_count": pending_cnt,
        "settled_count": settled_cnt,
        "rejected_count": rejected_cnt,
    }


async def get_beneficiary_breakdown_for_admin(user_id: PydanticObjectId) -> dict[str, Any]:
    """Returns granular earnings breakdown (consultations or pujas) for admin deep-dive inspection."""
    astrologer = await Astrologer.find_one({"user_id": user_id})
    purohit = await Purohit.find_one({"user_id": user_id}) if not astrologer else None

    if not astrologer and not purohit:
        raise NotFoundError("Beneficiary professional profile not found.")

    b_type = "purohit" if purohit else "astrologer"
    b_name = purohit.display_name if purohit else astrologer.display_name

    items = []
    if purohit:
        bookings = (
            await PujaBooking.find({"purohit_user_id": user_id})
            .sort([("created_at", -1)])
            .limit(50)
            .to_list()
        )
        for b in bookings:
            earned_paise = int(round(b.amount_inr * 100))
            items.append(
                {
                    "id": str(b.id),
                    "title": f"Puja: {b.puja_name}",
                    "service_type": "puja",
                    "user_name": b.user_name,
                    "duration_label": f"{b.puja_duration_minutes} mins (Gotra: {b.sankalpa_gotra})",
                    "gross_paise": earned_paise,
                    "earning_paise": earned_paise,
                    "created_at": b.created_at,
                    "status": str(b.status).upper(),
                }
            )
    else:
        entries = (
            await EarningEntry.find({"astrologer_user_id": user_id})
            .sort([("created_at", -1)])
            .limit(50)
            .to_list()
        )
        uids = [e.user_id for e in entries if e.user_id]
        users = await User.find({"_id": {"$in": uids}}).to_list() if uids else []
        umap = {u.id: u.full_name for u in users}

        for e in entries:
            items.append(
                {
                    "id": str(e.id),
                    "title": f"Consultation ({str(e.mode).capitalize()})",
                    "service_type": "consultation",
                    "user_name": umap.get(e.user_id, "Devotee"),
                    "duration_label": f"{e.minute_index} minute session",
                    "gross_paise": e.gross_paise,
                    "earning_paise": e.earning_paise,
                    "created_at": e.created_at,
                    "status": "CREDITED",
                }
            )

    bal = await get_astrologer_earnings_balance(user_id)
    return {
        "user_id": str(user_id),
        "beneficiary_name": b_name,
        "beneficiary_type": b_type,
        "total_earnings_paise": bal["total_earned_paise"],
        "pending_payout_paise": bal["total_pending_paise"],
        "settled_payout_paise": bal["total_settled_paise"],
        "items": items,
    }
