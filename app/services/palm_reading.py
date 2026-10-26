"""Turning a palm scan into a reading.

The rules live in MongoDB and are matched against the scan's measured values. Three
properties matter here and are enforced rather than hoped for:

  A rule fires only when every one of its conditions holds. No partial matches.

  A rule whose inputs were not measured is skipped and reported as skipped. If the
  heart line could not be traced, the heart-line rules do not run - they do not
  fall back to a default that would read as a finding.

  Each statement carries the values that produced it, so the reading can show its
  own basis instead of asserting.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.data.palm_rules_seed import PALM_RULES_SEED
from app.models.palm_reading import (
    FEATURE_LABELS,
    UNAVAILABLE_REASONS,
    Condition,
    PalmRule,
    ReadingSection,
    Requirement,
    SkippedFeature,
)


def flatten_scan_values(scan: dict[str, Any]) -> dict[str, Any]:
    """Collapse a scan result into the flat namespace the conditions address.

    Crease properties are addressed as "heart_line.contrast" and so on, which keeps
    a rule readable next to the client's own phrasing.
    """
    values: dict[str, Any] = {}
    values.update(scan.get("measurements") or {})
    values.update(scan.get("crease_relationships") or {})

    hand = scan.get("hand_type") or {}
    if hand.get("type"):
        values["hand_type"] = hand["type"]
        values["hand_type_confidence"] = hand.get("confidence", 0.0)

    for name, crease in (scan.get("creases") or {}).items():
        prefix = f"{name}_line"
        values[f"{prefix}.found"] = str(bool(crease.get("found")))
        for key in ("strength", "continuity", "contrast", "length", "curvature"):
            if crease.get(key) is not None:
                values[f"{prefix}.{key}"] = crease[key]
        if crease.get("termination_zone"):
            values[f"{prefix}.termination_zone"] = crease["termination_zone"]

    # Flatten temperament archetype & medical constitution keys
    arch = scan.get("temperament_archetype") or {}
    if arch.get("primary_archetype"):
        values["archetype_name"] = arch["primary_archetype"]
        values["archetype_affinity"] = arch.get("affinity_score_pct", 88)

    med = scan.get("medical_constitution") or {}
    pallor = med.get("pallor_diagnosis") or {}
    if pallor.get("state"):
        values["pallor_state"] = pallor["state"]

    kundli = scan.get("kundli_palm_sync") or {}
    if kundli.get("overall_alignment_pct"):
        values["kundli_alignment_pct"] = kundli["overall_alignment_pct"]

    return values


def available_requirements(scan: dict[str, Any]) -> set[str]:
    """What this particular scan can actually support.

    Geometry is available whenever a hand passed the gates. A crease requirement is
    available only when that crease was traced *and accepted*. The photo-impossible
    requirements are never available, by construction.
    """
    available = {Requirement.GEOMETRY.value}
    creases = scan.get("creases") or {}
    for name, requirement in (
        ("heart", Requirement.HEART_LINE.value),
        ("head", Requirement.HEAD_LINE.value),
        ("life", Requirement.LIFE_LINE.value),
        ("fate", Requirement.FATE_LINE.value),
    ):
        if (creases.get(name) or {}).get("found"):
            available.add(requirement)
    return available


def _explain(rule: PalmRule, values: dict[str, Any]) -> list[str]:
    """The measured values that satisfied this rule, in readable form."""
    reasons: list[str] = []
    for condition in rule.conditions:
        if condition.metric not in values:
            continue
        raw = values[condition.metric]
        pretty = condition.metric.replace("_", " ").replace(".", " ")
        if isinstance(raw, (int, float)):
            reasons.append(f"{pretty} measured {float(raw):.2f}")
        else:
            reasons.append(f"{pretty} is {raw}")
    return reasons


def _matches(rule: PalmRule, values: dict[str, Any]) -> bool:
    return all(condition.matches(values) for condition in rule.conditions)


def build_reading(
    scan: dict[str, Any], rules: list[PalmRule]
) -> tuple[list[ReadingSection], list[SkippedFeature]]:
    """Match every enabled rule against one scan."""
    values = flatten_scan_values(scan)
    available = available_requirements(scan)

    by_feature: dict[str, list[PalmRule]] = {}
    for rule in rules:
        if rule.enabled:
            by_feature.setdefault(rule.feature, []).append(rule)

    sections: list[ReadingSection] = []
    skipped: list[SkippedFeature] = []
    reported_requirements: set[str] = set()

    for feature, feature_rules in by_feature.items():
        usable = [r for r in feature_rules if set(r.requires) <= available]

        if not usable:
            # Report why, once per missing requirement, naming the first one the
            # feature needed and could not have.
            missing = sorted(
                {req for r in feature_rules for req in r.requires if req not in available}
            )
            for requirement in missing:
                key = f"{feature}:{requirement}"
                if key in reported_requirements:
                    continue
                reported_requirements.add(key)
                skipped.append(
                    SkippedFeature(
                        feature=feature,
                        feature_label=FEATURE_LABELS.get(feature, feature),
                        requirement=requirement,
                        reason=UNAVAILABLE_REASONS.get(
                            requirement,
                            "This crease could not be read clearly enough from the photo, "
                            "so the rules that depend on it were not applied.",
                        ),
                    )
                )
            continue

        matched = [r for r in usable if r.conditions and _matches(r, values)]
        if matched:
            # Highest priority wins; ties break on the more specific rule.
            chosen = max(matched, key=lambda r: (r.priority, len(r.conditions)))
        else:
            defaults = [r for r in usable if r.is_default]
            chosen = defaults[0] if defaults else None

        if chosen is None:
            continue

        sections.append(
            ReadingSection(
                feature=chosen.feature,
                feature_label=FEATURE_LABELS.get(chosen.feature, chosen.feature),
                option=chosen.option,
                label=chosen.label,
                meaning=chosen.meaning,
                area=chosen.area,
                source=chosen.source,
                because=_explain(chosen, values),
            )
        )

    # Stable order, so the same hand reads the same way twice.
    feature_order = list(FEATURE_LABELS.keys())
    sections.sort(
        key=lambda s: feature_order.index(s.feature) if s.feature in feature_order else 99
    )
    skipped.sort(
        key=lambda s: feature_order.index(s.feature) if s.feature in feature_order else 99
    )
    return sections, skipped


async def load_rules() -> list[PalmRule]:
    rules = await PalmRule.find_all().to_list()
    # Self-healing: if database rules are missing or outdated in count compared to PALM_RULES_SEED, sync immediately
    if not rules or len(rules) < len(PALM_RULES_SEED):
        try:
            logger.info(
                f"Syncing palm rules: DB has {len(rules)}, expected at least {len(PALM_RULES_SEED)}"
            )
            await seed_rules(force=False)
            rules = await PalmRule.find_all().to_list()
        except Exception as exc:
            logger.error(f"Error auto-seeding palm rules: {exc}")
    return rules


async def seed_rules(force: bool = False) -> dict[str, int]:
    """Load the starting rule set, without disturbing anything already edited.

    A rule the client's astrologer has reviewed is never overwritten: the whole
    point of keeping these in the database is that their corrections survive.
    """
    created = updated = skipped = 0

    for entry in PALM_RULES_SEED:
        existing = await PalmRule.find_one(
            PalmRule.feature == entry["feature"], PalmRule.option == entry["option"]
        )

        if existing is None:
            await PalmRule(
                feature=entry["feature"],
                option=entry["option"],
                label=entry["label"],
                conditions=[Condition(**c) for c in entry.get("conditions", [])],
                requires=entry.get("requires", [Requirement.GEOMETRY.value]),
                meaning=entry["meaning"],
                area=entry.get("area"),
                source=entry.get("source"),
                priority=entry.get("priority", 0),
                is_default=entry.get("is_default", False),
            ).insert()
            created += 1
            continue

        if existing.reviewed and not force:
            skipped += 1
            continue

        existing.label = entry["label"]
        existing.conditions = [Condition(**c) for c in entry.get("conditions", [])]
        existing.requires = entry.get("requires", [Requirement.GEOMETRY.value])
        existing.meaning = entry["meaning"]
        existing.area = entry.get("area")
        existing.source = entry.get("source")
        existing.priority = entry.get("priority", 0)
        existing.is_default = entry.get("is_default", False)
        await existing.save()
        updated += 1

    logger.info(f"palm rules seeded: {created} created, {updated} updated, {skipped} kept")
    return {"created": created, "updated": updated, "kept_reviewed": skipped}
