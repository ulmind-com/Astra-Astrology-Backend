"""Configuration parameters and thresholds for the MediaPipe + OpenCV facial scanning pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FaceScanConfig:
    """Configurable thresholds for face scanning and quality checks."""

    # Model configuration
    model_path: Path = Path(__file__).resolve().parent.parent.parent / "assets" / "face_landmarker.task"
    min_detection_confidence: float = 0.5
    min_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5

    # Input image constraints
    max_file_size_bytes: int = 15 * 1024 * 1024  # 15 MB
    min_image_width: int = 256
    min_image_height: int = 256
    max_image_dimension: int = 4096

    # Quality check thresholds
    # Laplacian variance for blur/sharpness
    min_sharpness_acceptable: float = 15.0       # below this: REJECTED (severe motion blur or out of focus)
    min_sharpness_recommended: float = 45.0      # below this: RETAKE_RECOMMENDED (soft focus advisory)

    # Exposure / brightness (mean grayscale value 0-255)
    min_brightness_acceptable: float = 25.0      # below this: underexposed (too dark)
    max_brightness_acceptable: float = 238.0     # above this: overexposed (washed out)
    overexposure_pixel_threshold: int = 250
    max_overexposed_pixel_ratio: float = 0.35    # >35% near-white pixels rejected

    # Lighting uniformity across face (left-to-right luminance ratio)
    min_lighting_symmetry: float = 0.25         # harsh shadow on one side (advisory)
    max_lighting_symmetry: float = 4.0

    # Face framing / coverage
    min_face_coverage_ratio: float = 0.02        # face bbox area / image area
    recommended_face_coverage: float = 0.06

    # Head pose angles (degrees)
    max_yaw_acceptable_deg: float = 28.0        # turned to side
    max_pitch_acceptable_deg: float = 30.0      # tilted up/down (selfie camera perspective)
    max_roll_acceptable_deg: float = 25.0       # tilted side-to-side

    # Retake recommended pose thresholds
    recommended_yaw_deg: float = 16.0
    recommended_pitch_deg: float = 18.0
    recommended_roll_deg: float = 14.0


    # Landmark mapping version
    landmark_mapping_version: str = "canonical_478_v1"
    model_version: str = "mediapipe_tasks_vision_1.1.1"


DEFAULT_CONFIG = FaceScanConfig()
