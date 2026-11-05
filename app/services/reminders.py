"""Automated 5-minute prior email reminders for scheduled appointments.

Runs on a recurring background loop, finds appointments whose starts_at is within
the 5-minute reminder window, claims an atomic lock on `reminded_at` so double-sends
are impossible, and dispatches rich transactional emails to both client and astrologer.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from beanie import PydanticObjectId
from loguru import logger

from app.core.config import settings
from app.models.appointment import Appointment, AppointmentStatus
from app.models.astrologer import Astrologer
from app.models.base import utcnow
from app.models.user import User
from app.services import email as email_service
from app.services.email_templates import (
    appointment_reminder_astrologer_email_html,
    appointment_reminder_client_email_html,
    generate_google_calendar_url,
)


def _format_ist_timing(starts_at: datetime, ends_at: datetime) -> str:
    """Formats start and end UTC timestamps into Indian Standard Time (IST) human string."""
    ist_delta = timedelta(hours=5, minutes=30)
    ist_start = starts_at + ist_delta
    ist_end = ends_at + ist_delta

    start_str = ist_start.strftime("%I:%M %p")
    end_str = ist_end.strftime("%I:%M %p")
    date_str = ist_start.strftime("%A, %d %b %Y")

    return f"{start_str} – {end_str} (IST), {date_str}"


def _format_birth_details(bd: dict[str, Any] | None) -> str | None:
    if not bd:
        return None
    parts = []
    if bd.get("date_of_birth") or bd.get("dob"):
        parts.append(f"DOB: {bd.get('date_of_birth') or bd.get('dob')}")
    if bd.get("time_of_birth") or bd.get("tob"):
        parts.append(f"Time: {bd.get('time_of_birth') or bd.get('tob')}")
    if bd.get("place_of_birth") or bd.get("pob"):
        parts.append(f"Place: {bd.get('place_of_birth') or bd.get('pob')}")
    return " | ".join(parts) if parts else None


async def send_reminder_for_appointment(appointment: Appointment) -> bool:
    """Dispatches the reminder email to both the user and the astrologer."""
    try:
        user = await User.get(appointment.user_id)
        if not user or not user.email:
            logger.warning(
                "Cannot send appointment reminder: User {} not found or has no email",
                appointment.user_id,
            )
            return False

        astrologer = await Astrologer.get(appointment.astrologer_id)
        if not astrologer:
            logger.warning(
                "Cannot send appointment reminder: Astrologer {} not found",
                appointment.astrologer_id,
            )
            return False

        # Find astrologer's user account to get their email address
        astrologer_user = await User.get(astrologer.user_id)
        astrologer_email = astrologer_user.email if astrologer_user else None

        client_name = user.full_name or user.first_name or "Valued Client"
        astro_name = astrologer.display_name or "Astrologer"
        timing_str = _format_ist_timing(appointment.starts_at, appointment.ends_at)

        # Base URLs for deep links
        frontend_url = settings.FRONTEND_URL.rstrip("/") if settings.FRONTEND_URL else "https://astra-astrology-web.vercel.app"
        admin_url = "https://astra-astrology-admin-five.vercel.app"

        client_chamber_url = f"{frontend_url}/account/appointments"
        admin_chamber_url = f"{admin_url}/appointments"

        # Generate 1-click Google Calendar add links
        gcal_client_url = generate_google_calendar_url(
            title=f"Sacred Consultation with {astro_name}",
            description=f"Consultation on {appointment.consultation_pillar or 'Vedic Astrology'}. Join link: {client_chamber_url}",
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            location=client_chamber_url,
        )
        gcal_astro_url = generate_google_calendar_url(
            title=f"Session with Client {client_name}",
            description=f"Consultation on {appointment.consultation_pillar or 'Vedic Astrology'}. Portal: {admin_chamber_url}",
            starts_at=appointment.starts_at,
            ends_at=appointment.ends_at,
            location=admin_chamber_url,
        )

        # 1. Send Email to User (Client)
        client_html = appointment_reminder_client_email_html(
            client_name=client_name,
            astrologer_name=astro_name,
            consultation_pillar=appointment.consultation_pillar or "Vedic Astrology",
            starts_at_str=timing_str,
            chamber_url=client_chamber_url,
            calendar_url=gcal_client_url,
        )
        await email_service.send_email(
            to=user.email,
            subject=f"🔔 Reminder: Your consultation with {astro_name} starts in 5 minutes!",
            html=client_html,
        )
        logger.info(
            "Dispatched 5-min consultation reminder email to client {} ({})",
            client_name,
            user.email,
        )

        # 2. Send Email to Astrologer (if email available)
        if astrologer_email:
            astro_html = appointment_reminder_astrologer_email_html(
                astrologer_name=astro_name,
                client_name=client_name,
                consultation_pillar=appointment.consultation_pillar or "Vedic Astrology",
                birth_details_str=_format_birth_details(appointment.birth_details),
                user_note=appointment.user_note,
                starts_at_str=timing_str,
                admin_chamber_url=admin_chamber_url,
                calendar_url=gcal_astro_url,
            )
            await email_service.send_email(
                to=astrologer_email,
                subject=f"🔔 Alert: Session with {client_name} starts in 5 minutes!",
                html=astro_html,
            )
            logger.info(
                "Dispatched 5-min consultation alert email to astrologer {} ({})",
                astro_name,
                astrologer_email,
            )

        return True

    except Exception as exc:
        logger.opt(exception=exc).error(
            "Error sending reminder for appointment {}: {}",
            appointment.id,
            exc,
        )
        return False


async def check_and_send_appointment_reminders() -> int:
    """Finds appointments starting in ~5 minutes that haven't been reminded yet.

    Uses atomic find_one_and_update to guarantee zero double-sends across concurrent workers.
    """
    now = utcnow()
    # Reminder window: Starting within the next 5.5 minutes, and not expired in the past (> now - 5m)
    reminder_threshold = now + timedelta(minutes=5, seconds=30)
    past_safety_margin = now - timedelta(minutes=5)

    reminded_count = 0

    # Query candidate appointments
    candidates = (
        await Appointment.find(
            {
                "status": AppointmentStatus.BOOKED,
                "reminded_at": None,
                "starts_at": {"$lte": reminder_threshold, "$gt": past_safety_margin},
            }
        )
        .limit(50)
        .to_list()
    )

    for candidate in candidates:
        # Atomic lock claim
        claimed = await Appointment.get_motor_collection().find_one_and_update(
            {
                "_id": candidate.id,
                "status": AppointmentStatus.BOOKED,
                "reminded_at": None,
            },
            {"$set": {"reminded_at": now}},
            return_document=True,
        )

        if claimed:
            refreshed = Appointment(**claimed)
            success = await send_reminder_for_appointment(refreshed)
            if success:
                reminded_count += 1

    return reminded_count


async def reconcile_orphaned_appointments() -> int:
    """Finds appointments concluded > 24 hours ago that were never completed or cancelled,
    and automatically completes them, capturing held escrow coins to the astrologer.
    Eliminates orphaned escrow holds.
    """
    from app.services import wallet as wallet_service
    from app.services.cosmic_intelligence import generate_divya_paramarsha_certificate_data

    now = utcnow()
    reconciliation_cutoff = now - timedelta(hours=24)

    orphaned = await Appointment.find({
        "status": AppointmentStatus.BOOKED,
        "ends_at": {"$lte": reconciliation_cutoff},
    }).limit(50).to_list()

    reconciled_count = 0
    for apt in orphaned:
        claimed = await Appointment.get_motor_collection().find_one_and_update(
            {
                "_id": apt.id,
                "status": AppointmentStatus.BOOKED,
            },
            {
                "$set": {
                    "status": AppointmentStatus.COMPLETED,
                    "completed_at": now,
                    "held_status": "captured",
                }
            },
            return_document=True,
        )
        if claimed:
            if getattr(apt, "held_coins", 0) > 0 and getattr(apt, "held_status", "") == "held":
                try:
                    await wallet_service.capture_held_coins(
                        user_id=apt.user_id,
                        amount_coins=apt.held_coins,
                        appointment_id=apt.id,
                        astrologer_user_id=apt.astrologer_user_id,
                        note="Automatic 24h consultation completion & escrow capture",
                    )
                except Exception as exc:
                    logger.error("Failed to capture held coins on auto-reconciliation: {}", exc)

            try:
                refreshed = Appointment(**claimed)
                astro = await Astrologer.get(refreshed.astrologer_id)
                client_u = await User.get(refreshed.user_id)
                if astro and client_u and not refreshed.certificate_data:
                    cert = generate_divya_paramarsha_certificate_data(refreshed, astro, client_u)
                    refreshed.certificate_data = cert
                    await refreshed.save()
            except Exception as cert_err:
                logger.error("Auto certificate generation failed on reconciliation: {}", cert_err)

            reconciled_count += 1
            logger.info("Auto-reconciled orphaned appointment {} after 24h", apt.id)

    return reconciled_count


async def reconcile_brahma_pause_timeouts() -> int:
    """Finds appointments where astrologer is on Brahma Pause and the session time has arrived (<= 10 mins)
    or rescue deadline passed without seeker action, and executes 100% full refund so funds are never stuck.
    """
    from app.services import wallet as wallet_service
    from app.models.enums import TransactionReason

    now = utcnow()
    threshold = now + timedelta(minutes=10)

    timeouts = await Appointment.find({
        "status": AppointmentStatus.BOOKED,
        "brahma_pause_affected": True,
        "starts_at": {"$lte": threshold},
    }).limit(50).to_list()

    processed_count = 0
    for apt in timeouts:
        claimed = await Appointment.get_motor_collection().find_one_and_update(
            {
                "_id": apt.id,
                "status": AppointmentStatus.BOOKED,
                "brahma_pause_affected": True,
            },
            {
                "$set": {
                    "status": AppointmentStatus.CANCELLED,
                    "cancelled_at": now,
                    "cancel_reason": "Automatic 100% refund: Brahma Pause session arrival without seeker reschedule",
                    "brahma_pause_affected": False,
                }
            },
            return_document=True,
        )
        if claimed:
            # Delete slots
            await AppointmentSlot.find(AppointmentSlot.appointment_id == apt.id).delete()

            # Release held coins
            if getattr(apt, "held_coins", 0) > 0 and getattr(apt, "held_status", "") == "held":
                try:
                    await wallet_service.release_held_coins(
                        user_id=apt.user_id,
                        amount_coins=apt.held_coins,
                        appointment_id=apt.id,
                    )
                except Exception as exc:
                    logger.error("Failed to release held coins on Brahma Pause timeout: {}", exc)

            # 100% refund deposit
            if getattr(apt, "deposit_coins", 0) > 0:
                try:
                    await wallet_service.credit(
                        user_id=apt.user_id,
                        amount_coins=apt.deposit_coins,
                        reason=TransactionReason.REFUND,
                        idempotency_key=f"appointment:{apt.id}:brahma_pause_auto_refund",
                        note="Automatic 100% refund for unrescheduled Brahma Pause consultation",
                    )
                except Exception as ref_err:
                    logger.error("Failed to credit deposit on Brahma Pause timeout: {}", ref_err)

            processed_count += 1
            logger.info("Auto-refunded Brahma Pause appointment {} before scheduled arrival", apt.id)

    return processed_count


async def appointment_reminder_worker_loop() -> None:
    """Continuous background worker running once per minute."""
    logger.info("Appointment 5-minute reminder and reconciliation worker started.")
    loop_tick = 0
    while True:
        try:
            await asyncio.sleep(60)
            loop_tick += 1

            # Check 5-min reminders every minute
            count = await check_and_send_appointment_reminders()
            if count > 0:
                logger.info("Appointment reminder loop processed {} reminder(s).", count)

            # Reconcile Brahma Pause timeouts every 2 minutes
            if loop_tick % 2 == 0:
                bp_refunds = await reconcile_brahma_pause_timeouts()
                if bp_refunds > 0:
                    logger.info("Brahma Pause reconciliation refunded {} timeout session(s).", bp_refunds)

            # Reconcile orphaned appointments once every 10 minutes
            if loop_tick % 10 == 0:
                reconciled = await reconcile_orphaned_appointments()
                if reconciled > 0:
                    logger.info("Appointment auto-reconciliation completed {} orphaned session(s).", reconciled)

        except asyncio.CancelledError:
            logger.info("Appointment reminder background worker stopped gracefully.")
            break
        except Exception as exc:
            logger.opt(exception=exc).error("Unexpected error in appointment reminder worker: {}", exc)
            await asyncio.sleep(15)

