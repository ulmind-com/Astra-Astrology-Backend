"""Unit tests for In-Chamber Interactive Cosmic Whiteboard."""

from unittest.mock import AsyncMock, MagicMock, patch
from beanie import PydanticObjectId
import pytest

from app.models.call import CallSession
from app.models.enums import CallStatus, ConsultationMode, UserRole
from app.models.user import User
from app.models.whiteboard import CallWhiteboard
from app.schemas.whiteboard import LoadChartRequest, WhiteboardSyncRequest
from app.services.whiteboard import (
    calculate_charts_and_transits,
    clear_whiteboard,
    get_or_create_whiteboard,
    load_custom_chart,
    resolve_drishti,
    sync_whiteboard,
)


def test_drishti_aspect_rules():
    """Verifies classical Vedic Drishti aspect calculations."""
    # Jupiter: 5th, 7th, 9th
    jup_h1 = resolve_drishti("Jupiter", 1)
    assert jup_h1["aspects_houses"] == [5, 7, 9]
    assert jup_h1["nature"] == "auspicious"

    jup_h8 = resolve_drishti("Jupiter", 8)
    assert jup_h8["aspects_houses"] == [12, 2, 4]

    # Mars: 4th, 7th, 8th
    mars_h1 = resolve_drishti("Mars", 1)
    assert mars_h1["aspects_houses"] == [4, 7, 8]
    assert mars_h1["nature"] == "challenging"

    # Saturn: 3rd, 7th, 10th
    sat_h10 = resolve_drishti("Saturn", 10)
    assert sat_h10["aspects_houses"] == [12, 4, 7]
    assert sat_h10["nature"] == "challenging"

    # Venus / Moon / Sun / Mercury: 7th
    ven_h4 = resolve_drishti("Venus", 4)
    assert ven_h4["aspects_houses"] == [10]
    assert ven_h4["nature"] == "auspicious"


def test_calculate_charts_and_transits():
    """Verifies that natal chart and real-time transit positions are generated."""
    asc_sign, planets, transits = calculate_charts_and_transits(
        birth_date="1992-05-15",
        birth_time="14:30",
        lat=22.5726,
        lon=88.3639,
    )
    assert 1 <= asc_sign <= 12
    assert len(planets) >= 9
    assert len(transits) >= 9

    # Check planets have required fields
    sun = next((p for p in planets if p["name"] == "Sun"), None)
    assert sun is not None
    assert 1 <= sun["house_num"] <= 12
    assert 1 <= sun["sign_num"] <= 12
    assert sun["is_transit"] is False

    # Check transit planets have is_transit flag and relative house
    sat_tr = next((p for p in transits if p["name"] == "Saturn"), None)
    assert sat_tr is not None
    assert sat_tr["is_transit"] is True
    assert 1 <= sat_tr["house_num"] <= 12


@pytest.mark.asyncio
async def test_whiteboard_sync_and_strokes():
    """Verifies whiteboard state creation, stroke appending, and aspect synchronization."""
    call_id = PydanticObjectId()
    user_id = PydanticObjectId()
    astro_id = PydanticObjectId()
    astro_user_id = PydanticObjectId()

    mock_session = MagicMock()
    mock_session.id = call_id
    mock_session.user_id = user_id
    mock_session.astrologer_id = astro_id
    mock_session.astrologer_user_id = astro_user_id
    mock_session.appointment_id = None

    mock_user = MagicMock()
    mock_user.id = astro_user_id
    mock_user.role = UserRole.ASTROLOGER

    with patch.object(CallWhiteboard, "get_pymongo_collection", return_value=MagicMock()):
        mock_whiteboard = MagicMock(spec=CallWhiteboard)
        mock_whiteboard.call_id = call_id
        mock_whiteboard.user_id = user_id
        mock_whiteboard.astrologer_id = astro_id
        mock_whiteboard.astrologer_user_id = astro_user_id
        mock_whiteboard.is_open = False
        mock_whiteboard.chart_style = "north"
        mock_whiteboard.active_tab = "d1"
        mock_whiteboard.drishti = None
        mock_whiteboard.highlighted_houses = []
        mock_whiteboard.strokes = []
        mock_whiteboard.version = 1
        mock_whiteboard.save = AsyncMock(return_value=None)

        with patch.object(CallSession, "get", new_callable=AsyncMock, return_value=mock_session), \
             patch.object(CallWhiteboard, "find_one", new_callable=AsyncMock, return_value=mock_whiteboard), \
             patch("app.services.realtime._broadcast") as mock_broadcast:

            # 1. Sync toggle & aspect
            synced = await sync_whiteboard(
                call_id=call_id,
                user=mock_user,
                payload=WhiteboardSyncRequest(
                    is_open=True,
                    active_tab="transit",
                    drishti={"planet": "Jupiter", "from_house": 1},
                    highlighted_houses=[1, 5, 7, 9],
                    append_stroke={"tool": "pen", "color": "#F59E0B", "points": [{"x": 10, "y": 20}]},
                ),
            )

            assert synced.is_open is True
            assert synced.active_tab == "transit"
            assert synced.drishti["aspects_houses"] == [5, 7, 9]
            assert synced.highlighted_houses == [1, 5, 7, 9]
            assert len(synced.strokes) == 1
            assert synced.version == 2

            # Verify broadcast to peer was dispatched
            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args
            assert call_args[0][0]["type"] == "whiteboard_sync"
            assert call_args[1]["to_user"] == str(user_id)

            # 2. Clear whiteboard
            mock_broadcast.reset_mock()
            cleared = await clear_whiteboard(call_id=call_id, user=mock_user)
            assert len(cleared.strokes) == 0
            assert cleared.drishti is None
            assert cleared.highlighted_houses == []
            mock_broadcast.assert_called_once()
