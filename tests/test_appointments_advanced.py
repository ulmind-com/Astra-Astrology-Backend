from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models.appointment import Appointment, AppointmentStatus, AvailabilityWindow
from app.models.astrologer import Astrologer
from app.models.enums import Skill, TransactionReason
from app.models.user import User
from app.services import wallet as wallet_service
from app.services.appointments import (
    calculate_slot_muhurat,
    book,
    cancel,
    update_prescription,
    day_view,
)


def test_vedic_choghadiya_and_muhurat_calculation():
    """Verify Choghadiya, Hora & Abhijit Muhurat calculation."""
    # Test Abhijit Muhurat time (12:00 PM IST = 06:30 AM UTC)
    t_abhijit = datetime(2026, 11, 4, 6, 30, tzinfo=UTC)
    res_abhijit = calculate_slot_muhurat(t_abhijit)
    assert res_abhijit["is_abhijit"] is True
    assert res_abhijit["quality"] == "super_auspicious"
    assert "অভিজিৎ" in res_abhijit["badge_bn"]

    # Test an evening time (8:00 PM IST = 14:30 UTC)
    t_evening = datetime(2026, 11, 4, 14, 30, tzinfo=UTC)
    res_evening = calculate_slot_muhurat(t_evening)
    assert "choghadiya" in res_evening
    assert "badge_bn" in res_evening
    assert "badge_hi" in res_evening
    assert "badge_en" in res_evening


@pytest.mark.asyncio
async def test_appointment_booking_with_pillar_and_prescription(client: AsyncClient):
    """Verify appointment creation with consultation pillar, Muhurat, and prescription workflow."""
    # Create test user
    client_user = await User(
        email="test_client@astra.com",
        first_name="Ananya",
        last_name="Roy",
        phone="+919876543210",
    ).insert()

    # Credit coins to user wallet
    await wallet_service.credit(
        user_id=client_user.id,
        amount_coins=5000,
        reason=TransactionReason.RECHARGE,
        idempotency_key="seed:client:5000",
    )

    # Create astrologer user & profile
    astro_user = await User(
        email="test_astro@astra.com",
        first_name="Ramesh",
        last_name="Shastri",
        phone="+919876543211",
        role="astrologer",
    ).insert()

    astrologer = await Astrologer(
        user_id=astro_user.id,
        slug="pt-ramesh-shastri",
        display_name="Pt. Ramesh Shastri",
        experience_years=15,
        skills=[Skill.VEDIC_ASTROLOGY, Skill.CAREER_BUSINESS],
        languages=["Bengali", "Hindi", "English"],
        is_listed=True,
    ).insert()

    # Configure appointment card
    astrologer.appointment.enabled = True
    astrologer.appointment.price_paise = 500_00  # ₹500
    astrologer.appointment.block_minutes = 30
    await astrologer.save()

    # Open a future window (Tomorrow 10:00 AM - 02:00 PM UTC)
    tomorrow = (datetime.now(UTC) + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    window_end = tomorrow + timedelta(hours=4)
    window = await AvailabilityWindow(
        astrologer_id=astrologer.id,
        day=tomorrow.date(),
        starts_at=tomorrow,
        ends_at=window_end,
    ).insert()

    # Test day_view
    view = await day_view(astrologer=astrologer, day_start=tomorrow, day_end=window_end)
    assert len(view["windows"]) >= 1
    assert "muhurat_ratings" in view
    assert len(view["muhurat_ratings"]) > 0

    # Book 30-min slot with pillar and birth details
    booking = await book(
        user=client_user,
        astrologer=astrologer,
        starts_at=tomorrow,
        minutes=30,
        note="Looking for guidance on career switch.",
        consultation_pillar="career_business",
        birth_details={"dob": "1995-05-12", "tob": "14:30", "pob": "Kolkata"},
    )

    assert booking.status == AppointmentStatus.BOOKED
    assert booking.consultation_pillar == "career_business"
    assert booking.muhurat_type is not None
    assert booking.birth_details["pob"] == "Kolkata"

    # Astrologer writes sacred prescription
    prescription_data = {
        "gemstone": "Yellow Sapphire (Pukhraj) 5.25 Ratti on Index Finger",
        "rudraksha": "5 Mukhi Nepal Rudraksha",
        "mantra": "Om Brim Brihaspataye Namah",
        "mantra_count": 108,
        "daan_remedy": "Donate yellow grams and bananas on Thursdays",
        "astrologer_notes": "Favorable Jupiter dasha begins next month; focus on higher leadership.",
    }

    updated_booking = await update_prescription(
        appointment=booking,
        astrologer_user_id=astro_user.id,
        prescription_data=prescription_data,
    )

    assert updated_booking.prescription is not None
    assert updated_booking.prescription["gemstone"].startswith("Yellow Sapphire")
    assert updated_booking.prescription["mantra_count"] == 108

    # Non-consulting user cannot update prescription
    with pytest.raises(Exception):
        await update_prescription(
            appointment=booking,
            astrologer_user_id=client_user.id,
            prescription_data=prescription_data,
        )

    # Cancel appointment
    cancelled = await cancel(appointment=booking, by=client_user, reason="Need to reschedule")
    assert cancelled.status == AppointmentStatus.CANCELLED
    assert cancelled.cancel_reason == "Need to reschedule"
