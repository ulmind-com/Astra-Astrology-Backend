"""Configuration for MediaPipe Hand Landmarker and OpenCV Palm Scanner."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PalmScanConfig:
    # Model configuration
    model_path: str = str(
        Path(__file__).resolve().parent.parent.parent / "assets" / "hand_landmarker.task"
    )
    min_detection_confidence: float = 0.5
    min_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5

    # Image constraints
    min_image_width: int = 240
    min_image_height: int = 240
    max_file_size_bytes: int = 15 * 1024 * 1024  # 15 MB

    # Quality thresholds
    min_laplacian_sharpness: float = 40.0
    min_brightness_mean: float = 35.0
    max_brightness_mean: float = 230.0
    min_contrast_std: float = 20.0
    min_hand_coverage_ratio: float = 0.12
    max_hand_coverage_ratio: float = 0.95


DEFAULT_CONFIG = PalmScanConfig()
