"""Turning face measurements into a reading.

The browser measures; this decides what the measurements mean. Nothing here
sees a photograph — by the time a request arrives it is roughly twenty ratios,
each already normalised against the subject's own face so that camera distance,
image size and lens have cancelled out.

Matching is deliberately simple and entirely data-driven: for each feature,
take the enabled rules whose conditions all hold, and keep the highest
priority. If none hold, the feature's default rule is used, so a reading never
comes back with a section missing. Every number lives in the database, because
every number is a judgement that will be revised.

Charging happens **after** the reading is composed. A wallet should not be
debited for a reading that then failed to build.
"""

from beanie import PydanticObjectId
from loguru import logger

from app.core.exceptions import BadRequestError, ServiceUnavailableError
from app.models.face_reading import FaceFeature, FaceReading, FaceRule, ReadingSection
from app.models.user import User

# A capture below this is not read at all. Face landmarking stays confident
# well past the point where the *proportions* stop being trustworthy — a head
# turned far enough foreshortens one side, and every width ratio is then wrong
# in a way nothing downstream can detect.
MIN_QUALITY = 0.55

# Sanity bounds. A ratio outside these did not come from a face, so the whole
# payload is refused rather than read.
METRIC_BOUNDS = (0.0, 10.0)


# A face has one shape. Everything else has independent aspects that can both
# be true at once — lips are full *and* upturned, a nose long *and* broad — and
# collapsing those to one verdict throws away a reading the rules already hold.
SINGLE_CHOICE = {FaceFeature.FACE_SHAPE}
MAX_PER_FEATURE = 2


def _pick(rules: list[FaceRule], measurements: dict[str, float]) -> list[FaceRule]:
    """Every rule that should speak for one feature, best first.

    Matched rules are grouped by the measurement they are about, and only the
    best of each group survives — two bands of the same ratio are alternatives,
    never both. Rules about *different* ratios can both stand.
    """
    matched = [
        rule
        for rule in rules
        if rule.conditions and all(c.matches(measurements) for c in rule.conditions)
    ]

    if not matched:
        default = next((rule for rule in rules if rule.is_default), None)
        return [default] if default else []

    best_per_metric: dict[str, FaceRule] = {}
    for rule in matched:
        # The first condition is the one the rule is really about; any others
        # narrow it.
        metric = rule.conditions[0].metric
        current = best_per_metric.get(metric)
        if current is None or rule.priority > current.priority:
            best_per_metric[metric] = rule

    chosen = sorted(best_per_metric.values(), key=lambda r: r.priority, reverse=True)

    feature = matched[0].feature
    limit = 1 if feature in SINGLE_CHOICE else MAX_PER_FEATURE
    return chosen[:limit]


async def compose(measurements: dict[str, float]) -> list[ReadingSection]:
    """Builds every section of a reading, in a fixed order."""
    rules = await FaceRule.find(FaceRule.enabled == True).to_list()  # noqa: E712

    by_feature: dict[str, list[FaceRule]] = {}
    for rule in rules:
        by_feature.setdefault(rule.feature, []).append(rule)

    sections: list[ReadingSection] = []
    for feature in FaceFeature.ALL:
        chosen = _pick(by_feature.get(feature, []), measurements)
        if not chosen:
            # No rule at all for this feature — skip it rather than invent one.
            logger.warning("Face reading: no rule for feature {}", feature)
            continue
        for rule in chosen:
            sections.append(
                ReadingSection(
                    feature=feature,
                    feature_label=FaceFeature.LABELS.get(feature, feature.title()),
                    option=rule.option,
                    label=rule.label,
                    meaning=rule.meaning,
                    area=rule.area,
                )
            )
    return sections


def validate(measurements: dict[str, float], quality: float) -> None:
    """Refuses a capture that cannot produce an honest reading."""
    if quality < MIN_QUALITY:
        raise BadRequestError(
            "That photo was taken at too much of an angle to measure. "
            "Face the camera straight on, in even light, and try again.",
            error_code="poor_capture",
        )
    if not measurements:
        raise BadRequestError("No measurements were sent.", error_code="no_measurements")

    low, high = METRIC_BOUNDS
    for name, value in measurements.items():
        if not isinstance(value, (int, float)) or value != value:  # NaN
            raise BadRequestError(
                f"Measurement '{name}' is not a number.", error_code="bad_measurement"
            )
        if not low <= value <= high:
            raise BadRequestError(
                f"Measurement '{name}' is out of range.", error_code="bad_measurement"
            )


