"""Tests for palm scanning.

Two things are being guarded here.

The first is that the pipeline cannot be made to crash. A palm scan takes an
arbitrary upload from the public internet, decodes it, and runs several hundred
lines of image processing over it. Every malformed, hostile or merely odd input
below must come back as a status, never as an exception reaching the worker.

The second is the property that makes the feature honest: **a reading is never
produced from something that was not measured.** An earlier palm pipeline in this
repository (commit 5994b57, removed the same day it landed) reported a "heart line
length" that was actually the distance between two knuckles and a "life line arc"
that was the thumb-to-wrist distance - figures that would come out identical on a
photograph of a hand with no lines on it. Several tests here exist specifically to
stop that class of defect returning.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import numpy as np
import pytest

from app.data.palm_rules_seed import PALM_RULES_SEED
from app.models.palm_reading import (
    FEATURE_LABELS,
    UNAVAILABLE_REASONS,
    Condition,
    PalmFeature,
    Requirement,
)
from app.services.palm_cv import (
    DEFAULT_CONFIG,
    build_canonical_palm,
    decode_image,
    execute_scan,
    extract,
    get_landmarker,
    hand_type,
    trace_creases,
)
from app.services.palm_cv import landmarks as L
from app.services.palm_cv.quality import assess, hand_pose
from app.services.palm_reading import (
    available_requirements,
    build_reading,
    flatten_scan_values,
)


# ----------------------------------------------------------------------------------
# A synthetic hand, so the geometry tests do not depend on a photograph
# ----------------------------------------------------------------------------------
def synthetic_landmarks(
    palm_length: float = 200.0,
    palm_width: float = 180.0,
    finger_scale: float = 1.0,
    thumb_scale: float = 1.0,
    spread: float = 0.0,
) -> list[tuple[float, float, float]]:
    """A plausible right hand, fingers up, wrist at the origin.

    Built rather than photographed so that a measurement can be checked against a
    number that is known exactly. A ratio test against a real photo can only ever
    say "about right".
    """
    points = [(0.0, 0.0, 0.0)] * 21
    points[L.WRIST] = (0.0, 0.0, 0.0)

    knuckle_y = -palm_length
    xs = {
        L.INDEX_MCP: -palm_width / 2,
        L.MIDDLE_MCP: -palm_width / 6,
        L.RING_MCP: palm_width / 6,
        L.PINKY_MCP: palm_width / 2,
    }
    for index, x in xs.items():
        points[index] = (x, knuckle_y, 0.0)

    lengths = {"index": 0.78, "middle": 0.86, "ring": 0.80, "pinky": 0.62}
    for name, chain in L.FINGER_CHAINS.items():
        mcp, pip, dip, tip = chain
        base_x, base_y, _ = points[mcp]
        total = palm_length * lengths[name] * finger_scale
        lean = spread * (list(L.FINGER_CHAINS).index(name) - 1.5)
        for step, joint in enumerate((pip, dip, tip), start=1):
            share = (0.45, 0.75, 1.0)[step - 1]
            points[joint] = (
                base_x + lean * share,
                base_y - total * share,
                0.0,
            )

    # Thumb, out to the radial side and angled away.
    thumb_total = palm_length * 0.70 * thumb_scale
    points[L.THUMB_CMC] = (-palm_width * 0.42, -palm_length * 0.18, 0.0)
    points[L.THUMB_MCP] = (-palm_width * 0.62, -palm_length * 0.36, 0.0)
    points[L.THUMB_IP] = (-palm_width * 0.74, -palm_length * 0.52, 0.0)
    points[L.THUMB_TIP] = (
        -palm_width * 0.42 - thumb_total * 0.62,
        -palm_length * 0.18 - thumb_total * 0.62,
        0.0,
    )
    return points


@dataclass
class RuleShim:
    """Stands in for a stored PalmRule.

    Beanie documents cannot be built without a live database, and the matching
    logic only ever reads attributes, so the rules under test are plain objects.
    That keeps these tests running without MongoDB.
    """

    feature: str
    option: str
    label: str
    meaning: str
    conditions: list = field(default_factory=list)
    requires: list = field(default_factory=list)
    area: str | None = None
    source: str | None = None
    priority: int = 0
    is_default: bool = False
    enabled: bool = True


def seeded_rules() -> list[RuleShim]:
    return [
        RuleShim(
            feature=entry["feature"],
            option=entry["option"],
            label=entry["label"],
            meaning=entry["meaning"],
            conditions=[Condition(**c) for c in entry.get("conditions", [])],
            requires=entry.get("requires", [Requirement.GEOMETRY.value]),
            area=entry.get("area"),
            source=entry.get("source"),
            priority=entry.get("priority", 0),
            is_default=entry.get("is_default", False),
        )
        for entry in PALM_RULES_SEED
    ]


def jpeg_bytes(array: np.ndarray) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


# ----------------------------------------------------------------------------------
# Nothing may crash the worker
# ----------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "payload,label",
    [
        (b"", "empty"),
        (b"not an image", "plain text"),
        (b"\xff\xd8\xff\xe0" + b"\x00" * 200, "truncated JPEG header"),
        (bytes(range(256)) * 50, "random bytes"),
        (b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n", "a PDF"),
        (b"GIF89a" + b"\x00" * 100, "truncated GIF"),
    ],
)
def test_malformed_uploads_are_rejected_not_raised(payload, label):
    result = execute_scan(payload)
    assert result.status in {"rejected", "error"}, label
    assert result.message
    assert result.processing_ms >= 0


def test_a_picture_with_no_hand_is_rejected():
    noise = (np.random.default_rng(7).random((640, 640, 3)) * 255).astype(np.uint8)
    result = execute_scan(jpeg_bytes(noise))
    assert result.status == "rejected"
    assert not result.hand_detected
    assert "hand" in (result.message or "").lower()


def test_a_blank_image_is_rejected():
    blank = np.full((640, 640, 3), 220, dtype=np.uint8)
    result = execute_scan(jpeg_bytes(blank))
    assert result.status == "rejected"


def test_a_tiny_image_is_rejected_before_anything_else():
    tiny = (np.random.default_rng(3).random((40, 40, 3)) * 255).astype(np.uint8)
    result = execute_scan(jpeg_bytes(tiny))
    assert result.status == "rejected"


def test_a_rejected_scan_carries_no_measurements():
    """A rejected photo must not leak half-computed numbers a caller might use."""
    result = execute_scan(b"not an image")
    assert result.measurements == {}
    assert result.creases == {}
    assert result.hand_type == {}


# ----------------------------------------------------------------------------------
# Geometry, against a hand whose proportions are known exactly
# ----------------------------------------------------------------------------------
def test_phalange_shares_sum_to_one():
    """Each finger's three phalanges are shares of that finger, so they must total 1.

    This catches a whole class of indexing mistake: swap two joints and the shares
    still look plausible individually but stop summing.
    """
    measured = extract(synthetic_landmarks())
    for finger in ("index", "middle", "ring", "pinky"):
        total = sum(
            measured.values[f"{finger}_phalange_{part}"]
            for part in ("first", "second", "third")
        )
        assert total == pytest.approx(1.0, abs=1e-6), finger


def test_measurements_are_scale_invariant():
    """The same hand near and far must measure the same.

    Every value is a ratio for exactly this reason; a stray pixel count would show
    up here immediately.
    """
    near = extract(synthetic_landmarks(palm_length=200, palm_width=180))
    far = extract(synthetic_landmarks(palm_length=80, palm_width=72))
    for key, value in near.values.items():
        if key == "thumb_index_angle":
            continue  # an angle, compared below
        assert value == pytest.approx(far.values[key], rel=1e-6), key


def test_angles_are_scale_invariant_too():
    near = extract(synthetic_landmarks(palm_length=200, palm_width=180))
    far = extract(synthetic_landmarks(palm_length=80, palm_width=72))
    assert near.values["thumb_index_angle"] == pytest.approx(
        far.values["thumb_index_angle"], abs=0.5
    )


def test_longer_fingers_raise_the_finger_palm_ratio():
    short = extract(synthetic_landmarks(finger_scale=0.85))
    long = extract(synthetic_landmarks(finger_scale=1.15))
    assert long.values["finger_palm_ratio"] > short.values["finger_palm_ratio"]


def test_a_longer_thumb_measures_longer():
    small = extract(synthetic_landmarks(thumb_scale=0.7))
    large = extract(synthetic_landmarks(thumb_scale=1.3))
    assert large.values["thumb_length_ratio"] > small.values["thumb_length_ratio"]


def test_spreading_the_fingers_raises_the_spread_measure():
    closed = extract(synthetic_landmarks(spread=0.0))
    open_hand = extract(synthetic_landmarks(spread=14.0))
    assert open_hand.values["finger_spread"] > closed.values["finger_spread"]


@pytest.mark.parametrize(
    "aspect,fingers,expected",
    [
        (0.95, 0.90, "Earth"),
        (0.95, 1.00, "Air"),
        (0.80, 0.90, "Fire"),
        (0.80, 1.00, "Water"),
    ],
)
def test_hand_type_quadrants(aspect, fingers, expected):
    assert hand_type({"palm_aspect": aspect, "finger_palm_ratio": fingers})["type"] == expected


def test_hand_type_reports_low_confidence_on_a_boundary():
    """A hand sitting exactly on the dividing line must say so rather than assert."""
    on_edge = hand_type({"palm_aspect": 0.92, "finger_palm_ratio": 0.95})
    clear = hand_type({"palm_aspect": 0.70, "finger_palm_ratio": 1.20})
    assert on_edge["confidence"] < clear["confidence"]
    assert on_edge["confidence"] < 0.2


# ----------------------------------------------------------------------------------
# Quality gates
# ----------------------------------------------------------------------------------
def test_pose_detects_a_square_on_palm():
    pose = hand_pose(synthetic_landmarks())
    assert pose["tilt_degrees"] < 15.0
    assert abs(pose["roll_degrees"]) < 15.0


def test_pose_detects_rotation():
    points = synthetic_landmarks()
    angle = np.deg2rad(40.0)
    cos, sin = np.cos(angle), np.sin(angle)
    rotated = [(x * cos - y * sin, x * sin + y * cos, z) for x, y, z in points]
    assert abs(hand_pose(rotated)["roll_degrees"]) > 25.0


def test_every_quality_gate_has_an_actionable_message():
    """A rejection the user cannot act on is as good as no message at all."""
    image = np.full((700, 700, 3), 160, dtype=np.uint8)
    report = assess(image, synthetic_landmarks(palm_length=160, palm_width=150))
    for check in report.checks:
        assert check.message, check.name
        # Every message should tell the user what to do, not just what is wrong.
        assert len(check.message) > 25, check.name


# ----------------------------------------------------------------------------------
# Crease tracing: the property that stops the old defect returning
# ----------------------------------------------------------------------------------
def test_a_featureless_palm_yields_no_creases():
    """On a surface with no lines, nothing may be reported as a line.

    This is the test the removed pipeline would have failed. Its crease metrics
    were computed from landmark distances and edge counts, so a blank surface
    still produced confident "heart line length" and "life line arc" figures.
    """
    flat = np.full((DEFAULT_CONFIG.canonical_size, DEFAULT_CONFIG.canonical_size, 3), 190, np.uint8)
    # A faint, even gradient, so it is not pathologically uniform.
    gradient = np.linspace(0, 12, DEFAULT_CONFIG.canonical_size, dtype=np.float32)
    flat = np.clip(flat + gradient[None, :, None], 0, 255).astype(np.uint8)

    landmarks = synthetic_landmarks(palm_length=300, palm_width=280)
    shifted = [(x + 256, y + 400, z) for x, y, z in landmarks]
    palm = build_canonical_palm(flat, shifted)
    creases = trace_creases(palm)

    for name, crease in creases.items():
        assert not crease.found, f"{name} was reported on a palm with no lines"


def test_crease_contrast_is_reported_so_a_weak_trace_is_visible():
    flat = np.full((DEFAULT_CONFIG.canonical_size, DEFAULT_CONFIG.canonical_size, 3), 190, np.uint8)
    landmarks = synthetic_landmarks(palm_length=300, palm_width=280)
    shifted = [(x + 256, y + 400, z) for x, y, z in landmarks]
    creases = trace_creases(build_canonical_palm(flat, shifted))
    for crease in creases.values():
        assert crease.contrast >= 0.0
        assert "contrast" in crease.as_dict()


def test_handedness_is_normalised_so_both_hands_use_one_frame():
    """A left and a right palm are mirror images.

    Without normalising, every band and every rule would need two versions, and
    the pair would drift. The frame reports whether it flipped.
    """
    image = np.full((900, 900, 3), 185, dtype=np.uint8)
    right = [(x + 450, y + 600, z) for x, y, z in synthetic_landmarks()]
    left = [(900 - x, y, z) for x, y, z in right]

    right_palm = build_canonical_palm(image, right)
    left_palm = build_canonical_palm(image, left)
    assert right_palm.mirrored != left_palm.mirrored


# ----------------------------------------------------------------------------------
# A reading is never produced from something that was not measured
# ----------------------------------------------------------------------------------
def _scan_stub(creases_found: dict[str, bool], **values) -> dict:
    measurements = {
        "palm_aspect": 0.80, "finger_palm_ratio": 1.02, "index_ring_ratio": 0.98,
        "thumb_length_ratio": 1.20, "thumb_flange_ratio": 1.05, "thumb_index_angle": 38.0,
        "finger_spread": 8.0, "finger_lean_to_thumb": 0.0, "jupiter_bend": 6.0,
        "finger_thickness": 0.26, "index_phalange_first": 0.28,
        "index_phalange_second": 0.30, "index_phalange_third": 0.42,
        "is_square_palm": 0.0, "mercury_reach_ratio": 0.84,
    }
    measurements.update({k: v for k, v in values.items() if isinstance(v, (int, float))})
    return {
        "measurements": measurements,
        "hand_type": {"type": "Water", "confidence": 0.9},
        "creases": {
            name: {
                "found": found,
                "contrast": 4.0 if found else 0.8,
                "termination_zone": "lower Jupiter" if found else None,
            }
            for name, found in creases_found.items()
        },
        "crease_relationships": {"heart_head_gap": 0.14, "life_reach": 0.45},
    }


def test_crease_rules_are_skipped_when_the_crease_was_not_traced():
    scan = _scan_stub({"heart": False, "head": False, "life": False, "fate": False})
    sections, skipped = build_reading(scan, seeded_rules())

    crease_features = {
        PalmFeature.HEART_LINE.value, PalmFeature.HEAD_LINE.value,
        PalmFeature.LIFE_LINE.value, PalmFeature.LINE_RELATIONSHIP.value,
    }
    stated = {s.feature for s in sections}
    assert not (stated & crease_features), "a crease rule fired without its crease"
    assert skipped, "the skipped creases must be reported, not silently dropped"


def test_geometry_rules_still_fire_when_no_crease_was_traced():
    """Losing the lines must not lose the whole reading."""
    scan = _scan_stub({"heart": False, "head": False, "life": False, "fate": False})
    sections, _ = build_reading(scan, seeded_rules())
    assert any(s.feature == PalmFeature.HAND_TYPE.value for s in sections)
    assert any(s.feature == PalmFeature.THUMB.value for s in sections)


def test_crease_rules_fire_once_the_crease_is_there():
    scan = _scan_stub({"heart": True, "head": True, "life": True, "fate": True})
    sections, _ = build_reading(scan, seeded_rules())
    assert any(s.feature == PalmFeature.HEART_LINE.value for s in sections)


def test_photo_impossible_requirements_can_never_be_satisfied():
    """Fingerprints, skin texture and mount height are not in a photograph.

    No scan, however good, may make these available, and every one must carry a
    reason the user can read.
    """
    scan = _scan_stub({"heart": True, "head": True, "life": True, "fate": True})
    available = available_requirements(scan)
    for requirement in (
        Requirement.FINGERPRINTS, Requirement.SKIN_TEXTURE,
        Requirement.MOUNT_HEIGHT, Requirement.MINOR_MARKS,
    ):
        assert requirement.value not in available
        assert UNAVAILABLE_REASONS[requirement.value]


def test_every_statement_shows_what_produced_it():
    scan = _scan_stub({"heart": True, "head": True, "life": True, "fate": True})
    sections, _ = build_reading(scan, seeded_rules())
    assert sections
    defaults = {entry["option"] for entry in PALM_RULES_SEED if entry.get("is_default")}
    for section in sections:
        assert section.meaning
        assert section.feature_label
        # A statement with conditions must be able to say which values met them.
        if section.option not in defaults:
            assert section.because, section.option


def test_only_one_statement_per_feature():
    """Two findings about the thumb in one reading would contradict each other."""
    scan = _scan_stub({"heart": True, "head": True, "life": True, "fate": True})
    sections, _ = build_reading(scan, seeded_rules())
    features = [s.feature for s in sections]
    assert len(features) == len(set(features))


def test_the_reading_is_stable_for_the_same_hand():
    scan = _scan_stub({"heart": True, "head": True, "life": True, "fate": True})
    first, _ = build_reading(scan, seeded_rules())
    second, _ = build_reading(scan, seeded_rules())
    assert [s.option for s in first] == [s.option for s in second]


# ----------------------------------------------------------------------------------
# The rule set itself
# ----------------------------------------------------------------------------------
def test_every_rule_cites_the_client_document_it_came_from():
    for entry in PALM_RULES_SEED:
        assert entry.get("source"), entry["option"]
        assert entry.get("meaning"), entry["option"]
        assert entry.get("area"), entry["option"]


def test_rule_identities_are_unique():
    seen = {(e["feature"], e["option"]) for e in PALM_RULES_SEED}
    assert len(seen) == len(PALM_RULES_SEED)


def test_every_rule_feature_has_a_label():
    for entry in PALM_RULES_SEED:
        assert entry["feature"] in FEATURE_LABELS, entry["feature"]


def test_crease_rules_declare_the_crease_they_need():
    """A heart-line rule that forgot to declare the heart line would fire blind."""
    crease_requirement = {
        PalmFeature.HEART_LINE.value: Requirement.HEART_LINE.value,
        PalmFeature.HEAD_LINE.value: Requirement.HEAD_LINE.value,
        PalmFeature.LIFE_LINE.value: Requirement.LIFE_LINE.value,
    }
    for entry in PALM_RULES_SEED:
        needed = crease_requirement.get(entry["feature"])
        if needed:
            assert needed in entry.get("requires", []), entry["option"]


def test_a_feature_has_at_most_one_default():
    defaults: dict[str, int] = {}
    for entry in PALM_RULES_SEED:
        if entry.get("is_default"):
            defaults[entry["feature"]] = defaults.get(entry["feature"], 0) + 1
    for feature, count in defaults.items():
        assert count == 1, feature


def test_conditions_reference_metrics_the_scan_actually_produces():
    """A rule testing a metric nothing measures can never fire, silently."""
    scan = _scan_stub({"heart": True, "head": True, "life": True, "fate": True})
    available = set(flatten_scan_values(scan))
    # Metrics produced only by a real image or crease_relationships
    from_real_scans = {
        "life_line.contrast", "fate_line.contrast", "fate_line.found", "fate_origin",
        "heart_height", "head_height", "head_slope", "head_life_gap", "head_line.length",
        "heart_line.contrast", "heart_line.curvature", "life_descent", "life_line.contrast",
    }
    for entry in PALM_RULES_SEED:
        for condition in entry.get("conditions", []):
            metric = condition["metric"]
            assert metric in available or metric in from_real_scans, (
                f"{entry['option']} tests '{metric}', which nothing measures"
            )


# ----------------------------------------------------------------------------------
# End to end, on a real photograph
# ----------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def real_palm_scan():
    from pathlib import Path

    candidate = Path(__file__).parent / "fixtures" / "palm.jpg"
    if not candidate.exists():
        pytest.skip("no real palm fixture available")
    return execute_scan(candidate.read_bytes())


def test_a_real_palm_produces_a_reading(real_palm_scan):
    assert real_palm_scan.status == "ok"
    sections, _ = build_reading(real_palm_scan.as_dict(), seeded_rules())
    assert sections


def test_a_real_scan_returns_an_overlay(real_palm_scan):
    """The overlay is how a user checks the reading, so it is not optional."""
    assert real_palm_scan.overlay_image
    assert real_palm_scan.overlay_image.startswith("data:image/jpeg;base64,")


def test_a_real_scan_completes_quickly(real_palm_scan):
    assert real_palm_scan.processing_ms < 4000
