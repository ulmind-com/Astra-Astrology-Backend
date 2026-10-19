"""Image quality assessment and head pose estimation using OpenCV and NumPy."""

import io
from dataclasses import dataclass, field
from enum import Enum
import cv2
import numpy as np
from PIL import Image, ImageOps

from app.services.face_cv.config import FaceScanConfig, DEFAULT_CONFIG
from app.services.face_cv.landmarks import (
    CANONICAL_3D_FACE_MODEL,
    HEAD_POSE_LANDMARK_INDICES,
    FACE_OVAL_INDICES,
)


class QualityStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    RETAKE_RECOMMENDED = "RETAKE_RECOMMENDED"
    REJECTED = "REJECTED"


@dataclass
class HeadPose:
    yaw_deg: float      # negative = turned to subject's right, positive = turned to subject's left
    pitch_deg: float    # negative = looking down, positive = looking up
    roll_deg: float     # tilt side-to-side
    is_frontal: bool


@dataclass
class QualityChecks:
    sharpness_score: float
    brightness_mean: float
    overexposed_ratio: float
    lighting_symmetry_ratio: float
    face_coverage_ratio: float
    head_pose: HeadPose | None
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class QualityAssessment:
    status: QualityStatus
    score: float  # 0.0 to 1.0 confidence/quality rating
    checks: QualityChecks
    message: str


def decode_and_correct_orientation(raw_bytes: bytes) -> np.ndarray:
    """Decodes raw image bytes with EXIF orientation correction and returns RGB uint8 image."""
    try:
        # Use PIL to read EXIF orientation safely
        pil_image = Image.open(io.BytesIO(raw_bytes))
        pil_image = ImageOps.exif_transpose(pil_image)
        # Convert to RGB (handles RGBA, Grayscale, CMYK, etc.)
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        return np.array(pil_image, dtype=np.uint8)
    except Exception:
        # Fallback to OpenCV imdecode if PIL fails on uncommon formats
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("The provided file could not be decoded as an image.")
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def calculate_sharpness(gray: np.ndarray) -> float:
    """Computes focus measure using the variance of the Laplacian operator."""
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


def estimate_head_pose(
    landmarks_px: list[tuple[float, float, float]],
    img_w: int,
    img_h: int,
    config: FaceScanConfig = DEFAULT_CONFIG,
) -> HeadPose:

    """Estimates head yaw, pitch, and roll in degrees using cv2.solvePnP."""
    image_points = np.array(
        [[landmarks_px[idx][0], landmarks_px[idx][1]] for idx in HEAD_POSE_LANDMARK_INDICES],
        dtype=np.float64,
    )
    model_points = np.array(CANONICAL_3D_FACE_MODEL, dtype=np.float64)

    # Approximate camera intrinsic matrix (assuming center principal point and focal length ~ img_w)
    focal_length = float(img_w)
    center = (float(img_w) / 2.0, float(img_h) / 2.0)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]],
         [0, focal_length, center[1]],
         [0, 0, 1]],
        dtype=np.float64,
    )
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)  # Assume minimal lens distortion

    success, rotation_vector, translation_vector = cv2.solvePnP(
        model_points,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )

    if not success:
        return HeadPose(yaw_deg=0.0, pitch_deg=0.0, roll_deg=0.0, is_frontal=True)

    # Convert rotation vector to rotation matrix
    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

    # Use OpenCV's RQ decomposition to extract Euler angles in degrees
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rotation_matrix)
    pitch_raw, yaw_raw, roll_raw = float(angles[0]), float(angles[1]), float(angles[2])

    # Face looking towards camera has pitch near ±180 in raw camera frame
    pitch_deg = pitch_raw + 180.0 if pitch_raw < 0 else pitch_raw - 180.0
    yaw_deg = yaw_raw
    roll_deg = roll_raw

    is_frontal = (
        abs(yaw_deg) <= config.max_yaw_acceptable_deg
        and abs(pitch_deg) <= config.max_pitch_acceptable_deg
        and abs(roll_deg) <= config.max_roll_acceptable_deg
    )

    return HeadPose(
        yaw_deg=round(yaw_deg, 2),
        pitch_deg=round(pitch_deg, 2),
        roll_deg=round(roll_deg, 2),
        is_frontal=is_frontal,
    )



