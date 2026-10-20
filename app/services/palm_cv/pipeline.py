"""Complete palm scanning pipeline orchestrator."""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.services.palm_cv.config import DEFAULT_CONFIG, PalmScanConfig
from app.services.palm_cv.crease_extractor import extract_crease_metrics
from app.services.palm_cv.detector import get_hand_landmarker
from app.services.palm_cv.measurements import extract_palm_measurements
from app.services.palm_cv.quality import (
    QualityStatus,
    assess_palm_quality,
    decode_and_correct_orientation,
)
from app.services.palm_cv.visualizer import draw_palm_overlay


@dataclass
class PalmScanPipelineResult:
    scan_id: str
    status: QualityStatus
    quality_score: float
    quality_checks: dict[str, Any]
    detected_hand: str | None
    expected_hand: str
    is_hand_matched: bool
    measurements: dict[str, float]
    measurement_details: dict[str, dict[str, Any]]
    visualization_image: str | None
    processing_duration_ms: float
    warnings: list[str]
    error_message: str | None = None
    landmark_mapping_version: str = "canonical_21_v1"
    model_version: str = "mediapipe_tasks_hand_landmarker_1.1.1"


def execute_palm_scan_pipeline(
    raw_image_bytes: bytes,
    gender: str = "male",
    hand: str = "auto",
    config: PalmScanConfig = DEFAULT_CONFIG,
) -> PalmScanPipelineResult:
    """Executes the full computer vision and biometric palm scanning pipeline."""
    start_time = time.perf_counter()
    scan_id = str(uuid.uuid4())

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
            f"Image resolution {w}x{h} is too low. Minimum required is "
            f"{config.min_image_width}x{config.min_image_height} pixels."
        )

    # Determine expected hand based on Shastra gender rules:
    # Male: Left Hand; Female: Right Hand
    if hand and hand.lower() in ["left", "right"]:
        expected_hand = hand.lower()
    else:
        expected_hand = "right" if gender.lower() == "female" else "left"

    # Stage 1: MediaPipe Hand Landmarker detection
    detector = get_hand_landmarker(config)
    detection = detector.detect(img_rgb)

    # Stage 2: Quality & Pose Assessment
    quality_assessment = assess_palm_quality(
        img_rgb=img_rgb,
        landmarks_px=detection.landmarks_px,
        hand_count=detection.hand_count,
        detected_hand=detection.detected_hand,
        expected_hand=expected_hand,
        config=config,
    )

    qc_dict = {
        "is_valid": quality_assessment.is_valid,
        "status": quality_assessment.status.value,
        "hand_count": quality_assessment.hand_count,
        "detected_hand": quality_assessment.detected_hand,
        "expected_hand": quality_assessment.expected_hand,
        "is_hand_matched": quality_assessment.is_hand_matched,
        "hand_coverage_pct": quality_assessment.hand_coverage_pct,
        "blur_score": quality_assessment.blur_score,
        "brightness_mean": quality_assessment.brightness_mean,
        "contrast_std": quality_assessment.contrast_std,
        "fingers_extended": quality_assessment.fingers_extended,
        "issues": quality_assessment.issues,
        "recommendations": quality_assessment.recommendations,
    }

    warnings = list(quality_assessment.issues)

    # If image rejected (e.g. no hand found, blurred beyond recognition), abort early
    if quality_assessment.status == QualityStatus.REJECTED or not detection.landmarks_px:
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 1)
        err_msg = (
            quality_assessment.issues[0]
            if quality_assessment.issues
            else "Palm image quality does not meet scanning requirements."
        )
        return PalmScanPipelineResult(
            scan_id=scan_id,
            status=QualityStatus.REJECTED,
            quality_score=quality_assessment.quality_score,
            quality_checks=qc_dict,
            detected_hand=detection.detected_hand,
            expected_hand=expected_hand,
            is_hand_matched=quality_assessment.is_hand_matched,
            measurements={},
            measurement_details={},
            visualization_image=None,
            processing_duration_ms=duration_ms,
            warnings=warnings,
            error_message=err_msg,
        )

    # Stage 3: Crease & Ridge Extraction using OpenCV
    creases = extract_crease_metrics(
        img_rgb=img_rgb,
        landmarks_px=detection.landmarks_px,
        handedness=detection.detected_hand or "Left",
    )

    # Stage 4: Geometric Biometric Ratios Calculation
    measurements, measurement_details = extract_palm_measurements(
        landmarks_norm=detection.landmarks_norm,
        landmarks_px=detection.landmarks_px,
        creases=creases,
    )

    # Stage 5: Overlay Visualization Rendering
    vis_image = draw_palm_overlay(
        img_rgb=img_rgb,
        landmarks_px=detection.landmarks_px,
        handedness=detection.detected_hand or expected_hand.capitalize(),
        quality_score=quality_assessment.quality_score,
    )

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 1)

    return PalmScanPipelineResult(
        scan_id=scan_id,
        status=quality_assessment.status,
        quality_score=quality_assessment.quality_score,
        quality_checks=qc_dict,
        detected_hand=detection.detected_hand,
        expected_hand=expected_hand,
        is_hand_matched=quality_assessment.is_hand_matched,
        measurements=measurements,
        measurement_details=measurement_details,
        visualization_image=vis_image,
        processing_duration_ms=duration_ms,
        warnings=warnings,
        error_message=None,
    )
