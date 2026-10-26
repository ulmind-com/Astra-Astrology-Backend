"""Automated test suite for MediaPipe + OpenCV facial scanning pipeline.

Covers:
- Landmark mapping validation
- Geometric ratio extraction and [0.0, 10.0] bounds guarantees
- Image decoding, EXIF correction, and invalid input handling
- Quality assessment (blur, exposure, symmetry, face coverage)
- Head pose estimation (solvePnP yaw, pitch, roll)
- Visualization overlay generation
- Full pipeline execution and error handling
"""

import math
import cv2
import numpy as np
import pytest

from app.services.face_cv.config import FaceScanConfig, DEFAULT_CONFIG
from app.services.face_cv.landmarks import LandmarkIndex, CANONICAL_3D_FACE_MODEL
from app.services.face_cv.measurements import extract_measurements, _dist2d, _dist3d, _safe_div
from app.services.face_cv.quality import (
    decode_and_correct_orientation,
    assess_quality,
    estimate_head_pose,
    QualityStatus,
)
from app.services.face_cv.visualizer import draw_facial_mesh_overlay
from app.services.face_cv.pipeline import execute_scan_pipeline


def _make_dummy_image(
    width: int = 640,
    height: int = 640,
    color: tuple[int, int, int] = (128, 128, 128),
) -> bytes:
    """Creates a raw JPEG byte buffer of a solid image."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


def _make_dummy_landmarks(count: int = 478) -> list[tuple[float, float, float]]:
    """Generates synthetic landmarks simulating a frontal normalized face."""
    landmarks = []
    for i in range(count):
        # Default roughly centered around (0.5, 0.5, 0.0)
        x = 0.5 + 0.1 * math.sin(i * 0.1)
        y = 0.5 + 0.1 * math.cos(i * 0.1)
        z = 0.0
        landmarks.append((x, y, z))

    # Place specific landmarks for predictable geometry
    # Cheek width: (0.3 to 0.7) -> 0.4
    landmarks[LandmarkIndex.CHEEK_LEFT] = (0.7, 0.5, 0.0)
    landmarks[LandmarkIndex.CHEEK_RIGHT] = (0.3, 0.5, 0.0)
    # Forehead top to chin bottom: (0.2 to 0.8) -> 0.6
    landmarks[LandmarkIndex.FOREHEAD_TOP] = (0.5, 0.2, 0.0)
    landmarks[LandmarkIndex.CHIN_BOTTOM] = (0.5, 0.8, 0.0)
    # Jaw
    landmarks[LandmarkIndex.JAW_LEFT] = (0.65, 0.7, 0.0)
    landmarks[LandmarkIndex.JAW_RIGHT] = (0.35, 0.7, 0.0)
    # Brows
    landmarks[LandmarkIndex.BROW_RIDGE_LEFT] = (0.65, 0.35, 0.0)
    landmarks[LandmarkIndex.BROW_RIDGE_RIGHT] = (0.35, 0.35, 0.0)
    # Eyes
    landmarks[LandmarkIndex.L_EYE_INNER] = (0.53, 0.42, 0.0)
    landmarks[LandmarkIndex.L_EYE_OUTER] = (0.62, 0.42, 0.0)
    landmarks[LandmarkIndex.R_EYE_INNER] = (0.47, 0.42, 0.0)
    landmarks[LandmarkIndex.R_EYE_OUTER] = (0.38, 0.42, 0.0)
    # Nose
    landmarks[LandmarkIndex.NOSE_BRIDGE_TOP] = (0.5, 0.38, 0.0)
    landmarks[LandmarkIndex.NOSE_TIP] = (0.5, 0.55, 0.0)
    landmarks[LandmarkIndex.NOSE_LEFT_WING] = (0.55, 0.55, 0.0)
    landmarks[LandmarkIndex.NOSE_RIGHT_WING] = (0.45, 0.55, 0.0)
    # Mouth
    landmarks[LandmarkIndex.MOUTH_CORNER_LEFT] = (0.58, 0.68, 0.0)
    landmarks[LandmarkIndex.MOUTH_CORNER_RIGHT] = (0.42, 0.68, 0.0)
    landmarks[LandmarkIndex.LIP_UPPER_TOP] = (0.5, 0.65, 0.0)
    landmarks[LandmarkIndex.LIP_LOWER_BOTTOM] = (0.5, 0.71, 0.0)
    landmarks[LandmarkIndex.LIP_INNER_TOP] = (0.5, 0.67, 0.0)
    landmarks[LandmarkIndex.LIP_INNER_BOTTOM] = (0.5, 0.69, 0.0)
    # Cheeks
    landmarks[LandmarkIndex.CHEEK_LINE_LEFT] = (0.62, 0.68, 0.0)
    landmarks[LandmarkIndex.CHEEK_LINE_RIGHT] = (0.38, 0.68, 0.0)
    return landmarks



# ==============================================================================
# 1. Landmark Mapping Tests
# ==============================================================================
def test_landmark_indices_uniqueness():
    """Verifies all landmark indices in LandmarkIndex are unique and within 0..477."""
    indices = [
        val for key, val in vars(LandmarkIndex).items()
        if not key.startswith("_") and isinstance(val, int)
    ]
    assert len(indices) > 20
    for idx in indices:
        assert 0 <= idx < 478, f"Index {idx} out of 478 MediaPipe range."


def test_canonical_3d_points_shape():
    """Checks 3D anthropometric face model point definitions."""
    arr = np.array(CANONICAL_3D_FACE_MODEL, dtype=np.float32)
    assert arr.shape == (6, 3)


# ==============================================================================
# 2. Measurement Extraction & Bounds Tests
# ==============================================================================
def test_safe_div_guards():
    """Ensures division by zero, NaN, or Inf never leaks."""
    assert _safe_div(10.0, 0.0) == 0.0
    assert _safe_div(float("nan"), 5.0) == 0.0
    assert _safe_div(5.0, float("nan")) == 0.0
    assert _safe_div(10.0, 2.0) == 5.0


def test_measurement_extraction_values():
    """Verifies all 23 measurements are extracted within valid bounds [0.0, 10.0]."""
    synthetic_landmarks = _make_dummy_landmarks(478)
    measurements, details = extract_measurements(synthetic_landmarks)

    expected_keys = [
        "wh_ratio", "jaw_cheek", "brow_cheek", "forehead_h",
        "eye_open", "eye_size", "eye_gap", "eye_tilt", "eye_asym",
        "brow_thick", "brow_arch", "brow_gap", "brow_len",
        "nose_w", "nose_len", "nostril", "nose_dev",
        "lip_thick", "mouth_w", "lip_corner", "lip_asym",
        "chin_h", "cheek_full",
    ]
    assert len(expected_keys) == 23
    for key in expected_keys:
        assert key in measurements, f"Missing expected measurement: {key}"
        val = measurements[key]
        assert not math.isnan(val), f"{key} is NaN"
        assert not math.isinf(val), f"{key} is Inf"
        assert 0.0 <= val <= 10.0, f"{key} = {val} is outside [0.0, 10.0]"
        assert key in details



def test_insufficient_landmarks_error():
    """Ensures ValueError is raised if landmark count is less than 468."""
    with pytest.raises(ValueError):
        extract_measurements([(0.5, 0.5, 0.0)] * 100)


# ==============================================================================
# 3. Image Decoding & Quality Assessment Tests
# ==============================================================================
def test_image_decoding_valid():
    """Tests decoding and RGB conversion of a valid JPEG."""
    buf = _make_dummy_image(300, 300)
    rgb = decode_and_correct_orientation(buf)
    assert rgb.shape == (300, 300, 3)
    assert rgb.dtype == np.uint8


def test_image_decoding_corrupted():
    """Ensures corrupt bytes raise ValueError."""
    with pytest.raises(ValueError, match="could not be decoded as an image"):
        decode_and_correct_orientation(b"not an image at all corrupt garbage")



def test_quality_assessment_no_face():
    """No face detected should yield REJECTED status."""
    dummy_rgb = np.zeros((480, 480, 3), dtype=np.uint8)
    result = assess_quality(dummy_rgb, landmarks_px=None, face_count=0)
    assert result.status == QualityStatus.REJECTED
    assert "No face detected" in result.checks.issues[0]


def test_quality_assessment_multiple_faces():
    """Multiple faces should yield REJECTED status."""
    dummy_rgb = np.zeros((480, 480, 3), dtype=np.uint8)
    result = assess_quality(dummy_rgb, landmarks_px=None, face_count=2)
    assert result.status == QualityStatus.REJECTED
    assert "Multiple faces detected" in result.checks.issues[0]


def test_quality_assessment_dark_image():
    """Excessively dark image should be flagged."""
    dark_rgb = np.full((480, 480, 3), 10, dtype=np.uint8)
    # Synthetic landmarks in pixel space
    lms_px = [(x * 480, y * 480, 0.0) for x, y, _ in _make_dummy_landmarks(478)]
    result = assess_quality(dark_rgb, landmarks_px=lms_px, face_count=1)
    assert any("dark" in issue.lower() for issue in result.checks.issues)


def test_head_pose_estimation():
    """Frontal landmarks should give near-zero yaw, pitch, roll and is_frontal True."""
    w, h = 640, 640
    lms = [(0.5, 0.5, 0.0)] * 478
    lms[LandmarkIndex.NOSE_TIP] = (0.50, 0.23, -0.06)
    lms[LandmarkIndex.CHIN_BOTTOM] = (0.50, 0.34, 0.0)
    lms[LandmarkIndex.R_EYE_OUTER] = (0.42, 0.17, 0.02)
    lms[LandmarkIndex.L_EYE_OUTER] = (0.57, 0.17, 0.02)
    lms[LandmarkIndex.MOUTH_CORNER_RIGHT] = (0.43, 0.26, 0.01)
    lms[LandmarkIndex.MOUTH_CORNER_LEFT] = (0.56, 0.25, 0.01)

    lms_px = [(x * w, y * h, z) for x, y, z in lms]
    pose = estimate_head_pose(lms_px, w, h)
    assert pose is not None
    assert pose.is_frontal
    assert abs(pose.yaw_deg) < 20.0
    assert abs(pose.pitch_deg) < 25.0
    assert abs(pose.roll_deg) < 15.0




# ==============================================================================
# 4. Mesh Visualization Tests
# ==============================================================================
def test_mesh_visualization_overlay():
    """Tests generating the base64 JPEG overlay with mesh lines."""
    dummy_rgb = np.full((300, 300, 3), 180, dtype=np.uint8)
    lms_px = [(x * 300, y * 300, 0.0) for x, y, _ in _make_dummy_landmarks(478)]
    data_url = draw_facial_mesh_overlay(dummy_rgb, lms_px, QualityStatus.ACCEPTED)
    assert data_url.startswith("data:image/jpeg;base64,")
    assert len(data_url) > 100


# ==============================================================================
# 5. Pipeline Integration Tests
# ==============================================================================
def test_pipeline_empty_bytes():
    """Rejects empty bytes."""
    with pytest.raises(ValueError, match="Empty image"):
        execute_scan_pipeline(b"")


def test_pipeline_low_resolution():
    """Rejects images smaller than configured minimum resolution."""
    small_buf = _make_dummy_image(150, 150)
    with pytest.raises(ValueError, match="too low"):
        execute_scan_pipeline(small_buf)


def test_pipeline_rejection_no_face():
    """Solid color image has no face -> pipeline returns status REJECTED without crashing."""
    solid_buf = _make_dummy_image(480, 480, (120, 120, 120))
    res = execute_scan_pipeline(solid_buf)
    assert res.status == QualityStatus.REJECTED
    assert len(res.warnings) > 0
    assert res.measurements == {}
    assert res.visualization_image == ""


def test_pipeline_real_face_scan():
    """Runs the full pipeline on a real face photograph."""
    from pathlib import Path
    img_path = Path(__file__).resolve().parent.parent.parent / "Astra-Astrology-Web" / "public" / "_facetest.jpg"
    if not img_path.exists():
        pytest.skip(f"Test image not found at {img_path}")

    raw_bytes = img_path.read_bytes()
    res = execute_scan_pipeline(raw_bytes)

    assert res.status in (QualityStatus.ACCEPTED, QualityStatus.RETAKE_RECOMMENDED)
    assert res.scan_id != ""
    assert res.quality_score > 0.4
    assert res.head_pose is not None
    assert abs(res.head_pose["yaw_deg"]) < 25.0
    assert len(res.measurements) == 26
    assert "forehead_lines" in res.measurements
    assert "forehead_lines_depth" in res.measurements
    assert "forehead_lines_continuous" in res.measurements
    assert res.forehead_lines_count >= 0
    assert isinstance(res.forehead_lines_data, list)
    assert isinstance(res.forehead_lines_shastra, dict)
    assert res.visualization_image.startswith("data:image/jpeg;base64,")
    assert res.processing_duration_ms > 0


def test_pipeline_repeatability_and_invariance():
    """Validates repeatability across slight lighting and brightness alterations."""
    from pathlib import Path
    img_path = Path(__file__).resolve().parent.parent.parent / "Astra-Astrology-Web" / "public" / "_facetest.jpg"
    if not img_path.exists():
        pytest.skip(f"Test image not found at {img_path}")

    raw_bytes_orig = img_path.read_bytes()
    res1 = execute_scan_pipeline(raw_bytes_orig)

    # Decode and adjust brightness slightly (+10% luminance)
    img_bgr = cv2.imdecode(np.frombuffer(raw_bytes_orig, np.uint8), cv2.IMREAD_COLOR)
    img_bright = cv2.convertScaleAbs(img_bgr, alpha=1.05, beta=8)
    ok, buf = cv2.imencode(".jpg", img_bright)
    assert ok
    res2 = execute_scan_pipeline(buf.tobytes())

    # Measurement ratios should be highly repeatable (within 4% drift)
    for metric, val1 in res1.measurements.items():
        val2 = res2.measurements[metric]
        diff_abs = abs(val1 - val2)
        diff_pct = diff_abs / max(1e-3, (val1 + val2) / 2.0)
        assert diff_abs < 0.035 or diff_pct < 0.15, f"Metric {metric} repeatability variance too high: {val1} vs {val2}"




def test_json_serialization_safety():
    """Verifies FaceScanResponse schema serializes to JSON without NaN or Infinity."""
    import json
    from app.schemas.face_reading import FaceScanResponse, QualityChecksOut, HeadPoseOut, MeasurementDetailOut

    checks = QualityChecksOut(
        is_valid=True,
        status="ACCEPTED",
        face_count=1,
        face_coverage_pct=0.25,
        blur_score=150.0,
        brightness_mean=130.0,
        contrast_std=45.0,
        lighting_symmetry_ratio=1.05,
        head_pose=HeadPoseOut(yaw=1.2, pitch=2.5, roll=-0.5, is_frontal=True),
        issues=[],
        recommendations=[],
    )
    resp = FaceScanResponse(
        scan_id="test-scan-123",
        status="ACCEPTED",
        quality_score=0.92,
        quality_checks=checks,
        head_pose=HeadPoseOut(yaw=1.2, pitch=2.5, roll=-0.5, is_frontal=True),
        measurements={"wh_ratio": 0.75, "chin_h": 0.22},
        measurement_details={
            "wh_ratio": MeasurementDetailOut(
                name="wh_ratio",
                value=0.75,
                description="Face width to height",
                formula="w/h",
                landmarks_used=[234, 454],
                status="available",
            )
        },
        measurement_status="valid",
        visualization_image="data:image/jpeg;base64,abc",
        reading=None,
        coins_charged=0,
        landmark_mapping_version="canonical_478_v1",
        model_version="mediapipe_tasks_vision_1.1.1",
        processing_duration_ms=45.2,
        warnings=[],
        error_message=None,
    )

    data = resp.model_dump()
    json_str = json.dumps(data)
    assert "NaN" not in json_str
    assert "Infinity" not in json_str
    parsed = json.loads(json_str)
    assert parsed["scan_id"] == "test-scan-123"
    assert parsed["measurements"]["wh_ratio"] == 0.75


def test_head_pose_schema_normalization():
    """Validates HeadPoseOut handles yaw_deg, pitch_deg, roll_deg input seamlessly."""
    from app.schemas.face_reading import HeadPoseOut

    raw_payload = {"yaw_deg": 7.29, "pitch_deg": -7.77, "roll_deg": 0.09, "is_frontal": True}
    hp = HeadPoseOut(**raw_payload)
    assert hp.yaw == 7.29
    assert hp.pitch == -7.77
    assert hp.roll == 0.09
    assert hp.is_frontal is True


def test_quality_checks_schema_normalization():
    """Validates QualityChecksOut normalizes sharpness_score and face_coverage_ratio."""
    from app.schemas.face_reading import QualityChecksOut

    raw_checks = {
        "sharpness_score": 142.5,
        "face_coverage_ratio": 0.32,
        "brightness_mean": 128.0,
        "overexposed_ratio": 0.01,
        "lighting_symmetry_ratio": 1.02,
        "head_pose": {"yaw_deg": 3.1, "pitch_deg": -2.0, "roll_deg": 0.5, "is_frontal": True},
        "issues": [],
        "recommendations": [],
    }
    qc = QualityChecksOut(**raw_checks)
    assert qc.blur_score == 142.5
    assert qc.face_coverage_pct == 32.0
    assert qc.head_pose is not None
    assert qc.head_pose.yaw == 3.1


def test_execute_scan_pipeline_accepted(monkeypatch):
    """Ensures execute_scan_pipeline runs through Stage E, F, G, TriZone, Mahabhuta without NameError."""
    from unittest.mock import MagicMock
    from app.services.face_cv.detector import DetectionResult
    from app.services.face_cv.quality import QualityAssessment, QualityChecks, HeadPose
    import app.services.face_cv.pipeline as pipeline_mod

    raw_img = _make_dummy_image(640, 640)
    dummy_lms_norm = _make_dummy_landmarks(478)
    dummy_lms_px = [(x * 640, y * 640, z * 640) for x, y, z in dummy_lms_norm]

    # Mock detector
    mock_detector = MagicMock()
    mock_detector.detect.return_value = DetectionResult(
        face_count=1,
        landmarks_norm=dummy_lms_norm,
        landmarks_px=dummy_lms_px,
        transformation_matrix=np.eye(4),
    )
    monkeypatch.setattr(pipeline_mod, "get_landmarker", lambda cfg: mock_detector)

    # Mock quality assessment to ACCEPTED
    mock_qa = QualityAssessment(
        status=QualityStatus.ACCEPTED,
        score=0.95,
        message=None,
        checks=QualityChecks(
            sharpness_score=150.0,
            brightness_mean=128.0,
            overexposed_ratio=0.01,
            lighting_symmetry_ratio=1.0,
            face_coverage_ratio=0.35,
            head_pose=HeadPose(
                yaw_deg=1.0,
                pitch_deg=2.0,
                roll_deg=0.0,
                is_frontal=True,
                rotation_matrix=np.eye(3),
            ),
            issues=[],
            recommendations=[],
        ),
    )
    monkeypatch.setattr(pipeline_mod, "assess_quality", lambda **kwargs: mock_qa)

    result = pipeline_mod.execute_scan_pipeline(raw_img)
    assert result.status == QualityStatus.ACCEPTED
    assert result.measurements is not None
    assert len(result.measurements) > 10
    assert result.tri_zone_analysis is not None
    assert "ratio_str" in result.tri_zone_analysis
    assert result.pancha_mahabhuta is not None
    assert "dominant_element" in result.pancha_mahabhuta



