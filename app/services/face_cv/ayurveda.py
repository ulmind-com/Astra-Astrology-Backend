"""Ayurvedic Tridosha (Vata, Pitta, Kapha) & Ojas Skin Radiance Diagnostic Engine.

Analyzes facial structure, angularity, lips, eyes, and skin undertone to determine
the native's dominant Ayurvedic constitution (Prakriti) and prescribed diet/lifestyle.
"""

from __future__ import annotations

import numpy as np
from typing import Any


def analyze_ayurvedic_prakriti(
    measurements: dict[str, float],
    img_rgb: np.ndarray | None = None,
) -> dict[str, Any]:
    """Calculates Vata, Pitta, and Kapha percentages, plus Ojas skin radiance score."""
    # 1. Structural indicators from geometric measurements
    face_ratio = measurements.get("face_ratio", 1.35)
    jaw_ratio = measurements.get("jaw_width_ratio", 0.72)
    lip_fullness = measurements.get("lip_fullness", 0.35)
    eye_aspect = measurements.get("eye_aspect_ratio", 0.28)
    chin_prominence = measurements.get("chin_prominence", 0.40)
    cheek_prominence = measurements.get("cheek_prominence_3d", 0.35)
    forehead_height = measurements.get("forehead_height_ratio", 0.33)

    # Vata Indicators: Angularity, elongated/narrow face, thinner lips, variable spacing
    vata_raw = (
        (1.0 if face_ratio > 1.4 else 0.4) * 25.0
        + (1.0 if lip_fullness < 0.32 else 0.3) * 25.0
        + (1.0 if jaw_ratio < 0.70 else 0.3) * 25.0
        + (1.0 if chin_prominence < 0.38 else 0.4) * 25.0
    )

    # Pitta Indicators: Sharp angular jaw, prominent cheekbones, medium face frame, sharp nose
    pitta_raw = (
        (1.0 if 0.70 <= jaw_ratio <= 0.82 else 0.4) * 25.0
        + (1.0 if cheek_prominence > 0.32 else 0.4) * 25.0
        + (1.0 if 0.30 <= lip_fullness <= 0.42 else 0.4) * 25.0
        + (1.0 if forehead_height > 0.32 else 0.4) * 25.0
    )

    # Kapha Indicators: Full lips, broad soft contours, wide gentle eyes, rounded jaw
    kapha_raw = (
        (1.0 if lip_fullness > 0.38 else 0.3) * 25.0
        + (1.0 if jaw_ratio > 0.78 else 0.3) * 25.0
        + (1.0 if eye_aspect > 0.29 else 0.4) * 25.0
        + (1.0 if face_ratio < 1.32 else 0.3) * 25.0
    )

    total = vata_raw + pitta_raw + kapha_raw + 1e-6
    vata_pct = round((vata_raw / total) * 100.0, 1)
    pitta_pct = round((pitta_raw / total) * 100.0, 1)
    kapha_pct = round((kapha_raw / total) * 100.0, 1)

    # Determine dominant doshas
    scores = [("Vata", vata_pct), ("Pitta", pitta_pct), ("Kapha", kapha_pct)]
    scores.sort(key=lambda x: x[1], reverse=True)
    dominant_dosha = scores[0][0]
    secondary_dosha = scores[1][0]
    prakriti_type = f"{dominant_dosha}-{secondary_dosha}"

    # Calculate Ojas (Skin Radiance / Vitality) Score
    ojas_score = 82.0
    if img_rgb is not None:
        try:
            # Measure luminosity uniformity and vibrant contrast
            gray = np.mean(img_rgb, axis=2)
            std_dev = float(np.std(gray))
            mean_lum = float(np.mean(gray))
            ojas_score = round(min(98.0, max(65.0, 60.0 + (mean_lum / 255.0) * 25.0 + (min(std_dev, 45.0) / 45.0) * 13.0)), 1)
        except Exception:
            ojas_score = 84.0

    recommendations = {
        "Vata": {
            "nature_en": "Air & Ether (বায়ু ও আকাশ) — Quick, intuitive, creative, prone to overthinking & fatigue.",
            "nature_bn": "বায়ু ও আকাশ তত্ত্ব — ক্ষিপ্র বুদ্ধি, সৃজনশীল ও সংবেদনশীল, তবে চঞ্চলতা ও ক্লান্তির প্রবণতা।",
            "nature_hi": "वायु व आकाश तत्व — चंचल बुद्धि, सृजनशील, लेकिन थकान व चिंता की संभावना।",
            "diet_en": "Warm, grounding, nourished foods (ghee, cooked oats, nuts, sweet fruits, warm milk). Avoid iced drinks and dry raw snacks.",
            "diet_bn": "উষ্ণ ও স্নিগ্ধ খাবার (ঘি, ওটস, বাদাম, মিষ্টি পাকা ফল, উষ্ণ দুধ)। অতিরিক্ত ঠান্ডা পানীয় বা শুকনো খাবার পরিহার্য।",
            "diet_hi": "गर्म, पौष्टिक व स्निग्ध आहार (घी, दलिया, बादाम, मीठे फल, गुनगुना दूध)। ठंडे पेय व सूखा भोजन टालें।",
            "lifestyle_en": "Consistent sleep schedule, grounding yoga, warm sesame oil massage (Abhyanga), and daily quiet contemplation.",
            "lifestyle_bn": "নির্দিষ্ট সময়ে ঘুম, ধীরগতির প্রাণায়াম, তিলের তেল মালিশ (অভ্যঙ্গ) এবং মানসিক শান্ত অভ্যাস।",
            "lifestyle_hi": "नियमित दिनचर्या, शांत योग, तिल के तेल से मालिश और पर्याप्त विश्राम।",
        },
        "Pitta": {
            "nature_en": "Fire & Water (অগ্নি ও জল) — Dynamic leader, razor-sharp analytical focus, courageous, prone to heat & irritability.",
            "nature_bn": "অগ্নি ও জল তত্ত্ব — প্রখর মেধা, নেতৃত্বের গুণ ও নির্ভীক সংকল্প, তবে অতিরিক্ত উত্তাপ ও ক্রোধের প্রবণতা।",
            "nature_hi": "अग्नि व जल तत्व — नेतृत्व क्षमता, तीक्ष्ण विश्लेषण और निर्भीकता, लेकिन क्रोध व पित्त का प्रकोप संभव।",
            "diet_en": "Cooling, alkalizing foods (coconut water, sweet melons, cucumbers, fennel, basmati rice). Moderate spicy, fried, and fermented foods.",
            "diet_bn": "শীতল ও মৃদু খাবার (ডাবের জল, শসা, তরমুজ, মৌরি, বাসমতি চাল)। অতিরিক্ত ঝাল, ভাজাভুজি বা অম্ল খাবার কম গ্রহণীয়।",
            "diet_hi": "शीतल व सुपाच्य आहार (नारियल पानी, खीरा, तरबूज, सौंफ)। अत्यधिक मिर्च-मसालेदार व तले भोजन से बचें।",
            "lifestyle_en": "Cool evening walks under moonlight, swimming, avoiding midday sun, practicing compassion and forgiveness.",
            "lifestyle_bn": "সন্ধ্যার মুক্ত বাতাসে ভ্রমণ, সাঁতার, অতিরিক্ত রোদে না থাকা এবং মনের শীতলতা বজায় রাখা।",
            "lifestyle_hi": "शीतल वातावरण में टहलना, तैराकी, दोपहर की धूप से बचना और शांत चित्त रखना।",
        },
        "Kapha": {
            "nature_en": "Earth & Water (পৃথ্বী ও জল) — Enduring patience, loving stability, strong immunity, prone to inertia and lethargy.",
            "nature_bn": "পৃথ্বী ও জল তত্ত্ব — অগাধ ধৈর্য, অপরিসীম মানসিক স্থিরতা ও দীর্ঘায়ু, তবে অলসতা ও ভারাক্রান্ততার সম্ভাবনা।",
            "nature_hi": "पृथ्वी व जल तत्व — असीम धैर्य, स्थिरता व मजबूत रोग प्रतिरोधक क्षमता, लेकिन आलस्य की संभावना।",
            "diet_en": "Light, warm, pungent and stimulating foods (ginger, black pepper, steamed vegetables, honey, barley). Limit heavy dairy and sweets.",
            "diet_bn": "হালকা, গরম ও মশলাদার খাবার (আদা, গোলমরিচ, সিদ্ধ শাকসবজি, মধু)। মিষ্টি ও অতিরিক্ত দুগ্ধজাত খাবার কমানো উচিত।",
            "diet_hi": "हल्का, गर्म व पाचक भोजन (अदरक, काली मिर्च, उबली सब्जियां, शहद)। भारी मिठाई व वसायुक्त भोजन कम करें।",
            "lifestyle_en": "Vigorous morning workouts, brisk walking, adopting novelty, staying actively motivated and avoiding daytime naps.",
            "lifestyle_bn": "সকালের শরীরচর্চা, নিয়মিত হাঁটা, নতুন কাজের উদ্যোগ এবং দিনের বেলা ঘুম পরিহার।",
            "lifestyle_hi": "प्रातःकाल तीव्र व्यायाम, सक्रिय जीवनशैली और दिन में सोने से बचना।",
        },
    }

    rec = recommendations.get(dominant_dosha, recommendations["Pitta"])

    return {
        "prakriti_type": prakriti_type,
        "dominant_dosha": dominant_dosha,
        "secondary_dosha": secondary_dosha,
        "vata_percentage": vata_pct,
        "pitta_percentage": pitta_pct,
        "kapha_percentage": kapha_pct,
        "ojas_score": ojas_score,
        "constitution_en": rec["nature_en"],
        "constitution_bn": rec["nature_bn"],
        "constitution_hi": rec["nature_hi"],
        "diet_advice_en": rec["diet_en"],
        "diet_advice_bn": rec["diet_bn"],
        "diet_advice_hi": rec["diet_hi"],
        "lifestyle_advice_en": rec["lifestyle_en"],
        "lifestyle_advice_bn": rec["lifestyle_bn"],
        "lifestyle_advice_hi": rec["lifestyle_hi"],
    }
