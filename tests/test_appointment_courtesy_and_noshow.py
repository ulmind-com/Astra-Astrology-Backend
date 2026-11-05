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

