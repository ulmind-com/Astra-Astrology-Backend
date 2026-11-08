from datetime import UTC, datetime, timedelta
import pytest
from httpx import AsyncClient

from app.models.appointment import Appointment, AppointmentStatus
from app.models.astrologer import Astrologer
from app.models.user import User
from app.services.email_templates import (
    appointment_reminder_astrologer_email_html,
    appointment_reminder_client_email_html,
    generate_google_calendar_url,
)
from app.services.reminders import (
    _format_birth_details,
    _format_ist_timing,
    check_and_send_appointment_reminders,
    send_reminder_for_appointment,
)


def test_google_calendar_url_generator():
    start = datetime(2026, 11, 5, 12, 30, tzinfo=UTC)
    end = datetime(2026, 11, 5, 13, 0, tzinfo=UTC)
    url = generate_google_calendar_url(
        title="Consultation with Soumyajit",
        description="Career & Wealth session",
        starts_at=start,
        ends_at=end,
        location="https://astra.com",
    )
    assert "https://calendar.google.com/calendar/render" in url
    assert "action=TEMPLATE" in url
    assert "20261105T123000Z%2F20261105T130000Z" in url or "20261105T123000Z/20261105T130000Z" in url


def test_timing_and_birth_details_formatters():
    start = datetime(2026, 11, 5, 12, 30, tzinfo=UTC)
    end = datetime(2026, 11, 5, 13, 0, tzinfo=UTC)
    timing = _format_ist_timing(start, end)
    assert "06:00 PM" in timing
    assert "06:30 PM" in timing
    assert "IST" in timing

    bd = {"dob": "1995-10-15", "tob": "14:30", "pob": "Kolkata"}
    formatted_bd = _format_birth_details(bd)
    assert "DOB: 1995-10-15" in formatted_bd
    assert "Place: Kolkata" in formatted_bd


def test_reminder_email_templates_render():
    client_html = appointment_reminder_client_email_html(
        client_name="Rahul",
        astrologer_name="Astrologer Soumyajit",
        consultation_pillar="career_wealth",
        starts_at_str="06:00 PM – 06:30 PM (IST)",
        chamber_url="https://astra-astrology-web.vercel.app/account/appointments",
        calendar_url="https://calendar.google.com",
    )
    assert "Rahul" in client_html
    assert "Astrologer Soumyajit" in client_html
    assert "Career Wealth" in client_html
    assert "Add to Google Calendar" in client_html

    astro_html = appointment_reminder_astrologer_email_html(
        astrologer_name="Astrologer Soumyajit",
        client_name="Rahul",
        consultation_pillar="career_wealth",
        birth_details_str="DOB: 1995-10-15 | Place: Kolkata",
        user_note="Want guidance regarding promotion.",
        starts_at_str="06:00 PM – 06:30 PM (IST)",
        admin_chamber_url="https://astra-astrology-admin-five.vercel.app/appointments",
        calendar_url="https://calendar.google.com",
    )
    assert "Rahul" in astro_html
    assert "Want guidance regarding promotion" in astro_html
    assert "Open Astrologer Chamber" in astro_html

