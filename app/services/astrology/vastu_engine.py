"""16-Zone, 32-Pada Vastu Shastra Calculation and Audit Engine.

Derived directly from Client's Resource Documents:
- Rahul Pandat PDFs / Vastu Rules / 8d3ab98adef23b71.pdf (Deepak Rajput Advanced Vastu, 55 pp)
- Rahul Pandat PDFs / Vastu Rules / 6ab2d85272f5ea7e.pdf (120 Vastu Tips & Miraculous Remedies)
- Rahul Pandat PDFs / Vastu Rules / 606123a3cc7abcd8.pdf (Essentials of Vastu, 34 pp)
- Rahul Pandat PDFs / Vastu Rules / a0df3a72402320df.pdf (16 Zones, Organs, Pathologies, 115 pp)
- Rahul Pandat PDFs / Vastu Rules / fdceabd8c2a79bfd.pdf (Energy Fields & Grids, 130 pp)
"""

from typing import Any
from app.schemas.vastu import (
    AstroVastuRule,
    AyadiCalculationResponse,
    MedicalVastuItem,
    PadaInfo,
    PlacementEvaluationItem,
    VastuAuditResponse,
    VastuRemedyItem,
    VastuZoneInfo,
)

# ---------------------------------------------------------------------------
# 32 Padas Definition (11.25° each, N5 centered at 0.0° True North)
# ---------------------------------------------------------------------------
# N5 spans 354.375° to 5.625°
# Quadrant structure: North (N1-N8), East (E1-E8), South (S1-S8), West (W1-W8)

PADA_DEFINITIONS: list[dict[str, Any]] = [
    # North Quadrant
    {"pada_id": "N1", "quadrant": "North", "deity": "Roga (রোগ)", "center": 309.375, "auspicious": False, "effects": "দীর্ঘস্থায়ী অসুস্থতা, ঈর্ষা ও শত্রুভীতি বৃদ্ধি পায়।", "challenge": "অসুস্থতা ও দুর্বল জীবনীশক্তি"},
    {"pada_id": "N2", "quadrant": "North", "deity": "Naga (নাগ)", "center": 320.625, "auspicious": False, "effects": "উদ্বেগ, আত্মীয়দের সাথে বৈরিতা ও মানসিক অস্থিরতা।", "challenge": "মানসিক ক্লেশ ও সম্পর্কের টানাপোড়েন"},
    {"pada_id": "N3", "quadrant": "North", "deity": "Mukhya (মুখ্য)", "center": 331.875, "auspicious": True, "effects": "বিশাল ধনলাভ, বাণিজ্যিক সমৃদ্ধি ও নতুন অর্থপ্রবাহের পথ উন্মোচন।", "challenge": "অতি-উচ্চাকাঙ্ক্ষা নিয়ন্ত্রণ"},
    {"pada_id": "N4", "quadrant": "North", "deity": "Bhallat (ভল্লাট)", "center": 343.125, "auspicious": True, "effects": "পূর্বপুরুষের সম্পত্তি লাভ, প্রচুর সঞ্চয় ও অক্ষয় ঐশ্বর্য।", "challenge": "সম্পদের সদ্ব্যবহার"},
    {"pada_id": "N5", "quadrant": "North", "deity": "Soma (সোম / কুবের)", "center": 354.375, "auspicious": False, "effects": "পারিবারিক টানাপোড়েন, সন্তানহীনতার চিন্তা ও আবেগীয় সংকট।", "challenge": "আবেগীয় বিচ্ছিন্নতা"},
    {"pada_id": "N6", "quadrant": "North", "deity": "Bhujanga (ভুজঙ্গ)", "center": 5.625, "auspicious": False, "effects": "পুত্রসন্তানের সাথে মনোমালিন্য, অহংকার ও আত্মঘাতী সিদ্ধান্ত।", "challenge": "পারিবারিক অসহযোগিতা"},
    {"pada_id": "N7", "quadrant": "North", "deity": "Aditi (অদিতি)", "center": 16.875, "auspicious": False, "effects": "গৃহের নারীদের মধ্যে অস্থিরতা ও অতিরিক্ত দুশ্চিন্তা।", "challenge": "নারীদের মানসিক চাপ"},
    {"pada_id": "N8", "quadrant": "North", "deity": "Diti (দিতি)", "center": 28.125, "auspicious": False, "effects": "অতিরিক্ত ব্যয়, ঋণগ্রস্ততা ও আয়ের তুলনায় খরচের আধিক্য।", "challenge": "অর্থ অপচয়"},

    # East Quadrant
    {"pada_id": "E1", "quadrant": "East", "deity": "Shikhi (শিখী / অগ্নি)", "center": 39.375, "auspicious": False, "effects": "অগ্নিকাণ্ড বা বৈদ্যুতিক বিপদের ঝুঁকি, আর্থিক ক্ষতি।", "challenge": "আকস্মিক দুর্যোগ"},
    {"pada_id": "E2", "quadrant": "East", "deity": "Parjanya (পর্জন্য)", "center": 50.625, "auspicious": False, "effects": "কন্যা সন্তানের স্বাস্থ্য সমস্যা ও আর্থিক অনটন।", "challenge": "পারিবারিক ব্যয়বৃদ্ধি"},
    {"pada_id": "E3", "quadrant": "East", "deity": "Jayanta (জয়ন্ত)", "center": 61.875, "auspicious": True, "effects": "বিজয়, রাজকীয় সম্মান, সামাজিক গ্রহণযোগ্যতা ও সৌভাগ্য।", "challenge": "সততা বজায় রাখা"},
    {"pada_id": "E4", "quadrant": "East", "deity": "Indra (ইন্দ্র)", "center": 73.125, "auspicious": True, "effects": "সরকারি সহযোগিতা, উচ্চপদস্থ কর্মকর্তাদের কৃপা ও প্রভাবশালী খ্যাতি।", "challenge": "অহংকার পরিহার"},
    {"pada_id": "E5", "quadrant": "East", "deity": "Surya (সূর্য)", "center": 84.375, "auspicious": False, "effects": "অতিরিক্ত আত্মম্ভরিতা, ক্রোধ ও পরিবারের সদস্যদের মধ্যে বিরোধ।", "challenge": "উগ্র মনোভাব"},
    {"pada_id": "E6", "quadrant": "East", "deity": "Satya (সত্য)", "center": 95.625, "auspicious": False, "effects": "বিশ্বাসভঙ্গ, প্রতিশ্রুতি পালনে ব্যর্থতা ও আইনি জটিলতা।", "challenge": "মিথ্যা অপবাদ"},
    {"pada_id": "E7", "quadrant": "East", "deity": "Bhrisha (ভৃশ)", "center": 106.875, "auspicious": False, "effects": "ক্রোধোন্মাদনা, উগ্র আচরণ ও আত্মীয়দের সাথে বিচ্ছেদ।", "challenge": "হঠকারিতা"},
    {"pada_id": "E8", "quadrant": "East", "deity": "Antariksha (অন্তরীক্ষ)", "center": 118.125, "auspicious": False, "effects": "চুরি, প্রতারণা ও আকস্মিক আর্থিক ডাকাতি।", "challenge": "প্রতারণা ঝুঁকি"},

    # South Quadrant
    {"pada_id": "S1", "quadrant": "South", "deity": "Anila (অনিল / বায়ু)", "center": 129.375, "auspicious": False, "effects": "সন্তান প্রসবের জটিলতা, ব্যবসায় মন্দা ও তীব্র হতাশা।", "challenge": "উদ্যমহীনতা"},
    {"pada_id": "S2", "quadrant": "South", "deity": "Pusna (পূষা)", "center": 140.625, "auspicious": False, "effects": "পরাধীনতা, দাসত্বতুল্য চাকরি ও কর্মক্ষেত্রে অবমূল্যায়ন।", "challenge": "স্বাধীনতার অভাব"},
    {"pada_id": "S3", "quadrant": "South", "deity": "Vitatha (বিতথ)", "center": 151.875, "auspicious": True, "effects": "উদ্যোক্তা হিসেবে বিপুল লাভ, নির্ভীক কর্মশক্তি ও প্রতিপত্তি।", "challenge": "অসাধু পথ পরিহার"},
    {"pada_id": "S4", "quadrant": "South", "deity": "Gruhakshat (গৃহক্ষত)", "center": 163.125, "auspicious": True, "effects": "সন্তানদের সার্বিক সমৃদ্ধি, পারিবারিক আনন্দ ও সামাজিক মর্যাদা।", "challenge": "পারিবারিক দায়িত্ব"},
    {"pada_id": "S5", "quadrant": "South", "deity": "Yama (যম)", "center": 174.375, "auspicious": False, "effects": "চরম সংকট — অকাল মৃত্যুভীতি, দীর্ঘস্থায়ী রোগ ও পুলিশি ঝামেলা।", "challenge": "মরণসম সংকট"},
    {"pada_id": "S6", "quadrant": "South", "deity": "Gandharva (গন্ধর্ব)", "center": 185.625, "auspicious": False, "effects": "অপমান, আর্থিক দেউলিয়াত্ব ও সামাজিক অপযশ।", "challenge": "সম্মানহানি"},
    {"pada_id": "S7", "quadrant": "South", "deity": "Bhrangaraj (ভৃঙ্গরাজ)", "center": 196.875, "auspicious": False, "effects": "কঠোর শ্রমেও চরম ব্যর্থতা, সঞ্চিত অর্থ নাশ।", "challenge": "শ্রমে ব্যর্থতা"},
    {"pada_id": "S8", "quadrant": "South", "deity": "Mriga (মৃগ)", "center": 208.125, "auspicious": False, "effects": "পুত্রসন্তানের রোগ, পরিবারের শক্তির অবক্ষয় ও দুর্বল প্রতিরোধ।", "challenge": "শক্তিহীনতা"},

    # West Quadrant
    {"pada_id": "W1", "quadrant": "West", "deity": "Pitri (পিতৃ / নৈঋত)", "center": 219.375, "auspicious": False, "effects": "পিতৃপুরুষের অসন্তোষ, দারিদ্র্য ও দীর্ঘস্থায়ী পারিবারিক সংকট।", "challenge": "পিতৃ দোষ"},
    {"pada_id": "W2", "quadrant": "West", "deity": "Dauvarika (দৌবারিক)", "center": 230.625, "auspicious": False, "effects": "সম্পর্কের অস্থিতিশীলতা, অতিরিক্ত সন্দেহ ও দাম্পত্য দূরত্ব।", "challenge": "অবিশ্বাস"},
    {"pada_id": "W3", "quadrant": "West", "deity": "Sugriva (সুগ্রীব)", "center": 241.875, "auspicious": True, "effects": "দ্রুত বস্তুগত সমৃদ্ধি, ব্যবসায়িক সম্প্রসারণ ও নির্ভরযোগ্য মিত্রলাভ।", "challenge": "বিনয়ী থাকা"},
    {"pada_id": "W4", "quadrant": "West", "deity": "Pushpadanta (পুষ্পদন্ত)", "center": 253.125, "auspicious": True, "effects": "অটল ধনসম্পদ, সামাজিক প্রতিপত্তি ও কন্যা সন্তানের সৌভাগ্য।", "challenge": "ধনের অহংকার"},
    {"pada_id": "W5", "quadrant": "West", "deity": "Varuna (বরুণ)", "center": 264.375, "auspicious": False, "effects": "অতিরিক্ত প্রত্যাশা, হতাশা ও মাদকাসক্তির ঝুঁকি।", "challenge": "আকাঙ্ক্ষার অপূর্ণতা"},
    {"pada_id": "W6", "quadrant": "West", "deity": "Asura (অসুর)", "center": 275.625, "auspicious": False, "effects": "আইনি নোটিস, ট্যাক্স জটিলতা ও সরকারি দণ্ডাদেশ।", "challenge": "রাজদণ্ড"},
    {"pada_id": "W7", "quadrant": "West", "deity": "Shesha (শোষ)", "center": 286.875, "auspicious": False, "effects": "শারীরিক দুর্বলতা, বিষণ্নতা ও জীবনীশক্তির অবক্ষয়।", "challenge": "হতাশা ও ক্লান্তি"},
    {"pada_id": "W8", "quadrant": "West", "deity": "Papadayakshma (পাপযক্ষ্মা)", "center": 298.125, "auspicious": False, "effects": "অনৈতিক কাজে লিপ্ত হওয়া, গুপ্ত রোগ ও সামাজিক কলঙ্ক।", "challenge": "অসৎ প্রবৃত্তি"},
]


