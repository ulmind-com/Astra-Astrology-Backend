"""Transactional email via Resend."""

import asyncio
from typing import Any

import resend
from loguru import logger

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.services.email_templates import (
    astrologer_welcome_email_html,
    purohit_welcome_email_html,
    otp_email_html,
    welcome_email_html,
)

if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY


def _from_address() -> str:
    return f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>"


async def send_email(
    to: str | list[str],
    subject: str,
    html: str,
    *,
    text: str | None = None,
    reply_to: str | None = None,
) -> dict[str, Any] | None:
    """Sends one email. Returns the Resend response, or None when not configured."""
    recipients = [to] if isinstance(to, str) else to

    if not settings.resend_configured:
        logger.warning("RESEND_API_KEY is not set — skipping email '{}' to {}", subject, recipients)
        if settings.DEBUG:
            logger.debug("Email body that would have been sent:\n{}", html)
        return None

    params: dict[str, Any] = {
        "from": _from_address(),
        "to": recipients,
        "subject": subject,
        "html": html,
    }
    if text:
        params["text"] = text
    if reply_to:
        params["reply_to"] = reply_to

    try:
        # The Resend SDK is synchronous, so keep it off the event loop.
        response = await asyncio.to_thread(resend.Emails.send, params)
        logger.info("Email '{}' sent to {}", subject, recipients)
        return response
    except Exception as exc:  # noqa: BLE001 - surfaced as a 503 below
        logger.opt(exception=exc).error("Failed to send email '{}' to {}", subject, recipients)
        raise ServiceUnavailableError(
            "Could not send the email right now. Please try again.",
            error_code="email_send_failed",
        )


async def send_otp_email(to: str, code: str, purpose: str, name: str | None = None) -> None:
    subjects = {
        "signup": f"{code} is your {settings.APP_NAME} sign-up code",
        "login": f"{code} is your {settings.APP_NAME} login code",
        "email_verification": f"Verify your email — {settings.APP_NAME}",
        "password_reset": f"Reset your {settings.APP_NAME} password",
    }
    await send_email(
        to=to,
        subject=subjects.get(purpose, f"{code} is your {settings.APP_NAME} code"),
        html=otp_email_html(code=code, purpose=purpose, name=name),
        text=(
            f"Your {settings.APP_NAME} verification code is {code}. "
            f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes."
        ),
    )


async def send_welcome_email(to: str, name: str | None = None) -> None:
    await send_email(
        to=to,
        subject=f"Welcome to {settings.APP_NAME}",
        html=welcome_email_html(name=name),
        text=(
            f"Welcome to {settings.APP_NAME}! Your account is ready. "
            "You can now get your kundli, numerology and daily panchang."
        ),
    )


async def send_astrologer_welcome_email(to: str, name: str, password: str) -> bool:
    """Carries the generated password, so it must never be logged or echoed.

    Returns False when mail is not configured and the message was dropped, so the
    caller can hand the password over another way instead of claiming it was sent.
    """
    sent = await send_email(
        to=to,
        subject=f"Your {settings.APP_NAME} astrologer account is ready",
        html=astrologer_welcome_email_html(name=name, email=to, password=password),
        text=(
            f"Welcome to {settings.APP_NAME}, {name}.\n\n"
            f"Sign in with:\n  Email: {to}\n  Temporary password: {password}\n\n"
            "Please change this password after your first sign-in."
        ),
    )
    return sent is not None


async def send_purohit_welcome_email(to: str, name: str, password: str) -> bool:
    """Carries the generated password for newly onboarded Purohit (Vedic Priest)."""
    sent = await send_email(
        to=to,
        subject=f"স্বাগতম — আপনার {settings.APP_NAME} পুরোহিত অ্যাকাউন্ট প্রস্তুত",
        html=purohit_welcome_email_html(name=name, email=to, password=password),
        text=(
            f"নমস্কার {name}!\n\n"
            f"{settings.APP_NAME} প্ল্যাটফর্মে আপনার পুরোহিত অ্যাকাউন্ট তৈরি সম্পন্ন হয়েছে।\n\n"
            f"লগইন পোর্টাল: https://admin.divinlink.com/login\n"
            f"Email: {to}\n"
            f"পাসওয়ার্ড: {password}\n\n"
            "প্রথমবার লগইনের পর দয়া করে পাসওয়ার্ড পরিবর্তন করুন।"
        ),
    )
    return sent is not None


