"""Call Whiteboard document model for in-chamber interactive cosmic chart consultations."""

from datetime import datetime
from typing import Any

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from app.models.base import TimestampedDocument


class CallWhiteboard(TimestampedDocument):
    """Stores the active cosmic whiteboard state (Kundali, Gochar transit, Drishti, and drawings)."""

    call_id: PydanticObjectId
    appointment_id: PydanticObjectId | None = None
    user_id: PydanticObjectId
    astrologer_id: PydanticObjectId
    astrologer_user_id: PydanticObjectId

    is_open: bool = False
    chart_style: str = "north"  # north, south, east, wheel
    active_tab: str = "d1"  # d1 (Lagna), d9 (Navamsha), transit (Gochar), freehand

    # Seeker chart metadata
    client_name: str | None = None
    birth_date: str | None = None
    birth_time: str | None = None
    birth_place: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    # Chart calculation state
    asc_sign_num: int = 1
    planets: list[dict[str, Any]] = Field(default_factory=list)
    transit_planets: list[dict[str, Any]] = Field(default_factory=list)

    # Active interactive annotations
    drishti: dict[str, Any] | None = None  # active planetary aspect ray info
    highlighted_houses: list[int] = Field(default_factory=list)
    strokes: list[dict[str, Any]] = Field(default_factory=list)  # vector lines, arrows, marks

    version: int = 1

    class Settings:
        name = "call_whiteboards"
        indexes = [
            pymongo.IndexModel(
                [("call_id", pymongo.ASCENDING)],
                name="whiteboard_call_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("appointment_id", pymongo.ASCENDING)],
                name="whiteboard_appointment",
            ),
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING)],
                name="whiteboard_user",
            ),
        ]
