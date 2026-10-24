"""The palm scan, start to finish.

Order matters, and the order is deliberate: nothing is measured until the photo has
earned it. Detection first, because without a hand there is nothing to assess;
quality next, because a photo that fails the gates must be sent back rather than
measured; and only then the geometry and the creases.

Every failure along the way returns a result with `status` set and a message the
user can act on. Nothing here raises past the caller, so a malformed upload cannot
take a worker down.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from loguru import logger

from app.services.palm_cv.config import DEFAULT_CONFIG, PalmScanConfig
from app.services.palm_cv.creases import (
    build_canonical_palm,
    crease_relationships,
    trace_creases,
)
from app.services.palm_cv.detector import get_landmarker
from app.services.palm_cv.measurements import extract, extract_3d_metrics, hand_type
from app.services.palm_cv.quality import QualityStatus, assess, decode_image, hand_pose
from app.services.palm_cv.visualizer import draw_overlay, draw_response_map, to_data_url


@dataclass
class PalmScanResult:
    scan_id: str
    status: str  # "ok" | "rejected" | "error"
    message: str | None = None

    hand_detected: bool = False
    handedness: str | None = None
    handedness_confidence: float = 0.0

    quality: dict[str, Any] = field(default_factory=dict)
    pose: dict[str, float] = field(default_factory=dict)

    measurements: dict[str, float] = field(default_factory=dict)
    measurement_details: dict[str, Any] = field(default_factory=dict)
    hand_type: dict[str, Any] = field(default_factory=dict)

    creases: dict[str, Any] = field(default_factory=dict)
    crease_relationships: dict[str, Any] = field(default_factory=dict)

    overlay_image: str | None = None
    response_image: str | None = None

    #: 3D world scan coordinates, mount elevations, and depth metrics
    landmarks_3d: list[list[float]] = field(default_factory=list)
    world_landmarks_mm: list[list[float]] = field(default_factory=list)
    mount_elevations_3d: dict[str, float] = field(default_factory=dict)
    palm_cup_depth_mm: float = 0.0
    finger_flexibility_3d: dict[str, Any] = field(default_factory=dict)
    finger_inclinations_3d: dict[str, float] = field(default_factory=dict)

    processing_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)

    #: Pinned so a stored reading can be told apart from one produced by a later
    #: version of the tracing, which is the only way to know whether an old reading
    #: is still comparable with a new one.
    pipeline_version: str = "palm_cv_v1"
    model_version: str = "mediapipe_hand_landmarker_v1"

    def as_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "status": self.status,
            "message": self.message,
            "hand_detected": self.hand_detected,
            "handedness": self.handedness,
            "handedness_confidence": round(self.handedness_confidence, 3),
            "quality": self.quality,
            "pose": {k: round(v, 3) for k, v in self.pose.items()},
            "measurements": self.measurements,
            "measurement_details": self.measurement_details,
            "hand_type": self.hand_type,
            "creases": self.creases,
            "crease_relationships": self.crease_relationships,
            "landmarks_3d": self.landmarks_3d,
            "world_landmarks_mm": self.world_landmarks_mm,
            "mount_elevations_3d": self.mount_elevations_3d,
            "palm_cup_depth_mm": round(self.palm_cup_depth_mm, 2),
            "finger_flexibility_3d": self.finger_flexibility_3d,
            "finger_inclinations_3d": self.finger_inclinations_3d,
            "overlay_image": self.overlay_image,
            "response_image": self.response_image,
            "processing_ms": round(self.processing_ms, 1),
            "warnings": self.warnings,
            "pipeline_version": self.pipeline_version,
            "model_version": self.model_version,
        }


def execute_scan(
    raw_image: bytes,
    config: PalmScanConfig = DEFAULT_CONFIG,
    include_images: bool = True,
) -> PalmScanResult:
    """Run one palm scan. Never raises; failures come back as a status."""
    started = time.perf_counter()
    result = PalmScanResult(scan_id=str(uuid.uuid4()), status="error")

    try:
        # --- decode -------------------------------------------------------
        try:
            image = decode_image(raw_image, config)
        except ValueError as exc:
            result.status = "rejected"
            result.message = str(exc)
            return result

        # --- find the hand ------------------------------------------------
        landmarker = get_landmarker(config)
        if not landmarker.is_ready:
            result.status = "error"
            result.message = (
                "The hand detection model is not available on this server. "
                "Nothing approximate has been returned."
            )
            logger.error(f"palm scan unavailable: {landmarker.load_error}")
            return result

        detection = landmarker.detect(image)
        if not detection.landmarks_px:
            result.status = "rejected"
            result.message = (
                "No hand was found in that photo. Hold your open palm towards the "
                "camera, fingers pointing up, and fill most of the frame."
            )
            return result

        result.hand_detected = True
        result.handedness = detection.handedness
        result.handedness_confidence = detection.handedness_confidence
        result.pose = hand_pose(detection.landmarks_px)

        # --- quality gates -------------------------------------------------
        quality = assess(image, detection.landmarks_px, config)
        result.quality = quality.as_dict()
        if quality.status is QualityStatus.REJECTED:
            result.status = "rejected"
            result.message = " ".join(quality.failures)
            return result

        # --- geometry ------------------------------------------------------
        measured = extract(detection.landmarks_px)
        result.measurements = {k: round(v, 4) for k, v in measured.values.items()}
        result.measurement_details = {k: m.as_dict() for k, m in measured.details.items()}
        result.hand_type = hand_type(measured.values)

        # --- 3D scan & depth topography ------------------------------------
        metrics_3d = extract_3d_metrics(detection.landmarks_px, detection.landmarks_world)
        result.palm_cup_depth_mm = metrics_3d["hollow_depth_mm"]
        result.mount_elevations_3d = metrics_3d["mount_elevations"]
        result.finger_flexibility_3d = {
            "dorsiflexion_deg": metrics_3d["dorsiflexion_deg"],
            "is_spontaneous": bool(metrics_3d["is_spontaneous_flexible"]),
            "is_stiff": bool(metrics_3d["is_stiff_fingers"]),
        }
        result.finger_inclinations_3d = {
            "saturn_to_sun_deg": metrics_3d["saturn_sun_tilt_deg"],
            "jupiter_to_thumb_deg": metrics_3d["jupiter_thumb_angle_deg"],
        }
        if detection.landmarks_norm:
            result.landmarks_3d = [[round(p[0], 4), round(p[1], 4), round(p[2], 4)] for p in detection.landmarks_norm]
        if detection.landmarks_world:
            result.world_landmarks_mm = [
                [round(p[0] * 1000.0, 2), round(p[1] * 1000.0, 2), round(p[2] * 1000.0, 2)]
                for p in detection.landmarks_world
            ]

        # Feed 3D metrics directly into measurements for rule evaluation
        result.measurements["hollow_depth_mm"] = metrics_3d["hollow_depth_mm"]
        result.measurements["dorsiflexion_deg"] = metrics_3d["dorsiflexion_deg"]
        result.measurements["is_spontaneous_flexible"] = metrics_3d["is_spontaneous_flexible"]
        result.measurements["is_stiff_fingers"] = metrics_3d["is_stiff_fingers"]
        result.measurements["saturn_sun_tilt_deg"] = metrics_3d["saturn_sun_tilt_deg"]
        result.measurements["jupiter_thumb_angle_deg"] = metrics_3d["jupiter_thumb_angle_deg"]
        result.measurements["thumb_gap_wide"] = metrics_3d["thumb_gap_wide"]
        result.measurements["saturn_leaning_sun"] = metrics_3d["saturn_leaning_sun"]
        for m_name, m_val in metrics_3d["mount_elevations"].items():
            result.measurements[m_name] = m_val

        # --- creases -------------------------------------------------------
        palm = build_canonical_palm(image, detection.landmarks_px, config)
        creases = trace_creases(palm, config)
        result.creases = {name: crease.as_dict() for name, crease in creases.items()}
        result.crease_relationships = crease_relationships(creases, palm.size)

        missing = [name for name, crease in creases.items() if not crease.found]
        if missing:
            result.warnings.append(
                "These creases could not be read clearly from this photo: "
                + ", ".join(missing)
                + ". Rules that depend on them have been left out rather than guessed."
            )

        if include_images:
            try:
                result.overlay_image = to_data_url(draw_overlay(palm, creases))
                result.response_image = to_data_url(draw_response_map(palm), quality=70)
            except Exception as exc:
                # A reading without its picture is still a reading.
                logger.warning(f"palm overlay failed: {exc}")
                result.warnings.append("The overlay image could not be produced.")

        result.status = "ok"
        return result

    except Exception as exc:
        # Anything unforeseen becomes a logged error and a clean message, never a
        # traceback escaping into the request handler.
        logger.exception("palm scan failed")
        result.status = "error"
        result.message = "The palm scan could not be completed. Please try again."
        result.warnings.append(type(exc).__name__)
        return result

    finally:
        result.processing_ms = (time.perf_counter() - started) * 1000.0
