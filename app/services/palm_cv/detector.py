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
    #: Real-world metric 3D coordinates (x, y, z) in meters from MediaPipe world landmarks.
    landmarks_world: list[tuple[float, float, float]] | None = None


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
            # Multi-pass sub-region detection:
            # 1. Skin-tone saliency segmentation to locate hand bounding boxes dynamically
            # 2. Quadrant fallbacks for typical camera/selfie compositions
            candidate_boxes: list[tuple[float, float, float, float]] = []

            try:
                ycrcb = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2YCrCb)
                skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
                k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
                skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, k)
                cnts, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for c in cnts:
                    area = cv2.contourArea(c)
                    if area > (height * width * 0.03):
                        bx, by, bw, bh = cv2.boundingRect(c)
                        pad_x = int(bw * 0.16)
                        pad_y = int(bh * 0.16)
                        x0 = max(0, bx - pad_x)
                        y0 = max(0, by - pad_y)
                        x1 = min(width, bx + bw + pad_x)
                        y1 = min(height, by + bh + pad_y)
                        candidate_boxes.append((y0 / height, y1 / height, x0 / width, x1 / width))
            except Exception:
                pass

            # Standard fallback quadrants
            candidate_boxes.extend([
                (0.0, 0.95, 0.30, 1.0),   # Right half
                (0.0, 0.95, 0.0, 0.70),   # Left half
                (0.05, 0.90, 0.15, 0.85), # Center
            ])

            for y0_f, y1_f, x0_f, x1_f in candidate_boxes:
                x0 = int(round(x0_f * width))
                x1 = int(round(x1_f * width))
                y0 = int(round(y0_f * height))
                y1 = int(round(y1_f * height))
                cw = x1 - x0
                ch = y1 - y0
                if cw < 100 or ch < 100:
                    continue

                crop = image_rgb[y0:y1, x0:x1]
                max_d = max(cw, ch)
                square = np.zeros((max_d, max_d, 3), dtype=np.uint8)
                square[:ch, :cw] = crop

                mp_sub = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(square))
                sub_res = self._landmarker.detect(mp_sub)
                if sub_res.hand_landmarks:
                    sub_pts = sub_res.hand_landmarks[0]
                    # Verify detected hand is actually inside the crop, not the zero-padded margin
                    valid_pts = 0
                    norm = []
                    px = []
                    for p in sub_pts:
                        pt_x_crop = p.x * max_d
                        pt_y_crop = p.y * max_d
                        if 0 <= pt_x_crop <= cw + 5 and 0 <= pt_y_crop <= ch + 5:
                            valid_pts += 1
                        g_px_x = x0 + pt_x_crop
                        g_px_y = y0 + pt_y_crop
                        g_norm_x = np.clip(g_px_x / width, 0.0, 1.0)
                        g_norm_y = np.clip(g_px_y / height, 0.0, 1.0)
                        g_norm_z = p.z * (max_d / width)
                        norm.append((float(g_norm_x), float(g_norm_y), float(g_norm_z)))
                        px.append((float(g_px_x), float(g_px_y), float(g_norm_z * width)))

                    if valid_pts < 15:
                        continue

                    world = None
                    if sub_res.hand_world_landmarks and sub_res.hand_world_landmarks[0]:
                        world = [(p.x, p.y, p.z) for p in sub_res.hand_world_landmarks[0]]

                    handedness = None
                    confidence = 0.0
                    if sub_res.handedness and sub_res.handedness[0]:
                        top = sub_res.handedness[0][0]
                        handedness = top.category_name
                        confidence = float(top.score)

                    return HandDetection(
                        hand_count=len(sub_res.hand_landmarks),
                        landmarks_norm=norm,
                        landmarks_px=px,
                        handedness=handedness,
                        handedness_confidence=confidence,
                        landmarks_world=world,
                    )

            return HandDetection(0, None, None, None, 0.0)

        points = result.hand_landmarks[0]
        norm = [(p.x, p.y, p.z) for p in points]
        px = [(p.x * width, p.y * height, p.z * width) for p in points]

        world = None
        if result.hand_world_landmarks and result.hand_world_landmarks[0]:
            world = [(p.x, p.y, p.z) for p in result.hand_world_landmarks[0]]

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
            landmarks_world=world,
        )


def get_landmarker(config: PalmScanConfig = DEFAULT_CONFIG) -> HandLandmarkerManager:
    return HandLandmarkerManager.get_instance(config)
