"""Face reading request and response shapes."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubmitReadingRequest(BaseModel):
    """What the browser sends after measuring a face.

    Measurements only — never an image. Each is a ratio against the subject's
    own face, so nothing here identifies anybody.
    """

    measurements: dict[str, float]
    # How square-on and well-lit the capture was, 0–1, decided on the device.
    quality: float = Field(ge=0, le=1)


class ReadingSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature: str
    feature_label: str
    option: str
    label: str
    meaning: str
    area: str | None = None


class FaceReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    yaw: float
    pitch: float
    roll: float
    is_frontal: bool


class QualityChecksOut(BaseModel):
    is_valid: bool
    status: str
    face_count: int
    face_coverage_pct: float
    blur_score: float
    brightness_mean: float
    contrast_std: float
    lighting_symmetry_ratio: float
    head_pose: HeadPoseOut | None = None
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class MeasurementDetailOut(BaseModel):
    name: str
    value: float
    description: str
    formula: str
    landmarks_used: list[int]
    status: str = "available"


class FaceScanResponse(BaseModel):
    scan_id: str
    status: str
    quality_score: float
    quality_checks: QualityChecksOut
    head_pose: HeadPoseOut | None = None
    measurements: dict[str, float] = Field(default_factory=dict)
    measurement_details: dict[str, MeasurementDetailOut] = Field(default_factory=dict)
    measurement_status: str
    visualization_image: str | None = None
    reading: FaceReadingOut | None = None
    coins_charged: int = 0
    landmark_mapping_version: str
    model_version: str
    processing_duration_ms: float
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

