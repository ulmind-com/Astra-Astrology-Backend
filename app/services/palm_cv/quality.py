"""Whether a photo is good enough to read creases from.

Crease tracing will always return *something*: run it on a blurred photo and it
will happily follow skin texture and report a heart line. The gates here are what
separate a reading from a fabrication, so they are deliberately strict and they
fail loudly with a reason the user can act on.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import cv2
import numpy as np

from app.services.palm_cv.config import DEFAULT_CONFIG, PalmScanConfig
from app.services.palm_cv import landmarks as L


class QualityStatus(str, Enum):
    OK = "ok"
    REJECTED = "rejected"


@dataclass
class QualityCheck:
    name: str
    passed: bool
    value: float
    threshold: float
    message: str


@dataclass
class QualityReport:
    status: QualityStatus
    score: float
    checks: list[QualityCheck] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "score": round(self.score, 3),
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "value": round(c.value, 4),
                    "threshold": round(c.threshold, 4),
                    "message": c.message,
                }
                for c in self.checks
            ],
            "failures": self.failures,
        }


def decode_image(raw: bytes, config: PalmScanConfig = DEFAULT_CONFIG) -> np.ndarray:
    """Decode to RGB with EXIF rotation applied.

    Phone cameras store the sensor image unrotated and record the orientation in
    EXIF. Ignoring it is how a portrait photo arrives sideways, which turns the
    palm's long axis into its short one and quietly ruins every proportion.
    """
    if not raw:
        raise ValueError("No image data was received.")

    try:
        from PIL import Image, ImageOps

        with Image.open(io.BytesIO(raw)) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            if img.width * img.height > config.max_image_pixels:
                raise ValueError("That image is too large to process.")
            array = np.asarray(img)
    except ImportError:
        buffer = np.frombuffer(raw, dtype=np.uint8)
        decoded = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if decoded is None:
            raise ValueError("That file could not be read as an image.")
        array = cv2.cvtColor(decoded, cv2.COLOR_BGR2RGB)
    except Exception as exc:
        raise ValueError("That file could not be read as an image.") from exc

    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("That file could not be read as a colour image.")

    height, width = array.shape[:2]
    if width > config.working_width:
        scale = config.working_width / float(width)
        array = cv2.resize(
            array,
            (config.working_width, max(1, int(round(height * scale)))),
            interpolation=cv2.INTER_AREA,
        )
    return array


def palm_mask(
    image_shape: tuple[int, ...],
    landmarks_px: list[tuple[float, float, float]],
) -> np.ndarray:
    """Filled polygon covering the palm proper, fingers excluded."""
    height, width = image_shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    points = np.array(
        [[int(round(landmarks_px[i][0])), int(round(landmarks_px[i][1]))] for i in L.PALM_BOUNDARY],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(mask, cv2.convexHull(points), 255)
    return mask


def _finger_extension(landmarks_px: list[tuple[float, float, float]], palm_length: float) -> float:
    """How far the fingers are extended, 0 (curled) to about 1 (straight).

    A curled hand hides the upper palm, which is exactly where the heart line is,
    so a scan of a half-closed hand would miss or mistrace it.
    """
    if palm_length <= 0:
        return 0.0
    ratios: list[float] = []
    for mcp, _pip, _dip, tip in L.FINGER_CHAINS.values():
        span = float(
            np.hypot(
                landmarks_px[tip][0] - landmarks_px[mcp][0],
                landmarks_px[tip][1] - landmarks_px[mcp][1],
            )
        )
        ratios.append(span / palm_length)
    return float(np.mean(ratios))


def hand_pose(landmarks_px: list[tuple[float, float, float]]) -> dict[str, float]:
    """In-plane roll and how far the palm is turned away from the camera."""
    wrist = np.array(landmarks_px[L.WRIST][:2])
    index_mcp = np.array(landmarks_px[L.INDEX_MCP][:2])
    pinky_mcp = np.array(landmarks_px[L.PINKY_MCP][:2])
    middle_mcp = np.array(landmarks_px[L.MIDDLE_MCP][:2])

    axis = middle_mcp - wrist
    knuckles = pinky_mcp - index_mcp

    roll = float(np.degrees(np.arctan2(axis[0], -axis[1])))

    # With the palm square to the camera the knuckle row is perpendicular to the
    # wrist axis. Departure from perpendicular means the hand is turned, and the
    # creases are being seen at an angle that shortens them.
    axis_norm = np.linalg.norm(axis)
    knuckle_norm = np.linalg.norm(knuckles)
    if axis_norm < 1e-6 or knuckle_norm < 1e-6:
        tilt = 90.0
    else:
        cosine = float(np.dot(axis, knuckles) / (axis_norm * knuckle_norm))
        tilt = abs(90.0 - float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))))

    # A foreshortened palm also shows up as the knuckle row being short relative to
    # the wrist axis, which catches rotation the angle alone can miss.
    aspect = float(knuckle_norm / axis_norm) if axis_norm > 1e-6 else 0.0

    return {"roll_degrees": roll, "tilt_degrees": tilt, "knuckle_aspect": aspect}


def assess(
    image_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]],
    config: PalmScanConfig = DEFAULT_CONFIG,
) -> QualityReport:
    """Run every gate and report which, if any, the photo failed."""
    checks: list[QualityCheck] = []
    height, width = image_rgb.shape[:2]

    mask = palm_mask(image_rgb.shape, landmarks_px)
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    palm_pixels = gray[mask > 0]

    # --- resolution -------------------------------------------------------
    checks.append(
        QualityCheck(
            "resolution",
            width >= config.min_image_width and height >= config.min_image_height,
            float(min(width, height)),
            float(min(config.min_image_width, config.min_image_height)),
            "The photo is too small for the creases to be resolved. Use a larger image.",
        )
    )

    # --- how much of the frame the palm fills ------------------------------
    area_ratio = float(np.count_nonzero(mask)) / float(max(1, height * width))
    checks.append(
        QualityCheck(
            "palm_size",
            area_ratio >= config.min_palm_area_ratio,
            area_ratio,
            config.min_palm_area_ratio,
            "The hand is too far away. Fill more of the frame with your palm.",
        )
    )

    # --- focus -------------------------------------------------------------
    # Compute Laplacian of the grayscale image first. To avoid boundary jump artifacts
    # between the palm and dark mask borders, evaluate variance across the eroded palm interior.
    if palm_pixels.size > 0:
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        eroded_mask = cv2.erode(mask, kernel)
        palm_lap = lap[eroded_mask > 0] if np.count_nonzero(eroded_mask) > 100 else lap[mask > 0]
        sharpness = float(palm_lap.var()) if palm_lap.size > 0 else 0.0
    else:
        sharpness = 0.0
    checks.append(
        QualityCheck(
            "sharpness",
            sharpness >= config.min_sharpness,
            sharpness,
            config.min_sharpness,
            "The photo is not sharp enough. Hold steady and let the camera focus on your palm.",
        )
    )

    # --- exposure ----------------------------------------------------------
    brightness = float(np.mean(palm_pixels)) if palm_pixels.size else 0.0
    checks.append(
        QualityCheck(
            "brightness",
            config.min_brightness <= brightness <= config.max_brightness,
            brightness,
            config.min_brightness,
            "The lighting is too dark or too bright. Use even, indirect light.",
        )
    )

    overexposed = (
        float(np.count_nonzero(palm_pixels >= 250)) / float(palm_pixels.size)
        if palm_pixels.size
        else 1.0
    )
    checks.append(
        QualityCheck(
            "glare",
            overexposed <= config.max_overexposed_ratio,
            overexposed,
            config.max_overexposed_ratio,
            "There is glare on the palm. Move out of direct light or away from the flash.",
        )
    )

    # --- pose --------------------------------------------------------------
    pose = hand_pose(landmarks_px)
    checks.append(
        QualityCheck(
            "palm_facing",
            pose["tilt_degrees"] <= config.max_tilt_degrees,
            pose["tilt_degrees"],
            config.max_tilt_degrees,
            "The palm is turned away from the camera. Hold it flat and face on.",
        )
    )
    checks.append(
        QualityCheck(
            "rotation",
            abs(pose["roll_degrees"]) <= config.max_roll_degrees,
            abs(pose["roll_degrees"]),
            config.max_roll_degrees,
            "The hand is rotated too far. Point the fingers towards the top of the frame.",
        )
    )

    wrist = np.array(landmarks_px[L.WRIST][:2])
    middle_mcp = np.array(landmarks_px[L.MIDDLE_MCP][:2])
    palm_length = float(np.linalg.norm(middle_mcp - wrist))
    extension = _finger_extension(landmarks_px, palm_length)
    checks.append(
        QualityCheck(
            "fingers_open",
            extension >= config.min_finger_extension,
            extension,
            config.min_finger_extension,
            "Open your fingers. A curled hand hides the upper palm.",
        )
    )

    failures = [c.message for c in checks if not c.passed]
    passed = [c for c in checks if c.passed]
    score = len(passed) / float(len(checks)) if checks else 0.0

    return QualityReport(
        status=QualityStatus.OK if not failures else QualityStatus.REJECTED,
        score=score,
        checks=checks,
        failures=failures,
    )