# ---------------------------------------------------------------------------
# 16 Directional Zones Definitions
# ---------------------------------------------------------------------------

ZONE_METADATA: dict[str, dict[str, Any]] = {
    "N": {
        "name": "North (উত্তর)", "name_bn": "উত্তর দিক (কুবের স্থান)", "center": 0.0,
        "element": "Water", "element_bn": "জল তত্ত্ব",
        "organs": "কিডনি, মূত্রাশয় ও কান", "dosha": "Kapha (কফ)",
        "life_aspect": "নতুন সুযোগ, অর্থ উপার্জন ও কর্মসংস্থান",
        "ideal": ["প্রবেশদ্বার (N3, N4)", "আন্ডারগ্রাউন্ড ওয়াটার", "মানিব্যাগ/লকার", "লিভিং রুম"],
        "prohibited": ["রান্নাঘর (অগ্নি)", "টয়লেট", "ওভারহেড ভারী ট্যাঙ্ক", "লাল/গোলাপি রঙ"],
        "self_colors": ["Blue", "Light Blue", "Black"],
        "enhancing": ["White", "Silver", "Grey"],
        "destructive": ["Yellow", "Red", "Orange"],
    },
    "NNE": {
        "name": "North-North-East (উত্তর-উত্তর-পূর্ব)", "name_bn": "স্বাস্থ্য ও আরোগ্য জোন", "center": 22.5,
        "element": "Water", "element_bn": "জল তত্ত্ব",
        "organs": "রোগ প্রতিরোধ ক্ষমতা ও শারীরিক জীবনীশক্তি", "dosha": "Kapha",
        "life_aspect": "সুস্বাস্থ্য, নিরাময় ও প্রতিরোধ ক্ষমতা",
        "ideal": ["ওষুধ সংরক্ষণ", "ধ্যান কক্ষ", "জলপ্রবাহ"],
        "prohibited": ["টয়লেট", "রান্নাঘর", "ভারী আবর্জনা"],
        "self_colors": ["Blue", "Off-White"],
        "enhancing": ["White", "Silver"],
        "destructive": ["Red", "Dark Yellow"],
    },
    "NE": {
        "name": "North-East (উত্তর-পূর্ব / ঈশান)", "name_bn": "ঈশান কোণ (ঈশ্বর স্থান)", "center": 45.0,
        "element": "Water/Ether", "element_bn": "জল ও আকাশ তত্ত্ব",
        "organs": "মস্তিষ্ক, স্নায়ুতন্ত্র ও চক্ষু", "dosha": "Vata-Kapha",
        "life_aspect": "মানসিক স্পষ্টতা, প্রজ্ঞা ও আধ্যাত্মিক সংযোগ",
        "ideal": ["পূজা ঘর / মন্দির", "ধ্যান কেন্দ্র", "খোলা বারান্দা", "টিউবওয়েল"],
        "prohibited": ["টয়লেট (চরম অশুভ)", "রান্নাঘর (চরম অশুভ)", "সিঁড়ি", "মাস্টার বেডরুম"],
        "self_colors": ["White", "Off-White", "Sky Blue"],
        "enhancing": ["Silver", "Light Cream"],
        "destructive": ["Red", "Pink", "Dark Yellow", "Black"],
    },
    "ENE": {
        "name": "East-North-East (পূর্ব-উত্তর-পূর্ব)", "name_bn": "আনন্দ ও বিনোদন জোন", "center": 67.5,
        "element": "Air/Wood", "element_bn": "বায়ু / বৃক্ষ তত্ত্ব",
        "organs": "যকৃৎ (লিভার) ও কাঁধ", "dosha": "Pitta-Vata",
        "life_aspect": "আনন্দ, পারিবারিক বিনোদন ও মানসিক সতেজতা",
        "ideal": ["ড্রয়িং রুম", "টিভি / বিনোদন কেন্দ্র", "বাচ্চাদের খেলাধুলার স্থান"],
        "prohibited": ["টয়লেট", "অতিরিক্ত ভারী স্টোরেজ"],
        "self_colors": ["Green", "Light Green"],
        "enhancing": ["Blue", "Light Blue"],
        "destructive": ["White", "Silver", "Grey"],
    },
    "E": {
        "name": "East (পূর্ব)", "name_bn": "পূর্ব দিক (সূর্য স্থান)", "center": 90.0,
        "element": "Air/Wood", "element_bn": "বায়ু / বৃক্ষ তত্ত্ব",
        "organs": "যকৃৎ, পিত্তথলি ও স্নায়ু", "dosha": "Pitta",
        "life_aspect": "সামাজিক যোগাযোগ, সরকারি পৃষ্ঠপোষকতা ও প্রতিপত্তি",
        "ideal": ["প্রধান ফটক (E3, E4)", "লিভিং রুম", "ব্রাস সূর্য স্থাপন", "খোলা জানালা"],
        "prohibited": ["টয়লেট", "রান্নাঘর", "ভারী বন্ধ দেওয়াল"],
        "self_colors": ["Green", "Brown"],
        "enhancing": ["Blue", "Black"],
        "destructive": ["White", "Silver", "Metallic"],
    },
    "ESE": {
        "name": "East-South-East (পূর্ব-দক্ষিণ-পূর্ব)", "name_bn": "মন্থন ও চিন্তন জোন", "center": 112.5,
        "element": "Air/Wood", "element_bn": "বায়ু / বৃক্ষ তত্ত্ব",
        "organs": "অগ্ন্যাশয় (প্যানক্রিয়াস) ও অন্ত্র", "dosha": "Pitta",
        "life_aspect": "গভীর বিশ্লেষণ, পরিকল্পনা ও মন্থন",
        "ideal": ["টয়লেট (উপযুক্ত)", "কনফারেন্স কক্ষ", "চিন্তাশীল কাজের ডেস্ক"],
        "prohibited": ["মাস্টার বেডরুম (অবিরাম তর্ক)", "পূজা ঘর"],
        "self_colors": ["Light Green", "Cream"],
        "enhancing": ["Light Blue"],
        "destructive": ["Red", "Bright Yellow"],
    },
    "SE": {
        "name": "South-East (দক্ষিণ-পূর্ব / অগ্নি)", "name_bn": "অগ্নি কোণ (ধনাগমন জোন)", "center": 135.0,
        "element": "Fire", "element_bn": "অগ্নি তত্ত্ব",
        "organs": "জরায়ু, রক্তপ্রবাহ ও হজমশক্তি", "dosha": "Pitta",
        "life_aspect": "তরল অর্থপ্রবাহ (Liquid Cash), উদ্দীপনা ও ভোগবিলাস",
        "ideal": ["রান্নাঘর / গ্যাসের চুলা", "বৈদ্যুতিক মিটার", "রেড বাল্ব স্থাপন"],
        "prohibited": ["আন্ডারগ্রাউন্ড ওয়াটার ট্যাঙ্ক", "টয়লেট", "নীল/কালো রঙ"],
        "self_colors": ["Red", "Orange", "Crimson"],
        "enhancing": ["Green", "Light Brown"],
        "destructive": ["Blue", "Black", "Dark Grey"],
    },
    "SSE": {
        "name": "South-South-East (দক্ষিণ-দক্ষিণ-পূর্ব)", "name_bn": "শক্তি ও আত্মবিশ্বাস জোন", "center": 157.5,
        "element": "Fire", "element_bn": "অগ্নি তত্ত্ব",
        "organs": "পেশিশক্তি ও শারীরিক সহনশীলতা", "dosha": "Pitta",
        "life_aspect": "আত্মবিশ্বাস, নির্ভীক মানসিকতা ও শারীরিক পরাক্রম",
        "ideal": ["ব্যায়ামাগার (Gym)", "দ্বিতীয় রান্নাঘর", "নিরাপত্তা কক্ষ"],
        "prohibited": ["টয়লেট", "জলাশয়", "নীল রঙ"],
        "self_colors": ["Red", "Orange"],
        "enhancing": ["Green"],
        "destructive": ["Blue", "Black"],
    },
    "S": {
        "name": "South (দক্ষিণ / যম স্থান)", "name_bn": "খ্যাতি ও বিশ্রাম জোন", "center": 180.0,
        "element": "Fire", "element_bn": "অগ্নি তত্ত্ব",
        "organs": "হৃদপিণ্ড ও রক্ত সঞ্চালন", "dosha": "Pitta",
        "life_aspect": "সামাজিক খ্যাতি, নাম, সুখ্যাতি ও প্রশান্ত ঘুম",
        "ideal": ["শোবার ঘর (দক্ষিণে মাথা)", "১২টি লাল ঘোড়া স্থাপন", "ভারী আসবাব"],
        "prohibited": ["জলধারা", "প্রধান ফটক (অশুভ পদ)", "নীল বা ধূসর রঙ"],
        "self_colors": ["Red", "Maroon"],
        "enhancing": ["Green", "Light Yellow"],
        "destructive": ["Blue", "Water Tones"],
    },
    "SSW": {
        "name": "South-South-West (দক্ষিণ-দক্ষিণ-পশ্চিম)", "name_bn": "বিসর্জন জোন (Disposal Zone)", "center": 202.5,
        "element": "Earth", "element_bn": "পৃথিবী তত্ত্ব",
        "organs": "রেচনতন্ত্র ও বর্জ্য নিষ্কাশন", "dosha": "Vata",
        "life_aspect": "অপ্রয়োজনীয় বর্জ্য, ক্লান্তি ও নেতিবাচকতা বিসর্জন",
        "ideal": ["টয়লেট / কমোড (আদর্শ)", "ডাস্টবিন", "স্যুয়ারেজ ড্রেন"],
        "prohibited": ["শোবার ঘর (প্রাণশক্তি ক্ষয়)", "পূজা ঘর", "স্টাডি রুম"],
        "self_colors": ["Yellow", "Beige", "Earth"],
        "enhancing": ["Red", "Pink"],
        "destructive": ["Green", "Blue"],
    },
    "SW": {
        "name": "South-West (দক্ষিণ-পশ্চিম / নৈঋত)", "name_bn": "নৈঋত কোণ (স্থায়িত্ব ও পিতৃ কৃপা)", "center": 225.0,
        "element": "Earth", "element_bn": "পৃথিবী তত্ত্ব",
        "organs": "প্রজনন অঙ্গ, পা ও অস্থি সন্ধি", "dosha": "Kapha",
        "life_aspect": "দাম্পত্য সম্পর্ক, কর্মদক্ষতা ও পিতৃপুরুষের আশীর্বাদ",
        "ideal": ["প্রধান কর্তা/কর্ত্রীর মাস্টার বেডরুম", "ভারী সিন্দুক", "পারিবারিক ছবি"],
        "prohibited": ["টয়লেট (চরম অশুভ)", "রান্নাঘর (দাম্পত্য নাশ)", "আন্ডারগ্রাউন্ড ট্যাঙ্ক"],
        "self_colors": ["Yellow", "Mustard", "Gold"],
        "enhancing": ["Red", "Pink", "Orange"],
        "destructive": ["Green", "Blue", "Black"],
    },
    "WSW": {
        "name": "West-South-West (পশ্চিম-দক্ষিণ-পশ্চিম)", "name_bn": "বিদ্যা ও সঞ্চয় জোন", "center": 247.5,
        "element": "Space/Metal", "element_bn": "আকাশ / ধাতু তত্ত্ব",
        "organs": "কণ্ঠনালী ও স্বরযন্ত্র", "dosha": "Vata",
        "life_aspect": "লেখাপড়া, জ্ঞান সংরক্ষণ ও টেকসই সঞ্চয়",
        "ideal": ["স্টাডি রুম / পড়ার টেবিল", "বইয়ের আলমারি", "সঞ্চয়পত্র"],
        "prohibited": ["টয়লেট", "রান্নাঘর", "সবুজ গাছপালা"],
        "self_colors": ["White", "Cream", "Silver"],
        "enhancing": ["Yellow", "Earth"],
        "destructive": ["Red", "Green"],
    },
    "W": {
        "name": "West (পশ্চিম / বরুণ স্থান)", "name_bn": "লাভ ও প্রাপ্তি জোন (Gains & Profits)", "center": 270.0,
        "element": "Space/Metal", "element_bn": "আকাশ / ধাতু তত্ত্ব",
        "organs": "ফুসফুস ও শ্বাসযন্ত্র", "dosha": "Vata",
        "life_aspect": "বাণিজ্যিক লাভ, ইচ্ছাপূরণ ও বৈষয়িক প্রাপ্তি",
        "ideal": ["ডাইনিং রুম", "জুয়েলারি বক্স", "ওভারহেড ওয়াটার ট্যাঙ্ক", "সিন্দুক"],
        "prohibited": ["রান্নাঘর", "সবুজ গাছপালা (লাভ ব্যাহত করে)", "লাল রঙ"],
        "self_colors": ["White", "Silver", "Grey"],
        "enhancing": ["Yellow", "Ochre"],
        "destructive": ["Red", "Green"],
    },
    "WNW": {
        "name": "West-North-West (পশ্চিম-উত্তর-পশ্চিম)", "name_bn": "মানসিক বিষাদমুক্তি জোন", "center": 292.5,
        "element": "Space/Metal", "element_bn": "আকাশ / ধাতু তত্ত্ব",
        "organs": "থাইরয়েড ও অনাল গ্রন্থি", "dosha": "Vata",
        "life_aspect": "মানসিক চাপ মুক্তি, বিষাদ দূরীকরণ ও ডিটক্সিফিকেশন",
        "ideal": ["টয়লেট (আদর্শ)", "ওয়াশিং মেশিন", "কাউন্সেলিং রুম"],
        "prohibited": ["পূজা ঘর", "মাস্টার বেডরুম (বিষাদ বৃদ্ধি পায়)"],
        "self_colors": ["White", "Off-White"],
        "enhancing": ["Yellow"],
        "destructive": ["Red", "Green"],
    },
    "NW": {
        "name": "North-West (উত্তর-পশ্চিম / বায়ু)", "name_bn": "বায়ু কোণ (সহায়তা ও ব্যাংকিং)", "center": 315.0,
        "element": "Space/Metal", "element_bn": "আকাশ / ধাতু তত্ত্ব",
        "organs": "হাত ও কাঁধ", "dosha": "Vata",
        "life_aspect": "ব্যাংকিং সুবিধা, সহায়তা দানকারী বন্ধু ও সরকারি সাপোর্ট",
        "ideal": ["অতিথি কক্ষ (Guest Room)", "রেডি পণ্য স্টোরেজ", "সাদা ঘোড়া প্রতিকৃতি"],
        "prohibited": ["রান্নাঘর", "অতিরিক্ত ভারী স্থাবর লকার"],
        "self_colors": ["White", "Metallic", "Cream"],
        "enhancing": ["Yellow", "Earth"],
        "destructive": ["Red", "Fire Tones"],
    },
    "NNW": {
        "name": "North-North-West (উত্তর-উত্তর-পশ্চিম)", "name_bn": "আকর্ষণ ও যৌনসুখ জোন", "center": 337.5,
        "element": "Water", "element_bn": "জল তত্ত্ব",
        "organs": "যৌনাঙ্গ ও হরমোন ব্যালান্স", "dosha": "Kapha",
        "life_aspect": "পারস্পরিক আকর্ষণ, দাম্পত্য রসায়ন ও যৌনসুখ",
        "ideal": ["নবদম্পতির শোবার ঘর", "ড্রেসিং রুম", "সুগন্ধি সামগ্রী"],
        "prohibited": ["টয়লেট", "রান্নাঘর", "অগ্নিযন্ত্র"],
        "self_colors": ["Blue", "White"],
        "enhancing": ["Silver"],
        "destructive": ["Red", "Yellow"],
    },
}


