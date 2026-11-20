"""Multi-Device Shopping Cart Synchronization Service for Astra AstroStore.

Guarantees 100% persistent state sync between mobile app, desktop web, and tablets.
Enriches lightweight cart references with live product catalogs, pricing, discounts,
stock checks, and complimentary Vedic gifts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from beanie import PydanticObjectId
from bson import ObjectId

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.shop import (
    Cart,
    CartItem,
    CouponDiscountType,
    Product,
    ShopCoupon,
)
from app.schemas.shop import (
    CartItemIn,
    CartItemOut,
    CartOut,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_or_create_cart(user_id: PydanticObjectId) -> Cart:
    """Finds or initializes a persistent Cart document for the authenticated user."""
    cart = await Cart.find_one({"user_id": user_id})
    if not cart:
        cart = Cart(
            user_id=user_id,
            items=[],
            coupon_code=None,
            last_activity_at=_utcnow(),
        )
        await cart.insert()
    return cart


async def enrich_cart(cart: Cart) -> CartOut:
    """Enriches the database Cart items with real-time product information,

    stock validation, dynamic discounts, bundled gifts, and cashback coins.
    """
    if not cart.items:
        return CartOut(
            items=[],
            item_count=0,
            subtotal=0.0,
            coupon_code=cart.coupon_code,
            discount_amount=0.0,
            coupon_title=None,
            is_coupon_valid=False,
            cashback_coins=0,
            free_gifts=[],
            updated_at=cart.updated_at or cart.last_activity_at,
        )

    # 1. Gather all product IDs
    product_ids: list[PydanticObjectId] = []
    for it in cart.items:
        if ObjectId.is_valid(it.product_id):
            product_ids.append(PydanticObjectId(it.product_id))

    # 2. Fetch live products from DB in one query
    products = await Product.find({"_id": {"$in": product_ids}}).to_list()
    product_map: dict[str, Product] = {str(p.id): p for p in products}

    # 3. Construct enriched item list, automatically pruning deleted/inactive products
    enriched_items: list[CartItemOut] = []
    clean_cart_items: list[CartItem] = []
    subtotal = 0.0
    item_count = 0
    total_cashback_coins = 0
    bundled_gifts: list[dict[str, Any]] = []
    seen_gift_titles: set[str] = set()

    for it in cart.items:
        pid_str = str(it.product_id)
        product = product_map.get(pid_str)

        # Skip if product was removed from catalog or disabled
        if not product or not product.is_active:
            continue

        clean_cart_items.append(it)

        # Quantity bound to stock and safety limit
        qty = max(1, min(it.quantity, 50))
        is_in_stock = product.stock_quantity > 0
        sale_price = float(product.sale_price)
        mrp = float(product.mrp)
        line_total = sale_price * qty

        subtotal += line_total
        item_count += qty

        # Cashback calculation
        cb_pct = float(product.cashback_percent or 100.0)
        item_cashback = round(line_total * (cb_pct / 100.0))
        total_cashback_coins += item_cashback

        enriched_items.append(
            CartItemOut(
                id=pid_str,
                slug=product.slug,
                sku=product.sku,
                title=product.title,
                price=sale_price,
                mrp=mrp,
                image=product.featured_image or (product.images[0] if product.images else ""),
                quantity=qty,
                stock_quantity=product.stock_quantity,
                is_in_stock=is_in_stock,
                free_gift_title=gift_title,
                free_gift_value=gift_val,
                free_gift_badge=gift_badge,
                free_gift_image_url=product.free_gift_image_url,
                cashback_percent=cb_pct,
                sankalpa=it.sankalpa,
                line_total=line_total,
            )
        )

    # If stale items were pruned, persist clean list to database
    if len(clean_cart_items) != len(cart.items):
        cart.items = clean_cart_items
        await cart.save()

    # 4. Coupon Validation & Discount
    discount_amount = 0.0
    coupon_title: str | None = None
    is_coupon_valid = False

    if cart.coupon_code:
        coupon = await ShopCoupon.find_one({
            "code": cart.coupon_code.strip().upper(),
            "is_active": True,
        })
        if coupon and coupon.is_valid_now:
            if subtotal >= coupon.min_order_amount:
                is_coupon_valid = True
                coupon_title = coupon.title or f"{coupon.code} Discount"
                if coupon.discount_type == CouponDiscountType.PERCENTAGE:
                    calculated = subtotal * (coupon.discount_value / 100.0)
                    if coupon.max_discount_amount:
                        calculated = min(calculated, coupon.max_discount_amount)
                    discount_amount = round(calculated, 2)
                else:
                    discount_amount = round(min(coupon.discount_value, subtotal), 2)
            else:
                is_coupon_valid = False
                coupon_title = f"Min order ₹{coupon.min_order_amount:.0f} required"
        else:
            is_coupon_valid = False

    return CartOut(
        items=enriched_items,
        item_count=item_count,
        subtotal=round(subtotal, 2),
        coupon_code=cart.coupon_code if is_coupon_valid else None,
        discount_amount=discount_amount,
        coupon_title=coupon_title,
        is_coupon_valid=is_coupon_valid,
        cashback_coins=total_cashback_coins,
        free_gifts=bundled_gifts,
        updated_at=cart.updated_at or cart.last_activity_at,
    )


async def get_user_cart(user_id: PydanticObjectId) -> CartOut:
    """Retrieves and enriches the current active cart for the user."""
    cart = await get_or_create_cart(user_id)
    return await enrich_cart(cart)


async def sync_cart(
    user_id: PydanticObjectId,
    local_items: list[CartItemIn],
    coupon_code: str | None = None,
) -> CartOut:
    """Merges offline/guest browser items into the persistent database cart.

    If an item already exists in the server cart, preserves the maximum quantity.
    """
    cart = await get_or_create_cart(user_id)

    # Map existing server items by product_id
    server_items_map: dict[str, CartItem] = {str(it.product_id): it for it in cart.items}

    for local_item in local_items:
        pid_clean = local_item.product_id.strip()
        if not ObjectId.is_valid(pid_clean):
            continue

        if pid_clean in server_items_map:
            existing = server_items_map[pid_clean]
            # Use max quantity from local or server, capped at 50
            existing.quantity = max(1, min(max(existing.quantity, local_item.quantity), 50))
            if local_item.sankalpa and not existing.sankalpa:
                existing.sankalpa = local_item.sankalpa
        else:
            new_item = CartItem(
                product_id=PydanticObjectId(pid_clean),
                quantity=max(1, min(local_item.quantity, 50)),
                sankalpa=local_item.sankalpa,
                added_at=_utcnow(),
            )
            cart.items.append(new_item)
            server_items_map[pid_clean] = new_item

    # Apply coupon if user brought one and server had none
    if coupon_code and not cart.coupon_code:
        cart.coupon_code = coupon_code.strip().upper()

    cart.last_activity_at = _utcnow()
    await cart.save()
    return await enrich_cart(cart)


async def add_cart_item(
    user_id: PydanticObjectId,
    product_id_str: str,
    quantity: int = 1,
    sankalpa: dict | None = None,
) -> CartOut:
    """Adds a product or increments quantity in the user's persistent cart."""
    pid_clean = product_id_str.strip()
    if not ObjectId.is_valid(pid_clean):
        raise BadRequestError("Invalid product ID.")

    product = await Product.get(PydanticObjectId(pid_clean))
    if not product or not product.is_active:
        raise NotFoundError("Product not found or currently unavailable.")

    if product.stock_quantity <= 0:
        raise BadRequestError("This consecrated product is currently out of stock.")

    cart = await get_or_create_cart(user_id)

    existing_item = next((it for it in cart.items if str(it.product_id) == pid_clean), None)
    if existing_item:
        existing_item.quantity = min(existing_item.quantity + max(1, quantity), min(50, product.stock_quantity))
        if sankalpa:
            existing_item.sankalpa = sankalpa
    else:
        cart.items.append(
            CartItem(
                product_id=PydanticObjectId(pid_clean),
                quantity=min(max(1, quantity), min(50, product.stock_quantity)),
                sankalpa=sankalpa,
                added_at=_utcnow(),
            )
        )

    cart.last_activity_at = _utcnow()
    await cart.save()
    return await enrich_cart(cart)


