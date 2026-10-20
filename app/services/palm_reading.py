"""Turning palm biometric measurements into authentic Samudrik Shastra readings.

The rules live in MongoDB so that astrological interpretations and thresholds can be
calibrated without server redeployments.
"""

from beanie import PydanticObjectId
from loguru import logger

from app.core.exceptions import BadRequestError, ServiceUnavailableError
from app.models.palm_reading import (
    Condition,
    PalmFeature,
    PalmReading,
    PalmRule,
    ReadingSection,
)
from app.models.user import User

MIN_QUALITY = 0.40
METRIC_BOUNDS = (-2.0, 10.0)

# A palm belongs to one primary elemental type; other features can match multiple aspects
SINGLE_CHOICE = {PalmFeature.HAND_TYPE}
MAX_PER_FEATURE = 2


def _pick(rules: list[PalmRule], measurements: dict[str, float]) -> list[PalmRule]:
    """Selects the best matching rules for one palm feature."""
    matched = [
        rule
        for rule in rules
        if rule.conditions and all(c.matches(measurements) for c in rule.conditions)
    ]

    if not matched:
        default = next((rule for rule in rules if rule.is_default), None)
        return [default] if default else []

    feature = matched[0].feature
    limit = 1 if feature in SINGLE_CHOICE else MAX_PER_FEATURE

    chosen: list[PalmRule] = []
    used_metrics: set[str] = set()

    for rule in sorted(matched, key=lambda r: r.priority, reverse=True):
        rule_metrics = {c.metric for c in rule.conditions}
        if not (rule_metrics & used_metrics):
            chosen.append(rule)
            used_metrics.update(rule_metrics)
            if len(chosen) >= limit:
                break

    return chosen


async def compose(measurements: dict[str, float]) -> list[ReadingSection]:
    """Composes every section of a palm reading in fixed astrological order."""
    rules = await PalmRule.find(PalmRule.enabled == True).to_list()  # noqa: E712

    by_feature: dict[str, list[PalmRule]] = {}
    for rule in rules:
        by_feature.setdefault(rule.feature, []).append(rule)

    sections: list[ReadingSection] = []
    for feature in PalmFeature.ALL:
        chosen = _pick(by_feature.get(feature, []), measurements)
        if not chosen:
            logger.warning("Palm reading: no rule matching feature {}", feature)
            continue
        for rule in chosen:
            sections.append(
                ReadingSection(
                    feature=feature,
                    feature_label=PalmFeature.LABELS.get(feature, feature.title()),
                    option=rule.option,
                    label=rule.label,
                    meaning=rule.meaning,
                    area=rule.area,
                )
            )

    return sections


def validate(measurements: dict[str, float], quality: float) -> None:
    """Rejects malformed measurements before processing."""
    if quality < MIN_QUALITY:
        raise BadRequestError(
            "Palm capture quality is too low for an accurate reading. Please hold hand steady in good lighting.",
            error_code="low_quality_capture",
        )

    if not measurements:
        raise BadRequestError(
            "No palm measurements provided.", error_code="empty_measurements"
        )

    low, high = METRIC_BOUNDS
    for name, value in measurements.items():
        if not isinstance(value, (int, float)) or value != value:  # NaN check
            raise BadRequestError(
                f"Measurement '{name}' is not a valid number.",
                error_code="bad_measurement",
            )
        if not (low <= value <= high):
            raise BadRequestError(
                f"Measurement '{name}' is out of valid range.",
                error_code="bad_measurement",
            )


async def create(
    *,
    user: User,
    hand_scanned: str = "left",
    gender: str = "male",
    measurements: dict[str, float],
    quality: float,
    visualization_image: str | None = None,
) -> PalmReading:
    """Composes a palm reading, charges wallet coins, and saves the reading."""
    from app.models.enums import TransactionReason
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    platform = await settings_service.get_settings()
    if not platform.palm_reading_enabled:
        raise ServiceUnavailableError(
            "Palm reading is currently disabled on the platform.",
            error_code="palm_reading_disabled",
        )

    validate(measurements, quality)

    sections = await compose(measurements)
    if not sections:
        raise ServiceUnavailableError(
            "Palm reading rules are being updated. Please try again shortly.",
            error_code="rules_unavailable",
        )

    reading = PalmReading(
        user_id=user.id,
        hand_scanned=hand_scanned,
        gender=gender,
        measurements=measurements,
        sections=sections,
        coins_charged=platform.palm_reading_coins,
        quality=round(quality, 3),
        visualization_image=visualization_image,
    )
    await reading.insert()

    if platform.palm_reading_coins > 0:
        try:
            await wallet_service.debit(
                user_id=user.id,
                amount_coins=platform.palm_reading_coins,
                reason=TransactionReason.CONSULTATION,
                idempotency_key=f"palm-reading:{reading.id}",
                note="Palm reading scan",
            )
        except Exception:
            await reading.delete()
            raise

    logger.info(
        "Palm reading {} for {} — {} sections, {} coins",
        reading.id,
        user.email,
        len(sections),
        reading.coins_charged,
    )
    return reading


async def for_user(user_id: PydanticObjectId, limit: int = 20) -> list[PalmReading]:
    return (
        await PalmReading.find(PalmReading.user_id == user_id)
        .sort(-PalmReading.created_at)
        .limit(limit)
        .to_list()
    )


async def seed(force: bool = False) -> dict[str, int]:
    """Seeds the initial Palm Rules from authentic Samudrik Shastra data."""
    from app.data.palm_rules_seed import RULES

    created = updated = skipped = 0
    for row in RULES:
        existing = await PalmRule.find_one(
            PalmRule.feature == row["feature"], PalmRule.option == row["option"]
        )
        conditions = [Condition(**c) for c in row.get("conditions", [])]

        if existing is None:
            await PalmRule(
                feature=row["feature"],
                option=row["option"],
                label=row["label"],
                conditions=conditions,
                meaning=row["meaning"],
                area=row.get("area"),
                priority=row.get("priority", 0),
                is_default=row.get("is_default", False),
            ).insert()
            created += 1
        elif force:
            existing.label = row["label"]
            existing.conditions = conditions
            existing.meaning = row["meaning"]
            existing.area = row.get("area")
            existing.priority = row.get("priority", 0)
            existing.is_default = row.get("is_default", False)
            await existing.save()
            updated += 1
        else:
            skipped += 1

    return {"created": created, "updated": updated, "skipped": skipped}


__all__ = [
    "MIN_QUALITY",
    "compose",
    "create",
    "for_user",
    "seed",
    "validate",
]
