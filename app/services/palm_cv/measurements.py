"""Biometric hand proportions and Samudrik Shastra ratio calculations."""

import math
from typing import Any
import numpy as np

from app.services.palm_cv.crease_extractor import PalmCreaseMetrics


def _dist(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def extract_palm_measurements(
    landmarks_norm: list[tuple[float, float, float]],
    landmarks_px: list[tuple[float, float, float]],
    creases: PalmCreaseMetrics,
) -> tuple[dict[str, float], dict[str, dict[str, Any]]]:
    """Calculates all normalized geometric and chiromantic ratios."""
    # Landmarks indexing:
    # 0: Wrist
    # 1: Thumb CMC, 2: Thumb MCP, 3: Thumb IP, 4: Thumb TIP
    # 5: Index MCP, 6: Index PIP, 7: Index DIP, 8: Index TIP
    # 9: Middle MCP, 10: Middle PIP, 11: Middle DIP, 12: Middle TIP
    # 13: Ring MCP, 14: Ring PIP, 15: Ring DIP, 16: Ring TIP
    # 17: Pinky MCP, 18: Pinky PIP, 19: Pinky DIP, 20: Pinky TIP

    pts = landmarks_norm

    # Palm dimensions
    palm_len = max(0.001, _dist(pts[0], pts[9]))  # Wrist to Middle MCP
    palm_wid = max(0.001, _dist(pts[5], pts[17]))  # Index MCP to Pinky MCP

    # 1. Palm Aspect Ratio (Width / Length)
    palm_aspect_ratio = round(palm_wid / palm_len, 3)

    # 2. Finger to Palm Ratio (Middle finger length / Palm length)
    middle_finger_len = _dist(pts[9], pts[12])
    finger_to_palm_ratio = round(middle_finger_len / palm_len, 3)

    # 3. 2D:4D Ratio (Index finger length / Ring finger length)
    index_finger_len = max(0.001, _dist(pts[5], pts[8]))
    ring_finger_len = max(0.001, _dist(pts[13], pts[16]))
    ratio_2d_4d = round(index_finger_len / ring_finger_len, 3)

    # 4. Pinky reach relative to ring finger distal joint (DIP 15)
    # Pinky tip 20 distance from wrist vs Ring DIP 15 distance from wrist
    dist_pinky = _dist(pts[0], pts[20])
    dist_ring_dip = max(0.001, _dist(pts[0], pts[15]))
    pinky_reach = round(dist_pinky / dist_ring_dip, 3)

    # 5. Thumb angle (degrees converted to normalized scale [0-1])
    v_thumb = np.array([pts[4][0] - pts[2][0], pts[4][1] - pts[2][1]])
    v_index = np.array([pts[5][0] - pts[2][0], pts[5][1] - pts[2][1]])
    denom = np.linalg.norm(v_thumb) * np.linalg.norm(v_index)
    thumb_angle_deg = 45.0
    if denom > 0:
        cos_ang = np.clip(np.dot(v_thumb, v_index) / denom, -1.0, 1.0)
        thumb_angle_deg = math.degrees(math.acos(cos_ang))
    thumb_openness = round(min(1.0, max(0.0, thumb_angle_deg / 90.0)), 3)

    measurements: dict[str, float] = {
        "palm_aspect_ratio": palm_aspect_ratio,
        "finger_to_palm_ratio": finger_to_palm_ratio,
        "ratio_2d_4d": ratio_2d_4d,
        "pinky_reach": pinky_reach,
        "thumb_openness": thumb_openness,
        "heart_line_curvature": creases.heart_line_curvature,
        "heart_line_length": creases.heart_line_length,
        "heart_line_depth": creases.heart_line_depth,
        "head_line_slope": creases.head_line_slope,
        "head_line_length": creases.head_line_length,
        "head_line_depth": creases.head_line_depth,
        "life_line_arc": creases.life_line_arc,
        "life_line_length": creases.life_line_length,
        "life_line_depth": creases.life_line_depth,
        "fate_line_prominence": creases.fate_line_prominence,
        "fate_line_length": creases.fate_line_length,
        "fate_line_from_moon": creases.fate_line_from_moon,
        "sun_line_prominence": creases.sun_line_prominence,
        "mount_jupiter_prominence": creases.mount_jupiter_prominence,
        "mount_venus_prominence": creases.mount_venus_prominence,
        "mount_mercury_prominence": creases.mount_mercury_prominence,
        "mount_moon_prominence": creases.mount_moon_prominence,
    }

    details: dict[str, dict[str, Any]] = {
        "palm_aspect_ratio": {
            "name": "তালুর অনুপাত (Palm Aspect Ratio)",
            "value": palm_aspect_ratio,
            "description": "তালুর প্রস্থ ও দৈর্ঘ্যের অনুপাত যা পৃথ্বী, বায়ু, অগ্নি বা জল হস্ত নির্ধারণ করে।",
            "status": "available",
        },
        "finger_to_palm_ratio": {
            "name": "অঙ্গুলির দৈর্ঘ্য অনুপাত (Finger to Palm Ratio)",
            "value": finger_to_palm_ratio,
            "description": "মধ্যমা অঙ্গুলির দৈর্ঘ্য বনাম তালুর দৈর্ঘ্য অনুপাত।",
            "status": "available",
        },
        "ratio_2d_4d": {
            "name": "তর্জনী বনাম অনামিকা অনুপাত (2D:4D Ratio)",
            "value": ratio_2d_4d,
            "description": "বৃহস্পতি ও রবির আঙুলের তুলনামূলক অনুপাত যা নেতৃত্ব ও আত্মবিশ্বাস নির্দেশ করে।",
            "status": "available",
        },
        "pinky_reach": {
            "name": "বুধের আঙুলের বিস্তার (Pinky Reach)",
            "value": pinky_reach,
            "description": "কনিষ্ঠা আঙুলের উচ্চতা যা বাকপটুতা ও অর্থজ্ঞানের দ্যোতক।",
            "status": "available",
        },
        "heart_line_curvature": {
            "name": "হৃদয় রেখার বক্রতা (Heart Line Curvature)",
            "value": creases.heart_line_curvature,
            "description": "হৃদয় রেখার বৃহস্পতি পর্বতাভিমুখী উত্থান যা প্রেম ও বিশ্বস্ততা নির্দেশ করে।",
            "status": "available",
        },
        "head_line_slope": {
            "name": "মস্তিষ্ক রেখার ঢাল (Head Line Slope)",
            "value": creases.head_line_slope,
            "description": "মস্তিষ্ক রেখার চন্দ্র পর্বতাভিমুখী বিস্তার যা সৃষ্টিশীলতা নির্দেশ করে।",
            "status": "available",
        },
        "life_line_arc": {
            "name": "জীবন রেখার বৃত্তচাপ (Life Line Arc)",
            "value": creases.life_line_arc,
            "description": "শুক্র পর্বতকে বেষ্টনকারী বৃত্তচাপ যা জীবনীশক্তি ও স্বাস্থ্য নির্দেশ করে।",
            "status": "available",
        },
        "fate_line_prominence": {
            "name": "ভাগ্য রেখার প্রখরতা (Fate Line Prominence)",
            "value": creases.fate_line_prominence,
            "description": "মণিবন্ধ থেকে শনি পর্বত পর্যন্ত ভাগ্য রেখার স্পষ্টতা।",
            "status": "available",
        },
        "sun_line_prominence": {
            "name": "রবি রেখার উজ্জ্বলতা (Sun Line Prominence)",
            "value": creases.sun_line_prominence,
            "description": "রবি পর্বতের রেখা যা যশ, প্রতিষ্ঠা ও সামাজিক সম্মান নির্দেশ করে।",
            "status": "available",
        },
    }

    return measurements, details