# ---------------------------------------------------------------------------
# 120 Miraculous Remedies Catalog from `6ab2d85272f5ea7e.pdf`
# ---------------------------------------------------------------------------
VASTU_REMEDIES_CATALOG: list[dict[str, Any]] = [
    {
        "id": 1,
        "category": "Financial Growth",
        "title_bn": "আটকে থাকা টাকা উদ্ধার ও ক্যাশ ফ্লো বৃদ্ধি",
        "action_bn": "সাউথ-ইস্ট (SE) অগ্নি জোনে একটি ১৫ ওয়াটের লাল বাল্ব (Red Bulb) ২৪ ঘণ্টা জ্বালিয়ে রাখুন।",
        "target_zone": "SE",
        "item_required": "লাল বৈদ্যুতিক বাল্ব (Red Bulb)",
    },
    {
        "id": 2,
        "category": "Financial Growth",
        "title_bn": "কুবের দেবতার আশীর্বাদে বিপুল ধনলাভ",
        "action_bn": "নর্থ (North) কুবের জোনে একটি পিতলের কুবের মূর্তি (Brass Kuber) উত্তরমুখী করে স্থাপন করুন।",
        "target_zone": "N",
        "item_required": "পিতলের কুবের মূর্তি",
    },
    {
        "id": 3,
        "category": "Brand & Fame",
        "title_bn": "প্রতিষ্ঠানের ব্র্যান্ড ভ্যালু ও সামাজিক খ্যাতি",
        "action_bn": "সাউথ (South) খ্যাতি জোনে উত্তর দিকে ধাবমান ১২টি লাল রঙের ঘোড়ার মূর্তি বা চিত্র স্থাপন করুন।",
        "target_zone": "S",
        "item_required": "১২টি লাল ঘোড়ার চিত্র / ভাস্কর্য",
    },
    {
        "id": 4,
        "category": "Opportunities",
        "title_bn": "নতুন চাকরি ও ব্যবসায়িক সুযোগ আকর্ষণ",
        "action_bn": "উত্তর (North) দেওয়ালে একটি সবুজ পাহাড়ি ল্যান্ডস্কেপ বা মানিপ্ল্যান্ট নীল বোতলে রাখুন।",
        "target_zone": "N",
        "item_required": "নীল কাচের বোতলে মানিপ্ল্যান্ট",
    },
    {
        "id": 5,
        "category": "Social Ties",
        "title_bn": "প্রভাবশালী ব্যক্তিদের সাথে যোগাযোগ ও ভালো ভাড়াটিয়া লাভ",
        "action_bn": "ইস্ট (East) সূর্য জোনে একটি খাঁটি পিতলের সূর্যমণ্ডল (Brass Sun) দেওয়ালে স্থাপন করুন।",
        "target_zone": "E",
        "item_required": "পিতলের সূর্যমণ্ডল (Brass Sun)",
    },
    {
        "id": 6,
        "category": "Financial Growth",
        "title_bn": "মুনাফা বৃদ্ধি ও ব্যবসায়িক সাফল্য",
        "action_bn": "ওয়েস্ট (West) লাভ জোনে মূল্যবান গহনার বাক্স রাখুন এবং সমস্ত সবুজ গাছপালা অবিলম্বে সরিয়ে ফেলুন।",
        "target_zone": "W",
        "item_required": "ধাতব জুয়েলারি বক্স",
    },
    {
        "id": 7,
        "category": "Health & Vitality",
        "title_bn": "মানসিক বিভ্রান্তি দূরীকরণ ও আত্মিক শান্তি",
        "action_bn": "নর্থ-ইস্ট (NE) ঈশান কোণে স্ফটিকের শ্রীযন্ত্র বা খাঁটি রূপার পাত্রে গঙ্গাজল স্থাপন করুন।",
        "target_zone": "NE",
        "item_required": "স্ফটিক শ্রীযন্ত্র / রূপার পাত্র",
    },
    {
        "id": 8,
        "category": "Family Harmony",
        "title_bn": "দাম্পত্য কলহ নিবারণ ও পারিবারিক ঐক্য",
        "action_bn": "সাউথ-ওয়েস্ট (SW) জোনে একটি সোনালী ফ্রেমে বাঁধানো যৌথ পারিবারিক ছবি স্থাপন করুন।",
        "target_zone": "SW",
        "item_required": "সোনালী ফ্রেমে বাঁধানো ছবি",
    },
    {
        "id": 9,
        "category": "Non-Demolition Blocking",
        "title_bn": "টয়লেট দোষ নিবারণে মেটাল স্ট্রিপ থেরাপি",
        "action_bn": "ভুল জোনে অবস্থিত কমোডের চারপাশে মেঝেতে ৩-৪ মিমি চওড়া ধাতব স্ট্রিপ (পিতল/কপার/অ্যালুমিনিয়াম) সিল করে দিন।",
        "target_zone": "SW/SE/NW",
        "item_required": "ধাতব স্ট্রিপ (Brass / Copper / Aluminum Strip)",
    },
    {
        "id": 10,
        "category": "Academic Success",
        "title_bn": "স্মৃতিশক্তি ও পরীক্ষায় একাগ্রতা বৃদ্ধি",
        "action_bn": "ওয়েস্ট-সাউথ-ওয়েস্ট (WSW) জোনে হলুদ রঙের কলমদানি ও সরস্বতী যন্ত্র স্থাপন করুন।",
        "target_zone": "WSW",
        "item_required": "হলুদ কলমদানি ও সরস্বতী যন্ত্র",
    },
]


