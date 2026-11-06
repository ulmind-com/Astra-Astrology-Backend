"""Pydantic schemas for the in-chamber Interactive Cosmic Whiteboard."""

from typing import Any
from pydantic import BaseModel, Field


class WhiteboardStrokePoint(BaseModel):
    x: float
    y: float


class WhiteboardStroke(BaseModel):
    tool: str = "pen"  # pen, highlighter, arrow, laser, stamp
    color: str = "#F59E0B"
    width: int = 3
    points: list[WhiteboardStrokePoint] = Field(default_factory=list)
    symbol: str | None = None
    timestamp: float | None = None


class WhiteboardSyncRequest(BaseModel):
    is_open: bool | None = None
    chart_style: str | None = None  # north, south, east, wheel
    active_tab: str | None = None  # d1, d9, transit, freehand
    drishti: dict[str, Any] | None = None
    highlighted_houses: list[int] | None = None
    strokes: list[dict[str, Any]] | None = None
    append_stroke: dict[str, Any] | None = None
    clear_strokes: bool | None = None


class LoadChartRequest(BaseModel):
    name: str | None = None
    date: str = Field(description="YYYY-MM-DD")
    time: str = Field(default="12:00", description="HH:MM")
    place: str = Field(default="Kolkata, West Bengal, India")
    latitude: float = Field(default=22.5726)
    longitude: float = Field(default=88.3639)
    timezone_offset: float = Field(default=5.5)


class WhiteboardOut(BaseModel):
    id: str
    call_id: str
    appointment_id: str | None = None
    is_open: bool = False
    chart_style: str = "north"
    active_tab: str = "d1"

    client_name: str | None = None
    birth_date: str | None = None
    birth_time: str | None = None
    birth_place: str | None = None

    asc_sign_num: int = 1
    planets: list[dict[str, Any]] = Field(default_factory=list)
    transit_planets: list[dict[str, Any]] = Field(default_factory=list)

    drishti: dict[str, Any] | None = None
    highlighted_houses: list[int] = Field(default_factory=list)
    strokes: list[dict[str, Any]] = Field(default_factory=list)

    version: int = 1
