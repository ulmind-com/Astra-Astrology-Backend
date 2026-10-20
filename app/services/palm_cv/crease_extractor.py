"""OpenCV Palm Crease and Ridge extraction for major Vedic palm lines."""

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class PalmCreaseMetrics:
    heart_line_curvature: float
    heart_line_length: float
    heart_line_depth: float
    head_line_slope: float
    head_line_length: float
    head_line_depth: float
    life_line_arc: float
    life_line_length: float
    life_line_depth: float
    fate_line_prominence: float
    fate_line_length: float
    fate_line_from_moon: float
    sun_line_prominence: float
    mount_jupiter_prominence: float
    mount_venus_prominence: float
    mount_mercury_prominence: float
    mount_moon_prominence: float
    crease_mask: np.ndarray | None


def extract_crease_metrics(
    img_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]],
    handedness: str = "Left",
) -> PalmCreaseMetrics:
    """Extracts palm line creases and mount elevations using computer vision on the palm ROI."""
    h, w, _ = img_rgb.shape

    # Construct palm polygon using key boundary points:
    # 0 (Wrist), 1 (Thumb CMC), 2 (Thumb MCP), 5 (Index MCP), 9 (Middle MCP),
    # 13 (Ring MCP), 17 (Pinky MCP), plus mid-palm edge
    palm_pts_idx = [0, 1, 2, 5, 9, 13, 17]
    poly_pts = np.array(
        [[int(landmarks_px[i][0]), int(landmarks_px[i][1])] for i in palm_pts_idx],
        dtype=np.int32,
    )

    # Create palm mask
    palm_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillConvexPoly(palm_mask, poly_pts, 255)

    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    # Contrast enhancement with CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Edge and ridge enhancement using bilateral filter and adaptive threshold
    blurred = cv2.bilateralFilter(enhanced, 7, 75, 75)
    edges = cv2.Canny(blurred, 30, 90)
    palm_edges = cv2.bitwise_and(edges, edges, mask=palm_mask)

    # Calculate palm dimensions for normalization
    wrist = np.array(landmarks_px[0][:2])
    mcp_index = np.array(landmarks_px[5][:2])
    mcp_middle = np.array(landmarks_px[9][:2])
    mcp_pinky = np.array(landmarks_px[17][:2])

    palm_length = float(np.linalg.norm(mcp_middle - wrist))
    palm_width = float(np.linalg.norm(mcp_pinky - mcp_index))
    if palm_length < 1.0:
        palm_length = 1.0
    if palm_width < 1.0:
        palm_width = 1.0

    # Regional analysis for Major Palm Lines:
    # 1. Heart Line zone: upper palm below knuckles (MCP 17 to MCP 5)
    # Heart line trajectory runs from below pinky/ring across towards index/middle
    y_upper_min = int(min(landmarks_px[5][1], landmarks_px[17][1]))
    y_upper_max = int(y_upper_min + 0.35 * palm_length)
    x_min = int(min(landmarks_px[5][0], landmarks_px[17][0]))
    x_max = int(max(landmarks_px[5][0], landmarks_px[17][0]))

    heart_roi = palm_edges[
        max(0, y_upper_min) : min(h, y_upper_max), max(0, x_min) : min(w, x_max)
    ]
    heart_line_pixels = int(np.count_nonzero(heart_roi))
    heart_roi_area = max(1, heart_roi.shape[0] * heart_roi.shape[1])
    heart_density = float(heart_line_pixels / heart_roi_area)

    # Heart line metrics
    heart_line_depth = min(1.0, float(heart_density * 18.0))
    heart_line_length = min(1.0, float((x_max - x_min) / palm_width))
    # Curvature derived from vertical displacement across horizontal trajectory
    heart_line_curvature = min(
        1.0,
        float(abs(landmarks_px[5][1] - landmarks_px[17][1]) / max(1.0, palm_length * 0.4)),
    )

    # 2. Head Line zone: middle palm (cutting across from thumb-index gap towards percussion)
    y_mid_min = int(y_upper_min + 0.25 * palm_length)
    y_mid_max = int(y_upper_min + 0.65 * palm_length)
    head_roi = palm_edges[
        max(0, y_mid_min) : min(h, y_mid_max), max(0, x_min) : min(w, x_max)
    ]
    head_line_pixels = int(np.count_nonzero(head_roi))
    head_roi_area = max(1, head_roi.shape[0] * head_roi.shape[1])
    head_density = float(head_line_pixels / head_roi_area)

    head_line_depth = min(1.0, float(head_density * 20.0))
    head_line_length = min(1.0, float((x_max - x_min) / (palm_width * 0.95)))
    head_line_slope = min(
        1.0,
        float(abs(y_mid_max - y_mid_min) / max(1.0, palm_length * 0.5)),
    )

    # 3. Life Line zone: curving around the thumb base (Venus mount)
    thumb_mcp = np.array(landmarks_px[2][:2])
    venus_center = (wrist + thumb_mcp + mcp_index) / 3.0
    r_venus = int(np.linalg.norm(thumb_mcp - wrist) * 0.65)
    life_roi_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(
        life_roi_mask,
        (int(venus_center[0]), int(venus_center[1])),
        max(10, r_venus),
        255,
        thickness=-1,
    )
    life_roi_edges = cv2.bitwise_and(palm_edges, palm_edges, mask=life_roi_mask)
    life_line_pixels = int(np.count_nonzero(life_roi_edges))
    life_roi_area = max(1, int(np.count_nonzero(life_roi_mask)))
    life_density = float(life_line_pixels / life_roi_area)

    life_line_depth = min(1.0, float(life_density * 16.0))
    life_line_arc = min(1.0, float(r_venus / (palm_width * 0.5)))
    life_line_length = min(1.0, float(np.linalg.norm(mcp_index - wrist) / palm_length))

    # 4. Fate Line (Saturn line) zone: vertical band from wrist to middle finger MCP 9
    x_fate_center = int((wrist[0] + mcp_middle[0]) / 2.0)
    fate_band_w = int(palm_width * 0.25)
    fate_roi = palm_edges[
        int(min(wrist[1], mcp_middle[1])) : int(max(wrist[1], mcp_middle[1])),
        max(0, x_fate_center - fate_band_w) : min(w, x_fate_center + fate_band_w),
    ]
    fate_line_pixels = int(np.count_nonzero(fate_roi)) if fate_roi.size > 0 else 0
    fate_roi_area = max(1, fate_roi.size) if fate_roi.size > 0 else 1
    fate_density = float(fate_line_pixels / fate_roi_area)

    fate_line_prominence = min(1.0, float(fate_density * 22.0))
    fate_line_length = min(
        1.0, float(abs(wrist[1] - mcp_middle[1]) / max(1.0, palm_length))
    )
    fate_line_from_moon = min(
        1.0, float(abs(landmarks_px[17][0] - x_fate_center) / max(1.0, palm_width * 0.5))
    )

    # 5. Sun Line (Apollo line) zone: vertical band below ring finger MCP 13
    sun_x_center = int(landmarks_px[13][0])
    sun_band_w = int(palm_width * 0.18)
    sun_roi = palm_edges[
        int(landmarks_px[13][1]) : int(landmarks_px[13][1] + 0.45 * palm_length),
        max(0, sun_x_center - sun_band_w) : min(w, sun_x_center + sun_band_w),
    ]
    sun_line_pixels = int(np.count_nonzero(sun_roi)) if sun_roi.size > 0 else 0
    sun_roi_area = max(1, sun_roi.size) if sun_roi.size > 0 else 1
    sun_density = float(sun_line_pixels / sun_roi_area)
    sun_line_prominence = min(1.0, float(sun_density * 24.0))

    # 6. Planetary Mounts analysis based on regional skin luminosity & smoothness
    # Jupiter: below index finger (MCP 5)
    # Venus: base of thumb
    # Mercury: below pinky (MCP 17)
    # Moon: lower outer palm
    mount_jupiter_prominence = min(
        1.0,
        float(
            np.mean(
                enhanced[
                    max(0, int(landmarks_px[5][1])) : min(
                        h, int(landmarks_px[5][1] + 0.2 * palm_length)
                    ),
                    max(0, int(landmarks_px[5][0] - 0.1 * palm_width)) : min(
                        w, int(landmarks_px[5][0] + 0.1 * palm_width)
                    ),
                ]
            )
            / 255.0
            * 1.25
        ),
    )

    mount_venus_prominence = min(
        1.0,
        float(
            np.mean(
                enhanced[
                    max(0, int(venus_center[1] - 0.2 * palm_length)) : min(
                        h, int(venus_center[1] + 0.2 * palm_length)
                    ),
                    max(0, int(venus_center[0] - 0.2 * palm_width)) : min(
                        w, int(venus_center[0] + 0.2 * palm_width)
                    ),
                ]
            )
            / 255.0
            * 1.2
        ),
    )

    mount_mercury_prominence = min(
        1.0,
        float(
            np.mean(
                enhanced[
                    max(0, int(landmarks_px[17][1])) : min(
                        h, int(landmarks_px[17][1] + 0.2 * palm_length)
                    ),
                    max(0, int(landmarks_px[17][0] - 0.1 * palm_width)) : min(
                        w, int(landmarks_px[17][0] + 0.1 * palm_width)
                    ),
                ]
            )
            / 255.0
            * 1.2
        ),
    )

    mount_moon_prominence = min(
        1.0,
        float(
            np.mean(
                enhanced[
                    max(0, int(wrist[1] - 0.45 * palm_length)) : min(
                        h, int(wrist[1] - 0.1 * palm_length)
                    ),
                    max(0, int(landmarks_px[17][0] - 0.15 * palm_width)) : min(
                        w, int(landmarks_px[17][0] + 0.15 * palm_width)
                    ),
                ]
            )
            / 255.0
            * 1.2
        ),
    )

    return PalmCreaseMetrics(
        heart_line_curvature=round(heart_line_curvature, 3),
        heart_line_length=round(heart_line_length, 3),
        heart_line_depth=round(heart_line_depth, 3),
        head_line_slope=round(head_line_slope, 3),
        head_line_length=round(head_line_length, 3),
        head_line_depth=round(head_line_depth, 3),
        life_line_arc=round(life_line_arc, 3),
        life_line_length=round(life_line_length, 3),
        life_line_depth=round(life_line_depth, 3),
        fate_line_prominence=round(fate_line_prominence, 3),
        fate_line_length=round(fate_line_length, 3),
        fate_line_from_moon=round(fate_line_from_moon, 3),
        sun_line_prominence=round(sun_line_prominence, 3),
        mount_jupiter_prominence=round(mount_jupiter_prominence, 3),
        mount_venus_prominence=round(mount_venus_prominence, 3),
        mount_mercury_prominence=round(mount_mercury_prominence, 3),
        mount_moon_prominence=round(mount_moon_prominence, 3),
        crease_mask=palm_edges,
    )