# ---------------------------------------------------------------------------
# Trigonometric Pada Finder
# ---------------------------------------------------------------------------

def resolve_entrance_pada(degree: float) -> PadaInfo:
    """Finds the exact Pada (1-32) for any angle 0.0 - 359.99° with N5 centered at 0°."""
    # Normalize degree to [0, 360)
    deg = degree % 360.0

    # Each pada is 11.25°.
    # N5 center is 0.0° (or 360.0°). Range: [354.375°, 360.0) U [0.0°, 5.625°)
    for p in PADA_DEFINITIONS:
        c = p["center"]
        start = (c - 5.625) % 360.0
        end = (c + 5.625) % 360.0

        if start > end:  # Spans across 0°
            if deg >= start or deg < end:
                return PadaInfo(
                    pada_id=p["pada_id"],
                    quadrant=p["quadrant"],
                    deity=p["deity"],
                    start_degree=round(start, 2),
                    center_degree=round(c, 2),
                    end_degree=round(end, 2),
                    is_auspicious=p["auspicious"],
                    life_effects=p["effects"],
                    challenge=p["challenge"],
                )
        else:
            if start <= deg < end:
                return PadaInfo(
                    pada_id=p["pada_id"],
                    quadrant=p["quadrant"],
                    deity=p["deity"],
                    start_degree=round(start, 2),
                    center_degree=round(c, 2),
                    end_degree=round(end, 2),
                    is_auspicious=p["auspicious"],
                    life_effects=p["effects"],
                    challenge=p["challenge"],
                )

    # Fallback to N5
    p5 = PADA_DEFINITIONS[4]
    return PadaInfo(
        pada_id=p5["pada_id"],
        quadrant=p5["quadrant"],
        deity=p5["deity"],
        start_degree=354.38,
        center_degree=0.0,
        end_degree=5.62,
        is_auspicious=p5["auspicious"],
        life_effects=p5["effects"],
        challenge=p5["challenge"],
    )


# ---------------------------------------------------------------------------
# Room Placement Evaluation Engine
# ---------------------------------------------------------------------------

