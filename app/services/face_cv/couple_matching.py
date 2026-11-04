"""Couple Face Reading (Mukha Milan & Facial Synastry) Engine.

Evaluates bilateral physiognomic and Pancha Mahabhuta complementarity between two partners
based on classical Samudrika Shastra rules of union, temperament, and mutual destiny.
"""

from __future__ import annotations

from typing import Any


def calculate_couple_face_compatibility(
    partner_a_measurements: dict[str, float],
    partner_b_measurements: dict[str, float],
    partner_a_name: str = "Partner 1",
    partner_b_name: str = "Partner 2",
) -> dict[str, Any]:
    """Calculates mutual compatibility score and relationship dynamics between two faces."""
    # Symmetry and harmonious balance
    sym_a = partner_a_measurements.get("symmetry_index", 0.90)
    sym_b = partner_b_measurements.get("symmetry_index", 0.90)

    # Lip fullness (Warmth & verbal communication harmony)
    lip_a = partner_a_measurements.get("lip_fullness", 0.35)
    lip_b = partner_b_measurements.get("lip_fullness", 0.35)
    lip_harmony = 1.0 - min(0.3, abs(lip_a - lip_b))

    # Face ratio (Grounding vs Agility balance)
    fr_a = partner_a_measurements.get("face_ratio", 1.35)
    fr_b = partner_b_measurements.get("face_ratio", 1.35)
    ratio_complementarity = 0.85 + (0.10 if abs(fr_a - fr_b) < 0.15 else 0.05)

    # Base compatibility calculation (80% to 96%)
    base_score = 75.0 + (sym_a * 10.0) + (sym_b * 10.0) + (lip_harmony * 8.0)
    overall_score = round(min(98.0, max(72.0, base_score)), 1)

    # Relationship traits
    strengths_en = [
        "Natural mutual empathy: Eye and brow balance indicates high emotional understanding.",
        "Complementary financial approach: Balanced jaw and nasal contours promote joint asset stability.",
        "Lifelong companionship resonance: Compatible tri-zone longevity markers.",
    ]
    strengths_bn = [
        "স্বাভাবিক পারস্পরিক সহমর্মিতা: দৃষ্টি ও ভ্রু রেখার সামঞ্জস্য মনের গভীর ভাব বিনিময়ে সহায়ক।",
        "আর্থিক ও সাংসারিক ভারসাম্য: চোয়াল ও নাসিকার গঠন যৌথ সমৃদ্ধি ও স্থায়িত্ব নির্দেশ করে।",
        "দীর্ঘস্থায়ী দাম্পত্য বন্ধন: মুখের ত্রিকাল মণ্ডল পরস্পরের পরিপূরক ও সৌভাগ্যবর্ধক।",
    ]
    strengths_hi = [
        "पारस्परिक समझ व स्नेह: आंखों और भौंहों का संतुलन उच्च भावनात्मक तालमेल दर्शाता है।",
        "आर्थिक स्थिरता: नासिका व जबड़े की बनावट संयुक्त संपत्ति व समृद्धि का संकेत है।",
        "सुदीर्घ दांपत्य सुख: चेहरे के तीनों काल मंडल एक-दूसरे के अनुकूल हैं।",
    ]

    advice_en = "Cultivate shared spiritual rituals and open conversations during key career transitions to amplify harmony."
    advice_bn = "জীবনের বড় সিদ্ধান্তের সময় পারস্পরিক পরামর্শ এবং একসাথে আধ্যাত্মিক চর্চা দাম্পত্য সুখকে বহুগুণ বাড়িয়ে তুলবে।"
    advice_hi = "पारस्परिक संवाद बनाए रखें और महत्वपूर्ण निर्णयों में एक-दूसरे के सुझाव को प्राथमिकता दें।"

    return {
        "overall_compatibility_score": overall_score,
        "is_harmonious": overall_score >= 80.0,
        "communication_harmony_score": round(lip_harmony * 100.0, 1),
        "destiny_alignment_score": round(ratio_complementarity * 100.0, 1),
        "strengths_en": strengths_en,
        "strengths_bn": strengths_bn,
        "strengths_hi": strengths_hi,
        "harmonizing_advice_en": advice_en,
        "harmonizing_advice_bn": advice_bn,
        "harmonizing_advice_hi": advice_hi,
    }
