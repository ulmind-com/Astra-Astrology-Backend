"""Facial feature measurement module.

Calculates the 23 classical biometric and geometric proportions used in
Vedic Samudrik Shastra physiognomy analysis.

Every formula is documented with its anatomical interpretation, landmark pairs,
and normalization method. All outputs are strictly finite, non-negative, and
bounded in [0.0, 10.0].
"""

import math
from dataclasses import dataclass
from typing import Any
import numpy as np

from app.services.face_cv.landmarks import LandmarkIndex as P


@dataclass
class MeasurementDetail:
    name: str
    value: float
    description: str
    formula: str
    landmarks_used: list[int]
    status: str = "available"


def _dist2d(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
    """Euclidean distance in 2D projection."""
    return float(math.hypot(p1[0] - p2[0], p1[1] - p2[1]))


def _dist3d(p1: tuple[float, float, float], p2: tuple[float, float, float]) -> float:
    """Euclidean distance in 3D landmark coordinates."""
    return float(math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2))


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Guards against division by zero or NaN results."""
    if denominator < 1e-6 or math.isnan(denominator) or math.isnan(numerator):
        return default
    val = numerator / denominator
    if math.isinf(val) or math.isnan(val):
        return default
    return val


def canonicalize_landmarks_3d(
    landmarks: list[tuple[float, float, float]],
    rotation_matrix: np.ndarray | None = None,
) -> list[tuple[float, float, float]]:
    """Rotates 3D landmarks into a perfectly canonical frontal pose (0 yaw, 0 pitch, 0 roll).

    Compensates for minor natural head rotations using the inverse solvePnP rotation matrix R^T
    around the facial midline pivot. Ensures 100% pose-invariant biometric ratios.
    """
    if rotation_matrix is None or len(landmarks) < 468:
        return landmarks

    pts = np.array(landmarks, dtype=np.float64)  # shape (N, 3)
    pivot = np.mean(pts[[P.CHEEK_RIGHT, P.CHEEK_LEFT, P.NOSE_BRIDGE_TOP]], axis=0)

    # R is rotation from model to camera space. R^T is inverse rotation back to canonical frontal space.
    r_inv = rotation_matrix.T

    pts_centered = pts - pivot
    pts_canonical = np.dot(pts_centered, r_inv.T) + pivot

    return [tuple(float(c) for c in row) for row in pts_canonical]


def extract_measurements(
    landmarks: list[tuple[float, float, float]],
) -> tuple[dict[str, float], dict[str, MeasurementDetail]]:
    """Extracts all 23 geometric facial proportions from 478 landmarks.

    Args:
        landmarks: List of (x, y, z) coordinates (either normalized or pixel).

    Returns:
        (measurements_dict, details_dict)
    """
    if len(landmarks) < 468:
        raise ValueError(f"Insufficient landmarks: expected at least 468, got {len(landmarks)}")

    # 1. Base Framework Dimensions in 3D anatomical space
    face_w = _dist3d(landmarks[P.CHEEK_RIGHT], landmarks[P.CHEEK_LEFT])
    face_h = _dist3d(landmarks[P.FOREHEAD_TOP], landmarks[P.CHIN_BOTTOM])
    jaw_w = _dist3d(landmarks[P.JAW_RIGHT], landmarks[P.JAW_LEFT])
    brow_w = _dist3d(landmarks[P.BROW_RIDGE_RIGHT], landmarks[P.BROW_RIDGE_LEFT])

    # 2. Eye Dimensions (averaged across both eyes for symmetry independence)
    r_eye_w = _dist3d(landmarks[P.R_EYE_OUTER], landmarks[P.R_EYE_INNER])
    l_eye_w = _dist3d(landmarks[P.L_EYE_INNER], landmarks[P.L_EYE_OUTER])
    r_eye_h = _dist3d(landmarks[P.R_EYE_TOP], landmarks[P.R_EYE_BOTTOM])
    l_eye_h = _dist3d(landmarks[P.L_EYE_TOP], landmarks[P.L_EYE_BOTTOM])

    eye_w = (r_eye_w + l_eye_w) / 2.0
    eye_h = (r_eye_h + l_eye_h) / 2.0

    # 3. Eyebrow Dimensions in 3D
    r_brow_thick = _dist3d(landmarks[P.R_BROW_PEAK], landmarks[P.R_BROW_PEAK_LOWER])
    l_brow_thick = _dist3d(landmarks[P.L_BROW_PEAK], landmarks[P.L_BROW_PEAK_LOWER])
    brow_thick = (r_brow_thick + l_brow_thick) / 2.0

    r_brow_len = _dist3d(landmarks[P.R_BROW_INNER], landmarks[P.R_BROW_OUTER])
    l_brow_len = _dist3d(landmarks[P.L_BROW_INNER], landmarks[P.L_BROW_OUTER])
    brow_len = (r_brow_len + l_brow_len) / 2.0

    # Arch rise: distance of peak from chord connecting inner & outer ends in 3D
    def _arch_rise(inner_idx: int, peak_idx: int, outer_idx: int) -> float:
        inner = landmarks[inner_idx]
        peak = landmarks[peak_idx]
        outer = landmarks[outer_idx]
        chord_mid = ((inner[0] + outer[0]) / 2.0, (inner[1] + outer[1]) / 2.0, (inner[2] + outer[2]) / 2.0)
        return _dist3d(peak, chord_mid)

    brow_arch = (_arch_rise(P.R_BROW_INNER, P.R_BROW_PEAK, P.R_BROW_OUTER) +
                 _arch_rise(P.L_BROW_INNER, P.L_BROW_PEAK, P.L_BROW_OUTER)) / 2.0

    # 4. Nose Dimensions in 3D
    nose_w = _dist3d(landmarks[P.NOSE_RIGHT_WING], landmarks[P.NOSE_LEFT_WING])
    nose_len = _dist3d(landmarks[P.NOSE_BRIDGE_TOP], landmarks[P.NOSE_BASE])
    nostril_w = _dist3d(landmarks[P.NOSTRIL_RIGHT], landmarks[P.NOSTRIL_LEFT])
    face_mid_x = (landmarks[P.CHEEK_RIGHT][0] + landmarks[P.CHEEK_LEFT][0]) / 2.0

    # 5. Mouth & Lip Dimensions in 3D
    mouth_w = _dist3d(landmarks[P.MOUTH_CORNER_RIGHT], landmarks[P.MOUTH_CORNER_LEFT])
    lip_h = _dist3d(landmarks[P.LIP_UPPER_TOP], landmarks[P.LIP_LOWER_BOTTOM])
    corner_y = (landmarks[P.MOUTH_CORNER_RIGHT][1] + landmarks[P.MOUTH_CORNER_LEFT][1]) / 2.0

    # 6. Lower Face & Cheeks in 3D
    cheek_line_w = _dist3d(landmarks[P.CHEEK_LINE_RIGHT], landmarks[P.CHEEK_LINE_LEFT])
    forehead_h_val = _dist3d(landmarks[P.GLABELLA], landmarks[P.FOREHEAD_TOP])

    # 7. Compute All 23 Standard Vedic Proportions
    raw_measurements: dict[str, tuple[float, str, str, list[int]]] = {
        "wh_ratio": (
            _safe_div(face_w, face_h),
            "Face width-to-height ratio (cheekbone to cheekbone / hairline to chin)",
            "face_w / face_h",
            [P.CHEEK_RIGHT, P.CHEEK_LEFT, P.FOREHEAD_TOP, P.CHIN_BOTTOM],
        ),
        "jaw_cheek": (
            _safe_div(jaw_w, face_w),
            "Jaw width relative to cheekbone width",
            "jaw_w / face_w",
            [P.JAW_RIGHT, P.JAW_LEFT, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "brow_cheek": (
            _safe_div(brow_w, face_w),
            "Upper forehead / brow ridge width relative to cheek width",
            "brow_w / face_w",
            [P.BROW_RIDGE_RIGHT, P.BROW_RIDGE_LEFT, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "forehead_h": (
            _safe_div(forehead_h_val, face_h),
            "Vertical forehead height relative to total face height",
            "forehead_h / face_h",
            [P.GLABELLA, P.FOREHEAD_TOP, P.CHIN_BOTTOM],
        ),
        "eye_open": (
            _safe_div(eye_h, eye_w),
            "Eye openness (palpebral aperture height relative to fissure width)",
            "eye_h / eye_w",
            [P.R_EYE_TOP, P.R_EYE_BOTTOM, P.R_EYE_OUTER, P.R_EYE_INNER],
        ),
        "eye_size": (
            _safe_div(eye_w, face_w),
            "Eye width relative to total face width",
            "eye_w / face_w",
            [P.R_EYE_OUTER, P.R_EYE_INNER, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "eye_gap": (
            _safe_div(_dist2d(landmarks[P.R_EYE_INNER], landmarks[P.L_EYE_INNER]), eye_w),
            "Inter-canthal distance (gap between eyes relative to single eye width)",
            "inter_eye_gap / eye_w",
            [P.R_EYE_INNER, P.L_EYE_INNER],
        ),
        "eye_tilt": (
            max(0.0, _safe_div(
                ((landmarks[P.R_EYE_INNER][1] - landmarks[P.R_EYE_OUTER][1]) +
                 (landmarks[P.L_EYE_INNER][1] - landmarks[P.L_EYE_OUTER][1])) / 2.0,
                eye_w,
            )),
            "Eye axis canthal tilt (outer canthus elevation above inner canthus / eye width)",
            "canthal_tilt / eye_w",
            [P.R_EYE_INNER, P.R_EYE_OUTER, P.L_EYE_INNER, P.L_EYE_OUTER],
        ),
        "eye_asym": (
            _safe_div(abs(r_eye_h - l_eye_h), max(1e-6, (r_eye_h + l_eye_h) / 2.0)),
            "Left/right eye height asymmetry relative to mean eye height",
            "|r_eye_h - l_eye_h| / mean_eye_h",
            [P.R_EYE_TOP, P.R_EYE_BOTTOM, P.L_EYE_TOP, P.L_EYE_BOTTOM],
        ),
        "brow_thick": (
            _safe_div(brow_thick, eye_w),
            "Eyebrow thickness relative to eye width",
            "brow_thickness / eye_w",
            [P.R_BROW_PEAK, P.R_BROW_PEAK_LOWER, P.L_BROW_PEAK, P.L_BROW_PEAK_LOWER],
        ),
        "brow_arch": (
            _safe_div(brow_arch, brow_len),
            "Eyebrow arch curvature (vertical rise / brow length)",
            "brow_arch_rise / brow_length",
            [P.R_BROW_INNER, P.R_BROW_PEAK, P.R_BROW_OUTER],
        ),
        "brow_gap": (
            _safe_div(_dist2d(landmarks[P.R_BROW_INNER], landmarks[P.L_BROW_INNER]), eye_w),
            "Gap between medial eyebrow heads relative to eye width",
            "inter_brow_gap / eye_w",
            [P.R_BROW_INNER, P.L_BROW_INNER],
        ),
        "brow_len": (
            _safe_div(brow_len, eye_w),
            "Eyebrow length relative to eye width",
            "brow_length / eye_w",
            [P.R_BROW_INNER, P.R_BROW_OUTER],
        ),
        "nose_w": (
            _safe_div(nose_w, face_w),
            "Alar nose width relative to face width",
            "nose_w / face_w",
            [P.NOSE_RIGHT_WING, P.NOSE_LEFT_WING, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "nose_len": (
            _safe_div(nose_len, face_h),
            "Nose length (nasion to subnasale) relative to face height",
            "nose_len / face_h",
            [P.NOSE_BRIDGE_TOP, P.NOSE_BASE, P.FOREHEAD_TOP, P.CHIN_BOTTOM],
        ),
        "nostril": (
            _safe_div(nostril_w, nose_w),
            "Nostril width relative to alar nose width",
            "nostril_w / nose_w",
            [P.NOSTRIL_RIGHT, P.NOSTRIL_LEFT, P.NOSE_RIGHT_WING, P.NOSE_LEFT_WING],
        ),
        "nose_dev": (
            _safe_div(abs(landmarks[P.NOSE_TIP][0] - face_mid_x), face_w),
            "Nose tip lateral deviation from face vertical midline relative to face width",
            "|nose_tip.x - mid.x| / face_w",
            [P.NOSE_TIP, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "lip_thick": (
            _safe_div(lip_h, mouthW := max(1e-6, mouth_w)),
            "Total lip thickness relative to mouth width",
            "lip_h / mouth_w",
            [P.LIP_UPPER_TOP, P.LIP_LOWER_BOTTOM, P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT],
        ),
        "mouth_w": (
            _safe_div(mouth_w, face_w),
            "Mouth width (cheilion to cheilion) relative to face width",
            "mouth_w / face_w",
            [P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
        "lip_corner": (
            max(0.0, _safe_div(landmarks[P.LIP_LOWER_BOTTOM][1] - corner_y, mouth_w)),
            "Mouth corner elevation from lower vermilion border / mouth width (upturned vs downturned)",
            "(lip_bottom.y - corner.y) / mouth_w",
            [P.LIP_LOWER_BOTTOM, P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT],
        ),
        "lip_asym": (
            _safe_div(
                abs(landmarks[P.MOUTH_CORNER_RIGHT][1] - landmarks[P.MOUTH_CORNER_LEFT][1]),
                max(1e-6, lip_h),
            ),
            "Oral commissure height difference relative to lip thickness",
            "|corner_r.y - corner_l.y| / lip_h",
            [P.MOUTH_CORNER_RIGHT, P.MOUTH_CORNER_LEFT, P.LIP_UPPER_TOP, P.LIP_LOWER_BOTTOM],
        ),
        "chin_h": (
            _safe_div(abs(landmarks[P.CHIN_BOTTOM][1] - landmarks[P.LIP_LOWER_BOTTOM][1]), face_h),
            "Vertical chin height (sublabiale to gnathion) relative to face height",
            "chin_h / face_h",
            [P.CHIN_BOTTOM, P.LIP_LOWER_BOTTOM, P.FOREHEAD_TOP],
        ),
        "cheek_full": (
            _safe_div(cheek_line_w, face_w),
            "Lower cheek width at stomion level relative to zygomatic face width",
            "cheek_line_w / face_w",
            [P.CHEEK_LINE_RIGHT, P.CHEEK_LINE_LEFT, P.CHEEK_RIGHT, P.CHEEK_LEFT],
        ),
    }

    measurements_dict: dict[str, float] = {}
    details_dict: dict[str, MeasurementDetail] = {}

    for name, (val, desc, formula, lm_indices) in raw_measurements.items():
        # Clamp strictly between 0.0 and 10.0 and round to 4 decimals
        clamped_val = round(max(0.0, min(10.0, float(val))), 4)
        measurements_dict[name] = clamped_val
        details_dict[name] = MeasurementDetail(
            name=name,
            value=clamped_val,
            description=desc,
            formula=formula,
            landmarks_used=lm_indices,
            status="available",
        )

    return measurements_dict, details_dict


def calculate_tri_zone_analysis(
    landmarks: list[tuple[float, float, float]] | None = None,
    measurements: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Calculates classical Samudrika Shastra Tri-Zone (Triguna / Three Ages) balance.

    Upper Zone (Trichion to Glabella): 0-28 yrs, ruled by Sun & Jupiter.
    Middle Zone (Glabella to Subnasale): 28-50 yrs, ruled by Mars & Mercury.
    Lower Zone (Subnasale to Menton): 50+ yrs, ruled by Venus & Saturn.
    Ideal proportion is 1:1:1 (33.3% each) representing 'Samata Tri-Kuta'.
    """
    if landmarks and len(landmarks) >= 468:
        upper_h = _dist3d(landmarks[P.FOREHEAD_TOP], landmarks[P.GLABELLA])
        middle_h = _dist3d(landmarks[P.GLABELLA], landmarks[P.NOSE_BASE])
        lower_h = _dist3d(landmarks[P.NOSE_BASE], landmarks[P.CHIN_BOTTOM])
    elif measurements:
        fh = measurements.get("forehead_h", 0.25)
        nl = measurements.get("nose_len", 0.34)
        ch = measurements.get("chin_h", 0.22)
        upper_h = max(0.01, fh)
        middle_h = max(0.01, nl)
        lower_h = max(0.01, ch + 0.10)
    else:
        upper_h, middle_h, lower_h = 0.333, 0.333, 0.334

    tot = max(1e-6, upper_h + middle_h + lower_h)
    upper_pct = round((upper_h / tot) * 100, 1)
    middle_pct = round((middle_h / tot) * 100, 1)
    lower_pct = round((lower_h / tot) * 100, 1)

    # Normalize to 100%
    diff = round(100.0 - (upper_pct + middle_pct + lower_pct), 1)
    middle_pct = round(middle_pct + diff, 1)

    ratio_str = f"{round(upper_pct / 33.33, 2)} : {round(middle_pct / 33.33, 2)} : {round(lower_pct / 33.33, 2)}"

    max_v = max(upper_pct, middle_pct, lower_pct)
    min_v = min(upper_pct, middle_pct, lower_pct)

    if (max_v - min_v) <= 6.5:
        balance_status = "balanced"
        title_en = "Harmonious Tri-Kuta Equilibrium (সমত্রিকূট লক্ষণ)"
        desc_en = "Your three facial zones exist in auspicious 1:1:1 equilibrium. Signifies steady karma, uninterrupted fortune, and graceful life progress through youth, middle age, and maturity."
        desc_bn = "আপনার মুখের তিনটি মণ্ডল নিখুঁত ১:১:১ ভারসাম্যে বিরাজ করছে। শাস্ত্রানুযায়ী এটি সমত্রিকূট লক্ষণ—যা শৈশব, যৌবন ও উত্তর বয়সে নিরবচ্ছিন্ন সৌভাগ্য ও মানসিক স্থিরতার পরিচায়ক।"
        desc_hi = "आपके चेहरे के तीनों मंडल 1:1:1 के शुभ संतुलन में हैं। यह जीवन के सभी पड़ावों में स्थिर भाग्य और सुखद प्रगति का प्रतीक है।"
    elif upper_pct >= middle_pct and upper_pct >= lower_pct:
        balance_status = "upper_dominant"
        title_en = "Intellectual & Ancestral Eminence (উর্ধ্ব মণ্ডল প্রাধান্য)"
        desc_en = "Upper zone (0-28 yrs, Sun & Jupiter) is preeminent. Indicates exceptional analytical acumen, parental merit, philosophical vision, and prominent early-life educational success."
        desc_bn = "উর্ধ্ব মণ্ডল (০–২৮ বছর, সূর্য ও বৃহস্পতি শাসিত) সর্বাধিক বিকশিত। প্রখর মেধা, পিতৃবংশের আশীর্বাদ, উচ্চ বিদ্যা ও জীবনের প্রথমার্ধে দ্রুত সাফল্যের পরিচায়ক।"
        desc_hi = "ऊपरी मंडल (0-28 वर्ष, सूर्य व गुरु) सबसे प्रबल है। यह उच्च विद्या, प्रखर बुद्धि और पूर्वजों के आशीर्वाद से आरंभिक जीवन में सफलता का संकेत है।"
    elif middle_pct >= upper_pct and middle_pct >= lower_pct:
        balance_status = "middle_dominant"
        title_en = "Enterprise & Material Triumph (মধ্য মণ্ডল প্রাধান্য)"
        desc_en = "Middle zone (28-50 yrs, Mars & Mercury) is dominant. Bestows tenacious entrepreneurial drive, financial accumulation, leadership authority, and peak worldly prosperity in adult life."
        desc_bn = "মধ্য মণ্ডল (২৮–৫০ বছর, মঙ্গল ও বুধ শাসিত) সর্বাধিক বিকশিত। প্রবল কর্মোদ্যোগ, স্বোপার্জিত অর্থবিত্ত এবং কর্মজীবনে উচ্চ প্রতিপত্তি ও সমৃদ্ধির নির্দেশক।"
        desc_hi = "मध्य मंडल (28-50 वर्ष, मंगल व बुध) प्रधान है। यह कार्यक्षेत्र में अपार सफलता, धन संचय और मध्य आयु में प्रतिष्ठा का प्रतीक है।"
    else:
        balance_status = "lower_dominant"
        title_en = "Longevity & Enduring Legacy (নিম্ন মণ্ডল প্রাধান্য)"
        desc_en = "Lower zone (50+ yrs, Venus & Saturn) is preeminent. Signifies grounded fortitude, deep family affection, real-estate security, and a peaceful, revered later life."
        desc_bn = "নিম্ন মণ্ডল (৫০+ বছর, শুক্র ও শনি শাসিত) সর্বাধিক বিকশিত। অটল ধৈর্য, পারিবারিক সৌহার্দ্য, ভূসম্পত্তি লাভ এবং জীবনের উত্তরকালে পরম শান্তি ও শ্রদ্ধার পরিচায়ক।"
        desc_hi = "निचला मंडल (50+ वर्ष, शुक्र व शनि) प्रबल है। यह दीर्घायु, पारिवारिक सुख, अचल संपत्ति और उत्तरार्ध में शांतिपूर्ण जीवन का सूचक है।"

    eras = [
        {
            "era_name": "Upper Zone (Purva Punya & Youth)",
            "era_name_bn": "উর্ধ্ব মণ্ডল (পূর্বপুণ্য ও বাল্য/তারুণ্য)",
            "age_span": "0 – 28 years",
            "score_pct": upper_pct,
            "rulers": "Sun & Jupiter (সূর্য ও বৃহস্পতি)",
            "deity": "Surya & Prajapati",
            "forecast_en": "Governs foundation, academic focus, parental heritage, and core mental ideals.",
            "forecast_bn": "শিক্ষা, চরিত্র গঠন, পিতৃভাগ্য এবং মননশীলতার ভিত্তি নির্দেশ করে।",
        },
        {
            "era_name": "Middle Zone (Karma & Material Drive)",
            "era_name_bn": "মধ্য মণ্ডল (কর্ম, অর্থ ও পুরুষকার)",
            "age_span": "28 – 50 years",
            "score_pct": middle_pct,
            "rulers": "Mars & Mercury (মঙ্গল ও বুধ)",
            "deity": "Kartikeya & Vishnu",
            "forecast_en": "Governs professional conquest, financial expansion, partnerships, and executive energy.",
            "forecast_bn": "পেশাগত উন্নতি, স্বোপার্জিত সম্পদ, ব্যবসায়িক কৌশল ও নেতৃত্বের বিকাশ নির্দেশ করে।",
        },
        {
            "era_name": "Lower Zone (Sancheet Karma & Longevity)",
            "era_name_bn": "নিম্ন মণ্ডল (সঞ্চিত ভাগ্য, স্থায়িত্ব ও বার্ধক্য)",
            "age_span": "50+ years & Later Life",
            "score_pct": lower_pct,
            "rulers": "Venus & Saturn (শুক্র ও শনি)",
            "deity": "Yama & Lakshmi",
            "forecast_en": "Governs family harmony, physical longevity, accumulated assets, and spiritual peace.",
            "forecast_bn": "পারিবারিক ঐক্য, দীর্ঘায়ু, উত্তরকালের প্রাচুর্য ও আধ্যাত্মিক পরমানন্দ নির্দেশ করে।",
        },
    ]

    return {
        "upper_pct": upper_pct,
        "middle_pct": middle_pct,
        "lower_pct": lower_pct,
        "ratio_str": ratio_str,
        "status": balance_status,
        "title_en": title_en,
        "desc_en": desc_en,
        "desc_bn": desc_bn,
        "desc_hi": desc_hi,
        "eras": eras,
    }


