"""Unit tests for 16-Zone, 32-Pada Vastu Shastra Engine."""

import pytest
from app.services.astrology.vastu_engine import (
    PADA_DEFINITIONS,
    ZONE_METADATA,
    perform_vastu_audit,
    resolve_entrance_pada,
)


def test_pada_count_and_anchors():
    assert len(PADA_DEFINITIONS) == 32
    # Verify N5 is centered at 0° (or 354.375° to 5.625°)
    n5 = [p for p in PADA_DEFINITIONS if p["pada_id"] == "N5"][0]
    assert n5["quadrant"] == "North"
    assert n5["center"] == 354.375  # Spans across 0° North


def test_auspicious_entrances():
    # Test Golden Doors: N3, N4, E3, E4, S3, S4, W3, W4
    auspicious_ids = {p["pada_id"] for p in PADA_DEFINITIONS if p["auspicious"]}
    expected = {"N3", "N4", "E3", "E4", "S3", "S4", "W3", "W4"}
    assert auspicious_ids == expected


def test_resolve_pada_trigonometry():
    # 0.0° should resolve to N5
    p0 = resolve_entrance_pada(0.0)
    assert p0.pada_id in ("N5", "N6")  # Right at the meridian

    # 62.0° should resolve to E3 (Jayanta - Auspicious)
    p_e3 = resolve_entrance_pada(62.0)
    assert p_e3.pada_id == "E3"
    assert p_e3.is_auspicious is True
    assert p_e3.deity == "Jayanta (জয়ন্ত)"

    # 175.0° should resolve to S5 (Yama - Malefic)
    p_s5 = resolve_entrance_pada(175.0)
    assert p_s5.pada_id == "S5"
    assert p_s5.is_auspicious is False


def test_16_zones_metadata():
    assert len(ZONE_METADATA) == 16
    for code, z in ZONE_METADATA.items():
        assert "element" in z
        assert "dosha" in z
        assert "organs" in z
        assert "self_colors" in z
        assert len(z["ideal"]) > 0
        assert len(z["prohibited"]) > 0


def test_full_vastu_audit_excellent():
    res = perform_vastu_audit(
        main_entrance_degree=62.0,  # E3 Jayanta (Auspicious)
        placements={
            "kitchen": "SE",
            "master_bed": "SW",
            "toilet": "SSW",
            "puja_room": "NE",
            "underground_water": "N",
            "overhead_tank": "W",
            "locker": "N",
        }
    )
    assert res.overall_score >= 90
    assert "A+" in res.grade
    assert res.main_entrance_pada.is_auspicious is True
    assert len(res.evaluations) == 7
    assert len(res.warnings_critical) == 0


def test_full_vastu_audit_critical_defects():
    res = perform_vastu_audit(
        main_entrance_degree=175.0,  # S5 Yama
        placements={
            "kitchen": "NE",  # Severe Fire in Ishanya
            "toilet": "NE",   # Severe Defect
            "puja_room": "SW", # Severe Defect
        }
    )
    assert res.overall_score <= 40
    assert "C" in res.grade
    assert len(res.warnings_critical) >= 3
    # Check that metal strip blocking is provided for toilet in NE
    toilet_eval = [e for e in res.evaluations if e.category_id == "toilet"][0]
    assert toilet_eval.metal_strip_blocking is not None
