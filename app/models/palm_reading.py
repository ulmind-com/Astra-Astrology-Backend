"""Palm reading rules and stored readings.

The rules live in MongoDB rather than in code for the same reason the face-reading
rules do: the client's astrologer will want to correct wording and move thresholds,
and neither should need a deployment.

One thing differs from face reading and it matters. A face scan measures everything
it needs from the landmarks, so every rule can always be evaluated. A palm scan
cannot: fingerprint patterns, skin texture and mount height are in the client's
documents but are not readable from a phone photograph of a whole hand. Each rule
therefore declares what it requires, and a rule whose inputs were not measured is
*skipped and reported as skipped* rather than evaluated against a guess.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument


class PalmFeature(str, Enum):
    """What a rule is about. Grouped the way the client's documents are."""

    HAND_TYPE = "hand_type"
    PALM_SHAPE = "palm_shape"
    FINGERS = "fingers"
    FINGER_LENGTH = "finger_length"
    FINGER_DYNAMICS = "finger_dynamics"
    THUMB = "thumb"
    JUPITER_FINGER = "jupiter_finger"
    MERCURY_FINGER = "mercury_finger"
    PHALANGES = "phalanges"
    HEART_LINE = "heart_line"
    HEAD_LINE = "head_line"
    LIFE_LINE = "life_line"
    FATE_LINE = "fate_line"
    LINE_RELATIONSHIP = "line_relationship"
    CAREER_FORECAST = "career_forecast"
    RELATIONSHIP_FORECAST = "relationship_forecast"
    HEALTH_FORECAST = "health_forecast"
    MOUNTS_3D = "mounts_3d"
    FINGER_FLEXIBILITY_3D = "finger_flexibility_3d"
    PALM_HOLLOW_3D = "palm_hollow_3d"
    SUN_LINE = "sun_line"
    MARS_LINE = "mars_line"
    SACRED_MARKS = "sacred_marks"
    SKIN_VITALITY = "skin_vitality"


#: Human labels, used in the reading and in the admin list.
FEATURE_LABELS: dict[str, str] = {
    PalmFeature.HAND_TYPE: "Hand Element & Constitution",
    PalmFeature.PALM_SHAPE: "Palm Geometry & Proportion",
    PalmFeature.FINGERS: "Finger Proportion",
    PalmFeature.FINGER_LENGTH: "Mental Processing Pace",
    PalmFeature.FINGER_DYNAMICS: "Temperament & Social Stance",
    PalmFeature.THUMB: "Willpower & Logic (Thumb)",
    PalmFeature.JUPITER_FINGER: "Ambition & Authority (Jupiter)",
    PalmFeature.MERCURY_FINGER: "Communication & Commerce (Mercury)",
    PalmFeature.PHALANGES: "Phalangeal Orientation",
    PalmFeature.HEART_LINE: "Emotional Flow (Water Line)",
    PalmFeature.HEAD_LINE: "Intellect & Strategy (Air Line)",
    PalmFeature.LIFE_LINE: "Vitality & Roots (Earth Line)",
    PalmFeature.FATE_LINE: "Career & Destiny (Fire Line)",
    PalmFeature.LINE_RELATIONSHIP: "Mind-Heart Equilibrium",
    PalmFeature.CAREER_FORECAST: "Career & Financial Synthesis",
    PalmFeature.RELATIONSHIP_FORECAST: "Love & Marriage Synthesis",
    PalmFeature.HEALTH_FORECAST: "Vitality & Wellness Synthesis",
    PalmFeature.MOUNTS_3D: "3D Mount Topography & Planetary Energies",
    PalmFeature.FINGER_FLEXIBILITY_3D: "3D Joint Flexibility & Spontaneity",
    PalmFeature.PALM_HOLLOW_3D: "3D Plain of Mars & Core Fortitude",
    PalmFeature.SUN_LINE: "Sun Line (Fame, Public Eminence & Surya Radiance)",
    PalmFeature.MARS_LINE: "Mars Line (Guardian Vitality & Sanjeevani Shield)",
    PalmFeature.SACRED_MARKS: "Sacred Marks & Auspicious Yogas (Chihnas)",
    PalmFeature.SKIN_VITALITY: "Ayurvedic Skin Radiance & Prana Flush",
}


class Requirement(str, Enum):
    """What a rule needs before it can be judged at all.

    This is the mechanism that keeps the reading honest. A rule requiring
    FINGERPRINTS is never evaluated, because a phone photo of a whole hand does not
    resolve ridge patterns; it is listed as unavailable instead, with the reason.
    """

    #: Landmark geometry. Always available once a hand passes the quality gates.
    GEOMETRY = "geometry"
    #: A named crease must have been traced and accepted.
    HEART_LINE = "heart_line"
    HEAD_LINE = "head_line"
    LIFE_LINE = "life_line"
    FATE_LINE = "fate_line"
    #: Not obtainable from a single photograph. Rules needing these are carried so
    #: the client's material is not lost, and are reported as not assessable.
    FINGERPRINTS = "fingerprints"
    SKIN_TEXTURE = "skin_texture"
    MOUNT_HEIGHT = "mount_height"
    MINOR_MARKS = "minor_marks"


