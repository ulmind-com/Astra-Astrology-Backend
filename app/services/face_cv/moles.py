"""AI Mole & Til Vichar (Astrological Facial Markings) Engine.

Detects distinctive pigmentations, moles (Til), and beauty marks on facial skin regions
using OpenCV, and maps them to classical Vedic Samudrika Shastra & Dharmender Kumar Bansal rules.
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import Any


# Classical Samudrika Shastra Til Interpretations (Bansal & Brihat Samhita)
TIL_RULES = {
    "forehead_center": {
        "planet": "Jupiter (বৃহস্পতি)",
        "name_en": "Center of Forehead (Third Eye / Trikuti)",
        "name_bn": "কপালের কেন্দ্রবিন্দু (ত্রিকূটী / আজ্ঞা চক্র)",
        "name_hi": "ललाट मध्य (त्रिकुटी)",
        "en": "Exceptional wisdom, philosophical foresight, spiritual authority, and respected public status.",
        "bn": "অসাধারণ প্রজ্ঞা, আধ্যাত্মিক দূরদর্শিতা, সামাজিক সম্মান এবং নীতিবান নেতৃত্বের প্রকাশ।",
        "hi": "असाधारण प्रज्ञा, आध्यात्मिक दृष्टि, समाज में उच्च सम्मान और नीतिपरक नेतृत्व।",
        "male_auspicious": True,
        "female_auspicious": True,
    },
    "forehead_right": {
        "planet": "Sun (সূর্য)",
        "name_en": "Right Forehead (Surya Mandala)",
        "name_bn": "ডান কপাল (সূর্য মণ্ডল)",
        "name_hi": "दाहिना ललाट (सूर्य मंडल)",
        "en": "Rapid career ascent, financial independence, administrative prowess, and royal patronage.",
        "bn": "দ্রুত কর্মোন্নতি, আর্থিক সমৃদ্ধি, প্রশাসনিক সাফল্য এবং উচ্চপদস্থ ব্যক্তির কৃপালাভ।",
        "hi": "शीघ्र पदोन्नति, आर्थिक संप्रभुता, प्रशासनिक क्षमता और उच्चाधिकारियों का सहयोग।",
        "male_auspicious": True,
        "female_auspicious": False,
    },
    "forehead_left": {
        "planet": "Moon (চন্দ্র)",
        "name_en": "Left Forehead (Chandra Mandala)",
        "name_bn": "বাম কপাল (চন্দ্র মণ্ডল)",
        "name_hi": "बायां ललाट (चंद्र मंडल)",
        "en": "Artistic sensibility, fluctuating wealth in early youth, strong devotion, and foreign travel.",
        "bn": "কলা ও নান্দনিক রুচি, প্রথম বয়সে আয়ে কিছুটা অস্থিরতা, কিন্তু বিদেশ ভ্রমণ ও আত্মতৃপ্তি।",
        "hi": "कलात्मक अभिरुचि, विदेश यात्रा के अवसर और गहरी संवेदनशीलता।",
        "male_auspicious": False,
        "female_auspicious": True,
    },
    "cheek_right": {
        "planet": "Venus (শুক্র)",
        "name_en": "Right Cheek (Kapola Dakshina)",
        "name_bn": "ডান গাল (কপোল দক্ষিণ)",
        "name_hi": "दाहिना गाल",
        "en": "Prosperity post-marriage, magnetic social appeal, eloquence, and commercial acumen.",
        "bn": "বিবাহোত্তর সৌভাগ্য, আকর্ষণীয় ব্যক্তিত্ব, মিষ্টভাষী স্বভাব এবং বাণিজ্যে বিশেষ লাভ।",
        "hi": "विवाह उपरांत भाग्योदय, चुंबकीय आकर्षण और व्यापार में प्रचुर सफलता।",
        "male_auspicious": True,
        "female_auspicious": False,
    },
    "cheek_left": {
        "planet": "Mercury (বুধ)",
        "name_en": "Left Cheek (Kapola Vama)",
        "name_bn": "বাম গাল (কপোল বাম)",
        "name_hi": "बायां गाल",
        "en": "Philosophical mindset, deep selective friendships, and artistic creative talents.",
        "bn": "গভীর চিন্তাশীল মন, বাছাই করা ঘনিষ্ঠ বন্ধু এবং সৃজনশীল ও দার্শনিক প্রতিভা।",
        "hi": "गहरा चिंतन, चुनिंदा मित्र और उत्कृष्ट रचनात्मक एवं कलात्मक प्रतिभा।",
        "male_auspicious": False,
        "female_auspicious": True,
    },
    "nose_tip": {
        "planet": "Mercury (বুধ) / Mars (মঙ্গল)",
        "name_en": "Nose Tip or Bridge (Nasa)",
        "name_bn": "নাকের চূড়া বা ব্রিজ (নাসা)",
        "name_hi": "नासिका अग्र",
        "en": "Quick analytical wit, sudden wealth windfall, self-esteem, and high ambition.",
        "bn": "তীক্ষ্ণ বুদ্ধি, আকস্মিক অর্থাগম, প্রবল আত্মমর্যাদাবোধ এবং উচ্চাকাঙ্ক্ষা।",
        "hi": "तीक्ष्ण बुद्धि, अचानक धन लाभ, आत्मसम्मान और महत्वाकांक्षी स्वभाव।",
        "male_auspicious": True,
        "female_auspicious": True,
    },
    "upper_lip": {
        "planet": "Venus (শুক্র)",
        "name_en": "Upper Lip Area (Oshta)",
        "name_bn": "উপরের ঠোঁট (ওষ্ঠ)",
        "name_hi": "ऊपरी होंठ",
        "en": "Charismatic speaking, love for fine culinary arts, luxurious lifestyle, and warm hospitality.",
        "bn": "মনোমুগ্ধকর বাচনভঙ্গি, উত্তম খাদ্যানুরাগ, সৌখিন জীবনযাত্রা এবং অতিথিপরায়ণতা।",
        "hi": "मधुर वाणी, सुरुचिपूर्ण खानपान, विलासितापूर्ण जीवन और अतिथि सत्कार।",
        "male_auspicious": True,
        "female_auspicious": True,
    },
    "lower_lip": {
        "planet": "Moon (চন্দ্র)",
        "name_en": "Lower Lip Area (Adhara)",
        "name_bn": "নিচের ঠোঁট (অধর)",
        "name_hi": "निचला होंठ",
        "en": "Poetic sensibility, romantic allure, refined tastes, and fondness for travel.",
        "bn": "কাব্যিক ভাব, রোমান্টিক প্রকৃতি, সুকুমার বৃত্তিতে অনুরাগ এবং ভ্রমণপ্রিয়তা।",
        "hi": "काव्यमयी स्वभाव, सौंदर्य प्रेमी और यात्राओं का शौकीन।",
        "male_auspicious": True,
        "female_auspicious": True,
    },
    "chin_center": {
        "planet": "Saturn (শনি)",
        "name_en": "Chin Center (Chibuka)",
        "name_bn": "চিবুক (চিবুক কেন্দ্র)",
        "name_hi": "ठोड़ी (चिबुक)",
        "en": "Steadfast determination, immovable property accumulation, and stable respected longevity.",
        "bn": "দৃঢ় মানসিক শক্তি, স্থাবর সম্পত্তি সঞ্চয়, ধৈর্য এবং বয়সের সাথে মর্যাদা বৃদ্ধি।",
        "hi": "अटल संकल्प, अचल संपत्ति का संचय, संयम और वृद्धावस्था में सुख व सम्मान।",
        "male_auspicious": True,
        "female_auspicious": True,
    },
}


def detect_facial_moles(
    img_rgb: np.ndarray,
    landmarks_px: list[list[int]],
    gender: str = "male",
) -> list[dict[str, Any]]:
    """Detects facial moles/pigments using computer vision and interprets them."""
    if img_rgb is None or len(landmarks_px) < 468:
        return []

    h, w, _ = img_rgb.shape
    # Convert to LAB to decouple luminance from color channels
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    # Blur slightly to eliminate camera sensor noise
    blurred = cv2.GaussianBlur(l_channel, (5, 5), 0)

    # Face center and landmarks
    forehead_center = landmarks_px[10]  # Mid-forehead
    glabella = landmarks_px[9]
    nose_tip = landmarks_px[4]
    cheek_r = landmarks_px[205]
    cheek_l = landmarks_px[425]
    mouth_top = landmarks_px[0]
    mouth_bottom = landmarks_px[17]
    chin = landmarks_px[152]

    # Define facial ROIs to inspect for distinctive moles
    regions_to_test = [
        ("forehead_center", glabella, 24),
        ("forehead_right", [forehead_center[0] - int(w * 0.08), forehead_center[1] - int(h * 0.04)], 22),
        ("forehead_left", [forehead_center[0] + int(w * 0.08), forehead_center[1] - int(h * 0.04)], 22),
        ("cheek_right", cheek_r, 28),
        ("cheek_left", cheek_l, 28),
        ("nose_tip", nose_tip, 20),
        ("upper_lip", mouth_top, 16),
        ("lower_lip", mouth_bottom, 16),
        ("chin_center", chin, 22),
    ]

    detected_moles: list[dict[str, Any]] = []

    for zone_id, center_pt, radius_px in regions_to_test:
        cx, cy = int(center_pt[0]), int(center_pt[1])
        x1 = max(0, cx - radius_px)
        x2 = min(w, cx + radius_px)
        y1 = max(0, cy - radius_px)
        y2 = min(h, cy + radius_px)

        if x2 <= x1 or y2 <= y1:
            continue

        roi_l = blurred[y1:y2, x1:x2]
        if roi_l.size == 0:
            continue

        local_mean = float(np.mean(roi_l))
        local_min = float(np.min(roi_l))

        # Check for significant dark pigment contrast compared to surrounding skin
        contrast = local_mean - local_min
        if contrast > 32.0 and local_min < 110:
            # Find the minimum pixel coordinate
            min_loc = np.unravel_index(np.argmin(roi_l), roi_l.shape)
            mole_y = int(y1 + min_loc[0])
            mole_x = int(x1 + min_loc[1])

            rule = TIL_RULES.get(zone_id)
            if not rule:
                continue

            is_male = gender.lower() != "female"
            is_auspicious = rule["male_auspicious"] if is_male else rule["female_auspicious"]

            detected_moles.append({
                "zone_id": zone_id,
                "name_en": rule["name_en"],
                "name_bn": rule["name_bn"],
                "name_hi": rule["name_hi"],
                "planet": rule["planet"],
                "x": mole_x,
                "y": mole_y,
                "x_norm": round(mole_x / w, 4),
                "y_norm": round(mole_y / h, 4),
                "contrast": round(contrast, 1),
                "is_auspicious": is_auspicious,
                "interpretation_en": rule["en"],
                "interpretation_bn": rule["bn"],
                "interpretation_hi": rule["hi"],
            })

    # Sort descending by contrast/prominence, keep top 4
    detected_moles.sort(key=lambda m: m["contrast"], reverse=True)
    return detected_moles[:4]
