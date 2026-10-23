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


def _draw_label(
    canvas: np.ndarray, text: str, origin: tuple[int, int], colour: tuple[int, int, int]
) -> None:
    """Label with a dark plate behind it, so it stays readable over any skin tone."""
    font, scale, thickness = cv2.FONT_HERSHEY_SIMPLEX, 0.46, 1
    (width, height), baseline = cv2.getTextSize(text, font, scale, thickness)
    x, y = origin
    cv2.rectangle(
        canvas, (x - 4, y - height - 6), (x + width + 6, y + baseline + 2), (18, 14, 10), -1
    )
    cv2.putText(canvas, text, (x, y), font, scale, colour, thickness, cv2.LINE_AA)


def draw_overlay(
    palm: CanonicalPalm,
    creases: dict[str, TracedCrease],
    landmarks_px: list[tuple[float, float, float]] | None = None,
    show_skeleton: bool = False,
) -> np.ndarray:
    """The normalised palm with every traced crease drawn on it."""
    canvas = palm.image.copy()
    size = palm.size

    # A faint wash outside the palm, so the region that was actually searched is
    # obvious and nobody wonders why a line stops where it does.
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

    used_label_rows: list[int] = []
    for name, crease in creases.items():
        if not crease.found or len(crease.path) < 2:
            continue
        colour = CREASE_COLOURS.get(name, (255, 255, 255))
        points = np.array(
            [[int(x * size), int(y * size)] for x, y in crease.path], dtype=np.int32
        )
        # A dark halo first, so the line reads against both pale and dark skin.
        cv2.polylines(canvas, [points], False, (20, 16, 12), 6, cv2.LINE_AA)
        cv2.polylines(canvas, [points], False, colour, 3, cv2.LINE_AA)

        head = points[0]
        label_x = int(np.clip(head[0] + 8, 4, size - 150))
        label_y = int(np.clip(head[1] - 8, 18, size - 8))
        # Two creases that begin near each other would otherwise print their
        # labels on top of one another and neither would be readable.
        while any(abs(label_y - taken) < 22 for taken in used_label_rows):
            label_y += 24
            if label_y > size - 8:
                label_y = 18
                break
        used_label_rows.append(label_y)
        _draw_label(canvas, CREASE_LABELS.get(name, name), (label_x, label_y), colour)

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
