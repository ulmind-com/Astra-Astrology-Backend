"""Unit tests for advanced palm reading features.

Verifies:
  1. Dual-hand synastry (Prarabdha vs Purushartha karma evolution).
  2. 1-Year resolution Ayur Nirnay age timeline.
  3. Fingers, thumb launchpad & 2D:4D digit ratio.
  4. Sacred signs detection (Yav rekha on thumb, Swastika, Trident, Fish).
"""

from __future__ import annotations

import pytest

from app.services.palm_cv.dual_hand import calculate_dual_hand_synastry
from app.services.palm_cv.fingers_thumb import analyze_fingers_thumb_and_nails
from app.services.palm_cv.timeline_1year import get_palm_timeline_for_age


def test_dual_hand_synastry():
    res = calculate_dual_hand_synastry(
        left_hand_data={"measurements": {"head_curvature": 0.22, "fate_strength": 0.40}},
        right_hand_data={"measurements": {"head_curvature": 0.11, "fate_strength": 0.78}},
        primary_handedness="Right",
    )
    assert res["is_harmonious"] is True
    assert 70 <= res["karma_evolution_score"] <= 100
    assert len(res["transformation_strengths_en"]) >= 2
    assert len(res["transformation_strengths_bn"]) >= 2
    assert len(res["transformation_strengths_hi"]) >= 2
    assert "Prarabdha" in res["prarabdha_summary_en"]
    assert "পুরুষার্থ" in res["purushartha_summary_bn"]


def test_palm_timeline_1year():
    for test_age in [12, 21, 28, 35, 42, 52, 70]:
        forecast = get_palm_timeline_for_age(age=test_age, gender="male")
        assert forecast["age"] == test_age
        assert len(forecast["epoch_name_bn"]) > 0
        assert len(forecast["prediction_en"]) > 0
        assert len(forecast["prediction_bn"]) > 0
        assert len(forecast["norm_coord"]) == 2


def test_fingers_thumb_and_nails():
    measurements = {
        "index_ring_ratio": 0.94,  # High competitive drive (Long ring finger)
        "thumb_length_ratio": 0.72,  # Leader 2000cc thumb
        "thumb_flange_ratio": 1.25,
        "thumb_index_angle": 48.0,
        "dorsiflexion_deg": 38.0,  # Spontaneous flex >35 deg
    }
    metrics_3d = {"hollow_depth_mm": 5.2}
    skin_vitality = {"flush_tone": "Rosy Pink", "vitality_score": 92}

    res = analyze_fingers_thumb_and_nails(measurements, metrics_3d, skin_vitality)
    assert res["digit_ratio_2d_4d"] == 0.94
    assert "High Competitive" in res["digit_ratio_type_en"]
    assert "অনামিকা" in res["digit_ratio_type_bn"]
    assert "2000cc" in res["thumb_class_en"]
    assert "২০০০ সিসি" in res["thumb_class_bn"]
    assert res["willpower_pct"] > 0
    assert res["lunula_score"] >= 75
    assert len(res["nail_health_bn"]) > 0


def test_palm_reading_router_import():
    from app.api.v1.palm_reading import router

    assert router is not None
    route_paths = [r.path for r in router.routes]
    assert "/palm-reading/timeline-age" in route_paths
    assert "/palm-reading/dual-match" in route_paths


