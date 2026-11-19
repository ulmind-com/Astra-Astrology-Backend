"""Printable PDF / HTML Invoice & Packing Slip Service for Physical Orders.

Supports:
1. Exact Flipkart/Amazon luxury invoice layout matching customer's golden lotus aesthetic.
2. Dynamic GST support:
   - If client adds GSTIN in Admin Dashboard: Renders "TAX INVOICE" with GSTIN, State Codes, and CGST/SGST/IGST breakdown.
   - If client has no GSTIN (current default): Renders legally compliant "BILL OF SUPPLY / RETAIL INVOICE" under Section 22/24 of CGST Act.
3. Automatically generates and persists unique `invoice_number` (e.g. DIVIN-INV-2026-A1B2C3).
4. Full breakdown of line items, bundled complimentary Vedic gifts, sankalpa gotra, coupon discounts, and shipping.
5. High-resolution standalone print-ready HTML with @media print A4 optimization and window.print() automation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.cms import CMS_KEY_SHOP, ShopCMS
from app.models.enums import ShopPaymentMethod, ShopPaymentStatus
from app.models.shop import ShopOrder
from app.schemas.shop import (
    InvoiceBuyerOut,
    InvoiceDataOut,
    InvoiceItemOut,
    InvoiceSellerOut,
)

logger = logging.getLogger("astra.shop.invoice_service")


def _format_inr(amount: float) -> str:
    return f"₹{amount:,.2f}".replace(".00", "")


async def get_or_create_invoice_data(
    order_key: str,
    user_id: PydanticObjectId | None = None,
    is_admin: bool = False,
) -> InvoiceDataOut:
    """Fetches order and constructs complete invoice data snapshot.
    Generates and persists invoice_number if not already created.
    """
    order = None
    if PydanticObjectId.is_valid(order_key):
        order = await ShopOrder.get(PydanticObjectId(order_key))
    if not order:
        order = await ShopOrder.find_one(ShopOrder.order_number == order_key)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Access control: only the order owner or admin can view the invoice
    if not is_admin:
        if not user_id or order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this invoice")

    # Fetch store CMS business & GST profile
    cms = await ShopCMS.find_one(ShopCMS.key == CMS_KEY_SHOP)
    if not cms:
        cms = ShopCMS(key=CMS_KEY_SHOP)

    # Generate official invoice number if missing
    if not order.invoice_number:
        prefix = getattr(cms, "invoice_prefix", "DIVIN-INV") or "DIVIN-INV"
        year = order.created_at.year
        clean_num = order.order_number.replace("ASTRA-ORD-", "").replace("DIVIN-ORD-", "")
        suffix = clean_num[-6:] if len(clean_num) >= 6 else str(order.id)[-6:]
        order.invoice_number = f"{prefix}-{year}-{suffix.upper()}"
        await order.save()

    # Determine GST Status
    company_gstin = getattr(cms, "company_gstin", None)
    is_tax_invoice = bool(company_gstin and company_gstin.strip())

    seller_state = getattr(cms, "company_state", "Uttar Pradesh")
    seller_state_code = getattr(cms, "company_state_code", "09")
    buyer_state = order.shipping_address.state or seller_state

    tax_rate_percent = 0.0
    cgst_amount = 0.0
    sgst_amount = 0.0
    igst_amount = 0.0
    tax_amount = 0.0

    if is_tax_invoice:
        invoice_type_label = "TAX INVOICE"
        tax_rate_percent = 3.0  # Standard Vedic gems/jewellery GST slab
        # Check Intra-state vs Inter-state supply
        is_intra_state = buyer_state.strip().lower() == seller_state.strip().lower()
        if is_intra_state:
            cgst_amount = round(order.subtotal * 0.015, 2)
            sgst_amount = round(order.subtotal * 0.015, 2)
            tax_amount = cgst_amount + sgst_amount
        else:
            igst_amount = round(order.subtotal * 0.03, 2)
            tax_amount = igst_amount
    else:
        invoice_type_label = "RETAIL INVOICE / BILL OF SUPPLY"
        tax_amount = 0.0

    seller = InvoiceSellerOut(
        legal_name=getattr(cms, "company_legal_name", "DivinLink Spiritual Technologies Pvt. Ltd."),
        trade_name=getattr(cms, "company_trade_name", "DivinLink / Astra AstroStore"),
        address=getattr(cms, "company_address", "Kashi Vishwanath Temple Corridor, Dashashwamedh Ghat, Varanasi, Uttar Pradesh - 221001, India"),
        state=seller_state,
        state_code=seller_state_code,
        phone=getattr(cms, "company_phone", "+91 91530 08182"),
        email=getattr(cms, "company_email", "support@divinlink.com"),
        website=getattr(cms, "company_website", "https://www.divinlink.com"),
        pan=getattr(cms, "company_pan", None),
        gstin=company_gstin if is_tax_invoice else None,
    )

    buyer = InvoiceBuyerOut(
        name=order.shipping_address.recipient_name,
        phone=order.shipping_address.phone_number,
        email=order.user_email,
        address_line1=order.shipping_address.address_line1,
        address_line2=order.shipping_address.address_line2,
        landmark=order.shipping_address.landmark,
        city=order.shipping_address.city,
        state=order.shipping_address.state,
        pincode=order.shipping_address.pincode,
        address_type=order.shipping_address.address_type,
        sankalpa_devotee_name=order.sankalpa.devotee_name if order.sankalpa else None,
        sankalpa_gotra=order.sankalpa.gotra if order.sankalpa else None,
    )

    items = [
        InvoiceItemOut(
            title=it.title,
            sku=it.sku,
            category_name=it.category_name,
            quantity=it.quantity,
            unit_mrp=it.unit_mrp,
            unit_sale_price=it.unit_sale_price,
            line_total=it.line_total,
            free_gift_title=it.free_gift_title,
        )
        for it in order.items
    ]

    payment_method_str = (
        "Razorpay Online Payment (UPI / Cards / NetBanking)"
        if order.payment_method == ShopPaymentMethod.RAZORPAY
        else "Cash on Delivery (COD)"
        if order.payment_method == ShopPaymentMethod.COD
        else "Astra Wallet"
    )

    payment_status_str = "PAID" if order.payment_status == ShopPaymentStatus.PAID else "PENDING_AT_DELIVERY" if order.payment_method == ShopPaymentMethod.COD else "PENDING"

    footer_notes = getattr(
        cms,
        "invoice_footer_notes",
        "Thank you for welcoming divine vibrations into your sacred home! May Lord Shiva and the Navagrahas bestow eternal peace, health, and prosperity.",
    )

    return InvoiceDataOut(
        invoice_number=order.invoice_number,
        invoice_date=order.created_at,
        order_number=order.order_number,
        order_date=order.created_at,
        is_tax_invoice=is_tax_invoice,
        invoice_type_label=invoice_type_label,
        seller=seller,
        buyer=buyer,
        payment_method=payment_method_str,
        payment_status=payment_status_str,
        payment_transaction_id=order.razorpay_payment_id,
        paid_at=order.paid_at,
        items=items,
        free_gifts=order.free_gifts or [],
        subtotal=order.subtotal,
        coupon_code=order.coupon_code,
        discount_amount=order.discount_amount,
        shipping_fee=order.shipping_fee,
        tax_amount=tax_amount,
        tax_rate_percent=tax_rate_percent,
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        igst_amount=igst_amount,
        grand_total=order.grand_total,
        footer_notes=footer_notes,
        support_phone=seller.phone,
        support_email=seller.email,
    )


def generate_invoice_html(invoice: InvoiceDataOut, auto_print: bool = False) -> str:
    """Generates clean, luxury, print-ready HTML matching the customer's design screenshot."""
    formatted_date = invoice.invoice_date.strftime("%d %b %Y")
    subtotal_str = f"₹{invoice.subtotal:,.2f}".replace(".00", "")
    discount_str = f"- ₹{invoice.discount_amount:,.2f}".replace(".00", "")
    shipping_str = "FREE" if invoice.shipping_fee == 0 else f"₹{invoice.shipping_fee:,.2f}".replace(".00", "")
    tax_str = f"₹{invoice.tax_amount:,.2f}".replace(".00", "") if invoice.is_tax_invoice else "₹0 (Exempt / Composite)"
    total_str = f"₹{invoice.grand_total:,.2f}".replace(".00", "")

    # Item rows HTML
    rows_html = ""
    for item in invoice.items:
        gift_badge = (
            f"<div style='font-size:10px;color:#92400e;margin-top:2px;'>🎁 Includes: {item.free_gift_title}</div>"
            if item.free_gift_title
            else ""
        )
        unit_price_str = f"₹{item.unit_sale_price:,.2f}".replace(".00", "")
        item_total_str = f"₹{item.line_total:,.2f}".replace(".00", "")

        rows_html += f"""
        <tr>
          <td style="padding:14px 12px;border-bottom:1px solid #f1ece4;vertical-align:top;">
            <div style="font-weight:600;color:#1c1917;font-size:13px;">{item.title}</div>
            <div style="font-size:10px;color:#78716c;margin-top:2px;">SKU: {item.sku} • {item.category_name} • Consecrated in Kashi</div>
            {gift_badge}
          </td>
          <td style="padding:14px 12px;border-bottom:1px solid #f1ece4;text-align:center;color:#44403c;font-size:13px;vertical-align:top;">
            {item.quantity}
          </td>
          <td style="padding:14px 12px;border-bottom:1px solid #f1ece4;text-align:right;color:#44403c;font-size:13px;vertical-align:top;">
            {unit_price_str}
          </td>
          <td style="padding:14px 12px;border-bottom:1px solid #f1ece4;text-align:right;font-weight:600;color:#1c1917;font-size:13px;vertical-align:top;">
            {item_total_str}
          </td>
        </tr>
        """

    # Add free gifts if present
    for gift in invoice.free_gifts:
        g_title = gift.get("title", "Complimentary Sacred Vedic Gift")
        g_val = gift.get("value", 729)
        rows_html += f"""
        <tr style="background-color:#fffdfa;">
          <td style="padding:12px;border-bottom:1px solid #f1ece4;vertical-align:top;">
            <div style="font-weight:600;color:#b45309;font-size:12px;">🎁 {g_title}</div>
            <div style="font-size:10px;color:#78716c;">Complimentary Blessing Gift with Remedy Order</div>
          </td>
          <td style="padding:12px;border-bottom:1px solid #f1ece4;text-align:center;color:#44403c;font-size:12px;vertical-align:top;">1</td>
          <td style="padding:12px;border-bottom:1px solid #f1ece4;text-align:right;color:#059669;font-weight:600;font-size:12px;vertical-align:top;">FREE (₹{g_val})</td>
          <td style="padding:12px;border-bottom:1px solid #f1ece4;text-align:right;color:#059669;font-weight:700;font-size:12px;vertical-align:top;">₹0</td>
        </tr>
        """

    # GST Details Block
    gst_info_html = ""
    if invoice.is_tax_invoice and invoice.seller.gstin:
        gst_info_html = f"""
        <div style="margin-top:6px;font-size:11px;color:#57534e;">
          <strong>GSTIN:</strong> {invoice.seller.gstin} | <strong>State Code:</strong> {invoice.seller.state_code} ({invoice.seller.state})
        </div>
        """
    else:
        gst_info_html = """
        <div style="margin-top:4px;font-size:10px;color:#78716c;">
          Composition Scheme / Small Seller Exemption under Section 22/24 of CGST Act
        </div>
        """

    # Sankalpa banner
    sankalpa_html = ""
    if invoice.buyer.sankalpa_devotee_name:
        sankalpa_html = f"""
        <div style="margin-top:6px;padding:6px 10px;background:#fefce8;border:1px solid #fef08a;border-radius:8px;font-size:11px;color:#854d0e;">
          🔱 <strong>Sankalpa (সংকল্প):</strong> {invoice.buyer.sankalpa_devotee_name} {f'({invoice.buyer.sankalpa_gotra} Gotra)' if invoice.buyer.sankalpa_gotra else ''}
        </div>
        """

    discount_row_html = ""
    if invoice.discount_amount > 0:
        discount_row_html = f"""
        <tr>
          <td style="padding:6px 0;color:#059669;font-weight:600;">Coupon Discount {f'({invoice.coupon_code})' if invoice.coupon_code else ''}</td>
          <td style="padding:6px 0;text-align:right;color:#059669;font-weight:700;">{discount_str}</td>
        </tr>
        """

    tax_breakdown_rows = ""
    if invoice.is_tax_invoice:
        if invoice.cgst_amount > 0 and invoice.sgst_amount > 0:
            tax_breakdown_rows = f"""
            <tr>
              <td style="padding:4px 0;color:#78716c;font-size:11px;">CGST (1.5%)</td>
              <td style="padding:4px 0;text-align:right;color:#44403c;font-size:11px;">₹{invoice.cgst_amount:,.2f}</td>
            </tr>
            <tr>
              <td style="padding:4px 0;color:#78716c;font-size:11px;">SGST (1.5%)</td>
              <td style="padding:4px 0;text-align:right;color:#44403c;font-size:11px;">₹{invoice.sgst_amount:,.2f}</td>
            </tr>
            """
        elif invoice.igst_amount > 0:
            tax_breakdown_rows = f"""
            <tr>
              <td style="padding:4px 0;color:#78716c;font-size:11px;">IGST (3.0%)</td>
              <td style="padding:4px 0;text-align:right;color:#44403c;font-size:11px;">₹{invoice.igst_amount:,.2f}</td>
            </tr>
            """
    else:
        tax_breakdown_rows = """
        <tr>
          <td style="padding:6px 0;color:#78716c;">Tax (0% / Exempted)</td>
          <td style="padding:6px 0;text-align:right;color:#78716c;">₹0</td>
        </tr>
        """

    auto_print_script = "<script>window.onload = function() { window.print(); };</script>" if auto_print else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Invoice #{invoice.invoice_number} - {invoice.seller.trade_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;800;900&family=Playfair+Display:ital,wght@0,600;0,800;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #faf8f5;
      color: #292524;
      line-height: 1.5;
      padding: 40px 20px;
    }}
    .invoice-wrapper {{
      max-width: 800px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #ebd9c5;
      border-radius: 20px;
      box-shadow: 0 10px 40px rgba(78, 47, 18, 0.08);
      padding: 56px 52px;
      position: relative;
      overflow: hidden;
    }}
    .no-print-bar {{
      max-width: 800px;
      margin: 0 auto 20px auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .btn-print {{
      background: linear-gradient(135deg, #d97706, #b45309);
      color: #ffffff;
      font-weight: 700;
      font-size: 13px;
      padding: 10px 22px;
      border-radius: 12px;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(180, 83, 9, 0.25);
      transition: all 0.2s;
    }}
    .btn-print:hover {{
      background: #92400e;
      transform: translateY(-1px);
    }}
    @media print {{
      body {{
        background: #ffffff;
        padding: 0;
      }}
      .no-print-bar {{
        display: none !important;
      }}
      .invoice-wrapper {{
        box-shadow: none !important;
        border: none !important;
        padding: 0 !important;
        max-width: 100% !important;
        border-radius: 0 !important;
      }}
      @page {{
        size: A4;
        margin: 15mm;
      }}
    }}
  </style>
</head>
<body>

  <!-- Floating Print Controls (Hidden when printed) -->
  <div class="no-print-bar">
    <div style="font-size:13px;color:#78716c;font-weight:600;">
      Official Customer Invoice & Packing Slip
    </div>
    <div style="display:flex;gap:8px;">
      <button class="btn-print" onclick="window.print()">
        🖨️ Print / Download PDF
      </button>
    </div>
  </div>

  <div class="invoice-wrapper">
    <!-- Top Header: Sacred Lotus Emblem (Left) & Elegant INVOICE (Right) -->
    <div style="display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:32px;">
      <!-- Gold Lotus Emblem -->
      <div>
        <svg width="76" height="76" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="48" stroke="#E6D0B3" stroke-width="1.5" stroke-dasharray="3 3"/>
          <path d="M50 15C50 15 35 38 35 56C35 68 41 78 50 85C59 78 65 68 65 56C65 38 50 15 50 15Z" fill="#C5A880" fill-opacity="0.18" stroke="#A9844F" stroke-width="2.2" stroke-linejoin="round"/>
          <path d="M50 30C42 42 20 52 20 66C20 76 29 84 42 85C36 78 35 68 37 57C39 46 50 30 50 30Z" fill="#C5A880" fill-opacity="0.28" stroke="#A9844F" stroke-width="1.8" stroke-linejoin="round"/>
          <path d="M50 30C58 42 80 52 80 66C80 76 71 84 58 85C64 78 65 68 63 57C61 46 50 30 50 30Z" fill="#C5A880" fill-opacity="0.28" stroke="#A9844F" stroke-width="1.8" stroke-linejoin="round"/>
          <circle cx="50" cy="58" r="4" fill="#92400e"/>
        </svg>
        <div style="font-family:'Cinzel',serif;font-size:15px;font-weight:700;color:#78350f;letter-spacing:1px;margin-top:6px;">
          {invoice.seller.trade_name}
        </div>
      </div>

      <!-- INVOICE Serif Title -->
      <div style="text-align:right;">
        <h1 style="font-family:'Cinzel',serif;font-size:36px;font-weight:800;color:#1c1917;letter-spacing:2px;line-height:1;">
          INVOICE
        </h1>
        <div style="font-size:11px;font-weight:700;color:#b45309;letter-spacing:1.5px;text-transform:uppercase;margin-top:4px;">
          {invoice.invoice_type_label}
        </div>
      </div>
    </div>

    <!-- Sub-Header: BILLED TO (Left) & INVOICE NO / DATE (Right) -->
    <div style="display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:32px;gap:24px;">
      <!-- Billed to -->
      <div style="flex:1;max-width:380px;">
        <div style="font-family:'Cinzel',serif;font-size:12px;font-weight:700;color:#1c1917;letter-spacing:1px;margin-bottom:6px;">
          BILLED TO:
        </div>
        <div style="font-size:14px;font-weight:700;color:#1c1917;">
          {invoice.buyer.name}
        </div>
        <div style="font-size:12px;color:#57534e;margin-top:2px;line-height:1.45;">
          {invoice.buyer.address_line1}{f', {invoice.buyer.address_line2}' if invoice.buyer.address_line2 else ''}<br>
          {f'Landmark: {invoice.buyer.landmark}<br>' if invoice.buyer.landmark else ''}
          {invoice.buyer.city}, {invoice.buyer.state} - {invoice.buyer.pincode}
        </div>
        <div style="font-size:12px;color:#57534e;margin-top:4px;">
          📞 {invoice.buyer.phone} | ✉️ {invoice.buyer.email}
        </div>
        {sankalpa_html}
      </div>

      <!-- Invoice Metadata -->
      <div style="text-align:right;min-width:240px;">
        <div style="font-size:13px;color:#44403c;">
          <strong style="color:#1c1917;">Invoice No:</strong> {invoice.invoice_number}
        </div>
        <div style="font-size:12px;color:#78716c;margin-top:4px;">
          <strong>Order Ref:</strong> #{invoice.order_number}
        </div>
        <div style="font-size:12px;color:#78716c;margin-top:3px;">
          <strong>Date:</strong> {formatted_date}
        </div>
        <div style="font-size:11px;color:#57534e;margin-top:6px;padding:4px 8px;background:#f5f5f4;border-radius:6px;display:inline-block;">
          <strong>Payment:</strong> {invoice.payment_method} ({invoice.payment_status})
        </div>
      </div>
    </div>

    <!-- Line Items Table -->
    <table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
      <thead>
        <tr style="border-top:1.5px solid #1c1917;border-bottom:1.5px solid #1c1917;">
          <th style="font-family:'Cinzel',serif;padding:10px 12px;text-align:left;font-size:11px;font-weight:700;color:#1c1917;letter-spacing:0.5px;">Item</th>
          <th style="font-family:'Cinzel',serif;padding:10px 12px;text-align:center;font-size:11px;font-weight:700;color:#1c1917;letter-spacing:0.5px;width:80px;">Quantity</th>
          <th style="font-family:'Cinzel',serif;padding:10px 12px;text-align:right;font-size:11px;font-weight:700;color:#1c1917;letter-spacing:0.5px;width:110px;">Unit Price</th>
          <th style="font-family:'Cinzel',serif;padding:10px 12px;text-align:right;font-size:11px;font-weight:700;color:#1c1917;letter-spacing:0.5px;width:110px;">Total</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>

    <!-- Financial Calculation Breakdown (Right-Aligned) -->
    <div style="display:flex;justify-content:flex-end;margin-bottom:40px;">
      <div style="width:280px;font-size:12px;">
        <table style="width:100%;">
          <tr>
            <td style="padding:6px 0;color:#57534e;">Subtotal</td>
            <td style="padding:6px 0;text-align:right;font-weight:600;color:#1c1917;">{subtotal_str}</td>
          </tr>
          {discount_row_html}
          <tr>
            <td style="padding:6px 0;color:#57534e;">Express Shipping</td>
            <td style="padding:6px 0;text-align:right;font-weight:600;color:#059669;">{shipping_str}</td>
          </tr>
          {tax_breakdown_rows}
          <tr style="border-top:1.5px solid #1c1917;">
            <td style="font-family:'Cinzel',serif;padding:14px 0 0 0;font-size:16px;font-weight:800;color:#1c1917;letter-spacing:0.5px;">Total</td>
            <td style="font-family:'Cinzel',serif;padding:14px 0 0 0;text-align:right;font-size:20px;font-weight:900;color:#1c1917;">{total_str}</td>
          </tr>
        </table>
      </div>
    </div>

    <!-- Thank you Greeting -->
    <div style="padding-top:10px;margin-bottom:32px;">
      <h2 style="font-family:'Playfair Display',serif;font-size:26px;font-style:italic;color:#1c1917;margin-bottom:6px;">
        Thank you!
      </h2>
      <p style="font-size:11px;color:#78716c;max-width:480px;line-height:1.5;">
        {invoice.footer_notes}
      </p>
    </div>

    <!-- Footer: Sold By / Payment Information & Registered Address -->
    <div style="border-top:1px solid #ebd9c5;padding-top:24px;display:flex;justify-content:space-between;align-items:flex-end;font-size:11px;gap:20px;">
      <div>
        <div style="font-family:'Cinzel',serif;font-size:10px;font-weight:800;color:#1c1917;letter-spacing:1px;margin-bottom:4px;">
          SOLD BY / DISPATCHED FROM:
        </div>
        <div style="font-weight:700;color:#1c1917;">{invoice.seller.legal_name}</div>
        <div style="color:#57534e;max-width:360px;margin-top:2px;">
          {invoice.seller.address}
        </div>
        <div style="color:#57534e;margin-top:2px;">
          Support: {invoice.seller.phone} | {invoice.seller.email}
        </div>
        {gst_info_html}
      </div>

      <!-- Authorised Signatory Stamp -->
      <div style="text-align:right;">
        <div style="font-family:'Playfair Display',serif;font-size:18px;font-style:italic;color:#78350f;letter-spacing:0.5px;">
          DivinLink Sanctum
        </div>
        <div style="font-size:10px;color:#78716c;margin-top:2px;">
          Authorised Vedic Repository Custodian
        </div>
        <div style="font-size:9px;color:#a8a29e;margin-top:2px;">
          Digitally generated in compliance with IT Act 2000
        </div>
      </div>
    </div>
  </div>

  {auto_print_script}
</body>
</html>
"""
    return html
