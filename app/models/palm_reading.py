"""Palm reading: rules, measurements, and readings produced from them.

In Samudrik Shastra (হস্তরেখা বিচার / Palmistry), the lines, mounts, and proportions
of the hand reveal a person's temperament, destiny, relationships, and health tendencies.

As per authentic Shastra traditions:
- For males: the Left hand reflects inherent destiny, karmic blueprint, and subconscious potential.
- For females: the Right hand reflects active karmic manifestation and life journey.
- Both active and passive hands offer deep esoteric insights.

Like face reading, the rules live in the database so that astrologers can calibrate
thresholds and interpretations without requiring server redeployments.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument


class PalmFeature:
    """The anatomical and chiromantic features a palm reading is built from."""

    HAND_TYPE = "hand_type"
    HEART_LINE = "heart_line"
    HEAD_LINE = "head_line"
    LIFE_LINE = "life_line"
    FATE_LINE = "fate_line"
    SUN_LINE = "sun_line"
    MOUNTS = "mounts"
    FINGERS = "fingers"

    ALL = [
        HAND_TYPE,
        HEART_LINE,
        HEAD_LINE,
        LIFE_LINE,
        FATE_LINE,
        SUN_LINE,
        MOUNTS,
        FINGERS,
    ]

    LABELS = {
        HAND_TYPE: "হস্ত প্রকার ও পঞ্চভূত (Hand Type & Element)",
        HEART_LINE: "হৃদয় রেখা (Heart Line / প্রেম ও আবেগ)",
        HEAD_LINE: "মস্তিষ্ক রেখা (Head Line / মেধা ও বিচারবুদ্ধি)",
        LIFE_LINE: "জীবন রেখা (Life Line / স্বাস্থ্য ও জীবনীশক্তি)",
        FATE_LINE: "ভাগ্য রেখা (Fate Line / ভাগ্য ও কর্মজীবন)",
        SUN_LINE: "রবি রেখা (Sun Line / খ্যাতি ও প্রতিষ্ঠা)",
        MOUNTS: "গ্রহ পর্বত (Planetary Mounts / বৃহস্পতি, শুক্র ও চন্দ্র)",
        FINGERS: "অঙ্গুলি বিচার (Fingers & Thumb / ইচ্ছাশক্তি ও ব্যক্তিত্ব)",
    }


class Condition(BaseModel):
    """When this rule applies.

    One measurement against a band. `min` is inclusive, `max` exclusive, and
    either may be null for open-ended intervals.
    """

    metric: str
    min: float | None = None
    max: float | None = None

    def matches(self, measurements: dict[str, float]) -> bool:
        value = measurements.get(self.metric)
        if value is None:
            return False
        if self.min is not None and value < self.min:
            return False
        return not (self.max is not None and value >= self.max)


class PalmRule(TimestampedDocument):
    """One astrological option of one palm feature, and when to apply it."""

    feature: str
    option: str
    label: str

    conditions: list[Condition] = Field(default_factory=list)

    # Detailed authentic Samudrik Shastra interpretation in Bengali & English
    meaning: str = Field(max_length=4000)

    # Life domain: career, love, health, wealth, personality, spirituality
    area: str | None = Field(default=None, max_length=40)

    # Higher priority takes precedence during matching
    priority: int = 0

    # Fallback rule if no specific threshold matches
    is_default: bool = False

    enabled: bool = True
    reviewed: bool = False

    class Settings:
        name = "palm_rules"
        indexes = [
            pymongo.IndexModel(
                [("feature", pymongo.ASCENDING), ("option", pymongo.ASCENDING)],
                name="palm_rule_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("feature", pymongo.ASCENDING), ("priority", pymongo.DESCENDING)],
                name="palm_rule_match",
            ),
        ]


class ReadingSection(BaseModel):
    """One section of a completed palm reading."""

    feature: str
    feature_label: str
    option: str
    label: str
    meaning: str
    area: str | None = None


class PalmReading(TimestampedDocument):
    """One recorded palm reading, preserved with exact measurements and text."""

    user_id: PydanticObjectId

    # Hand scanned: 'left' or 'right'
    hand_scanned: str = Field(default="left")

    # Subject's gender: 'male', 'female', 'other', 'undisclosed'
    gender: str = Field(default="male")

    # Biometric hand and line ratios computed from image or client landmarker
    measurements: dict[str, float] = Field(default_factory=dict)

    sections: list[ReadingSection] = Field(default_factory=list)

    # Frozen coin charge
    coins_charged: int = Field(default=0, ge=0)

    # Quality score [0.0 - 1.0]
    quality: float = Field(default=1.0, ge=0, le=1)

    # Optional base64 or stored URL of visualized analysis overlay
    visualization_image: str | None = None

    expires_at: datetime | None = None

    class Settings:
        name = "palm_readings"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="palm_reading_user_recent",
            ),
        ]