def calculate_pancha_mahabhuta(measurements: dict[str, float]) -> dict[str, Any]:
    """Calculates Five Elements (Pancha Mahabhuta) & Pancha Mahapurusha physiognomy.

    Maps facial proportions to Agni, Prithvi, Jala, Vayu, and Akasha principles.
    """
    wh = measurements.get("wh_ratio", 0.95)
    jc = measurements.get("jaw_cheek", 0.83)
    fh = measurements.get("forehead_h", 0.25)
    lt = measurements.get("lip_thick", 0.35)
    cf = measurements.get("cheek_full", 0.92)
    eo = measurements.get("eye_open", 0.40)

    # 1. Agni (Fire) - Ruchaka (Mars)
    # Characterized by tapered/triangular face, sharp jaw/chin, intense alert eyes
    agni_score = 0.0
    if wh < 0.90:
        agni_score += 35.0
    if jc < 0.82:
        agni_score += 35.0
    if eo > 0.42:
        agni_score += 30.0

    # 2. Prithvi (Earth) - Bhadra (Mercury)
    # Characterized by solid, square proportions, broad grounded jaw
    prithvi_score = 0.0
    if wh >= 1.02:
        prithvi_score += 40.0
    if jc >= 0.85:
        prithvi_score += 40.0
    if cf >= 0.92:
        prithvi_score += 20.0

    # 3. Jala (Water) - Malavya (Venus)
    # Characterized by soft curves, full lips, plump cheeks, soothing grace
    jala_score = 0.0
    if 0.92 <= wh <= 1.05:
        jala_score += 30.0
    if lt >= 0.37:
        jala_score += 40.0
    if cf >= 0.93:
        jala_score += 30.0

    # 4. Vayu (Air) - Sasa (Saturn)
    # Characterized by oblong/long face, lean cheeks, contemplative gaze
    vayu_score = 0.0
    if wh < 0.92:
        vayu_score += 45.0
    if cf < 0.92:
        vayu_score += 35.0
    if jc < 0.84:
        vayu_score += 20.0

    # 5. Akasha (Ether) - Hamsa (Jupiter)
    # Characterized by harmonious oval, broad noble forehead, balanced symmetry
    akasha_score = 0.0
    if 0.90 <= wh <= 1.02:
        akasha_score += 35.0
    if fh >= 0.26:
        akasha_score += 40.0
    if 0.81 <= jc <= 0.85:
        akasha_score += 25.0

    scores = {
        "Agni (Fire)": round(agni_score, 1),
        "Prithvi (Earth)": round(prithvi_score, 1),
        "Jala (Water)": round(jala_score, 1),
        "Vayu (Air)": round(vayu_score, 1),
        "Akasha (Ether)": round(akasha_score, 1),
    }

    dominant = max(scores, key=scores.get)

    profiles = {
        "Agni (Fire)": {
            "element_bn": "অগ্নি তত্ত্ব",
            "element_hi": "अग्नि तत्व",
            "mahapurusha": "Ruchaka Lakshana (Mars / মঙ্গল)",
            "mahapurusha_bn": "রুচক লক্ষণ (মঙ্গল প্রভাবিত)",
            "traits_en": "Driven, fearless, dynamic leader. Instinctive courage, high passion, and decisive executive capability.",
            "traits_bn": "নির্ভীক, তেজস্বী ও অপরাজেয় নেতৃত্বগুণ। তাৎক্ষণিক সিদ্ধান্ত নেওয়ার ক্ষমতা এবং যেকোনো প্রতিকূলতায় বিজয়ী হওয়ার প্রেরণা।",
            "traits_hi": "निडर, साहसी और ओजस्वी नेतृत्व। त्वरित निर्णय क्षमता और चुनौतियों पर विजय पाने की अदम्य इच्छाशक्ति।",
        },
        "Prithvi (Earth)": {
            "element_bn": "পৃথ্বী তত্ত্ব",
            "element_hi": "पृथ्वी तत्व",
            "mahapurusha": "Bhadra Lakshana (Mercury / বুধ)",
            "mahapurusha_bn": "ভদ্র লক্ষণ (বুধ প্রভাবিত)",
            "traits_en": "Pragmatic, steadfast, enduring prosperity. Methodical builder, trustworthy anchor, and solid financial acumen.",
            "traits_bn": "বাস্তববাদী, অটল ও দীর্ঘস্থায়ী সাফল্যের অধিকারী। নির্ভরযোগ্য সুদৃঢ় চরিত্র এবং নিখুঁত অর্থনৈতিক দূরদর্শিতা।",
            "traits_hi": "व्यावहारिक, स्थिर और भरोसेमंद व्यक्तित्व। मजबूत आर्थिक सूझबूझ और ठोस परिणामों पर विश्वास।",
        },
        "Jala (Water)": {
            "element_bn": "জল তত্ত্ব",
            "element_hi": "जल तत्व",
            "mahapurusha": "Malavya Lakshana (Venus / শুক্র)",
            "mahapurusha_bn": "মালব্য লক্ষণ (শুক্র প্রভাবিত)",
            "traits_en": "Magnetic, compassionate, artistic flair. Deep emotional intuition, aesthetic taste, and natural harmonious charm.",
            "traits_bn": "মনোমুগ্ধকর লাবণ্য, গভীর সহমর্মিতা ও কলাকুশলতা। স্বাভাবিক সামাজিক আকর্ষণ ও সবাইকে আপন করে নেওয়ার অনন্য ক্ষমতা।",
            "traits_hi": "आकर्षक, संवेदनशील और कलात्मक अभिरुचि। दूसरों को प्रभावित करने और सामंजस्य बनाए रखने की स्वाभाविक प्रतिभा।",
        },
        "Vayu (Air)": {
            "element_bn": "বায়ু তত্ত্ব",
            "element_hi": "वायु तत्व",
            "mahapurusha": "Sasa Lakshana (Saturn / শনি)",
            "mahapurusha_bn": "শশ লক্ষণ (শনি প্রভাবিত)",
            "traits_en": "Philosophical, detached, profound endurance. Penetrating thinker, unswayed by superficial trends, and disciplined scholar.",
            "traits_bn": "গভীর চিন্তাশীল, সংযমী ও অপার সহনশীল। বাহ্যিক কোলাহল এড়িয়ে অন্তর্নিহিত সত্যের অনুসন্ধানী এবং চরম নীতিবান।",
            "traits_hi": "दार्शनिक, गंभीर और असीम धैर्यवान। दिखावे से दूर रहकर सत्य और सिद्धांतों पर अडिग रहने वाला व्यक्तित्व।",
        },
        "Akasha (Ether)": {
            "element_bn": "আকাশ তত্ত্ব",
            "element_hi": "आकाश तत्व",
            "mahapurusha": "Hamsa Lakshana (Jupiter / বৃহস্পতি)",
            "mahapurusha_bn": "হংস লক্ষণ (বৃহস্পতি প্রভাবিত)",
            "traits_en": "Enlightened, noble, expansive wisdom. Inspires universal trust, moral clarity, and statesman-like benevolence.",
            "traits_bn": "মহিমান্বিত প্রজ্ঞা, ন্যায়পরায়ণতা ও সর্বজনীন শ্রদ্ধা। শিক্ষক ও পথপ্রদর্শকের মতো সমাজহিতৈষী নেতৃত্ব।",
            "traits_hi": "विद्वान, न्यायप्रिय और सर्वसमावेशी प्रज्ञा। समाज में स्वाभाविक आदर और मार्गदर्शन देने की उच्च क्षमता।",
        },
    }

    info = profiles[dominant]

    return {
        "dominant_element": dominant,
        "element_bn": info["element_bn"],
        "element_hi": info["element_hi"],
        "mahapurusha": info["mahapurusha"],
        "mahapurusha_bn": info["mahapurusha_bn"],
        "traits_en": info["traits_en"],
        "traits_bn": info["traits_bn"],
        "traits_hi": info["traits_hi"],
        "scores": scores,
    }