async def create(
    *, user: User, measurements: dict[str, float], quality: float
) -> FaceReading:
    """Reads a face, charges for it, and keeps the result."""
    from app.models.enums import TransactionReason
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    platform = await settings_service.get_settings()
    if not platform.face_reading_enabled:
        raise ServiceUnavailableError(
            "Face reading is not available right now.",
            error_code="face_reading_disabled",
        )

    validate(measurements, quality)

    sections = await compose(measurements)
    if not sections:
        # Means the rule set is empty or broken. Charging for an empty reading
        # would be worse than refusing it.
        raise ServiceUnavailableError(
            "Face reading is being updated. Please try again shortly.",
            error_code="rules_unavailable",
        )

    reading = FaceReading(
        user_id=user.id,
        measurements=measurements,
        sections=sections,
        coins_charged=platform.face_reading_coins,
        quality=round(quality, 3),
    )
    # Inserted first so the charge can carry its id, which is what makes the
    # debit idempotent — a retried request cannot be billed twice.
    await reading.insert()

    if platform.face_reading_coins > 0:
        try:
            await wallet_service.debit(
                user_id=user.id,
                amount_coins=platform.face_reading_coins,
                reason=TransactionReason.CONSULTATION,
                idempotency_key=f"face-reading:{reading.id}",
                note="Face reading",
            )
        except Exception:
            # Nothing was delivered, so nothing is kept. Without this a failed
            # payment would still leave a readable reading in their history.
            await reading.delete()
            raise

    logger.info(
        "Face reading {} for {} — {} sections, {} coins",
        reading.id,
        user.email,
        len(sections),
        reading.coins_charged,
    )
    return reading


async def for_user(user_id: PydanticObjectId, limit: int = 20) -> list[FaceReading]:
    return (
        await FaceReading.find(FaceReading.user_id == user_id)
        .sort(-FaceReading.created_at)
        .limit(limit)
        .to_list()
    )


async def public_rules() -> list[dict]:
    """The rule set, for anyone who wants to see how a reading is decided.

    Served without the meanings: those are the paid part. What this exposes is
    the shape — which features are read, which options exist, and the bands —
    so the method is inspectable even though the text is not free.
    """
    rules = await FaceRule.find(FaceRule.enabled == True).to_list()  # noqa: E712
    return [
        {
            "feature": r.feature,
            "feature_label": FaceFeature.LABELS.get(r.feature, r.feature),
            "option": r.option,
            "label": r.label,
            "conditions": [c.model_dump() for c in r.conditions],
            "is_default": r.is_default,
        }
        for r in rules
    ]


async def seed(force: bool = False) -> dict[str, int]:
    """Loads the starting rule set.

    Existing rows are left alone unless `force` is passed, so re-running this
    after an admin has corrected a threshold does not undo their work.
    """
    from app.data.face_rules_seed import RULES
    from app.models.face_reading import Condition

    created = updated = skipped = 0
    for row in RULES:
        existing = await FaceRule.find_one(
            FaceRule.feature == row["feature"], FaceRule.option == row["option"]
        )
        conditions = [Condition(**c) for c in row.get("conditions", [])]

        if existing is None:
            await FaceRule(
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


async def unmatched_features(measurements: dict[str, float]) -> list[str]:
    """Features that fell through to their default.

    Not shown to the user. It is how we find out, from real faces, which bands
    are set wrongly — a feature that always falls through has thresholds nobody
    reaches.
    """
    rules = await FaceRule.find(FaceRule.enabled == True).to_list()  # noqa: E712
    by_feature: dict[str, list[FaceRule]] = {}
    for rule in rules:
        by_feature.setdefault(rule.feature, []).append(rule)

    fell_through = []
    for feature, group in by_feature.items():
        chosen = _pick(group, measurements)
        if chosen and all(r.is_default for r in chosen):
            fell_through.append(feature)
    return fell_through


__all__ = [
    "MIN_QUALITY",
    "compose",
    "create",
    "for_user",
    "public_rules",
    "seed",
    "unmatched_features",
    "validate",
]
