"""3D Volumetric Depth Mesh Analyzer.

Calculates genuine 3D facial depth, inclination, and projection ratios using
MediaPipe Z-axis depth coordinates, overcoming 2D perspective distortions.
"""

from __future__ import annotations

import math
from typing import Any

from app.services.face_cv.landmarks import LandmarkIndex as P


def calculate_3d_volumetric_measurements(
    landmarks_3d: list[list[float]],  # [[x, y, z], ...]
) -> dict[str, float]:
    """Calculates 3D depth metrics and curvature from normalized 3D landmarks."""
    if not landmarks_3d or len(landmarks_3d) < 468:
        return {}

    def _pt(idx: int) -> list[float]:
        return landmarks_3d[idx]

    # Z-axis in MediaPipe: negative is closer to camera (protruding forward),
    # positive is further away (receding backward).
    glabella = _pt(P.GLABELLA)
    forehead_top = _pt(P.FOREHEAD_TOP)
    nose_tip = _pt(P.NOSE_TIP)
    subnasale = _pt(P.NOSE_BASE)
    mid_eyes = _pt(P.NOSE_BRIDGE_TOP)
    chin = _pt(P.CHIN_BOTTOM)
    lower_lip = _pt(P.LIP_LOWER_BOTTOM)
    cheek_r = _pt(P.CHEEK_RIGHT)
    cheek_l = _pt(P.CHEEK_LEFT)
    jaw_r = _pt(P.JAW_RIGHT)
    jaw_l = _pt(P.JAW_LEFT)

    # 1. Forehead 3D Inclination (Slope of forehead relative to eye plane)
    # Forward-sloping (prominent intellect) vs receding (intuitive/practical)
    dy_forehead = abs(forehead_top[1] - glabella[1]) + 1e-6
    dz_forehead = forehead_top[2] - glabella[2]
    forehead_inclination = round(dz_forehead / dy_forehead * 10.0, 3)

    # 2. 3D Nasal Tip Projection (Elevation of nose tip forward from nasal base)
    nose_length = math.dist(subnasale[:2], glabella[:2]) + 1e-6
    # Relative forward protrusion of nose tip compared to subnasale and mid-eyes
    dz_nose = (subnasale[2] + mid_eyes[2]) / 2.0 - nose_tip[2]
    nose_projection_3d = round(max(0.0, dz_nose / nose_length * 5.0), 3)

    # 3. 3D Cheekbone Prominence (Forward projection of zygomatic arches)
    cheek_mid_z = (cheek_r[2] + cheek_l[2]) / 2.0
    jaw_mid_z = (jaw_r[2] + jaw_l[2]) / 2.0
    face_width = math.dist(jaw_r[:2], jaw_l[:2]) + 1e-6
    dz_cheeks = jaw_mid_z - cheek_mid_z
    cheek_prominence_3d = round(max(0.0, dz_cheeks / face_width * 5.0), 3)

    # 4. 3D Chin Projection (Mental protuberance relative to lower lip)
    chin_length = math.dist(chin[:2], lower_lip[:2]) + 1e-6
    dz_chin = lower_lip[2] - chin[2]
    chin_projection_3d = round(dz_chin / chin_length * 5.0, 3)

    # 5. 3D Facial Curvature / Volumetric Convexity
    # Measures the curvature from temples across cheekbones to nose
    lateral_z = (jaw_r[2] + jaw_l[2] + cheek_r[2] + cheek_l[2]) / 4.0
    medial_z = (nose_tip[2] + glabella[2] + subnasale[2]) / 3.0
    volumetric_convexity = round(max(0.0, (lateral_z - medial_z) / face_width * 3.0), 3)

    return {
        "forehead_inclination_3d": float(forehead_inclination),
        "nose_projection_3d": float(nose_projection_3d),
        "cheek_prominence_3d": float(cheek_prominence_3d),
        "chin_projection_3d": float(chin_projection_3d),
        "volumetric_convexity_3d": float(volumetric_convexity),
    }