ROOM_EVALUATION_RULES: dict[str, dict[str, Any]] = {
    "kitchen": {
        "name": "রান্নাঘর (Kitchen / Fire Element)",
        "scores": {
            "SE": 100, "SSE": 90, "S": 80,
            "E": 70, "W": 55, "NW": 50,
            "SSW": 40, "WSW": 40, "ESE": 35,
            "N": 15, "NNW": 15, "WNW": 20,
            "NE": 0, "NNE": 5, "SW": 0
        },
        "impacts": {
            "SE": "আদর্শ অগ্নিকোণ — তরল অর্থের অবিরাম আগমন, গৃহকর্ত্রীর সুস্বাস্থ্য ও বংশবৃদ্ধি।",
            "SSE": "চমৎকার স্থান — শক্তি ও আত্মবিশ্বাস বজায় থাকে।",
            "NE": "মারাত্মক বাস্তু দোষ — মাথার রোগ, স্নায়বিক ক্ষতি, আকস্মিক দেউলিয়াত্ব ও চরম চিকিৎসা ব্যয়।",
            "SW": "চরম বাস্তু দোষ — দাম্পত্য জীবনে অশান্তি, বিবাহবিচ্ছেদের ঝুঁকি ও পরিবারের সম্পর্কের চরম অবনতি।",
            "N": "জল ও অগ্নির সরাসরি সংঘাত — উপার্জনের পথ বন্ধ হওয়া ও ক্যারিয়ারে তীব্র স্থবিরতা।",
        },
        "remedies": {
            "NE": "কোনো ভাঙচুর ছাড়া সমাধান: গ্যাসের চুলার নিচে একটি সবুজ বরোদা মার্বেল (Green Baroda Marble) স্থাপন করুন।",
            "SW": "চুলার নিচে একটি হলুদ জাইসলমের পাথর (Yellow Jaisalmer Stone) প্রতিস্থাপন করুন।",
            "N": "চুলার নিচে একটি সবুজ পাথর স্থাপন করুন এবং দেওয়ালে একটি ছোট তামার তারের ফ্রেম দিন।",
            "default": "চুলা ও সিঙ্কের মাঝে একটি কাঠের বিভাজন বা সবুজ মার্বেল স্ল্যাব রাখুন।"
        },
        "metal_strip": "কপার স্ট্রিপ (Copper Strip)",
    },
    "master_bed": {
        "name": "মাস্টার বেডরুম (Master Bedroom)",
        "scores": {
            "SW": 100, "S": 90, "SSW": 30,
            "W": 85, "WSW": 75, "NW": 60,
            "SE": 35, "ESE": 25, "N": 50,
            "NE": 15, "NNE": 20, "E": 65
        },
        "impacts": {
            "SW": "আদর্শ নৈঋত কোণ — গৃহকর্তার সম্পূর্ণ কর্তৃত্ব, মানসিক স্থায়িত্ব ও চমৎকার দাম্পত্য বন্ধন।",
            "S": "উচ্চ খ্যাতি, শারীরিক বিশ্রাম ও দীর্ঘায়ু।",
            "NE": "অবিরাম মাথাব্যথা, অনিদ্রা, অতিরিক্ত আধ্যাত্মিক বৈরাগ্য ও সাংসারিক দায়িত্বে অবহেলা।",
            "SSW": "জীবনীশক্তি ক্ষয়, ক্লান্তি ও অলসতা বৃদ্ধি পায়।",
            "ESE": "স্বামী-স্ত্রীর মধ্যে তুচ্ছ বিষয় নিয়ে অন্তহীন বাদানুবাদ ও মন্থন।",
        },
        "remedies": {
            "NE": "খাটের নিচে পিতলের বাটিতে সৈন্ধব লবণ রাখুন এবং উত্তর-পূর্ব কোণে হালকা ওজনের আসবাব ব্যবহার করুন।",
            "ESE": "শোবার ঘরের পর্দা ও চাদরে হালকা পেস্টাল বা ক্রিম রঙ ব্যবহার করুন।",
            "default": "মাথা সর্বদা দক্ষিণ বা পূর্ব দিকে রেখে ঘুমানোর ব্যবস্থা করুন।"
        },
        "metal_strip": "ব্রাস স্ট্রিপ (Brass Strip)",
    },
    "toilet": {
        "name": "টয়লেট / কমোড (Toilet / Commode)",
        "scores": {
            "SSW": 100, "WNW": 95, "ESE": 85,
            "NW": 60, "S": 45, "W": 50,
            "E": 25, "SE": 20, "SW": 0,
            "N": 10, "NNE": 5, "NE": 0
        },
        "impacts": {
            "SSW": "আদর্শ বিসর্জন জোন — ঘরের সমস্ত নেতিবাচক শক্তি ও বিষাদ স্বাভাবিকভাবে নিষ্কাশিত হয়।",
            "WNW": "মানসিক চাপ ও অপ্রয়োজনীয় আবেগীয় বোঝা দূর হয়।",
            "NE": "চরম মারাত্মক দোষ — স্মৃতিভ্রম, পক্ষাঘাত, ক্যানসারের ঝুঁকি ও পরিবারের অগ্রগতি চিরতরে রুদ্ধ।",
            "SW": "সম্পর্কের মৃত্যু — স্বামী-স্ত্রীর সম্পর্ক ছিন্ন হওয়া এবং পিতৃপুরুষের কৃপা বিলুপ্ত হওয়া।",
            "N": "নতুন উপার্জনের সুযোগ নর্দমায় পতিত হওয়া, তীব্র অর্থকষ্ট।",
        },
        "remedies": {
            "NE": "জরুরি প্রতিকার: কমোডের চারপাশের মেঝে কেটে একটি ৩ মিমি অ্যালুমিনিয়াম বা রূপার তারের স্ট্রিপ দিয়ে সম্পূর্ণ ব্লক করুন।",
            "SW": "কমোডের চারপাশে পিতলের স্ট্রিপ (Brass Strip) ফ্লোরিংয়ে স্থাপন করে এনার্জি কাট অফ করুন।",
            "N": "নীল রঙের বা অ্যালুমিনিয়াম স্ট্রিপ দিয়ে কমোডের চারপাশ আবদ্ধ করুন।",
            "default": "টয়লেটের ঢাকনা সর্বদা বন্ধ রাখুন এবং একটি কাচের বাটিতে সামুদ্রিক লবণ রাখুন।"
        },
        "metal_strip": "পিতল বা অ্যালুমিনিয়াম স্ট্রিপ",
    },
    "puja_room": {
        "name": "পূজা ঘর / মন্দির (Puja Room / Mandir)",
        "scores": {
            "NE": 100, "E": 90, "N": 85,
            "ENE": 80, "NNE": 80, "W": 60,
            "NW": 50, "SE": 25, "S": 15,
            "SW": 0, "SSW": 0, "WNW": 10
        },
        "impacts": {
            "NE": "ঈশান কোণ — পরম ঈশ্বরের বাসস্থান। অনন্ত শান্তি, আধ্যাত্মিক শক্তি ও পারিবারিক মঙ্গল।",
            "E": "সূর্যের প্রত্যক্ষ শক্তি — সমাজে সুনাম ও মর্যাদা।",
            "SW": "নৈঋত কোণ — দেবতা ও পিতৃপুরুষের শক্তি সংঘাত, সংসারে বিপর্যয়।",
            "SSW": "প্রার্থনার সুফল বিসর্জনে চলে যায়, কোনো পুণ্য ফলিত হয় না।",
        },
        "remedies": {
            "SW": "মন্দির অবিলম্বে ঈশান বা পূর্ব দিকে স্থানান্তর করুন, অথবা একটি রূপার ওম প্রতীক ঈশানে স্থাপন করুন।",
            "default": "মন্দিরে স্নিগ্ধ আলো রাখুন এবং মৃত পূর্বপুরুষের ছবি ঠাকুর ঘরে রাখবেন না।"
        },
        "metal_strip": None,
    },
    "underground_water": {
        "name": "আন্ডারগ্রাউন্ড ওয়াটার ট্যাঙ্ক / বোরওয়েল",
        "scores": {
            "N": 100, "NE": 95, "NNE": 90,
            "E": 80, "ENE": 75, "NW": 50,
            "W": 30, "SE": 0, "SSE": 0,
            "S": 0, "SW": 0, "SSW": 0
        },
        "impacts": {
            "N": "কুবেরের আশীর্বাদে বিপুল ধনবৃদ্ধি ও অর্থনৈতিক নিরাপত্তা।",
            "NE": "অপরিমেয় সৌভাগ্য ও আধ্যাত্মিক উন্নতি।",
            "SE": "অগ্নি-জলের চরম যুদ্ধ — রক্তপাত, অগ্নিকাণ্ড, অর্থনাশ ও গৃহকর্ত্রীর অকাল পীড়া।",
            "SW": "নৈঋতে গর্ত — গৃহকর্তার মারাত্মক পতন, আকস্মিক বিপর্যয় ও বংশনাশ।",
        },
        "remedies": {
            "SE": "ট্যাঙ্কের চারপাশে তামার পাত বা কপার তারের গ্রিড বসিয়ে এনার্জি নিউট্রালাইজ করুন।",
            "SW": "ট্যাঙ্কের চারপাশে পিতলের পাত স্থাপন করুন এবং ভারী পাথর বসান।",
            "default": "জলাধারের মুখ সর্বদা পরিষ্কার ও ঢাকা রাখুন।"
        },
        "metal_strip": "কপার বা ব্রাস স্ট্রিপ",
    },
    "overhead_tank": {
        "name": "ওভারহেড ওয়াটার ট্যাঙ্ক (Overhead Water Tank)",
        "scores": {
            "W": 100, "SW": 90, "S": 80,
            "NW": 70, "WSW": 75, "SE": 40,
            "N": 15, "NE": 0, "ENE": 20
        },
        "impacts": {
            "W": "পশ্চিম দিকে ভারী জলাধার বরুণের শক্তির স্থায়িত্ব ও স্থায়ী ধন দেয়।",
            "SW": "উচ্চতা ও ওজন স্থিতিশীলতা বৃদ্ধি করে।",
            "NE": "ঈশান কোণে ভারী ওজন স্থাপন মানে ঈশ্বরের মাথায় পাথর চাপা দেওয়া — চরম দুর্ভোগ।",
        },
        "remedies": {
            "NE": "ট্যাঙ্কটি অবিলম্বে সরিয়ে পশ্চিমে নিন, অথবা ট্যাঙ্কের নিচে পিরামিড এনার্জি প্লেট রাখুন।",
            "default": "ট্যাঙ্কের রঙ গাঢ় নীল বা কালো না রেখে সাদা বা হলুদ রাখুন।"
        },
        "metal_strip": None,
    },
    "locker": {
        "name": "টাকার সিন্দুক / ক্যাশ লকার (Cash Locker / Safe)",
        "scores": {
            "N": 100, "W": 90, "SW": 85,
            "E": 70, "NE": 60, "NW": 45,
            "SE": 35, "SSW": 0, "WNW": 10
        },
        "impacts": {
            "N": "উত্তরমুখী হয়ে খোলে — কুবেরের দৃষ্টিতে সর্বদা সম্পদে পরিপূর্ণ থাকে।",
            "W": "স্থায়ী মুনাফা ও সঞ্চয় বৃদ্ধি পায়।",
            "SSW": "টাকা বিসর্জন জোনে — সঞ্চিত অর্থ চিকিৎসা ও অপ্রয়োজনীয় দণ্ডে দ্রুত বিনষ্ট হয়।",
            "SE": "টাকা দ্রুত পুড়ে যায়, খরচের লাগাম থাকে না।",
        },
        "remedies": {
            "SSW": "লকারটি অবিলম্বে উত্তর বা পশ্চিম দেওয়ালে স্থানান্তর করুন।",
            "SE": "লকারের ভেতরে রূপার কয়েন ও একটি লাল কাপড়ে মোড়ানো এলাচ রাখুন।",
            "default": "লকারের দরজা যেন সর্বদা উত্তর বা পূর্ব দিকে খোলে।"
        },
        "metal_strip": "ব্রাস স্ট্রিপ",
    },
    "staircase": {
        "name": "সিঁড়ি (Staircase)",
        "scores": {
            "S": 100, "SW": 95, "W": 90,
            "NW": 70, "SE": 60, "SSW": 80,
            "E": 40, "N": 20, "NE": 0
        },
        "impacts": {
            "S / SW / W": "দক্ষিণ বা পশ্চিমে ভারী সিঁড়ি বাস্তু শক্তিকে সুদৃঢ় করে।",
            "NE": "ঈশানে সিঁড়ি — পারিবারিক অগ্রগতি ও বুদ্ধিবৃত্তিক বিকাশ চিরতরে পিষ্ট হয়ে যায়।",
        },
        "remedies": {
            "NE": "সিঁড়ির প্রথম ধাপে তামার তারের গ্রিড এবং দেয়ালে পঞ্চমুখী হনুমান যন্ত্র স্থাপন করুন।",
            "default": "সিঁড়ি যেন সর্বদা ঘড়ির কাঁটার দিকে (Clockwise) ওপরের দিকে ওঠে।"
        },
        "metal_strip": "কপার স্ট্রিপ",
    },
}


# ---------------------------------------------------------------------------
# Master Vastu Audit Evaluation Function
# ---------------------------------------------------------------------------

