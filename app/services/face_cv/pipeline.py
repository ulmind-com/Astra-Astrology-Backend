"""Complete facial scanning pipeline orchestrator (Stages A through G)."""

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from app.services.face_cv.config import DEFAULT_CONFIG, FaceScanConfig
from app.services.face_cv.detector import get_landmarker
from app.services.face_cv.forehead_analyzer import analyze_forehead_lines
from app.services.face_cv.landmarks import LandmarkIndex as P
from app.services.face_cv.measurements import (
    MeasurementDetail,
    canonicalize_landmarks_3d,
    extract_measurements,
)
from app.services.face_cv.quality import (
    QualityStatus,
    assess_quality,
    decode_and_correct_orientation,
)
from app.services.face_cv.visualizer import draw_facial_mesh_overlay


@dataclass
class ScanPipelineResult:
    scan_id: str
    status: QualityStatus
    quality_score: float
    quality_checks: dict[str, Any]
    head_pose: dict[str, float] | None
    measurements: dict[str, float]
    measurement_details: dict[str, dict[str, Any]]
    visualization_image: str  # data:image/jpeg;base64,...
    processing_duration_ms: float
    warnings: list[str]
    error_message: str | None = None
    forehead_lines_count: int = 0
    forehead_lines_data: list[dict[str, Any]] = field(default_factory=list)
    forehead_lines_shastra: dict[str, str] = field(default_factory=dict)
    landmark_mapping_version: str = "canonical_478_v1"
    model_version: str = "mediapipe_tasks_vision_1.1.1"


