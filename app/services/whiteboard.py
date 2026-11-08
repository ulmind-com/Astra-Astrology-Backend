"""Service for In-Chamber Cosmic Whiteboard state management, Vedic chart calculation,
real-time Drishti (aspect) resolution, and Gochar (transit) computation.
"""

from datetime import datetime, timezone
from typing import Any

from beanie import PydanticObjectId
from loguru import logger

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.appointment import Appointment
from app.models.call import CallSession
from app.models.user import User
from app.models.whiteboard import CallWhiteboard
from app.schemas.astrology import KundliCalculateRequest
from app.schemas.whiteboard import LoadChartRequest, WhiteboardSyncRequest
from app.services import realtime
from app.services.astrology import kundli_service


# Classical Vedic Drishti rules (Parashara)
DRISHTI_RULES: dict[str, list[int]] = {
    "Sun": [7],
    "Moon": [7],
    "Mars": [4, 7, 8],
    "Mercury": [7],
    "Jupiter": [5, 7, 9],
    "Venus": [7],
    "Saturn": [3, 7, 10],
    "Rahu": [5, 7, 9],
    "Ketu": [5, 7, 9],
}

PLANET_BENEFIC_STATUS: dict[str, str] = {
    "Jupiter": "auspicious",
    "Venus": "auspicious",
    "Moon": "auspicious",
    "Mercury": "neutral",
    "Sun": "challenging",
    "Mars": "challenging",
    "Saturn": "challenging",
    "Rahu": "challenging",
    "Ketu": "challenging",
}


def resolve_drishti(planet_name: str, from_house: int) -> dict[str, Any]:
    """Calculates the aspected houses and qualitative nature for any planet."""
    aspect_offsets = DRISHTI_RULES.get(planet_name, [7])
    aspects_houses: list[int] = []
    for offset in aspect_offsets:
        target = ((from_house - 1 + offset - 1) % 12) + 1
        aspects_houses.append(target)

    nature = PLANET_BENEFIC_STATUS.get(planet_name, "neutral")

    label_en = f"{planet_name}'s Vedic Drishti ({', '.join(str(h) for h in aspects_houses)}th Houses)"
    label_bn = f"{planet_name}-এর বৈদিক দৃষ্টি ({', '.join(str(h) for h in aspects_houses)} নম্বর ভাব)"

    return {
        "planet": planet_name,
        "from_house": from_house,
        "aspect_offsets": aspect_offsets,
        "aspects_houses": aspects_houses,
        "nature": nature,
        "label_en": label_en,
        "label_bn": label_bn,
    }


def _parse_date_time(date_str: str, time_str: str) -> tuple[int, int, int, int, int]:
    """Extracts year, month, day, hour, minute from standard strings."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        year, month, day = dt.year, dt.month, dt.day
    except Exception:
        now = datetime.now(timezone.utc)
        year, month, day = now.year, now.month, now.day

    hour, minute = 12, 0
    if time_str:
        try:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except Exception:
            hour, minute = 12, 0

    return year, month, day, hour, minute


def calculate_charts_and_transits(
    birth_date: str,
    birth_time: str,
    lat: float = 22.5726,
    lon: float = 88.3639,
    tz_offset: float = 5.5,
) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]]]:
    """Computes client's Natal D1/D9 chart and Real-Time Gochar (Transit) Chart."""
    y, m, d, h, mn = _parse_date_time(birth_date, birth_time)

    # 1. Natal Kundli
    natal_req = KundliCalculateRequest(
        day=d,
        month=m,
        year=y,
        hour=h,
        minute=mn,
        period="24H",
        latitude=lat,
        longitude=lon,
        timezone_offset=tz_offset,
        name="Seeker",
    )
    natal_res = kundli_service.calculate_kundli(natal_req)

    asc_sign_num = natal_res.d1_asc_sign
    planets_data: list[dict[str, Any]] = []
    for p in natal_res.d1_planets:
        planets_data.append(
            {
                "name": p.name,
                "symbol": getattr(p, "symbol", p.name[:2]),
                "code": getattr(p, "code", p.name[:2]),
                "sign_num": p.sign_num,
                "house_num": p.house_num,
                "d9_sign_num": getattr(p, "d9_sign_num", p.sign_num),
                "d9_house_num": getattr(p, "d9_house_num", p.house_num),
                "is_retrograde": getattr(p, "is_retrograde", False),
                "degree": p.degree,
                "is_transit": False,
            }
        )

    # 2. Current Real-Time Gochar (Transit)
    now = datetime.now(timezone.utc)
    transit_req = KundliCalculateRequest(
        day=now.day,
        month=now.month,
        year=now.year,
        hour=now.hour,
        minute=now.minute,
        period="24H",
        latitude=lat,
        longitude=lon,
        timezone_offset=tz_offset,
        name="Transit",
    )
    transit_res = kundli_service.calculate_kundli(transit_req)

    transit_data: list[dict[str, Any]] = []
    for p in transit_res.d1_planets:
        # Natal Lagna determines the transit house position
        transit_house = ((p.sign_num - asc_sign_num) % 12) + 1
        transit_data.append(
            {
                "name": p.name,
                "symbol": getattr(p, "symbol", p.name[:2]),
                "code": getattr(p, "code", p.name[:2]),
                "sign_num": p.sign_num,
                "house_num": transit_house,
                "is_retrograde": getattr(p, "is_retrograde", False),
                "degree": p.degree,
                "is_transit": True,
            }
        )

    return asc_sign_num, planets_data, transit_data


