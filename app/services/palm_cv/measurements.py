"""Hand geometry measured from the 21 landmarks.

These are the measurements the client's own documents turn on. `Fingers in general
and Thumb` and `Jupiter finger` are almost entirely about proportion - long against
short fingers, thick against thin, which phalange dominates, how far the thumb
opens, whether the index is longer or shorter than the ring - and every one of
those is a ratio between joints MediaPipe already gives us.

Unlike the crease work, nothing here depends on image contrast. A landmark is a
landmark whether the photo is crisp or soft, so these are the numbers the reading
can lean on hardest.

Every value is a ratio, never a pixel count, so a hand photographed close up and
the same hand at arm's length measure the same.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.services.palm_cv import landmarks as L


@dataclass
class Measurement:
    """One measured ratio, with everything needed to audit it."""

    key: str
    value: float
    #: What the number is, in plain words, so a reading can explain itself.
    description: str
    #: The landmark indices it was computed from.
    sources: tuple[int, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": round(self.value, 4),
            "description": self.description,
            "sources": list(self.sources),
        }


@dataclass
class HandMeasurements:
    values: dict[str, float] = field(default_factory=dict)
    details: dict[str, Measurement] = field(default_factory=dict)

    def add(self, key: str, value: float, description: str, sources: tuple[int, ...] = ()) -> None:
        clean = float(value) if np.isfinite(value) else 0.0
        self.values[key] = clean
        self.details[key] = Measurement(key, clean, description, sources)

    def as_dict(self) -> dict[str, Any]:
        return {
            "values": {k: round(v, 4) for k, v in self.values.items()},
            "details": {k: m.as_dict() for k, m in self.details.items()},
        }


def _point(landmarks: list[tuple[float, float, float]], index: int) -> np.ndarray:
    return np.array(landmarks[index][:2], dtype=np.float64)


def _distance(landmarks: list[tuple[float, float, float]], a: int, b: int) -> float:
    return float(np.linalg.norm(_point(landmarks, a) - _point(landmarks, b)))


def _chain_length(landmarks: list[tuple[float, float, float]], chain: tuple[int, ...]) -> float:
    """Length along a finger, joint to joint, rather than base to tip.

    A bent finger measured base to tip reads short; measured along the chain it
    reads its true length, which is what the client's long/short rules mean.
    """
    return sum(_distance(landmarks, a, b) for a, b in zip(chain, chain[1:]))


def _angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    n1, n2 = float(np.linalg.norm(v1)), float(np.linalg.norm(v2))
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    cosine = float(np.dot(v1, v2) / (n1 * n2))
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def extract(landmarks_px: list[tuple[float, float, float]]) -> HandMeasurements:
    """Every ratio the rule set needs, from one set of landmarks."""
    m = HandMeasurements()
    lm = landmarks_px

    wrist = _point(lm, L.WRIST)
    index_mcp = _point(lm, L.INDEX_MCP)
    middle_mcp = _point(lm, L.MIDDLE_MCP)
    pinky_mcp = _point(lm, L.PINKY_MCP)

    # --- the palm itself -----------------------------------------------------
    palm_length = float(np.linalg.norm(middle_mcp - wrist))
    palm_width = float(np.linalg.norm(pinky_mcp - index_mcp))
    if palm_length < 1e-6:
        palm_length = 1.0
    if palm_width < 1e-6:
        palm_width = 1.0

    m.add(
        "palm_aspect",
        palm_width / palm_length,
        "Palm width against palm length. Near 1 is a square palm, below it a long one.",
        (L.WRIST, L.MIDDLE_MCP, L.INDEX_MCP, L.PINKY_MCP),
    )

    # --- finger lengths ------------------------------------------------------
    finger_lengths: dict[str, float] = {}
    for name, chain in L.FINGER_CHAINS.items():
        length = _chain_length(lm, chain)
        finger_lengths[name] = length
        m.add(
            f"{name}_length_ratio",
            length / palm_length,
            f"Length of the {L.FINGER_CLASSICAL[name]} finger against palm length.",
            chain,
        )

    middle_length = finger_lengths["middle"] or 1.0

    # The client's central hand-type rule: fingers measured against the palm.
    m.add(
        "finger_palm_ratio",
        middle_length / palm_length,
        "The longest finger against palm length. This is what separates the "
        "elemental hand types, and what the rule 'longer palm than fingers' turns on.",
        (L.WRIST, L.MIDDLE_MCP, L.MIDDLE_TIP),
    )

    # --- digit ratio ---------------------------------------------------------
    # Index against ring. The client's Jupiter-finger document reads this directly.
    m.add(
        "index_ring_ratio",
        finger_lengths["index"] / (finger_lengths["ring"] or 1.0),
        "The Jupiter (index) finger against the Sun (ring) finger. Below 1 means "
        "the Sun finger is the longer of the two.",
        (L.INDEX_MCP, L.INDEX_TIP, L.RING_MCP, L.RING_TIP),
    )

    # --- phalanges -----------------------------------------------------------
    # "First, second, third phalange" in the client's documents, counted from the
    # tip. Each is given as a share of its own finger so the three sum to 1.
    for name, (mcp, pip, dip, tip) in L.FINGER_CHAINS.items():
        total = _chain_length(lm, (mcp, pip, dip, tip)) or 1.0
        classical = L.FINGER_CLASSICAL[name]
        m.add(
            f"{name}_phalange_first",
            _distance(lm, dip, tip) / total,
            f"Top phalange of the {classical} finger as a share of that finger. "
            "The client's documents tie this to the spiritual and intellectual side.",
            (dip, tip),
        )
        m.add(
            f"{name}_phalange_second",
            _distance(lm, pip, dip) / total,
            f"Middle phalange of the {classical} finger as a share of that finger. "
            "Tied to processing and execution.",
            (pip, dip),
        )
        m.add(
            f"{name}_phalange_third",
            _distance(lm, mcp, pip) / total,
            f"Base phalange of the {classical} finger as a share of that finger. "
            "Tied to the physical and material side.",
            (mcp, pip),
        )

    # --- thumb ---------------------------------------------------------------
    thumb_length = _chain_length(lm, L.THUMB_CHAIN)
    m.add(
        "thumb_length_ratio",
        thumb_length / palm_length,
        "Thumb length against palm length. The client's small, middle and long "
        "thumb cases are read from this.",
        L.THUMB_CHAIN,
    )

    lower_flange = _distance(lm, L.THUMB_CMC, L.THUMB_MCP)
    upper_flange = _distance(lm, L.THUMB_MCP, L.THUMB_IP) + _distance(lm, L.THUMB_IP, L.THUMB_TIP)
    m.add(
        "thumb_flange_ratio",
        upper_flange / (lower_flange or 1.0),
        "Upper thumb flange against lower. The client reads the upper as will and "
        "the lower as logic, so this is the balance between them.",
        (L.THUMB_CMC, L.THUMB_MCP, L.THUMB_TIP),
    )

    # The opening between thumb and index: "gap is more, outspoken and generous".
    thumb_gap = _angle_between(
        _point(lm, L.THUMB_TIP) - _point(lm, L.THUMB_CMC),
        _point(lm, L.INDEX_TIP) - index_mcp,
    )
    m.add(
        "thumb_index_angle",
        thumb_gap,
        "Angle between thumb and index finger, in degrees. The client reads a wide "
        "opening as outspoken and generous, a narrow one as reserved.",
        (L.THUMB_CMC, L.THUMB_TIP, L.INDEX_MCP, L.INDEX_TIP),
    )

    # --- finger spread -------------------------------------------------------
    # "Spread fingers are bold"; "closed together, caution and inhibition".
    spreads: list[float] = []
    chain_items = list(L.FINGER_CHAINS.items())
    for (name_a, chain_a), (name_b, chain_b) in zip(chain_items, chain_items[1:]):
        spreads.append(
            _angle_between(
                _point(lm, chain_a[3]) - _point(lm, chain_a[0]),
                _point(lm, chain_b[3]) - _point(lm, chain_b[0]),
            )
        )
    m.add(
        "finger_spread",
        float(np.mean(spreads)) if spreads else 0.0,
        "Average angle between neighbouring fingers, in degrees.",
        tuple(c[3] for c in L.FINGER_CHAINS.values()),
    )

    # --- finger lean ---------------------------------------------------------
    # "All fingers towards thumb" against "all fingers away from thumb", and the
    # Jupiter finger's own bend, which the client reads separately.
    palm_axis = middle_mcp - wrist
    thumb_side = _point(lm, L.THUMB_CMC) - wrist
    # Positive when the fingers lean the same way the thumb lies.
    leans: list[float] = []
    for chain in L.FINGER_CHAINS.values():
        direction = _point(lm, chain[3]) - _point(lm, chain[0])
        cross_axis = float(np.cross(palm_axis, direction))
        cross_thumb = float(np.cross(palm_axis, thumb_side))
        leans.append(np.sign(cross_thumb) * cross_axis / (np.linalg.norm(palm_axis) ** 2 or 1.0))
    m.add(
        "finger_lean_to_thumb",
        float(np.mean(leans)) if leans else 0.0,
        "How far the fingers lean towards the thumb side. Positive is towards the "
        "thumb, negative away from it.",
        tuple(c[3] for c in L.FINGER_CHAINS.values()),
    )

    index_direction = _point(lm, L.INDEX_TIP) - index_mcp
    middle_direction = _point(lm, L.MIDDLE_TIP) - middle_mcp
    m.add(
        "jupiter_bend",
        _angle_between(index_direction, middle_direction),
        "How far the Jupiter finger leans away from the Saturn finger, in degrees. "
        "The client reads a lean towards the thumb as a desire to lead.",
        (L.INDEX_MCP, L.INDEX_TIP, L.MIDDLE_MCP, L.MIDDLE_TIP),
    )

    # --- finger thickness ----------------------------------------------------
    # "Thick fingers, field work; thin fingers, office work." Width is estimated
    # from the knuckle spacing, which is the only width the landmarks expose.
    knuckle_spacings = [
        _distance(lm, L.INDEX_MCP, L.MIDDLE_MCP),
        _distance(lm, L.MIDDLE_MCP, L.RING_MCP),
        _distance(lm, L.RING_MCP, L.PINKY_MCP),
    ]
    m.add(
        "finger_thickness",
        float(np.mean(knuckle_spacings)) / middle_length,
        "Knuckle spacing against finger length, standing in for how thick the "
        "fingers are. Landmarks give no outline, so this is an estimate from the "
        "skeleton rather than a measured width.",
        L.KNUCKLES,
    )

    # --- Mercury (pinky) finger: communication, business acumen, eloquence ---
    pinky_length = finger_lengths.get("pinky") or 1.0
    ring_length = finger_lengths.get("ring") or 1.0
    m.add(
        "mercury_reach_ratio",
        pinky_length / ring_length,
        "Mercury finger length compared to Sun (ring) finger. Reaching the top "
        "joint indicates eloquence, business acumen, and public communication.",
        (L.PINKY_MCP, L.PINKY_TIP, L.RING_MCP, L.RING_TIP),
    )

    m.add(
        "is_square_palm",
        1.0 if (palm_width / palm_length) >= 0.92 else 0.0,
        "Whether the palm is square (1.0) or elongated (0.0).",
        (L.WRIST, L.MIDDLE_MCP, L.INDEX_MCP, L.PINKY_MCP),
    )

    return m


def hand_type(values: dict[str, float]) -> dict[str, Any]:
    """The four elemental hand types, from palm shape and finger length.

    This is the classification the client's documents lean on most, and it is
    purely proportional:

        Earth  square palm, short fingers
        Air    square palm, long fingers
        Fire   long palm,   short fingers
        Water  long palm,   long fingers
    """
    aspect = values.get("palm_aspect", 1.0)
    fingers = values.get("finger_palm_ratio", 1.0)

    square_palm = aspect >= 0.92
    long_fingers = fingers >= 0.95

    if square_palm and not long_fingers:
        name, reason = "Earth", "a square palm with shorter fingers"
    elif square_palm and long_fingers:
        name, reason = "Air", "a square palm with longer fingers"
    elif not square_palm and not long_fingers:
        name, reason = "Fire", "a longer palm with shorter fingers"
    else:
        name, reason = "Water", "a longer palm with longer fingers"

    # How clearly it falls in its quadrant rather than sitting on a boundary.
    confidence = min(1.0, (abs(aspect - 0.92) / 0.12 + abs(fingers - 0.95) / 0.12) / 2.0)

    return {
        "type": name,
        "reason": reason,
        "palm_aspect": round(aspect, 4),
        "finger_palm_ratio": round(fingers, 4),
        "confidence": round(confidence, 3),
    }


def extract_3d_metrics(
    landmarks_px: list[tuple[float, float, float]],
    landmarks_world: list[tuple[float, float, float]] | None = None,
) -> dict[str, Any]:
    """Compute 3D palm metrics: mount elevations, palm cup depth, finger dorsiflexion and inclinations."""
    if landmarks_world and len(landmarks_world) == 21:
        pts3d = np.array([[p[0] * 1000.0, p[1] * 1000.0, p[2] * 1000.0] for p in landmarks_world], dtype=np.float32)
        unit = "mm"
    else:
        pts3d = np.array(landmarks_px, dtype=np.float32)
        unit = "norm"

    wrist = pts3d[L.WRIST]
    idx_mcp = pts3d[L.INDEX_MCP]
    mid_mcp = pts3d[L.MIDDLE_MCP]
    ring_mcp = pts3d[L.RING_MCP]
    pinky_mcp = pts3d[L.PINKY_MCP]
    thumb_cmc = pts3d[L.THUMB_CMC]
    thumb_mcp = pts3d[L.THUMB_MCP]

    axis = mid_mcp - wrist
    across = pinky_mcp - idx_mcp
    normal = np.cross(across, axis)
    normal_len = float(np.linalg.norm(normal))
    normal = normal / (normal_len + 1e-9)

    palm_center = (wrist + idx_mcp + mid_mcp + ring_mcp + pinky_mcp) / 5.0
    hollow_depth = abs(float(np.dot(palm_center - mid_mcp, normal)))

    mounts = {
        "jupiter_mount_mm": round(float(np.dot(idx_mcp - wrist, normal)), 2),
        "saturn_mount_mm": round(float(np.dot(mid_mcp - wrist, normal)), 2),
        "sun_mount_mm": round(float(np.dot(ring_mcp - wrist, normal)), 2),
        "mercury_mount_mm": round(float(np.dot(pinky_mcp - wrist, normal)), 2),
        "venus_mount_mm": round(float(np.dot(thumb_mcp - wrist, normal)), 2),
        "moon_mount_mm": round(float(np.dot(pinky_mcp * 0.5 + wrist * 0.5 - wrist, normal)), 2),
    }

    mid_tip = pts3d[L.MIDDLE_TIP]
    mid_finger_vec = mid_tip - mid_mcp
    axis_norm = axis / (np.linalg.norm(axis) + 1e-9)
    bend_rad = np.arctan2(np.dot(mid_finger_vec, normal), np.dot(mid_finger_vec, axis_norm))
    dorsiflexion = float(np.degrees(bend_rad))

    mid_vec = pts3d[L.MIDDLE_TIP] - mid_mcp
    ring_vec = pts3d[L.RING_TIP] - ring_mcp
    dot_sr = np.dot(mid_vec, ring_vec) / (np.linalg.norm(mid_vec) * np.linalg.norm(ring_vec) + 1e-9)
    saturn_sun_tilt = float(np.degrees(np.arccos(np.clip(dot_sr, -1.0, 1.0))))

    idx_vec = pts3d[L.INDEX_TIP] - idx_mcp
    th_vec = pts3d[L.THUMB_TIP] - thumb_mcp
    dot_jt = np.dot(idx_vec, th_vec) / (np.linalg.norm(idx_vec) * np.linalg.norm(th_vec) + 1e-9)
    jupiter_thumb_angle = float(np.degrees(np.arccos(np.clip(dot_jt, -1.0, 1.0))))

    is_spontaneous = 1.0 if abs(dorsiflexion) >= 28.0 else 0.0
    is_stiff = 1.0 if abs(dorsiflexion) < 12.0 else 0.0
    thumb_gap_wide = 1.0 if jupiter_thumb_angle >= 50.0 else 0.0
    saturn_leaning_sun = 1.0 if saturn_sun_tilt >= 7.5 else 0.0

    return {
        "hollow_depth_mm": round(hollow_depth, 2),
        "dorsiflexion_deg": round(dorsiflexion, 1),
        "saturn_sun_tilt_deg": round(saturn_sun_tilt, 1),
        "jupiter_thumb_angle_deg": round(jupiter_thumb_angle, 1),
        "is_spontaneous_flexible": is_spontaneous,
        "is_stiff_fingers": is_stiff,
        "thumb_gap_wide": thumb_gap_wide,
        "saturn_leaning_sun": saturn_leaning_sun,
        "mount_elevations": mounts,
        "unit": unit,
    }