def perform_vastu_audit(
    main_entrance_degree: float,
    placements: dict[str, str],
    property_type: str = "residential"
) -> VastuAuditResponse:
    """Executes a 360° scientific Vastu Audit evaluating Entrance Pada and Room Placements."""
    # 1. Resolve Main Entrance Pada
    entrance_pada = resolve_entrance_pada(main_entrance_degree)
    entrance_verdict = (
        f"অত্যন্ত শুভ ও বরকতময় প্রবেশদ্বার ({entrance_pada.pada_id} - {entrance_pada.deity})। "
        if entrance_pada.is_auspicious
        else f"প্রতিকূল প্রবেশদ্বার ({entrance_pada.pada_id} - {entrance_pada.deity})। দোষ নিবারক প্রতিকার আবশ্যক।"
    )

    evaluations: list[PlacementEvaluationItem] = []
    total_score = 0
    max_score = 0
    critical_warnings: list[str] = []

    # If entrance is malefic, add critical warning
    if not entrance_pada.is_auspicious:
        critical_warnings.append(f"মূল প্রবেশদ্বার {entrance_pada.pada_id} ({entrance_pada.deity}) শুভ নয়। চ্যালেঞ্জ: {entrance_pada.challenge}।")

    # Evaluate each room placement
    for cat_id, zone_code in placements.items():
        z_clean = zone_code.strip().upper()
        rule = ROOM_EVALUATION_RULES.get(cat_id)
        if not rule:
            continue

        scores_map = rule.get("scores", {})
        impacts_map = rule.get("impacts", {})
        remedies_map = rule.get("remedies", {})

        score = scores_map.get(z_clean, 50)
        total_score += score
        max_score += 100

        # Rating label
        if score >= 90:
            rating = "Excellent"
        elif score >= 75:
            rating = "Good"
        elif score >= 50:
            rating = "Acceptable"
        elif score > 20:
            rating = "Fault"
        else:
            rating = "Critical Negative"

        # Impact and Remedy text
        impact = impacts_map.get(z_clean, f"{z_clean} জোনে {rule['name']} সাধারণ মানের ফলপ্রসূ।")
        remedy = remedies_map.get(z_clean, remedies_map.get("default", "কোনো বিশেষ প্রতিকারের প্রয়োজন নেই।"))

        if score <= 20:
            critical_warnings.append(f"{rule['name']} {z_clean} জোনে মারাত্মক বাস্তু দোষ সৃষ্টি করছে: {impact}")

        evaluations.append(PlacementEvaluationItem(
            category_id=cat_id,
            category_name=rule["name"],
            placed_zone=z_clean,
            rating=rating,
            score=score,
            impact_bn=impact,
            remedy_bn=remedy,
            metal_strip_blocking=rule.get("metal_strip") if score < 60 else None,
            object_remedy="রেমেডি ক্যাটালগ অনুযায়ী প্রতিষেধক প্রয়োগ করুন।" if score < 60 else None,
        ))

    # Overall percentage
    final_score = int((total_score / max(max_score, 1)) * 100) if max_score > 0 else 75
    # Factor entrance
    if not entrance_pada.is_auspicious:
        final_score = max(final_score - 15, 20)
    else:
        final_score = min(final_score + 5, 100)

    if final_score >= 85:
        grade = "A+ (অত্যন্ত চমৎকার ও সমৃদ্ধিপ্রদ বাস্তু)"
        summary = "ভবনটির বাস্তু বিন্যাস অত্যন্ত বিজ্ঞানসম্মত এবং ইতিবাচক শক্তি প্রবাহে পরিপূর্ণ। সামান্য কিছু সাধারণ সুরভী ও রুটিন পরিচ্ছন্নতা বজায় রাখলেই সর্বোচ্চ বরকত বজায় থাকবে।"
    elif final_score >= 65:
        grade = "B (মধ্যম মানের বাস্তু - কিছু সংশোধন প্রয়োজন)"
        summary = "ভবনটিতে কয়েকটি গুরুত্বপূর্ণ শুভ সংযোগ থাকলেও কিছু জোনে উপাদানগত সংঘাত রয়েছে। উল্লেখিত অহিংস মেটাল স্ট্রিপ ও প্রতিকার সামগ্রী ব্যবহার করলে স্কোর ৮৫+ এ উন্নীত হবে।"
    else:
        grade = "C (মারাত্মক বাস্তু দোষ যুক্ত - তাৎক্ষণিক অহিংস প্রতিকার আবশ্যক)"
        summary = "ভবনটিতে প্রধান শক্তি জোনে (যেমন ঈশান, অগ্নি বা নৈঋতে) উপাদানগত চরম সংঘাত বা দোষ রয়েছে। কোনো ভাঙচুর ছাড়াই অবিলম্বে নির্দেশিত পিরামিড, মেটাল স্ট্রিপ ও প্রতিকার ব্যবস্থা সম্পন্ন করুন।"

    # Elemental Balance calculation
    element_counts = {"Water": 0, "Air/Wood": 0, "Fire": 0, "Earth": 0, "Space/Metal": 0}
    for ev in evaluations:
        zone_info = ZONE_METADATA.get(ev.placed_zone)
        if zone_info:
            elem = zone_info["element"]
            if "Water" in elem:
                element_counts["Water"] += ev.score
            elif "Air" in elem or "Wood" in elem:
                element_counts["Air/Wood"] += ev.score
            elif "Fire" in elem:
                element_counts["Fire"] += ev.score
            elif "Earth" in elem:
                element_counts["Earth"] += ev.score
            else:
                element_counts["Space/Metal"] += ev.score

    tot_elem = max(sum(element_counts.values()), 1)
    elemental_balance = {k: int((v / tot_elem) * 100) for k, v in element_counts.items()}

    # Selected key remedies from catalog
    key_remedies = [
        VastuRemedyItem(
            remedy_id=r["id"],
            category=r["category"],
            title_bn=r["title_bn"],
            action_bn=r["action_bn"],
            target_zone=r["target_zone"],
            item_required=r["item_required"],
        )
        for r in VASTU_REMEDIES_CATALOG[:5]
    ]

    return VastuAuditResponse(
        overall_score=final_score,
        grade=grade,
        summary_bn=summary,
        main_entrance_pada=entrance_pada,
        entrance_verdict=entrance_verdict,
        evaluations=evaluations,
        elemental_balance=elemental_balance,
        key_remedies=key_remedies,
        warnings_critical=critical_warnings,
    )


# ---------------------------------------------------------------------------
# Classical Ayadi Shadvarga Vedic Engine (Aaya Prakarana)
# ---------------------------------------------------------------------------
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

AAYA_DATA = {
    1: {"name": "Dhwaja Aaya", "name_bn": "ধ্বজ আয় (১)", "auspicious": True, "significance": "ধ্বজ আয় — অপার অর্থপ্রাপ্তি, প্রতিষ্ঠা, রাজকীয় সম্মান ও দীর্ঘস্থায়ী ঐশ্বর্য নির্দেশ করে।", "directions": ["পূর্ব (East)", "উত্তর (North)"]},
    2: {"name": "Dhuma Aaya", "name_bn": "ধূম্র আয় (২)", "auspicious": False, "significance": "ধূম্র আয় — অতিরিক্ত মানসিক উদ্বেগ, অগ্নিভয় ও আর্থিক অনিশ্চয়তা সৃষ্টি করে।", "directions": ["প্রতিকার প্রয়োজন"]},
    3: {"name": "Simha Aaya", "name_bn": "সিংহ আয় (৩)", "auspicious": True, "significance": "সিংহ আয় — বিজয়, অতুলনীয় কর্তৃত্ব, সামাজিক খ্যাতি ও সর্বকাজে সাফল্য দেয়।", "directions": ["দক্ষিণ (South)", "পূর্ব (East)"]},
    4: {"name": "Shwana Aaya", "name_bn": "শ্বান আয় (৪)", "auspicious": False, "significance": "শ্বান আয় — অপযশ, কলহ ও পরিবারের মধ্যে আত্মিক দূরত্বের কারণ হয়।", "directions": ["প্রতিকার প্রয়োজন"]},
    5: {"name": "Vrisha Aaya", "name_bn": "বৃষভ আয় (৫)", "auspicious": True, "significance": "বৃষভ আয় — স্থাবর সম্পত্তি, বংশবৃদ্ধি, মানসিক স্থিরতা ও দীর্ঘমেয়াদী সমৃদ্ধি আনে।", "directions": ["পশ্চিম (West)", "উত্তর (North)"]},
    6: {"name": "Khara Aaya", "name_bn": "খর আয় (৬)", "auspicious": False, "significance": "খর আয় — অতিরিক্ত শ্রম সত্ত্বেও অপ্রতুল প্রতিদান ও পরাধীনতার সৃষ্টি করে।", "directions": ["প্রতিকার প্রয়োজন"]},
    7: {"name": "Gaja Aaya", "name_bn": "গজ আয় (৭)", "auspicious": True, "significance": "গজ আয় — রাজকীয় ঐশ্বর্য, সৌভাগ্য, মিত্রলাভ ও ব্যবসা-বাণিজ্যে অটল স্থায়িত্ব দেয়।", "directions": ["উত্তর (North)", "পূর্ব (East)"]},
    8: {"name": "Kaka Aaya", "name_bn": "কাক আয় (৮)", "auspicious": False, "significance": "কাক আয় — অর্থনাশ, শোক ও পরিবারের অগ্রগতিতে অনাকাঙ্ক্ষিত বাধা তৈরি করে।", "directions": ["প্রতিকার প্রয়োজন"]},
}


def calculate_ayadi_shadvarga(length: float, width: float, unit: str = "feet") -> AyadiCalculationResponse:
    """Calculates classical Ayadi Shadvarga parameters from client's Essentials of Vastu."""
    length_ft = length if unit == "feet" else length * 3.28084
    width_ft = width if unit == "feet" else width * 3.28084
    area_sqft = round(length_ft * width_ft, 2)
    int_area = max(int(round(area_sqft)), 1)

    # 1. Aaya (Area * 8) % 8
    aaya_rem = (int_area * 8) % 8
    aaya_num = 8 if aaya_rem == 0 else aaya_rem
    aaya_info = AAYA_DATA[aaya_num]

    # 2. Dhana (Income) & Rina (Expenditure)
    dhana = ((int_area * 8) % 12) or 12
    rina = ((int_area * 3) % 8) or 8
    is_dhana_dominant = dhana >= rina

    # 3. Structure Longevity (Aayu in years)
    aayu_years = ((int_area * 27) % 100) or 100

    # 4. Building Nakshatra
    nakshatra_idx = ((int_area * 8) % 27)
    nakshatra_name = NAKSHATRA_NAMES[nakshatra_idx]

    return AyadiCalculationResponse(
        length=round(length, 2),
        width=round(width, 2),
        area_sqft=area_sqft,
        aaya_number=aaya_num,
        aaya_name=aaya_info["name"],
        aaya_name_bn=aaya_info["name_bn"],
        is_auspicious=aaya_info["auspicious"],
        aaya_significance_bn=aaya_info["significance"],
        dhana_score=dhana,
        rina_score=rina,
        is_dhana_dominant=is_dhana_dominant,
        structure_longevity_years=aayu_years,
        building_nakshatra_number=nakshatra_idx + 1,
        building_nakshatra_name=nakshatra_name,
        best_facing_directions_bn=aaya_info["directions"],
    )


