"""The overlay the user is shown alongside their reading.

This is not decoration. A palm reading from a photograph is only as trustworthy as
the tracing behind it, and the only way to let someone judge that for themselves is
to show them exactly which creases the system followed. If a trace has wandered
onto a skin fold, the picture says so immediately, where a page of confident prose
would not.

Rendered with high-fidelity bioluminescent energy nadis, subpixel anti-aliasing,
Gaussian glow passes, and elegant non-intrusive micro-tags.
"""

from __future__ import annotations

import base64
from typing import Any

import cv2
import numpy as np

from app.services.palm_cv import landmarks as L
from app.services.palm_cv.creases import CanonicalPalm, TracedCrease

#: Celestial bioluminescent palette (RGB)
CREASE_COLOURS: dict[str, tuple[int, int, int]] = {
    "heart": (244, 63, 94),     # Radiant Rose Quartz / Fuchsia
    "head": (6, 182, 212),      # Electric Azure / Cyan
    "life": (16, 185, 129),     # Pranic Emerald / Jade
    "fate": (245, 158, 11),     # Divine Solar Gold
}

CREASE_LABELS: dict[str, str] = {
    "heart": "Heart Line",
    "head": "Head Line",
    "life": "Life Line",
    "fate": "Fate Line",
}

SECONDARY_COLOURS: dict[str, tuple[int, int, int]] = {
    "sun": (234, 179, 8),       # Warm Solar Amber
    "mercury": (20, 184, 166),  # Aquamarine / Turquoise
    "mars": (249, 115, 22),     # Coral Flame
}

SECONDARY_LABELS: dict[str, str] = {
    "sun": "Sun Line",
    "mercury": "Mercury Line",
    "mars": "Mars Line",
}


def _smooth_crease_points(pts: np.ndarray, window: int = 5) -> np.ndarray:
    """Smooth crease polyline using moving average window to eliminate pixel stepping."""
    if len(pts) < window:
        return pts
    kernel = np.ones(window, dtype=np.float32) / float(window)
    x = np.convolve(pts[:, 0].astype(np.float32), kernel, mode="same")
    y = np.convolve(pts[:, 1].astype(np.float32), kernel, mode="same")
    half = window // 2
    x[:half] = pts[:half, 0]
    x[-half:] = pts[-half:, 0]
    y[:half:] = pts[:half, 1]
    y[-half:] = pts[-half:, 1]
    return np.round(np.stack([x, y], axis=1)).astype(np.int32)


def _draw_luminous_crease(
    canvas: np.ndarray,
    pts: np.ndarray,
    colour: tuple[int, int, int],
    is_primary: bool = True,
) -> None:
    """Render a clean, high-contrast luminous energy line along crease path."""
    if len(pts) < 2:
        return

    pts_smooth = _smooth_crease_points(pts, window=5 if len(pts) >= 6 else 3)

    # 1. Outer radiant glow
    glow_width = 5 if is_primary else 3
    cv2.polylines(canvas, [pts_smooth], False, colour, glow_width, cv2.LINE_AA)

    # 2. Super-fine bright core
    core_colour = (255, 255, 255) if is_primary else tuple(min(255, c + 75) for c in colour)
    cv2.polylines(canvas, [pts_smooth], False, core_colour, 1, cv2.LINE_AA)

    # 3. Terminal pearls
    for pt in (pts_smooth[0], pts_smooth[-1]):
        cv2.circle(canvas, (int(pt[0]), int(pt[1])), 4 if is_primary else 3, colour, -1, cv2.LINE_AA)
        cv2.circle(canvas, (int(pt[0]), int(pt[1])), 2, (255, 255, 255), -1, cv2.LINE_AA)


