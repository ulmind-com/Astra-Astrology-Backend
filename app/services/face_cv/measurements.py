"""Facial feature measurement module.

Calculates the 23 classical biometric and geometric proportions used in
Vedic Samudrik Shastra physiognomy analysis.

Every formula is documented with its anatomical interpretation, landmark pairs,
and normalization method. All outputs are strictly finite, non-negative, and
bounded in [0.0, 10.0].
"""

import math
from dataclasses import dataclass
from typing import Any
import numpy as np

from app.services.face_cv.landmarks import LandmarkIndex as P


@dataclass
class MeasurementDetail:
    name: str
    value: float
    description: str
    formula: str
    landmarks_used: list[int]
    status: str = "available"


def _dist2d(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
    """Euclidean distance in 2D projection."""
    return float(math.hypot(p1[0] - p2[0], p1[1] - p2[1]))


def _dist3d(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
    """Euclidean distance in 3D landmark coordinates."""
    return float(math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2))


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Guards against division by zero or NaN results."""
    if denominator < 1e-6 or math.isnan(denominator) or math.isnan(numerator):
        return default
    val = numerator / denominator
    if math.isinf(val) or math.isnan(val):
        return default
    return val


def extract_measurements(
    landmarks: list[tuple[float, float, float]],
) -> tuple[dict[str, float], dict[str, MeasurementDetail]]:
    """Extracts all 23 geometric facial proportions from 478 landmarks.

    Args:
        landmarks: List of (x, y, z) coordinates (either normalized or pixel).

    Returns:
        (measurements_dict, details_dict)
    """
    if len(landmarks) < 468:
        raise ValueError(f"Insufficient landmarks: expected at least 468, got {len(landmarks)}")

    # 1. Base Framework Dimensions in 3D anatomical space
    face_w = _dist3d(landmarks[P.CHEEK_RIGHT], landmarks[P.CHEEK_LEFT])
    face_h = _dist3d(landmarks[P.FOREHEAD_TOP], landmarks[P.CHIN_BOTTOM])
    jaw_w = _dist3d(landmarks[P.JAW_RIGHT], landmarks[P.JAW_LEFT])
    brow_w = _dist3d(landmarks[P.BROW_RIDGE_RIGHT], landmarks[P.BROW_RIDGE_LEFT])

    # 2. Eye Dimensions (averaged across both eyes for symmetry independence)
    r_eye_w = _dist3d(landmarks[P.R_EYE_OUTER], landmarks[P.R_EYE_INNER])
    l_eye_w = _dist3d(landmarks[P.L_EYE_INNER], landmarks[P.L_EYE_OUTER])
    r_eye_h = _dist3d(landmarks[P.R_EYE_TOP], landmarks[P.R_EYE_BOTTOM])
    l_eye_h = _dist3d(landmarks[P.L_EYE_TOP], landmarks[P.L_EYE_BOTTOM])

    eye_w = (r_eye_w + l_eye_w) / 2.0
    eye_h = (r_eye_h + l_eye_h) / 2.0

    # 3. Eyebrow Dimensions in 3D
    r_brow_thick = _dist3d(landmarks[P.R_BROW_PEAK], landmarks[P.R_BROW_PEAK_LOWER])
    l_brow_thick = _dist3d(landmarks[P.L_BROW_PEAK], landmarks[P.L_BROW_PEAK_LOWER])
    brow_thick = (r_brow_thick + l_brow_thick) / 2.0

    r_brow_len = _dist3d(landmarks[P.R_BROW_INNER], landmarks[P.R_BROW_OUTER])
    l_brow_len = _dist3d(landmarks[P.L_BROW_INNER], landmarks[P.L_BROW_OUTER])
    brow_len = (r_brow_len + l_brow_len) / 2.0

    # Arch rise: distance of peak from chord connecting inner & outer ends in 3D
    def _arch_rise(inner_idx: int, peak_idx: int, outer_idx: int) -> float:
        inner = landmarks[inner_idx]
        peak = landmarks[peak_idx]
        outer = landmarks[outer_idx]
        chord_mid = ((inner[0] + outer[0]) / 2.0, (inner[1] + outer[1]) / 2.0, (inner[2] + outer[2]) / 2.0)
        return _dist3d(peak, chord_mid)

    brow_arch = (_arch_rise(P.R_BROW_INNER, P.R_BROW_PEAK, P.R_BROW_OUTER) +
                 _arch_rise(P.L_BROW_INNER, P.L_BROW_PEAK, P.L_BROW_OUTER)) / 2.0

    # 4. Nose Dimensions in 3D
    nose_w = _dist3d(landmarks[P.NOSE_RIGHT_WING], landmarks[P.NOSE_LEFT_WING])
    nose_len = _dist3d(landmarks[P.NOSE_BRIDGE_TOP], landmarks[P.NOSE_BASE])
    nostril_w = _dist3d(landmarks[P.NOSTRIL_RIGHT], landmarks[P.NOSTRIL_LEFT])
    face_mid_x = (landmarks[P.CHEEK_RIGHT][0] + landmarks[P.CHEEK_LEFT][0]) / 2.0

    # 5. Mouth & Lip Dimensions in 3D
    mouth_w = _dist3d(landmarks[P.MOUTH_CORNER_RIGHT], landmarks[P.MOUTH_CORNER_LEFT])
    lip_h = _dist3d(landmarks[P.LIP_UPPER_TOP], landmarks[P.LIP_LOWER_BOTTOM])
    corner_y = (landmarks[P.MOUTH_CORNER_RIGHT][1] + landmarks[P.MOUTH_CORNER_LEFT][1]) / 2.0

    # 6. Lower Face & Cheeks in 3D
    cheek_line_w = _dist3d(landmarks[P.CHEEK_LINE_RIGHT], landmarks[P.CHEEK_LINE_LEFT])
    forehead_h_val = _dist3d(landmarks[P.GLABELLA], landmarks[P.FOREHEAD_TOP])

    # 7. Compute All 23 Standard Vedic Proportions
    raw_measurements: dict[str, tuple[float, str, str, list[int]]] = {
        "wh_ratio": (
            _safe_div(face_w, face_h),
            "Face width-to-height ratio (cheekbone to cheekbone / hairline to chin)",
            "face_w / face_h",
            [P.CHEEK_RIGHT, P.CHEEK_LEFT, P.FOREHEAD_TOP, P.CHIN_BOTTOM],
        ),
        "jaw_cheek": (
            _safe_div(jaw_w, face_w),
            "Jaw width relative to cheekbone width",
            "jaw_w / face_w",
            [P.JAW_RIGHT, P.JAW_LEFT, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "brow_cheek": (
            _safe_div(brow_w, face_w),
            "Upper forehead / brow ridge width relative to cheek width",
            "brow_w / face_w",
            [P.BROW_RIDGE_RIGHT, P.BROW_RIDGE_LEFT, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "forehead_h": (
            _safe_div(forehead_h_val, face_h),
            "Vertical forehead height relative to total face height",
            "forehead_h / face_h",
            [P.GLABELLA, P.FOREHEAD_TOP, P.CHIN_BOTTOM],
        ),
        "eye_open": (
            _safe_div(eye_h, eye_w),
            "Eye openness (palpebral aperture height relative to fissure width)",
            "eye_h / eye_w",
            [P.R_EYE_TOP, P.R_EYE_BOTTOM, P.R_EYE_OUTER, P.R_EYE_INNER],
        ),
        "eye_size": (
            _safe_div(eye_w, face_w),
            "Eye width relative to total face width",
            "eye_w / face_w",
            [P.R_EYE_OUTER, P.R_EYE_INNER, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "eye_gap": (
            _safe_div(_dist2d(landmarks[P.R_EYE_INNER], landmarks[P.L_EYE_INNER]), eye_w),
            "Inter-canthal distance (gap between eyes relative to single eye width)",
            "inter_eye_gap / eye_w",
            [P.R_EYE_INNER, P.L_EYE_INNER],
        ),
        "eye_tilt": (
            max(0.0, _safe_div(
                ((landmarks[P.R_EYE_INNER][1] - landmarks[P.R_EYE_OUTER][1]) +
                 (landmarks[P.L_EYE_INNER][1] - landmarks[P.L_EYE_OUTER][1])) / 2.0,
                eye_w,
            )),
            "Eye axis canthal tilt (outer canthus elevation above inner canthus / eye width)",
            "canthal_tilt / eye_w",
            [P.R_EYE_INNER, P.R_EYE_OUTER, P.L_EYE_INNER, P.L_EYE_OUTER],
        ),
        "eye_asym": (
            _safe_div(abs(r_eye_h - l_eye_h), max(1e-6, (r_eye_h + l_eye_h) / 2.0)),
            "Left/right eye height asymmetry relative to mean eye height",
            "|r_eye_h - l_eye_h| / mean_eye_h",
            [P.R_EYE_TOP, P.R_EYE_BOTTOM, P.L_EYE_TOP, P.L_EYE_BOTTOM],
        ),
        "brow_thick": (
            _safe_div(brow_thick, eye_w),
            "Eyebrow thickness relative to eye width",
            "brow_thickness / eye_w",
            [P.R_BROW_PEAK, P.R_BROW_PEAK_LOWER, P.L_BROW_PEAK, P.L_BROW_PEAK_LOWER],
        ),
        "brow_arch": (
            _safe_div(brow_arch, brow_len),
            "Eyebrow arch curvature (vertical rise / brow length)",
            "brow_arch_rise / brow_length",
            [P.R_BROW_INNER, P.R_BROW_PEAK, P.R_BROW_OUTER],
        ),
        "brow_gap": (
            _safe_div(_dist2d(landmarks[P.R_BROW_INNER], landmarks[P.L_BROW_INNER]), eye_w),
            "Gap between medial eyebrow heads relative to eye width",
            "inter_brow_gap / eye_w",
            [P.R_BROW_INNER, P.L_BROW_INNER],
        ),
        "brow_len": (
            _safe_div(brow_len, eye_w),
            "Eyebrow length relative to eye width",
            "brow_length / eye_w",
            [P.R_BROW_INNER, P.R_BROW_OUTER],
        ),
        "nose_w": (
            _safe_div(nose_w, face_w),
            "Alar nose width relative to face width",
            "nose_w / face_w",
            [P.NOSE_RIGHT_WING, P.NOSE_LEFT_WING, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "nose_len": (
            _safe_div(nose_len, face_h),
            "Nose length (nasion to subnasale) relative to face height",
            "nose_len / face_h",
            [P.NOSE_BRIDGE_TOP, P.NOSE_BASE, P.FOREHEAD_TOP, P.CHIN_BOTTOM],
        ),
        "nostril": (
            _safe_div(nostril_w, nose_w),
            "Nostril width relative to alar nose width",
            "nostril_w / nose_w",
            [P.NOSTRIL_RIGHT, P.NOSTRIL_LEFT, P.NOSE_RIGHT_WING, P.NOSE_LEFT_WING],
        ),
        "nose_dev": (
            _safe_div(abs(landmarks[P.NOSE_TIP][0] - face_mid_x), face_w),
            "Nose tip lateral deviation from face vertical midline relative to face width",
            "|nose_tip.x - mid.x| / face_w",
            [P.NOSE_TIP, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "lip_thick": (
            _safe_div(lip_h, mouthW := max(1e-6, mouth_w)),
            "Total lip thickness relative to mouth width",
            "lip_h / mouth_w",
            [P.LIP_UPPER_TOP, P.LIP_LOWER_BOTTOM, P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT],
        ),
        "mouth_w": (
            _safe_div(mouth_w, face_w),
            "Mouth width (cheilion to cheilion) relative to face width",
            "mouth_w / face_w",
            [P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "lip_corner": (
            max(0.0, _safe_div(landmarks[P.LIP_LOWER_BOTTOM][1] - corner_y, mouth_w)),
            "Mouth corner elevation from lower vermilion border / mouth width (upturned vs downturned)",
            "(lip_bottom.y - corner.y) / mouth_w",
            [P.LIP_LOWER_BOTTOM, P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT],
        ),
        "lip_asym": (
            _safe_div(
                abs(landmarks[P.MOUTH_CORNER_RIGHT][1] - landmarks[P.MOUTH_CORNER_LEFT][1]),
                max(1e-6, lip_h),
            ),
            "Oral commissure height difference relative to lip thickness",
            "|corner_r.y - corner_l.y| / lip_h",
            [P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT, P.LIP_UPPER_TOP, P.LIP_LOWER_BOTTOM],
        ),
        "chin_h": (
            _safe_div(abs(landmarks[P.CHIN_BOTTOM][1] - landmarks[P.LIP_LOWER_BOTTOM][1]), face_h),
            "Vertical chin height (sublabiale to gnathion) relative to face height",
            "chin_h / face_h",
            [P.CHIN_BOTTOM, P.LIP_LOWER_BOTTOM, P.FOREHEAD_TOP],
        ),
        "cheek_full": (
            _safe_div(cheek_line_w, face_w),
            "Lower cheek width at stomion level relative to zygomatic face width",
            "cheek_line_w / face_w",
            [P.CHEEK_LINE_RIGHT, P.CHEEK_LINE_LEFT, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
    }

    measurements_dict: dict[str, float] = {}
    details_dict: dict[str, MeasurementDetail] = {}

    for name, (val, desc, formula, lm_indices) in raw_measurements.items():
        # Clamp strictly between 0.0 and 10.0 and round to 4 decimals
        clamped_val = round(max(0.0, min(10.0, float(val))), 4)
        measurements_dict[name] = clamped_val
        details_dict[name] = MeasurementDetail(
            name=name,
            value=clamped_val,
            description=desc,
            formula=formula,
            landmarks_used=lm_indices,
            status="available",
        )

    return measurements_dict, details_dict
