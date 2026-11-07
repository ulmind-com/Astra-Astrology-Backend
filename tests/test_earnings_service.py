from datetime import UTC, datetime
from zoneinfo import ZoneInfo
import pytest

from app.services.earnings import _windows

IST = ZoneInfo("Asia/Kolkata")


def test_earnings_windows_ist_midnight():
    # Simulate Nov 8, 2026 at 02:00:00 AM IST (which is Nov 7, 2026 20:30:00 UTC)
    simulated_now_ist = datetime(2026, 11, 8, 2, 0, 0, tzinfo=IST)
    simulated_now_utc = simulated_now_ist.astimezone(UTC)

    windows = _windows(simulated_now_utc)
    today_boundary = windows["today"]

    # Today boundary must be exactly 2026-11-08 00:00:00 IST in UTC
    expected_midnight_ist = datetime(2026, 11, 8, 0, 0, 0, tzinfo=IST)
    expected_midnight_utc = expected_midnight_ist.astimezone(UTC)

    assert today_boundary == expected_midnight_utc

    # A consultation at 01:00 AM IST on Nov 8 (Nov 7 19:30 UTC)
    consultation_at_1am = datetime(2026, 11, 8, 1, 0, 0, tzinfo=IST).astimezone(UTC)
    assert consultation_at_1am >= today_boundary, "1 AM IST consultation must fall in today"

    # A consultation at 11:59 PM IST on Nov 7 (Nov 7 18:29 UTC)
    consultation_yesterday = datetime(2026, 11, 7, 23, 59, 0, tzinfo=IST).astimezone(UTC)
    assert consultation_yesterday < today_boundary, "Yesterday 11:59 PM IST must NOT fall in today"


def test_earnings_windows_at_5am_ist():
    # Simulate Nov 8, 2026 at 05:20:00 AM IST (before 5:30 AM UTC midnight)
    simulated_early_ist = datetime(2026, 11, 8, 5, 20, 0, tzinfo=IST)
    windows_520 = _windows(simulated_early_ist)

    # Simulate Nov 8, 2026 at 05:40:00 AM IST (after 5:30 AM UTC midnight)
    simulated_later_ist = datetime(2026, 11, 8, 5, 40, 0, tzinfo=IST)
    windows_540 = _windows(simulated_later_ist)

    # Both must have the identical 'today' start boundary because they are both on Nov 8 IST!
    assert windows_520["today"] == windows_540["today"], "IST day boundary must not jump at 5:30 AM IST"
