"""Astra AstroStore Order & Checkout Service with 100% Wallet Cashback Accounting.

Production-grade rules:
1. Strict Idempotency: All wallet credits and debits use deterministic idempotency keys.
2. Anti-Abuse: Cashback is only credited upon verified payment success (never for unverified or pending COD).
3. Reversal Integrity: Order cancellations automatically claw back credited cashback coins to prevent cash-out gaming.
4. Concurrency Safe: Atomic inventory management prevents stock over-allocation.
"""

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from typing import Any
import asyncio

from beanie import PydanticObjectId
from loguru import logger

from app.core.config import settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, ServiceUnavailableError
from app.models.cms import CMS_KEY_SHOP, ShopCMS
from app.models.enums import (
    ShopOrderStatus,
    ShopPaymentMethod,
    ShopPaymentStatus,
    ShopRefundStatus,
    TransactionDirection,
    TransactionReason,
)
from app.models.shop import (
    OrderItemSnapshot,
    OrderStatusLog,
    Product,
    SankalpaDetails,
    ShippingAddressSnapshot,
    ShopCoupon,
    ShopOrder,
)
from app.models.wallet import TransactionRef, Wallet
from app.schemas.shop import (
    PincodeCheckResponse,
    ShopAdminCompleteRefundPayload,
    ShopAdminOrderUpdate,
    ShopCheckoutRequest,
    ShopCheckoutResponse,
    ShopCouponOut,
    ShopCouponRecommendationOut,
    ShopCouponRecommendationsResponse,
    ShopCouponValidateResponse,
    ShopOrderItemOut,
    ShopOrderListResponse,
    ShopOrderOut,
    ShopOrderStatusLogOut,
    ShopPaymentVerifyRequest,
)
from app.services import wallet as wallet_service
from app.services.payments import _razorpay
from app.services.settings import get_coins_per_rupee