def assess_quality(
    img_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]] | None,
    face_count: int,
    config: FaceScanConfig = DEFAULT_CONFIG,
) -> QualityAssessment:
    """Runs complete Stage B image-quality assessment."""
    h, w, _ = img_rgb.shape
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    issues: list[str] = []
    recommendations: list[str] = []

    # 1. Face count check
    if face_count > 1:
        return QualityAssessment(
            status=QualityStatus.REJECTED,
            score=0.0,
            checks=QualityChecks(
                sharpness_score=0.0,
                brightness_mean=float(np.mean(gray)),
                overexposed_ratio=0.0,
                lighting_symmetry_ratio=1.0,
                face_coverage_ratio=0.0,
                head_pose=None,
                issues=["Multiple faces detected."],
                recommendations=["Please capture or upload a photo with only one person in the frame."],
            ),
            message="Multiple faces detected. Please provide an image with only one face.",
        )

    if face_count == 0 or landmarks_px is None or len(landmarks_px) < 468:
        return QualityAssessment(
            status=QualityStatus.REJECTED,
            score=0.0,
            checks=QualityChecks(
                sharpness_score=0.0,
                brightness_mean=float(np.mean(gray)),
                overexposed_ratio=0.0,
                lighting_symmetry_ratio=1.0,
                face_coverage_ratio=0.0,
                head_pose=None,
                issues=["No face detected in the frame."],
                recommendations=["Position your face in the center of the frame in good lighting."],
            ),
            message="No face detected. Please ensure your full face is visible and well lit.",
        )

    # 2. Sharpness / Blur check
    sharpness = calculate_sharpness(gray)
    if sharpness < config.min_sharpness_acceptable:
        issues.append("Image is too blurry for accurate landmark detection.")
        recommendations.append("Hold camera steady and ensure proper lens focus.")
    elif sharpness < config.min_sharpness_recommended:
        issues.append("Image is slightly soft; sharper focus is recommended.")

    # 3. Brightness / Exposure check
    brightness_mean = float(np.mean(gray))
    overexposed_ratio = float(np.sum(gray >= config.overexposure_pixel_threshold)) / float(gray.size)

    if brightness_mean < config.min_brightness_acceptable:
        issues.append("Image is too dark (underexposed).")
        recommendations.append("Increase room lighting or face towards a light source.")
    elif brightness_mean > config.max_brightness_acceptable or overexposed_ratio > config.max_overexposed_pixel_ratio:
        issues.append("Image has harsh glare or overexposure.")
        recommendations.append("Avoid direct flash glare or harsh backlighting.")

    # 4. Face Bounding Box & Coverage
    oval_pts = np.array([[landmarks_px[i][0], landmarks_px[i][1]] for i in FACE_OVAL_INDICES], dtype=np.float32)
    min_x, min_y = np.min(oval_pts, axis=0)
    max_x, max_y = np.max(oval_pts, axis=0)
    face_w = max(1.0, max_x - min_x)
    face_h = max(1.0, max_y - min_y)
    face_coverage = (face_w * face_h) / float(w * h)

    if face_coverage < config.min_face_coverage_ratio:
        issues.append("Face is too small in the frame.")
        recommendations.append("Move closer to the camera so your face occupies the center.")
    elif face_coverage < config.recommended_face_coverage:
        recommendations.append("A slightly closer portrait will give even higher landmark precision.")

    # 5. Lighting Symmetry across Face
    fx1 = int(max(0, min_x))
    fy1 = int(max(0, min_y))
    fx2 = int(min(w, max_x))
    fy2 = int(min(h, max_y))

    face_crop = gray[fy1:fy2, fx1:fx2]
    lighting_symmetry = 1.0
    if face_crop.shape[1] >= 10:
        mid_col = face_crop.shape[1] // 2
        left_half = face_crop[:, :mid_col]
        right_half = face_crop[:, mid_col:]
        left_mean = float(np.mean(left_half)) + 1e-4
        right_mean = float(np.mean(right_half)) + 1e-4
        lighting_symmetry = left_mean / right_mean

        if lighting_symmetry < config.min_lighting_symmetry or lighting_symmetry > config.max_lighting_symmetry:
            issues.append("Harsh shadow on one side of your face.")
            recommendations.append("Ensure balanced, frontal lighting across both sides of your face.")

    # 6. Head Pose Estimation (Yaw, Pitch, Roll)
    head_pose = estimate_head_pose(landmarks_px, w, h)

    if abs(head_pose.yaw_deg) > config.max_yaw_acceptable_deg:
        issues.append(f"Head is turned sideways by {abs(head_pose.yaw_deg):.1f}° (max {config.max_yaw_acceptable_deg}°).")
        recommendations.append("Look directly straight into the camera lens.")
    elif abs(head_pose.yaw_deg) > config.recommended_yaw_deg:
        recommendations.append("Slight sideways turn detected; facing directly forward is optimal.")

    if abs(head_pose.pitch_deg) > config.max_pitch_acceptable_deg:
        issues.append(f"Head is tilted up/down by {abs(head_pose.pitch_deg):.1f}° (max {config.max_pitch_acceptable_deg}°).")
        recommendations.append("Keep camera at eye level.")
    elif abs(head_pose.pitch_deg) > config.recommended_pitch_deg:
        recommendations.append("Camera slightly above or below eye level; keep it horizontal.")

    if abs(head_pose.roll_deg) > config.max_roll_acceptable_deg:
        issues.append(f"Head is tilted sideways by {abs(head_pose.roll_deg):.1f}° (max {config.max_roll_acceptable_deg}°).")
        recommendations.append("Keep your head level.")

    # Determine Quality Status
    # Critical rejections:
    is_rejected = (
        sharpness < config.min_sharpness_acceptable
        or brightness_mean < config.min_brightness_acceptable
        or brightness_mean > config.max_brightness_acceptable
        or face_coverage < config.min_face_coverage_ratio
        or not head_pose.is_frontal
        or (lighting_symmetry < config.min_lighting_symmetry or lighting_symmetry > config.max_lighting_symmetry)
    )

    # Score calculation (0.0 to 1.0)
    sharp_factor = min(1.0, max(0.0, (sharpness - 50.0) / 200.0))
    pose_factor = max(0.0, 1.0 - (abs(head_pose.yaw_deg) / 25.0 + abs(head_pose.pitch_deg) / 25.0 + abs(head_pose.roll_deg) / 20.0) / 3.0)
    coverage_factor = min(1.0, max(0.0, face_coverage / config.recommended_face_coverage))
    quality_score = float(np.clip(0.4 * sharp_factor + 0.4 * pose_factor + 0.2 * coverage_factor, 0.05, 1.0))

    if is_rejected:
        status = QualityStatus.REJECTED
        message = issues[0] if issues else "Image did not pass quality checks."
    elif issues or recommendations:
        status = QualityStatus.RETAKE_RECOMMENDED
        message = "Image accepted with minor advisory notices."
    else:
        status = QualityStatus.ACCEPTED
        message = "Image passed all biometric quality and pose checks."

    checks = QualityChecks(
        sharpness_score=round(sharpness, 2),
        brightness_mean=round(brightness_mean, 2),
        overexposed_ratio=round(overexposed_ratio, 4),
        lighting_symmetry_ratio=round(lighting_symmetry, 2),
        face_coverage_ratio=round(face_coverage, 4),
        head_pose=head_pose,
        issues=issues,
        recommendations=recommendations,
    )

    return QualityAssessment(
        status=status,
        score=round(quality_score, 3),
        checks=checks,
        message=message,
    )