async def get_or_create_whiteboard(
    call_id: PydanticObjectId,
    user: User,
) -> CallWhiteboard:
    """Retrieves or auto-initializes the Cosmic Whiteboard for this live call."""
    session = await CallSession.get(call_id)
    if not session:
        raise NotFoundError("Call session not found.", error_code="call_not_found")

    if user.id not in (session.user_id, session.astrologer_user_id) and user.role != "admin":
        raise ForbiddenError("Not authorized to access this call's whiteboard.")

    whiteboard = await CallWhiteboard.find_one({"call_id": session.id})
    if whiteboard:
        return whiteboard

    # Initialize new whiteboard with client birth details
    client_name = "Seeker"
    birth_date = "1995-01-01"
    birth_time = "12:00"
    birth_place = "Kolkata, West Bengal, India"
    lat, lon, tz = 22.5726, 88.3639, 5.5

    # 1. Try appointment birth details if appointment session
    if session.appointment_id:
        apt = await Appointment.get(session.appointment_id)
        if apt:
            if apt.birth_details:
                birth_date = apt.birth_details.get("birth_date") or apt.birth_details.get("date") or birth_date
                birth_time = apt.birth_details.get("birth_time") or apt.birth_details.get("time") or birth_time
                birth_place = apt.birth_details.get("birth_place") or apt.birth_details.get("place") or birth_place
                lat = apt.birth_details.get("latitude", lat)
                lon = apt.birth_details.get("longitude", lon)
                tz = apt.birth_details.get("timezone_offset", tz)

    # 2. Try user profile birth details
    client_user = await User.get(session.user_id)
    if client_user:
        client_name = client_user.full_name
        if client_user.birth and client_user.birth.is_chart_ready:
            birth_date = str(client_user.birth.date_of_birth or birth_date)
            birth_time = client_user.birth.time_of_birth or birth_time
            birth_place = client_user.birth.place or birth_place
            lat = client_user.birth.latitude or lat
            lon = client_user.birth.longitude or lon
            tz = client_user.birth.timezone_offset or tz

    try:
        asc_sign, planets, transits = calculate_charts_and_transits(birth_date, birth_time, lat, lon, tz)
    except Exception as e:
        logger.warning("Could not calculate initial chart for whiteboard: {}", e)
        asc_sign, planets, transits = 1, [], []

    whiteboard = CallWhiteboard(
        call_id=session.id,
        appointment_id=session.appointment_id,
        user_id=session.user_id,
        astrologer_id=session.astrologer_id,
        astrologer_user_id=session.astrologer_user_id,
        is_open=False,
        chart_style="north",
        active_tab="d1",
        client_name=client_name,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=birth_place,
        latitude=lat,
        longitude=lon,
        asc_sign_num=asc_sign,
        planets=planets,
        transit_planets=transits,
        version=1,
    )
    await whiteboard.insert()
    return whiteboard


