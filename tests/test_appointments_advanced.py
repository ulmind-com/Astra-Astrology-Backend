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

    # Guard check: Premature completion of future booking MUST be blocked!
    from app.services.appointments import complete
    from app.core.exceptions import BadRequestError

    with pytest.raises(BadRequestError) as exc_info:
        await complete(appointment=booking, by=astro_user)
    assert exc_info.value.error_code == "premature_completion"
    assert "Cannot complete a session before it starts" in str(exc_info.value.message)

    # Cancel appointment
    cancelled = await cancel(appointment=booking, by=client_user, reason="Need to reschedule")
    assert cancelled.status == AppointmentStatus.CANCELLED
    assert cancelled.cancel_reason == "Need to reschedule"


@pytest.mark.asyncio
async def test_private_astrological_vault_notes(client: AsyncClient):
    """Verify astrologer private vault notes are confidential and hidden from seeker."""
    from app.api.v1.appointments import _out
    from app.services.appointments import update_private_notes

    astro_user = await User(
        email="pandit.vault@divinlink.com",
        first_name="Pandit",
        phone="+919988776655",
        role="astrologer",
    ).insert()

    astro_profile = await Astrologer(
        user_id=astro_user.id,
        display_name="Acharya Vault",
        slug="acharya-vault",
        is_verified=True,
        is_listed=True,
    ).insert()

    client_user = await User(
        email="seeker.vault@divinlink.com",
        phone="+919988776654",
        role="user",
    ).insert()

    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(minutes=30)
    booking = await Appointment(
        user_id=client_user.id,
        astrologer_id=astro_profile.id,
        astrologer_user_id=astro_user.id,
        starts_at=starts_at,
        ends_at=ends_at,
        minutes=30,
        price_paise=50000,
        deposit_paise=10000,
        deposit_coins=10,
        balance_due_paise=40000,
        status=AppointmentStatus.BOOKED,
    ).insert()

    # Astrologer writes confidential private notes
    secret_note = "গোপন নোট: ক্লায়েন্টের মানসিক অস্থিরতা তীব্র, রাহু-চন্দ্রের গোচর প্রতিকূল।"
    updated = await update_private_notes(
        appointment=booking,
        astrologer_user_id=astro_user.id,
        notes=secret_note,
    )
    assert updated.astrologer_private_notes == secret_note
    assert updated.astrologer_private_notes_updated_at is not None

    # Seeker serialization MUST mask private notes to None
    seeker_view = await _out(updated, client_user)
    assert seeker_view.astrologer_private_notes is None
    assert seeker_view.astrologer_private_notes_updated_at is None

    # Astrologer serialization MUST show the confidential private notes
    astro_view = await _out(updated, astro_user)
    assert astro_view.astrologer_private_notes == secret_note
    assert astro_view.astrologer_private_notes_updated_at is not None

    # Unauthorized user (seeker) cannot update private notes
    with pytest.raises(Exception):
        await update_private_notes(
            appointment=booking,
            astrologer_user_id=client_user.id,
            notes="Hacked note",
        )


