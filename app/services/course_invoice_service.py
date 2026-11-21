"""Official Printable Tax Invoice & Bill of Supply Service for Gurukul Course Purchases.

Generates:
1. Legal GST-compliant Tax Invoice (if company GSTIN is registered in ShopCMS)
   or Bill of Supply / Retail Invoice under Section 31 of CGST Act (SAC 999293:
   Commercial Training and Coaching Services).
2. Unique, persistent invoice number: e.g. DIVIN-CRS-INV-2026-F8A2D1.
3. Luxury gold-trimmed, A4 print-optimized HTML layout with @media print support.
4. Embedded QR code for cryptographic course enrollment verification.
"""

from __future__ import annotations

import logging
import urllib.parse
from datetime import datetime, timezone
from typing import Any

from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.cms import CMS_KEY_SHOP, ShopCMS
from app.models.course import Course, CourseEnrollment, CourseOrder
from app.models.enums import PaymentOrderStatus
from app.models.user import User
from app.schemas.course import (
    CourseInvoiceBuyerOut,
    CourseInvoiceDataOut,
    CourseInvoiceItemOut,
    CourseInvoiceSellerOut,
)

logger = logging.getLogger("astra.course.invoice_service")


def _format_inr(amount: float) -> str:
    return f"₹{amount:,.2f}".replace(".00", "")


def _generate_qr_url(data: str) -> str:
    """Generates a QR code image URL for instant verification on the invoice."""
    if not data:
        return ""
    encoded = urllib.parse.quote(data, safe="")
    return f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={encoded}"


