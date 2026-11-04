"""100-Year Life Timeline Map (Classical Samudrika & Mian Xiang 1-100 Age Grid).

Maps every year of human life onto a specific facial coordinate, palace, and planetary ruler.
Allows users to slide through ages 1 to 100 and receive year-specific life fortunes.
"""

from __future__ import annotations

from typing import Any


AGE_EPOCHS = [
    {
        "range": (1, 14),
        "zone_key": "ears",
        "name_en": "Ears (Karna Mandala) — Childhood & Ancestral Foundation",
        "name_bn": "কর্ণ মণ্ডল (শৈশব ও পূর্বপুরুষের সংস্কার)",
        "name_hi": "कर्ण मंडल (बचपन व पैतृक संस्कार)",
        "governor": "Moon / Mercury (চন্দ্র ও বুধ)",
        "focus_en": "Parental warmth, emotional immunity, early schooling, and inherited luck.",
        "focus_bn": "পিতা-মাতার স্নেহ, প্রাথমিক স্বাস্থ্য, প্রথম শিক্ষা এবং পারিবারিক ভাগ্য।",
        "focus_hi": "माता-पिता का स्नेह, प्रारंभिक स्वास्थ्य व पारिवारिक सुख।",
    },
    {
        "range": (15, 30),
        "zone_key": "forehead",
        "name_en": "Forehead (Lalata Mandala) — Youth, Higher Intellect & Early Career",
        "name_bn": "ললাট মণ্ডল (যৌবন, মেধা ও কর্মের সূচনা)",
        "name_hi": "ललाट मंडल (युवावस्था, उच्च बुद्धि व करियर की शुरुआत)",
        "governor": "Jupiter / Sun (বৃহস্পতি ও সূর্য)",
        "focus_en": "Academic honors, competitive exams, independent identity, and career launchpad.",
        "focus_bn": "উচ্চশিক্ষা, প্রতিযোগিতামূলক পরীক্ষায় সাফল্য, প্রথম কর্মসংস্থান এবং সমাজে প্রতিষ্ঠা।",
        "focus_hi": "उच्च शिक्षा, प्रतियोगी परीक्षाओं में सफलता और करियर की नींव।",
    },
    {
        "range": (31, 40),
        "zone_key": "eyebrows_eyes",
        "name_en": "Brows & Eyes (Netra Mandala) — Decisive Ambition, Passion & Marriage",
        "name_bn": "নেত্র ও ভ্রু মণ্ডল (উচ্চাকাঙ্ক্ষা, দাম্পত্য ও আত্মপ্রতিষ্ঠা)",
        "name_hi": "नेत्र व भौंह मंडल (महत्वाकांक्षा, विवाह व निर्णायक मोड़)",
        "governor": "Venus / Mars (শুক্র ও মঙ্গল)",
        "focus_en": "Marital partnership, decisive career pivot, personal property, and social magnetic rise.",
        "focus_bn": "বিবাহ ও দাম্পত্য সুখ, কর্মজীবনে বিশেষ পদোন্নতি, নতুন গৃহ ও সম্পর্কের পরিপক্বতা।",
        "focus_hi": "विवाह, व्यापार या नौकरी में बड़ा बदलाव और पारिवारिक विस्तार।",
    },
    {
        "range": (41, 50),
        "zone_key": "nose_cheeks",
        "name_en": "Nose & Cheeks (Nasa & Kapola) — Peak Wealth, Enterprise & Authority",
        "name_bn": "নাসা ও কপোল মণ্ডল (শীর্ষ অর্থভাগ্য, নেতৃত্ব ও সামাজিক কর্তৃত্ব)",
        "name_hi": "नासिका व गाल मंडल (शिखर धन, अधिकार व सामाजिक प्रभुत्व)",
        "governor": "Sun / Mercury (সূর্য ও বুধ)",
        "focus_en": "Peak asset accumulation, corporate leadership, public stature, and material stability.",
        "focus_bn": "জীবনের শ্রেষ্ঠ আর্থিক সঞ্চয়, কর্তৃত্বপূর্ণ অবস্থান, ব্যবসায়িক সাফল্য এবং মানসম্মান।",
        "focus_hi": "आर्थिक समृद्धि का शिखर, नेतृत्व और सामाजिक प्रतिष्ठा।",
    },
    {
        "range": (51, 60),
        "zone_key": "philtrum_mouth",
        "name_en": "Philtrum & Mouth (Mukha Mandala) — Family Legacy & Harvest of Efforts",
        "name_bn": "মুখ ও ওষ্ঠ মণ্ডল (কর্মফল প্রাপ্তি, পারিবারিক মর্যাদা ও উত্তরসূরি)",
        "name_hi": "मुख व होंठ मंडल (परिश्रम का फल, परिवार का सम्मान)",
        "governor": "Jupiter / Venus (বৃহস্পতি ও শুক্র)",
        "focus_en": "Children's success, mentoring younger generations, inner harmony, and health discipline.",
        "focus_bn": "সন্তান-সন্ততির অগ্রগতি, পরবর্তী প্রজন্মকে পথপ্রদর্শন, গৃহশান্তি এবং স্বাস্থ্য সচেতনতা।",
        "focus_hi": "संतान की उन्नति, सामाजिक सम्मान और स्वास्थ्य पर ध्यान।",
    },
    {
        "range": (61, 100),
        "zone_key": "chin_jaw",
        "name_en": "Chin & Jawline (Chibuka Mandala) — Wisdom, Spiritual Peace & Longevity",
        "name_bn": "চিবুক ও চোয়াল মণ্ডল (প্রজ্ঞা, পরম আধ্যাত্মিক শান্তি ও দীর্ঘায়ু)",
        "name_hi": "चिबुक व जबड़ा मंडल (प्रज्ञा, आध्यात्मिक शांति व दीर्घायु)",
        "governor": "Saturn / Ketu (শনি ও কেতু)",
        "focus_en": "Spiritual fulfillment, ancestral respect, lasting legacy, and serene peace of mind.",
        "focus_bn": "আধ্যাত্মিক তৃপ্তি, গুরুমর্যাদা, পারিবারিক শ্রদ্ধা এবং শান্তিময় দীর্ঘ জীবন।",
        "focus_hi": "आध्यात्मिक संतोष, मान-सम्मान और शांत दीर्घायु जीवन।",
    },
]


