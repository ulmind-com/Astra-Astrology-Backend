"""OpenCV-based 3D facial mesh and biometric measurement visualization module."""

import base64
from typing import Any

import cv2
import numpy as np

from app.services.face_cv.landmarks import (
    LandmarkIndex as P,
)
from app.services.face_cv.mesh_connections import (
    FACEMESH_CONTOURS,
    FACEMESH_TESSELATION,
    LEFT_IRIS_CONNECTIONS,
    RIGHT_IRIS_CONNECTIONS,
)
from app.services.face_cv.quality import QualityStatus


def draw_facial_mesh_overlay(
    img_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]],
    quality_status: QualityStatus,
    forehead_lines: list[Any] | None = None,
) -> str:
    """Draws a high-precision 3D biometric face mesh overlay and returns a base64 JPEG string.

    Features:
        - 2,556-edge 3D canonical surface tesselation with alpha-blended depth shading
        - Distinct anatomical contour highlighting (eyes, brows, nose bridge, lips, oval)
        - 3D iris and pupil tracking nodes (landmarks 468 & 473)
        - 478 3D micro-coordinate nodes with depth-attenuated luminosity
        - Glowing dual-ring anchor nodes at primary Vedic anthropometric landmarks
        - Planetary forehead wrinkle & fold line biometric tracking paths
        - Anatomical symmetry and horizontal eye-plane alignment guides
    """
    vis_bgr = cv2.cvtColor(img_rgb.copy(), cv2.COLOR_RGB2BGR)
    h, w, _ = vis_bgr.shape

    # Color palette tailored for futuristic cybernetic & Vedic biometric aesthetics (BGR format)
    if quality_status == QualityStatus.ACCEPTED:
        mesh_color = (200, 220, 60)       # Light turquoise / cyan mesh (subtle)
        contour_color = (160, 230, 80)    # Vibrant emerald-cyan
        accent_color = (80, 235, 255)     # Glowing gold / electric yellow
        node_glow_color = (255, 215, 0)   # Gold glow
        iris_color = (255, 230, 100)      # Bright cyan for pupils
    elif quality_status == QualityStatus.RETAKE_RECOMMENDED:
        mesh_color = (100, 180, 240)      # Soft amber
        contour_color = (40, 180, 250)    # Amber-orange
        accent_color = (80, 235, 255)
        node_glow_color = (36, 191, 251)
        iris_color = (255, 230, 100)
    else:
        mesh_color = (120, 120, 220)      # Muted red/coral
        contour_color = (70, 70, 240)
        accent_color = (50, 150, 255)
        node_glow_color = (68, 68, 239)
        iris_color = (180, 180, 255)

    n_pts = len(landmarks_px)
    pts = np.array([(int(round(pt[0])), int(round(pt[1]))) for pt in landmarks_px], dtype=np.int32)
    z_vals = [pt[2] for pt in landmarks_px]
    min_z = min(z_vals) if z_vals else 0.0
    max_z = max(z_vals) if z_vals else 1.0
    z_span = max(1e-4, max_z - min_z)

    # 1. Layer 1: Dense 3D Surface Tesselation Mesh (Alpha-blended for rich 3D topology)
    mesh_layer = vis_bgr.copy()
    for start_idx, end_idx in FACEMESH_TESSELATION:
        if start_idx < n_pts and end_idx < n_pts:
            p1 = pts[start_idx]
            p2 = pts[end_idx]
            cv2.line(
                mesh_layer, (p1[0], p1[1]), (p2[0], p2[1]), mesh_color, 1, lineType=cv2.LINE_AA
            )

    # Blend the 3D tesselation wireframe at 36% opacity for subtle, realistic depth
    cv2.addWeighted(mesh_layer, 0.36, vis_bgr, 0.64, 0, vis_bgr)

    # 2. Layer 2: Anatomical Feature Contours (Eyes, Brows, Lips, Nose, Oval)
    for start_idx, end_idx in FACEMESH_CONTOURS:
        if start_idx < n_pts and end_idx < n_pts:
            p1 = pts[start_idx]
            p2 = pts[end_idx]
            cv2.line(
                vis_bgr, (p1[0], p1[1]), (p2[0], p2[1]), contour_color, 1, lineType=cv2.LINE_AA
            )

    # 3. Layer 3: Irises and Pupils (Landmarks 468-477)
    for start_idx, end_idx in RIGHT_IRIS_CONNECTIONS + LEFT_IRIS_CONNECTIONS:
        if start_idx < n_pts and end_idx < n_pts:
            p1 = pts[start_idx]
            p2 = pts[end_idx]
            cv2.line(vis_bgr, (p1[0], p1[1]), (p2[0], p2[1]), iris_color, 1, lineType=cv2.LINE_AA)

    # Pupil centers
    if n_pts > P.R_PUPIL:
        pr = pts[P.R_PUPIL]
        cv2.circle(vis_bgr, (pr[0], pr[1]), 2, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(vis_bgr, (pr[0], pr[1]), 4, iris_color, 1, lineType=cv2.LINE_AA)
    if n_pts > P.L_PUPIL:
        pl = pts[P.L_PUPIL]
        cv2.circle(vis_bgr, (pl[0], pl[1]), 2, (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(vis_bgr, (pl[0], pl[1]), 4, iris_color, 1, lineType=cv2.LINE_AA)

    # 4. Layer 4: Micro-nodes across 3D landmarks with depth attenuation
    for i in range(0, n_pts, 3):  # Subsampled for balanced density without visual clutter
        p = pts[i]
        depth_norm = 1.0 - ((z_vals[i] - min_z) / z_span)
        radius = 2 if depth_norm > 0.65 else 1
        cv2.circle(vis_bgr, (p[0], p[1]), radius, mesh_color, -1, lineType=cv2.LINE_AA)

    # 5. Layer 5: High-Precision Vedic Anchor Nodes (Glowing Dual-Ring Markers)
    vedic_anchor_nodes = [
        # Upper third: Trichion, Glabella, Temples, Brow arches
        P.FOREHEAD_TOP, P.GLABELLA, P.BROW_RIDGE_RIGHT, P.BROW_RIDGE_LEFT,
        P.R_BROW_INNER, P.R_BROW_PEAK, P.R_BROW_OUTER,
        P.L_BROW_INNER, P.L_BROW_PEAK, P.L_BROW_OUTER,
        # Middle third: Eyes, Nose Bridge, Tip, Wings, Cheeks
        P.R_EYE_OUTER, P.R_EYE_INNER, P.L_EYE_INNER, P.L_EYE_OUTER,
        P.NOSE_BRIDGE_TOP, P.NOSE_TIP, P.NOSE_BASE,
        P.NOSE_RIGHT_WING, P.NOSE_LEFT_WING,
        P.CHEEK_RIGHT, P.CHEEK_LEFT,
        # Lower third: Cheilion corners, Lips, Jaw angles, Chin
        P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT,
        P.LIP_UPPER_TOP, P.LIP_LOWER_BOTTOM,
        P.CHEEK_LINE_RIGHT, P.CHEEK_LINE_LEFT,
        P.JAW_RIGHT, P.JAW_LEFT,
        P.CHIN_BOTTOM,
    ]

    for node_idx in vedic_anchor_nodes:
        if node_idx < n_pts:
            p = pts[node_idx]
            # Outer glow halo
            cv2.circle(vis_bgr, (p[0], p[1]), 5, node_glow_color, 1, lineType=cv2.LINE_AA)
            # Solid core
            cv2.circle(vis_bgr, (p[0], p[1]), 2, accent_color, -1, lineType=cv2.LINE_AA)

    # 5.5 Layer 5.5: Planetary Forehead Wrinkles & Crease Lines Biometric Highlight
    if forehead_lines:
        for f_line in forehead_lines:
            x_s = getattr(f_line, "x_start", 0)
            x_e = getattr(f_line, "x_end", 0)
            y_c = getattr(f_line, "y_center", 0)
            c_pts = getattr(f_line, "contour_points", [])
            p_name = getattr(f_line, "planet_name", "")

            # If contour points are present, draw conforming curved crease path
            if c_pts and len(c_pts) >= 2:
                pts_line = np.array(c_pts, dtype=np.int32).reshape((-1, 1, 2))
                # Translucent glow
                cv2.polylines(vis_bgr, [pts_line], False, (40, 180, 250), 3, lineType=cv2.LINE_AA)
                # Crisp core
                cv2.polylines(vis_bgr, [pts_line], False, (80, 235, 255), 1, lineType=cv2.LINE_AA)
            elif x_e > x_s:
                # Geometric horizontal biometric tracking vector
                cv2.line(vis_bgr, (x_s, y_c), (x_e, y_c), (40, 180, 250), 3, lineType=cv2.LINE_AA)
                cv2.line(vis_bgr, (x_s, y_c), (x_e, y_c), (80, 235, 255), 1, lineType=cv2.LINE_AA)

            # Endcap coordinate anchors
            if x_e > x_s and 0 <= x_s < w and 0 <= x_e < w and 0 <= y_c < h:
                cv2.circle(vis_bgr, (x_s, y_c), 3, (40, 180, 250), 1, lineType=cv2.LINE_AA)
                cv2.circle(vis_bgr, (x_s, y_c), 1, (255, 255, 255), -1, lineType=cv2.LINE_AA)
                cv2.circle(vis_bgr, (x_e, y_c), 3, (40, 180, 250), 1, lineType=cv2.LINE_AA)
                cv2.circle(vis_bgr, (x_e, y_c), 1, (255, 255, 255), -1, lineType=cv2.LINE_AA)

                # Planetary indicator badge
                if p_name:
                    short_tag = p_name.split(" ")[0]
                    txt_x = min(w - 55, x_e + 6)
                    cv2.putText(
                        vis_bgr,
                        short_tag,
                        (txt_x, max(12, y_c + 3)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.32,
                        (80, 235, 255),
                        1,
                        cv2.LINE_AA,
                    )

    # 6. Layer 6: Anatomical Alignment Grid (Facial Midline & Eye Plane)
    if n_pts > P.R_EYE_OUTER and n_pts > P.L_EYE_OUTER:
        pt_r = pts[P.R_EYE_OUTER]
        pt_l = pts[P.L_EYE_OUTER]
        cv2.line(
            vis_bgr,
            (pt_r[0], pt_r[1]),
            (pt_l[0], pt_l[1]),
            (255, 255, 255),
            1,
            lineType=cv2.LINE_AA,
        )

    if n_pts > P.FOREHEAD_TOP and n_pts > P.CHIN_BOTTOM:
        pt_top = pts[P.FOREHEAD_TOP]
        pt_bot = pts[P.CHIN_BOTTOM]
        cv2.line(
            vis_bgr,
            (pt_top[0], pt_top[1]),
            (pt_bot[0], pt_bot[1]),
            (255, 255, 255),
            1,
            lineType=cv2.LINE_AA,
        )

    # Encode to high-quality JPEG
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    success, buffer = cv2.imencode(".jpg", vis_bgr, encode_param)
    if not success:
        return ""

    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"
