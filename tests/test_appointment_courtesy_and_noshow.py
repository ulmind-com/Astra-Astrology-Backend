"""Unit tests for Courtesy Reschedule and Client No-Show handling."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from beanie import PydanticObjectId

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError
from app.models.appointment import Appointment, AppointmentSlot, AppointmentStatus
from app.models.astrologer import Astrologer
from app.models.enums import CallStatus
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


@pytest.mark.asyncio
async def test_session_extension_offer_and_clash_detection():
    """Astrologer offers in-chamber extension and detects clashing future bookings."""
    now = datetime.now(UTC)
    starts = now - timedelta(minutes=20)
    ends = starts + timedelta(minutes=30)
    appt_id = PydanticObjectId()
    astro_id = PydanticObjectId()
    astro_user_id = PydanticObjectId()
    client_id = PydanticObjectId()

    appointment = SimpleNamespace(
        id=appt_id,
        astrologer_id=astro_id,
        astrologer_user_id=astro_user_id,
        user_id=client_id,
        starts_at=starts,
        ends_at=ends,
        minutes=30,
        price_paise=60000,
        coins_per_rupee=1,
        status=AppointmentStatus.BOOKED,
        extension_offered=False,
        extension_offered_minutes=None,
        extension_cost_paise=0,
        extension_cost_coins=0,
        extension_offered_at=None,
        extension_status="none",
        save=AsyncMock(),
    )

    astrologer_profile = SimpleNamespace(
        id=astro_id,
        user_id=astro_user_id,
        display_name="Acharya Sharma",
        appointment=SimpleNamespace(price_paise=60000, block_minutes=30, buffer_minutes=5),
    )
    astrologer_user = SimpleNamespace(id=astro_user_id, role="astrologer")

    with patch("app.models.astrologer.Astrologer.get", AsyncMock(return_value=astrologer_profile)):
        with patch("app.services.realtime.publish_appointment_event", AsyncMock()) as mock_pub:
            # 1. Successful offer for 10 minutes
            with patch("app.models.appointment.AppointmentSlot.find") as mock_slot_find:
                mock_slot_find.return_value.first_or_none = AsyncMock(return_value=None)
                updated = await service.offer_session_extension(
                    appointment=appointment,
                    by=astrologer_user,
                    extra_minutes=10,
                )
                assert updated.extension_offered is True
                assert updated.extension_offered_minutes == 10
                assert updated.extension_status == "pending"
                assert updated.extension_cost_paise == 20000
                assert updated.extension_cost_coins == 200
                assert mock_pub.called

            # 2. Clash detected: another appointment booked in that window
            with patch("app.models.appointment.AppointmentSlot.find") as mock_slot_find:
                mock_slot_find.return_value.first_or_none = AsyncMock(
                    return_value=SimpleNamespace(starts_at=ends + timedelta(minutes=5))
                )
                with pytest.raises(BadRequestError) as exc_info:
                    await service.offer_session_extension(
                        appointment=appointment,
                        by=astrologer_user,
                        extra_minutes=15,
                    )
                assert "overlap" in str(exc_info.value.message).lower()
                assert exc_info.value.error_code == "extension_clash_with_future_booking"


@pytest.mark.asyncio
async def test_session_extension_accept_and_decline():
    """Client can decline or accept extension with atomic wallet debit and slot locking."""
    now = datetime.now(UTC)
    starts = now - timedelta(minutes=25)
    ends = starts + timedelta(minutes=30)
    appt_id = PydanticObjectId()
    astro_id = PydanticObjectId()
    astro_user_id = PydanticObjectId()
    client_id = PydanticObjectId()
    call_id = PydanticObjectId()

    appointment = SimpleNamespace(
        id=appt_id,
        astrologer_id=astro_id,
        astrologer_user_id=astro_user_id,
        user_id=client_id,
        starts_at=starts,
        ends_at=ends,
        minutes=30,
        price_paise=60000,
        coins_per_rupee=1,
        status=AppointmentStatus.BOOKED,
        call_session_id=call_id,
        extension_offered=True,
        extension_offered_minutes=10,
        extension_cost_paise=20000,
        extension_cost_coins=200,
        extension_offered_at=now,
        extension_status="pending",
        extension_total_extended_minutes=0,
        save=AsyncMock(),
    )

    client_user = SimpleNamespace(id=client_id, role="user")
    astrologer_profile = SimpleNamespace(
        id=astro_id,
        user_id=astro_user_id,
        display_name="Acharya Sharma",
        profile_image_url="https://example.com/avatar.jpg",
        appointment=SimpleNamespace(price_paise=60000, block_minutes=30, buffer_minutes=0),
    )

    call_session = SimpleNamespace(
        id=call_id,
        status=CallStatus.ACTIVE,
        requested_minutes=30,
        save=AsyncMock(),
    )

    with patch("app.models.astrologer.Astrologer.get", AsyncMock(return_value=astrologer_profile)):
        with patch("app.models.call.CallSession.get", AsyncMock(return_value=call_session)):
            with patch("app.services.realtime.publish_appointment_event", AsyncMock()):
                # 1. Decline
                appointment_declining = SimpleNamespace(
                    id=appt_id,
                    astrologer_id=astro_id,
                    astrologer_user_id=astro_user_id,
                    user_id=client_id,
                    starts_at=starts,
                    ends_at=ends,
                    minutes=30,
                    status=AppointmentStatus.BOOKED,
                    extension_offered=True,
                    extension_status="pending",
                    save=AsyncMock(),
                )
                declined = await service.handle_session_extension_action(
                    appointment=appointment_declining,
                    by=client_user,
                    action="decline",
                )
                assert declined.extension_status == "declined"
                assert declined.extension_offered is False

                # 2. Accept - Insufficient wallet balance
                with patch("app.services.wallet.get_or_create_wallet", AsyncMock(return_value=SimpleNamespace(available_coins=50))):
                    with pytest.raises(BadRequestError) as exc_info:
                        await service.handle_session_extension_action(
                            appointment=appointment,
                            by=client_user,
                            action="accept",
                        )
                    assert "Insufficient coins" in str(exc_info.value.message)
                    assert exc_info.value.error_code == "insufficient_balance"

                # 3. Accept - Success
                with patch("app.services.wallet.get_or_create_wallet", AsyncMock(return_value=SimpleNamespace(available_coins=500))):
                    with patch("app.services.wallet.debit", AsyncMock()) as mock_debit:
                        with patch("app.models.appointment.AppointmentSlot.find") as mock_slot_find:
                            mock_slot_find.return_value.to_list = AsyncMock(return_value=[])
                            with patch.object(AppointmentSlot, "get_pymongo_collection", MagicMock()):
                                with patch("app.models.appointment.AppointmentSlot.insert", AsyncMock()):
                                    accepted = await service.handle_session_extension_action(
                                        appointment=appointment,
                                        by=client_user,
                                        action="accept",
                                    )
                                    assert accepted.extension_status == "accepted"
                                    assert accepted.minutes == 40
                                    assert accepted.price_paise == 80000
                                    assert accepted.ends_at == ends + timedelta(minutes=10)
                                    assert mock_debit.called
                                    assert call_session.requested_minutes == 40
                                    assert call_session.save.called


@pytest.mark.asyncio
async def test_follow_up_pass_issue_and_messaging():
    """Astrologer issues 7-day remedy pass and client asks questions within quota."""
    now = datetime.now(UTC)
    appt_id = PydanticObjectId()
    astro_id = PydanticObjectId()
    astro_user_id = PydanticObjectId()
    client_id = PydanticObjectId()

    appointment = SimpleNamespace(
        id=appt_id,
        astrologer_id=astro_id,
        astrologer_user_id=astro_user_id,
        user_id=client_id,
        status=AppointmentStatus.COMPLETED,
        follow_up_pass_enabled=False,
        follow_up_window_days=7,
        follow_up_expires_at=None,
        follow_up_max_messages=2,
        follow_up_messages_used=0,
        follow_up_granted_at=None,
        follow_up_notes=None,
        follow_up_thread=[],
        save=AsyncMock(),
    )

    astrologer_user = SimpleNamespace(id=astro_user_id, role="astrologer", email="pandit@astra.com", full_name="Acharya Sharma")
    client_user = SimpleNamespace(id=client_id, role="user", email="seeker@gmail.com", full_name="Rahul Roy")

    with patch("app.services.realtime.publish_appointment_event", AsyncMock()):
        # 1. Astrologer issues 7-day pass with max 2 questions
        issued = await service.issue_follow_up_pass(
            appointment=appointment,
            by=astrologer_user,
            window_days=7,
            max_messages=2,
            notes="Please ask within 7 days for any mantra or gemstone clarity.",
        )
        assert issued.follow_up_pass_enabled is True
        assert issued.follow_up_window_days == 7
        assert issued.follow_up_max_messages == 2
        assert issued.follow_up_expires_at > now
        assert issued.follow_up_notes == "Please ask within 7 days for any mantra or gemstone clarity."

        # 2. Client sends question 1 -> succeeds
        appt, msg1 = await service.send_follow_up_message(
            appointment=issued,
            by=client_user,
            text="Panditji, which finger should I wear the Yellow Sapphire on?",
        )
        assert appt.follow_up_messages_used == 1
        assert len(appt.follow_up_thread) == 1
        assert msg1["sender_role"] == "user"
        assert "Yellow Sapphire" in msg1["text"]

        # 3. Astrologer replies -> succeeds and does not increment client quota
        appt, msg_reply = await service.send_follow_up_message(
            appointment=appt,
            by=astrologer_user,
            text="Wear it on the index finger of your right hand on a Thursday morning.",
        )
        assert appt.follow_up_messages_used == 1  # Astrologer reply does not consume quota
        assert len(appt.follow_up_thread) == 2
        assert msg_reply["sender_role"] == "astrologer"

        # 4. Client sends question 2 -> succeeds (quota becomes 2/2)
        appt, msg2 = await service.send_follow_up_message(
            appointment=appt,
            by=client_user,
            text="Should I fast on the day of energizing the stone?",
        )
        assert appt.follow_up_messages_used == 2

        # 5. Client attempts question 3 -> blocked by quota
        with pytest.raises(BadRequestError) as exc_info:
            await service.send_follow_up_message(
                appointment=appt,
                by=client_user,
                text="One more question please!",
            )
        assert "used all 2 complimentary questions" in str(exc_info.value.message)
        assert exc_info.value.error_code == "follow_up_limit_reached"

        # 6. Expired pass test
        appt.follow_up_messages_used = 0
        appt.follow_up_expires_at = now - timedelta(hours=1)  # expired
        with pytest.raises(BadRequestError) as exc_info:
            await service.send_follow_up_message(
                appointment=appt,
                by=client_user,
                text="Is the pass still working?",
            )
        assert "expired" in str(exc_info.value.message).lower()
        assert exc_info.value.error_code == "follow_up_expired"