async def sync_whiteboard(
    call_id: PydanticObjectId,
    user: User,
    payload: WhiteboardSyncRequest,
) -> CallWhiteboard:
    """Updates whiteboard state and immediately broadcasts changes to the peer."""
    session = await CallSession.get(call_id)
    if not session:
        raise NotFoundError("Call session not found.")

    if user.id not in (session.user_id, session.astrologer_user_id) and user.role != "admin":
        raise ForbiddenError("Not authorized to sync this whiteboard.")

    whiteboard = await CallWhiteboard.find_one({"call_id": session.id})
    if not whiteboard:
        whiteboard = await get_or_create_whiteboard(call_id, user)

    # Apply updates
    if payload.is_open is not None:
        whiteboard.is_open = payload.is_open
    if payload.chart_style is not None:
        whiteboard.chart_style = payload.chart_style
    if payload.active_tab is not None:
        whiteboard.active_tab = payload.active_tab
    if payload.highlighted_houses is not None:
        whiteboard.highlighted_houses = payload.highlighted_houses

    # Drishti aspect update
    if payload.drishti is not None:
        if payload.drishti.get("clear"):
            whiteboard.drishti = None
        elif "planet" in payload.drishti and "from_house" in payload.drishti:
            whiteboard.drishti = resolve_drishti(
                payload.drishti["planet"], int(payload.drishti["from_house"])
            )
        else:
            whiteboard.drishti = payload.drishti

    # Stroke handling
    if payload.clear_strokes:
        whiteboard.strokes = []
    elif payload.strokes is not None:
        whiteboard.strokes = payload.strokes
    elif payload.append_stroke is not None:
        whiteboard.strokes.append(payload.append_stroke)

    whiteboard.version += 1
    await whiteboard.save()

    # Determine peer user id for realtime WebSocket push
    peer_id = str(session.user_id if user.id == session.astrologer_user_id else session.astrologer_user_id)
    sync_data = {
        "call_id": str(session.id),
        "is_open": whiteboard.is_open,
        "chart_style": whiteboard.chart_style,
        "active_tab": whiteboard.active_tab,
        "drishti": whiteboard.drishti,
        "highlighted_houses": whiteboard.highlighted_houses,
        "strokes": whiteboard.strokes,
        "version": whiteboard.version,
    }
    realtime._broadcast({"type": "whiteboard_event", "data": sync_data}, to_user=peer_id)
    realtime._broadcast({"type": "whiteboard_sync", "data": sync_data}, to_user=peer_id)

    return whiteboard


async def clear_whiteboard(
    call_id: PydanticObjectId,
    user: User,
) -> CallWhiteboard:
    """Clears all strokes and highlighted aspects on the whiteboard."""
    return await sync_whiteboard(
        call_id,
        user,
        WhiteboardSyncRequest(clear_strokes=True, drishti={"clear": True}, highlighted_houses=[]),
    )


async def load_custom_chart(
    call_id: PydanticObjectId,
    user: User,
    payload: LoadChartRequest,
) -> CallWhiteboard:
    """Recalculates client chart and current transits for custom birth details."""
    session = await CallSession.get(call_id)
    if not session:
        raise NotFoundError("Call session not found.")

    if user.id not in (session.user_id, session.astrologer_user_id) and user.role != "admin":
        raise ForbiddenError("Not authorized to modify chart on this whiteboard.")

    whiteboard = await CallWhiteboard.find_one({"call_id": session.id})
    if not whiteboard:
        whiteboard = await get_or_create_whiteboard(call_id, user)

    asc_sign, planets, transits = calculate_charts_and_transits(
        payload.date,
        payload.time,
        payload.latitude,
        payload.longitude,
        payload.timezone_offset,
    )

    whiteboard.client_name = payload.name or whiteboard.client_name
    whiteboard.birth_date = payload.date
    whiteboard.birth_time = payload.time
    whiteboard.birth_place = payload.place
    whiteboard.latitude = payload.latitude
    whiteboard.longitude = payload.longitude
    whiteboard.asc_sign_num = asc_sign
    whiteboard.planets = planets
    whiteboard.transit_planets = transits
    whiteboard.strokes = []
    whiteboard.drishti = None
    whiteboard.highlighted_houses = []
    whiteboard.version += 1
    await whiteboard.save()

    peer_id = str(session.user_id if user.id == session.astrologer_user_id else session.astrologer_user_id)
    chart_data = {
        "call_id": str(session.id),
        "client_name": whiteboard.client_name,
        "asc_sign_num": whiteboard.asc_sign_num,
        "planets": whiteboard.planets,
        "transit_planets": whiteboard.transit_planets,
        "version": whiteboard.version,
    }
    realtime._broadcast({"type": "whiteboard_event", "data": chart_data}, to_user=peer_id)
    realtime._broadcast({"type": "whiteboard_chart_reloaded", "data": chart_data}, to_user=peer_id)

    return whiteboard
