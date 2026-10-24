"""The overlay the user is shown alongside their reading.

This is not decoration. A palm reading from a photograph is only as trustworthy as
the tracing behind it, and the only way to let someone judge that for themselves is
to show them exactly which creases the system followed. If a trace has wandered
onto a skin fold, the picture says so immediately, where a page of confident prose
would not.
"""

from __future__ import annotations

import base64

import cv2
import numpy as np

from app.services.palm_cv import landmarks as L
from app.services.palm_cv.creases import CanonicalPalm, TracedCrease

#: Distinct in both hue and lightness, so the lines stay separable for viewers who
#: do not distinguish red from green.
CREASE_COLOURS: dict[str, tuple[int, int, int]] = {
    "heart": (229, 57, 53),    # red
    "head": (30, 136, 229),    # blue
    "life": (67, 160, 71),     # green
    "fate": (251, 192, 45),    # amber
}

CREASE_LABELS: dict[str, str] = {
    "heart": "Heart (Water)",
    "head": "Head (Air)",
    "life": "Life (Earth)",
    "fate": "Fate (Fire)",
}


def _draw_badge(
    canvas: np.ndarray,
    text: str,
    pt: tuple[int, int],
    colour: tuple[int, int, int],
) -> tuple[int, int, int, int]:
    """Draw a modern translucent pill badge with a coloured dot and crisp label."""
    h, w = canvas.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.38
    thickness = 1
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)

    pad_x = 6
    pad_y = 4
    x = int(np.clip(pt[0], pad_x + 4, w - tw - pad_x - 18))
    y = int(np.clip(pt[1], th + pad_y + 4, h - pad_y - 4))

    x1, y1 = x - pad_x, y - th - pad_y
    x2, y2 = x + tw + pad_x + 12, y + baseline + pad_y - 2

    x1_c, y1_c = max(0, x1), max(0, y1)
    x2_c, y2_c = min(w, x2), min(h, y2)

    if x2_c > x1_c and y2_c > y1_c:
        sub = canvas[y1_c:y2_c, x1_c:x2_c]
        dark = np.full_like(sub, (16, 12, 10))
        cv2.addWeighted(sub, 0.25, dark, 0.75, 0, sub)

    dot_x = x1 + 6
    dot_y = (y1 + y2) // 2
    cv2.circle(canvas, (dot_x, dot_y), 3, colour, -1, cv2.LINE_AA)
    cv2.putText(canvas, text, (dot_x + 7, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
    return (x1, y1, x2, y2)


def draw_overlay(
    palm: CanonicalPalm,
    creases: dict[str, TracedCrease],
    landmarks_px: list[tuple[float, float, float]] | None = None,
    show_skeleton: bool = False,
    original_image: np.ndarray | None = None,
) -> np.ndarray:
    """The palm with every traced crease drawn on it.

    When original_image is provided, creases are inversely transformed via
    palm.matrix and rendered directly onto the user's full photograph with
    subpixel anti-aliasing and luminous biometric styling.
    """
    if original_image is not None:
        canvas = original_image.copy()
        h, w = canvas.shape[:2]
        inv_matrix = np.linalg.inv(palm.matrix)

        if show_skeleton and landmarks_px:
            for a, b in L.HAND_CONNECTIONS:
                pa = (int(round(landmarks_px[a][0])), int(round(landmarks_px[a][1])))
                pb = (int(round(landmarks_px[b][0])), int(round(landmarks_px[b][1])))
                cv2.line(canvas, pa, pb, (220, 220, 220), 1, cv2.LINE_AA)

        placed_boxes: list[tuple[int, int, int, int]] = []
        for name, crease in creases.items():
            if not crease.found or len(crease.path) < 2:
                continue
            label_text = CREASE_LABELS.get(name, name)
            colour = CREASE_COLOURS.get(name, (255, 255, 255))
            light_colour = tuple(min(255, int(c * 0.4 + 200 * 0.6)) for c in colour)

            # Map canonical normalized points back to original image coordinates
            can_pts = []
            for x, y in crease.path:
                cx = (1.0 - x) * palm.size if palm.mirrored else x * palm.size
                cy = y * palm.size
                can_pts.append([cx, cy])
            can_arr = np.array(can_pts, dtype=np.float32).reshape(-1, 1, 2)
            orig_pts = cv2.perspectiveTransform(can_arr, inv_matrix).reshape(-1, 2)
            pts_int = np.round(orig_pts).astype(np.int32)

            # Glowing multi-layer anti-aliased polyline
            cv2.polylines(canvas, [pts_int], False, (14, 12, 10), 6, cv2.LINE_AA)
            cv2.polylines(canvas, [pts_int], False, colour, 3, cv2.LINE_AA)
            cv2.polylines(canvas, [pts_int], False, light_colour, 1, cv2.LINE_AA)

            # Strategic anchor index per crease to place badges in non-conflicting palm quadrants
            if name == "heart":
                badge_anchor_idx = min(len(pts_int) - 1, int(len(pts_int) * 0.85))
            elif name == "head":
                badge_anchor_idx = min(len(pts_int) - 1, int(len(pts_int) * 0.50))
            elif name == "life":
                badge_anchor_idx = min(len(pts_int) - 1, int(len(pts_int) * 0.25))
            else:  # fate
                badge_anchor_idx = min(len(pts_int) - 1, int(len(pts_int) * 0.10))

            anchor = pts_int[badge_anchor_idx]
            bx = int(anchor[0] + 6)
            by = int(anchor[1] - 8)

            for _ in range(8):
                overlap = False
                for ox1, oy1, ox2, oy2 in placed_boxes:
                    if not (bx + 110 < ox1 or bx > ox2 or by < oy1 or by - 22 > oy2):
                        overlap = True
                        break
                if overlap:
                    by += 22
                    if by > h - 20:
                        by = 24
                else:
                    break

            box = _draw_badge(canvas, label_text, (bx, by), colour)
            placed_boxes.append(box)

        return canvas

    # Fallback to drawing on canonical image
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
                (int(wa[0]), int(wa[1])), (int(wb[0]), int(wb[1])),
                (255, 255, 255), 1, cv2.LINE_AA,
            )

    placed_boxes_can: list[tuple[int, int, int, int]] = []
    for name, crease in creases.items():
        if not crease.found or len(crease.path) < 2:
            continue
        colour = CREASE_COLOURS.get(name, (255, 255, 255))
        light_colour = tuple(min(255, int(c * 0.4 + 200 * 0.6)) for c in colour)
        points = np.array(
            [[int(round(x * size)), int(round(y * size))] for x, y in crease.path], dtype=np.int32
        )
        cv2.polylines(canvas, [points], False, (14, 12, 10), 6, cv2.LINE_AA)
        cv2.polylines(canvas, [points], False, colour, 3, cv2.LINE_AA)
        cv2.polylines(canvas, [points], False, light_colour, 1, cv2.LINE_AA)

        head = points[0]
        bx = int(np.clip(head[0] + 8, 4, size - 150))
        by = int(np.clip(head[1] - 8, 18, size - 8))
        while any(abs(by - oy1) < 22 for _, oy1, _, _ in placed_boxes_can):
            by += 24
            if by > size - 8:
                by = 18
                break
        box = _draw_badge(canvas, CREASE_LABELS.get(name, name), (bx, by), colour)
        placed_boxes_can.append(box)

    return canvas


def draw_response_map(palm: CanonicalPalm) -> np.ndarray:
    """The valley-response map, for support and for debugging a bad scan."""
    coloured = cv2.applyColorMap((palm.response * 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    return cv2.cvtColor(coloured, cv2.COLOR_BGR2RGB)


def to_data_url(image_rgb: np.ndarray, quality: int = 86) -> str:
    """JPEG data URL, so the overlay can be returned inline with the reading."""
    ok, buffer = cv2.imencode(
        ".jpg", cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    )
    if not ok:
        raise RuntimeError("Could not encode the overlay image.")
    return "data:image/jpeg;base64," + base64.b64encode(buffer.tobytes()).decode("ascii")
