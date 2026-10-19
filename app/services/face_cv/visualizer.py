"""OpenCV-based facial mesh and biometric measurement visualization module."""

import base64
import cv2
import numpy as np

from app.services.face_cv.landmarks import (
    FACE_OVAL_INDICES,
    RIGHT_EYE_INDICES,
    LEFT_EYE_INDICES,
    RIGHT_EYEBROW_INDICES,
    LEFT_EYEBROW_INDICES,
    LIPS_OUTER_INDICES,
    NOSE_INDICES,
    LandmarkIndex as P,
)
from app.services.face_cv.quality import QualityStatus


def draw_facial_mesh_overlay(
    img_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]],
    quality_status: QualityStatus,
) -> str:
    """Draws an aesthetic, professional biometric face mesh overlay and returns a base64 JPEG string.

    Args:
        img_rgb: Input RGB image (numpy array uint8).
        landmarks_px: List of (x, y, z) pixel coordinates.
        quality_status: ACCEPTED, RETAKE_RECOMMENDED, or REJECTED.

    Returns:
        Base64-encoded JPEG data URL ('data:image/jpeg;base64,...').
    """
    # Work on a copy in BGR format for OpenCV drawing operations
    vis_bgr = cv2.cvtColor(img_rgb.copy(), cv2.COLOR_RGB2BGR)
    h, w, _ = vis_bgr.shape

    # Color definitions (BGR format)
    # Emerald green for ACCEPTED, Amber/Gold for RETAKE_RECOMMENDED, Red for REJECTED
    if quality_status == QualityStatus.ACCEPTED:
        primary_color = (153, 211, 52)     # Emerald (#34d399)
        secondary_color = (200, 240, 160)  # Soft green
        accent_color = (74, 229, 242)      # Gold/Yellow
    elif quality_status == QualityStatus.RETAKE_RECOMMENDED:
        primary_color = (36, 191, 251)     # Amber/Orange (#f59e0b)
        secondary_color = (160, 220, 255)  # Light orange
        accent_color = (74, 229, 242)
    else:
        primary_color = (68, 68, 239)      # Red (#ef4444)
        secondary_color = (180, 180, 255)
        accent_color = (36, 191, 251)

    pts = np.array([(int(round(pt[0])), int(round(pt[1]))) for pt in landmarks_px], dtype=np.int32)

    # 1. Draw facial contours with anti-aliasing
    def draw_contour(indices: list[int], color: tuple[int, int, int], thickness: int = 1, is_closed: bool = True):
        contour_pts = np.array([pts[i] for i in indices if i < len(pts)], dtype=np.int32)
        if len(contour_pts) > 1:
            cv2.polylines(vis_bgr, [contour_pts], isClosed=is_closed, color=color, thickness=thickness, lineType=cv2.LINE_AA)

    # Face contour
    draw_contour(FACE_OVAL_INDICES, secondary_color, thickness=1, is_closed=True)
    # Eyebrows
    draw_contour(RIGHT_EYEBROW_INDICES, primary_color, thickness=2, is_closed=False)
    draw_contour(LEFT_EYEBROW_INDICES, primary_color, thickness=2, is_closed=False)
    # Eyes
    draw_contour(RIGHT_EYE_INDICES, primary_color, thickness=2, is_closed=True)
    draw_contour(LEFT_EYE_INDICES, primary_color, thickness=2, is_closed=True)
    # Nose bridge & base
    draw_contour(NOSE_INDICES, primary_color, thickness=1, is_closed=False)
    # Lips
    draw_contour(LIPS_OUTER_INDICES, primary_color, thickness=2, is_closed=True)

    # 2. Key biometric landmark nodes (small circles)
    key_nodes = [
        P.FOREHEAD_TOP, P.CHIN_BOTTOM, P.CHEEK_RIGHT, P.CHEEK_LEFT,
        P.R_EYE_OUTER, P.R_EYE_INNER, P.L_EYE_INNER, P.L_EYE_OUTER,
        P.NOSE_BRIDGE_TOP, P.NOSE_TIP, P.NOSE_RIGHT_WING, P.NOSE_LEFT_WING,
        P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT, P.LIP_UPPER_TOP, P.LIP_LOWER_BOTTOM,
        P.R_BROW_PEAK, P.L_BROW_PEAK,
    ]

    for node_idx in key_nodes:
        if node_idx < len(pts):
            p = pts[node_idx]
            cv2.circle(vis_bgr, (p[0], p[1]), 3, accent_color, -1, lineType=cv2.LINE_AA)
            cv2.circle(vis_bgr, (p[0], p[1]), 5, primary_color, 1, lineType=cv2.LINE_AA)

    # 3. Eye Level Guideline (dashed line connecting outer eye corners)
    if P.R_EYE_OUTER < len(pts) and P.L_EYE_OUTER < len(pts):
        pt_r = pts[P.R_EYE_OUTER]
        pt_l = pts[P.L_EYE_OUTER]
        cv2.line(vis_bgr, (pt_r[0], pt_r[1]), (pt_l[0], pt_l[1]), secondary_color, 1, lineType=cv2.LINE_AA)

    # 4. Vertical Symmetry Line (Forehead top -> Chin bottom)
    if P.FOREHEAD_TOP < len(pts) and P.CHIN_BOTTOM < len(pts):
        pt_top = pts[P.FOREHEAD_TOP]
        pt_bot = pts[P.CHIN_BOTTOM]
        cv2.line(vis_bgr, (pt_top[0], pt_top[1]), (pt_bot[0], pt_bot[1]), (255, 255, 255), 1, lineType=cv2.LINE_AA)

    # Encode to JPEG
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 88]
    success, buffer = cv2.imencode(".jpg", vis_bgr, encode_param)
    if not success:
        return ""

    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"