class ShopOrderService:
    """Manages the full lifecycle of physical remedy orders, payments, and 100% wallet cashback."""

    @staticmethod
    def _order_to_out(order: ShopOrder) -> ShopOrderOut:
        items_out = [
            ShopOrderItemOut(
                product_id=str(it.product_id),
                title=it.title,
                slug=it.slug,
                sku=it.sku,
                category_name=it.category_name,
                featured_image=it.featured_image,
                unit_mrp=it.unit_mrp,
                unit_sale_price=it.unit_sale_price,
                quantity=it.quantity,
                line_total=it.line_total,
                free_gift_title=it.free_gift_title,
                free_gift_value=it.free_gift_value,
                lab_certified=it.lab_certified,
                lab_certificate_number=it.lab_certificate_number,
            )
            for it in order.items
        ]

        history_out = [
            ShopOrderStatusLogOut(
                status=h.status,
                changed_at=h.changed_at,
                notes=h.notes,
            )
            for h in (order.status_history or [])
        ]

        return ShopOrderOut(
            id=str(order.id),
            order_number=order.order_number,
            user_id=str(order.user_id),
            user_email=order.user_email,
            user_phone=order.user_phone,
            shipping_address=order.shipping_address.model_dump(),
            items=items_out,
            sankalpa=order.sankalpa.model_dump() if order.sankalpa else None,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            coupon_code=order.coupon_code,
            shipping_fee=order.shipping_fee,
            tax_amount=order.tax_amount,
            grand_total=order.grand_total,
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            order_status=order.order_status,
            razorpay_order_id=order.razorpay_order_id,
            razorpay_payment_id=order.razorpay_payment_id,
            cashback_percent=order.cashback_percent,
            cashback_coins_eligible=order.cashback_coins_eligible,
            cashback_coins_credited=order.cashback_coins_credited,
            cashback_credited_at=order.cashback_credited_at,
            free_gifts=order.free_gifts or [],
            courier_partner=order.courier_partner,
            tracking_id=order.tracking_id,
            tracking_url=order.tracking_url,
            estimated_delivery_date=order.estimated_delivery_date,
            delivered_at=order.delivered_at,
            consecration_certificate_url=order.consecration_certificate_url,
            stock_reserved_until=order.stock_reserved_until,
            is_stock_restored=order.is_stock_restored,
            rto_at=order.rto_at,
            rto_reason=order.rto_reason,
            cancellation_reason=order.cancellation_reason,
            refund_status=order.refund_status,
            refund_amount=order.refund_amount,
            refund_upi_id=order.refund_upi_id,
            refund_qr_code_url=order.refund_qr_code_url,
            refund_requested_at=order.refund_requested_at,
            refund_sla_days=order.refund_sla_days,
            refund_completed_at=order.refund_completed_at,
            refund_transaction_id=order.refund_transaction_id,
            refund_notes=order.refund_notes,
            status_history=history_out,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    @classmethod
    async def is_cod_blacklisted(
        cls,
        phone: str | None,
        user_id: PydanticObjectId | None = None,
    ) -> tuple[bool, str | None]:
        """Anti-Abuse Engine: Checks if customer phone or account is blacklisted from COD due to past RTO shipments."""
        cms = None
        try:
            cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
        except Exception:
            cms = None

        max_rto = getattr(cms, "cod_max_rto_allowed", 2) or 2
        blacklisted_phones = getattr(cms, "cod_blacklisted_phones", []) or []

        clean_phone = phone.strip() if phone else ""
        digits_only = "".join(filter(str.isdigit, clean_phone))
        last10 = digits_only[-10:] if len(digits_only) >= 10 else digits_only

        # Check explicit admin blacklist
        if last10 and any(last10 in b for b in blacklisted_phones):
            return (
                True,
                "পূর্ববর্তী পার্সেল ডেলিভারি সংক্রান্ত জটিলতার কারণে আপনার নম্বরে ক্যাশ অন ডেলিভারি (COD) সাময়িকভাবে স্থগিত রয়েছে। অনুগ্রহ করে প্রিপেইড মোডে (UPI, কার্ড) অর্ডার সম্পন্ন করুন।",
            )

        # Count previous RTO orders for this phone or account
        query_conditions = []
        if last10:
            query_conditions.append({"shipping_address.phone_number": {"$regex": f"{last10}$"}})
            query_conditions.append({"user_phone": {"$regex": f"{last10}$"}})
        if user_id:
            query_conditions.append({"user_id": user_id})

        if not query_conditions:
            return False, None

        rto_count = 0
        try:
            rto_count = await ShopOrder.find(
                {
                    "order_status": ShopOrderStatus.RTO,
                    "payment_method": ShopPaymentMethod.COD,
                    "$or": query_conditions,
                }
            ).count()
        except Exception:
            rto_count = 0

        if rto_count >= max_rto:
            # Auto-blacklist this phone if not yet registered in CMS blacklist
            if clean_phone and cms and clean_phone not in blacklisted_phones:
                await ShopCMS.get_pymongo_collection().update_one(
                    {"_id": cms.id},
                    {"$addToSet": {"cod_blacklisted_phones": clean_phone}},
                )
            return (
                True,
                f"আপনার নম্বর থেকে পূর্ববর্তী {rto_count}টি ক্যাশ অন ডেলিভারি (COD) পার্সেল গ্রহণ না করার (RTO) কারণে COD সুবিধা স্থগিত করা হয়েছে। অনুগ্রহ করে প্রিপেইড পেমেন্ট (UPI, কার্ড, নেট ব্যাংকিং) বেছে নিন।",
            )

        return False, None

    @classmethod
    async def create_order(
        cls,
        user_id: PydanticObjectId,
        user_email: str,
        user_phone: str,
        payload: ShopCheckoutRequest,
    ) -> ShopCheckoutResponse:
        """Processes cart items, validates stock, attaches free gifts, calculates 100% cashback, and initiates order."""
        if not payload.items:
            raise BadRequestError("Cart is empty.")

        # 1. Fetch Store CMS Settings
        cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
        cashback_enabled = getattr(cms, "cashback_enabled", True) if cms else True
        default_cashback_pct = getattr(cms, "cashback_percent", 100) if cms else 100
        free_shipping_threshold = getattr(cms, "free_shipping_threshold", 499.0) if cms else 499.0
        standard_shipping_fee = getattr(cms, "standard_shipping_fee", 70.0) if cms else 70.0
        cod_enabled = getattr(cms, "cod_enabled", True) if cms else True
        cod_extra_charge = getattr(cms, "cod_extra_charge", 0.0) if cms else 0.0

        if payload.payment_method == ShopPaymentMethod.WALLET:
            raise BadRequestError(
                "ই-কমার্স সামগ্রী ওয়ালেটের কয়েন দিয়ে ক্রয় করা সম্ভব নয়। অনুগ্রহ করে অনলাইন (Razorpay) বা ক্যাশ অন ডেলিভারি (COD)-এর মাধ্যমে পেমেন্ট সম্পন্ন করুন।",
                error_code="wallet_payment_not_allowed",
            )

        if payload.payment_method == ShopPaymentMethod.COD:
            if not cod_enabled:
                raise BadRequestError(
                    "ক্যাশ অন ডেলিভারি (COD) বর্তমানে সাময়িকভাবে বন্ধ আছে। অনুগ্রহ করে অনলাইন পেমেন্ট বেছে নিন।",
                    error_code="cod_disabled",
                )
            # Anti-Abuse Check: Verify that user or recipient phone is not blacklisted from COD due to past RTO shipments
            recipient_phone = payload.shipping_address.phone_number or user_phone
            is_blacklisted, bl_msg = await cls.is_cod_blacklisted(phone=recipient_phone, user_id=user_id)
            if is_blacklisted:
                raise BadRequestError(bl_msg, error_code="cod_blacklisted")

        # 2. Validate Items & Inventory
        item_snapshots: list[OrderItemSnapshot] = []
        bundled_gifts: list[dict] = []
        subtotal = 0.0

        for line in payload.items:
            product = None
            try:
                prod_oid = PydanticObjectId(line.product_id)
                product = await Product.get(prod_oid)
            except Exception:
                pass

            if not product:
                product = await Product.find_one(Product.slug == line.product_id)

            if not product or getattr(product, "is_deleted", False) or not getattr(product, "is_active", True):
                raise NotFoundError(f"Product '{line.product_id}' is no longer available.")

            stock_left = getattr(product, "stock_quantity", 0)
            if stock_left < line.quantity:
                raise BadRequestError(
                    f"Insufficient inventory for '{product.title}'. Only {stock_left} remaining."
                )

            line_total = round(product.sale_price * line.quantity, 2)
            subtotal += line_total

            # Product-specific bundled free gift or default
            gift_title = product.free_gift_title or (getattr(cms, "free_gift_default_title", "Raw Selenite Plate") if cms else "Raw Selenite Plate")
            gift_val = product.free_gift_value or (getattr(cms, "free_gift_default_value", 729.0) if cms else 729.0)
            gift_badge = product.free_gift_badge or (getattr(cms, "free_gift_default_badge", "FREE Raw Selenite Plate worth ₹729") if cms else "FREE Raw Selenite Plate worth ₹729")

            # Attach free gift record
            if gift_title and not any(g.get("title") == gift_title for g in bundled_gifts):
                bundled_gifts.append({
                    "title": gift_title,
                    "value": gift_val,
                    "badge": gift_badge,
                    "image_url": getattr(product, "free_gift_image_url", None) or (getattr(cms, "free_gift_default_image_url", None) if cms else None),
                    "reason": f"Complimentary gift with {product.title}",
                })

            item_snapshots.append(
                OrderItemSnapshot(
                    product_id=product.id,
                    title=product.title,
                    slug=product.slug,
                    sku=product.sku,
                    category_name=getattr(product, "category_slug", None) or "remedy",
                    featured_image=product.featured_image,
                    unit_mrp=product.mrp,
                    unit_sale_price=product.sale_price,
                    quantity=line.quantity,
                    line_total=line_total,
                    weight_grams=getattr(product, "weight_grams", 100.0) or 100.0,
                    free_gift_title=gift_title,
                    free_gift_value=gift_val,
                    lab_certified=getattr(product, "lab_certified", True),
                    lab_certificate_number=getattr(product, "lab_certificate_number", None),
                )
            )

        # 3. Coupons & Discounts (Strict Enforcement)
        discount_amount = 0.0
        applied_coupon = None
        coupon_to_increment: ShopCoupon | None = None
        if payload.coupon_code and payload.coupon_code.strip():
            code = payload.coupon_code.strip().upper()
            coupon = await ShopCoupon.find_one(ShopCoupon.code == code)
            if not coupon:
                raise BadRequestError(
                    f"কুপন কোড '{code}' সঠিক নয়।",
                    error_code="coupon_invalid",
                )

            user_orders_count = 0
            user_coupon_usage = 0
            if user_id:
                user_orders_count = await ShopOrder.find(
                    ShopOrder.user_id == user_id,
                    ShopOrder.order_status != ShopOrderStatus.CANCELLED,
                ).count()
                user_coupon_usage = await ShopOrder.find(
                    ShopOrder.user_id == user_id,
                    ShopOrder.coupon_code == code,
                    ShopOrder.order_status != ShopOrderStatus.CANCELLED,
                ).count()

            is_app, reason = coupon.check_applicability(subtotal, user_orders_count, user_coupon_usage)
            if not is_app:
                raise BadRequestError(
                    reason or f"কুপন '{code}' এই অর্ডারে প্রযোজ্য নয়।",
                    error_code="coupon_not_applicable",
                )

            discount_amount = coupon.calculate_discount(subtotal)
            applied_coupon = code
            coupon_to_increment = coupon

        # 4. Shipping Calculation
        net_order_value = max(0.0, subtotal - discount_amount)
        shipping_fee = 0.0 if net_order_value >= free_shipping_threshold else standard_shipping_fee
        cod_fee = cod_extra_charge if payload.payment_method == ShopPaymentMethod.COD else 0.0

        grand_total = round(net_order_value + shipping_fee + cod_fee, 2)

        # 5. 100% Wallet Cashback Calculation
        effective_cashback_pct = default_cashback_pct if cashback_enabled else 0
        coins_per_rupee = await get_coins_per_rupee()
        cashback_coins_eligible = 0

        # Prepaid orders (Razorpay or Wallet) are instantly eligible for 100% cashback
        if cashback_enabled and effective_cashback_pct > 0:
            cashback_coins_eligible = int(round(grand_total * (effective_cashback_pct / 100.0) * coins_per_rupee))

        # 6. ATOMIC INVENTORY RESERVATION (Strict Zero-Overselling Guard - Loophole 3)
        # We execute MongoDB conditional atomic decrement BEFORE touching payments, wallets, or external gateways.
        # This completely guarantees that two concurrent users clicking "Pay" at the same microsecond
        # will NEVER oversell inventory or drive stock below zero.
        reserved_items: list[tuple[PydanticObjectId, int]] = []
        for it in item_snapshots:
            res = await Product.get_pymongo_collection().update_one(
                {
                    "_id": it.product_id,
                    "stock_quantity": {"$gte": it.quantity},
                    "is_active": True,
                    "is_deleted": False,
                },
                {"$inc": {"stock_quantity": -it.quantity}},
            )
            if res.modified_count == 0:
                # Concurrent race conflict: another devotee just purchased the remaining available stock!
                # Atomically rollback any items already decremented in this checkout
                for rollback_id, rollback_qty in reserved_items:
                    await Product.get_pymongo_collection().update_one(
                        {"_id": rollback_id},
                        {"$inc": {"stock_quantity": rollback_qty}},
                    )
                raise BadRequestError(
                    f"দুঃখিত, '{it.title}' এর পর্যাপ্ত স্টক এই মুহূর্তে অবশিষ্ট নেই। অন্য একজন ভক্ত এইমাত্র শেষ সামগ্রীটি সংগ্রহ করেছেন। অনুগ্রহ করে কার্টটি পুনরায় যাচাই করুন।",
                    error_code="insufficient_stock",
                )
            reserved_items.append((it.product_id, it.quantity))

        # 7. TRANSACTIONAL EXECUTION (Payment Gateway / Wallet Charging / Order Insertion)
        # Wrapped in a fail-safe try-except block: if ANY payment gateway or database insert step fails,
        # the reserved inventory is immediately and safely returned to the active warehouse catalog!
        try:
            today_str = datetime.now(UTC).strftime("%Y%m%d")
            order_number = f"ASTRA-ORD-{today_str}-{secrets.token_hex(3).upper()}"

            shipping_snap = ShippingAddressSnapshot(
                recipient_name=payload.shipping_address.recipient_name,
                phone_number=payload.shipping_address.phone_number,
                alternate_phone=payload.shipping_address.alternate_phone,
                address_line1=payload.shipping_address.address_line1,
                address_line2=payload.shipping_address.address_line2,
                landmark=payload.shipping_address.landmark,
                city=payload.shipping_address.city,
                state=payload.shipping_address.state,
                pincode=payload.shipping_address.pincode,
                address_type=payload.shipping_address.address_type,
            )

            sankalpa_snap = None
            if payload.sankalpa and payload.sankalpa.devotee_name:
                sankalpa_snap = SankalpaDetails(
                    devotee_name=payload.sankalpa.devotee_name.strip(),
                    gotra=(payload.sankalpa.gotra or "Kashyap").strip(),
                    date_of_birth=payload.sankalpa.date_of_birth,
                    birth_time=payload.sankalpa.birth_time,
                    birth_place=payload.sankalpa.birth_place,
                    special_prayer_wish=payload.sankalpa.special_prayer_wish,
                )

            reservation_minutes = getattr(cms, "checkout_reservation_minutes", 20) if cms else 20
            stock_reserved_until = (
                datetime.now(UTC) + timedelta(minutes=reservation_minutes)
                if payload.payment_method == ShopPaymentMethod.RAZORPAY
                else None
            )

            order = ShopOrder(
                order_number=order_number,
                user_id=user_id,
                user_email=user_email,
                user_phone=user_phone or payload.shipping_address.phone_number,
                shipping_address=shipping_snap,
                items=item_snapshots,
                sankalpa=sankalpa_snap,
                subtotal=subtotal,
                discount_amount=discount_amount,
                coupon_code=applied_coupon,
                shipping_fee=shipping_fee,
                tax_amount=0.0,
                grand_total=grand_total,
                payment_method=payload.payment_method,
                payment_status=ShopPaymentStatus.PENDING,
                order_status=ShopOrderStatus.PLACED,
                cashback_percent=effective_cashback_pct,
                cashback_coins_eligible=cashback_coins_eligible,
                cashback_coins_credited=0,
                free_gifts=bundled_gifts,
                stock_reserved_until=stock_reserved_until,
                is_stock_restored=False,
                estimated_delivery_date=datetime.now(UTC) + timedelta(days=4),
                status_history=[
                    OrderStatusLog(
                        status=ShopOrderStatus.PLACED,
                        notes=(
                            f"Inventory atomically reserved for {reservation_minutes} minutes pending Razorpay online payment."
                            if payload.payment_method == ShopPaymentMethod.RAZORPAY
                            else "Order placed by devotee. Consecration and packing queued."
                        ),
                    )
                ],
            )

            # Payment Handling: Razorpay, Wallet, or COD
            razorpay_order_id = None
            razorpay_key_id = None

            if payload.payment_method == ShopPaymentMethod.RAZORPAY:
                if settings.razorpay_configured:
                    amount_paise = int(round(grand_total * 100))
                    try:
                        rzp_resp = await asyncio.to_thread(
                            _razorpay().order.create,
                            {
                                "amount": amount_paise,
                                "currency": "INR",
                                "receipt": order_number,
                                "notes": {
                                    "order_number": order_number,
                                    "user_id": str(user_id),
                                    "store": "Astra AstroStore",
                                },
                            },
                        )
                        razorpay_order_id = rzp_resp.get("id")
                        razorpay_key_id = settings.RAZORPAY_KEY_ID
                        order.razorpay_order_id = razorpay_order_id
                    except Exception as exc:
                        logger.opt(exception=exc).error(
                            "Razorpay order creation failed for shop order {}: {}", order_number, exc
                        )
                        raise ServiceUnavailableError(
                            "Payment gateway could not initiate transaction. Please try again or choose Cash on Delivery.",
                            error_code="razorpay_order_failed",
                        ) from exc
                else:
                    # Mock order id for test/sandbox
                    razorpay_order_id = f"order_mock_{secrets.token_hex(8)}"
                    razorpay_key_id = "rzp_test_mock"
                    order.razorpay_order_id = razorpay_order_id

            elif payload.payment_method == ShopPaymentMethod.WALLET:
                raise BadRequestError(
                    "ই-কমার্স সামগ্রী ওয়ালেটের কয়েন দিয়ে ক্রয় করা সম্ভব নয়। অনুগ্রহ করে অনলাইন (Razorpay) বা ক্যাশ অন ডেলিভারি (COD)-এর মাধ্যমে পেমেন্ট সম্পন্ন করুন।",
                    error_code="wallet_payment_not_allowed",
                )

            elif payload.payment_method == ShopPaymentMethod.COD:
                order.payment_status = ShopPaymentStatus.PENDING
                order.order_status = ShopOrderStatus.PLACED

            await order.insert()
            if coupon_to_increment:
                await ShopCoupon.get_pymongo_collection().update_one(
                    {"_id": coupon_to_increment.id},
                    {"$inc": {"usage_count": 1}},
                )

            # Clear persistent server-side cart for user upon successful order placement (COD only)
            # For prepaid (Razorpay), the cart is safely retained until payment is confirmed to prevent empty cart errors
            if payload.payment_method == ShopPaymentMethod.COD:
                try:
                    from app.services import shop_cart_service
                    await shop_cart_service.clear_cart(user_id)
                except Exception as cart_err:
                    logger.warning("Non-blocking: Failed to auto-clear server cart for user {}: {}", user_id, cart_err)
            logger.info(
                "Created Shop Order '{}' (grand_total=₹{}, payment_method={}, cashback_coins={})",
                order.order_number,
                order.grand_total,
                order.payment_method,
                order.cashback_coins_eligible,
            )
        except Exception as exc:
            # Critical Transaction Rollback: if Razorpay, Wallet, or DB insert throws any error,
            # release all reserved items back into the active stock collection immediately!
            for rollback_id, rollback_qty in reserved_items:
                await Product.get_pymongo_collection().update_one(
                    {"_id": rollback_id},
                    {"$inc": {"stock_quantity": rollback_qty}},
                )
            logger.error(
                "Checkout failed for user {}. Safely rolled back {} reserved item(s). Error: {}",
                user_id,
                len(reserved_items),
                exc,
            )
            raise exc

        return ShopCheckoutResponse(
            order_id=str(order.id),
            order_number=order.order_number,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            shipping_fee=order.shipping_fee,
            grand_total=order.grand_total,
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            order_status=order.order_status,
            razorpay_order_id=razorpay_order_id,
            razorpay_key_id=razorpay_key_id,
            cashback_percent=effective_cashback_pct,
            cashback_coins_eligible=cashback_coins_eligible,
            free_gifts=bundled_gifts,
        )

    @classmethod
    async def verify_razorpay_payment(
        cls,
        user_id: PydanticObjectId,
        payload: ShopPaymentVerifyRequest,
    ) -> ShopOrderOut:
        """Verifies Razorpay HMAC signature, marks order paid, and executes 100% Wallet Cashback."""
        order = None
        if payload.razorpay_order_id:
            order = await ShopOrder.find_one(ShopOrder.razorpay_order_id == payload.razorpay_order_id)
        if not order and payload.order_id:
            try:
                order = await ShopOrder.get(PydanticObjectId(payload.order_id))
            except Exception:
                pass

        if not order:
            raise NotFoundError("Order not found for verification.")

        if order.user_id != user_id:
            raise ForbiddenError("You are not authorized to verify this order.")

        # Idempotency check: if order was already confirmed/paid (e.g. by webhook)
        if order.payment_status == ShopPaymentStatus.PAID:
            logger.info("Shop order '{}' already verified/paid. Returning idempotent output.", order.order_number)
            return cls._order_to_out(order)

        # Signature check
        if settings.razorpay_configured:
            rzp_order_id = payload.razorpay_order_id or order.razorpay_order_id
            if not rzp_order_id:
                raise BadRequestError("Razorpay order ID is missing for verification.")

            expected = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                f"{rzp_order_id}|{payload.razorpay_payment_id}".encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, payload.razorpay_signature):
                logger.warning("Invalid Razorpay signature for shop order '{}'", order.order_number)
                raise BadRequestError("Payment verification failed: invalid signature.")

        # Handle late payment if order was swept by TTL background cleaner
        if order.order_status == ShopOrderStatus.EXPIRED or order.is_stock_restored:
            reclaimed_items: list[tuple[PydanticObjectId, int]] = []
            can_reclaim_all = True
            for it in order.items:
                res = await Product.get_pymongo_collection().update_one(
                    {"_id": it.product_id, "stock_quantity": {"$gte": it.quantity}, "is_active": True},
                    {"$inc": {"stock_quantity": -it.quantity}},
                )
                if res.modified_count == 0:
                    can_reclaim_all = False
                    break
                reclaimed_items.append((it.product_id, it.quantity))

            if can_reclaim_all:
                order.is_stock_restored = False
                order.stock_restored_at = None
                order.stock_reserved_until = None
                order.order_status = ShopOrderStatus.CONFIRMED
                order.status_history.append(
                    OrderStatusLog(
                        status=ShopOrderStatus.CONFIRMED,
                        notes="Late payment captured after timeout. Inventory successfully re-reserved for devotee.",
                    )
                )
            else:
                for r_id, r_qty in reclaimed_items:
                    await Product.get_pymongo_collection().update_one(
                        {"_id": r_id},
                        {"$inc": {"stock_quantity": r_qty}},
                    )
                order.payment_status = ShopPaymentStatus.PAID
                order.paid_at = datetime.now(UTC)
                order.razorpay_payment_id = payload.razorpay_payment_id
                order.razorpay_signature = payload.razorpay_signature
                order.order_status = ShopOrderStatus.CANCELLED
                order.cancellation_reason = "Payment captured after checkout timeout, but stock is now exhausted. Auto-refund required."
                order.status_history.append(
                    OrderStatusLog(
                        status=ShopOrderStatus.CANCELLED,
                        notes=order.cancellation_reason,
                    )
                )
                await order.save()
                return cls._order_to_out(order)
        else:
            order.stock_reserved_until = None

        # Mark Paid if not already
        if order.payment_status != ShopPaymentStatus.PAID:
            order.payment_status = ShopPaymentStatus.PAID
            order.paid_at = datetime.now(UTC)
            order.razorpay_payment_id = payload.razorpay_payment_id
            order.razorpay_signature = payload.razorpay_signature
            order.order_status = ShopOrderStatus.CONFIRMED
            order.status_history.append(
                OrderStatusLog(
                    status=ShopOrderStatus.CONFIRMED,
                    notes=f"Payment verified successfully (ID: {payload.razorpay_payment_id}). Queued for Varanasi consecration.",
                )
            )

        # -------------------------------------------------------------
        # EXECUTE 100% WALLET CASHBACK (Idempotent & Anti-Abuse)
        # -------------------------------------------------------------
        cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
        cashback_timing = getattr(cms, "cashback_credit_timing", "on_delivery") if cms else "on_delivery"

        if cashback_timing == "on_payment":
            # Instant Credit Mode
            if order.cashback_coins_eligible > 0 and order.cashback_coins_credited == 0:
                cb_idempotency = f"shop_cashback_{order.order_number}"
                try:
                    txn, was_created = await wallet_service.credit(
                        user_id=order.user_id,
                        amount_coins=order.cashback_coins_eligible,
                        reason=TransactionReason.SHOP_CASHBACK,
                        idempotency_key=cb_idempotency,
                        ref=TransactionRef(
                            razorpay_payment_id=payload.razorpay_payment_id,
                            shop_order_id=order.id,
                            shop_order_number=order.order_number,
                        ),
                        note=f"100% Cashback for Sacred Remedy Order #{order.order_number}",
                    )
                    order.cashback_coins_credited = order.cashback_coins_eligible
                    order.cashback_credited_at = datetime.now(UTC)
                    order.cashback_transaction_id = txn.id
                    logger.info(
                        "Credited {} cashback coins to user {} for order {}",
                        order.cashback_coins_eligible,
                        order.user_id,
                        order.order_number,
                    )
                except Exception as e:
                    logger.error("Failed to credit cashback for order {}: {}", order.order_number, e)
        else:
            # Safe Anti-Fraud Mode ('on_delivery'):
            # Cashback coins remain eligible and are credited automatically once parcel is DELIVERED.
            order.status_history.append(
                OrderStatusLog(
                    status=ShopOrderStatus.CONFIRMED,
                    notes=f"100% Cashback benefit of {order.cashback_coins_eligible} coins reserved. Coins will be credited to wallet upon safe doorstep delivery.",
                )
            )

        await order.save()

        # Clear persistent server-side cart for user upon confirmed payment
        try:
            from app.services import shop_cart_service
            await shop_cart_service.clear_cart(order.user_id)
        except Exception as cart_err:
            logger.warning("Non-blocking: Failed to auto-clear server cart for user {}: {}", order.user_id, cart_err)

        return cls._order_to_out(order)

    @classmethod
    async def confirm_order_from_webhook(
        cls,
        order: ShopOrder,
        payment_id: str,
        payment: dict[str, Any],
    ) -> str:
        """Called by Razorpay webhook when payment is captured for a ShopOrder."""
        if order.payment_status == ShopPaymentStatus.PAID:
            return "already_paid"

        # Check late payment/expiration
        if order.order_status == ShopOrderStatus.EXPIRED or order.is_stock_restored:
            reclaimed_items: list[tuple[PydanticObjectId, int]] = []
            can_reclaim_all = True
            for it in order.items:
                res = await Product.get_pymongo_collection().update_one(
                    {"_id": it.product_id, "stock_quantity": {"$gte": it.quantity}, "is_active": True},
                    {"$inc": {"stock_quantity": -it.quantity}},
                )
                if res.modified_count == 0:
                    can_reclaim_all = False
                    break
                reclaimed_items.append((it.product_id, it.quantity))

            if can_reclaim_all:
                order.is_stock_restored = False
                order.stock_restored_at = None
                order.stock_reserved_until = None
                order.order_status = ShopOrderStatus.CONFIRMED
            else:
                for r_id, r_qty in reclaimed_items:
                    await Product.get_pymongo_collection().update_one(
                        {"_id": r_id},
                        {"$inc": {"stock_quantity": r_qty}},
                    )
                order.payment_status = ShopPaymentStatus.PAID
                order.paid_at = datetime.now(UTC)
                order.razorpay_payment_id = payment_id
                order.order_status = ShopOrderStatus.CANCELLED
                order.cancellation_reason = "Payment captured after checkout timeout, but stock is now exhausted. Auto-refund required."
                order.status_history.append(
                    OrderStatusLog(
                        status=ShopOrderStatus.CANCELLED,
                        notes=order.cancellation_reason,
                    )
                )
                await order.save()
                return "stock_exhausted_cancelled"

        order.stock_reserved_until = None
        order.payment_status = ShopPaymentStatus.PAID
        order.paid_at = datetime.now(UTC)
        order.razorpay_payment_id = payment_id
        order.order_status = ShopOrderStatus.CONFIRMED
        order.status_history.append(
            OrderStatusLog(
                status=ShopOrderStatus.CONFIRMED,
                notes=f"Payment captured via webhook (ID: {payment_id}). Queued for Varanasi consecration.",
            )
        )

        cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
        cashback_timing = getattr(cms, "cashback_credit_timing", "on_delivery") if cms else "on_delivery"

        if cashback_timing == "on_payment":
            if order.cashback_coins_eligible > 0 and order.cashback_coins_credited == 0:
                cb_idempotency = f"shop_cashback_{order.order_number}"
                try:
                    txn, was_created = await wallet_service.credit(
                        user_id=order.user_id,
                        amount_coins=order.cashback_coins_eligible,
                        reason=TransactionReason.SHOP_CASHBACK,
                        idempotency_key=cb_idempotency,
                        ref=TransactionRef(
                            razorpay_payment_id=payment_id,
                            shop_order_id=order.id,
                            shop_order_number=order.order_number,
                        ),
                        note=f"100% Cashback for Sacred Remedy Order #{order.order_number}",
                    )
                    order.cashback_coins_credited = order.cashback_coins_eligible
                    order.cashback_credited_at = datetime.now(UTC)
                    order.cashback_transaction_id = txn.id
                except Exception as e:
                    logger.error("Failed to credit cashback for order {}: {}", order.order_number, e)
        else:
            order.status_history.append(
                OrderStatusLog(
                    status=ShopOrderStatus.CONFIRMED,
                    notes=f"100% Cashback benefit of {order.cashback_coins_eligible} coins reserved. Coins will be credited to wallet upon safe doorstep delivery.",
                )
            )

        await order.save()

        # Clear server cart
        try:
            from app.services import shop_cart_service
            await shop_cart_service.clear_cart(order.user_id)
        except Exception:
            pass

        return "confirmed"

    @classmethod
    async def handle_payment_failure_from_webhook(
        cls,
        order: ShopOrder,
        payment: dict[str, Any],
    ) -> str:
        """Called by Razorpay webhook when payment.failed is received for a ShopOrder."""
        if order.payment_status == ShopPaymentStatus.PAID:
            return "already_paid_ignore_failure"

        # Restore reserved stock immediately if not yet restored
        if not order.is_stock_restored:
            for it in order.items:
                await Product.get_pymongo_collection().update_one(
                    {"_id": it.product_id},
                    {"$inc": {"stock_quantity": it.quantity}},
                )
            order.is_stock_restored = True
            order.stock_restored_at = datetime.now(UTC)

        order.stock_reserved_until = None
        order.payment_status = ShopPaymentStatus.FAILED
        order.order_status = ShopOrderStatus.CANCELLED
        failure_msg = payment.get("error_description") or payment.get("error_reason") or "Payment failed on payment gateway"
        order.cancellation_reason = f"Payment failed on gateway: {failure_msg}"
        order.status_history.append(
            OrderStatusLog(
                status=ShopOrderStatus.CANCELLED,
                notes=f"Payment failed: {failure_msg}. Reserved inventory released back to catalog.",
            )
        )
        if order.coupon_code:
            await ShopCoupon.get_pymongo_collection().update_one(
                {"code": order.coupon_code, "usage_count": {"$gt": 0}},
                {"$inc": {"usage_count": -1}},
            )
        await order.save()
        return "marked_failed"

    @classmethod
    async def abort_checkout(
        cls,
        order_id: str,
        user_id: PydanticObjectId,
    ) -> bool:
        """Atomically aborts an unpaid Razorpay checkout attempt when devotee closes the payment modal,

        immediately releases the reserved inventory stock, cancels the draft order, and keeps
        devotee cart intact for retry or COD.
        """
        order = None
        try:
            oid = PydanticObjectId(order_id)
            order = await ShopOrder.get(oid)
        except Exception:
            pass

        if not order:
            order = await ShopOrder.find_one(ShopOrder.order_number == order_id)

        if not order:
            logger.warning("Abort checkout: order '{}' not found", order_id)
            return False

        if order.user_id != user_id:
            raise ForbiddenError("Not authorized to abort this checkout.")

        # If already paid, do not abort
        if order.payment_status == ShopPaymentStatus.PAID:
            logger.info("Cannot abort already paid order '{}'", order.order_number)
            return False

        # If already cancelled or expired, ensure stock is restored and return
        if order.order_status in (ShopOrderStatus.CANCELLED, ShopOrderStatus.EXPIRED):
            if not order.is_stock_restored:
                for it in order.items:
                    await Product.get_pymongo_collection().update_one(
                        {"_id": it.product_id},
                        {"$inc": {"stock_quantity": it.quantity}},
                    )
                order.is_stock_restored = True
                order.stock_restored_at = datetime.now(UTC)
                await order.save()
            return True

        # Atomically restore inventory stock to active warehouse catalog
        if not order.is_stock_restored:
            for it in order.items:
                await Product.get_pymongo_collection().update_one(
                    {"_id": it.product_id},
                    {"$inc": {"stock_quantity": it.quantity}},
                )
            order.is_stock_restored = True
            order.stock_restored_at = datetime.now(UTC)

        order.stock_reserved_until = None
        order.order_status = ShopOrderStatus.CANCELLED
        order.payment_status = ShopPaymentStatus.FAILED
        order.cancellation_reason = "Devotee cancelled payment at checkout modal."
        order.status_history.append(
            OrderStatusLog(
                status=ShopOrderStatus.CANCELLED,
                notes="Devotee closed Razorpay payment modal without completing transaction. Reserved stock released back to inventory.",
                updated_by=user_id,
            )
        )

        # Revert coupon usage count if applied
        if order.coupon_code:
            await ShopCoupon.get_pymongo_collection().update_one(
                {"code": order.coupon_code, "usage_count": {"$gt": 0}},
                {"$inc": {"usage_count": -1}},
            )

        await order.save()
        logger.info("Successfully aborted unpaid checkout for order '{}', stock restored.", order.order_number)
        return True

    @classmethod
    async def cancel_order(
        cls,
        order_id: str,
        user_id: PydanticObjectId | None = None,
        reason: str | None = None,
        upi_id: str | None = None,
        qr_code_url: str | None = None,
        qr_code_public_id: str | None = None,
    ) -> ShopOrderOut:
        """Cancels an un-shipped order, restores stock, claws back credited cashback coins, and initiates UPI/QR refund request."""
        try:
            oid = PydanticObjectId(order_id)
        except Exception:
            raise BadRequestError("Invalid order ID format.")

        order = await ShopOrder.get(oid)
        if not order:
            raise NotFoundError("Order not found.")

        if user_id and order.user_id != user_id:
            raise ForbiddenError("Not authorized to cancel this order.")

        if order.order_status in (ShopOrderStatus.SHIPPED, ShopOrderStatus.OUT_FOR_DELIVERY, ShopOrderStatus.DELIVERED, ShopOrderStatus.RTO):
            raise BadRequestError(
                "কাশী বিশ্বনাথ থেকে সিদ্ধ ও প্রাণ-প্রতিষ্ঠিত পবিত্র বৈদিক সামগ্রী একবার ডিসপ্যাচ বা ডেলিভারি হওয়ার পর কোনো রিটার্ন নেওয়া হয় না।",
                error_code="return_not_allowed",
            )

        if order.order_status == ShopOrderStatus.CANCELLED:
            return cls._order_to_out(order)

        # Policy checks for customer-initiated cancellation
        cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
        if user_id:
            allow_cancel = getattr(cms, "allow_user_cancellation", True) if cms else True
            if not allow_cancel:
                raise BadRequestError(
                    "অর্ডারটি সরাসরি অনলাইন থেকে বাতিল করার সুবিধা সাময়িকভাবে বন্ধ রয়েছে। সহায়তার জন্য অনুগ্রহ করে কাস্টমার সাপোর্টে যোগাযোগ করুন।",
                    error_code="cancellation_disabled",
                )
            grace_hours = getattr(cms, "cancellation_grace_hours", 24) if cms else 24
            order_age_hours = (datetime.now(UTC) - order.created_at).total_seconds() / 3600.0
            if order_age_hours > grace_hours:
                raise BadRequestError(
                    f"অর্ডার বাতিলের অনুমোদিত সময়সীমা ({grace_hours} ঘণ্টা) উত্তীর্ণ হয়েছে। অর্ডারটি কাশীর ঘাটে সংকল্প ব্যাচে প্রস্তুত হচ্ছে। সহায়তার জন্য কাস্টমার সাপোর্টে যোগাযোগ করুন।",
                    error_code="cancellation_window_expired",
                )

        # ---------------------------------------------------------------------
        # ANTI-FRAUD COIN PROTECTION: Check if user already spent their cashback coins
        # ---------------------------------------------------------------------
        if order.cashback_coins_credited > 0 and not order.cashback_reversed_at:
            wallet = await Wallet.find_one(Wallet.user_id == order.user_id)
            blocked = getattr(wallet, "blocked_coins", 0) or 0
            available_coins = max(0, (wallet.balance_coins if wallet else 0) - blocked)

            if available_coins < order.cashback_coins_credited:
                logger.warning(
                    "Anti-fraud blocked cancellation: User {} has already spent cashback coins for order {} (Balance: {}, Required: {})",
                    order.user_id,
                    order.order_number,
                    available_coins,
                    order.cashback_coins_credited,
                )
                raise BadRequestError(
                    "এই অর্ডারের জন্য প্রাপ্ত ক্যাশব্যাক কয়েন ইতিমধ্যে জ্যোতিষী পরামর্শে ব্যবহার করা হয়েছে। তাই এই অর্ডারটি সরাসরি বাতিল করা সম্ভব নয়। বিশদ সহায়তার জন্য অনুগ্রহ করে কাস্টমার সাপোর্টে যোগাযোগ করুন।",
                    error_code="cashback_already_spent",
                )

            # User has sufficient coins -> Claw back the cashback
            rev_key = f"shop_cashback_rev_{order.order_number}"
            try:
                await wallet_service.debit(
                    user_id=order.user_id,
                    amount_coins=order.cashback_coins_credited,
                    reason=TransactionReason.SHOP_CASHBACK_REVERSAL,
                    idempotency_key=rev_key,
                    ref=TransactionRef(shop_order_id=order.id, shop_order_number=order.order_number),
                    note=f"Reversal of cashback due to cancellation of Order #{order.order_number}",
                )
                order.cashback_reversed_at = datetime.now(UTC)
                logger.info("Reversed {} cashback coins for cancelled order {}", order.cashback_coins_credited, order.order_number)
            except Exception as e:
                logger.error("Error reversing cashback for cancelled order {}: {}", order.order_number, e)
                raise BadRequestError(f"অর্ডার বাতিলের সময় ক্যাশব্যাক কয়েন রিভার্স করা যায়নি: {str(e)}")

        # 1. Restore Stock atomically (if not already restored)
        if not order.is_stock_restored:
            for it in order.items:
                await Product.get_pymongo_collection().update_one(
                    {"_id": it.product_id},
                    {"$inc": {"stock_quantity": it.quantity}},
                )
            order.is_stock_restored = True
            order.stock_restored_at = datetime.now(UTC)

        order.order_status = ShopOrderStatus.CANCELLED
        order.cancellation_reason = reason or ("Cancelled by customer" if user_id else "Cancelled by administrator")

        # Restore coupon usage count if applied
        if order.coupon_code:
            await ShopCoupon.get_pymongo_collection().update_one(
                {"code": order.coupon_code, "usage_count": {"$gt": 0}},
                {"$inc": {"usage_count": -1}},
            )

        # 2. Refund Lifecycle Assignment
        is_paid_order = order.payment_status == ShopPaymentStatus.PAID
        refund_sla = getattr(cms, "refund_sla_days", 3) if cms else 3

        if is_paid_order:
            if user_id and not (upi_id or qr_code_url):
                raise BadRequestError(
                    "অনলাইন পেমেন্টকৃত অর্ডারের টাকা রিফান্ডের জন্য আপনার UPI ID অথবা QR কোড প্রদান করা আবশ্যক।",
                    error_code="refund_upi_required",
                )
            order.refund_status = ShopRefundStatus.PENDING
            order.refund_amount = order.grand_total
            order.refund_upi_id = upi_id.strip() if upi_id else None
            order.refund_qr_code_url = qr_code_url
            order.refund_qr_code_public_id = qr_code_public_id
            order.refund_requested_at = datetime.now(UTC)
            order.refund_sla_days = refund_sla
            log_notes = f"Order cancelled. Refund of ₹{order.grand_total} requested to UPI: {order.refund_upi_id or 'via QR Code'}. Promised SLA: {refund_sla} business days."
        else:
            order.refund_status = ShopRefundStatus.NOT_APPLICABLE
            log_notes = f"Order cancelled. Reason: {order.cancellation_reason}."

        order.status_history.append(
            OrderStatusLog(
                status=ShopOrderStatus.CANCELLED,
                notes=log_notes,
                updated_by=user_id,
            )
        )
        await order.save()
        return cls._order_to_out(order)

    @classmethod
    async def complete_refund_by_admin(
        cls,
        order_id: str,
        admin_id: PydanticObjectId,
        payload: ShopAdminCompleteRefundPayload,
    ) -> ShopOrderOut:
        """Admin completes refund payout to customer's UPI, deletes uploaded QR from Cloudinary, and notifies devotee."""
        try:
            oid = PydanticObjectId(order_id)
        except Exception:
            raise BadRequestError("Invalid order ID format.")

        order = await ShopOrder.get(oid)
        if not order:
            raise NotFoundError("Order not found.")

        if order.order_status != ShopOrderStatus.CANCELLED:
            raise BadRequestError("কেবলমাত্র বাতিলকৃত (Cancelled) অর্ডারের রিফান্ড সম্পন্ন করা সম্ভব।")

        if order.refund_status == ShopRefundStatus.COMPLETED:
            return cls._order_to_out(order)

        order.refund_status = ShopRefundStatus.COMPLETED
        order.payment_status = ShopPaymentStatus.REFUNDED
        order.refund_completed_at = datetime.now(UTC)
        order.refund_transaction_id = payload.transaction_id.strip() if payload.transaction_id else None
        order.refund_notes = payload.notes

        order.status_history.append(
            OrderStatusLog(
                status=ShopOrderStatus.CANCELLED,
                notes=f"Refund of ₹{order.refund_amount or order.grand_total} completed by admin via UPI {order.refund_upi_id or 'QR'}. UTR/Ref: {order.refund_transaction_id or 'N/A'}.",
                updated_by=admin_id,
            )
        )

        # -------------------------------------------------------------
        # Clean up Cloudinary QR Code storage to prevent orphaned assets
        # -------------------------------------------------------------
        if order.refund_qr_code_public_id:
            try:
                from app.services.storage import delete_file
                await delete_file(order.refund_qr_code_public_id, resource_type="image")
                logger.info("Deleted refund QR code asset '{}' from Cloudinary for order {}", order.refund_qr_code_public_id, order.order_number)
            except Exception as e:
                logger.warning("Could not delete refund QR public_id {}: {}", order.refund_qr_code_public_id, e)
        elif order.refund_qr_code_url:
            try:
                from app.services.storage import safe_delete_cloudinary_image
                await safe_delete_cloudinary_image(order.refund_qr_code_url)
                logger.info("Deleted refund QR code url from Cloudinary for order {}", order.order_number)
            except Exception as e:
                logger.warning("Could not delete refund QR url {}: {}", order.refund_qr_code_url, e)

        # Clear asset references after deletion
        order.refund_qr_code_url = None
        order.refund_qr_code_public_id = None

        await order.save()

        # Send official confirmation email to customer
        try:
            from app.services.email import send_shop_order_refund_email
            asyncio.create_task(
                send_shop_order_refund_email(
                    to=order.user_email,
                    order_number=order.order_number,
                    amount_inr=order.refund_amount or order.grand_total,
                    upi_id=order.refund_upi_id,
                    transaction_id=order.refund_transaction_id,
                    items_count=len(order.items),
                    recipient_name=order.shipping_address.recipient_name if order.shipping_address else None,
                )
            )
        except Exception as mail_err:
            logger.warning("Failed to dispatch refund email for order {}: {}", order.order_number, mail_err)

        return cls._order_to_out(order)

    @classmethod
    async def update_order_by_admin(
        cls,
        order_id: str,
        payload: ShopAdminOrderUpdate,
        admin_id: PydanticObjectId,
    ) -> ShopOrderOut:
        """Admin updates order status, tracking AWB, courier partner, and handles COD cashback on delivery."""
        try:
            oid = PydanticObjectId(order_id)
        except Exception:
            raise BadRequestError("Invalid order ID format.")

        order = await ShopOrder.get(oid)
        if not order:
            raise NotFoundError("Order not found.")

        old_status = order.order_status

        if payload.courier_partner is not None:
            order.courier_partner = payload.courier_partner
        if payload.tracking_id is not None:
            order.tracking_id = payload.tracking_id
        if payload.tracking_url is not None:
            order.tracking_url = payload.tracking_url
        if payload.estimated_delivery_date is not None:
            order.estimated_delivery_date = payload.estimated_delivery_date
        if payload.consecration_certificate_url is not None:
            order.consecration_certificate_url = payload.consecration_certificate_url

        if payload.order_status is not None and payload.order_status != old_status:
            order.order_status = payload.order_status
            order.status_history.append(
                OrderStatusLog(
                    status=payload.order_status,
                    notes=payload.notes or f"Status updated to {payload.order_status} by admin.",
                    updated_by=admin_id,
                )
            )

            # If order is cancelled, expired, or returned to origin (RTO), restore stock if not already restored
            if payload.order_status in (ShopOrderStatus.CANCELLED, ShopOrderStatus.EXPIRED, ShopOrderStatus.RTO) and not order.is_stock_restored:
                for it in order.items:
                    await Product.get_pymongo_collection().update_one(
                        {"_id": it.product_id},
                        {"$inc": {"stock_quantity": it.quantity}},
                    )
                order.is_stock_restored = True
                order.stock_restored_at = datetime.now(UTC)

            # Handle Courier Return to Origin (RTO) and auto-blacklist evaluation
            if payload.order_status == ShopOrderStatus.RTO:
                order.rto_at = datetime.now(UTC)
                order.rto_reason = payload.rto_reason or payload.notes or "Courier Return to Origin (Customer refused delivery / address unreachable)"
                # If COD order, evaluate phone for auto-blacklist
                clean_phone = order.shipping_address.phone_number or order.user_phone
                if clean_phone and order.payment_method == ShopPaymentMethod.COD:
                    cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
                    max_rto = getattr(cms, "cod_max_rto_allowed", 2) or 2
                    digits_only = "".join(filter(str.isdigit, clean_phone))
                    last10 = digits_only[-10:] if len(digits_only) >= 10 else digits_only
                    rto_count = await ShopOrder.find({
                        "order_status": ShopOrderStatus.RTO,
                        "payment_method": ShopPaymentMethod.COD,
                        "$or": [
                            {"shipping_address.phone_number": {"$regex": f"{last10}$"}},
                            {"user_phone": {"$regex": f"{last10}$"}},
                        ],
                    }).count()
                    if rto_count >= max_rto and cms:
                        await ShopCMS.get_pymongo_collection().update_one(
                            {"_id": cms.id},
                            {"$addToSet": {"cod_blacklisted_phones": clean_phone}},
                        )
                        logger.warning("Auto-blacklisted phone {} from COD after {} RTO deliveries", clean_phone, rto_count)

            # If COD order was successfully DELIVERED, mark PAID and credit 100% cashback!
            if payload.order_status == ShopOrderStatus.DELIVERED:
                order.delivered_at = datetime.now(UTC)
                if order.payment_method == ShopPaymentMethod.COD and order.payment_status != ShopPaymentStatus.PAID:
                    order.payment_status = ShopPaymentStatus.PAID
                    order.paid_at = datetime.now(UTC)

                # Credit cashback upon delivery for any order that hasn't received coins yet
                if order.cashback_coins_eligible > 0 and order.cashback_coins_credited == 0:
                    cb_key = f"shop_cashback_del_{order.order_number}"
                    try:
                        txn, _ = await wallet_service.credit(
                            user_id=order.user_id,
                            amount_coins=order.cashback_coins_eligible,
                            reason=TransactionReason.SHOP_CASHBACK,
                            idempotency_key=cb_key,
                            ref=TransactionRef(shop_order_id=order.id, shop_order_number=order.order_number),
                            note=f"100% Cashback for Delivered Remedy Order #{order.order_number}",
                        )
                        order.cashback_coins_credited = order.cashback_coins_eligible
                        order.cashback_credited_at = datetime.now(UTC)
                        order.cashback_transaction_id = txn.id
                        order.status_history.append(
                            OrderStatusLog(
                                status=ShopOrderStatus.DELIVERED,
                                notes=f"Credited {order.cashback_coins_eligible} cashback coins to user wallet upon verified delivery.",
                            )
                        )
                        logger.info("Successfully credited {} delivery cashback coins for order {}", order.cashback_coins_eligible, order.order_number)
                    except Exception as e:
                        logger.error("Failed to credit cashback on delivery for {}: {}", order.order_number, e)

        await order.save()
        return cls._order_to_out(order)

    @classmethod
    async def get_user_orders(
        cls,
        user_id: PydanticObjectId,
        page: int = 1,
        limit: int = 20,
    ) -> ShopOrderListResponse:
        """Lists orders placed by a devotee.

        Only includes confirmed orders: either successfully paid prepaid orders (Razorpay)
        or valid Cash on Delivery (COD) orders. Unpaid abandoned checkouts are strictly excluded.
        """
        skip = (page - 1) * limit
        query = ShopOrder.find(
            ShopOrder.user_id == user_id,
            {
                "$or": [
                    {"payment_status": ShopPaymentStatus.PAID},
                    {"payment_method": ShopPaymentMethod.COD},
                ]
            },
        )
        total = await query.count()
        orders = await query.sort("-created_at").skip(skip).limit(limit).to_list()
        pages = (total + limit - 1) // limit if total > 0 else 1

        return ShopOrderListResponse(
            items=[cls._order_to_out(o) for o in orders],
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

    @classmethod
    async def get_order_by_number_or_id(
        cls,
        order_key: str,
        user_id: PydanticObjectId | None = None,
    ) -> ShopOrderOut:
        """Retrieves single order with security ownership check."""
        order = await ShopOrder.find_one(ShopOrder.order_number == order_key)
        if not order:
            try:
                order = await ShopOrder.get(PydanticObjectId(order_key))
            except Exception:
                pass

        if not order:
            raise NotFoundError("Order not found.")

        if user_id and order.user_id != user_id:
            raise ForbiddenError("You are not authorized to view this order.")

        return cls._order_to_out(order)

    @classmethod
    async def list_admin_orders(
        cls,
        status: str | None = None,
        payment_status: ShopPaymentStatus | None = None,
        refund_status: ShopRefundStatus | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> ShopOrderListResponse:
        """Admin order management with filtering by status and search."""
        skip = (page - 1) * limit
        filters: list[Any] = []

        if status == "abandoned":
            # Specific view for abandoned or cancelled unpaid Razorpay checkouts
            filters.append(ShopOrder.payment_method == ShopPaymentMethod.RAZORPAY)
            filters.append(ShopOrder.payment_status != ShopPaymentStatus.PAID)
            filters.append({
                "$or": [
                    {"order_status": {"$in": [ShopOrderStatus.CANCELLED, ShopOrderStatus.EXPIRED, ShopOrderStatus.PLACED]}},
                    {"payment_status": {"$in": [ShopPaymentStatus.PENDING, ShopPaymentStatus.FAILED, ShopPaymentStatus.EXPIRED]}},
                ]
            })
        elif status == ShopOrderStatus.PLACED or status == "placed":
            # Real placed orders only: either confirmed COD, or paid
            filters.append(ShopOrder.order_status == ShopOrderStatus.PLACED)
            filters.append({
                "$or": [
                    {"payment_status": ShopPaymentStatus.PAID},
                    {"payment_method": ShopPaymentMethod.COD},
                ]
            })
        elif status:
            filters.append(ShopOrder.order_status == status)
        else:
            # Default "all" tab: show legitimate orders (PAID or COD), exclude phantom unpaid checkouts
            filters.append({
                "$or": [
                    {"payment_status": ShopPaymentStatus.PAID},
                    {"payment_method": ShopPaymentMethod.COD},
                ]
            })

        if payment_status:
            filters.append(ShopOrder.payment_status == payment_status)
        if refund_status:
            filters.append(ShopOrder.refund_status == refund_status)
        if search and search.strip():
            term = search.strip()
            filters.append({
                "$or": [
                    {"order_number": {"$regex": term, "$options": "i"}},
                    {"user_email": {"$regex": term, "$options": "i"}},
                    {"user_phone": {"$regex": term, "$options": "i"}},
                    {"shipping_address.recipient_name": {"$regex": term, "$options": "i"}},
                    {"sankalpa.devotee_name": {"$regex": term, "$options": "i"}},
                ]
            })

        query = ShopOrder.find(*filters) if filters else ShopOrder.find_all()
        total = await query.count()
        orders = await query.sort("-created_at").skip(skip).limit(limit).to_list()
        pages = (total + limit - 1) // limit if total > 0 else 1

        return ShopOrderListResponse(
            items=[cls._order_to_out(o) for o in orders],
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )

    @classmethod
    async def check_pincode(
        cls,
        pincode: str,
        phone: str | None = None,
        user_id: PydanticObjectId | None = None,
    ) -> PincodeCheckResponse:
        """Fast Indian delivery serviceability and COD validator with anti-abuse blacklist check."""
        clean = pincode.strip()
        if not clean.isdigit() or len(clean) != 6:
            raise BadRequestError("Pincode must be a 6-digit numeric postal code.")

        store_cod_enabled = True
        try:
            cms = await ShopCMS.find_one({"$or": [{"key": CMS_KEY_SHOP}, {"key": "shop_cms"}]})
            if cms:
                store_cod_enabled = getattr(cms, "cod_enabled", True)
        except Exception:
            pass

        is_cod_avail = store_cod_enabled
        cod_disabled_reason = None

        if store_cod_enabled and (phone or user_id):
            try:
                is_blacklisted, bl_reason = await cls.is_cod_blacklisted(phone=phone, user_id=user_id)
                if is_blacklisted:
                    is_cod_avail = False
                    cod_disabled_reason = bl_reason
            except Exception:
                pass
        elif not store_cod_enabled:
            cod_disabled_reason = "ক্যাশ অন ডেলিভারি (COD) বর্তমানে পুরো স্টোরে বন্ধ রয়েছে।"

        prefix = clean[:2]
        state_map = {
            "11": ("New Delhi", "Delhi"),
            "12": ("Gurugram / Faridabad", "Haryana"),
            "13": ("Ambala / Karnal", "Haryana"),
            "14": ("Ludhiana / Jalandhar", "Punjab"),
            "16": ("Chandigarh", "Chandigarh"),
            "17": ("Shimla / Dharamshala", "Himachal Pradesh"),
            "18": ("Jammu", "Jammu & Kashmir"),
            "20": ("Aligarh / Meerut", "Uttar Pradesh"),
            "21": ("Varanasi / Prayagraj", "Uttar Pradesh"),
            "22": ("Lucknow / Ayodhya", "Uttar Pradesh"),
            "24": ("Dehradun / Haridwar", "Uttarakhand"),
            "30": ("Jaipur", "Rajasthan"),
            "38": ("Ahmedabad", "Gujarat"),
            "39": ("Surat / Vadodara", "Gujarat"),
            "40": ("Mumbai", "Maharashtra"),
            "41": ("Pune", "Maharashtra"),
            "50": ("Hyderabad", "Telangana"),
            "56": ("Bengaluru", "Karnataka"),
            "60": ("Chennai", "Tamil Nadu"),
            "70": ("Kolkata", "West Bengal"),
            "71": ("Howrah / Hooghly", "West Bengal"),
            "72": ("Midnapore", "West Bengal"),
            "73": ("Siliguri / Darjeeling", "West Bengal"),
            "74": ("Nadia / North 24 Pgs", "West Bengal"),
            "78": ("Guwahati", "Assam"),
            "80": ("Patna", "Bihar"),
            "83": ("Ranchi / Jamshedpur", "Jharkhand"),
            "75": ("Bhubaneswar / Cuttack", "Odisha"),
        }

        city, state = state_map.get(prefix, ("Direct Courier Destination", "India"))
        est_days = 3 if prefix in ("70", "71", "21", "22", "11", "40", "56") else 4
        del_date = (datetime.now(UTC) + timedelta(days=est_days)).strftime("%A, %d %B")

        return PincodeCheckResponse(
            pincode=clean,
            city=city,
            state=state,
            is_serviceable=True,
            cod_available=is_cod_avail,
            cod_disabled_reason=cod_disabled_reason,
            estimated_delivery_days=est_days,
            estimated_delivery_date=del_date,
        )

    @classmethod
    async def validate_coupon(
        cls,
        code: str,
        subtotal: float,
        user_id: PydanticObjectId | None = None,
    ) -> ShopCouponValidateResponse:
        """Validates a coupon code against current cart subtotal and user eligibility."""
        clean_code = code.strip().upper()
        if not clean_code:
            return ShopCouponValidateResponse(
                is_valid=False,
                code="",
                discount_amount=0.0,
                new_subtotal=subtotal,
                message="অনুগ্রহ করে একটি কুপন কোড প্রদান করুন।",
            )

        coupon = await ShopCoupon.find_one(ShopCoupon.code == clean_code)
        if not coupon:
            return ShopCouponValidateResponse(
                is_valid=False,
                code=clean_code,
                discount_amount=0.0,
                new_subtotal=subtotal,
                message=f"কুপন কোড '{clean_code}' পাওয়া যায়নি বা সঠিক নয়।",
            )

        user_orders_count = 0
        user_coupon_usage = 0
        if user_id:
            user_orders_count = await ShopOrder.find(
                ShopOrder.user_id == user_id,
                ShopOrder.order_status != ShopOrderStatus.CANCELLED,
            ).count()
            user_coupon_usage = await ShopOrder.find(
                ShopOrder.user_id == user_id,
                ShopOrder.coupon_code == clean_code,
                ShopOrder.order_status != ShopOrderStatus.CANCELLED,
            ).count()

        is_app, reason = coupon.check_applicability(subtotal, user_orders_count, user_coupon_usage)
        if not is_app:
            return ShopCouponValidateResponse(
                is_valid=False,
                code=clean_code,
                discount_amount=0.0,
                new_subtotal=subtotal,
                message=reason or "এই কুপনটি আপনার বর্তমান কার্টে প্রযোজ্য নয়।",
            )

        discount = coupon.calculate_discount(subtotal)
        new_subtotal = max(0.0, round(subtotal - discount, 2))

        from app.services.shop_admin import _coupon_to_out
        return ShopCouponValidateResponse(
            is_valid=True,
            code=clean_code,
            discount_amount=discount,
            new_subtotal=new_subtotal,
            message=f"কুপন '{clean_code}' সফলভাবে প্রয়োগ হয়েছে! আপনার ₹{discount:,.2f} সাশ্রয় হয়েছে।",
            coupon=_coupon_to_out(coupon),
        )

    @classmethod
    async def get_coupon_recommendations(
        cls,
        subtotal: float,
        user_id: PydanticObjectId | None = None,
    ) -> ShopCouponRecommendationsResponse:
        """Evaluates all active store coupons, calculates exact savings, and highlights the best offer."""
        from collections import Counter
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        coupons = await ShopCoupon.find(ShopCoupon.is_active == True).to_list()

        user_orders_count = 0
        user_coupon_counts: dict[str, int] = {}
        if user_id:
            user_orders = await ShopOrder.find(
                ShopOrder.user_id == user_id,
                ShopOrder.order_status != ShopOrderStatus.CANCELLED,
            ).to_list()
            user_orders_count = len(user_orders)
            user_coupon_counts = Counter(o.coupon_code for o in user_orders if o.coupon_code)

        candidates: list[ShopCouponRecommendationOut] = []
        for c in coupons:
            # Skip if out of temporal validity
            if c.expiry_date and now > c.expiry_date:
                continue
            if c.start_date and now < c.start_date:
                continue
            if c.usage_limit is not None and c.usage_count >= c.usage_limit:
                continue

            user_usage = user_coupon_counts.get(c.code, 0)
            is_app, reason = c.check_applicability(subtotal, user_orders_count, user_usage)
            discount = c.calculate_discount(subtotal) if is_app else 0.0

            candidates.append(
                ShopCouponRecommendationOut(
                    code=c.code,
                    title=c.title or c.code,
                    description=c.description,
                    discount_type=c.discount_type.value,
                    discount_value=c.discount_value,
                    min_order_amount=c.min_order_amount,
                    max_discount_amount=c.max_discount_amount,
                    discount_amount=discount,
                    is_applicable=is_app,
                    reason_if_inapplicable=reason,
                    is_best_offer=False,
                    is_first_order_deal=c.first_order_only,
                    expiry_date=c.expiry_date,
                )
            )

        # Smart Recommendation ranking:
        # 1. Applicable coupons sorted by discount_amount DESC
        # 2. Inapplicable coupons sorted by min_order_amount ASC
        applicable = [c for c in candidates if c.is_applicable and c.discount_amount > 0]
        inapplicable = [c for c in candidates if not c.is_applicable or c.discount_amount == 0]

        applicable.sort(key=lambda x: x.discount_amount, reverse=True)
        inapplicable.sort(key=lambda x: x.min_order_amount)

        best_coupon_code = None
        max_savings = 0.0

        if applicable:
            applicable[0].is_best_offer = True
            best_coupon_code = applicable[0].code
            max_savings = applicable[0].discount_amount

        all_items = applicable + inapplicable

        return ShopCouponRecommendationsResponse(
            items=all_items,
            best_coupon_code=best_coupon_code,
            max_savings=max_savings,
            user_orders_count=user_orders_count,
        )

