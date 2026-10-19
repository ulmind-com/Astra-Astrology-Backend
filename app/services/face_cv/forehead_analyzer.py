"""Forehead wrinkle and line detection (Samudrika Shastra planetary line analysis).

Uses multi-scale Gabor filter banks, CLAHE illumination normalization, and
connected-component ridge clustering to detect, classify, and count horizontal
forehead lines according to Vedic physiognomy principles.
"""

from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class ForeheadLine:
    """Represents a single detected horizontal forehead fold/line."""

    y_center: int
    x_start: int
    x_end: int
    width_px: int
    prominence: float  # 0.0 to 1.0 (normalized depth/contrast of wrinkle)
    is_continuous: bool
    planet_name: str
    contour_points: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class ForeheadAnalysisResult:
    """Complete biometric and Vedic analysis of the forehead surface."""

    lines_count: int
    lines: list[ForeheadLine]
    avg_prominence: float
    continuity_ratio: float
    forehead_height_px: float
    forehead_width_px: float
    area_type: str  # "smooth", "single_line", "two_lines", "three_lines", "multi_lines"
    shastra_interpretation: dict[str, str]


# Canonical planetary line names in Vedic Samudrika Shastra (from top hairline to lower brow)
PLANETARY_LINES = [
    ("Saturn", "শনি রেখা"),
    ("Jupiter", "বৃহস্পতি রেখা"),
    ("Mars", "মঙ্গল রেখা"),
    ("Sun", "সূর্য রেখা"),
    ("Moon", "চন্দ্র রেখা"),
    ("Venus", "শুক্র রেখা"),
    ("Mercury", "বুধ রেখা"),
]


def _build_gabor_bank(
    ksize: int = 17, sigma: float = 2.5, lambd: float = 7.0
) -> list[np.ndarray]:
    """Generates Gabor kernels tuned for human skin horizontal wrinkle detection.

    Wrinkles are dark linear depressions primarily oriented along the
    horizontal axis (theta ~ 0 rad).
    """
    kernels = []
    # Evaluate at 0 deg, +12 deg, and -12 deg to handle natural facial curved folds
    for theta in [-0.21, -0.10, 0.0, 0.10, 0.21]:
        kernel = cv2.getGaborKernel(
            ksize=(ksize, ksize),
            sigma=sigma,
            theta=theta,
            lambd=lambd,
            gamma=0.5,
            psi=0,
            ktype=cv2.CV_32F,
        )
        kernels.append(kernel)
    return kernels


