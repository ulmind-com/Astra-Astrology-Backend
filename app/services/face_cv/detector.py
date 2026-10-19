"""Thread-safe singleton manager for MediaPipe Tasks Face Landmarker."""

import threading
from dataclasses import dataclass
from pathlib import Path
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

from app.services.face_cv.config import FaceScanConfig, DEFAULT_CONFIG


@dataclass
class DetectionResult:
    face_count: int
    landmarks_norm: list[tuple[float, float, float]] | None  # Normalized (x, y, z) [0.0 - 1.0]
    landmarks_px: list[tuple[float, float, float]] | None    # Pixel coordinates (x, y, z)
    transformation_matrix: np.ndarray | None                 # 4x4 facial transformation matrix if available


class FaceLandmarkerManager:
    """Thread-safe singleton for reusable MediaPipe Tasks FaceLandmarker."""

    _instance: "FaceLandmarkerManager | None" = None
    _lock = threading.Lock()

    def __init__(self, config: FaceScanConfig = DEFAULT_CONFIG):
        self.config = config
        self._landmarker: vision.FaceLandmarker | None = None
        self._init_lock = threading.Lock()
        self._initialize()

    @classmethod
    def get_instance(cls, config: FaceScanConfig = DEFAULT_CONFIG) -> "FaceLandmarkerManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = FaceLandmarkerManager(config)
            return cls._instance

    def _initialize(self) -> None:
        with self._init_lock:
            if self._landmarker is not None:
                return

            model_path = Path(self.config.model_path)
            if not model_path.exists():
                raise FileNotFoundError(
                    f"MediaPipe Face Landmarker model not found at {model_path}. "
                    "Ensure app/assets/face_landmarker.task is downloaded."
                )

            base_options = python.BaseOptions(
                model_asset_path=str(model_path),
                delegate=python.BaseOptions.Delegate.CPU,
            )

            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=self.config.min_detection_confidence,
                min_face_presence_confidence=self.config.min_presence_confidence,
                min_tracking_confidence=self.config.min_tracking_confidence,
                output_facial_transformation_matrixes=True,
            )
            self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def detect(self, img_rgb: np.ndarray) -> DetectionResult:
        """Runs face landmarker on an RGB uint8 NumPy image."""
        if self._landmarker is None:
            self._initialize()
            if self._landmarker is None:
                raise RuntimeError("FaceLandmarker failed to initialize.")

        h, w, _ = img_rgb.shape
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

        with self._init_lock:
            result = self._landmarker.detect(mp_image)

        face_landmarks_list = result.face_landmarks
        if not face_landmarks_list:
            return DetectionResult(face_count=0, landmarks_norm=None, landmarks_px=None, transformation_matrix=None)

        face_count = len(face_landmarks_list)
        first_face = face_landmarks_list[0]

        landmarks_norm: list[tuple[float, float, float]] = []
        landmarks_px: list[tuple[float, float, float]] = []

        for lm in first_face:
            # Normalized coordinates
            nx, ny, nz = float(lm.x), float(lm.y), float(lm.z)
            landmarks_norm.append((nx, ny, nz))
            # Image pixel coordinates
            px = nx * float(w)
            py = ny * float(h)
            pz = nz * float(w)  # MediaPipe defines z scaled roughly with width
            landmarks_px.append((px, py, pz))

        transform_mat = None
        if result.facial_transformation_matrixes and len(result.facial_transformation_matrixes) > 0:
            transform_mat = np.array(result.facial_transformation_matrixes[0], dtype=np.float64)

        return DetectionResult(
            face_count=face_count,
            landmarks_norm=landmarks_norm,
            landmarks_px=landmarks_px,
            transformation_matrix=transform_mat,
        )

    def close(self) -> None:
        """Closes landmarker and frees resources."""
        with self._init_lock:
            if self._landmarker is not None:
                self._landmarker.close()
                self._landmarker = None


def get_landmarker(config: FaceScanConfig = DEFAULT_CONFIG) -> FaceLandmarkerManager:
    """Retrieves the singleton FaceLandmarkerManager."""
    return FaceLandmarkerManager.get_instance(config)
