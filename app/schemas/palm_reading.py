"""Request and response shapes for palm reading."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PalmReadingAvailability(BaseModel):
    """Whether the feature can be used, and what it costs."""

    enabled: bool
    coins_required: int
    wallet_balance: int
    can_afford: bool
    #: Stated up front rather than discovered after paying.
    requires: list[str] = Field(default_factory=list)


class QualityCheckOut(BaseModel):
    name: str
    passed: bool
    value: float
    threshold: float
    message: str


class CreaseOut(BaseModel):
    name: str
    elemental_name: str
    found: bool
    strength: float = 0.0
    continuity: float = 0.0
    #: How far the traced path stands above the surrounding skin. The single most
    #: useful number for judging whether a trace is real.
    contrast: float = 0.0
    length: float = 0.0
    curvature: float = 0.0
    termination_zone: str | None = None
    path: list[list[float]] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReadingSectionOut(BaseModel):
    feature: str
    feature_label: str
    option: str
    label: str
    meaning: str
    area: str | None = None
    source: str | None = None
    because: list[str] = Field(default_factory=list)


class SkippedFeatureOut(BaseModel):
    feature: str
    feature_label: str
    requirement: str
    reason: str


class PalmScanResponse(BaseModel):
    """A completed scan and the reading drawn from it."""

    scan_id: str
    status: str
    message: str | None = None

    hand_detected: bool = False
    handedness: str | None = None
    quality_score: float = 0.0
    quality_checks: list[QualityCheckOut] = Field(default_factory=list)

    hand_type: dict[str, Any] = Field(default_factory=dict)
    measurements: dict[str, Any] = Field(default_factory=dict)
    measurement_details: dict[str, Any] = Field(default_factory=dict)

    creases: list[CreaseOut] = Field(default_factory=list)
    crease_relationships: dict[str, Any] = Field(default_factory=dict)

    sections: list[ReadingSectionOut] = Field(default_factory=list)
    #: What the client's material covers but this photo could not support, with
    #: the reason. Shown rather than omitted.
    skipped: list[SkippedFeatureOut] = Field(default_factory=list)

    #: 3D world scan coordinates, mount elevations, and depth metrics
    landmarks_3d: list[list[float]] = Field(default_factory=list)
    world_landmarks_mm: list[list[float]] = Field(default_factory=list)
    mount_elevations_3d: dict[str, float] = Field(default_factory=dict)
    palm_cup_depth_mm: float = 0.0
    finger_flexibility_3d: dict[str, Any] = Field(default_factory=dict)
    finger_inclinations_3d: dict[str, float] = Field(default_factory=dict)

    #: Astrological extensions: Secondary lines, Sacred marks, Timeline, Skin vitality, Loops, Marriage, Archetype, Medical, Kundli Sync
    secondary_lines: dict[str, Any] = Field(default_factory=dict)
    sacred_marks: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    skin_vitality: dict[str, Any] = Field(default_factory=dict)
    karmic_summary: dict[str, Any] = Field(default_factory=dict)
    dermatoglyphic_loops: list[dict[str, Any]] = Field(default_factory=list)
    marriage_patterns: list[dict[str, Any]] = Field(default_factory=list)
    temperament_archetype: dict[str, Any] = Field(default_factory=dict)
    medical_constitution: dict[str, Any] = Field(default_factory=dict)
    kundli_palm_sync: dict[str, Any] = Field(default_factory=dict)

    #: The traced overlay, so the reading can be checked against what was read.
    overlay_image: str | None = None
    response_image: str | None = None

    coins_charged: int = 0
    wallet_balance: int = 0
    processing_ms: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    reading_id: str | None = None


class PalmReadingOut(BaseModel):
    id: str
    hand: str
    hand_type: dict[str, Any] = Field(default_factory=dict)
    sections: list[ReadingSectionOut] = Field(default_factory=list)
    skipped: list[SkippedFeatureOut] = Field(default_factory=list)

    #: 3D world scan coordinates, mount elevations, and depth metrics
    landmarks_3d: list[list[float]] = Field(default_factory=list)
    world_landmarks_mm: list[list[float]] = Field(default_factory=list)
    mount_elevations_3d: dict[str, float] = Field(default_factory=dict)
    palm_cup_depth_mm: float = 0.0
    finger_flexibility_3d: dict[str, Any] = Field(default_factory=dict)
    finger_inclinations_3d: dict[str, float] = Field(default_factory=dict)

    secondary_lines: dict[str, Any] = Field(default_factory=dict)
    sacred_marks: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    skin_vitality: dict[str, Any] = Field(default_factory=dict)
    karmic_summary: dict[str, Any] = Field(default_factory=dict)
    dermatoglyphic_loops: list[dict[str, Any]] = Field(default_factory=list)
    marriage_patterns: list[dict[str, Any]] = Field(default_factory=list)
    temperament_archetype: dict[str, Any] = Field(default_factory=dict)
    medical_constitution: dict[str, Any] = Field(default_factory=dict)
    kundli_palm_sync: dict[str, Any] = Field(default_factory=dict)

    overlay_image: str | None = None
    coins_charged: int = 0
    quality_score: float = 1.0
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class PalmRuleOut(BaseModel):
    id: str
    feature: str
    option: str
    label: str
    meaning: str
    area: str | None = None
    source: str | None = None
    requires: list[str] = Field(default_factory=list)
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    priority: int = 0
    is_default: bool = False
    enabled: bool = True
    reviewed: bool = False


class PalmRuleUpdate(BaseModel):
    """What an admin may change. Thresholds and wording, not the rule's identity."""

    label: str | None = Field(default=None, max_length=120)
    meaning: str | None = Field(default=None, max_length=4000)
    area: str | None = Field(default=None, max_length=40)
    conditions: list[dict[str, Any]] | None = None
    priority: int | None = Field(default=None, ge=-100, le=100)
    enabled: bool | None = None
    reviewed: bool | None = None
