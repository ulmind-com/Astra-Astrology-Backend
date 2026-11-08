"""Tests for advanced Vedic palm reading features.

Validates the full implementation of:
  1. 11 Palmer Dermatoglyphic Loops (Loops.docx)
  2. 12 Authentic Marriage & Relationship Cards (IMG_2718 - IMG_2729)
  3. 17 Authentic Vedic Temperament Archetypes (Nature through palm.docx)
  4. Medical Chirology & Ayurvedic Constitution (Health palmistry.docx)
  5. Kundli-Palm Planetary Synchronization (Graha-Mount Matrix)
"""

from __future__ import annotations

import numpy as np
import pytest

from app.data.palm_rules_seed import PALM_RULES_SEED, rule_count_by_feature
from app.models.palm_reading import PalmFeature
from app.services.palm_cv.astrology_insights import (
    assess_medical_constitution,
    classify_temperament_archetype,
    detect_dermatoglyphic_loops,
    detect_marriage_patterns,
    synchronize_palm_with_kundli,
)
from app.services.palm_cv.creases import CanonicalPalm, TracedCrease


@pytest.fixture
def dummy_canonical_palm() -> CanonicalPalm:
    size = 512
    img = np.full((size, size, 3), 180, dtype=np.uint8)
    # Add warm skin tones
    img[:, :, 0] = 210  # R
    img[:, :, 1] = 175  # G
    img[:, :, 2] = 160  # B
    mask = np.full((size, size), 255, dtype=np.uint8)
    resp = np.full((size, size), 0.05, dtype=np.float32)
    # Simulate a crease response line
    resp[200:205, 100:400] = 0.45
    return CanonicalPalm(
        image=img,
        response=resp,
        mask=mask,
        matrix=np.eye(3, dtype=np.float32),
        size=size,
        knuckles_canonical={
            "index": (0.3, 0.15),
            "middle": (0.5, 0.12),
            "ring": (0.7, 0.14),
            "pinky": (0.88, 0.20),
        },
    )


def test_dermatoglyphic_loops_detection(dummy_canonical_palm):
    """Ensure all client-specified dermatoglyphic loops can be evaluated without failure."""
    creases = {
        "head": TracedCrease(name="head", found=True, end=(0.85, 0.60)),
        "heart": TracedCrease(name="heart", found=True, continuity=0.8),
        "life": TracedCrease(name="life", found=True),
        "fate": TracedCrease(name="fate", found=True, strength=0.7),
    }
    measurements = {
        "mount_sun_mm": 1.5,
        "mount_saturn_mm": 1.6,
        "mount_jupiter_mm": 1.7,
        "mount_venus_mm": 1.8,
        "mount_mars_lower_mm": 1.5,
        "mount_moon_mm": 1.6,
        "mount_mars_upper_mm": 1.4,
    }

    loops = detect_dermatoglyphic_loops(dummy_canonical_palm, creases, measurements)
    assert len(loops) >= 5
    loop_ids = {lp["id"] for lp in loops}
    assert "loop_leisure" in loop_ids
    assert "loop_industry" in loop_ids
    assert "loop_raja" in loop_ids
    assert "loop_sensitivity" in loop_ids
    assert "loop_courage" in loop_ids

    for lp in loops:
        assert lp["found"] is True
        assert lp["confidence"] > 0.5
        assert lp["source"] == "Loops.docx"


def test_marriage_patterns_detection(dummy_canonical_palm):
    """Ensure authentic marriage cards from IMG_2718-2729 are detected and well-formed."""
    creases = {
        "head": TracedCrease(name="head", found=True),
        "heart": TracedCrease(name="heart", found=True, continuity=0.7),
        "life": TracedCrease(name="life", found=True),
        "fate": TracedCrease(name="fate", found=True, strength=0.6),
    }
    secondary = {
        "sun": TracedCrease(name="sun", found=True, strength=0.4),
        "mars": TracedCrease(name="mars", found=True, strength=0.5),
    }
    measurements = {
        "mount_moon_mm": 1.5,
        "mount_saturn_mm": 1.4,
        "mount_jupiter_mm": 1.6,
        "saturn_to_sun_deg": 7.0,
    }

    patterns = detect_marriage_patterns(dummy_canonical_palm, creases, secondary, measurements)
    assert len(patterns) >= 2
    card_ids = [p["card_id"] for p in patterns]
    # Card 6 (Moon to Fate) and Card 7 (Sister support) should trigger
    assert 6 in card_ids
    assert 7 in card_ids
    assert 8 in card_ids

    for pat in patterns:
        assert "image_ref" in pat
        assert pat["image_ref"].startswith("IMG_")
        assert len(pat["description"]) > 20


def test_temperament_archetype_classification():
    """Ensure the 17 Vedic temperament archetypes from Nature through palm.docx evaluate accurately."""
    hand_types = [
        ({"type": "Fire"}, {"dorsiflexion_deg": 188.0, "hollow_depth_mm": 7.0}, "The Restless Pioneer"),
        ({"type": "Water"}, {"finger_palm_ratio": 0.85}, "The High Intuitive Visionary"),
        ({"type": "Earth"}, {"mount_saturn_mm": 1.5}, "The Materialistic Builder"),
    ]

    for ht_data, meas, expected_archetype in hand_types:
        creases = {"head": TracedCrease(name="head", found=True), "heart": TracedCrease(name="heart", found=True)}
        res = classify_temperament_archetype(ht_data, meas, creases, [])
        assert "primary_archetype" in res
        assert "vedic_archetype_name" in res
        assert "affinity_score_pct" in res
        assert res["affinity_score_pct"] >= 70
        assert "source" in res
        assert "Nature through palm.docx" in res["source"]