def _draw_minimalist_badge(
    canvas: np.ndarray,
    text: str,
    anchor_pt: tuple[int, int],
    target_pt: tuple[int, int],
    colour: tuple[int, int, int],
) -> tuple[int, int, int, int]:
    """Draw a modern translucent glassmorphic micro-badge with a thin leader line."""
    h, w = canvas.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.33
    thickness = 1
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)

    pad_x = 7
    pad_y = 4
    bx = int(np.clip(target_pt[0], pad_x + 4, w - tw - pad_x - 16))
    by = int(np.clip(target_pt[1], th + pad_y + 4, h - pad_y - 6))

    x1, y1 = bx - pad_x, by - th - pad_y
    x2, y2 = bx + tw + pad_x + 10, by + baseline + pad_y - 1

    x1_c, y1_c = max(0, x1), max(0, y1)
    x2_c, y2_c = min(w, x2), min(h, y2)

    # Thin leader line directly to badge center
    cv2.line(canvas, anchor_pt, ((x1 + x2) // 2, (y1 + y2) // 2), colour, 1, cv2.LINE_AA)

    # Dark badge backdrop (solid, crisp, zero canvas bleaching)
    if x2_c > x1_c and y2_c > y1_c:
        canvas[y1_c:y2_c, x1_c:x2_c] = (15, 23, 42)
        cv2.rectangle(canvas, (x1_c, y1_c), (x2_c, y2_c), colour, 1, cv2.LINE_AA)

    dot_x = x1 + 6
    dot_y = (y1 + y2) // 2
    cv2.circle(canvas, (dot_x, dot_y), 3, colour, -1, cv2.LINE_AA)
    cv2.circle(canvas, (dot_x, dot_y), 1, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.putText(
        canvas, text, (dot_x + 6, by), font, scale, (255, 255, 255), thickness, cv2.LINE_AA
    )
    return (x1, y1, x2, y2)


def draw_overlay(
    palm: CanonicalPalm,
    creases: dict[str, TracedCrease],
    landmarks_px: list[tuple[float, float, float]] | None = None,
    show_skeleton: bool = False,
    original_image: np.ndarray | None = None,
    secondary_creases: dict[str, TracedCrease] | None = None,
    sacred_marks: list[dict[str, Any]] | None = None,
) -> np.ndarray:
    """The palm with every traced crease drawn on it.

    When original_image is provided, creases are inversely transformed via
    palm.matrix and rendered directly onto the user's photograph with
    subpixel anti-aliasing, multi-pass bioluminescent glow, and clean edge badges.
    """
    if original_image is not None:
        canvas = original_image.copy()
        h, w = canvas.shape[:2]
        inv_matrix = np.linalg.inv(palm.matrix)

        # Subtle anatomical skeleton wireframe
        if show_skeleton and landmarks_px:
            skel_layer = canvas.copy()
            for a, b in L.HAND_CONNECTIONS:
                pa = (int(round(landmarks_px[a][0])), int(round(landmarks_px[a][1])))
                pb = (int(round(landmarks_px[b][0])), int(round(landmarks_px[b][1])))
                cv2.line(skel_layer, pa, pb, (220, 240, 255), 1, cv2.LINE_AA)
            cv2.addWeighted(canvas, 1.0, skel_layer, 0.40, 0, canvas)

        placed_boxes: list[tuple[int, int, int, int]] = []

        # 1. Render Secondary Creases (Sun, Mercury, Mars) first as subtle underlay
        if secondary_creases:
            for name, crease in secondary_creases.items():
                if not crease.found or len(crease.path) < 2:
                    continue
                colour = SECONDARY_COLOURS.get(name, (200, 200, 200))
                can_pts = []
                for x, y in crease.path:
                    cx = (1.0 - x) * palm.size if palm.mirrored else x * palm.size
                    cy = y * palm.size
                    can_pts.append([cx, cy])
                can_arr = np.array(can_pts, dtype=np.float32).reshape(-1, 1, 2)
                orig_pts = cv2.perspectiveTransform(can_arr, inv_matrix).reshape(-1, 2)
                pts_int = np.round(orig_pts).astype(np.int32)
                _draw_luminous_crease(canvas, pts_int, colour, is_primary=False)

        # 2. Render Principal Creases (Heart, Head, Life, Fate)
        for name, crease in creases.items():
            if not crease.found or len(crease.path) < 2:
                continue
            colour = CREASE_COLOURS.get(name, (255, 255, 255))
            label_text = CREASE_LABELS.get(name, name)

            can_pts = []
            for x, y in crease.path:
                cx = (1.0 - x) * palm.size if palm.mirrored else x * palm.size
                cy = y * palm.size
                can_pts.append([cx, cy])
            can_arr = np.array(can_pts, dtype=np.float32).reshape(-1, 1, 2)
            orig_pts = cv2.perspectiveTransform(can_arr, inv_matrix).reshape(-1, 2)
            pts_int = np.round(orig_pts).astype(np.int32)

            _draw_luminous_crease(canvas, pts_int, colour, is_primary=True)

            # Elegant terminal placement for labels at outer margins
            if name == "heart":
                term_pt = pts_int[-1]
                # Offset toward outer percussion
                badge_x = int(np.clip(term_pt[0] + 35, 15, w - 90))
                badge_y = int(np.clip(term_pt[1] - 12, 20, h - 20))
            elif name == "head":
                term_pt = pts_int[-1]
                badge_x = int(np.clip(term_pt[0] + 30, 15, w - 90))
                badge_y = int(np.clip(term_pt[1] + 18, 20, h - 20))
            elif name == "life":
                term_pt = pts_int[-1]
                badge_x = int(np.clip(term_pt[0] - 25, 15, w - 90))
                badge_y = int(np.clip(term_pt[1] + 30, 20, h - 20))
            else:  # fate
                term_pt = pts_int[0]
                badge_x = int(np.clip(term_pt[0] + 20, 15, w - 90))
                badge_y = int(np.clip(term_pt[1] + 25, 20, h - 20))

            anchor = (int(term_pt[0]), int(term_pt[1]))
            # Avoid badge collisions
            for _ in range(6):
                if any(not (badge_x + 85 < ox1 or badge_x > ox2 or badge_y < oy1 or badge_y - 18 > oy2) for ox1, oy1, ox2, oy2 in placed_boxes):
                    badge_y += 20
                    if badge_y > h - 16:
                        badge_y = 20
                else:
                    break

            box = _draw_minimalist_badge(canvas, label_text, anchor, (badge_x, badge_y), colour)
            placed_boxes.append(box)

        # 3. Render Detected Sacred Marks (Golden Starburst glyphs)
        if sacred_marks:
            for sm in sacred_marks:
                if not sm.get("found") or not sm.get("location_norm"):
                    continue
                loc = sm["location_norm"]
                sx = int(round(loc[0] * w))
                sy = int(round(loc[1] * h))
                name = sm.get("sanskrit_name", "Sacred Mark")

                # Subtle golden aura ring
                cv2.circle(canvas, (sx, sy), 8, (245, 158, 11), 1, cv2.LINE_AA)
                cv2.circle(canvas, (sx, sy), 2, (255, 255, 255), -1, cv2.LINE_AA)

        return canvas

    # Fallback to drawing on canonical square image
    canvas = palm.image.copy()
    size = palm.size

    if palm.mask is not None:
        outside = palm.mask == 0
        canvas[outside] = (canvas[outside] * 0.45).astype(np.uint8)

    if show_skeleton and landmarks_px:
        for a, b in L.HAND_CONNECTIONS:
            pa = np.array([[landmarks_px[a][0], landmarks_px[a][1]]], dtype=np.float32)
            pb = np.array([[landmarks_px[b][0], landmarks_px[b][1]]], dtype=np.float32)
            wa = cv2.perspectiveTransform(pa.reshape(1, 1, 2), palm.matrix).reshape(2)
            wb = cv2.perspectiveTransform(pb.reshape(1, 1, 2), palm.matrix).reshape(2)
            if palm.mirrored:
                wa[0], wb[0] = size - wa[0], size - wb[0]
            cv2.line(
                canvas,
                (int(wa[0]), int(wa[1])),
                (int(wb[0]), int(wb[1])),
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

    placed_boxes_can: list[tuple[int, int, int, int]] = []
    for name, crease in creases.items():
        if not crease.found or len(crease.path) < 2:
            continue
        colour = CREASE_COLOURS.get(name, (255, 255, 255))
        points = np.array(
            [[int(round(x * size)), int(round(y * size))] for x, y in crease.path],
            dtype=np.int32,
        )
        _draw_luminous_crease(canvas, points, colour, is_primary=True)

        head = points[0]
        bx = int(np.clip(head[0] + 8, 4, size - 120))
        by = int(np.clip(head[1] - 8, 18, size - 8))
        box = _draw_minimalist_badge(
            canvas,
            CREASE_LABELS.get(name, name),
            (int(head[0]), int(head[1])),
            (bx, by),
            colour,
        )
        placed_boxes_can.append(box)

    return canvas


def draw_response_map(palm: CanonicalPalm) -> np.ndarray:
    """The valley-response map, for support and for debugging a bad scan."""
    coloured = cv2.applyColorMap((palm.response * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    return cv2.cvtColor(coloured, cv2.COLOR_BGR2RGB)


def to_data_url(image_rgb: np.ndarray, quality: int = 88) -> str:
    """JPEG data URL, so the overlay can be returned inline with the reading."""
    ok, buffer = cv2.imencode(
        ".jpg",
        cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR),
        [int(cv2.IMWRITE_JPEG_QUALITY), quality],
    )
    if not ok:
        raise RuntimeError("Could not encode the overlay image.")
    return "data:image/jpeg;base64," + base64.b64encode(buffer.tobytes()).decode("ascii")