def analyze_forehead_lines(
    img_rgb: np.ndarray,
    landmarks_px: list[tuple[float, float, float]],
) -> ForeheadAnalysisResult:
    """Detects and measures horizontal forehead lines / wrinkles using biometrics and OpenCV.

    Args:
        img_rgb: RGB input image.
        landmarks_px: 478 pixel landmark coordinates.

    Returns:
        ForeheadAnalysisResult containing lines count, prominence, continuity, and Vedic meanings.
    """
    h_img, w_img, _ = img_rgb.shape
    if len(landmarks_px) < 468:
        return _empty_result(0.0, 0.0)

    # 1. Extract Forehead Polygonal Boundary
    # Hairline landmarks (top): 10, 109, 338, 67, 297, 108, 337
    # Brow landmarks (bottom): 68, 107, 70, 63, 105, 334, 293, 300, 276
    try:
        poly_pts = [
            (int(landmarks_px[10][0]), int(landmarks_px[10][1])),
            (int(landmarks_px[338][0]), int(landmarks_px[338][1])),
            (int(landmarks_px[297][0]), int(landmarks_px[297][1])),
            (int(landmarks_px[332][0]), int(landmarks_px[332][1])),
            (int(landmarks_px[284][0]), int(landmarks_px[284][1])),
            # Eyebrow tops (with a 6px clearance margin above brows to avoid brow hairs)
            (int(landmarks_px[334][0]), int(landmarks_px[334][1] - 8)),
            (int(landmarks_px[9][0]), int(landmarks_px[9][1] - 8)),
            (int(landmarks_px[105][0]), int(landmarks_px[105][1] - 8)),
            (int(landmarks_px[54][0]), int(landmarks_px[54][1])),
            (int(landmarks_px[103][0]), int(landmarks_px[103][1])),
            (int(landmarks_px[67][0]), int(landmarks_px[67][1])),
            (int(landmarks_px[109][0]), int(landmarks_px[109][1])),
        ]
    except (IndexError, TypeError):
        return _empty_result(0.0, 0.0)

    pts_arr = np.array(poly_pts, dtype=np.int32)
    x_min = max(0, int(np.min(pts_arr[:, 0])))
    y_min = max(0, int(np.min(pts_arr[:, 1])))
    x_max = min(w_img, int(np.max(pts_arr[:, 0])))
    y_max = min(h_img, int(np.max(pts_arr[:, 1])))

    forehead_w = float(x_max - x_min)
    forehead_h = float(y_max - y_min)

    if forehead_w < 35 or forehead_h < 15:
        return _empty_result(forehead_w, forehead_h)

    # 2. Create forehead mask
    mask_full = np.zeros((h_img, w_img), dtype=np.uint8)
    cv2.fillPoly(mask_full, [pts_arr], 255)

    # Inset mask slightly to avoid boundary hair or eyebrow noise
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_full = cv2.erode(mask_full, erode_kernel, iterations=1)

    # Crop Forehead ROI
    roi_gray = cv2.cvtColor(img_rgb[y_min:y_max, x_min:x_max], cv2.COLOR_RGB2GRAY)
    mask_roi = mask_full[y_min:y_max, x_min:x_max]

    if roi_gray.size == 0 or mask_roi.size == 0:
        return _empty_result(forehead_w, forehead_h)

    # 3. Illumination Normalization via CLAHE and Bilateral Edge-Preserving Filter
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(roi_gray)
    smoothed = cv2.bilateralFilter(enhanced, d=7, sigmaColor=35, sigmaSpace=35)

    # 4. Multi-Scale Gabor Filter Bank for directional horizontal folds
    gabor_kernels = _build_gabor_bank()
    gabor_responses = [cv2.filter2D(smoothed, cv2.CV_32F, k) for k in gabor_kernels]
    gabor_max = np.maximum.reduce(gabor_responses)
    gabor_norm = cv2.normalize(gabor_max, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Vertical gradient response (detects valleys where intensity dips locally)
    sobel_y = cv2.Sobel(smoothed, cv2.CV_32F, 0, 1, ksize=3)
    sobel_mag = np.abs(sobel_y)
    sobel_norm = cv2.normalize(sobel_mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Combined wrinkle energy map
    combined = cv2.addWeighted(gabor_norm, 0.70, sobel_norm, 0.30, 0)
    combined = cv2.bitwise_and(combined, combined, mask=mask_roi)

    # 5. Adaptive Thresholding on Forehead Skin Energy
    valid_pixels = combined[mask_roi > 0]
    if len(valid_pixels) == 0:
        return _empty_result(forehead_w, forehead_h)

    mean_val = float(np.mean(valid_pixels))
    std_val = float(np.std(valid_pixels))

    # Prominent wrinkle threshold: significantly higher than flat skin microtexture
    thresh_val = min(245.0, mean_val + 1.25 * std_val)
    _, binary = cv2.threshold(combined, thresh_val, 255, cv2.THRESH_BINARY)

    # Horizontal bridging morphological closing
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 2))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, morph_kernel)

    # 6. Connected Component & Contour Analysis
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_line_len = forehead_w * 0.18  # Must span at least 18% of forehead width
    candidates = []

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = float(w) / max(1.0, float(h))
        # Wrinkles must be primarily horizontal and exceed minimum width
        if w >= min_line_len and aspect_ratio >= 1.9:
            # Measure contrast prominence inside the wrinkle segment
            c_mask = np.zeros_like(roi_gray)
            cv2.drawContours(c_mask, [c], -1, 255, -1)
            prominence = float(np.mean(combined[c_mask > 0])) / 255.0

            candidates.append({
                "y_center": int(y_min + y + h / 2.0),
                "x_start": int(x_min + x),
                "x_end": int(x_min + x + w),
                "width_px": int(w),
                "prominence": min(1.0, prominence * 1.3),
                "contour": [(int(p[0][0] + x_min), int(p[0][1] + y_min)) for p in c],
            })

    # 7. Cluster and merge lines occurring at nearly the same Y height
    # (Two segments on the same horizontal level are parts of one broken line)
    merged_lines: list[ForeheadLine] = []
    candidates.sort(key=lambda item: item["y_center"])

    y_tolerance = max(4.0, forehead_h * 0.12)
    clusters: list[list[dict]] = []

    for cand in candidates:
        matched_cluster = None
        for cluster in clusters:
            avg_y = sum(c["y_center"] for c in cluster) / len(cluster)
            if abs(cand["y_center"] - avg_y) <= y_tolerance:
                matched_cluster = cluster
                break
        if matched_cluster is not None:
            matched_cluster.append(cand)
        else:
            clusters.append([cand])

    # Convert clusters to unified ForeheadLine entries
    for cluster in clusters:
        y_c = int(sum(c["y_center"] for c in cluster) / len(cluster))
        x_s = min(c["x_start"] for c in cluster)
        x_e = max(c["x_end"] for c in cluster)
        span_w = x_e - x_s
        total_w = sum(c["width_px"] for c in cluster)

        # If total segment width covers >= 75% of overall span, it is considered continuous
        is_cont = (total_w / max(1.0, float(span_w))) >= 0.75
        avg_prom = float(sum(c["prominence"] for c in cluster) / len(cluster))

        all_pts = []
        for c in cluster:
            all_pts.extend(c["contour"])

        merged_lines.append(
            ForeheadLine(
                y_center=y_c,
                x_start=x_s,
                x_end=x_e,
                width_px=span_w,
                prominence=round(avg_prom, 2),
                is_continuous=is_cont,
                planet_name="",  # Assigned below
                contour_points=all_pts,
            )
        )

    # Sort lines from top (near hairline) to bottom (near eyebrows)
    merged_lines.sort(key=lambda line: line.y_center)

    # Limit to maximum 7 planetary lines as per Samudrika Shastra
    merged_lines = merged_lines[:7]
    lines_count = len(merged_lines)

    # Assign Vedic Planetary Line names based on relative vertical position
    for idx, line in enumerate(merged_lines):
        if lines_count == 1:
            line.planet_name = "Sun (সূর্য রেখা)"
        elif lines_count == 2:
            line.planet_name = "Jupiter (বৃহস্পতি)" if idx == 0 else "Mars (মঙ্গল)"
        elif lines_count == 3:
            names = ["Saturn (শনি রেখা)", "Jupiter (বৃহস্পতি রেখা)", "Mars (মঙ্গল রেখা)"]
            line.planet_name = names[idx]
        else:
            p_idx = min(idx, len(PLANETARY_LINES) - 1)
            line.planet_name = f"{PLANETARY_LINES[p_idx][0]} ({PLANETARY_LINES[p_idx][1]})"

    # Overall Metrics
    avg_prom = (
        round(float(np.mean([item.prominence for item in merged_lines])), 2)
        if merged_lines
        else 0.0
    )
    cont_ratio = (
        round(float(np.mean([1.0 if item.is_continuous else 0.5 for item in merged_lines])), 2)
        if merged_lines
        else 1.0
    )

    # Area type classification
    if lines_count == 0:
        area_type = "smooth"
    elif lines_count == 1:
        area_type = "single_line"
    elif lines_count == 2:
        area_type = "two_lines"
    elif lines_count == 3:
        area_type = "three_lines"
    else:
        area_type = "multi_lines"

    interp = _get_shastra_interpretation(lines_count, cont_ratio, merged_lines)

    return ForeheadAnalysisResult(
        lines_count=lines_count,
        lines=merged_lines,
        avg_prominence=avg_prom,
        continuity_ratio=cont_ratio,
        forehead_height_px=round(forehead_h, 1),
        forehead_width_px=round(forehead_w, 1),
        area_type=area_type,
        shastra_interpretation=interp,
    )