@pytest.mark.asyncio
async def test_contiguous_availability_windows_boundary_collision(client: AsyncClient):
    """Verify that adjacent/contiguous slots (e.g. 5-6 PM and 6-7 PM) do NOT trigger false overlap errors."""
    from beanie.operators import GT, LT, And
    from app.core.exceptions import BadRequestError
    from app.services.appointments import open_quick_tatkal_window

    astro_user = await User(
        email="contiguous_astro@astra.com",
        first_name="Contiguous",
        last_name="Pandit",
    ).insert()

    astro = await Astrologer(
        user_id=astro_user.id,
        display_name="Acharya Contiguous",
        skills=[Skill.VEDIC_ASTROLOGY],
        languages=["Bengali", "English"],
    ).insert()

    base_time = (datetime.now(UTC) + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
    w1_start = base_time.replace(hour=17)
    w1_end = base_time.replace(hour=18)

    # Window 1: 17:00 - 18:00
    w1 = await AvailabilityWindow(
        astrologer_id=astro.id,
        day=w1_start.date(),
        starts_at=w1_start,
        ends_at=w1_end,
    ).insert()

    # Contiguous Window 2: 18:00 - 19:00 (Boundary touches w1_end, MUST NOT clash!)
    w2_start = base_time.replace(hour=18)
    w2_end = base_time.replace(hour=19)

    clash_contiguous = await AvailabilityWindow.find_one(
        And(
            AvailabilityWindow.astrologer_id == astro.id,
            LT(AvailabilityWindow.starts_at, w2_end),
            GT(AvailabilityWindow.ends_at, w2_start),
        )
    )
    assert clash_contiguous is None, "Contiguous adjacent slot (18:00-19:00) falsely clashed with (17:00-18:00)!"

    w2 = await AvailabilityWindow(
        astrologer_id=astro.id,
        day=w2_start.date(),
        starts_at=w2_start,
        ends_at=w2_end,
    ).insert()

    # Truly Overlapping Window 3: 17:30 - 18:30 (Overlaps both w1 and w2, MUST clash!)
    w3_start = base_time.replace(hour=17, minute=30)
    w3_end = base_time.replace(hour=18, minute=30)

    clash_overlapping = await AvailabilityWindow.find_one(
        And(
            AvailabilityWindow.astrologer_id == astro.id,
            LT(AvailabilityWindow.starts_at, w3_end),
            GT(AvailabilityWindow.ends_at, w3_start),
        )
    )
    assert clash_overlapping is not None, "Overlapping slot (17:30-18:30) failed to detect clash!"

    # Contiguous VIP Tatkal slot: 19:00 - 19:30 (Right after w2_end, MUST succeed without clash)
    w_tatkal = await open_quick_tatkal_window(
        astrologer=astro,
        starts_at=base_time.replace(hour=19),
        minutes=30,
        multiplier=2.0,
    )
    assert w_tatkal is not None
    assert w_tatkal.starts_at == base_time.replace(hour=19)
    assert w_tatkal.ends_at == base_time.replace(hour=19, minute=30)

    # Overlapping VIP Tatkal slot: 18:45 - 19:15 (Overlaps w2 and tatkal, MUST raise BadRequestError)
    with pytest.raises(BadRequestError):
        await open_quick_tatkal_window(
            astrologer=astro,
            starts_at=base_time.replace(hour=18, minute=45),
            minutes=30,
        )


@pytest.mark.asyncio
async def test_availability_window_timezone_date_truncation_fix(client: AsyncClient):
    """Verify that slots scheduled past midnight in IST (e.g. 01:00 AM IST) do not get truncated to the previous day in UTC."""
    from zoneinfo import ZoneInfo
    from app.services.appointments import open_quick_tatkal_window

    astro_user = await User(
        email="tz_astro@astra.com",
        first_name="Timezone",
        last_name="Pandit",
    ).insert()

    astro = await Astrologer(
        user_id=astro_user.id,
        display_name="Acharya Timezone",
        skills=[Skill.VEDIC_ASTROLOGY],
        languages=["Bengali", "English"],
    ).insert()

    IST = ZoneInfo("Asia/Kolkata")
    # Astrologer in Kolkata wants to open a window on 2026-11-15 at 01:00 AM IST to 02:00 AM IST
    # In UTC, 01:00 AM IST on 2026-11-15 is 19:30 UTC on 2026-11-14!
    ist_start = datetime(2026, 11, 15, 1, 0, tzinfo=IST)
    utc_start = ist_start.astimezone(UTC)

    assert utc_start.date() == datetime(2026, 11, 14).date(), "Sanity check: in UTC date is 14th"
    assert ist_start.date() == datetime(2026, 11, 15).date(), "Sanity check: in IST date is 15th"

    # Quick tatkal window
    w_tatkal = await open_quick_tatkal_window(
        astrologer=astro,
        starts_at=utc_start,
        minutes=30,
        timezone_name="Asia/Kolkata",
    )
    # The stored day MUST be 2026-11-15 (IST date), NOT 2026-11-14 (UTC truncated date)!
    assert w_tatkal.day == datetime(2026, 11, 15).date(), f"Expected 2026-11-15 but got {w_tatkal.day}"