async def get_or_create_course_invoice_data(
    identifier: str,
    user_id: PydanticObjectId | None = None,
    is_admin: bool = False,
) -> CourseInvoiceDataOut:
    """Fetches course order/enrollment and constructs complete invoice data snapshot.

    Generates and persists invoice_number on CourseOrder and CourseEnrollment if not present.
    """
    order: CourseOrder | None = None
    enrollment: CourseEnrollment | None = None
    course: Course | None = None

    # 1. Resolve CourseOrder by MongoDB id or razorpay_order_id
    if PydanticObjectId.is_valid(identifier):
        order = await CourseOrder.get(PydanticObjectId(identifier))
    if not order:
        order = await CourseOrder.find_one(CourseOrder.razorpay_order_id == identifier)

    # 2. If not found by order id, user might have requested by course_id
    if not order and PydanticObjectId.is_valid(identifier) and user_id:
        course_obj_id = PydanticObjectId(identifier)
        order = (
            await CourseOrder.find(
                CourseOrder.user_id == user_id,
                CourseOrder.course_id == course_obj_id,
                CourseOrder.status == PaymentOrderStatus.PAID,
            )
            .sort([("paid_at", -1), ("created_at", -1)])
            .first_or_none()
        )
        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_obj_id,
        )

    if not order and not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course order or enrollment record not found for this invoice.",
        )

    # Determine course
    course_id = order.course_id if order else enrollment.course_id  # type: ignore[union-attr]
    course = await Course.get(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The associated course could not be located.",
        )

    # Determine buyer user
    buyer_user_id = order.user_id if order else enrollment.user_id  # type: ignore[union-attr]
    if not is_admin and user_id and buyer_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this course invoice.",
        )

    buyer_user = await User.get(buyer_user_id)
    if not enrollment and order:
        enrollment = await CourseEnrollment.find_one(
            CourseEnrollment.user_id == order.user_id,
            CourseEnrollment.course_id == order.course_id,
        )

    # Fetch store CMS business & GST profile
    cms = await ShopCMS.find_one(ShopCMS.key == CMS_KEY_SHOP)
    if not cms:
        cms = ShopCMS(key=CMS_KEY_SHOP)

    # Generate or recover official invoice number
    invoice_number = (order.invoice_number if order else None) or (
        enrollment.invoice_number if enrollment else None
    )
    if not invoice_number:
        prefix = "DIVIN-CRS-INV"
        created_time = (order.paid_at if order and order.paid_at else None) or (
            enrollment.enrolled_at if enrollment else None
        ) or datetime.now(timezone.utc)
        year = created_time.year
        raw_key = (
            (order.razorpay_order_id if order else "")
            or (enrollment.order_id if enrollment else "")
            or str(order.id if order else enrollment.id)  # type: ignore[union-attr]
        )
        clean_key = raw_key.replace("order_", "").replace("crs_", "").replace("-", "")
        suffix = clean_key[-6:].upper() if len(clean_key) >= 6 else str(buyer_user_id)[-6:].upper()
        invoice_number = f"{prefix}-{year}-{suffix}"

        # Persist on order and enrollment
        if order:
            order.invoice_number = invoice_number
            await order.save()
        if enrollment:
            enrollment.invoice_number = invoice_number
            await enrollment.save()

    # Determine GST Status & Tax breakdown (SAC Code 999293)
    company_gstin = getattr(cms, "company_gstin", None)
    is_tax_invoice = bool(company_gstin and company_gstin.strip())

    seller_state = getattr(cms, "company_state", "Uttar Pradesh")
    seller_state_code = getattr(cms, "company_state_code", "09")
    buyer_state = seller_state

    # Calculation
    if order:
        grand_total = round(order.amount_paise / 100.0, 2)
    elif enrollment:
        grand_total = round(float(enrollment.amount_paid), 2)
    else:
        grand_total = round(float(course.price), 2)

    discount_amount = 0.0
    if course.mrp and course.mrp > course.price:
        discount_amount = round(course.mrp - course.price, 2)

    cgst_amount = 0.0
    sgst_amount = 0.0
    igst_amount = 0.0
    tax_amount = 0.0

    if is_tax_invoice and grand_total > 0:
        # Online education services (SAC 999293) standard GST rate is 18% inclusive
        base_taxable = round(grand_total / 1.18, 2)
        total_gst = round(grand_total - base_taxable, 2)
        is_intra_state = buyer_state.strip().lower() == seller_state.strip().lower()
        if is_intra_state:
            cgst_amount = round(total_gst / 2.0, 2)
            sgst_amount = round(total_gst - cgst_amount, 2)
            tax_amount = cgst_amount + sgst_amount
        else:
            igst_amount = total_gst
            tax_amount = igst_amount
        subtotal = base_taxable
    else:
        subtotal = grand_total
        tax_amount = 0.0

    frontend_base = getattr(settings, "FRONTEND_URL", "https://astra-astrology-web.vercel.app").rstrip("/")
    course_url = f"{frontend_base}/courses/{course.slug or str(course.id)}"
    invoice_url = f"{frontend_base}/account/courses/invoice/{str(order.id if order else course.id)}"
    verification_qr = _generate_qr_url(course_url)

    invoice_date = (
        (order.paid_at if order and order.paid_at else None)
        or (enrollment.enrolled_at if enrollment else None)
        or (order.created_at if order else datetime.now(timezone.utc))
    )

    buyer_name = (
        (getattr(buyer_user, "full_name", None) or getattr(buyer_user, "name", None))
        if buyer_user
        else (order.student_name if order else None)
    ) or "Valued Scholar"

    buyer_email = (
        getattr(buyer_user, "email", None)
        if buyer_user
        else (order.student_email if order else None)
    ) or "scholar@divinlink.com"

    buyer_phone = (
        getattr(buyer_user, "phone", None)
        or getattr(buyer_user, "mobile_number", None)
    ) if buyer_user else None

    seller = CourseInvoiceSellerOut(
        legal_name=getattr(cms, "company_legal_name", "DivinLink Spiritual Technologies Pvt. Ltd."),
        trade_name=getattr(cms, "company_trade_name", "DivinLink Gurukul • Vedic Astrological Sciences"),
        address=getattr(
            cms,
            "company_address",
            "Kashi Vishwanath Corridor, Dashashwamedh Ghat, Varanasi, Uttar Pradesh - 221001, India",
        ),
        state=seller_state,
        state_code=seller_state_code,
        phone=getattr(cms, "company_phone", "+91 91530 08182"),
        email=getattr(cms, "company_email", "support@divinlink.com"),
        website=getattr(cms, "company_website", "https://www.divinlink.com"),
        pan=getattr(cms, "company_pan", None),
        gstin=company_gstin if is_tax_invoice else None,
    )

    buyer = CourseInvoiceBuyerOut(
        name=buyer_name,
        email=buyer_email,
        phone=buyer_phone,
        state=buyer_state,
    )

    access_type = "Lifetime Access"
    if course.access_duration_days and course.access_duration_days > 0:
        access_type = f"{course.access_duration_days} Days Access"

    item = CourseInvoiceItemOut(
        course_id=str(course.id),
        title=course.title,
        slug=course.slug or str(course.id),
        instructor_name=course.instructor_name or "Pt. Acharya Rahul Sharma",
        level=course.level.replace("_", " ").title() if hasattr(course, "level") else "Vedic Masterclass",
        sac_code="999293",
        access_type=access_type,
        quantity=1,
        rate_inr=subtotal,
        discount_inr=discount_amount,
        taxable_amount_inr=subtotal,
        total_inr=grand_total,
    )

    return CourseInvoiceDataOut(
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        order_id=(order.razorpay_order_id if order else (enrollment.order_id if enrollment else "N/A")) or "N/A",
        payment_id=(order.razorpay_payment_id if order else (enrollment.payment_id if enrollment else "N/A")) or "N/A",
        payment_method=(order.method.upper() if order and order.method else "ONLINE_RAZORPAY"),
        payment_status="PAID",
        currency="INR",
        seller=seller,
        buyer=buyer,
        item=item,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        is_tax_invoice=is_tax_invoice,
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        igst_amount=igst_amount,
        grand_total=grand_total,
        course_url=course_url,
        invoice_url=invoice_url,
        verification_qr_url=verification_qr,
    )