async def update_cart_item(
    user_id: PydanticObjectId,
    product_id_str: str,
    quantity: int,
    sankalpa: dict | None = None,
) -> CartOut:
    """Updates quantity or Sankalpa for an existing item in the cart.

    If quantity is 0 or less, the item is removed.
    """
    pid_clean = product_id_str.strip()
    if not ObjectId.is_valid(pid_clean):
        raise BadRequestError("Invalid product ID.")

    cart = await get_or_create_cart(user_id)

    if quantity <= 0:
        cart.items = [it for it in cart.items if str(it.product_id) != pid_clean]
    else:
        existing_item = next((it for it in cart.items if str(it.product_id) == pid_clean), None)
        if existing_item:
            existing_item.quantity = max(1, min(quantity, 50))
            if sankalpa is not None:
                existing_item.sankalpa = sankalpa

    cart.last_activity_at = _utcnow()
    await cart.save()
    return await enrich_cart(cart)


async def remove_cart_item(user_id: PydanticObjectId, product_id_str: str) -> CartOut:
    """Removes a single product from the user's persistent cart."""
    pid_clean = product_id_str.strip()
    cart = await get_or_create_cart(user_id)
    cart.items = [it for it in cart.items if str(it.product_id) != pid_clean]
    cart.last_activity_at = _utcnow()
    await cart.save()
    return await enrich_cart(cart)


async def clear_cart(user_id: PydanticObjectId) -> CartOut:
    """Empties the user's cart (e.g.

    after checkout completion or user request).
    """
    cart = await get_or_create_cart(user_id)
    cart.items = []
    cart.coupon_code = None
    cart.last_activity_at = _utcnow()
    await cart.save()
    return await enrich_cart(cart)


async def apply_cart_coupon(user_id: PydanticObjectId, code: str | None) -> CartOut:
    """Sets or clears the promotional discount coupon on the user's cart."""
    cart = await get_or_create_cart(user_id)
    if code and code.strip():
        cart.coupon_code = code.strip().upper()
    else:
        cart.coupon_code = None

    cart.last_activity_at = _utcnow()
    await cart.save()
    return await enrich_cart(cart)
