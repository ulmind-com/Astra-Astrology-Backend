"""Thread-safe singleton manager for MediaPipe Tasks Hand Landmarker."""

import threading
from dataclasses import dataclass
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

from app.services.palm_cv.config import DEFAULT_CONFIG, PalmScanConfig


@dataclass
class HandDetectionResult:
    hand_count: int
    detected_hand: str | None  # "Left" or "Right"
    handedness_confidence: float  # [0.0 - 1.0]
    landmarks_norm: list[tuple[float, float, float]] | None  # Normalized (x, y, z)
    landmarks_px: list[tuple[float, float, float]] | None    # Pixel (x, y, z)


class HandLandmarkerManager:
    """Thread-safe singleton for reusable MediaPipe Tasks HandLandmarker."""

    _instance: "HandLandmarkerManager | None" = None
    _lock = threading.Lock()

    def __init__(self, config: PalmScanConfig = DEFAULT_CONFIG):
        self.config = config
        self._landmarker: vision.HandLandmarker | None = None
        self._init_lock = threading.Lock()
        self._initialize()

    @classmethod
    def get_instance(cls, config: PalmScanConfig = DEFAULT_CONFIG) -> "HandLandmarkerManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = HandLandmarkerManager(config)
            return cls._instance

    def _initialize(self) -> None:
        with self._init_lock:
            if self._landmarker is not None:
                return

            model_path = Path(self.config.model_path)
            if not model_path.exists():
                raise FileNotFoundError(
                    f"MediaPipe Hand Landmarker model not found at {model_path}. "
                    "Ensure app/assets/hand_landmarker.task is present."
                )

            base_options = python.BaseOptions(
                model_asset_path=str(model_path),
                delegate=python.BaseOptions.Delegate.CPU,
            )

            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_hands=1,
                min_hand_detection_confidence=self.config.min_detection_confidence,
                min_hand_presence_confidence=self.config.min_presence_confidence,
                min_tracking_confidence=self.config.min_tracking_confidence,
            )
            self._landmarker = vision.HandLandmarker.create_from_options(options)

    def detect(self, img_rgb: np.ndarray) -> HandDetectionResult:
        """Runs hand landmarker on an RGB uint8 NumPy image."""
        if self._landmarker is None:
            self._initialize()
            if self._landmarker is None:
                raise RuntimeError("HandLandmarker failed to initialize.")

        h, w, _ = img_rgb.shape
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

        with self._init_lock:
            result = self._landmarker.detect(mp_image)

        hands_list = result.hand_landmarks
        if not hands_list:
            return HandDetectionResult(
                hand_count=0,
                detected_hand=None,
                handedness_confidence=0.0,
                landmarks_norm=None,
                landmarks_px=None,
            )

        hand_count = len(hands_list)
        first_hand = hands_list[0]

        # Extract handedness ('Left' or 'Right')
        detected_hand: str | None = None
        handedness_conf: float = 0.0
        if result.handedness and len(result.handedness) > 0 and len(result.handedness[0]) > 0:
            category = result.handedness[0][0]
            detected_hand = category.category_name
            handedness_conf = float(category.score)

        landmarks_norm: list[tuple[float, float, float]] = []
        landmarks_px: list[tuple[float, float, float]] = []

        for lm in first_hand:
            nx, ny, nz = float(lm.x), float(lm.y), float(lm.z)
            landmarks_norm.append((nx, ny, nz))
            px = nx * float(w)
            py = ny * float(h)
            pz = nz * float(w)
            landmarks_px.append((px, py, pz))

        return HandDetectionResult(
            hand_count=hand_count,
            detected_hand=detected_hand,
            handedness_confidence=handedness_conf,
            landmarks_norm=landmarks_norm,
            landmarks_px=landmarks_px,
        )

    def close(self) -> None:
        """Closes landmarker and frees resources."""
        with self._init_lock:
            if self._landmarker is not None:
                self._landmarker.close()
                self._landmarker = None


def get_hand_landmarker(config: PalmScanConfig = DEFAULT_CONFIG) -> HandLandmarkerManager:
    """Retrieves the singleton HandLandmarkerManager."""
    return HandLandmarkerManager.get_instance(config)