def _empty_result(w: float, h: float) -> ForeheadAnalysisResult:
    return ForeheadAnalysisResult(
        lines_count=0,
        lines=[],
        avg_prominence=0.0,
        continuity_ratio=1.0,
        forehead_height_px=round(h, 1),
        forehead_width_px=round(w, 1),
        area_type="smooth",
        shastra_interpretation=_get_shastra_interpretation(0, 1.0, []),
    )


def _get_shastra_interpretation(
    count: int,
    continuity: float,
    lines: list[ForeheadLine],
) -> dict[str, str]:
    """Provides authentic Samudrika Shastra (Vedic face reading) meanings for forehead lines."""
    lookup = {
        0: {
            "title_bn": "মসৃণ ও রেখাহীন কপাল (Smooth Forehead)",
            "title_en": "Smooth & Uncreased Forehead",
            "meaning_bn": (
                "কপালে কোনো দৃশ্যমান ভাঁজ বা রেখা না থাকা চঞ্চল মন, মুক্তচিন্তা এবং তরুণসুলভ "
                "প্রাণশক্তির নির্দেশক। আপনি জটিল চিন্তাভাবনা এড়িয়ে সোজা পথে কাজ করতে পছন্দ করেন।"
            ),
            "meaning_en": (
                "A smooth forehead without prominent lines signifies a clear mind, free-spirited "
                "nature, and natural vitality. You prefer straightforward action over complicated "
                "speculation."
            ),
        },
        1: {
            "title_bn": "একরেখা কপাল (Single Prominent Line)",
            "title_en": "Single Prominent Forehead Line",
            "meaning_bn": (
                "কপালে একটি সুস্পষ্ট রেখা গভীর একাগ্রতা এবং আত্মকেন্দ্রিক দৃঢ় সংকল্পের প্রতীক। "
                "সমুদ্র শাস্ত্র অনুযায়ী আপনি যেকোনো একটি লক্ষ্য বা দর্শনে অবিচল থেকে পথ তৈরি করেন।"
            ),
            "meaning_en": (
                "A single clear horizontal line represents laser-sharp focus and determined "
                "willpower. You forge your own unique path and achieve success through steadfast "
                "commitment."
            ),
        },
        2: {
            "title_bn": "দ্বিরেখা কপাল (Two Balanced Lines - বৃহস্পতি ও মঙ্গল)",
            "title_en": "Two Balanced Planetary Lines",
            "meaning_bn": (
                "কপালে দুটি সমান্তরাল রেখা জ্ঞান এবং কর্মের অপূর্ব ভারসাম্য প্রকাশ করে। আপনি একই সাথে "
                "তাত্ত্বিক প্রজ্ঞা এবং বাস্তবিক পদক্ষেপ নিতে পারদর্শী। সমাজে সুসিদ্ধান্তের জন্য সমাদৃত।"
            ),
            "meaning_en": (
                "Two parallel lines reveal an auspicious equilibrium between wisdom and decisive "
                "action. You balance strategic thinking with practical execution, earning trust."
            ),
        },
        3: {
            "title_bn": "ত্রিরেখা কপাল (Three Auspicious Lines - রাজযোগ লক্ষণ)",
            "title_en": "Three Auspicious Royal Lines (Trishula Yoga)",
            "meaning_bn": (
                "সমুদ্র শাস্ত্রে কপালে তিনটি অটুট রেখা থাকা অত্যন্ত সৌভাগ্য ও রাজযোগের লক্ষণ "
                "(শনি, বৃহস্পতি ও মঙ্গল রেখা)। এটি দীর্ঘায়ু, বিপুল জ্ঞান, সামাজিক খ্যাতি এবং "
                "অর্থভাগ্যের নির্দেশ করে।"
            ),
            "meaning_en": (
                "In Samudrika Shastra, three distinct, unbroken horizontal lines represent high "
                "fortune, leadership, and intellectual eminence. It bestows longevity, prosperity, "
                "and societal honor."
            ),
        },
    }

    if count in lookup:
        return lookup[count]

    return {
        "title_bn": f"বহুরেখা কপাল ({count}টি গ্রহীয় রেখা)",
        "title_en": f"Multiple Planetary Lines ({count} Lines)",
        "meaning_bn": (
            f"কপালে {count}টি রেখা থাকা গভীর দার্শনিক প্রবৃত্তি, বহুমুখী চিন্তাধারা এবং "
            "বহুদর্শী অভিজ্ঞতার পরিচায়ক। আপনি যেকোনো বিষয়ের গভীর তলিয়ে দেখতে পারেন।"
        ),
        "meaning_en": (
            f"Having {count} forehead lines denotes a multifaceted mind with philosophical "
            "depth and keen analytical perception. You look beyond surface appearances."
        ),
    }
