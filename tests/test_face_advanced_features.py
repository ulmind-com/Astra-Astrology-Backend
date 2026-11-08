import pytest
from app.services.face_cv.depth_volumetric import calculate_3d_volumetric_measurements
from app.services.face_cv.timeline_100 import get_timeline_forecast_for_age
from app.services.face_cv.ayurveda import analyze_ayurvedic_prakriti
from app.services.face_cv.birth_rectification import evaluate_birth_time_rectification
from app.services.face_cv.couple_matching import calculate_couple_face_compatibility


def test_3d_volumetric_measurements():
    # 478 mock 3d landmarks
    mock_3d = [[0.5, 0.5, -0.05 * (i % 10)] for i in range(478)]
    res = calculate_3d_volumetric_measurements(mock_3d)
    assert "forehead_inclination_3d" in res
    assert "nose_projection_3d" in res
    assert "cheek_prominence_3d" in res
    assert "chin_projection_3d" in res
    assert "volumetric_convexity_3d" in res


def test_timeline_100():
    for age in [14, 28, 35, 48, 65]:
        forecast = get_timeline_forecast_for_age(age, {})
        assert forecast["age"] == age
        assert len(forecast["epoch_name_en"]) > 0
        assert len(forecast["epoch_name_bn"]) > 0
        assert len(forecast["prediction_en"]) > 0
        assert 0.0 <= forecast["norm_x"] <= 1.0
        assert 0.0 <= forecast["norm_y"] <= 1.0


def test_ayurvedic_prakriti():
    measurements = {
        "face_ratio": 1.45,
        "jaw_width_ratio": 0.68,
        "lip_fullness": 0.28,
        "eye_aspect_ratio": 0.26,
    }
    prakriti = analyze_ayurvedic_prakriti(measurements)
    assert prakriti["dominant_dosha"] in ("Vata", "Pitta", "Kapha")
    assert prakriti["vata_percentage"] > 0
    assert prakriti["pitta_percentage"] > 0
    assert prakriti["kapha_percentage"] > 0
    assert prakriti["ojas_score"] >= 60.0
    assert len(prakriti["diet_advice_bn"]) > 0
    assert len(prakriti["lifestyle_advice_bn"]) > 0


def test_birth_rectification():
    measurements = {
        "jaw_width_ratio": 0.78,
        "forehead_height_ratio": 0.35,
        "symmetry_index": 0.94,
    }
    rect = evaluate_birth_time_rectification(
        birth_lagna_sign="Aries",
        lagna_lord="Mars",
        measurements=measurements,
    )
    assert rect["birth_lagna"] == "Aries"
    assert rect["match_confidence_pct"] >= 75.0
    assert len(rect["rectification_guidance_bn"]) > 0


def test_couple_face_compatibility():
    p1 = {"symmetry_index": 0.92, "lip_fullness": 0.36, "face_ratio": 1.34}
    p2 = {"symmetry_index": 0.90, "lip_fullness": 0.38, "face_ratio": 1.32}
    match = calculate_couple_face_compatibility(p1, p2)
    assert match["overall_compatibility_score"] >= 70.0
    assert len(match["strengths_en"]) > 0
    assert len(match["strengths_bn"]) > 0
    assert len(match["harmonizing_advice_bn"]) > 0
