"""Transactional email via Resend."""

import asyncio
from typing import Any

import resend
from loguru import logger

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

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