# ---------------------------------------------------------------------------
# Medical & Organ Vastu Diagnostics Catalog
# ---------------------------------------------------------------------------
MEDICAL_VASTU_CATALOG: list[MedicalVastuItem] = [
    MedicalVastuItem(
        ailment_id="depression_sorrow",
        name_bn="বিষণ্নতা, মানসিক অবসাদ ও একাকীত্ব",
        name_en="Depression, Anxiety & Emotional Grief",
        affected_zone="WNW",
        affected_element="Space/Metal (আকাশ ও ধাতু)",
        body_organ_bn="থাইরয়েড ও গ্ল্যান্ডুলার নিঃসরণ",
        dosha="Vata (বায়ু)",
        root_cause_bn="WNW (পশ্চিম-উত্তর-পশ্চিম) জোনে টয়লেট, ডাস্টবিন, ভারী জিনিস বা লাল রঙের অ্যান্টি-কালার উপস্থিতি।",
        remedy_bn="WNW কোণে হালকা হলুদ বা অফ-হোয়াইট রঙ ব্যবহার করুন। টয়লেট থাকলে ব্রাস বা অ্যালুমিনিয়াম স্ট্রিপ মেঝের খাঁজে বসিয়ে লক করুন।"
    ),
    MedicalVastuItem(
        ailment_id="insomnia_overthinking",
        name_bn="অনিদ্রা, অতিরিক্ত চিন্তা ও অস্থিরতা",
        name_en="Insomnia, Restlessness & Overthinking",
        affected_zone="NE / ESE",
        affected_element="Water & Air (জল ও বায়ু)",
        body_organ_bn="মস্তিষ্ক, স্নায়ুতন্ত্র ও পিনিয়াল গ্ল্যান্ড",
        dosha="Vata-Kapha",
        root_cause_bn="ঈশান কোণে (NE) রান্নাঘর (অগ্নি), লাল/গোলাপী রঙ অথবা ESE জোনে বেডরুম স্থাপন।",
        remedy_bn="ঈশানে নীল রঙের গ্লাস বা স্ফটিক বল ঝুলিয়ে রাখুন এবং রান্নাঘরের বার্নারের নিচে সবুজ মার্বেল স্ল্যাব স্থাপন করুন।"
    ),
    MedicalVastuItem(
        ailment_id="heart_high_bp",
        name_bn="হৃদরোগ, বুক ধড়ফড় ও উচ্চ রক্তচাপ",
        name_en="Heart Palpitations & High Blood Pressure",
        affected_zone="South / SSW",
        affected_element="Fire & Earth (অগ্নি ও পৃথিবী)",
        body_organ_bn="হৃদযন্ত্র ও রক্ত সংবহনতন্ত্র",
        dosha="Pitta (পিত্ত)",
        root_cause_bn="দক্ষিণ বা দক্ষিণ-দক্ষিণ-পশ্চিমে (SSW) জলের উপস্থিতি, বোরওয়েল, নীল রঙ অথবা কাটা কোণ।",
        remedy_bn="দক্ষিণে লাল/গোলাপী রঙ রাখুন ও ৯টি লাল মোমবাতি বা লাল জিরো বাল্ব ব্যবহার করুন। টয়লেটে কপার স্ট্রিপ ব্যবহার করুন।"
    ),
    MedicalVastuItem(
        ailment_id="liver_jaundice_digestion",
        name_bn="ফ্যাটি লিভার, জন্ডিস ও হজমের সমস্যা",
        name_en="Fatty Liver, Jaundice & Indigestion",
        affected_zone="East / ESE",
        affected_element="Air/Wood (বায়ু ও কাঠ)",
        body_organ_bn="যকৃৎ (Liver) ও পিত্তথলি (Gall Bladder)",
        dosha="Pitta",
        root_cause_bn="পূর্ব দিকে টয়লেট, বাথরুম বা বন্ধ অন্ধকার পরিবেশ যা সূর্যের প্রাণশক্তিকে ব্লক করে।",
        remedy_bn="পূর্বে সবুজ সতেজ গাছপালা রাখুন এবং দেওয়ালের পূর্ব দিকে ১২ ইঞ্চি পিতলের সূর্যমূর্তি স্থাপন করুন।"
    ),
    MedicalVastuItem(
        ailment_id="kidney_urinary",
        name_bn="কিডনির সমস্যা ও মূত্রনালীর ইনফেকশন",
        name_en="Kidney Stones & Urinary Incontinence",
        affected_zone="North / NNW",
        affected_element="Water (জল)",
        body_organ_bn="বৃক্ক (Kidneys) ও মূত্রাশয় (Bladder)",
        dosha="Kapha (কফ)",
        root_cause_bn="উত্তরে আগুনের উপস্থিতি (রান্নাঘর), অতিরিক্ত লাল রঙ অথবা উত্তর দিক ব্লক থাকা।",
        remedy_bn="উত্তর দিকে নীল পাপোশ, মানিপ্ল্যান্ট ও পিতলের কুবের মূর্তি রাখুন। রান্নার ওভেনের নিচে সবুজ স্ল্যাব দিন।"
    ),
    MedicalVastuItem(
        ailment_id="infertility_reproductive",
        name_bn="প্রজনন সমস্যা ও সন্তানধারণে বিলম্ব",
        name_en="Infertility & Reproductive Health",
        affected_zone="SW / SE",
        affected_element="Earth & Fire (পৃথিবী ও অগ্নি)",
        body_organ_bn="জরায়ু ও প্রজননতন্ত্র",
        dosha="Kapha-Pitta",
        root_cause_bn="দক্ষিণ-পশ্চিমে (SW) টয়লেট, আন্ডারগ্রাউন্ড ওয়াটার বা দক্ষিণ-পূর্বে (SE) রান্নাঘরের অনুপস্থিতি।",
        remedy_bn="SW-তে হলুদ পাথর, পিতলের স্বস্তিক ও ৪ মিমি ব্রাস স্ট্রিপ সিল করুন। SE-তে ১৫ ওয়াট লাল বাল্ব জ্বালান।"
    ),
    MedicalVastuItem(
        ailment_id="diabetes_pancreas",
        name_bn="ডায়াবেটিস ও অগ্ন্যাশয়ের সমস্যা",
        name_en="Diabetes & Pancreas Complications",
        affected_zone="ESE",
        affected_element="Air/Wood (বায়ু)",
        body_organ_bn="অগ্ন্যাশয় (Pancreas)",
        dosha="Pitta",
        root_cause_bn="ESE জোনে জলতত্ত্ব বা অতিরিক্ত বিশৃঙ্খলা, যা মানসিক মন্থন ও হরমোন নিঃসরণে বিশৃঙ্খলা আনে।",
        remedy_bn="ESE জোন পরিষ্কার পরিচ্ছন্ন রাখুন এবং স্টেইনলেস স্টিল স্ট্রিপ ও হালকা বাদামী রঙ ব্যবহার করুন।"
    ),
    MedicalVastuItem(
        ailment_id="lungs_asthma",
        name_bn="শ্বাসকষ্ট, হাঁপানি ও ফুসফুসের রোগ",
        name_en="Asthma, Bronchitis & Respiratory Disorders",
        affected_zone="West / WSW",
        affected_element="Space/Metal (আকাশ)",
        body_organ_bn="ফুসফুস (Lungs) ও শ্বাসতন্ত্র",
        dosha="Vata",
        root_cause_bn="পশ্চিম দিকে অতিরিক্ত সবুজ রঙ বা অগ্নির উপস্থিতি, যা মেটাল এলিমেন্টকে দহন করে।",
        remedy_bn="পশ্চিমে সাদা বা রূপালী রঙ করুন এবং গোলাকার সাদা ধাতব ফ্রেমের ছবি ও ধাতব উইন্ডচাইম স্থাপন করুন।"
    ),
    MedicalVastuItem(
        ailment_id="low_immunity_fatigue",
        name_bn="রোগ প্রতিরোধ ক্ষমতা হ্রাস ও দীর্ঘস্থায়ী ক্লান্তি",
        name_en="Low Immunity & Chronic Fatigue",
        affected_zone="NNE",
        affected_element="Water (জল)",
        body_organ_bn="ইমিউন সিস্টেম ও লিম্ফ্যাটিক গ্ল্যান্ডস",
        dosha="Kapha",
        root_cause_bn="NNE (উত্তর-উত্তর-পূর্ব) জোনে টয়লেট, ইনভার্টার, ডাস্টবিন বা অতিরিক্ত আবর্জনা।",
        remedy_bn="NNE জোনে পরিবারের যাবতীয় নিত্যদিনের ওষুধ সংরক্ষণ করুন এবং খাঁটি তুলসী পাতা ও জলের পাত্র রাখুন।"
    ),
    MedicalVastuItem(
        ailment_id="financial_drain_debts",
        name_bn="আটকে থাকা টাকা, দেনা ও আকস্মিক আর্থিক ক্ষতি",
        name_en="Severe Cashflow Blockage & Growing Debts",
        affected_zone="SE / SSW",
        affected_element="Fire & Earth (অগ্নি ও অপচয়)",
        body_organ_bn="অর্থের তারল্য ও শক্তি সঞ্চয়",
        dosha="Pitta",
        root_cause_bn="দক্ষিণ-পূর্বে (SE) টয়লেট বা আন্ডারগ্রাউন্ড ওয়াটার থাকা, যা নগদ টাকার প্রবাহ ভস্মীভূত করে।",
        remedy_bn="SE জোনে একটি ১৫ ওয়াটের জিরো লাল বাল্ব ২৪ ঘণ্টা জ্বালিয়ে রাখুন ও তামার স্ট্রিপ দিয়ে কমোড বিচ্ছিন্ন করুন।"
    ),
    MedicalVastuItem(
        ailment_id="marital_conflict",
        name_bn="দাম্পত্য কলহ ও বিবাহ বিচ্ছেদের আশঙ্কা",
        name_en="Marital Conflict & Relational Discord",
        affected_zone="SW / ESE",
        affected_element="Earth & Air (স্থায়িত্ব ও মন্থন)",
        body_organ_bn="পারিবারিক বন্ধন ও আবেগীয় সমতা",
        dosha="Kapha-Pitta",
        root_cause_bn="দক্ষিণ-পশ্চিমে (SW) আয়না, ওয়াশিং মেশিন বা কাটা কোণ থাকা।",
        remedy_bn="SW বেডরুমে হলুদ চাদর ব্যবহার করুন এবং একজোড়া লাভ বার্ডসের মূর্তি বা গোলাপী কোয়ার্টজ ক্রিস্টাল স্থাপন করুন।"
    ),
]


def get_medical_vastu_catalog() -> list[MedicalVastuItem]:
    """Returns the comprehensive Medical Vastu diagnostic catalog."""
    return MEDICAL_VASTU_CATALOG


