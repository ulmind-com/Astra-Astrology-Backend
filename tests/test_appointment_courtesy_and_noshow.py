"""Unit tests for Courtesy Reschedule and Client No-Show handling."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from beanie import PydanticObjectId

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError
from app.models.appointment import Appointment, AppointmentSlot, AppointmentStatus
from app.models.astrologer import Astrologer
from app.models.user import User
from app.services import appointments as service


@pytest.mark.asyncio
async def test_mark_no_show_too_early():
    """Astrologer cannot mark No-Show before waiting at least 10 minutes into the session."""
    now = datetime.now(UTC)
    astro_user_id = PydanticObjectId()
    appointment = SimpleNamespace(
        id=PydanticObjectId(),
        astrologer_user_id=astro_user_id,
        user_id=PydanticObjectId(),
        status=AppointmentStatus.BOOKED,
        starts_at=now - timedelta(minutes=5),  # only 5 mins have passed
        ends_at=now + timedelta(minutes=25),
    )
    astro_user = SimpleNamespace(id=astro_user_id, role="astrologer")

    with pytest.raises(BadRequestError) as exc_info:
        await service.mark_no_show(appointment=appointment, by=astro_user)

    assert "wait at least 10 minutes" in str(exc_info.value.message)
    assert exc_info.value.error_code == "no_show_too_early"


@pytest.mark.asyncio
async def test_courtesy_reschedule_limit_reached():
    """An appointment cannot be courtesy rescheduled more than once."""
    astro_user_id = PydanticObjectId()
    appointment = SimpleNamespace(
        id=PydanticObjectId(),
        astrologer_user_id=astro_user_id,
        user_id=PydanticObjectId(),
        status=AppointmentStatus.BOOKED,
        rescheduled_count=1,  # already used
    )
    astro_user = SimpleNamespace(id=astro_user_id, role="astrologer")

    with pytest.raises(BadRequestError) as exc_info:
        await service.reschedule(
            appointment=appointment,
            by=astro_user,
            new_starts_at=datetime.now(UTC) + timedelta(days=1),
        )

    assert "already been rescheduled once" in str(exc_info.value.message)
    assert exc_info.value.error_code == "reschedule_limit_reached"


@pytest.mark.asyncio
async def test_courtesy_reschedule_forbidden_for_other_users():
    """Only the consulting astrologer or admin can grant a courtesy reschedule."""
    astro_user_id = PydanticObjectId()
    other_user_id = PydanticObjectId()
    appointment = SimpleNamespace(
        id=PydanticObjectId(),
        astrologer_user_id=astro_user_id,
        user_id=PydanticObjectId(),
        status=AppointmentStatus.BOOKED,
        rescheduled_count=0,
    )
    other_user = SimpleNamespace(id=other_user_id, role="user")

    with pytest.raises(ForbiddenError):
        await service.reschedule(
            appointment=appointment,
            by=other_user,
            new_starts_at=datetime.now(UTC) + timedelta(days=1),
        )


@pytest.mark.asyncio
async def test_cancel_active_for_astrologer():
    """Verify cancel_active_for_astrologer executes cleanly and handles active appointments."""
    admin_user = SimpleNamespace(id=PydanticObjectId(), role="admin", email="admin@astra.com")
    astro_id = PydanticObjectId()

    mock_query = MagicMock()
    mock_query.to_list = AsyncMock(return_value=[])
    mock_slot_query = MagicMock()
    mock_slot_query.delete = AsyncMock(return_value=None)

    with patch.object(Appointment, "find", return_value=mock_query):
        with patch.object(AppointmentSlot, "find", return_value=mock_slot_query):
            cancelled = await service.cancel_active_for_astrologer(astro_id, by=admin_user)
            assert cancelled == 0


@pytest.mark.asyncio
async def test_activate_and_resume_brahma_pause():
    """Verify astrologer can activate and resume Brahma Pause."""
    now = datetime.now(UTC)
    astro = SimpleNamespace(
        id=PydanticObjectId(),
        brahma_pause_until=None,
        brahma_pause_reason=None,
        brahma_pause_activated_at=None,
        availability=SimpleNamespace(is_online=True, last_seen_at=now),
        save=AsyncMock(),
        display_name="Acharya Sharma",
    )

    mock_query = MagicMock()
    mock_query.to_list = AsyncMock(return_value=[])

    with patch.object(Appointment, "find", return_value=mock_query):
        res = await service.activate_brahma_pause(
            astrologer=astro,
            duration_hours=6,
            reason="Spiritual meditation",
        )
        assert res["affected_appointments_count"] == 0
        assert astro.brahma_pause_until is not None
        assert astro.brahma_pause_reason == "Spiritual meditation"
        assert astro.availability.is_online is False

        # Resume
        res_resume = await service.resume_brahma_pause(astrologer=astro)
        assert "ended successfully" in res_resume["message"]
        assert astro.brahma_pause_until is None


@pytest.mark.asyncio
async def test_brahma_pause_rescue_action_refund():
    """Verify seeker can choose 100% instant refund during Brahma Pause."""
    user_id = PydanticObjectId()
    user = SimpleNamespace(id=user_id, role="user")
    appointment = SimpleNamespace(
        id=PydanticObjectId(),
        user_id=user_id,
        astrologer_user_id=PydanticObjectId(),
        status=AppointmentStatus.BOOKED,
        brahma_pause_affected=True,
        held_coins=500,
        held_status="held",
        deposit_coins=250,
        save=AsyncMock(),
    )

    mock_slot_query = MagicMock()
    mock_slot_query.delete = AsyncMock(return_value=None)

    with patch.object(AppointmentSlot, "find", return_value=mock_slot_query):
        with patch("app.services.wallet.release_held_coins", AsyncMock()) as mock_release:
            with patch("app.services.wallet.credit", AsyncMock()) as mock_credit:
                updated = await service.handle_brahma_pause_rescue_action(
                    appointment=appointment,
                    user=user,
                    action="refund",
                )
                assert updated.status == AppointmentStatus.CANCELLED
                assert updated.brahma_pause_affected is False
                assert mock_release.called
                assert mock_credit.called


@pytest.mark.asyncio
async def test_red_flag_appointment_and_blacklist():
    """Astrologer can red-flag an abusive client, capture escrow fee, and blacklist client."""
    from app.models.abuse_report import AbuseReport

    astro_user_id = PydanticObjectId()
    astro_prof_id = PydanticObjectId()
    client_user_id = PydanticObjectId()
    appt_id = PydanticObjectId()

    appointment = SimpleNamespace(
        id=appt_id,
        astrologer_id=astro_prof_id,
        astrologer_user_id=astro_user_id,
        user_id=client_user_id,
        status=AppointmentStatus.BOOKED,
        held_coins=600,
        held_status="held",
        call_session_id=None,
        save=AsyncMock(),
    )
    astro_prof = SimpleNamespace(
        id=astro_prof_id,
        user_id=astro_user_id,
        blacklisted_user_ids=[],
        save=AsyncMock(),
    )
    astro_user = SimpleNamespace(id=astro_user_id, role="astrologer")

    mock_slot_query = MagicMock()
    mock_slot_query.delete = AsyncMock(return_value=None)

    with patch.object(Appointment, "get", AsyncMock(return_value=appointment)):
        with patch.object(Astrologer, "get", AsyncMock(return_value=astro_prof)):
            with patch.object(AppointmentSlot, "find", return_value=mock_slot_query):
                with patch("app.services.wallet.capture_held_coins", AsyncMock()) as mock_capture:
                    with patch.object(AbuseReport, "save", AsyncMock(return_value=None)):
                        res = await service.red_flag_appointment(
                            appointment_id=appt_id,
                            by=astro_user,
                            reason="Severe verbal abuse and profanity",
                            notes="Client began insulting during session",
                            blacklist_client=True,
                            terminate_call=False,
                        )
                        assert res.abuse_flagged is True
                        assert res.abuse_reason == "Severe verbal abuse and profanity"
                        assert res.status == AppointmentStatus.COMPLETED
                        assert client_user_id in astro_prof.blacklisted_user_ids
                        assert mock_capture.called


@pytest.mark.asyncio
async def test_request_and_update_birth_time_rectification():
    """Astrologer requests BTR and client successfully submits rectified parameters."""
    astro_user_id = PydanticObjectId()
    astro_prof_id = PydanticObjectId()
    client_user_id = PydanticObjectId()
    appt_id = PydanticObjectId()

    appointment = SimpleNamespace(
        id=appt_id,
        astrologer_id=astro_prof_id,
        astrologer_user_id=astro_user_id,
        user_id=client_user_id,
        status=AppointmentStatus.BOOKED,
        starts_at=datetime.now(UTC) + timedelta(days=2),
        birth_details={"date_of_birth": "1992-05-14", "time_of_birth": "04:30"},
        btr_requested=False,
        save=AsyncMock(),
    )
    astro_user = SimpleNamespace(id=astro_user_id, role="astrologer")
    client_user = SimpleNamespace(id=client_user_id, role="user", email="seeker@example.com", full_name="John Doe")
    astro_prof = SimpleNamespace(id=astro_prof_id, display_name="Pandit Sharma")

    with patch.object(Appointment, "get", AsyncMock(return_value=appointment)):
        with patch.object(User, "get", AsyncMock(return_value=client_user)):
            with patch.object(Astrologer, "get", AsyncMock(return_value=astro_prof)):
                with patch("app.services.email.send_email", AsyncMock()):
                    # Astrologer requests BTR
                    res = await service.request_birth_time_rectification(
                        appointment_id=appt_id,
                        by=astro_user,
                        note="Birth time falls on Gemini-Cancer cusp. Please confirm exact minute.",
                    )
                    assert res.btr_requested is True
                    assert res.btr_request_note == "Birth time falls on Gemini-Cancer cusp. Please confirm exact minute."
                    assert res.btr_fulfilled is False

                    # Client fulfills BTR
                    with patch.object(User, "get", AsyncMock(return_value=astro_user)):
                        res2 = await service.update_birth_time_rectification(
                            appointment_id=appt_id,
                            by=client_user,
                            birth_date="1992-05-14",
                            birth_time="04:47 AM",
                            birth_place="Kolkata, India",
                            notes="Verified from hospital birth certificate.",
                        )
                        assert res2.btr_fulfilled is True
                        assert res2.birth_details["time_of_birth"] == "04:47 AM"
                        assert res2.birth_details["place_of_birth"] == "Kolkata, India"
                        assert res2.birth_details["client_btr_notes"] == "Verified from hospital birth certificate."


@pytest.mark.asyncio
async def test_booking_blocked_for_blacklisted_user():
    """Client cannot book an appointment if blacklisted by the astrologer."""
    client_id = PydanticObjectId()
    astro_id = PydanticObjectId()
    client = SimpleNamespace(id=client_id, role="user")
    astrologer = SimpleNamespace(
        id=astro_id,
        appointment=SimpleNamespace(enabled=True, price_paise=50000, block_minutes=30),
        blacklisted_user_ids=[client_id],
        brahma_pause_until=None,
    )
    mock_platform = SimpleNamespace(
        min_appointment_minutes=15,
        max_appointment_minutes=120,
        appointment_booking_days_ahead=30,
    )

    with patch("app.services.settings.get_settings", AsyncMock(return_value=mock_platform)):
        starts = (datetime.now(UTC) + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
        with pytest.raises(BadRequestError) as exc_info:
            await service._book_locked(
                user=client,
                astrologer=astrologer,
                starts_at=starts,
                minutes=30,
            )

        assert "unavailable for your account" in str(exc_info.value.message)
        assert exc_info.value.error_code == "client_blacklisted"



