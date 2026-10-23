"""Thresholds for the palm scan.

Every number here is a gate on whether a photo is good enough to read, or a limit
on what the tracing will accept as a line. They are collected in one place because
the honest answer to "how accurate is this" depends almost entirely on them: a
scan that passes these gates is one we are willing to measure, and anything that
fails is sent back rather than guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PalmScanConfig:
    # --- model ---------------------------------------------------------------
    model_path: Path = Path(__file__).resolve().parents[2] / "assets" / "hand_landmarker.task"
    max_hands: int = 1
    min_hand_detection_confidence: float = 0.5
    min_hand_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5

    # --- input limits --------------------------------------------------------
    #: Below this the creases are simply not resolved and tracing becomes guessing.
    min_image_width: int = 480
    min_image_height: int = 480
    #: Guards against a decode bomb and keeps processing time bounded.
    max_image_pixels: int = 40_000_000
    #: Large images are worked at this width; beyond it the extra pixels cost time
    #: without adding crease detail.
    working_width: int = 1280

    # --- quality gates -------------------------------------------------------
    #: Variance of the Laplacian over the palm region. A blurred palm has no
    #: traceable creases at all, so this is the strictest gate.
    min_sharpness: float = 55.0
    #: Mean brightness of the palm region, 0-255.
    min_brightness: float = 45.0
    max_brightness: float = 225.0
    #: Fraction of palm pixels at the very top of the range. A blown-out palm has
    #: lost the creases to glare.
    max_overexposed_ratio: float = 0.18
    #: Palm area as a fraction of the frame. Too small and the creases span too few
    #: pixels to measure.
    min_palm_area_ratio: float = 0.045
    #: The palm must be roughly facing the camera. Measured as how far the knuckle
    #: row and the wrist axis depart from perpendicular.
    max_tilt_degrees: float = 32.0
    #: How much the hand may rotate in-plane before the normalisation stops being
    #: reliable.
    max_roll_degrees: float = 45.0
    #: Fingers must be open enough that the palm is not occluded.
    min_finger_extension: float = 0.55

    # --- normalised palm frame ----------------------------------------------
    #: The palm is warped into a square of this size before any crease work, so
    #: every measurement is in the same units regardless of photo resolution or
    #: how far away the hand was held.
    canonical_size: int = 512

    # --- crease tracing ------------------------------------------------------
    #: Gabor bank: creases are dark valleys a few pixels wide in the canonical frame.
    gabor_kernel_size: int = 21
    gabor_sigma: float = 4.0
    gabor_lambda: float = 9.0
    gabor_gamma: float = 0.5
    gabor_orientations: int = 16
    #: CLAHE, to lift creases out of uneven lighting before filtering.
    clahe_clip_limit: float = 3.0
    clahe_tile_grid: int = 8
    #: A traced path must average at least this much valley response to be called a
    #: line rather than skin texture. This is the gate that makes the difference
    #: between reporting a line and inventing one.
    min_line_response: float = 0.17
    #: And must hold that response over at least this fraction of its length.
    min_line_continuity: float = 0.45
    #: How far a traced path must stand above the median response of the band it
    #: was found in. The search always returns a best path, so this is the test
    #: that separates a crease from the least dark streak in a featureless region:
    #: a straight line through skin texture scores about 1.0.
    min_contrast_ratio: float = 1.6
    #: Smoothness penalty per row of lateral movement in the trace. This has to be
    #: small relative to the response values it competes against: the map is
    #: normalised to 0..1 and real creases sit around 0.1 to 0.4, so a penalty of
    #: the same order makes every optimal path a straight line regardless of what
    #: the creases are doing. Set well below the signal, the path follows the
    #: crease and the penalty only suppresses jitter.
    trace_smoothness: float = 0.10
    #: Steps either side a trace may move per column. Larger follows sharper curves
    #: but also follows noise.
    trace_max_step: int = 3


DEFAULT_CONFIG = PalmScanConfig()