def execute_scan_pipeline(
    raw_image_bytes: bytes,
    config: FaceScanConfig = DEFAULT_CONFIG,
) -> ScanPipelineResult:
    """Executes the complete production-grade facial scanning pipeline.

    Stages:
        Stage A: Image capture, validation, EXIF correction, OpenCV decoding.
        Stage C: MediaPipe Tasks Face Landmarker execution.
        Stage B & D: OpenCV quality & head pose assessment.
        Stage E: 23 Vedic geometric measurements calculation.
        Stage G: Mesh and landmark overlay visualization.
    """
    start_time = time.perf_counter()
    scan_id = str(uuid.uuid4())

    # --- Stage A: Image capture and validation ---
    if not raw_image_bytes:
        raise ValueError("Empty image payload received.")

    if len(raw_image_bytes) > config.max_file_size_bytes:
        max_mb = config.max_file_size_bytes // (1024 * 1024)
        raise ValueError(f"Image exceeds maximum allowed size of {max_mb} MB.")

    try:
        img_rgb = decode_and_correct_orientation(raw_image_bytes)
    except Exception as e:
        raise ValueError(f"Could not decode image: {str(e)}")

    h, w, _ = img_rgb.shape
    if w < config.min_image_width or h < config.min_image_height:
        raise ValueError(
            f"Image resolution {w}x{h} is too low. Minimum required resolution is "
            f"{config.min_image_width}x{config.min_image_height} pixels."
        )

    # --- Stage C: MediaPipe Face Landmarker detection ---
    detector = get_landmarker(config)
    detection = detector.detect(img_rgb)

    # --- Stage B & D: Quality & Head Pose Assessment ---
    quality_assessment = assess_quality(
        img_rgb=img_rgb,
        landmarks_px=detection.landmarks_px,
        face_count=detection.face_count,
        config=config,
    )

    def _format_pose(hp_obj):
        if not hp_obj:
            return None
        d = asdict(hp_obj) if hasattr(hp_obj, "__dataclass_fields__") else dict(hp_obj)
        d["yaw"] = round(float(d.get("yaw_deg", d.get("yaw", 0.0))), 2)
        d["pitch"] = round(float(d.get("pitch_deg", d.get("pitch", 0.0))), 2)
        d["roll"] = round(float(d.get("roll_deg", d.get("roll", 0.0))), 2)
        d["is_frontal"] = bool(d.get("is_frontal", True))
        d.pop("rotation_matrix", None)
        return d

    def _format_checks(checks_obj, status_val, face_cnt):
        d = asdict(checks_obj) if hasattr(checks_obj, "__dataclass_fields__") else dict(checks_obj)
        d["face_count"] = face_cnt
        d["is_valid"] = status_val != QualityStatus.REJECTED
        d["status"] = status_val.value if hasattr(status_val, "value") else str(status_val)
        cov = float(d.get("face_coverage_ratio", 0.0))
        d["face_coverage_pct"] = round(cov * 100.0, 2)
        d["blur_score"] = round(float(d.get("sharpness_score", 0.0)), 2)
        d["contrast_std"] = round(float(d.get("contrast_std", 0.0)), 2)
        if d.get("head_pose"):
            d["head_pose"] = _format_pose(d["head_pose"])
        return d

    # If rejected, construct early response with quality breakdown and guidance
    if quality_assessment.status == QualityStatus.REJECTED:
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 1)
        pose_dict = _format_pose(quality_assessment.checks.head_pose)
        checks_dict = _format_checks(
            quality_assessment.checks, QualityStatus.REJECTED, detection.face_count
        )

        return ScanPipelineResult(
            scan_id=scan_id,
            status=QualityStatus.REJECTED,
            quality_score=quality_assessment.score,
            quality_checks=checks_dict,
            head_pose=pose_dict,
            measurements={},
            measurement_details={},
            visualization_image="",
            processing_duration_ms=duration_ms,
            warnings=quality_assessment.checks.issues,
            error_message=quality_assessment.message,
            landmark_mapping_version=config.landmark_mapping_version,
            model_version=config.model_version,
        )

    # --- Stage E: Facial feature extraction with 3D Pose Normalization ---
    assert detection.landmarks_norm is not None, "Landmarks must be present for accepted image"
    pose_checks = quality_assessment.checks.head_pose
    rot_mat = pose_checks.rotation_matrix if pose_checks else None
    canonical_landmarks = canonicalize_landmarks_3d(detection.landmarks_norm, rot_mat)
    measurements, details = extract_measurements(canonical_landmarks)

    # --- Stage F: Biometric Forehead Wrinkle & Planetary Line Analysis ---
    assert detection.landmarks_px is not None
    forehead_analysis = analyze_forehead_lines(img_rgb, detection.landmarks_px)

    measurements["forehead_lines"] = float(forehead_analysis.lines_count)
    measurements["forehead_lines_depth"] = float(forehead_analysis.avg_prominence)
    measurements["forehead_lines_continuous"] = float(forehead_analysis.continuity_ratio)

    details["forehead_lines"] = MeasurementDetail(
        name="Forehead Line Count (কপালের রেখা সংখ্যা)",
        value=float(forehead_analysis.lines_count),
        description="Detected horizontal forehead wrinkles / planetary crease lines (0 to 7)",
        formula="Gabor filter bank + ridge contour clustering",
        landmarks_used=[P.FOREHEAD_TOP, P.GLABELLA, P.BROW_RIDGE_RIGHT, P.BROW_RIDGE_LEFT],
        status="available",
    )
    details["forehead_lines_depth"] = MeasurementDetail(
        name="Forehead Line Depth / Prominence",
        value=float(forehead_analysis.avg_prominence),
        description=(
            "Normalized contrast depth and prominence of detected forehead creases (0.0 to 1.0)"
        ),
        formula="CLAHE gradient contrast / local skin background",
        landmarks_used=[P.FOREHEAD_TOP, P.GLABELLA],
        status="available",
    )
    details["forehead_lines_continuous"] = MeasurementDetail(
        name="Forehead Line Continuity Ratio",
        value=float(forehead_analysis.continuity_ratio),
        description="Ratio of continuous, unbroken horizontal crease lines across the forehead",
        formula="continuous_length / total_span_width",
        landmarks_used=[P.FOREHEAD_TOP, P.GLABELLA],
        status="available",
    )

    # --- Stage G: Face mesh visualization ---
    vis_data_url = draw_facial_mesh_overlay(
        img_rgb=img_rgb,
        landmarks_px=detection.landmarks_px,
        quality_status=quality_assessment.status,
        forehead_lines=forehead_analysis.lines,
    )

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 1)

    pose_dict = _format_pose(quality_assessment.checks.head_pose)
    checks_dict = _format_checks(
        quality_assessment.checks, quality_assessment.status, detection.face_count
    )
    details_dict = {k: asdict(v) for k, v in details.items()}

    lines_data = [
        {
            "y_center": int(line_item.y_center),
            "x_start": int(line_item.x_start),
            "x_end": int(line_item.x_end),
            "width_px": int(line_item.width_px),
            "prominence": float(line_item.prominence),
            "is_continuous": bool(line_item.is_continuous),
            "planet_name": str(line_item.planet_name),
        }
        for line_item in forehead_analysis.lines
    ]

    all_warnings = quality_assessment.checks.issues + quality_assessment.checks.recommendations

    return ScanPipelineResult(
        scan_id=scan_id,
        status=quality_assessment.status,
        quality_score=quality_assessment.score,
        quality_checks=checks_dict,
        head_pose=pose_dict,
        measurements=measurements,
        measurement_details=details_dict,
        visualization_image=vis_data_url,
        processing_duration_ms=duration_ms,
        warnings=all_warnings,
        error_message=None,
        forehead_lines_count=forehead_analysis.lines_count,
        forehead_lines_data=lines_data,
        forehead_lines_shastra=forehead_analysis.shastra_interpretation,
        landmark_mapping_version=config.landmark_mapping_version,
        model_version=config.model_version,
    )
