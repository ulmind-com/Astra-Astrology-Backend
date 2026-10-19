"""Face reading request and response shapes."""

from datetime import datetime

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SubmitReadingRequest(BaseModel):
    """What the browser sends after measuring a face.

    Measurements only — never an image. Each is a ratio against the subject's
    own face, so nothing here identifies anybody.
    """

    measurements: dict[str, float]
    # How square-on and well-lit the capture was, 0–1, decided on the device.
    quality: float = Field(ge=0, le=1)


class ReadingSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    feature: str
    feature_label: str
    option: str
    label: str
    meaning: str
    area: str | None = None


class FaceReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    sections: list[ReadingSectionOut]
    coins_charged: int
    quality: float
    created_at: datetime


class FaceReadingAvailability(BaseModel):
    """What it costs and whether it is on, before anyone starts."""

    enabled: bool
    coins: int
    balance_coins: int
    can_afford: bool
    min_quality: float


class HeadPoseOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    is_frontal: bool = True

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "yaw" not in d and "yaw_deg" in d:
                d["yaw"] = d["yaw_deg"]
            if "pitch" not in d and "pitch_deg" in d:
                d["pitch"] = d["pitch_deg"]
            if "roll" not in d and "roll_deg" in d:
                d["roll"] = d["roll_deg"]
            return d
        return data


class QualityChecksOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    is_valid: bool = True
    status: str = "ACCEPTED"
    face_count: int = 1
    face_coverage_pct: float = 0.0
    blur_score: float = 0.0
    brightness_mean: float = 0.0
    contrast_std: float = 0.0
    lighting_symmetry_ratio: float = 1.0
    head_pose: HeadPoseOut | None = None
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "blur_score" not in d and "sharpness_score" in d:
                d["blur_score"] = d["sharpness_score"]
            if "face_coverage_pct" not in d and "face_coverage_ratio" in d:
                d["face_coverage_pct"] = round(d["face_coverage_ratio"] * 100.0, 2)
            return d
        return data


class MeasurementDetailOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    value: float = 0.0
    description: str = ""
    formula: str = ""
    landmarks_used: list[int] = Field(default_factory=list)
    status: str = "available"


class FaceScanResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scan_id: str
    status: str
    quality_score: float = 0.0
    quality_checks: QualityChecksOut
    head_pose: HeadPoseOut | None = None
    measurements: dict[str, float] = Field(default_factory=dict)
    measurement_details: dict[str, MeasurementDetailOut] = Field(default_factory=dict)
    measurement_status: str = "valid"
    visualization_image: str | None = None
    reading: FaceReadingOut | None = None
    coins_charged: int = 0
    landmark_mapping_version: str = "canonical_478_v1"
    model_version: str = "mediapipe_tasks_vision_1.1.1"
    processing_duration_ms: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None


class FaceScanBase64Request(BaseModel):
    image: str = Field(description="Base64 encoded image string (data URL or raw base64)")


class RuleOut(BaseModel):
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


class RuleUpdate(BaseModel):
    """An admin correcting a rule. Any field may be sent on its own."""

    label: str | None = Field(default=None, max_length=120)
    meaning: str | None = Field(default=None, max_length=4000)
    area: str | None = Field(default=None, max_length=40)
    conditions: list[dict] | None = None
    priority: int | None = None
    enabled: bool | None = None
    reviewed: bool | None = None

