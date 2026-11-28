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
    # Verify N5 is centered at 0.0° (spans 354.375° to 5.625°)
    n5 = [p for p in PADA_DEFINITIONS if p["pada_id"] == "N5"][0]
    assert n5["quadrant"] == "North"
    assert n5["center"] == 0.0  # Centered at 0.0° True North


def test_auspicious_entrances():
    # Test Golden Doors: N3, N4, E3, E4, S3, S4, W3, W4
    auspicious_ids = {p["pada_id"] for p in PADA_DEFINITIONS if p["auspicious"]}
    expected = {"N3", "N4", "E3", "E4", "S3", "S4", "W3", "W4"}
    assert auspicious_ids == expected


def test_resolve_pada_trigonometry():
    # 0.0° should resolve to N5
    p0 = resolve_entrance_pada(0.0)
    assert p0.pada_id == "N5"

    # 65.0° should resolve to E3 (Jayanta - Auspicious, span 61.875° - 73.125°)
    p_e3 = resolve_entrance_pada(65.0)
    assert p_e3.pada_id == "E3"
    assert p_e3.is_auspicious is True
    assert p_e3.deity == "Jayanta (জয়ন্ত)"

    # 175.0° should resolve to S5 (Yama - Malefic, span 174.375° - 185.625°)
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
        main_entrance_degree=65.0,  # E3 Jayanta (Auspicious, 61.875° - 73.125°)
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


def test_ayadi_shadvarga_calculation():
    from app.services.astrology.vastu_engine import calculate_ayadi_shadvarga
    # Test a plot of 40ft x 30ft = 1200 sqft
    res = calculate_ayadi_shadvarga(length=40.0, width=30.0, unit="feet")
    assert res.area_sqft == 1200.0
    assert 1 <= res.aaya_number <= 8
    assert res.aaya_name is not None
    assert res.structure_longevity_years > 0
    assert res.building_nakshatra_number >= 1
    assert 1 <= res.yoni_number <= 8
    assert res.varna_name_bn != ""
    assert res.tithi_name_bn != ""
    assert res.vara_name_bn != ""
    assert res.shadvarga_score > 0
    assert len(res.rectification_suggestions_bn) > 0

    # Test hasta units (1 hasta = 1.5 feet)
    res_hasta = calculate_ayadi_shadvarga(length=20.0, width=15.0, unit="hasta")
    assert res_hasta.length == 20.0
    assert res_hasta.area_sqft == (20.0 * 1.5) * (15.0 * 1.5)


def test_medical_vastu_catalog():
    from app.services.astrology.vastu_engine import get_medical_vastu_catalog
    catalog = get_medical_vastu_catalog()
    assert len(catalog) >= 10
    depression = [c for c in catalog if c.ailment_id == "depression_sorrow"][0]
    assert depression.affected_zone == "WNW"
    assert "Space/Metal" in depression.affected_element


def test_astrovastu_rules():
    from app.services.astrology.vastu_engine import get_astrovastu_rules
    rules = get_astrovastu_rules()
    assert len(rules) == 9
    rahu = [r for r in rules if r.planet_id == "rahu"][0]
    assert "SW" in rahu.governing_direction
    assert len(rahu.critical_dos_bn) > 0