# ---------------------------------------------------------------------------
# Astro-Vastu Synergy Engine
# ---------------------------------------------------------------------------
ASTROVASTU_RULES: list[AstroVastuRule] = [
    AstroVastuRule(
        planet_id="sun",
        planet_name_bn="রবি (Sun)",
        governing_direction="East (পূর্ব দিক)",
        element="Fire/Air (অগ্নি ও বায়ু)",
        importance_during_dasha_bn="সূর্যের মহাদশায় পদোন্নতি, সরকারি সাহায্য, আত্মমর্যাদা ও পিতা-পুত্রের সম্পর্ক বজায় রাখতে পূর্ব দিক সক্রিয় রাখা বাধ্যতামূলক।",
        critical_dos_bn=["পূর্ব দেওয়ালে ১২ ইঞ্চি পিতলের সূর্য টাঙান", "পূর্ব দিক সবসময় খোলা ও আলোকময় রাখুন", "সকালে সূর্য প্রণাম করুন"],
        critical_donts_bn=["পূর্বে কোনো ভারী স্টোররুম বা আবর্জনা রাখবেন না", "পূর্বে টয়লেট বা অন্ধকার রাখবেন না"],
        talismanic_remedy_bn="পূর্ব দেওয়ালে ৫ ফুট উচ্চতায় খাঁটি ব্রাস বা তামার সূর্যের প্রতিকৃতি স্থাপন করুন।"
    ),
    AstroVastuRule(
        planet_id="moon",
        planet_name_bn="চন্দ্র (Moon)",
        governing_direction="NW (উত্তর-পশ্চিম দিক)",
        element="Air/Water (বায়ু ও জল)",
        importance_during_dasha_bn="চন্দ্রের মহাদশায় মানসিক শান্তি, বিদেশযাত্রা, তরল অর্থ ও মাতার স্বাস্থ্য রক্ষায় উত্তর-পশ্চিম জোন ভারসাম্যপূর্ণ হওয়া আবশ্যক।",
        critical_dos_bn=["উত্তর-পশ্চিমে সিলভার উইন্ডচাইম বা পারদ শিবলিঙ্গ রাখুন", "সাদা ফুল বা রূপার স্বস্তিক লাগান"],
        critical_donts_bn=["উত্তর-পশ্চিমে অগ্নিতত্ত্ব বা গ্যাস ওভেন রাখবেন না", "অতিরিক্ত ভারী আলমারি রাখবেন না"],
        talismanic_remedy_bn="উত্তর-পশ্চিম কোণে কাচের পাত্রে খাঁটি কর্পূর ও রূপার চাঁদের প্রতীক স্থাপন করুন।"
    ),
    AstroVastuRule(
        planet_id="mars",
        planet_name_bn="মঙ্গল (Mars)",
        governing_direction="South (দক্ষিণ দিক)",
        element="Fire (অগ্নি)",
        importance_during_dasha_bn="মঙ্গলের মহাদশায় সাহস, জমি-সম্পত্তি, ভ্রাতৃসুখ ও রক্ত সংবহনের সুস্থতায় দক্ষিণ দিক ও অগ্নিকোণ সক্রিয় রাখা প্রয়োজন।",
        critical_dos_bn=["দক্ষিণ দেওয়ালে লাল রঙ বা লাল ঘোড়ার ছবি রাখুন", "অগ্নিকোণ পরিষ্কার রাখুন"],
        critical_donts_bn=["দক্ষিণে আন্ডারগ্রাউন্ড ওয়াটার বা নীল রঙ রাখবেন না", "দক্ষিণ খোলা রেখে উত্তর বন্ধ করবেন না"],
        talismanic_remedy_bn="দক্ষিণ দেওয়ালে উত্তরমূখী ১২টি তেজস্বী লাল ঘোড়ার প্রতিকৃতি স্থাপন করুন।"
    ),
    AstroVastuRule(
        planet_id="mercury",
        planet_name_bn="বুধ (Mercury)",
        governing_direction="North (উত্তর দিক)",
        element="Water/Earth (জল ও বুধ)",
        importance_during_dasha_bn="বুধের মহাদশায় ব্যবসা, বুদ্ধিদীপ্ত সিদ্ধান্ত, নতুন ক্লায়েন্ট ও তারল্য বৃদ্ধিতে উত্তর দিক সক্রিয় রাখা সর্বোত্তম।",
        critical_dos_bn=["উত্তরে সবুজ মানিপ্ল্যান্ট ও পিতলের কুবের মূর্তি রাখুন", "উত্তর দিক খোলামেলা ও পরিষ্কার রাখুন"],
        critical_donts_bn=["উত্তরে লাল/কমলা রঙ বা রান্নাঘরের বার্নার রাখবেন না", "উত্তরে ভারী লোহালক্কড় রাখবেন না"],
        talismanic_remedy_bn="উত্তর দেওয়ালে একটি সমৃদ্ধ সবুজ বনের দৃশ্য বা পিতলের কুবের যন্ত্র স্থাপন করুন।"
    ),
    AstroVastuRule(
        planet_id="jupiter",
        planet_name_bn="বৃহস্পতি (Jupiter)",
        governing_direction="NE (উত্তর-পূর্ব / ঈশান)",
        element="Water/Ether (জল ও আকাশ)",
        importance_during_dasha_bn="বৃহস্পতির মহাদশায় উচ্চশিক্ষা, আধ্যাত্মিক জ্ঞান, সুসন্তান ও দীর্ঘস্থায়ী ভাগ্যোন্নয়নে ঈশান কোণ ১০০% পবিত্র থাকতে হবে।",
        critical_dos_bn=["ঈশানে পূজা ঘর ও স্ফটিক মালা রাখুন", "হালকা হলুদ বা অফ-হোয়াইট রঙ রাখুন"],
        critical_donts_bn=["ঈশানে জুতো, ডাস্টবিন, ভারী সিঁড়ি বা টয়লেট রাখবেন না", "ঈশানে রান্নাঘর রাখবেন না"],
        talismanic_remedy_bn="ঈশান কোণে পিতলের পাত্রে পবিত্র গঙ্গাজল ও একটি কাঁচা হলুদ রাখুন।"
    ),
    AstroVastuRule(
        planet_id="venus",
        planet_name_bn="শুক্র (Venus)",
        governing_direction="SE (দক্ষিণ-পূর্ব / অগ্নিকোণ)",
        element="Fire (অগ্নি)",
        importance_during_dasha_bn="শুক্রের মহাদশায় বৈবাহিক সৌভাগ্য, লাক্সারি, নারী সঙ্গ ও নগদ অর্থের প্রাচুর্য পেতে দক্ষিণ-পূর্ব কোণ প্রজ্বলিত থাকা দরকার।",
        critical_dos_bn=["দক্ষিণ-পূর্বে রান্নাঘর রাখুন এবং ১৫ ওয়াট লাল বাল্ব জ্বালান", "রুপোর পাত্রে চন্দন রাখুন"],
        critical_donts_bn=["দক্ষিণ-পূর্বে জলের ট্যাপ, ওয়াশ বেসিন বা নীল রঙ রাখবেন না"],
        talismanic_remedy_bn="দক্ষিণ-পূর্ব দেওয়ালে একটি জ্বলন্ত প্রদীপের চিত্র বা গোলাপী কোয়ার্টজ ক্রিস্টাল রাখুন।"
    ),
    AstroVastuRule(
        planet_id="saturn",
        planet_name_bn="শনি (Saturn)",
        governing_direction="West (পশ্চিম দিক)",
        element="Space/Air (আকাশ ও বায়ু)",
        importance_during_dasha_bn="শনির মহাদশায় কর্মক্ষেত্রে দীর্ঘস্থায়ী লাভ, ধৈর্য ও স্থায়িত্ব অর্জনের জন্য পশ্চিম দিক সুশৃঙ্খল থাকা আবশ্যক।",
        critical_dos_bn=["পশ্চিমে ডাইনিং রুম বা অধ্যয়নের স্থান রাখুন", "ধাতব বা রূপালী আসবাব রাখুন"],
        critical_donts_bn=["পশ্চিমে আবর্জনা বা লাল রঙের ছটা রাখবেন না", "পশ্চিম দিক নিচু করবেন না"],
        talismanic_remedy_bn="পশ্চিম দিকে কালো ঘোড়ার নাল বা স্টেইনলেস স্টিল চক্র স্থাপন করুন।"
    ),
    AstroVastuRule(
        planet_id="rahu",
        planet_name_bn="রাহু (Rahu)",
        governing_direction="SW (দক্ষিণ-পশ্চিম / নৈঋত)",
        element="Earth (পৃথিবী)",
        importance_during_dasha_bn="রাহুর মহাদশায় আকস্মিক দুর্ঘটনা, আইনি ঝামেলা ও পারিবারিক সংকট এড়াতে দক্ষিণ-পশ্চিম কোণ সুরক্ষিত রাখা জীবনরক্ষাকারী।",
        critical_dos_bn=["দক্ষিণ-পশ্চিম সবচেয়ে উঁচু ও ভারী রাখুন", "হলুদ বা মাটির রঙ ব্যবহার করুন", "মাস্টার বেডরুম এখানে রাখুন"],
        critical_donts_bn=["নৈঋতে টয়লেট বা আন্ডারগ্রাউন্ড ওয়াটার চরম বিপর্যয় ডেকে আনে", "SW-তে কাটা কোণ রাখবেন না"],
        talismanic_remedy_bn="দক্ষিণ-পশ্চিমের মেঝের খাঁজে ৪ মিমি ব্রাস ও লেড স্ট্রিপ বসিয়ে সিল করুন এবং ভারী পিতলের হাতি রাখুন।"
    ),
    AstroVastuRule(
        planet_id="ketu",
        planet_name_bn="কেতু (Ketu)",
        governing_direction="NE / Brahmasthan (কেন্দ্র ও ঈশান)",
        element="Ether (আকাশ)",
        importance_during_dasha_bn="কেতুর মহাদশায় মোক্ষ, গুপ্তবিদ্যা ও আত্মিক জাগরণে ব্রহ্মস্থান সম্পূর্ণ ফাঁকা ও আলোকিত রাখা উচিত।",
        critical_dos_bn=["ঘরের কেন্দ্র সম্পূর্ণ ভারমুক্ত ও পরিচ্ছন্ন রাখুন", "ঈশানে রূপার স্বস্তিক প্রতীক রাখুন"],
        critical_donts_bn=["ব্রহ্মস্থানে পিলার, ভারী দেওয়াল বা সেপটিক ট্যাংক রাখবেন না"],
        talismanic_remedy_bn="ব্রহ্মস্থানে একটি অষ্টকোণী পিতলের সূর্য বা শ্রীযন্ত্র স্থাপন করুন।"
    ),
]


def get_astrovastu_rules(planet_id: str | None = None) -> list[AstroVastuRule]:
    """Returns AstroVastu planetary directions and guidelines."""
    if planet_id:
        return [r for r in ASTROVASTU_RULES if r.planet_id == planet_id.lower()]
    return ASTROVASTU_RULES

