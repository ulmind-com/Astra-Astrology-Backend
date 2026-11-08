"""Transactional email via Resend."""

import asyncio
from typing import Any

import resend
from loguru import logger

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.services.email_templates import (
    astrologer_welcome_email_html,
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
        f"Your Official Astra Gurukul Certificate ID: {certificate_id}\n\n"
        f"View and print your certificate here:\n{verify_url}\n\n"
        "Astra Cosmic Gurukul"
    )
    try:
        sent = await send_email(to=to, subject=subject, html=html, text=text)
        return sent is not None
    except Exception as exc:
        logger.opt(exception=exc).warning("Failed to deliver certificate email to {}", to)
        return False

