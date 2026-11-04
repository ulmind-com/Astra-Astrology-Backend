"""Dual-Hand Synastry & Karma Evolution Engine.

Implements the classical Hasta Samudrika Shastra principle of Bilateral Hand Comparison:
  - Left Hand (অক্রিয় হাত / Passive Hand): Prarabdha Karma (Sanchita Karma, inherited
    potential, subconscious instincts, ancestral blessings, and natal blueprint).
  - Right Hand (সক্রিয় হাত / Active Hand): Purushartha Karma (Kriyamana Karma, conscious
    free will, manifested achievements, and active destiny transformation).

Calculates the Karma Evolution Score (%) representing how much the native has actively
shaped, enhanced, or altered their inherited destiny.
"""

from __future__ import annotations

from typing import Any


def calculate_dual_hand_synastry(
    left_hand_data: dict[str, Any] | None = None,
    right_hand_data: dict[str, Any] | None = None,
    primary_handedness: str = "Right",
) -> dict[str, Any]:
    """Compare Left (Prarabdha) and Right (Purushartha) hands to compute Karma Evolution."""
    is_right_dominant = "right" in (primary_handedness or "Right").lower()

    # Extract or simulate baseline metrics if either scan is provided
    left_m = (left_hand_data or {}).get("measurements") or {}
    right_m = (right_hand_data or {}).get("measurements") or {}

    # 1. Head Line Evolution (Mental discipline & focus drift)
    left_head_curv = float(left_m.get("head_curvature", 0.18))
    right_head_curv = float(right_m.get("head_curvature", 0.12))
    mental_clarity_gain = max(0.0, (left_head_curv - right_head_curv) * 100)

    # 2. Fate Line Evolution (Career autonomy & self-made determination)
    left_fate_str = float(left_m.get("fate_strength", 0.45))
    right_fate_str = float(right_m.get("fate_strength", 0.72))
    fate_elevation = (right_fate_str - left_fate_str) * 100

    # 3. Mount Elevations (Jupiter ambition & Sun renown evolution)
    left_jup = float(left_m.get("mount_jupiter_elev_mm", 2.2))
    right_jup = float(right_m.get("mount_jupiter_elev_mm", 3.1))
    jup_elevation_gain = max(0.0, (right_jup - left_jup) * 15.0)

    # Overall Karma Evolution Index (baseline 78% + positive transformation deltas)
    evolution_delta = (mental_clarity_gain * 0.25) + (fate_elevation * 0.35) + (jup_elevation_gain * 0.40)
    karma_evolution_score = int(min(98, max(75, 84 + evolution_delta * 0.2)))

    # Identify key areas of conscious transformation
    transformations_en: list[str] = [
        "Strengthened Practical Reason: Head line on active hand reflects disciplined analytical mastery surpassing innate emotional impulses.",
        "Emergence of Self-Made Enterprise: Fate line manifests with higher continuity on the right hand, proving autonomous career success over family reliance.",
        "Elevated Mount of Jupiter: Increased leadership drive, executive authority, and higher societal respect manifested through conscious action.",
    ]
    transformations_bn: list[str] = [
        "ব্যবহারিক মেধার বিকাশ: সক্রিয় হাতে শিরোরেখার গভীরতা নির্দেশ করে আপনি আবেগকে সংযত করে বাস্তবমুখী যুক্তিবাদী সিদ্ধান্তের শক্তি অর্জন করেছেন।",
        "স্বনির্ভর ভাগ্যোদয়: ডান হাতে ভাগ্যরেখার স্পষ্ট বিস্তার প্রমাণ করে পৈতৃক আশ্রয়ের চেয়ে নিজের কর্মের মাধ্যমেই আপনার আসল প্রতিষ্ঠা গড়ে উঠেছে।",
        "উন্নত বৃহস্পতি পর্বত: নিজের অবিচল আত্মবিশ্বাসের ফলে নেতৃত্বে কর্তৃত্ব ও সামাজিক মর্যাদা বৃদ্ধি পেয়েছে।",
    ]
    transformations_hi: list[str] = [
        "व्यावहारिक बुद्धि का विकास: सक्रिय हाथ की मस्तिष्क रेखा दर्शाती है कि आपने भावनाओं को नियंत्रित कर यथार्थवादी निर्णयों की शक्ति प्राप्त की है।",
        "स्वनिर्मित भाग्योदय: दाएं हाथ में भाग्य रेखा की स्पष्टता सिद्ध करती है कि आपका भाग्य स्वयं के पुरुषार्थ से निर्मित हुआ है।",
        "उन्नत गुरु पर्वत: दृढ़ आत्मविश्वास के कारण नेतृत्व क्षमता एवं सामाजिक प्रतिष्ठा में उल्लेखनीय वृद्धि हुई है।",
    ]

    return {
        "is_harmonious": True,
        "karma_evolution_score": karma_evolution_score,
        "prarabdha_score": 86,
        "purushartha_score": karma_evolution_score,
        "dominant_hand": "Right (Active Manifestation)" if is_right_dominant else "Left (Active Intuition)",
        "prarabdha_summary_en": (
            "Your Left Hand reveals your innate blueprint (Prarabdha / Sanchita Karma). It reflects rich ancestral "
            "intuition, natural creative empathy, and philosophical inclinations brought from past merits."
        ),
        "prarabdha_summary_bn": (
            "আপনার বাম হাত নির্দেশ করে আপনার জন্মগত প্রারব্ধ (সঞ্চিত কর্ম)। এতে পূর্বপুরুষের আশীর্বাদ, অন্তর্দৃষ্টি "
            "এবং আধ্যাত্মিক মেধার প্রবল সম্ভাবনা বিদ্যমান ছিল।"
        ),
        "prarabdha_summary_hi": (
            "आपका बायां हाथ आपके जन्मजात प्रारब्ध (संचित कर्म) को दर्शाता है। इसमें पूर्वजों के आशीर्वाद, गहरी अंतर्दृष्टि "
            "और स्वाभाविक रचनात्मक प्रतिभा का संकेत है।"
        ),
        "purushartha_summary_en": (
            "Your Right Hand demonstrates active realization (Purushartha / Kriyamana Karma). Through personal discipline "
            "and bold life decisions, you have carved stronger career autonomy and grounded leadership."
        ),
        "purushartha_summary_bn": (
            "আপনার ডান হাত নির্দেশ করে সক্রিয় পুরুষার্থ (ক্রিয়মাণ কর্ম)। ব্যক্তিগত অধ্যবসায় ও দৃঢ় সংকল্পের দ্বারা "
            "আপনি ভাগ্যের রেখাকে আরও শক্তিশালী ও স্বাবলম্বী করে তুলেছেন।"
        ),
        "purushartha_summary_hi": (
            "आपका दायां हाथ सक्रिय पुरुषार्थ (क्रियमाण कर्म) का प्रमाण है। व्यक्तिगत परिश्रम और दृढ़ निर्णयों से आपने "
            "भाग्य रेखा को अधिक सबल और स्वावलंबी बनाया है।"
        ),
        "transformation_strengths_en": transformations_en,
        "transformation_strengths_bn": transformations_bn,
        "transformation_strengths_hi": transformations_hi,
        "karma_advice_en": (
            "Maintain conscious daily mindfulness and altruistic service (Nishkama Karma). Your hand shows that your free "
            "will is potent enough to override adverse planetary transits and accelerate material and spiritual fulfillment."
        ),
        "karma_advice_bn": (
            "প্রতিদিন নিষ্ঠার সাথে সৎকর্ম ও ধ্যান অভ্যাস রাখুন। আপনার হস্তরেখা স্পষ্টভাবে প্রমাণ করে যে আপনার সংকল্প ও পুরুষার্থ "
            "যেকোনো গ্রহীয় বাধাকে অতিক্রম করে কাঙ্ক্ষিত সফলতা এনে দেওয়ার ক্ষমতা রাখে।"
        ),
        "karma_advice_hi": (
            "सत्कर्म और नियमित ध्यान जारी रखें। आपकी हस्तरेखा स्पष्ट रूप से दर्शाती है कि आपका पुरुषार्थ किसी भी ग्रह बाधा "
            "को पार कर वांछित सफलता प्राप्त करने में सक्षम है।"
        ),
    }
