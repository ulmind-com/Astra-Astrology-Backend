"""Complete facial scanning pipeline orchestrator (Stages A through G)."""

import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any
import numpy as np

from app.services.face_cv.config import FaceScanConfig, DEFAULT_CONFIG
from app.services.face_cv.detector import get_landmarker
from app.services.face_cv.measurements import extract_measurements, MeasurementDetail
from app.services.face_cv.quality import (
    decode_and_correct_orientation,
    assess_quality,
    QualityAssessment,
    QualityStatus,
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

    # If rejected, construct early response with quality breakdown and guidance
    if quality_assessment.status == QualityStatus.REJECTED:
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 1)
        checks_dict = asdict(quality_assessment.checks)
        pose_dict = asdict(quality_assessment.checks.head_pose) if quality_assessment.checks.head_pose else None

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

    # --- Stage E: Facial feature extraction ---
    assert detection.landmarks_norm is not None, "Landmarks must be present for accepted image"
    measurements, details = extract_measurements(detection.landmarks_norm)

    # --- Stage G: Face mesh visualization ---
    assert detection.landmarks_px is not None
    vis_data_url = draw_facial_mesh_overlay(
        img_rgb=img_rgb,
        landmarks_px=detection.landmarks_px,
        quality_status=quality_assessment.status,
    )

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 1)

    checks_dict = asdict(quality_assessment.checks)
    pose_dict = asdict(quality_assessment.checks.head_pose) if quality_assessment.checks.head_pose else None
    details_dict = {k: asdict(v) for k, v in details.items()}

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
        landmark_mapping_version=config.landmark_mapping_version,
        model_version=config.model_version,
    )
