"""Thread-safe singleton for the MediaPipe Tasks Hand Landmarker.

The model is 7.8 MB and takes a noticeable moment to load, so it is built once and
shared. Loading is guarded because FastAPI serves requests concurrently and two
threads racing to build the same landmarker would waste memory at best.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

import mediapipe as mp
import numpy as np
from loguru import logger
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from app.services.palm_cv.config import DEFAULT_CONFIG, PalmScanConfig


@dataclass
class HandDetection:
    hand_count: int
    #: Normalised (x, y, z) in 0..1, as MediaPipe returns them.
    landmarks_norm: list[tuple[float, float, float]] | None
    #: The same points in pixel coordinates of the image that was passed in.
    landmarks_px: list[tuple[float, float, float]] | None
    #: "Left" or "Right", as seen by the camera.
    handedness: str | None
    handedness_confidence: float


class HandLandmarkerManager:
    """One landmarker, built lazily and reused."""

    _instance: "HandLandmarkerManager | None" = None
    _lock = threading.Lock()

    def __init__(self, config: PalmScanConfig = DEFAULT_CONFIG):
        self.config = config
        self._landmarker: vision.HandLandmarker | None = None
        self._init_lock = threading.Lock()
        self._load_error: str | None = None
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
            try:
                if not self.config.model_path.exists():
                    raise FileNotFoundError(
                        f"hand landmarker model missing at {self.config.model_path}"
                    )
                base = mp_python.BaseOptions(model_asset_path=str(self.config.model_path))
                options = vision.HandLandmarkerOptions(
                    base_options=base,
                    running_mode=vision.RunningMode.IMAGE,
                    num_hands=self.config.max_hands,
                    min_hand_detection_confidence=self.config.min_hand_detection_confidence,
                    min_hand_presence_confidence=self.config.min_hand_presence_confidence,
                    min_tracking_confidence=self.config.min_tracking_confidence,
                )
                self._landmarker = vision.HandLandmarker.create_from_options(options)
                logger.info("Hand landmarker ready")
            except Exception as exc:
                # A missing or unreadable model must surface as a clean service
                # error at request time, not as a crash during import.
                self._load_error = str(exc)
                logger.error(f"Hand landmarker failed to load: {exc}")

    @property
    def is_ready(self) -> bool:
        return self._landmarker is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def detect(self, image_rgb: np.ndarray) -> HandDetection:
        """Locate one hand and return its 21 landmarks."""
        if self._landmarker is None:
            raise RuntimeError(
                f"Hand landmarker is not available: {self._load_error or 'unknown error'}"
            )

        height, width = image_rgb.shape[:2]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image_rgb))
        result = self._landmarker.detect(mp_image)

        if not result.hand_landmarks:
            return HandDetection(0, None, None, None, 0.0)

        points = result.hand_landmarks[0]
        norm = [(p.x, p.y, p.z) for p in points]
        px = [(p.x * width, p.y * height, p.z * width) for p in points]

        handedness = None
        confidence = 0.0
        if result.handedness and result.handedness[0]:
            top = result.handedness[0][0]
            handedness = top.category_name
            confidence = float(top.score)

        return HandDetection(
            hand_count=len(result.hand_landmarks),
            landmarks_norm=norm,
            landmarks_px=px,
            handedness=handedness,
            handedness_confidence=confidence,
        )


def get_landmarker(config: PalmScanConfig = DEFAULT_CONFIG) -> HandLandmarkerManager:
    return HandLandmarkerManager.get_instance(config)