#: Why each unavailable requirement cannot be met, shown to the user verbatim so the
#: limitation is stated rather than hidden.
UNAVAILABLE_REASONS: dict[str, str] = {
    Requirement.FINGERPRINTS: (
        "Fingerprint patterns need far more detail than a photograph of a whole "
        "hand carries, so rules that depend on loops, whorls and arches are not assessed."
    ),
    Requirement.SKIN_TEXTURE: (
        "Skin texture cannot be judged reliably from an ordinary photograph, so "
        "rules describing silk, paper or grainy skin are not assessed."
    ),
    Requirement.MOUNT_HEIGHT: (
        "The height of the mounts is depth, and a single photograph has none, so "
        "rules about raised or flat mounts are not assessed."
    ),
    Requirement.MINOR_MARKS: (
        "Islands, crosses, stars and bars are smaller than a phone photograph of a "
        "whole hand resolves, so rules depending on them are not assessed."
    ),
}


class Condition(BaseModel):
    """One numeric test against a measured value.

    A rule fires only when every one of its conditions holds, so a rule with no
    conditions is a default and fires whenever nothing else in its feature did.
    """

    #: Key into the scan's measurements or crease values, e.g. "palm_aspect" or
    #: "heart_line.termination_zone".
    metric: str
    min: float | None = None
    max: float | None = None
    #: For non-numeric metrics such as a termination zone or the hand type.
    equals: str | None = None
    #: Substring match, for zone names like "upper Jupiter".
    contains: str | None = None

    def matches(self, values: dict[str, object]) -> bool:
        if self.metric not in values:
            return False
        raw = values[self.metric]

        if self.equals is not None or self.contains is not None:
            text = str(raw).lower()
            if self.equals is not None and text != self.equals.lower():
                return False
            if self.contains is not None and self.contains.lower() not in text:
                return False
            return True

        try:
            number = float(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
        if self.min is not None and number < self.min:
            return False
        if self.max is not None and number > self.max:
            return False
        return True


class PalmRule(TimestampedDocument):
    """One statement the reading can make, and what has to be true for it."""

    feature: str
    #: Short machine name for the option within the feature, e.g. "long_thumb".
    option: str
    #: Short human label, e.g. "Long thumb".
    label: str

    conditions: list[Condition] = Field(default_factory=list)
    #: What must have been measured for this rule to be judged at all.
    requires: list[str] = Field(default_factory=lambda: [Requirement.GEOMETRY.value])

    meaning: str = Field(max_length=4000)
    #: Area of life, for grouping in the UI.
    area: str | None = Field(default=None, max_length=40)

    #: Where in the client's material this came from, so any statement can be
    #: traced back and checked.
    source: str | None = Field(default=None, max_length=200)

    #: Higher wins when two rules in the same feature both match.
    priority: int = 0
    #: Fires when nothing else in the feature did.
    is_default: bool = False
    enabled: bool = True
    #: Set once the client's astrologer has checked the wording and thresholds.
    reviewed: bool = False

    class Settings:
        name = "palm_rules"
        indexes = [
            pymongo.IndexModel(
                [("feature", pymongo.ASCENDING), ("option", pymongo.ASCENDING)],
                name="palm_rule_feature_option",
                unique=True,
            ),
            pymongo.IndexModel([("enabled", pymongo.ASCENDING)], name="palm_rule_enabled"),
        ]


class ReadingSection(BaseModel):
    """One statement in a finished reading."""

    feature: str
    feature_label: str
    option: str
    label: str
    meaning: str
    area: str | None = None
    source: str | None = None
    #: Which measured values satisfied the rule, so a reader can see the basis.
    because: list[str] = Field(default_factory=list)


class SkippedFeature(BaseModel):
    """Something the client's material covers that this photo could not support."""

    feature: str
    feature_label: str
    requirement: str
    reason: str


class PalmReading(TimestampedDocument):
    """A stored reading.

    The rendered sections are stored alongside the measurements, not regenerated on
    read. A rule edit should change what new readings say, never silently rewrite
    what a user was told last month.
    """

    user_id: PydanticObjectId

    hand: str = Field(default="unknown", max_length=10)  # "Left" | "Right"
    measurements: dict[str, float] = Field(default_factory=dict)
    hand_type: dict = Field(default_factory=dict)
    creases: dict = Field(default_factory=dict)
    crease_relationships: dict = Field(default_factory=dict)

    #: 3D world scan coordinates, mount elevations, and depth metrics
    landmarks_3d: list[list[float]] = Field(default_factory=list)
    world_landmarks_mm: list[list[float]] = Field(default_factory=list)
    mount_elevations_3d: dict = Field(default_factory=dict)
    palm_cup_depth_mm: float = Field(default=0.0)
    finger_flexibility_3d: dict = Field(default_factory=dict)
    finger_inclinations_3d: dict = Field(default_factory=dict)

    secondary_lines: dict = Field(default_factory=dict)
    sacred_marks: list[dict] = Field(default_factory=list)
    timeline: list[dict] = Field(default_factory=list)
    skin_vitality: dict = Field(default_factory=dict)
    karmic_summary: dict = Field(default_factory=dict)

    sections: list[ReadingSection] = Field(default_factory=list)
    skipped: list[SkippedFeature] = Field(default_factory=list)

    #: The traced overlay, kept so the user can see what was read. Stored as a
    #: data URL alongside the reading rather than as a file, because it is only
    #: meaningful next to the reading it explains.
    overlay_image: str | None = None

    coins_charged: int = Field(default=0, ge=0)
    quality_score: float = Field(default=1.0, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)

    pipeline_version: str = Field(default="palm_cv_v1", max_length=40)

    #: Set when a retention period is configured, matching how chat retention works.
    expires_at: datetime | None = None

    class Settings:
        name = "palm_readings"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="palm_reading_user_recent",
            ),
            pymongo.IndexModel(
                [("expires_at", pymongo.ASCENDING)],
                name="palm_reading_ttl",
                expireAfterSeconds=0,
            ),
        ]
