"""Face reading: the rules, and the readings produced from them.

The rules live in the database rather than in code, and that is the whole
design. Every threshold here is a judgement — no supplied document says how
wide a "broad" nose is — so the numbers will be argued with and changed. When
the client's astrologer sends corrections, someone edits rows; nobody
redeploys.

A reading stores the measurements it was made from **and** the text it
produced. Storing only the measurements would mean an old reading silently
rewrote itself the next time a threshold moved, and a person who paid for a
reading should be able to open the one they paid for.

No photograph is stored, or even uploaded. The browser finds the landmarks on
the device and sends perhaps twenty ratios; a face never reaches this server.
"""

from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument


class FaceFeature:
    """The parts of a face a reading is built from."""

    FACE_SHAPE = "face_shape"
    FOREHEAD = "forehead"
    EYEBROWS = "eyebrows"
    EYES = "eyes"
    NOSE = "nose"
    LIPS = "lips"
    CHIN = "chin"
    CHEEKS = "cheeks"

    ALL = [FACE_SHAPE, FOREHEAD, EYEBROWS, EYES, NOSE, LIPS, CHIN, CHEEKS]

    LABELS = {
        FACE_SHAPE: "Face shape",
        FOREHEAD: "Forehead",
        EYEBROWS: "Eyebrows",
        EYES: "Eyes",
        NOSE: "Nose",
        LIPS: "Lips & smile",
        CHIN: "Chin & jaw",
        CHEEKS: "Cheeks",
    }


class Condition(BaseModel):
    """When this rule applies.

    One measurement against a band. `min` is inclusive, `max` exclusive, and
    either may be null for an open end — so three rules can cover a whole
    range with no gap and no overlap.
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


class FaceRule(TimestampedDocument):
    """One option of one feature, and when to say it."""

    feature: str
    option: str
    label: str

    # Every condition must hold. Usually one; face shape needs two or three.
    conditions: list[Condition] = Field(default_factory=list)

    # What the reading says. Written in our own words — see RESOURCES-MASTER §9.
    meaning: str = Field(max_length=4000)
    # Which part of life this speaks to, for grouping on screen.
    area: str | None = Field(default=None, max_length=40)

    # When two rules of the same feature both match, the higher one wins.
    # Lets a specific combination beat a broad band without reordering ranges.
    priority: int = 0

    # The fallback for its feature: used only when nothing else matched, so a
    # reading is never silently missing a section.
    is_default: bool = False

    enabled: bool = True
    # Set once the client's astrologer has approved the wording.
    reviewed: bool = False

    class Settings:
        name = "face_rules"
        indexes = [
            pymongo.IndexModel(
                [("feature", pymongo.ASCENDING), ("option", pymongo.ASCENDING)],
                name="face_rule_unique",
                unique=True,
            ),
            pymongo.IndexModel(
                [("feature", pymongo.ASCENDING), ("priority", pymongo.DESCENDING)],
                name="face_rule_match",
            ),
        ]


class ReadingSection(BaseModel):
    """One feature's verdict inside a finished reading."""

    feature: str
    feature_label: str
    option: str
    label: str
    meaning: str
    area: str | None = None


class FaceReading(TimestampedDocument):
    """One finished reading, kept exactly as it was given."""

    user_id: PydanticObjectId

    # The ratios the browser measured. Kept so a reading can be explained, and
    # so thresholds can be re-tested against real faces later.
    measurements: dict[str, float] = Field(default_factory=dict)

    sections: list[ReadingSection] = Field(default_factory=list)

    # What it cost, frozen. A later price change must not restate this.
    coins_charged: int = Field(default=0, ge=0)

    # How confident the capture was — see services.face_reading.
    quality: float = Field(default=1.0, ge=0, le=1)

    expires_at: datetime | None = None

    class Settings:
        name = "face_readings"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
                name="face_reading_user_recent",
            ),
        ]