async def send_course_certificate_email(
    to: str,
    user_name: str,
    course_title: str,
    certificate_id: str,
    issued_date: str,
    verify_url: str,
    instructor_name: str = "Pt. Acharya Rahul Sharma",
) -> bool:
    """Dispatches the official Gurukul graduation certificate email to the student."""
    from app.services.email_templates import course_certificate_email_html

    subject = f"🎓 Congratulations {user_name}! Your Official Certificate of Completion for {course_title}"
    html = course_certificate_email_html(
        user_name=user_name,
        course_title=course_title,
        certificate_id=certificate_id,
        issued_date=issued_date,
        verify_url=verify_url,
        instructor_name=instructor_name,
    )
    text = (
        f"Congratulations {user_name}!\n\n"
        f"You have successfully mastered 100% of the lessons in {course_title}.\n"
        f"Your Official DivinLink Gurukul Certificate ID: {certificate_id}\n\n"
        f"View and print your certificate here:\n{verify_url}\n\n"
        "DivinLink Gurukul"
    )
    try:
        sent = await send_email(to=to, subject=subject, html=html, text=text)
        return sent is not None
    except Exception as exc:
        logger.opt(exception=exc).warning("Failed to deliver certificate email to {}", to)
        return False


async def send_shop_order_refund_email(
    to: str,
    order_number: str,
    amount_inr: float,
    upi_id: str | None = None,
    transaction_id: str | None = None,
    items_count: int = 1,
    recipient_name: str | None = None,
) -> bool:
    """Dispatches a professional refund confirmation receipt when admin completes customer's UPI payout."""
    from app.services.email_templates import shop_order_refund_email_html

    subject = f"✅ Refund Processed: ₹{amount_inr:,.2f} for Order #{order_number} — {settings.APP_NAME}"
    html = shop_order_refund_email_html(
        order_number=order_number,
        amount_inr=amount_inr,
        upi_id=upi_id,
        transaction_id=transaction_id,
        items_count=items_count,
        recipient_name=recipient_name,
    )
    text = (
        f"Refund Confirmation for Order #{order_number}\n\n"
        f"Your refund of ₹{amount_inr:,.2f} has been processed successfully to your UPI account ({upi_id or 'Provided UPI/QR'}).\n"
        f"Bank UTR / Reference: {transaction_id or 'N/A'}\n\n"
        f"View your order status at: https://www.divinlink.com/account/orders\n\n"
        f"{settings.APP_NAME} Team"
    )
    try:
        sent = await send_email(to=to, subject=subject, html=html, text=text)
        return sent is not None
    except Exception as exc:
        logger.opt(exception=exc).warning("Failed to send refund email for order #{}: {}", order_number, exc)
        return False


