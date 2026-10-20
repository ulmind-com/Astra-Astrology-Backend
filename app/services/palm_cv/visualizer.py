"""Biometric and Sacred Geometry visualization overlay for palm scanning."""

import base64
import cv2
import numpy as np


# Hand connections from 21 MediaPipe landmarks
HAND_CONNECTIONS = [
    # Wrist to fingers
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17),                               # Base loop
]


def draw_palm_overlay(
    img_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]],
    handedness: str | None = "Left",
    quality_score: float = 0.95,
) -> str:
    """Draws sacred biometric mesh, major line tracks, and planetary mount rings on the palm image."""
    h, w, _ = img_rgb.shape
    vis = img_rgb.copy()
    overlay = np.zeros_like(vis)

    pts = [(int(p[0]), int(p[1])) for p in landmarks_px]

    # Colors (BGR for OpenCV drawing on RGB image -> note RGB mapping: [R, G, B])
    GOLD = (245, 158, 11)       # Solar Gold
    AMBER = (251, 191, 36)     # Light Amber
    CYAN = (6, 182, 212)       # Wisdom Cyan
    EMERALD = (16, 185, 129)   # Prana Emerald
    ROSE = (244, 63, 94)       # Heart Rose
    PURPLE = (168, 85, 247)    # Mystic Purple
    WHITE = (255, 255, 255)

    # 1. Draw glowing biometric skeleton connections
    for start_idx, end_idx in HAND_CONNECTIONS:
        if start_idx < len(pts) and end_idx < len(pts):
            p1, p2 = pts[start_idx], pts[end_idx]
            # Outer subtle glow line
            cv2.line(overlay, p1, p2, AMBER, thickness=4, lineType=cv2.LINE_AA)
            # Inner crisp wireframe line
            cv2.line(vis, p1, p2, WHITE, thickness=1, lineType=cv2.LINE_AA)

    # Blend outer glow
    cv2.addWeighted(vis, 1.0, overlay, 0.45, 0, vis)
    overlay.fill(0)

    # 2. Draw 21 Landmark Nodes (Chakra / Energy vertices)
    for i, pt in enumerate(pts):
        is_tip = i in [4, 8, 12, 16, 20]
        color = GOLD if is_tip else CYAN
        # Outer halo
        cv2.circle(vis, pt, 6 if is_tip else 4, color, thickness=1, lineType=cv2.LINE_AA)
        # Inner solid point
        cv2.circle(vis, pt, 3 if is_tip else 2, WHITE, thickness=-1, lineType=cv2.LINE_AA)

    # 3. Draw Major Palm Lines on the palm surface:
    wrist = np.array(pts[0])
    mcp_index = np.array(pts[5])
    mcp_middle = np.array(pts[9])
    mcp_ring = np.array(pts[13])
    mcp_pinky = np.array(pts[17])
    thumb_mcp = np.array(pts[2])

    palm_center = ((wrist + mcp_middle) / 2.0).astype(int)

    # a) Heart Line (Rose) - sweeping curve below pinky towards index/middle
    p_heart_start = (mcp_pinky + np.array([0, int(0.2 * np.linalg.norm(mcp_pinky - wrist))])).astype(int)
    p_heart_mid = ((mcp_ring + mcp_middle) / 2.0 + np.array([0, int(0.25 * np.linalg.norm(mcp_middle - wrist))])).astype(int)
    p_heart_end = (mcp_index + np.array([0, int(0.15 * np.linalg.norm(mcp_index - wrist))])).astype(int)
    heart_pts = np.array([p_heart_start, p_heart_mid, p_heart_end], dtype=np.int32)
    cv2.polylines(overlay, [heart_pts], isClosed=False, color=ROSE, thickness=5, lineType=cv2.LINE_AA)
    cv2.polylines(vis, [heart_pts], isClosed=False, color=(255, 200, 210), thickness=2, lineType=cv2.LINE_AA)

    # b) Head Line (Cyan) - from thumb-index gap across mid palm
    p_head_start = ((thumb_mcp + mcp_index) / 2.0).astype(int)
    p_head_mid = palm_center
    p_head_end = (mcp_pinky + np.array([0, int(0.5 * np.linalg.norm(mcp_pinky - wrist))])).astype(int)
    head_pts = np.array([p_head_start, p_head_mid, p_head_end], dtype=np.int32)
    cv2.polylines(overlay, [head_pts], isClosed=False, color=CYAN, thickness=5, lineType=cv2.LINE_AA)
    cv2.polylines(vis, [head_pts], isClosed=False, color=(200, 245, 255), thickness=2, lineType=cv2.LINE_AA)

    # c) Life Line (Emerald) - arc wrapping around Venus Mount (thumb base)
    p_life_start = p_head_start
    p_life_mid = ((thumb_mcp + wrist) / 2.0 + np.array([int(0.2 * np.linalg.norm(thumb_mcp - wrist)), 0])).astype(int)
    p_life_end = (wrist + np.array([int(0.15 * (thumb_mcp[0] - wrist[0])), -int(0.08 * (mcp_index[1] - wrist[1]))])).astype(int)
    life_pts = np.array([p_life_start, p_life_mid, p_life_end], dtype=np.int32)
    cv2.polylines(overlay, [life_pts], isClosed=False, color=EMERALD, thickness=5, lineType=cv2.LINE_AA)
    cv2.polylines(vis, [life_pts], isClosed=False, color=(200, 255, 220), thickness=2, lineType=cv2.LINE_AA)

    # d) Fate Line (Amber / Gold) - ascending vertically towards Saturn (MCP 9)
    p_fate_start = (wrist + np.array([0, -int(0.1 * np.linalg.norm(mcp_middle - wrist))])).astype(int)
    p_fate_mid = palm_center
    p_fate_end = (mcp_middle + np.array([0, int(0.2 * np.linalg.norm(mcp_middle - wrist))])).astype(int)
    fate_pts = np.array([p_fate_start, p_fate_mid, p_fate_end], dtype=np.int32)
    cv2.polylines(overlay, [fate_pts], isClosed=False, color=GOLD, thickness=4, lineType=cv2.LINE_AA)
    cv2.polylines(vis, [fate_pts], isClosed=False, color=(255, 240, 200), thickness=2, lineType=cv2.LINE_AA)

    # 4. Planetary Mounts Rings
    mounts = [
        ("Jupiter (বৃহস্পতি)", (mcp_index + np.array([0, int(0.12 * np.linalg.norm(mcp_index - wrist))])).astype(int), PURPLE),
        ("Saturn (শনি)", (mcp_middle + np.array([0, int(0.12 * np.linalg.norm(mcp_middle - wrist))])).astype(int), CYAN),
        ("Sun (রবি)", (mcp_ring + np.array([0, int(0.12 * np.linalg.norm(mcp_ring - wrist))])).astype(int), GOLD),
        ("Mercury (বুধ)", (mcp_pinky + np.array([0, int(0.12 * np.linalg.norm(mcp_pinky - wrist))])).astype(int), EMERALD),
        ("Venus (শুক্র)", ((wrist + thumb_mcp) / 2.0).astype(int), ROSE),
    ]

    for label, pt_m, col in mounts:
        cv2.circle(overlay, (int(pt_m[0]), int(pt_m[1])), 14, col, thickness=2, lineType=cv2.LINE_AA)
        cv2.circle(overlay, (int(pt_m[0]), int(pt_m[1])), 4, WHITE, thickness=-1, lineType=cv2.LINE_AA)

    # Blend line overlays
    cv2.addWeighted(vis, 1.0, overlay, 0.55, 0, vis)

    # 5. Overlay Sacred Palmistry Branding & Accuracy Badge
    badge_h = 44
    cv2.rectangle(vis, (12, h - badge_h - 12), (320, h - 12), (15, 23, 42), -1)
    cv2.rectangle(vis, (12, h - badge_h - 12), (320, h - 12), GOLD, 1)

    text_title = "ASTRA VEDIC PALM SCAN"
    text_info = f"HAND: {handedness or 'DETECTED'} | ACCURACY: {int(quality_score * 100)}%"
    cv2.putText(vis, text_title, (22, h - badge_h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, GOLD, 1, cv2.LINE_AA)
    cv2.putText(vis, text_info, (22, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.38, WHITE, 1, cv2.LINE_AA)

    # Convert RGB back to BGR for JPEG encode
    vis_bgr = cv2.cvtColor(vis, cv2.COLOR_RGB2BGR)
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 88]
    success, buffer = cv2.imencode(".jpg", vis_bgr, encode_params)
    if not success:
        return ""

    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"
