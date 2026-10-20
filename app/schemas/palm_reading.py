"""Palm reading request and response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubmitPalmReadingRequest(BaseModel):
    """Payload sent by client when measurements are calculated directly on device."""

    hand_scanned: str = Field(default="left", description="'left' or 'right'")
    gender: str = Field(default="male", description="'male', 'female', etc.")
    measurements: dict[str, float]
    quality: float = Field(ge=0, le=1)


class ReadingSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    feature: str
    feature_label: str
    option: str
    label: str
    meaning: str
    area: str | None = None


class PalmReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    hand_scanned: str = "left"
    gender: str = "male"
    sections: list[ReadingSectionOut]
    coins_charged: int
    quality: float
    visualization_image: str | None = None
    created_at: datetime


class PalmReadingAvailability(BaseModel):
    """Availability and pricing information checked before starting camera."""

    enabled: bool
    coins: int
    balance_coins: int
    can_afford: bool
    min_quality: float
    recommended_hand_male: str = "left"
    recommended_hand_female: str = "right"


class PalmQualityChecksOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    is_valid: bool = True
    status: str = "ACCEPTED"
    hand_count: int = 1
    detected_hand: str | None = None  # 'Left' or 'Right'
    expected_hand: str = "left"
    is_hand_matched: bool = True
    hand_coverage_pct: float = 0.0
    blur_score: float = 0.0
    brightness_mean: float = 0.0
    contrast_std: float = 0.0
    fingers_extended: bool = True
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class PalmMeasurementDetailOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    value: float = 0.0
    description: str = ""
    status: str = "available"


class PalmScanResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scan_id: str
    status: str  # ACCEPTED, RETAKE_RECOMMENDED, REJECTED
    quality_score: float = 0.0
    quality_checks: PalmQualityChecksOut
    detected_hand: str | None = None
    expected_hand: str = "left"
    is_hand_matched: bool = True
    measurements: dict[str, float] = Field(default_factory=dict)
    measurement_details: dict[str, PalmMeasurementDetailOut] = Field(default_factory=dict)
    visualization_image: str | None = None
    reading: PalmReadingOut | None = None
    coins_charged: int = 0
    processing_duration_ms: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None


class PalmScanBase64Request(BaseModel):
    image: str = Field(description="Base64 encoded image string (data URL or raw base64)")
    gender: str = Field(default="male", description="Subject's gender ('male' or 'female')")
    hand: str = Field(default="auto", description="Preferred hand ('left', 'right', or 'auto')")


class PalmRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    feature: str
    option: str
    label: str
    conditions: list[dict]
    meaning: str
    area: str | None = None
    priority: int
    is_default: bool
    enabled: bool
    reviewed: bool


class PalmRuleUpdate(BaseModel):
    """Admin updating an interpretation or threshold band."""

    label: str | None = Field(default=None, max_length=120)
    meaning: str | None = Field(default=None, max_length=4000)
    area: str | None = Field(default=None, max_length=40)
    conditions: list[dict] | None = None
    priority: int | None = None
    enabled: bool | None = None
    reviewed: bool | None = None