def test_medical_chirology_constitution(dummy_canonical_palm):
    """Ensure clinical health palmistry markers from Health palmistry.docx evaluate properly."""
    measurements = {
        "saturn_to_sun_deg": 6.5,
        "hollow_depth_mm": 7.2,
        "mercury_length_ratio": 0.70,
    }
    skin_vitality = {
        "rgb_ratios": {"red": 0.44, "green": 0.31, "blue": 0.25},
        "vitality_score": 92,
    }
    creases = {"head": TracedCrease(name="head", found=True)}

    med = assess_medical_constitution(dummy_canonical_palm, measurements, skin_vitality, creases)
    assert "pallor_diagnosis" in med
    assert med["pallor_diagnosis"]["state"] == "Deep Red / Flushed Palm"
    assert "neuro_serotonin_axis" in med
    assert "Serotonin Sensitivity" in med["neuro_serotonin_axis"]["status"]
    assert len(med["organ_sensitivities"]) >= 3
    assert med["source"] == "Health palmistry.docx"


def test_kundli_palm_synchronization():
    """Ensure 9 Grahas map correctly to 7 Palm Mounts, Rahu, and Ketu."""
    mount_elevations = {
        "mount_sun_mm": 1.6,
        "mount_moon_mm": 1.5,
        "mount_mars_upper_mm": 1.4,
        "mount_mercury_mm": 1.3,
        "mount_jupiter_mm": 1.7,
        "mount_venus_mm": 1.8,
        "mount_saturn_mm": 1.5,
        "hollow_depth_mm": 4.5,
    }
    creases = {"heart": TracedCrease(name="heart", found=True)}
    secondary = {"sun": TracedCrease(name="sun", found=True)}

    sync = synchronize_palm_with_kundli(None, mount_elevations, creases, secondary)
    assert sync["overall_alignment_pct"] >= 80
    assert len(sync["planets"]) == 9
    graha_names = [p["graha"] for p in sync["planets"]]
    assert "Surya" in graha_names
    assert "Chandra" in graha_names
    assert "Guru" in graha_names
    assert "Shukra" in graha_names
    assert "Shani" in graha_names


def test_rule_seed_integrity_for_new_features():
    """Verify that PALM_RULES_SEED covers all new features with default fallbacks."""
    counts = rule_count_by_feature()
    assert counts.get(PalmFeature.DERMATOGLYPHIC_LOOPS.value, 0) >= 6
    assert counts.get(PalmFeature.MARRIAGE_RELATIONSHIPS.value, 0) >= 6
    assert counts.get(PalmFeature.TEMPERAMENT_ARCHETYPE.value, 0) >= 5
    assert counts.get(PalmFeature.MEDICAL_CONSTITUTION.value, 0) >= 2
    assert counts.get(PalmFeature.KUNDLI_PALM_SYNC.value, 0) >= 2


def test_palm_reading_model_and_scan_response_validation():
    """Ensure PalmReading and PalmScanResponse Pydantic models validate successfully without float_parsing errors."""
    from beanie import PydanticObjectId
    from app.models.palm_reading import PalmReading
    from app.schemas.palm_reading import PalmScanResponse

    measurements = {
        "hollow_depth_mm": 5.2,
        "archetype_affinity_pct": 88.0,
        "pallor_index": 0.85,
        "kundli_alignment_pct": 92.0,
        "temperament_archetype": "The High Intuitive Visionary",
        "pallor_state": "Radiant Pink (Optimal Ojas)",
    }

    from unittest.mock import MagicMock
    saved_settings = getattr(PalmReading, "_document_settings", None)
    try:
        PalmReading._document_settings = MagicMock()
        reading = PalmReading(
            user_id=PydanticObjectId(),
            hand="Right",
            measurements=measurements,
            temperament_archetype={"primary_archetype": "The High Intuitive Visionary"},
            medical_constitution={"pallor_diagnosis": {"state": "Radiant Pink (Optimal Ojas)"}},
            kundli_palm_sync={"overall_alignment_pct": 92},
        )
        assert reading.measurements["archetype_affinity_pct"] == 88.0
        assert reading.measurements["temperament_archetype"] == "The High Intuitive Visionary"
        assert reading.measurements["pallor_state"] == "Radiant Pink (Optimal Ojas)"
    finally:
        PalmReading._document_settings = saved_settings

    scan_resp = PalmScanResponse(
        scan_id="test_scan_123",
        status="ok",
        hand_detected=True,
        measurements=measurements,
        temperament_archetype={"primary_archetype": "The High Intuitive Visionary"},
        medical_constitution={"pallor_diagnosis": {"state": "Radiant Pink (Optimal Ojas)"}},
        kundli_palm_sync={"overall_alignment_pct": 92},
    )
    assert scan_resp.measurements["kundli_alignment_pct"] == 92.0

