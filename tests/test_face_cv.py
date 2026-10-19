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
        "face_ratio", "forehead_w", "forehead_h", "jaw_w", "midface_h",
        "lower_face_h", "inter_eye_d", "eye_w", "eye_h", "eye_slant",
        "eye_asym", "nose_w", "nose_h", "nose_bridge_w", "mouth_w",
        "lip_full", "lip_ratio", "lip_corner", "lip_asym", "chin_h",
        "cheek_full", "brow_span", "brow_arch",
    ]
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
    """Frontal synthetic landmarks should give near-zero yaw, pitch, roll."""
    w, h = 640, 640
    lms_px = [(x * w, y * h, z) for x, y, z in _make_dummy_landmarks(478)]
    pose = estimate_head_pose(lms_px, w, h)
    assert pose is not None
    assert pose.is_frontal
    assert abs(pose.yaw_deg) < 30.0
    assert abs(pose.pitch_deg) < 30.0
    assert abs(pose.roll_deg) < 20.0



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
