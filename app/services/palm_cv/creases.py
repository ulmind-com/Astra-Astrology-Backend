"""Finding and tracing the principal palm creases.

HOW THIS DIFFERS FROM THE ATTEMPT THAT WAS REMOVED
--------------------------------------------------
An earlier pipeline in this repository (commit 5994b57, removed the same day)
reported crease metrics that never touched the creases. Its "heart line length"
was the distance between the index and pinky knuckles; its "life line arc" was
the thumb-to-wrist distance; its "depth" figures were Canny edge-pixel counts in a
rectangle multiplied by arbitrary constants. Those numbers would come out
identical on a photograph of a hand with no lines on it at all.

This module traces the actual creases. The method:

  1. Warp the palm into a fixed square frame using the landmarks, so a line's
     position means the same thing regardless of photo size, distance or rotation.
  2. Build a valley-response map. Creases are narrow *dark valleys* in the
     intensity surface, not step edges, so an edge detector is the wrong tool - it
     fires on both banks of a crease and equally hard on a skin-tone boundary. A
     bank of Gabor filters tuned to dark bars picks out valleys and their
     orientation together.
  3. Trace each principal crease by dynamic programming along the axis it runs in,
     choosing at each step the position with the strongest response subject to a
     smoothness penalty. This yields one continuous path per crease rather than a
     scatter of fragments needing to be stitched.
  4. Score the path. A path is always returned by the search; whether it is a
     *line* depends on the response it actually accumulated. A trace that averaged
     little more than skin texture is reported as not found, not as a faint line.

WHAT THIS CAN AND CANNOT SEE
----------------------------
It measures the four principal creases: position, path, length, curvature, where
each begins and ends relative to the fingers, how continuous it is, and how
strongly it registers. Those support the client's rules about where the heart line
terminates, how far the earth line reaches, and the gap between the heart and head
lines.

It does not see mount elevation - that is height, and a single photograph has no
depth. It does not reliably resolve islands, chains, stars or bars, which need far
more resolution than a phone photo of a whole hand provides. Those are reported as
unavailable rather than estimated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import cv2
import numpy as np

from app.services.palm_cv import landmarks as L
from app.services.palm_cv.config import DEFAULT_CONFIG, PalmScanConfig

CreaseName = Literal["heart", "head", "life", "fate"]

#: The client's documents name the creases after elements. Both names are carried
#: so a rule written either way can be matched.
CREASE_ELEMENTAL = {
    "heart": "Water line",
    "head": "Air line",
    "life": "Earth line",
    "fate": "Fire line",
}


@dataclass
class TracedCrease:
    name: CreaseName
    found: bool
    #: Path in canonical palm coordinates, each 0..1 with (0,0) at the radial side
    #: of the wrist and (1,1) under the pinky knuckle.
    path: list[tuple[float, float]] = field(default_factory=list)
    #: Mean valley response along the path, 0..1.
    strength: float = 0.0
    #: Fraction of the path that held a clear response.
    continuity: float = 0.0
    #: How far the path stands above the median response of its own band. About
    #: 1.0 means it is indistinguishable from the surrounding skin.
    contrast: float = 0.0
    #: Path length as a fraction of the canonical frame width.
    length: float = 0.0
    #: Positive means bowing towards the fingers, negative towards the wrist.
    curvature: float = 0.0
    start: tuple[float, float] | None = None
    end: tuple[float, float] | None = None
    #: Which finger the crease terminates under, when that is meaningful.
    termination_zone: str | None = None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "elemental_name": CREASE_ELEMENTAL[self.name],
            "found": self.found,
            "strength": round(self.strength, 4),
            "continuity": round(self.continuity, 4),
            "contrast": round(self.contrast, 4),
            "length": round(self.length, 4),
            "curvature": round(self.curvature, 4),
            "start": [round(v, 4) for v in self.start] if self.start else None,
            "end": [round(v, 4) for v in self.end] if self.end else None,
            "termination_zone": self.termination_zone,
            "path": [[round(x, 4), round(y, 4)] for x, y in self.path],
            "notes": self.notes,
        }


@dataclass
class CanonicalPalm:
    """The palm warped into a fixed square, with the transform that got it there."""

    image: np.ndarray          # canonical_size x canonical_size, RGB
    response: np.ndarray       # same size, float32 valley response 0..1, palm only
    mask: np.ndarray           # same size, 255 inside the palm
    matrix: np.ndarray         # 3x3 perspective transform, original -> canonical
    size: int
    #: Where each knuckle landed in canonical coordinates, used to say which finger
    #: a crease ends under.
    knuckles_canonical: dict[str, tuple[float, float]]


def build_canonical_palm(
    image_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]],
    config: PalmScanConfig = DEFAULT_CONFIG,
) -> CanonicalPalm:
    """Warp the palm into a square frame and compute its valley response.

    The four corners are taken from landmarks rather than from the image, so the
    same physical palm maps to the same canonical coordinates whether it was shot
    close up or at arm's length, straight on or rotated.
    """
    size = config.canonical_size

    points = np.array([[p[0], p[1]] for p in landmarks_px], dtype=np.float32)
    wrist = points[L.WRIST]
    index_mcp = points[L.INDEX_MCP]
    pinky_mcp = points[L.PINKY_MCP]
    middle_mcp = points[L.MIDDLE_MCP]
    thumb_cmc = points[L.THUMB_CMC]

    # Build an orthonormal palm frame rather than using the landmarks as corners
    # directly. Taking the corners straight from landmarks only frames the palm
    # correctly when the hand is already upright and square to the camera; off
    # axis it crops into the palm and the crease bands then point at the wrong
    # places.
    up = middle_mcp - wrist
    up_len = float(np.linalg.norm(up))
    if up_len < 1e-3:
        up = np.array([0.0, -1.0], dtype=np.float32)
        up_len = 1.0
    up_unit = up / up_len
    right_unit = np.array([-up_unit[1], up_unit[0]], dtype=np.float32)

    # Measure the palm's own extent along those axes, including the thumb ball,
    # so the whole reading surface is inside the frame whatever the hand's shape.
    palm_points = np.array(
        [points[i] for i in (L.WRIST, L.THUMB_CMC, L.THUMB_MCP, L.INDEX_MCP,
                             L.MIDDLE_MCP, L.RING_MCP, L.PINKY_MCP)],
        dtype=np.float32,
    )
    centred = palm_points - wrist
    along = centred @ up_unit
    across = centred @ right_unit

    # Pad outward: up past the knuckles so the heart line is not clipped, down
    # past the wrist landmark so the base of the earth line is included.
    pad = 0.10 * up_len
    top = float(along.max()) + pad * 1.4
    bottom = float(along.min()) - pad * 1.6
    left = float(across.min()) - pad
    right = float(across.max()) + pad

    # Keep the thumb side in view; on a wide hand the thumb ball reaches further
    # than the knuckle row.
    thumb_across = float((thumb_cmc - wrist) @ right_unit)
    left = min(left, thumb_across - pad)
    right = max(right, thumb_across + pad)

    def corner(a: float, c: float) -> np.ndarray:
        return wrist + up_unit * a + right_unit * c

    # Order: bottom-left, bottom-right, top-right, top-left, matching `target`.
    source = np.array(
        [corner(bottom, left), corner(bottom, right), corner(top, right), corner(top, left)],
        dtype=np.float32,
    )
    target = np.array(
        [[0, size - 1], [size - 1, size - 1], [size - 1, 0], [0, 0]], dtype=np.float32
    )

    matrix = cv2.getPerspectiveTransform(source, target)
    canonical = cv2.warpPerspective(
        image_rgb, matrix, (size, size), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    knuckles: dict[str, tuple[float, float]] = {}
    for finger, (mcp, *_rest) in L.FINGER_CHAINS.items():
        point = np.array([[landmarks_px[mcp][0], landmarks_px[mcp][1]]], dtype=np.float32)
        warped = cv2.perspectiveTransform(point.reshape(1, 1, 2), matrix).reshape(2)
        knuckles[finger] = (float(warped[0] / size), float(warped[1] / size))

    # Warp the palm outline into the canonical frame and keep only what falls
    # inside it, so nothing behind the hand can be mistaken for a crease.
    outline = np.array(
        [[points[i][0], points[i][1]] for i in L.PALM_BOUNDARY], dtype=np.float32
    ).reshape(-1, 1, 2)
    outline_canonical = cv2.perspectiveTransform(outline, matrix).reshape(-1, 2)
    # The hull of the knuckles and wrist sits well inside the real palm - those
    # landmarks mark joint centres, not the edge of the hand - so it is expanded
    # about its own centroid to cover the reading surface. Without this the mask
    # blanks out most of the palm and the traces have nothing to follow.
    hull = cv2.convexHull(outline_canonical.astype(np.float32)).reshape(-1, 2)
    centroid = hull.mean(axis=0)
    expanded = centroid + (hull - centroid) * 1.5
    mask = np.zeros((size, size), dtype=np.uint8)
    cv2.fillConvexPoly(mask, expanded.astype(np.int32), 255)
    # Keep the mask inside the frame, then pull the edge in a little: the palm
    # outline is itself a strong intensity step and would read as a crease running
    # around the rim.
    mask = cv2.erode(mask, np.ones((11, 11), np.uint8), iterations=1)

    response = _valley_response(canonical, config)
    response[mask == 0] = 0.0

    return CanonicalPalm(
        image=canonical,
        response=response,
        mask=mask,
        matrix=matrix,
        size=size,
        knuckles_canonical=knuckles,
    )


def _valley_response(canonical_rgb: np.ndarray, config: PalmScanConfig) -> np.ndarray:
    """Strength of dark, narrow, line-like structure at every pixel.

    Creases are valleys: darker than the skin on both sides, a few pixels wide. A
    Gabor bank tuned to that profile responds to them and largely ignores broad
    shading, which is what makes this usable under ordinary room lighting.
    """
    # The red channel carries the least crease contrast in skin; a weighted grey
    # favouring green and blue separates creases from skin tone better than a
    # plain luminance conversion.
    channels = canonical_rgb.astype(np.float32)
    gray = (0.15 * channels[:, :, 0] + 0.5 * channels[:, :, 1] + 0.35 * channels[:, :, 2])
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    clahe = cv2.createCLAHE(
        clipLimit=config.clahe_clip_limit,
        tileGridSize=(config.clahe_tile_grid, config.clahe_tile_grid),
    )
    gray = clahe.apply(gray)

    # Flatten slow lighting gradients so one side of the palm being brighter does
    # not swamp the response there.
    background = cv2.GaussianBlur(gray, (0, 0), sigmaX=config.canonical_size / 24.0)
    flattened = cv2.subtract(gray.astype(np.float32), background.astype(np.float32))

    # Invert, so creases become ridges and the filter bank looks for bright bars.
    inverted = -flattened

    accumulated = np.zeros_like(inverted, dtype=np.float32)
    ksize = config.gabor_kernel_size | 1  # must be odd
    for index in range(config.gabor_orientations):
        theta = np.pi * index / config.gabor_orientations
        kernel = cv2.getGaborKernel(
            (ksize, ksize),
            config.gabor_sigma,
            theta,
            config.gabor_lambda,
            config.gabor_gamma,
            0,
            ktype=cv2.CV_32F,
        )
        # Zero-mean so flat regions give no response at all.
        kernel -= kernel.mean()
        filtered = cv2.filter2D(inverted, cv2.CV_32F, kernel)
        accumulated = np.maximum(accumulated, filtered)

    accumulated[accumulated < 0] = 0.0
    peak = float(accumulated.max())
    if peak > 1e-6:
        accumulated /= peak
    return accumulated.astype(np.float32)


def _trace_horizontal(
    response: np.ndarray,
    row_lo: int,
    row_hi: int,
    col_lo: int,
    col_hi: int,
    config: PalmScanConfig,
) -> tuple[list[tuple[int, int]], float]:
    """Best left-to-right path through a band, by dynamic programming.

    At each column the path may move at most `trace_max_step` rows, and paying a
    `trace_smoothness` penalty per row moved. That keeps it on one crease instead
    of hopping between neighbouring ones whenever the next is marginally brighter.
    """
    row_lo = max(0, row_lo)
    row_hi = min(response.shape[0], row_hi)
    col_lo = max(0, col_lo)
    col_hi = min(response.shape[1], col_hi)
    if row_hi - row_lo < 3 or col_hi - col_lo < 8:
        return [], 0.0

    band = response[row_lo:row_hi, col_lo:col_hi]
    rows, cols = band.shape

    cost = np.full((rows, cols), -np.inf, dtype=np.float32)
    back = np.zeros((rows, cols), dtype=np.int32)
    cost[:, 0] = band[:, 0]

    step = config.trace_max_step
    penalty = config.trace_smoothness

    for col in range(1, cols):
        for offset in range(-step, step + 1):
            shifted = np.roll(cost[:, col - 1], offset)
            if offset > 0:
                shifted[:offset] = -np.inf
            elif offset < 0:
                shifted[offset:] = -np.inf
            candidate = shifted - penalty * abs(offset)
            better = candidate > cost[:, col]
            cost[better, col] = candidate[better]
            back[better, col] = offset
        cost[:, col] += band[:, col]

    end_row = int(np.argmax(cost[:, cols - 1]))
    path: list[tuple[int, int]] = []
    row = end_row
    for col in range(cols - 1, -1, -1):
        path.append((col + col_lo, row + row_lo))
        row = int(np.clip(row - back[row, col], 0, rows - 1))
    path.reverse()

    total = float(np.mean([band[min(rows - 1, max(0, y - row_lo)), x - col_lo] for x, y in path]))
    return path, total


def _trace_vertical(
    response: np.ndarray,
    col_lo: int,
    col_hi: int,
    row_lo: int,
    row_hi: int,
    config: PalmScanConfig,
) -> tuple[list[tuple[int, int]], float]:
    """The same search run bottom-to-top, for creases that run that way."""
    transposed = np.ascontiguousarray(response.T)
    path, score = _trace_horizontal(transposed, col_lo, col_hi, row_lo, row_hi, config)
    return [(y, x) for x, y in path], score


def _score_path(
    response: np.ndarray,
    path: list[tuple[int, int]],
    band: tuple[int, int, int, int],
    config: PalmScanConfig,
) -> tuple[float, float, float]:
    """How strongly a path registers, how continuously, and how far above its band.

    The contrast ratio is the one that matters. The dynamic-programming search
    always returns a best path, so on a weak photo it returns a flat line through
    noise - and that line can still clear an absolute threshold. Dividing by the
    band's own median asks the only question worth asking: is this brighter than
    the skin around it, or is it just the least dark part of a featureless region?
    A straight line through texture scores about 1.0 here; a real crease scores
    well above it.
    """
    if not path:
        return 0.0, 0.0, 0.0

    height, width = response.shape
    values = np.array(
        [float(response[min(height - 1, max(0, y)), min(width - 1, max(0, x))]) for x, y in path],
        dtype=np.float32,
    )
    strength = float(values.mean())

    row_lo, row_hi, col_lo, col_hi = band
    region = response[max(0, row_lo):min(height, row_hi), max(0, col_lo):min(width, col_hi)]
    inside = region[region > 0.0]
    baseline = float(np.median(inside)) if inside.size else 0.0
    contrast = float(strength / baseline) if baseline > 1e-6 else 0.0

    # Continuity is measured against the band too, so a crease that fades over part
    # of its run is not punished for the photo being darker there.
    clear_level = max(config.min_line_response, baseline * config.min_contrast_ratio)
    clear = float(np.count_nonzero(values >= clear_level)) / float(values.size)

    return strength, clear, contrast


def _curvature(path_norm: list[tuple[float, float]]) -> float:
    """Signed bow of a path away from the straight line joining its ends.

    Positive means the middle sits nearer the fingers than the chord does, which is
    how a heart line curving up towards the fingers reads.
    """
    if len(path_norm) < 3:
        return 0.0
    start = np.array(path_norm[0])
    end = np.array(path_norm[-1])
    chord = end - start
    span = float(np.linalg.norm(chord))
    if span < 1e-6:
        return 0.0
    normal = np.array([-chord[1], chord[0]]) / span
    offsets = [float(np.dot(np.array(p) - start, normal)) for p in path_norm]
    return float(np.mean(offsets) / span)


def _path_length(path_norm: list[tuple[float, float]]) -> float:
    if len(path_norm) < 2:
        return 0.0
    total = 0.0
    for (x1, y1), (x2, y2) in zip(path_norm, path_norm[1:]):
        total += float(np.hypot(x2 - x1, y2 - y1))
    return total


def _termination_zone(point: tuple[float, float], knuckles: dict[str, tuple[float, float]]) -> str:
    """Which finger a crease ends under, in the classical naming.

    This is what the client's heart-line rules turn on: whether the line stops
    below Saturn, reaches the lower Jupiter mount, or runs to the top of it.
    """
    x, y = point
    nearest = min(knuckles.items(), key=lambda kv: abs(kv[1][0] - x))
    finger = nearest[0]
    classical = L.FINGER_CLASSICAL[finger]
    # y is 0 at the knuckle row and 1 at the wrist, so a small y means the crease
    # climbed high onto the mount.
    height = "upper" if y < 0.22 else "lower" if y < 0.38 else "below"
    return f"{height} {classical}"


def trace_creases(
    palm: CanonicalPalm, config: PalmScanConfig = DEFAULT_CONFIG
) -> dict[str, TracedCrease]:
    """Trace the four principal creases in the canonical frame.

    Each is searched only in the band it anatomically occupies, which is what lets
    one path be told from another. The bands overlap, because real hands vary.
    """
    size = palm.size
    response = palm.response
    results: dict[str, TracedCrease] = {}

    def finish(
        name: CreaseName,
        path_px: list[tuple[int, int]],
        band: tuple[int, int, int, int],
        extra_notes: list[str] | None = None,
    ) -> TracedCrease:
        notes = list(extra_notes or [])
        if not path_px:
            return TracedCrease(name=name, found=False, notes=notes + ["No path could be traced."])

        strength, continuity, contrast = _score_path(response, path_px, band, config)
        path_norm = [(x / size, y / size) for x, y in path_px]
        found = (
            contrast >= config.min_contrast_ratio
            and strength >= config.min_line_response
            and continuity >= config.min_line_continuity
        )
        if not found:
            notes.append(
                "Traced, but the crease did not register strongly enough to report. "
                "This usually means lighting or focus rather than an absent line."
            )
        return TracedCrease(
            name=name,
            found=found,
            path=path_norm if found else [],
            strength=strength,
            continuity=continuity,
            contrast=contrast,
            length=_path_length(path_norm),
            curvature=_curvature(path_norm),
            start=path_norm[0] if found else None,
            end=path_norm[-1] if found else None,
            termination_zone=(
                _termination_zone(path_norm[0], palm.knuckles_canonical) if found else None
            ),
            notes=notes,
        )

    # --- heart (water) line: upper palm, running across below the knuckles ----
    heart_band = (int(0.08 * size), int(0.36 * size), int(0.10 * size), int(0.95 * size))
    heart_path, _ = _trace_horizontal(
        response, heart_band[0], heart_band[1], heart_band[2], heart_band[3], config
    )
    results["heart"] = finish("heart", heart_path, heart_band)

    # --- head (air) line: mid palm, across, starting near the thumb-index gap -
    head_band = (int(0.34 * size), int(0.60 * size), int(0.08 * size), int(0.92 * size))
    head_path, _ = _trace_horizontal(
        response, head_band[0], head_band[1], head_band[2], head_band[3], config
    )
    results["head"] = finish("head", head_path, head_band)

    # --- life (earth) line: arcs around the ball of the thumb ----------------
    # Traced vertically on the radial side, because the arc is closer to vertical
    # than horizontal over most of its run.
    life_band = (int(0.28 * size), int(0.98 * size), int(0.06 * size), int(0.52 * size))
    life_path, _ = _trace_vertical(
        response, life_band[2], life_band[3], life_band[0], life_band[1], config
    )
    results["life"] = finish("life", life_path, life_band)

    # --- fate (fire) line: vertical, wrist towards the middle finger ----------
    fate_band = (int(0.20 * size), int(0.98 * size), int(0.34 * size), int(0.70 * size))
    fate_path, _ = _trace_vertical(
        response, fate_band[2], fate_band[3], fate_band[0], fate_band[1], config
    )
    results["fate"] = finish(
        "fate",
        fate_path,
        fate_band,
        ["The fate line is absent in many hands; not finding one is a normal result."],
    )

    return results


def crease_relationships(creases: dict[str, TracedCrease], size: int) -> dict[str, Any]:
    """Measurements that depend on two creases at once.

    The client's documents lean on these: the gap between the heart and head lines
    is read as the balance between feeling and reasoning, and whether the heart
    line sits high or low decides which of the two dominates.
    """
    out: dict[str, Any] = {}
    heart = creases.get("heart")
    head = creases.get("head")

    if heart and head and heart.found and head.found:
        # Compare the two at the columns where both exist.
        heart_by_x = {round(x, 2): y for x, y in heart.path}
        head_by_x = {round(x, 2): y for x, y in head.path}
        shared = sorted(set(heart_by_x) & set(head_by_x))
        if shared:
            gaps = [head_by_x[x] - heart_by_x[x] for x in shared]
            out["heart_head_gap"] = round(float(np.mean(gaps)), 4)
            out["heart_head_gap_min"] = round(float(np.min(gaps)), 4)
            out["heart_head_gap_max"] = round(float(np.max(gaps)), 4)

    if heart and heart.found:
        # Height of the heart line above the wrist, 0 at the knuckles.
        out["heart_height"] = round(float(np.mean([y for _x, y in heart.path])), 4)

    if head and head.found:
        out["head_height"] = round(float(np.mean([y for _x, y in head.path])), 4)

    life = creases.get("life")
    if life and life.found:
        # How far the arc reaches across the palm, which is the basis of the
        # client's numbered earth-line cases.
        out["life_reach"] = round(float(max(x for x, _y in life.path)), 4)
        out["life_descent"] = round(float(max(y for _x, y in life.path)), 4)

    return out