def get_timeline_forecast_for_age(
    age: int,
    measurements: dict[str, float],
    gender: str = "male",
) -> dict[str, Any]:
    """Returns the precise facial coordinate, governor planet, and astrological prediction for a given age."""
    clamped_age = max(1, min(100, int(age)))

    epoch = next(
        (e for e in AGE_EPOCHS if e["range"][0] <= clamped_age <= e["range"][1]),
        AGE_EPOCHS[-1],
    )

    # Calculate normalized coordinate on facial canvas based on age
    # Forehead (y ~ 0.15 - 0.32), Eyes/Brows (y ~ 0.33 - 0.45), Nose (y ~ 0.46 - 0.60), Mouth (y ~ 0.62 - 0.75), Chin (y ~ 0.76 - 0.92)
    if clamped_age <= 14:
        # Ears (side coordinates)
        side_x = 0.18 if clamped_age % 2 == 1 else 0.82
        norm_x, norm_y = side_x, 0.42 + (clamped_age / 14.0) * 0.15
    elif clamped_age <= 30:
        # Forehead (top down to brow)
        progress = (clamped_age - 15) / 15.0
        norm_x = 0.50 + ((clamped_age % 5) - 2) * 0.08
        norm_y = 0.16 + progress * 0.16
    elif clamped_age <= 40:
        # Brows & Eyes
        progress = (clamped_age - 31) / 9.0
        norm_x = 0.35 + (clamped_age % 3) * 0.15
        norm_y = 0.34 + progress * 0.10
    elif clamped_age <= 50:
        # Nose & Cheeks
        progress = (clamped_age - 41) / 9.0
        norm_x = 0.50 if clamped_age in (41, 44, 45, 48) else (0.32 if clamped_age % 2 == 0 else 0.68)
        norm_y = 0.46 + progress * 0.14
    elif clamped_age <= 60:
        # Philtrum & Mouth
        progress = (clamped_age - 51) / 9.0
        norm_x = 0.50 + ((clamped_age % 3) - 1) * 0.08
        norm_y = 0.62 + progress * 0.12
    else:
        # Chin & Jaw
        progress = min(1.0, (clamped_age - 61) / 20.0)
        norm_x = 0.50 + ((clamped_age % 4) - 1.5) * 0.09
        norm_y = 0.76 + progress * 0.15

    # Specific predictions based on milestone ages
    year_prediction_en = f"Year {clamped_age} activates your {epoch['name_en'].split('—')[0].strip()}. Energy is ripe for consolidation, steady discipline, and alignment with your true goals."
    year_prediction_bn = f"{clamped_age} বছর বয়সে আপনার মুখের {epoch['name_bn'].split('(')[0].strip()} সক্রিয় হচ্ছে। এই সময়ে আপনার মানসিক সংকল্প ও কর্মে বিশেষ একাগ্রতা সাফল্য আনবে।"
    year_prediction_hi = f"{clamped_age} वर्ष की आयु में आपके मुख का {epoch['name_hi'].split('(')[0].strip()} सक्रिय होता है। यह समय धैर्य और सही दिशा में प्रयास करने का है।"

    if clamped_age == 28:
        year_prediction_en = "Age 28 is the 'Life Palace' (Trikuti): Major turning point in destiny, public recognition, moral maturity, and opening of new career doors."
        year_prediction_bn = "২৮ বছর বয়স হলো 'জীবন প্রাসাদ' (ত্রিকূটী): ভাগ্যোন্নতির প্রধান সন্ধিক্ষণ, সামাজিক প্রতিষ্ঠা এবং নতুন গুরুত্বপূর্ণ কর্মের সূচনা।"
        year_prediction_hi = "28 वर्ष की आयु 'भाग्य द्वार' (त्रिकुटी) मानी जाती है: जीवन का निर्णायक मोड़, सामाजिक प्रतिष्ठा और नए करियर के द्वार खुलते हैं।"
    elif clamped_age in (31, 32):
        year_prediction_en = "Activation of the Brow Ridge (Dharma): High ambition, professional breakthrough, and auspicious alignment for partnerships."
        year_prediction_bn = "ভ্রু রেখার শক্তি সক্রিয় (ধর্ম ও পরাক্রম): কর্মক্ষেত্রে বিশেষ বিস্তার, অংশীদারিত্বে লাভ এবং ব্যক্তিগত সম্পর্কের স্থায়িত্ব।"
        year_prediction_hi = "भौंहों का प्रभाव (धर्म व पराक्रम): कार्यक्षेत्र में बड़ी सफलता और साझेदारी के लिए अत्यंत शुभ समय।"
    elif clamped_age == 41:
        year_prediction_en = "Bridge of the Nose (San Gen / Wealth Root): Foundation of mid-life assets, enterprise expansion, and consolidated leadership."
        year_prediction_bn = "নাসামূলের সূচনা (অর্থ প্রাসাদ): মধ্য বয়সের আর্থিক ভিত্তি মজবুত হওয়া, বড় বিনিয়োগ ও সামাজিক কর্তৃত্ব প্রতিষ্ঠা।"
        year_prediction_hi = "नासिका मूल (धन व प्रभाव): मध्य आयु में आर्थिक नींव मजबूत होना और बड़े निर्णयों में सफलता।"
    elif clamped_age == 48:
        year_prediction_en = "Nose Tip (Zhun Tou / Treasury Palace): Peak harvest of financial accumulation and material fruition."
        year_prediction_bn = "নাসা চূড়া (কুবের ভাণ্ডার): জীবনের শ্রেষ্ঠ সঞ্চয়যোগ এবং দীর্ঘদিনের পরিশ্রমের সর্বোচ্চ ফলপ্রাপ্তি।"
        year_prediction_hi = "नासिका अग्र (कुबेर भंडार): जीवन में धन संचय और दीर्घकालिक प्रयासों का सर्वोत्तम फल मिलने का समय।"

    return {
        "age": clamped_age,
        "zone_key": epoch["zone_key"],
        "epoch_name_en": epoch["name_en"],
        "epoch_name_bn": epoch["name_bn"],
        "epoch_name_hi": epoch["name_hi"],
        "governor_planet": epoch["governor"],
        "norm_x": round(norm_x, 4),
        "norm_y": round(norm_y, 4),
        "focus_en": epoch["focus_en"],
        "focus_bn": epoch["focus_bn"],
        "focus_hi": epoch["focus_hi"],
        "prediction_en": year_prediction_en,
        "prediction_bn": year_prediction_bn,
        "prediction_hi": year_prediction_hi,
    }