async def send_payout_settlement_email(
    to: str,
    beneficiary_name: str,
    amount_inr: float,
    utr_number: str,
    payment_method: str = "bank_transfer",
    beneficiary_type: str = "astrologer",
) -> bool:
    """Sends a transactional email to the Astrologer or Pandit Ji when their payout is settled."""
    subject = f"💰 Payout Disbursed: ₹{amount_inr:,.2f} Settled to Your Account (UTR: {utr_number})"
    method_display = "Bank Account" if payment_method == "bank_transfer" else "UPI / VPA"
    role_display = "Vedic Astrologer" if beneficiary_type == "astrologer" else "Vedic Purohit (Pandit Ji)"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0c0a09; color: #f5f5f4; margin: 0; padding: 24px;">
      <div style="max-width: 580px; margin: 0 auto; background: #1c1917; border: 1px solid #292524; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.6);">
        <div style="background: linear-gradient(135deg, #d97706, #b45309); padding: 24px; text-align: center;">
          <h1 style="margin: 0; font-size: 22px; color: #ffffff; letter-spacing: 0.5px; font-weight: 700;">DivinLink Gurukul & Astrology</h1>
          <p style="margin: 6px 0 0; color: #fef3c7; font-size: 13px;">Official Payout Disbursement Advisory</p>
        </div>
        <div style="padding: 28px 24px;">
          <p style="font-size: 15px; color: #e7e5e4; margin-top: 0;">Pranam <strong>{beneficiary_name}</strong> ({role_display}),</p>
          <p style="color: #a8a29e; font-size: 14px; line-height: 1.6;">
            We are pleased to inform you that your withdrawal request has been verified and settled directly to your <strong>{method_display}</strong>.
          </p>
          <div style="background: #292524; border: 1px solid #44403c; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #44403c; padding-bottom: 10px; margin-bottom: 10px;">
              <span style="color: #a8a29e; font-size: 13px;">Disbursed Amount:</span>
              <strong style="color: #10b981; font-size: 18px;">₹{amount_inr:,.2f}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #44403c; padding-bottom: 10px; margin-bottom: 10px;">
              <span style="color: #a8a29e; font-size: 13px;">Bank Reference / UTR:</span>
              <strong style="color: #fbbf24; font-family: monospace; font-size: 14px;">{utr_number}</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #a8a29e; font-size: 13px;">Payment Channel:</span>
              <span style="color: #f5f5f4; font-size: 13px; font-weight: 600;">{method_display}</span>
            </div>
          </div>
          <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 12px 14px; border-radius: 6px; margin-bottom: 20px;">
            <p style="margin: 0; color: #6ee7b7; font-size: 13px; font-weight: 500;">
              ✓ Please inspect your bank account or UPI application balance. If you do not see the credited amount within a few hours, use UTR <strong>{utr_number}</strong> with your bank branch or customer support.
            </p>
          </div>
          <p style="color: #78716c; font-size: 12px; text-align: center; margin-bottom: 0;">
            DivinLink Gurukul • Spiritual & Astrological Ecosystem<br>
            Secure Automated Payout Processing Desk
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    text = (
        f"Pranam {beneficiary_name},\n\n"
        f"Your payout of ₹{amount_inr:,.2f} has been settled via {method_display}.\n"
        f"UTR Number: {utr_number}\n\n"
        f"Please check your bank account or UPI balance.\n\n"
        f"DivinLink Gurukul Team"
    )
    try:
        sent = await send_email(to=to, subject=subject, html=html, text=text)
        return sent is not None
    except Exception as exc:
        logger.opt(exception=exc).warning("Failed to send payout settlement email to {}: {}", to, exc)
        return False


async def send_course_purchase_invoice_email(
    to: str,
    user_name: str,
    course_title: str,
    invoice_number: str,
    order_id: str,
    payment_id: str,
    amount_inr: float,
    payment_method: str = "Online / Razorpay",
    purchase_date: str = "",
    course_url: str = "",
    invoice_url: str = "",
    instructor_name: str = "Pt. Acharya Rahul Sharma",
    access_type: str = "Lifetime Access",
) -> bool:
    """Dispatches the official Tax Invoice & Consecrated Enrollment Bill to the student upon successful payment."""
    from app.services.email_templates import course_purchase_invoice_email_html

    formatted_amount = f"₹{amount_inr:,.2f}".replace(".00", "")
    subject = f"🧾 Tax Invoice & Enrollment Bill: {course_title} (Invoice #{invoice_number})"

    html = course_purchase_invoice_email_html(
        user_name=user_name,
        user_email=to,
        course_title=course_title,
        invoice_number=invoice_number,
        order_id=order_id,
        payment_id=payment_id,
        amount_inr=amount_inr,
        payment_method=payment_method,
        purchase_date=purchase_date,
        course_url=course_url,
        invoice_url=invoice_url,
        instructor_name=instructor_name,
        access_type=access_type,
    )

    text = (
        f"Dear {user_name},\n\n"
        f"Thank you for enrolling in {course_title} at DivinLink Gurukul!\n\n"
        f"TAX INVOICE / ENROLLMENT BILL DETAILS:\n"
        f"-----------------------------------------\n"
        f"Invoice Number: #{invoice_number}\n"
        f"Course: {course_title}\n"
        f"Faculty / Acharya: {instructor_name}\n"
        f"Access: {access_type}\n"
        f"Date of Purchase: {purchase_date}\n"
        f"Razorpay Payment ID: {payment_id}\n"
        f"Order Reference: {order_id}\n"
        f"Payment Mode: {payment_method}\n"
        f"Status: PAID & CAPTURED\n"
        f"Total Amount Paid: {formatted_amount}\n"
        f"-----------------------------------------\n\n"
        f"Access your course anytime here:\n{course_url}\n\n"
        f"View and print your official invoice (PDF / HTML):\n{invoice_url}\n\n"
        f"DivinLink Gurukul • Council of Vedic Astrological Sciences\n"
        f"Support: support@divinlink.com | +91 91530 08182"
    )

    try:
        sent = await send_email(to=to, subject=subject, html=html, text=text)
        return sent is not None
    except Exception as exc:
        logger.opt(exception=exc).warning("Failed to dispatch course purchase invoice email to {}: {}", to, exc)
        return False


