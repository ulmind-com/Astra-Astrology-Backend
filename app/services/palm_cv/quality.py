"""Palm image quality assessment and EXIF orientation normalization."""

import io
from dataclasses import dataclass, field
from enum import Enum
import cv2
import numpy as np
from PIL import Image, ImageOps

from app.services.palm_cv.config import DEFAULT_CONFIG, PalmScanConfig


class QualityStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    RETAKE_RECOMMENDED = "RETAKE_RECOMMENDED"
    REJECTED = "REJECTED"


@dataclass
class PalmQualityAssessment:
    status: QualityStatus
    quality_score: float  # [0.0, 1.0]
    is_valid: bool
    hand_count: int
    detected_hand: str | None
    expected_hand: str
    is_hand_matched: bool
    hand_coverage_pct: float
    blur_score: float
    brightness_mean: float
    contrast_std: float
    fingers_extended: bool
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def decode_and_correct_orientation(raw_bytes: bytes) -> np.ndarray:
    """Decodes image bytes, respects EXIF orientation, and returns RGB NumPy array."""
    try:
        pil_img = Image.open(io.BytesIO(raw_bytes))
        pil_img = ImageOps.exif_transpose(pil_img)
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        return np.array(pil_img, dtype=np.uint8)
    except Exception:
        # Fallback to OpenCV standard decode
        nparr = np.frombuffer(raw_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Failed to decode image data into valid image matrix.")
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def assess_palm_quality(
    img_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]] | None,
    hand_count: int,
    detected_hand: str | None,
    expected_hand: str = "left",
    config: PalmScanConfig = DEFAULT_CONFIG,
) -> PalmQualityAssessment:
    """Evaluates palm capture quality, hand orientation, and finger positioning."""
    issues: list[str] = []
    recs: list[str] = []

    h, w, _ = img_rgb.shape
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    # Blur / Sharpness check via Laplacian variance
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    # Brightness mean and contrast
    brightness_mean = float(np.mean(gray))
    contrast_std = float(np.std(gray))

    # Reject if no hand or multiple hands
    if hand_count == 0 or not landmarks_px:
        issues.append("হাত শনাক্ত করা যায়নি (No hand detected).")
        recs.append("আপনার পুরো হাত ও তালু ফ্রেমের মাঝে রাখুন (Place your entire palm clearly in frame).")
        return PalmQualityAssessment(
            status=QualityStatus.REJECTED,
            quality_score=0.0,
            is_valid=False,
            hand_count=hand_count,
            detected_hand=None,
            expected_hand=expected_hand,
            is_hand_matched=False,
            hand_coverage_pct=0.0,
            blur_score=laplacian_var,
            brightness_mean=brightness_mean,
            contrast_std=contrast_std,
            fingers_extended=False,
            issues=issues,
            recommendations=recs,
        )

    if hand_count > 1:
        issues.append("একাধিক হাত শনাক্ত হয়েছে (Multiple hands detected).")
        recs.append("একবারে শুধুমাত্র একটি হাত ক্যামেরার সামনে ধরুন (Scan only one hand at a time).")
        return PalmQualityAssessment(
            status=QualityStatus.REJECTED,
            quality_score=0.15,
            is_valid=False,
            hand_count=hand_count,
            detected_hand=detected_hand,
            expected_hand=expected_hand,
            is_hand_matched=False,
            hand_coverage_pct=0.0,
            blur_score=laplacian_var,
            brightness_mean=brightness_mean,
            contrast_std=contrast_std,
            fingers_extended=False,
            issues=issues,
            recommendations=recs,
        )

    # Handedness check: match detected vs expected
    is_hand_matched = True
    if detected_hand and expected_hand:
        is_hand_matched = detected_hand.lower() == expected_hand.lower()
        if not is_hand_matched:
            issues.append(
                f"প্রত্যাশিত হাত {expected_hand.upper()}, কিন্তু {detected_hand.upper()} হাত পাওয়া গেছে।"
            )
            recs.append(
                f"শাস্ত্রীয় নিয়মে পুরুষদের জন্য বাম হাত (Left Hand) এবং মহিলাদের জন্য ডান হাত (Right Hand) স্ক্যান করুন।"
            )

    # Hand coverage bounding box
    xs = [pt[0] for pt in landmarks_px]
    ys = [pt[1] for pt in landmarks_px]
    min_x, max_x = max(0, min(xs)), min(w, max(xs))
    min_y, max_y = max(0, min(ys)), min(h, max(ys))
    box_area = (max_x - min_x) * (max_y - min_y)
    hand_coverage_pct = round((box_area / float(w * h)) * 100.0, 2)

    if hand_coverage_pct < (config.min_hand_coverage_ratio * 100):
        issues.append("হাতটি ক্যামেরা থেকে অনেক দূরে (Hand too far away).")
        recs.append("হাতটি ক্যামেরার আরেকটু কাছে আনুন (Bring your hand closer to fill the frame).")

    # Check finger extension (wrist 0 to tips 8, 12, 16 vs knuckles 5, 9, 13)
    wrist = np.array(landmarks_px[0][:2])
    tips = [np.array(landmarks_px[i][:2]) for i in [8, 12, 16]]
    mcps = [np.array(landmarks_px[i][:2]) for i in [5, 9, 13]]

    avg_tip_dist = np.mean([np.linalg.norm(t - wrist) for t in tips])
    avg_mcp_dist = np.mean([np.linalg.norm(m - wrist) for m in mcps])
    finger_extension_ratio = float(avg_tip_dist / max(1.0, avg_mcp_dist))
    fingers_extended = finger_extension_ratio >= 1.35

    if not fingers_extended:
        issues.append("আঙুলগুলো সম্পূর্ণ সোজা নেই (Fingers not fully extended).")
        recs.append("আঙুলগুলো সোজা ও স্বাভাবিকভাবে মেলে ধরুন (Keep fingers open and palm flat).")

    # Lighting checks
    if brightness_mean < config.min_brightness_mean:
        issues.append("আলো কম (Lighting is too dark).")
        recs.append("ভালো আলো বা দিনের আলোতে হাত স্ক্যান করুন (Ensure bright, even illumination).")
    elif brightness_mean > config.max_brightness_mean:
        issues.append("আলো অতিরিক্ত বেশি বা প্রতিফলিত (Excessive glare / overexposed).")
        recs.append("সরাসরি আলোর তীব্র প্রতিফলন এড়িয়ে চলুন (Avoid direct harsh glare on palm).")

    if laplacian_var < config.min_laplacian_sharpness:
        issues.append("ছবি কিছুটা ঝাপসা (Hand image is blurry).")
        recs.append("হাতটি স্থির রাখুন যাতে রেখাগুলো স্পষ্ট দেখা যায় (Hold your hand steady).")

    # Calculate overall quality score [0.0 - 1.0]
    sharpness_factor = min(1.0, laplacian_var / 120.0)
    brightness_factor = 1.0 - min(1.0, abs(brightness_mean - 128.0) / 110.0)
    contrast_factor = min(1.0, contrast_std / 45.0)
    coverage_factor = min(1.0, hand_coverage_pct / 30.0)
    extension_factor = 1.0 if fingers_extended else 0.65
    hand_match_factor = 1.0 if is_hand_matched else 0.85

    quality_score = round(
        float(
            0.25 * sharpness_factor
            + 0.20 * brightness_factor
            + 0.15 * contrast_factor
            + 0.15 * coverage_factor
            + 0.15 * extension_factor
            + 0.10 * hand_match_factor
        ),
        3,
    )

    # Determine status
    if quality_score >= 0.62 and fingers_extended:
        status = QualityStatus.ACCEPTED
    elif quality_score >= 0.40:
        status = QualityStatus.RETAKE_RECOMMENDED
    else:
        status = QualityStatus.REJECTED

    return PalmQualityAssessment(
        status=status,
        quality_score=quality_score,
        is_valid=(status != QualityStatus.REJECTED),
        hand_count=hand_count,
        detected_hand=detected_hand,
        expected_hand=expected_hand,
        is_hand_matched=is_hand_matched,
        hand_coverage_pct=hand_coverage_pct,
        blur_score=round(laplacian_var, 2),
        brightness_mean=round(brightness_mean, 2),
        contrast_std=round(contrast_std, 2),
        fingers_extended=fingers_extended,
        issues=issues,
        recommendations=recs,
    )