def generate_course_invoice_html(invoice: CourseInvoiceDataOut, auto_print: bool = False) -> str:
    """Generates an ultra-crisp, luxury gold-trimmed, print-ready A4 HTML Tax Invoice / Bill of Supply."""
    formatted_date = invoice.invoice_date.strftime("%d %B %Y, %I:%M %p UTC")
    grand_total_str = _format_inr(invoice.grand_total)
    subtotal_str = _format_inr(invoice.subtotal)
    tax_str = _format_inr(invoice.tax_amount) if invoice.is_tax_invoice else "₹0.00 (Bill of Supply)"

    auto_print_script = "<script>window.addEventListener('load', () => window.print());</script>" if auto_print else ""

    gst_section = ""
    if invoice.is_tax_invoice:
        gst_section = f"""
        <tr style="color:#475569;font-size:12px;">
          <td colspan="4" style="padding:6px 12px;text-align:right;">CGST (9%):</td>
          <td style="padding:6px 12px;text-align:right;">{_format_inr(invoice.cgst_amount)}</td>
        </tr>
        <tr style="color:#475569;font-size:12px;">
          <td colspan="4" style="padding:6px 12px;text-align:right;">SGST (9%):</td>
          <td style="padding:6px 12px;text-align:right;">{_format_inr(invoice.sgst_amount)}</td>
        </tr>
        """
        invoice_title = "TAX INVOICE"
        invoice_subtitle = "Commercial Training & Coaching Services (SAC: 999293)"
    else:
        invoice_title = "BILL OF SUPPLY / RETAIL INVOICE"
        invoice_subtitle = "Issued under Section 31(3)(c) of the Central Goods & Services Tax Act, 2017"

    qr_img_tag = (
        f'<img src="{invoice.verification_qr_url}" alt="Verification QR" style="width:84px;height:84px;border:1px solid #E2E8F0;border-radius:8px;padding:4px;background:#FFFFFF;" />'
        if invoice.verification_qr_url
        else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Invoice {invoice.invoice_number} — {invoice.item.title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 32px 16px;
      background-color: #0F172A;
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      color: #0F172A;
      -webkit-font-smoothing: antialiased;
    }}
    .invoice-card {{
      max-width: 820px;
      margin: 0 auto;
      background: #FFFFFF;
      border-radius: 18px;
      padding: 44px 48px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.45);
      position: relative;
      border: 1px solid rgba(200, 155, 60, 0.35);
    }}
    .gold-header-bar {{
      height: 6px;
      background: linear-gradient(90deg, #9E7730 0%, #D4AF37 50%, #9E7730 100%);
      border-radius: 6px 6px 0 0;
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
    }}
    .btn-action {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 10px 20px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.2s ease;
      border: none;
    }}
    .btn-print {{
      background: linear-gradient(135deg, #D97706 0%, #B45309 100%);
      color: #FFFFFF;
      box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
    }}
    .btn-print:hover {{
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(217, 119, 6, 0.4);
    }}
    .btn-secondary {{
      background: #F1F5F9;
      color: #334155;
    }}
    .btn-secondary:hover {{
      background: #E2E8F0;
    }}
    @media print {{
      body {{
        background: #FFFFFF !important;
        padding: 0 !important;
      }}
      .invoice-card {{
        box-shadow: none !important;
        border: none !important;
        padding: 24px 20px !important;
        max-width: 100% !important;
      }}
      .no-print {{
        display: none !important;
      }}
      @page {{
        size: A4;
        margin: 12mm;
      }}
    }}
  </style>
</head>
<body>
  {auto_print_script}

  <div class="no-print" style="max-width:820px;margin:0 auto 20px;display:flex;align-items:center;justify-content:space-between;">
    <a href="{invoice.course_url}" class="btn-action btn-secondary">
      ← Return to Course
    </a>
    <div style="display:flex;gap:10px;">
      <button onclick="window.print()" class="btn-action btn-print">
        🖨️ Print / Save PDF
      </button>
    </div>
  </div>

  <div class="invoice-card">
    <div class="gold-header-bar"></div>

    <!-- Header Section -->
    <div style="display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:28px;border-bottom:2px solid #F1F5F9;">
      <div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
          <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#FAF5E4 0%,#F3E8C8 100%);border:1px solid #D4AF37;display:flex;align-items:center;justify-content:center;color:#8B6508;font-size:18px;font-weight:bold;">
            ॐ
          </div>
          <div>
            <h1 style="margin:0;font-family:'Cinzel',serif;font-size:20px;font-weight:800;color:#0F172A;letter-spacing:1px;">
              DIVINLINK GURUKUL
            </h1>
            <p style="margin:0;font-size:10px;color:#8B6508;letter-spacing:1.5px;text-transform:uppercase;font-weight:700;">
              COUNCIL OF VEDIC ASTROLOGICAL SCIENCES
            </p>
          </div>
        </div>
        <p style="margin:0;font-size:11px;color:#64748B;max-width:320px;line-height:1.5;">
          {invoice.seller.legal_name}<br>
          {invoice.seller.address}<br>
          GSTIN: {invoice.seller.gstin or "N/A (Exempt Under Section 22)"} • PAN: {invoice.seller.pan or "N/A"}
        </p>
      </div>

      <div style="text-align:right;">
        <div style="display:inline-block;padding:4px 12px;background:#F1F5F9;border-radius:6px;font-size:11px;font-weight:800;color:#334155;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">
          {invoice_title}
        </div>
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:16px;font-weight:800;color:#0F172A;font-mono;">
          #{invoice.invoice_number}
        </div>
        <p style="margin:4px 0 0;font-size:11px;color:#64748B;">
          <strong>Date:</strong> {formatted_date}
        </p>
        <div style="margin-top:6px;">
          <span style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;background:#ECFDF5;color:#059669;border:1px solid #A7F3D0;border-radius:9999px;font-size:11px;font-weight:700;">
            ✓ PAYMENT {invoice.payment_status}
          </span>
        </div>
      </div>
    </div>

    <!-- Bill To & Order Summary Grid -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;padding:24px 0;border-bottom:1px solid #F1F5F9;font-size:12px;">
      <div>
        <h4 style="margin:0 0 8px;font-size:11px;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;font-weight:700;">
          BILLED TO (SCHOLAR):
        </h4>
        <div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:2px;">
          {invoice.buyer.name}
        </div>
        <div style="color:#475569;line-height:1.5;">
          Email: {invoice.buyer.email}<br>
          {f"Phone: {invoice.buyer.phone}<br>" if invoice.buyer.phone else ""}
          State of Supply: {invoice.buyer.state or invoice.seller.state} (Code: {invoice.seller.state_code})
        </div>
      </div>

      <div style="text-align:right;">
        <h4 style="margin:0 0 8px;font-size:11px;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;font-weight:700;">
          PAYMENT & SETTLEMENT INFO:
        </h4>
        <div style="color:#475569;line-height:1.6;">
          <strong>Order Ref:</strong> <span style="font-family:monospace;font-weight:600;">{invoice.order_id}</span><br>
          <strong>Transaction ID:</strong> <span style="font-family:monospace;font-weight:600;">{invoice.payment_id}</span><br>
          <strong>Payment Mode:</strong> {invoice.payment_method}<br>
          <strong>Currency:</strong> {invoice.currency} (Indian Rupee)
        </div>
      </div>
    </div>

    <!-- Line Items Table -->
    <div style="margin:24px 0;">
      <table style="width:100%;border-collapse:collapse;font-size:12px;">
        <thead>
          <tr style="background:#F8FAFC;border-bottom:2px solid #E2E8F0;color:#475569;text-align:left;font-weight:700;">
            <th style="padding:12px;width:8%;">#</th>
            <th style="padding:12px;width:52%;">DESCRIPTION / MASTERCLASS</th>
            <th style="padding:12px;width:12%;text-align:center;">SAC</th>
            <th style="padding:12px;width:12%;text-align:center;">QTY</th>
            <th style="padding:12px;width:16%;text-align:right;">AMOUNT (INR)</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom:1px solid #F1F5F9;">
            <td style="padding:16px 12px;color:#64748B;vertical-align:top;">01</td>
            <td style="padding:16px 12px;vertical-align:top;">
              <div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:3px;">
                {invoice.item.title}
              </div>
              <div style="font-size:11px;color:#64748B;line-height:1.4;">
                • Level: {invoice.item.level}<br>
                • Master / Acharya: {invoice.item.instructor_name}<br>
                • Enrollment Access: {invoice.item.access_type}<br>
                • Includes: Full Video Curriculum, Sacred Notes & Tamper-proof Gurukul Certificate
              </div>
            </td>
            <td style="padding:16px 12px;text-align:center;color:#475569;font-family:monospace;vertical-align:top;">
              {invoice.item.sac_code}
            </td>
            <td style="padding:16px 12px;text-align:center;color:#0F172A;font-weight:600;vertical-align:top;">
              {invoice.item.quantity}
            </td>
            <td style="padding:16px 12px;text-align:right;color:#0F172A;font-weight:700;font-size:13px;vertical-align:top;">
              {subtotal_str}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Calculation Totals Block -->
    <div style="display:flex;justify-content:space-between;align-items:flex-start;padding-top:12px;">
      <div style="display:flex;gap:14px;align-items:center;">
        {qr_img_tag}
        <div style="font-size:11px;color:#64748B;max-width:220px;line-height:1.4;">
          <strong>Scan to Access Course:</strong><br>
          Instant digital verification on DivinLink Gurukul official ledger.
        </div>
      </div>

      <div style="width:280px;">
        <table style="width:100%;font-size:12px;border-collapse:collapse;">
          <tr style="color:#475569;">
            <td style="padding:6px 0;">Subtotal:</td>
            <td style="padding:6px 0;text-align:right;font-weight:600;color:#0F172A;">{subtotal_str}</td>
          </tr>
          {gst_section}
          <tr style="border-top:2px solid #0F172A;font-size:15px;color:#0F172A;">
            <td style="padding:10px 0;font-weight:800;">TOTAL AMOUNT PAID:</td>
            <td style="padding:10px 0;text-align:right;font-weight:800;color:#B45309;">{grand_total_str}</td>
          </tr>
        </table>
      </div>
    </div>

    <!-- Footer Terms & Authorized Signature -->
    <div style="margin-top:36px;padding-top:20px;border-top:1px solid #F1F5F9;display:flex;justify-content:space-between;align-items:flex-end;">
      <div style="font-size:10px;color:#94A3B8;max-width:440px;line-height:1.5;">
        <strong>Terms & Declarations:</strong><br>
        1. This is a computer-generated tax invoice / bill of supply issued under Section 31 of CGST Act.<br>
        2. Electronic course enrollments are digital services activated immediately upon payment capture.<br>
        3. All courses include authentic Gurukul certification upon 100% curriculum completion.<br>
        For inquiries, email support@divinlink.com or call +91 91530 08182.
      </div>

      <div style="text-align:center;">
        <div style="font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:18px;color:#0F172A;margin-bottom:2px;">
          Pt. Acharya Rahul Sharma
        </div>
        <div style="height:1px;background:#CBD5E1;width:150px;margin:2px auto 4px;"></div>
        <div style="font-size:9px;font-weight:700;color:#64748B;letter-spacing:1px;text-transform:uppercase;">
          AUTHORIZED REGISTRAR<br>DIVINLINK GURUKUL
        </div>
      </div>
    </div>

  </div>
</body>
</html>
"""
