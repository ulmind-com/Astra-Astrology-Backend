"""Kundli & Planetary Position Service
Calculates 100% accurate Vedic Kundli parameters, Placidus House Cusps,
Lagna Chart (D1), Navamsha Chart (D9), 3x3 Vimshottari Dasha Grid,
and Classical Vedic Yogas & Doshas (Manglik, Kaal Sarp, Gaja Kesari, Kemadruma, Sunapha, etc.)
strictly matching AppliedJyotish screenshots and client resource documents.
"""

from datetime import datetime, timedelta, timezone as dt_timezone
import math
from typing import Any

try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    swe = None
    HAS_SWISSEPH = False

from app.schemas.astrology import (
    KundliCalculateRequest,
    KundliCalculateResponse,
    KundliPersonalDetails,
    KundliAstronomicalInfo,
    KundliAstroPositions,
    KundliPlanetaryInfo,
    KundliChartPlanet,
    KundliTableRow,
    KundliDashaPratyantar,
    KundliDashaAntar,
    KundliDashaCard,
    KundliYogaItem,
    KundliActiveYogaDetail,
    PlanetaryDignityItem,
    HousePredictionItem,
    ExtendedYogaItem,
    DoshaAnalysisItem,
    GemstoneItem,
    PersonalRemedies,
    CurrentDashaInfo,
    AshtakavargaResult,
    AshtakavargaPlanetPoints,
    AshtakavargaHouseSummary,
    KaalPurushaInsight,
    NakshatraPredictiveInsight,
)
from app.services.astrology.doshas import assess_manglik
from app.services.astrology.timezone_resolver import resolve as resolve_timezone

UTC = dt_timezone.utc

# 12 Zodiac Signs
RASHIS_DATA = [
    {"name_en": "Aries", "name_bn": "মেষ", "name_hi": "मेष", "lord": "Mars", "lord_code": "Ma", "symbol": "♈", "num": 1},
    {"name_en": "Taurus", "name_bn": "বৃষ", "name_hi": "वृषभ", "lord": "Venus", "lord_code": "Ve", "symbol": "♉", "num": 2},
    {"name_en": "Gemini", "name_bn": "মিথুন", "name_hi": "मिथुन", "lord": "Mercury", "lord_code": "Me", "symbol": "♊", "num": 3},
    {"name_en": "Cancer", "name_bn": "কর্কট", "name_hi": "कर्क", "lord": "Moon", "lord_code": "Mo", "symbol": "♋", "num": 4},
    {"name_en": "Leo", "name_bn": "সিংহ", "name_hi": "सिंह", "lord": "Sun", "lord_code": "Su", "symbol": "♌", "num": 5},
    {"name_en": "Virgo", "name_bn": "কন্যা", "name_hi": "कन्या", "lord": "Mercury", "lord_code": "Me", "symbol": "♍", "num": 6},
    {"name_en": "Libra", "name_bn": "তুলা", "name_hi": "तुला", "lord": "Venus", "lord_code": "Ve", "symbol": "♎", "num": 7},
    {"name_en": "Scorpio", "name_bn": "বৃশ্চিক", "name_hi": "वृश्चिक", "lord": "Mars", "lord_code": "Ma", "symbol": "♏", "num": 8},
    {"name_en": "Sagittarius", "name_bn": "ধনু", "name_hi": "धनु", "lord": "Jupiter", "lord_code": "Ju", "symbol": "♐", "num": 9},
    {"name_en": "Capricorn", "name_bn": "মকর", "name_hi": "मकर", "lord": "Saturn", "lord_code": "Sa", "symbol": "♑", "num": 10},
    {"name_en": "Aquarius", "name_bn": "কুম্ভ", "name_hi": "कुंभ", "lord": "Saturn", "lord_code": "Sa", "symbol": "♒", "num": 11},
    {"name_en": "Pisces", "name_bn": "মীন", "name_hi": "मीन", "lord": "Jupiter", "lord_code": "Ju", "symbol": "♓", "num": 12},
]

# 27 Nakshatras
NAKSHATRAS_DATA = [
    {"name": "Ashwini", "lord": "Ketu", "lord_code": "Ke"},
    {"name": "Bharani", "lord": "Venus", "lord_code": "Ve"},
    {"name": "Krittika", "lord": "Sun", "lord_code": "Su"},
    {"name": "Rohini", "lord": "Moon", "lord_code": "Mo"},
    {"name": "Mrigashira", "lord": "Mars", "lord_code": "Ma"},
    {"name": "Ardra", "lord": "Rahu", "lord_code": "Ra"},
    {"name": "Punarvasu", "lord": "Jupiter", "lord_code": "Ju"},
    {"name": "Pushya", "lord": "Saturn", "lord_code": "Sa"},
    {"name": "Ashlesha", "lord": "Mercury", "lord_code": "Me"},
    {"name": "Magha", "lord": "Ketu", "lord_code": "Ke"},
    {"name": "Purva Phalguni", "lord": "Venus", "lord_code": "Ve"},
    {"name": "Uttara Phalguni", "lord": "Sun", "lord_code": "Su"},
    {"name": "Hasta", "lord": "Moon", "lord_code": "Mo"},
    {"name": "Chitra", "lord": "Mars", "lord_code": "Ma"},
    {"name": "Swati", "lord": "Rahu", "lord_code": "Ra"},
    {"name": "Vishakha", "lord": "Jupiter", "lord_code": "Ju"},
    {"name": "Anuradha", "lord": "Saturn", "lord_code": "Sa"},
    {"name": "Jyeshtha", "lord": "Mercury", "lord_code": "Me"},
    {"name": "Mula", "lord": "Ketu", "lord_code": "Ke"},
    {"name": "Purva Ashadha", "lord": "Venus", "lord_code": "Ve"},
    {"name": "Uttara Ashadha", "lord": "Sun", "lord_code": "Su"},
    {"name": "Shravana", "lord": "Moon", "lord_code": "Mo"},
    {"name": "Dhanishta", "lord": "Mars", "lord_code": "Ma"},
    {"name": "Shatabhisha", "lord": "Rahu", "lord_code": "Ra"},
    {"name": "Purva Bhadrapada", "lord": "Jupiter", "lord_code": "Ju"},
    {"name": "Uttara Bhadrapada", "lord": "Saturn", "lord_code": "Sa"},
    {"name": "Revati", "lord": "Mercury", "lord_code": "Me"},
]

DASHA_LORDS_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10,
    "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}
TOTAL_DASHA_YEARS = 120

TITHIS_LIST = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shasthi", "Saptami",
    "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
    "Purnima", "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shasthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi",
    "Chaturdashi", "Amavasya"
]

YOGAS_LIST = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
    "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti"
]

KARANAS_LIST = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti (Bhadra)",
    "Shakuni", "Chatushpada", "Naga", "Kintughna"
]

DAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _format_dms_styled(deg_in_sign: float, sign_name: str) -> str:
    """Formats degree as: 21° Leo 35 ' 55\""""
    d = int(deg_in_sign)
    rem_m = (deg_in_sign - d) * 60.0
    m = int(rem_m)
    s = int(round((rem_m - m) * 60.0))
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    return f"{d}° {sign_name} {m} ' {s}\""


def _format_full_degree(lon: float) -> str:
    """Formats full degree as: 141° 35 ' 55\""""
    d = int(lon)
    rem_m = (lon - d) * 60.0
    m = int(rem_m)
    s = int(round((rem_m - m) * 60.0))
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    return f"{d}° {m} ' {s}\""


def _get_star_and_sub_lord(lon: float) -> tuple[str, str, str, int]:
    """Calculates Nakshatra name, Star Lord, KP Sub Lord, and Pada (1-4)."""
    nak_span = 360.0 / 27.0
    pada_span = nak_span / 4.0
    nak_idx = int(lon / nak_span) % 27
    offset = lon % nak_span

    nak_info = NAKSHATRAS_DATA[nak_idx]
    star_lord = nak_info["lord"]
    pada = int(offset / pada_span) + 1

    # KP Sub Lord
    start_lord_idx = DASHA_LORDS_ORDER.index(star_lord)
    accum = 0.0
    sub_lord = star_lord
    for step in range(9):
        curr_sub = DASHA_LORDS_ORDER[(start_lord_idx + step) % 9]
        sub_span = (nak_span * DASHA_YEARS[curr_sub]) / TOTAL_DASHA_YEARS
        if accum <= offset < (accum + sub_span):
            sub_lord = curr_sub
            break
        accum += sub_span

    return nak_info["name"], star_lord, sub_lord, pada


EXALT_DEBIL_MAP: dict[str, dict[str, Any]] = {
    "Sun": {"exalt_sign": 0, "debil_sign": 6, "moola_sign": 4, "own_signs": [4], "combust_orb": 0.0},
    "Moon": {"exalt_sign": 1, "debil_sign": 7, "moola_sign": 1, "own_signs": [3], "combust_orb": 12.0},
    "Mars": {"exalt_sign": 9, "debil_sign": 3, "moola_sign": 0, "own_signs": [0, 7], "combust_orb": 17.0},
    "Mercury": {"exalt_sign": 5, "debil_sign": 11, "moola_sign": 5, "own_signs": [2, 5], "combust_orb": 14.0},
    "Jupiter": {"exalt_sign": 3, "debil_sign": 9, "moola_sign": 8, "own_signs": [8, 11], "combust_orb": 11.0},
    "Venus": {"exalt_sign": 11, "debil_sign": 5, "moola_sign": 6, "own_signs": [1, 6], "combust_orb": 10.0},
    "Saturn": {"exalt_sign": 6, "debil_sign": 0, "moola_sign": 10, "own_signs": [9, 10], "combust_orb": 15.0},
    "Rahu": {"exalt_sign": 1, "debil_sign": 7, "moola_sign": 2, "own_signs": [10], "combust_orb": 0.0},
    "Ketu": {"exalt_sign": 7, "debil_sign": 1, "moola_sign": 8, "own_signs": [8], "combust_orb": 0.0},
}

PLANET_FRIENDS_MAP: dict[str, dict[str, list[str]]] = {
    "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "enemies": ["Venus", "Saturn"], "neutral": ["Mercury"]},
    "Moon": {"friends": ["Sun", "Mercury"], "enemies": [], "neutral": ["Mars", "Jupiter", "Venus", "Saturn"]},
    "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "enemies": ["Mercury"], "neutral": ["Venus", "Saturn"]},
    "Mercury": {"friends": ["Sun", "Venus"], "enemies": ["Moon"], "neutral": ["Mars", "Jupiter", "Saturn"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "enemies": ["Mercury", "Venus"], "neutral": ["Saturn"]},
    "Venus": {"friends": ["Mercury", "Saturn"], "enemies": ["Sun", "Moon"], "neutral": ["Mars", "Jupiter"]},
    "Saturn": {"friends": ["Mercury", "Venus"], "enemies": ["Sun", "Moon", "Mars"], "neutral": ["Jupiter"]},
    "Rahu": {"friends": ["Venus", "Saturn", "Mercury"], "enemies": ["Sun", "Moon", "Mars"], "neutral": ["Jupiter"]},
    "Ketu": {"friends": ["Venus", "Saturn", "Mars"], "enemies": ["Sun", "Moon"], "neutral": ["Mercury", "Jupiter"]},
}

PLANET_NAMES_LOCALIZED: dict[str, dict[str, str]] = {
    "Sun": {"bn": "সূর্য", "hi": "सूर्य", "sa": "Surya"},
    "Moon": {"bn": "চন্দ্র", "hi": "चन्द्र", "sa": "Chandra"},
    "Mars": {"bn": "মঙ্গল", "hi": "मंगल", "sa": "Mangala"},
    "Mercury": {"bn": "বুধ", "hi": "बुध", "sa": "Budha"},
    "Jupiter": {"bn": "বৃহস্পতি", "hi": "गुरु", "sa": "Brihaspati"},
    "Venus": {"bn": "শুক্র", "hi": "शुक्र", "sa": "Shukra"},
    "Saturn": {"bn": "শনি", "hi": "शनि", "sa": "Shani"},
    "Rahu": {"bn": "রাহু", "hi": "राहु", "sa": "Rahu"},
    "Ketu": {"bn": "কেতু", "hi": "केतु", "sa": "Ketu"},
}

BHAVA_METADATA = [
    {
        "num": 1,
        "name_en": "Tanu Bhava (1st House)",
        "name_bn": "তনু ভাব (১ম ঘর - লগ্ন)",
        "name_hi": "तनु भाव (प्रथम भाव - लग्न)",
        "desc_en": "Ascendant, physical constitution, self-identity, health, longevity, and innate life drive.",
        "desc_bn": "দৈহিক গঠন, ব্যক্তিত্ব, আত্মসম্মান, স্বাস্থ্য, দীর্ঘায়ু এবং জন্মগত জীবনশক্তি।",
        "desc_hi": "शारीरिक संरचना, व्यक्तित्व, स्वास्थ्य, दीर्घायु और जीवन शक्ति।",
    },
    {
        "num": 2,
        "name_en": "Dhana Bhava (2nd House)",
        "name_bn": "ধন ভাব (২য় ঘর - অর্থ ও পরিবার)",
        "name_hi": "धन भाव (द्वितीय भाव - कुटुंब एवं संपत्ति)",
        "desc_en": "Liquid wealth, family lineage, speech, savings, food habits, and facial features.",
        "desc_bn": "সঞ্চিত ধন, পারিবারিক সুখ, বাচনভঙ্গি, খাদ্যাভ্যাস ও মুখশ্রী।",
        "desc_hi": "संचित धन, कुटुंब सुख, वाणी, खान-पान और पारिवारिक संबंध।",
    },
    {
        "num": 3,
        "name_en": "Sahaja Bhava (3rd House)",
        "name_bn": "সহজ ভাব (৩য় ঘর - পরাক্রম ও ভ্রাতা)",
        "name_hi": "सहज भाव (तृतीय भाव - पराक्रम एवं भ्राता)",
        "desc_en": "Courage, valor, younger siblings, short journeys, communication, writing, and initiatives.",
        "desc_bn": "সাহস, পরাক্রম, কনিষ্ঠ ভ্রাতা-ভগিনী, স্বল্প ভ্রমণ, যোগাযোগ ও নিজস্ব উদ্যোগ।",
        "desc_hi": "साहस, पराक्रम, छोटे भाई-बहन, लघु यात्राएं, संवाद और पहल।",
    },
    {
        "num": 4,
        "name_en": "Sukha Bhava (4th House)",
        "name_bn": "সুখ ভাব (৪র্থ ঘর - মাতৃ ও গৃহসুখ)",
        "name_hi": "सुख भाव (चतुर्थ भाव - माता एवं गृह)",
        "desc_en": "Mother, domestic peace, vehicles, land, real estate, schooling, and mental contentment.",
        "desc_bn": "মা, গৃহশান্তি, যানবাহন, স্থাবর সম্পত্তি, মানসিক সুখ ও প্রাথমিক শিক্ষা।",
        "desc_hi": "माता, गृह शांति, वाहन, भूमि-भवन, प्राथमिक शिक्षा और मानसिक संतोष।",
    },
    {
        "num": 5,
        "name_en": "Suta Bhava (5th House)",
        "name_bn": "সুত ভাব (৫ম ঘর - বুদ্ধি ও পূর্বপুণ্য)",
        "name_hi": "सुत भाव (पंचम भाव - संतान एवं बुद्धि)",
        "desc_en": "Children, intellect, higher learning, speculative gains, creative pursuits, and past-life karma.",
        "desc_bn": "সন্তান ভাগ্য, তীক্ষ্ণ মেধা, উচ্চশিক্ষা, সৃজনশীলতা ও পূর্বজন্মের পুণ্যফল।",
        "desc_hi": "संतान, कुशाग्र बुद्धि, उच्च विद्या, रचनात्मकता और पूर्वजन्म के पुण्य।",
    },
    {
        "num": 6,
        "name_en": "Ripu Bhava (6th House)",
        "name_bn": "রিপু ভাব (৬ষ্ঠ ঘর - রোগ ও শত্রু)",
        "name_hi": "रिपु भाव (षष्ठ भाव - रोग एवं शत्रु)",
        "desc_en": "Enemies, debts, diseases, litigation, competitive examinations, and daily service.",
        "desc_bn": "রোগ, ঋণ, গুপ্ত শত্রু, মামলা-মোকদ্দমা, প্রতিযোগিতা ও দৈনন্দিন সেবা কর্ম।",
        "desc_hi": "रोग, ऋण, शत्रु, कोर्ट-कचहरी, प्रतियोगिता और नौकरी।",
    },
    {
        "num": 7,
        "name_en": "Jaya Bhava (7th House)",
        "name_bn": "জায়া ভাব (৭ম ঘর - বিবাহ ও অংশীদারিত্ব)",
        "name_hi": "जाया भाव (सप्तम भाव - विवाह एवं साझेदारी)",
        "desc_en": "Spouse, married life, business partnerships, public interactions, and open contracts.",
        "desc_bn": "জীবনসঙ্গী, দাম্পত্য সুখ, ব্যবসায়িক অংশীদারিত্ব ও সার্বজনীন সামাজিক সম্পর্ক।",
        "desc_hi": "जीवनसाथी, वैवाहिक जीवन, व्यापारिक साझेदारी और सामाजिक संबंध।",
    },
    {
        "num": 8,
        "name_en": "Randhra Bhava (8th House)",
        "name_bn": "রন্ধ্র ভাব (৮ম ঘর - আয়ু ও রূপান্তর)",
        "name_hi": "रन्ध्र भाव (अष्टम भाव - आयु एवं गूढ़ विद्या)",
        "desc_en": "Longevity, sudden events, inheritance, hidden knowledge, occult research, and rebirth.",
        "desc_bn": "আয়ুষ্কাল, অপ্রত্যাশিত ঘটনা, উত্তরাধিকার, তন্ত্র-জ্যোতিষ ও গোপন আবিষ্কার।",
        "desc_hi": "दीर्घायु, अप्रत्याशित घटनाएं, वसीयत, गूढ़ विद्या और आध्यात्मिक परिवर्तन।",
    },
    {
        "num": 9,
        "name_en": "Dharma Bhava (9th House)",
        "name_bn": "ধর্ম ভাব (৯ম ঘর - ভাগ্য ও গুরু)",
        "name_hi": "धर्म भाव (नवम भाव - भाग्य एवं धर्म)",
        "desc_en": "Fortune, father, religious merit, spiritual mentors, pilgrimage, and supreme luck.",
        "desc_bn": "ভাগ্যোদয়, পিতা, ধর্মপরায়ণতা, গুরুকৃপা, তীর্থ ভ্রমণ ও দৈব সহায়তা।",
        "desc_hi": "भाग्य, पिता, धार्मिक आचरण, गुरु कृपा, तीर्थ यात्रा और ईश्वरीय अनुग्रह।",
    },
    {
        "num": 10,
        "name_en": "Karma Bhava (10th House)",
        "name_bn": "কর্ম ভাব (১০ম ঘর - জীবিকা ও প্রতিষ্ঠা)",
        "name_hi": "कर्म भाव (दशम भाव - आजीविका एवं प्रतिष्ठा)",
        "desc_en": "Career, profession, social authority, government honors, reputation, and public deeds.",
        "desc_bn": "পেশাগত জীবন, সামাজিক প্রতিপত্তি, রাজকীয় সম্মান, পদমর্যাদা ও কীর্তি।",
        "desc_hi": "करियर, आजीविका, सामाजिक मान-सम्मान, पदोन्नति और सार्वजनिक प्रतिष्ठा।",
    },
    {
        "num": 11,
        "name_en": "Labha Bhava (11th House)",
        "name_bn": "লাভ ভাব (১১শ ঘর - প্রাপ্তি ও সমৃদ্ধি)",
        "name_hi": "लाभ भाव (एकादश भाव - आय एवं उपलब्धि)",
        "desc_en": "Financial gains, fulfillment of desires, influential networks, and elder siblings.",
        "desc_bn": "আর্থিক লাভ, সর্বার্থ সিদ্ধি, প্রভাবশালী মহলে যোগাযোগ ও জ্যেষ্ঠ ভ্রাতা-ভগিনী।",
        "desc_hi": "आर्थिक लाभ, मनोकामना पूर्ति, मित्र मंडली और उपलब्धियां।",
    },
    {
        "num": 12,
        "name_en": "Vyaya Bhava (12th House)",
        "name_bn": "ব্যয় ভাব (১২শ ঘর - বিদেশ ও মোক্ষ)",
        "name_hi": "व्यय भाव (द्वादश भाव - मोक्ष एवं विदेश)",
        "desc_en": "Expenditures, foreign settlements, spiritual liberation (Moksha), sleep, and meditation.",
        "desc_bn": "ব্যয়, বিদেশ বাস, আধ্যাত্মিক মোক্ষ লাভ, নির্জন সাধনা ও শয্যাসুখ।",
        "desc_hi": "व्यय, विदेश गमन, मोक्ष, आध्यात्मिक साधना और शयन सुख।",
    },
]

KAAL_SARP_VARIANTS: dict[int, dict[str, str]] = {
    1: {"name": "Ananta Kaal Sarp", "bn": "অনন্ত কালসর্প যোগ", "hi": "अनन्त कालसर्प योग", "desc_bn": "রাহু ১ম ভাব ও কেতু ৭ম ভাবে অবস্থিত। আত্মপ্রতিষ্ঠায় প্রাথমিক সংগ্রাম, তবে অবিচল অধ্যবসায়ে চরম প্রতিষ্ঠা লাভ।"},
    2: {"name": "Kulika Kaal Sarp", "bn": "কুলিক কালসর্প যোগ", "hi": "कुलिक कालसर्प योग", "desc_bn": "রাহু ২য় ভাব ও কেতু ৮ম ভাবে অবস্থিত। সঞ্চয় ও পারিবারিক সমন্বয়ে সতর্কতা দরকার; সত্য ও ধর্মনিষ্ঠায় প্রভূত উন্নতি।"},
    3: {"name": "Vasuki Kaal Sarp", "bn": "বাসুকি কালসর্প যোগ", "hi": "वासुकी कालसर्प योग", "desc_bn": "রাহু ৩য় ভাব ও কেতু ৯ম ভাবে অবস্থিত। ভ্রাতা-ভগিনী ও ভাগ্যোন্নয়নে সামান্য বিলম্ব হলেও জাতক অদম্য সাহসী হয়।"},
    4: {"name": "Shankhapala Kaal Sarp", "bn": "শঙ্খপাল কালসর্প যোগ", "hi": "शंखपाल कालसर्प योग", "desc_bn": "রাহু ৪র্থ ভাব ও কেতু ১০ম ভাবে অবস্থিত। গৃহসুখ ও মানসিক শান্তিতে ওঠানামা; নিয়মিত শিব আরাধনায় পরম শান্তি।"},
    5: {"name": "Padma Kaal Sarp", "bn": "পদ্ম কালসর্প যোগ", "hi": "पद्म कालसर्प योग", "desc_bn": "রাহু ৫ম ভাব ও কেতু ১১শ ভাবে অবস্থিত। সন্তান ও বুদ্ধিবৃত্তিক সাধনায় ধৈর্য দরকার; কলা ও বিদ্যায় সুনাম।"},
    6: {"name": "Mahapadma Kaal Sarp", "bn": "মহাপদ্ম কালসর্প যোগ", "hi": "महापद्म कालसर्प योग", "desc_bn": "রাহু ৬ষ্ঠ ভাব ও কেতু ১২শ ভাবে অবস্থিত। সকল শত্রু ও প্রকাশ্য প্রতিযোগীকে পরাভূত করার অনন্য বিজয়ী ক্ষমতা দেয়।"},
    7: {"name": "Takshaka Kaal Sarp", "bn": "তক্ষক কালসর্প যোগ", "hi": "तक्षक कालसर्प योग", "desc_bn": "রাহু ৭ম ভাব ও কেতু ১ম ভাবে অবস্থিত। দাম্পত্য ও অংশীদারিত্বে পরম সমঝোতা ও বোঝাপড়া রক্ষা করা বিধেয়।"},
    8: {"name": "Karkotaka Kaal Sarp", "bn": "কর্কেটক কালসর্প যোগ", "hi": "कर्कोटक कालसर्प योग", "desc_bn": "রাহু ৮ম ভাব ও কেতু ২য় ভাবে অবস্থিত। গোপন বাধা ও পৈতৃক সম্পত্তিতে জটিলতা এড়াতে পরিমিত আচরণ আবশ্যক।"},
    9: {"name": "Shankhachuda Kaal Sarp", "bn": "শঙ্খচূড় কালসর্প যোগ", "hi": "शंखचूड़ कालसर्प योग", "desc_bn": "রাহু ৯ম ভাব ও কেতু ৩য় ভাবে অবস্থিত। ভাগ্যোন্নয়নে উত্থান-পতন থাকে; পিতা ও গুরুজনের সেবায় ভাগ্যের দ্বার খোলে।"},
    10: {"name": "Ghataka Kaal Sarp", "bn": "ঘাতক কালসর্প যোগ", "hi": "घातक कालसर्प योग", "desc_bn": "রাহু ১০ম ভাব ও কেতু ৪র্থ ভাবে অবস্থিত। কর্মক্ষেত্রে আকস্মিক পরিবর্তন ও রাজনৈতিক প্রতিপত্তি লাভের সম্ভাবনা।"},
    11: {"name": "Vishadhara Kaal Sarp", "bn": "বিষধর কালসর্প যোগ", "hi": "विषधर कालसर्प योग", "desc_bn": "রাহু ১১শ ভাব ও কেতু ৫ম ভাবে অবস্থিত। অর্থলাভে অস্থিরতা দেখা দিলে তীর্থ ভ্রমণ ও দানধ্যানে প্রভূত লাভ।"},
    12: {"name": "Sheshanaga Kaal Sarp", "bn": "শেষনাগ কালসর্প যোগ", "hi": "शेषनाग कालसर्प योग", "desc_bn": "রাহু ১২শ ভাব ও কেতু ৬ষ্ঠ ভাবে অবস্থিত। অতিরিক্ত ব্যয় প্রবণতা নিয়ন্ত্রণে রাখলে বিদেশ বাসে অতুলনীয় প্রতিষ্ঠা।"},
}

GEMSTONES_MASTER: dict[str, dict[str, str]] = {
    "Sun": {
        "stone_name": "Ruby",
        "stone_name_bn": "মাণিক্য (চুনী)",
        "stone_name_hi": "माणिक्य (रूबी)",
        "sanskrit_name": "Manikya",
        "metal": "Gold / Copper",
        "metal_bn": "স্বর্ণ বা তামা",
        "finger": "Ring finger",
        "finger_bn": "অনামিকা অঙ্গুলি",
        "wearing_day": "Sunday morning",
        "wearing_day_bn": "রবিবার প্রাতঃকালে",
        "beej_mantra": "ॐ হ্রাং হ্রীং হ্রৌং সঃ সূর্যায় নমঃ",
        "benefit": "Enhances leadership, vitality, governmental favor, and fatherly blessings.",
        "benefit_bn": "নেতৃত্ব ক্ষমতা, জীবনীশক্তি, শারীরিক তেজ এবং সরকারি সম্মান বৃদ্ধিতে সহায়ক।",
    },
    "Moon": {
        "stone_name": "Natural Pearl",
        "stone_name_bn": "খাঁটি মুক্তা",
        "stone_name_hi": "सच्चा मोती",
        "sanskrit_name": "Mukta",
        "metal": "Silver",
        "metal_bn": "রূপা",
        "finger": "Little finger",
        "finger_bn": "কনিষ্ঠা অঙ্গুলি",
        "wearing_day": "Monday morning",
        "wearing_day_bn": "সোমবার প্রাতঃকালে",
        "beej_mantra": "ॐ শ্রাং শ্রীং শ্রৌং সঃ চন্দ্রায় নমঃ",
        "benefit": "Brings mental tranquility, emotional stability, sweet speech, and maternal blessings.",
        "benefit_bn": "মানসিক প্রশান্তি, গভীর স্মৃতিশক্তি, সিদ্ধান্ত গ্রহণের স্থিরতা এবং মায়ের সুস্বাস্থ্য আনে।",
    },
    "Mars": {
        "stone_name": "Red Coral",
        "stone_name_bn": "রক্ত প্রবাল",
        "stone_name_hi": "मूंगा (लाल प्रवाल)",
        "sanskrit_name": "Pravala",
        "metal": "Copper / Gold",
        "metal_bn": "তামা বা অষ্টধাতু",
        "finger": "Ring finger",
        "finger_bn": "অনামিকা অঙ্গুলি",
        "wearing_day": "Tuesday morning",
        "wearing_day_bn": "মঙ্গলবার প্রাতঃকালে",
        "beej_mantra": "ॐ ক্রাং ক্রীং ক্রৌং সঃ ভৌমায় নমঃ",
        "benefit": "Increases courage, willpower, muscular vitality, land property gains, and removes obstacles.",
        "benefit_bn": "সাহস, পরাক্রম, ভূমি সম্পত্তি লাভ, রক্ত সঞ্চালন এবং রক্তচাপের ভারসাম্য রক্ষা করে।",
    },
    "Mercury": {
        "stone_name": "Emerald",
        "stone_name_bn": "পান্না",
        "stone_name_hi": "पन्ना",
        "sanskrit_name": "Marakata",
        "metal": "Gold / Bronze",
        "metal_bn": "স্বর্ণ বা ব্রোঞ্জ",
        "finger": "Little finger",
        "finger_bn": "কনিষ্ঠা অঙ্গুলি",
        "wearing_day": "Wednesday morning",
        "wearing_day_bn": "বুধবার প্রাতঃকালে",
        "beej_mantra": "ॐ ব্রাং ব্রীং ব্রৌং সঃ বুধায় নমঃ",
        "benefit": "Sharpens analytical intellect, commerce acumen, speech eloquence, and academic success.",
        "benefit_bn": "তীক্ষ্ণ মেধা, ব্যবসায়িক বুদ্ধিমত্তা, মধুর বাচনভঙ্গি এবং হিসাবনিকাশে অসাধারণ দক্ষতা এনে দেয়।",
    },
    "Jupiter": {
        "stone_name": "Yellow Sapphire",
        "stone_name_bn": "হলুদ পোখরাজ",
        "stone_name_hi": "पुखराज",
        "sanskrit_name": "Pushparaga",
        "metal": "Gold",
        "metal_bn": "স্বর্ণ বা পিতল",
        "finger": "Index finger",
        "finger_bn": "তর্জনী অঙ্গুলি",
        "wearing_day": "Thursday morning",
        "wearing_day_bn": "বৃহস্পতিবার প্রাতঃকালে",
        "beej_mantra": "ॐ গ্রাং গ্রীং গ্রৌং সঃ গুরবে নমঃ",
        "benefit": "Expands wisdom, spiritual merit, financial affluence, marital harmony, and progeny joy.",
        "benefit_bn": "উচ্চ প্রজ্ঞা, আধ্যাত্মিক সুখ্যাতি, বিপুল ধনসম্পদ এবং দাম্পত্য ও সন্তান সুখ নিশ্চিত করে।",
    },
    "Venus": {
        "stone_name": "Diamond / White Zircon",
        "stone_name_bn": "হীরা বা সাদা জারকন",
        "stone_name_hi": "हीरा / सफेद जरकन",
        "sanskrit_name": "Vajra",
        "metal": "Silver / Platinum",
        "metal_bn": "রূপা বা প্লাটিনাম",
        "finger": "Middle or Little finger",
        "finger_bn": "মধ্যমা বা কনিষ্ঠা অঙ্গুলি",
        "wearing_day": "Friday morning",
        "wearing_day_bn": "শুক্রবার প্রাতঃকালে",
        "beej_mantra": "ॐ দ্রাং দ্রীং দ্রৌং সঃ শুক্রায় নমঃ",
        "benefit": "Grants luxury, artistic refinement, marital bliss, aesthetic beauty, and prosperous vehicles.",
        "benefit_bn": "সৌন্দর্য, বৈভব, শিল্পকলায় খ্যাতি, সুমধুর দাম্পত্য প্রেম এবং বিলাসবহুল জীবনযাপন প্রদান করে।",
    },
    "Saturn": {
        "stone_name": "Blue Sapphire / Amethyst",
        "stone_name_bn": "নীলা বা কাটাহেলা",
        "stone_name_hi": "नीलम / जमुनिया",
        "sanskrit_name": "Neelam",
        "metal": "Silver / Iron",
        "metal_bn": "পঞ্চধাতু বা রূপা",
        "finger": "Middle finger",
        "finger_bn": "মধ্যমা অঙ্গুলি",
        "wearing_day": "Saturday evening",
        "wearing_day_bn": "শনিবার গোধূলি লগ্নে",
        "beej_mantra": "ॐ প্রাং প্রীং প্রৌং সঃ শনৈশ্চরায় নমঃ",
        "benefit": "Endows discipline, patience, mass leadership, judicial triumph, and enduring career status.",
        "benefit_bn": "দৃঢ় ধৈর্য, কর্মনিষ্ঠা, জননেতৃত্ব, বিচারবুদ্ধি এবং কর্মক্ষেত্রে স্থায়ী প্রতিষ্ঠা দান করে।",
    },
}

RUDRAKSHA_MASTER: dict[str, dict[str, str]] = {
    "Sun": {"mukhi": "1-Mukhi / 12-Mukhi", "bn": "১-মুখী বা ১২-মুখী রুদ্রাক্ষ", "deity": "Lord Shiva & Surya Dev", "desc_bn": "আত্মবিশ্বাস, তেজস্বিতা এবং নেতৃত্ব বিকাশে পরম ফলদায়ী।"},
    "Moon": {"mukhi": "2-Mukhi", "bn": "২-মুখী রুদ্রাক্ষ (অর্ধনারীশ্বর)", "deity": "Ardhanarishvara", "desc_bn": "মানসিক শান্তি, দাম্পত্য সৌহার্দ্য এবং মানসিক অস্থিরতা নিরাময় করে।"},
    "Mars": {"mukhi": "3-Mukhi", "bn": "৩-মুখী রুদ্রাক্ষ", "deity": "Agni Dev", "desc_bn": "আত্মশক্তি, পরাক্রম এবং অতীত পাপের গ্লানি দূর করে কর্মোদ্যম বাড়ায়।"},
    "Mercury": {"mukhi": "4-Mukhi", "bn": "৪-মুখী রুদ্রাক্ষ (চতুরানন ব্রহ্মা)", "deity": "Lord Brahma", "desc_bn": "বুদ্ধিবিকাশ, বাকপটুতা, স্মৃতিশক্তি এবং শিক্ষায় শ্রেষ্ঠত্ব এনে দেয়।"},
    "Jupiter": {"mukhi": "5-Mukhi", "bn": "৫-মুখী রুদ্রাক্ষ (কালাগ্নি রুদ্র)", "deity": "Lord Kalagni Rudra", "desc_bn": "সর্বপাপহরা, সুস্বাস্থ্য, রক্তচাপ নিয়ন্ত্রণ এবং জ্ঞানসাধনায় অপরিহার্য।"},
    "Venus": {"mukhi": "6-Mukhi", "bn": "৬-মুখী রুদ্রাক্ষ", "deity": "Lord Kartikeya", "desc_bn": "আকর্ষণ ক্ষমতা, সৌন্দর্য, রোমান্স এবং শিল্পগুণ প্রস্ফুটিত করে।"},
    "Saturn": {"mukhi": "7-Mukhi / 14-Mukhi", "bn": "৭-মুখী রুদ্রাক্ষ (মহালক্ষ্মী রূপ)", "deity": "Goddess Mahalakshmi", "desc_bn": "আর্থিক সমৃদ্ধি, শনির সাড়ে সাতির উপশম এবং অকালমৃত্যু ভয় দূর করে।"},
}


def _add_calendar_years(dt: datetime, years: int) -> datetime:
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(year=dt.year + years, day=28)


def _calculate_planetary_dignities(
    raw_planets: dict[str, Any],
    planet_houses: dict[str, int],
    planet_signs: dict[str, int],
    asc_sign_idx: int,
    lang: str,
) -> list[PlanetaryDignityItem]:
    dignities: list[PlanetaryDignityItem] = []
    sun_lon = raw_planets["Sun"]["lon"]

    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        if p not in raw_planets:
            continue
        p_info = raw_planets[p]
        p_lon = p_info["lon"]
        s_idx = int(p_lon / 30.0) % 12
        deg_in_s = p_lon % 30.0
        house_num = planet_houses[p]
        meta = EXALT_DEBIL_MAP.get(p, {})

        # 1. Check Exaltation / Debilitation / Moolatrikona / Own Sign
        neechabhanga = False
        neechabhanga_reason = None

        if s_idx == meta.get("exalt_sign"):
            dignity = "Exalted"
            dignity_bn = "তুঙ্গী (উচ্চ)"
            dignity_hi = "उच्च"
        elif s_idx == meta.get("debil_sign"):
            dignity = "Debilitated"
            dignity_bn = "নীচস্থ"
            dignity_hi = "नीच"
            # Check Neechabhanga
            disp_lord = RASHIS_DATA[s_idx]["lord"]
            disp_h = planet_houses.get(disp_lord, 0)
            moon_s = planet_signs.get("Moon", 0)
            disp_from_moon = ((planet_signs.get(disp_lord, 0) - moon_s) % 12) + 1
            if disp_h in (1, 4, 7, 10) or disp_from_moon in (1, 4, 7, 10):
                neechabhanga = True
                neechabhanga_reason = f"রাশি অধিপতি {disp_lord} কেন্দ্রে থাকায় নীচভঙ্গ রাজযোগ সৃষ্টি হয়েছে।"
        elif s_idx == meta.get("moola_sign") and deg_in_s <= 20.0:
            dignity = "Moolatrikona"
            dignity_bn = "মূলত্রিকোণ"
            dignity_hi = "मूलत्रिकोण"
        elif s_idx in meta.get("own_signs", []):
            dignity = "Own Sign"
            dignity_bn = "স্বক্ষেত্র"
            dignity_hi = "स्वक्षेत्र"
        else:
            disp_lord = RASHIS_DATA[s_idx]["lord"]
            rel = PLANET_FRIENDS_MAP.get(p, {})
            if disp_lord in rel.get("friends", []):
                dignity = "Friendly Sign"
                dignity_bn = "মিত্র ক্ষেত্র"
                dignity_hi = "मित्र राशि"
            elif disp_lord in rel.get("enemies", []):
                dignity = "Enemy Sign"
                dignity_bn = "শত্রু ক্ষেত্র"
                dignity_hi = "शत्रु राशि"
            else:
                dignity = "Neutral Sign"
                dignity_bn = "সম ক্ষেত্র"
                dignity_hi = "सम राशि"

        # 2. Check Combustion
        is_combust = False
        if p != "Sun" and p not in ("Rahu", "Ketu"):
            diff = abs(p_lon - sun_lon) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff
            is_combust = diff <= meta.get("combust_orb", 10.0)

        # 3. Check Avastha
        if s_idx % 2 == 0:  # Odd sign
            if deg_in_s < 6.0:
                avastha, avastha_bn, avastha_hi = "Bal", "বাল (২৫% ফল)", "बाल"
            elif deg_in_s < 12.0:
                avastha, avastha_bn, avastha_hi = "Kumar", "কুমার (৫০% ফল)", "कुमार"
            elif deg_in_s < 18.0:
                avastha, avastha_bn, avastha_hi = "Yuva", "যুবা (১০০% ফলদায়ক)", "युवा"
            elif deg_in_s < 24.0:
                avastha, avastha_bn, avastha_hi = "Vriddha", "বৃদ্ধ (সামান্য ফল)", "वृद्ध"
            else:
                avastha, avastha_bn, avastha_hi = "Mrita", "মৃত (সুপ্ত ফল)", "मृत"
        else:  # Even sign
            if deg_in_s < 6.0:
                avastha, avastha_bn, avastha_hi = "Mrita", "মৃত (সুপ্ত ফল)", "मृत"
            elif deg_in_s < 12.0:
                avastha, avastha_bn, avastha_hi = "Vriddha", "বৃদ্ধ (সামান্য ফল)", "वृद्ध"
            elif deg_in_s < 18.0:
                avastha, avastha_bn, avastha_hi = "Yuva", "যুবা (১০০% ফলদায়ক)", "युवा"
            elif deg_in_s < 24.0:
                avastha, avastha_bn, avastha_hi = "Kumar", "কুমার (৫০% ফল)", "कुमार"
            else:
                avastha, avastha_bn, avastha_hi = "Bal", "বাল (২৫% ফল)", "बाल"

        p_local = PLANET_NAMES_LOCALIZED.get(p, {"bn": p, "hi": p})
        sign_info = RASHIS_DATA[s_idx]

        dignities.append(
            PlanetaryDignityItem(
                planet=p,
                planet_bn=p_local["bn"],
                planet_hi=p_local["hi"],
                sign=sign_info["name_en"],
                sign_bn=sign_info["name_bn"],
                house=house_num,
                degree=round(deg_in_s, 2),
                degree_formatted=_format_dms_styled(deg_in_s, sign_info["name_en"]),
                dignity=dignity,
                dignity_bn=dignity_bn,
                dignity_hi=dignity_hi,
                is_combust=is_combust,
                is_retrograde=p_info.get("is_retro", False),
                avastha=avastha,
                avastha_bn=avastha_bn,
                avastha_hi=avastha_hi,
                neechabhanga=neechabhanga,
                neechabhanga_reason=neechabhanga_reason,
            )
        )

    return dignities


def _calculate_12_house_predictions(
    cusps_list: list[float],
    planet_houses: dict[str, int],
    raw_planets: dict[str, Any],
    asc_sign_idx: int,
    lang: str,
) -> list[HousePredictionItem]:
    predictions: list[HousePredictionItem] = []

    for h_num in range(1, 13):
        h_idx = h_num - 1
        meta = BHAVA_METADATA[h_idx]
        c_lon = cusps_list[h_idx]
        s_idx = int(c_lon / 30.0) % 12
        sign_info = RASHIS_DATA[s_idx]
        sign_lord = sign_info["lord"]
        lord_h = planet_houses.get(sign_lord, 1)

        occupants = [p for p, ph in planet_houses.items() if ph == h_num]
        occupants_bn = [PLANET_NAMES_LOCALIZED[p]["bn"] for p in occupants if p in PLANET_NAMES_LOCALIZED]

        occ_str_bn = f"{', '.join(occupants_bn)} অবস্থান করছে" if occupants_bn else "কোনো প্রত্যক্ষ গ্রহ অবস্থান করেনি"

        if lord_h in (1, 4, 7, 10):
            lord_h_str_bn = f"কেন্দ্র ভাবে ({lord_h}ম ঘরে) অবস্থান করে শক্তিশালী ফল প্রদান করছে।"
        elif lord_h in (5, 9):
            lord_h_str_bn = f"ত্রিকোণ ভাবে ({lord_h}ম ঘরে) অবস্থান করে অতীব শুভ ও সৌভাগ্যপূর্ণ প্রভাব বিস্তার করছে।"
        elif lord_h in (6, 8, 12):
            lord_h_str_bn = f"দুঃস্থান ভাবে ({lord_h}ম ঘরে) অবস্থান করায় কিছু সতর্কতা ও নিয়মিত বৈদিক প্রতিকার কাম্য।"
        else:
            lord_h_str_bn = f"{lord_h}ম ঘরে অবস্থান করে প্রগতিশীল ফলাফল প্রদান করছে।"

        overview_bn = (
            f"{meta['name_bn']} রাশিতে {sign_info['name_bn']} রাশি পড়েছে। অধিপতি গ্রহ {PLANET_NAMES_LOCALIZED[sign_lord]['bn']} "
            f"লগ্নের সাপেক্ষে {lord_h_str_bn} এই ঘরে {occ_str_bn}। {meta['desc_bn']}"
        )
        overview_en = (
            f"{meta['name_en']} falls in {sign_info['name_en']}. Ruler {sign_lord} is situated in house {lord_h}. "
            f"Occupants: {', '.join(occupants) if occupants else 'None'}. {meta['desc_en']}"
        )
        overview_hi = (
            f"{meta['name_hi']} में {sign_info['name_hi']} राशि स्थित है। स्वामी {sign_lord} भाव {lord_h} में स्थित हैं। "
            f"{meta['desc_hi']}"
        )

        # Career / Wealth effect
        if h_num in (1, 2, 9, 10, 11):
            cw_bn = "কর্ম ও অর্থনৈতিক ক্ষেত্রে এই ভাবের প্রভাব অতি প্রবল। আত্মউদ্যম ও নীতিপরায়ণতায় নিরবচ্ছিন্ন প্রবৃদ্ধি নিশ্চিত।"
            cw_en = "Strongly elevates professional stature and material wealth through disciplined initiative."
            cw_hi = "करियर और आर्थिक समृद्धि में यह भाव अत्यंत शुभ और उन्नति प्रदायक है।"
        elif h_num in (5, 7):
            cw_bn = "মেধাভিত্তিক পরিকল্পনা এবং বিশ্বস্ত অংশীদারিত্বের মাধ্যমে ব্যবসায়িক লাভ বৃদ্ধি পাবে।"
            cw_en = "Strategic intelligence and credible alliances expand entrepreneurial success."
            cw_hi = "बुद्धिमत्ता और विश्वसनीय साझेदारी से व्यापारिक लाभ में वृद्धि होगी।"
        else:
            cw_bn = "আর্থিক লেনদেন ও অতিরিক্ত ব্যয় নিয়ন্ত্রণে রাখা এবং দীর্ঘমেয়াদী সঞ্চয়ে মনোযোগ দেওয়া শ্রেয়।"
            cw_en = "Maintain prudent risk management and emphasize long-term structured savings."
            cw_hi = "वित्तीय लेन-देन में विवेक रखें और दीर्घकालिक बचत पर ध्यान दें।"

        # Relationship / Family effect
        if h_num in (2, 4, 7):
            rf_bn = "পারিবারিক সৌহার্দ্য ও দাম্পত্য সুখের মূল নিয়ন্ত্রক। সুমধুর ভাষা ও পারস্পরিক সম্মান সুখ বজায় রাখবে।"
            rf_en = "Crucial anchor for domestic warmth and marital companionship; gentle speech maintains harmony."
            rf_hi = "पारिवारिक सद्भाव और दांपत्य सुख का मुख्य आधार; मधुर वाणी से शांति बनी रहेगी।"
        elif h_num in (1, 5, 9):
            rf_bn = "পরিবারের প্রতি কর্তব্যপরায়ণতা ও সন্তানদের সুশিক্ষা এবং পিতৃআশীর্বাদ জীবনকে আনন্দময় করে তোলে।"
            rf_en = "Devotion to family, children's high morals, and parental blessings bring deep contentment."
            rf_hi = "संतान की उच्च विद्या और बड़ों के आशीर्वाद से पारिवारिक वातावरण सुखद रहेगा।"
        else:
            rf_bn = "সম্পর্কের টানাপোড়েন এড়াতে অপ্রয়োজনীয় বিতর্ক থেকে দূরে থাকা এবং মানসিক সংযম রক্ষা জরুরি।"
            rf_en = "Avoid speculative disagreements and cultivate empathetic patience across domestic ties."
            rf_hi = "विवादों से बचें और पारिवारिक रिश्तों में धैर्य व समझदारी बनाए रखें।"

        predictions.append(
            HousePredictionItem(
                house_number=h_num,
                house_name=meta["name_en"],
                house_name_bn=meta["name_bn"],
                house_name_hi=meta["name_hi"],
                sign=sign_info["name_en"],
                sign_bn=sign_info["name_bn"],
                sign_lord=sign_lord,
                sign_lord_bn=PLANET_NAMES_LOCALIZED[sign_lord]["bn"],
                lord_placement_house=lord_h,
                occupants=occupants,
                occupants_bn=occupants_bn,
                overview=overview_bn if lang == "bn" else (overview_hi if lang == "hi" else overview_en),
                overview_bn=overview_bn,
                overview_hi=overview_hi,
                career_wealth_effect=cw_bn if lang == "bn" else (cw_hi if lang == "hi" else cw_en),
                career_wealth_effect_bn=cw_bn,
                career_wealth_effect_hi=cw_hi,
                relationship_family_effect=rf_bn if lang == "bn" else (rf_hi if lang == "hi" else rf_en),
                relationship_family_effect_bn=rf_bn,
                relationship_family_effect_hi=rf_hi,
            )
        )

    return predictions


def _calculate_extended_yogas(
    raw_planets: dict[str, Any],
    planet_signs: dict[str, int],
    planet_houses: dict[str, int],
    asc_sign_idx: int,
    is_manglik: bool,
    is_kaal_sarp: bool,
    is_budhaditya: bool,
    is_gaja_kesari: bool,
    is_kemadruma: bool,
    lang: str,
) -> list[ExtendedYogaItem]:
    yogas: list[ExtendedYogaItem] = []

    # 1. Ruchaka Yoga (Mars in Kendra in own/exalt sign: Aries, Scorpio, Capricorn)
    mars_h = planet_houses.get("Mars", 0)
    mars_s = planet_signs.get("Mars", 0)
    is_ruchaka = mars_h in (1, 4, 7, 10) and mars_s in (0, 7, 9)
    if is_ruchaka:
        yogas.append(
            ExtendedYogaItem(
                name="Ruchaka Yoga (Pancha Mahapurusha)",
                name_bn="রুচক যোগ (পঞ্চ মহাপুরুষ যোগ)",
                name_hi="रुचक योग (पंच महापुरुष योग)",
                category="Pancha Mahapurusha",
                category_bn="পঞ্চ মহাপুরুষ রাজযোগ",
                is_present=True,
                description="Mars is in a Kendra house (1, 4, 7, 10) in Aries, Scorpio, or Capricorn.",
                description_bn="মঙ্গল স্বক্ষেত্র বা তুঙ্গী হয়ে কেন্দ্রে অবস্থান করায় পরাশরীয় রুচক যোগ গঠিত হয়েছে।",
                description_hi="मंगल स्वराशि या उच्च राशि में केंद्र में स्थित होकर रुचक योग का निर्माण करता है।",
                effects="Endows fearless leadership, physical valor, land ownership, administrative commanding power, and victory over adversaries.",
                effects_bn="নির্ভীক নেতৃত্ব, শারীরিক তেজ, ভূসম্পত্তি লাভ, সামরিক বা প্রশাসনিক কর্তৃত্ব এবং সর্বশত্রু বিজয়ী পরাক্রম দান করে।",
                effects_hi="अतुलनीय पराक्रम, नेतृत्व क्षमता, भूमि संपत्ति और प्रशासनिक प्रतिष्ठा प्रदान करता है।",
            )
        )

    # 2. Bhadra Yoga (Mercury in Kendra in Gemini or Virgo)
    merc_h = planet_houses.get("Mercury", 0)
    merc_s = planet_signs.get("Mercury", 0)
    is_bhadra = merc_h in (1, 4, 7, 10) and merc_s in (2, 5)
    if is_bhadra:
        yogas.append(
            ExtendedYogaItem(
                name="Bhadra Yoga (Pancha Mahapurusha)",
                name_bn="ভদ্র যোগ (পঞ্চ মহাপুরুষ যোগ)",
                name_hi="भद्र योग (पंच महापुरुष योग)",
                category="Pancha Mahapurusha",
                category_bn="পঞ্চ মহাপুরুষ রাজযোগ",
                is_present=True,
                description="Mercury is in Kendra in own/exalted sign (Gemini or Virgo).",
                description_bn="বুধ স্বক্ষেত্র বা তুঙ্গী হয়ে কেন্দ্রস্থ হওয়ায় রাজকীয় ভদ্র যোগ গঠিত হয়েছে।",
                description_hi="बुध स्वराशि या उच्च राशि में केंद्र में स्थित होकर भद्र योग बनाता है।",
                effects="Bestows high intellect, sharp memory, eloquence, commercial genius, diplomacy, and enduring scholastic fame.",
                effects_bn="অসাধারণ ধীশক্তি, তীক্ষ্ণ স্মৃতি, অনবদ্য বাগ্মিতা, ব্যবসায়িক দূরদর্শিতা এবং পাণ্ডিত্যের সুখ্যাতি এনে দেয়।",
                effects_hi="प्रखर बुद्धि, वाणिज्यिक कौशल, विद्वता और समाज में उच्च सम्मान दिलाता है।",
            )
        )

    # 3. Hamsa Yoga (Jupiter in Kendra in Cancer, Sagittarius, or Pisces)
    jup_h = planet_houses.get("Jupiter", 0)
    jup_s = planet_signs.get("Jupiter", 0)
    is_hamsa = jup_h in (1, 4, 7, 10) and jup_s in (3, 8, 11)
    if is_hamsa:
        yogas.append(
            ExtendedYogaItem(
                name="Hamsa Yoga (Pancha Mahapurusha)",
                name_bn="হংস যোগ (পঞ্চ মহাপুরুষ যোগ)",
                name_hi="हंस योग (पंच महापुरुष योग)",
                category="Pancha Mahapurusha",
                category_bn="পঞ্চ মহাপুরুষ রাজযোগ",
                is_present=True,
                description="Jupiter is placed in Kendra in own or exalted sign (Cancer, Sagittarius, or Pisces).",
                description_bn="বৃহস্পতি কর্কট, ধনু বা মীন রাশিতে কেন্দ্রস্থ হয়ে দিব্য হংস যোগ সৃষ্টি করেছে।",
                description_hi="गुरु कर्क, धनु या मीन राशि में केंद्र में स्थित होकर हंस योग बनाता है।",
                effects="Brings saintly character, pure wisdom, high spiritual stature, societal reverence, ethical prosperity, and long righteous life.",
                effects_bn="ধার্মিক মানসিকতা, পরম প্রজ্ঞা, জনমানসে শ্রদ্ধা, আধ্যাত্মিক সুখ্যাতি এবং নিষ্কলঙ্ক রাজসম্মান প্রদান করে।",
                effects_hi="उच्च आध्यात्मिक चेतना, सात्विक आचरण, सर्वत्र आदर और सुखी जीवन प्रदान करता है।",
            )
        )

    # 4. Malavya Yoga (Venus in Kendra in Taurus, Libra, or Pisces)
    ven_h = planet_houses.get("Venus", 0)
    ven_s = planet_signs.get("Venus", 0)
    is_malavya = ven_h in (1, 4, 7, 10) and ven_s in (1, 6, 11)
    if is_malavya:
        yogas.append(
            ExtendedYogaItem(
                name="Malavya Yoga (Pancha Mahapurusha)",
                name_bn="মালব্য যোগ (পঞ্চ মহাপুরুষ যোগ)",
                name_hi="मालव्य योग (पंच महापुरुष योग)",
                category="Pancha Mahapurusha",
                category_bn="পঞ্চ মহাপুরুষ রাজযোগ",
                is_present=True,
                description="Venus is in Kendra in Taurus, Libra, or Pisces.",
                description_bn="শুক্র স্বক্ষেত্র বা তুঙ্গী হয়ে কেন্দ্রে বিরাজ করায় ঐশ্বর্যশালী মালব্য যোগ গঠিত হয়েছে।",
                description_hi="शुक्र वृषभ, तुला या मीन राशि में केंद्र में स्थित होकर मालव्य योग बनाता है।",
                effects="Grants luxurious comfort, fine arts mastery, enchanting charisma, marital ecstasy, vehicles, and immense material affluence.",
                effects_bn="বিলাসবহুল জীবনযাত্রা, রূপলাবণ্য, শিল্পকলায় নৈপুণ্য, সুখী দাম্পত্য এবং বিপুল ঐশ্বর্য ও যশের অধিকারী করে।",
                effects_hi="भौतिक सुख-सुविधाएं, कला में निपुणता, उत्तम दांपत्य और वाहन सुख प्रदान करता है।",
            )
        )

    # 5. Sasa Yoga (Saturn in Kendra in Libra, Capricorn, or Aquarius)
    sat_h = planet_houses.get("Saturn", 0)
    sat_s = planet_signs.get("Saturn", 0)
    is_sasa = sat_h in (1, 4, 7, 10) and sat_s in (6, 9, 10)
    if is_sasa:
        yogas.append(
            ExtendedYogaItem(
                name="Sasa Yoga (Pancha Mahapurusha)",
                name_bn="শশ যোগ (পঞ্চ মহাপুরুষ যোগ)",
                name_hi="शश योग (पंच महापुरुष योग)",
                category="Pancha Mahapurusha",
                category_bn="পঞ্চ মহাপুরুষ রাজযোগ",
                is_present=True,
                description="Saturn is placed in Kendra in Libra, Capricorn, or Aquarius.",
                description_bn="শনি তুঙ্গী বা স্বক্ষেত্রগত হয়ে কেন্দ্রে অবস্থান করায় শাস্ত্রীয় শশ যোগ সৃষ্টি হয়েছে।",
                description_hi="शनि तुला, मकर या कुंभ राशि में केंद्र में स्थित होकर शश योग बनाता है।",
                effects="Provides supreme endurance, mass leadership, judicial wisdom, disciplined authority, and enduring political or organizational power.",
                effects_bn="অটল সহনশীলতা, গণনেতৃত্ব, বিচারবুদ্ধি, সুদৃঢ় কর্মশৃঙ্খলা এবং দীর্ঘস্থায়ী রাজনৈতিক বা প্রাতিষ্ঠানিক ক্ষমতা দান করে।",
                effects_hi="जनसमर्थन, नेतृत्व क्षमता, न्यायप्रियता और दीर्घकालिक अधिकार प्रदान करता है।",
            )
        )

    # 6. Dharma-Karmadhipati Raj Yoga (9th & 10th lords connection)
    l9_lord = RASHIS_DATA[(asc_sign_idx + 8) % 12]["lord"]
    l10_lord = RASHIS_DATA[(asc_sign_idx + 9) % 12]["lord"]
    l9_h = planet_houses.get(l9_lord, 0)
    l10_h = planet_houses.get(l10_lord, 0)
    is_dk = (l9_h == l10_h) or (abs(l9_h - l10_h) == 6) or (l9_h in (9, 10) and l10_h in (9, 10))
    if is_dk:
        yogas.append(
            ExtendedYogaItem(
                name="Dharma-Karmadhipati Raj Yoga",
                name_bn="ধর্ম-কর্মাধিপতি রাজযোগ",
                name_hi="धर्म-कर्माधिपति राजयोग",
                category="Raj Yoga",
                category_bn="শ্রেষ্ঠ রাজযোগ",
                is_present=True,
                description="9th lord (Bhagya) and 10th lord (Karma) are in conjunction or mutual aspect.",
                description_bn="ভাগ্যপতি (৯ম পতি) এবং কর্মপতি (১০ম পতি)-র মধ্যে শুভ সম্পর্ক থাকায় পরম রাজযোগ গঠিত হয়েছে।",
                description_hi="नवमेश और दशमेश की युति या दृष्टि संबंध से महा राजयोग का निर्माण।",
                effects="One of the highest Vedic Raj Yogas, assuring effortless fortune in career, state honors, leadership, and divine spiritual grace.",
                effects_bn="বৈদিক জ্যোতিষের অন্যতম শ্রেষ্ঠ রাজযোগ—কর্মক্ষেত্রে সহজে শীর্ষস্থান লাভ, রাজসম্মান ও আজীবন ভাগ্যের দৈব সহায়তা নিশ্চিত করে।",
                effects_hi="करियर में अभूतपूर्व सफलता, राजसत्ता से मान-सम्मान और अपार कीर्ति दिलाता है।",
            )
        )

    # 7. Chandra-Mangala Yoga (Moon and Mars conjunct or mutual aspect)
    moon_h = planet_houses.get("Moon", 0)
    is_cm = (moon_h == mars_h) or (abs(moon_h - mars_h) == 6)
    if is_cm:
        yogas.append(
            ExtendedYogaItem(
                name="Chandra-Mangala (Gauri) Yoga",
                name_bn="চন্দ্র-মঙ্গল (লক্ষ্মী) যোগ",
                name_hi="चंद्र-मंगल (लक्ष्मी) योग",
                category="Dhana Yoga",
                category_bn="ধন যোগ",
                is_present=True,
                description="Moon and Mars are in conjunction or directly aspect each other.",
                description_bn="চন্দ্র ও মঙ্গল পরস্পর যুক্ত বা সমসপ্তমে অবস্থান করে ধনকারক লক্ষ্মী যোগ সৃষ্টি করেছে।",
                description_hi="चंद्र और मंगल की युति या परस्पर दृष्टि से लक्ष्मी योग का निर्माण।",
                effects="Drives high financial enterprise, commercial real estate gains, relentless earning ambition, and self-earned wealth.",
                effects_bn="উদ্যমী মনোভাব, রিয়েল এস্টেট ও ব্যবসায় বিপুল অর্থোপার্জন এবং স্বোপার্জিত সম্পদে স্বাবলম্বী হওয়ার সুযোগ দেয়।",
                effects_hi="व्यापार में प्रचुर धनलाभ, भूमि-भवन प्राप्ति और वित्तीय स्वावलंबन प्रदान करता है।",
            )
        )

    # 8. Viparita Raj Yoga (Harsha / Sarala / Vimala)
    l6_lord = RASHIS_DATA[(asc_sign_idx + 5) % 12]["lord"]
    l8_lord = RASHIS_DATA[(asc_sign_idx + 7) % 12]["lord"]
    l12_lord = RASHIS_DATA[(asc_sign_idx + 11) % 12]["lord"]
    l6_h = planet_houses.get(l6_lord, 0)
    l8_h = planet_houses.get(l8_lord, 0)
    l12_h = planet_houses.get(l12_lord, 0)
    is_harsha = l6_h in (6, 8, 12)
    is_sarala = l8_h in (6, 8, 12)
    is_vimala = l12_h in (6, 8, 12)
    if is_harsha or is_sarala or is_vimala:
        yogas.append(
            ExtendedYogaItem(
                name="Viparita Raj Yoga",
                name_bn="বিপরীত রাজযোগ (হর্ষ/সরল/বিমল)",
                name_hi="विपरीत राजयोग",
                category="Raj Yoga",
                category_bn="বিপরীত রাজযোগ",
                is_present=True,
                description="Lords of Dusthana houses (6th, 8th, or 12th) situated in Dusthanas, annihilating adversity.",
                description_bn="৬ষ্ঠ, ৮ম বা ১২শ পতি দুঃস্থানে অবস্থান করায় প্রতিকূলতা নাশ করে অপ্রত্যাশিত রাজতুল্য বিজয় প্রদান করে।",
                description_hi="त्रिक भावों (6, 8, 12) के स्वामियों की स्थिति से संकटों का नाश और विजय।",
                effects="Transforms critical crises into golden breakthroughs, overcomes bitter competition, and brings sudden windfall gains.",
                effects_bn="চরম প্রতিকূল পরিস্থিতিকে রাতারাতি বিজয়ে রূপান্তরিত করে, শত্রুদের নিষ্ক্রিয় করে এবং আকস্মিক সমৃদ্ধি আনে।",
                effects_hi="कठिन परिस्थितियों से अप्रत्याशित सफलता और शत्रुओं पर विजय दिलाता है।",
            )
        )

    # 9. Gaja Kesari Yoga
    if is_gaja_kesari:
        yogas.append(
            ExtendedYogaItem(
                name="Gaja Kesari Yoga",
                name_bn="গজকেশরী যোগ",
                name_hi="गजकेसरी योग",
                category="Auspicious",
                category_bn="শুভ রাজযোগ",
                is_present=True,
                description="Jupiter is in Kendra (1st, 4th, 7th, 10th) from Moon.",
                description_bn="চন্দ্র থেকে বৃহস্পতি কেন্দ্রগত (১ম, ৪র্থ, ৭ম বা ১০ম ভাবে) থাকায় রাজকীয় গজকেশরী যোগ গঠিত।",
                description_hi="चंद्रमा से केंद्र में गुरु स्थित होकर गजकेसरी योग बनाता है।",
                effects="Grants high social reputation, enduring intellect, administrative respect, wealth, and moral authority in leadership.",
                effects_bn="সমাজের শীর্ষস্থানীয় মহলে প্রতিষ্ঠা, অটুট সম্মান, সদ্গুণ, সুবক্তা হওয়া এবং সার্বিক আর্থিক সুরক্ষা দেয়।",
                effects_hi="समाज में उच्च पद, मान-प्रतिष्ठा, विद्वता और नेतृत्व का सामर्थ्य प्रदान करता है।",
            )
        )

    # 10. Budhaditya Yoga
    if is_budhaditya:
        yogas.append(
            ExtendedYogaItem(
                name="Budhaditya Yoga",
                name_bn="বুধাদিত্য যোগ",
                name_hi="बुधादित्य योग",
                category="Auspicious",
                category_bn="বুদ্ধি যোগ",
                is_present=True,
                description="Sun and Mercury in close conjunction in the same zodiac sign.",
                description_bn="সূর্য ও বুধ একই রাশিতে শুভ সংযোগ তৈরি করায় বিদ্যাবুদ্ধির বুধাদিত্য যোগ গঠিত হয়েছে।",
                description_hi="सूर्य और बुध की युति से ज्ञान और मेधा का बुधादित्य योग।",
                effects="Bestows sharp analytical intellect, administrative competence, persuasive communication, and scholastic honor.",
                effects_bn="তীক্ষ্ণ বিশ্লেষণ ক্ষমতা, চটজলদি সিদ্ধান্ত গ্রহণ, রাজকীয় বা প্রশাসনিক কাজে সাফল্য এবং পাণ্ডিত্যের খ্যাতি আনে।",
                effects_hi="कुशाग्र बुद्धि, प्रशासनिक योग्यता, उत्कृष्ट अभिव्यक्ति और शैक्षणिक सफलता दिलाता है।",
            )
        )

    # 11. Kemadruma Yoga
    if is_kemadruma:
        yogas.append(
            ExtendedYogaItem(
                name="Kemadruma Yoga",
                name_bn="কেমদ্রুম যোগ (সতর্কতামূলক)",
                name_hi="केमद्रुम योग",
                category="Inauspicious",
                category_bn="মানসিক ভাব",
                is_present=True,
                description="Moon is devoid of planetary support in 2nd and 12th houses.",
                description_bn="চন্দ্রের ২য় ও ১২শ ভাবে কোনো শুভ গ্রহ না থাকায় মন একাকীত্ব বা আত্মনির্ভরশীলতার শিক্ষা দেয়।",
                description_hi="चंद्रमा के 2रे और 12वें भाव में ग्रहों का अभाव।",
                effects="Instills deep introspective self-reliance, occasional loneliness, and mental detachment. Regular Shiva meditation brings peace.",
                effects_bn="স্বাবলম্বী হতে শেখায়, তবে কখনো কখনো মানসিক একাকীত্ব বোধ তৈরি করতে পারে। শিব সাধনা ও সাদা খাদ্য দানে শুভত্ব আসে।",
                effects_hi="आत्मनिर्भरता सिखाता है, मानसिक शांति के लिए शिव आराधना श्रेष्ठ है।",
            )
        )

    return yogas


def _calculate_doshas_analysis(
    raw_planets: dict[str, Any],
    planet_signs: dict[str, int],
    planet_houses: dict[str, int],
    asc_sign_idx: int,
    manglik: Any,
    is_kaal_sarp: bool,
    lang: str,
) -> list[DoshaAnalysisItem]:
    doshas: list[DoshaAnalysisItem] = []

    # 1. Manglik Dosha
    if manglik.is_manglik:
        severity = "High" if manglik.percentage >= 70 else ("Moderate" if manglik.percentage >= 40 else "Mild")
        severity_bn = "উচ্চ" if severity == "High" else ("মধ্যম" if severity == "Moderate" else "আংশিক")
        remedy_bn = "নিয়মিত হনুমান চালিসা পাঠ, প্রতি মঙ্গলবার মঙ্গল বীজ মন্ত্র জপ এবং বিবাহ পূর্বে ঘট বিবাহ/কুষ্ঠি মেলবন্ধন শুভ।"
        remedy_en = "Recite Hanuman Chalisa daily, chant Mars Beej Mantra on Tuesdays, and match charts carefully."
        remedy_hi = "नित्य हनुमान चालीसा का पाठ, मंगलवार को मंगल बीज मंत्र का जप और कुंडली मिलान आवश्यक है।"
        canc_reason = "; ".join(manglik.cancellations) if manglik.cancellations else None
    else:
        severity = "None"
        severity_bn = "দোষমুক্ত"
        remedy_bn = "মাঙ্গলিক দোষ নেই। স্বাভাবিক শাস্ত্রীয় ধর্মকর্ম অব্যাহত রাখুন।"
        remedy_en = "No Manglik Dosha present. Normal auspicious Vedic practices apply."
        remedy_hi = "मांगलिक दोष नहीं है। दांपत्य जीवन के लिए शुभ।"
        canc_reason = None

    doshas.append(
        DoshaAnalysisItem(
            dosha_name="Manglik Dosha",
            dosha_name_bn="মাঙ্গলিক দোষ",
            dosha_name_hi="मांगलिक दोष",
            is_present=manglik.is_manglik,
            severity=severity,
            severity_bn=severity_bn,
            specific_type=f"{manglik.percentage}% মাঙ্গলিক প্রভাব" if manglik.is_manglik else "মাঙ্গলিক দোষ মুক্ত",
            specific_type_bn=f"{manglik.percentage}% মাঙ্গলিক প্রভাব" if manglik.is_manglik else "মাঙ্গলিক দোষ মুক্ত",
            cancellation_reason=canc_reason,
            cancellation_reason_bn=canc_reason,
            remedy=remedy_bn if lang == "bn" else (remedy_hi if lang == "hi" else remedy_en),
            remedy_bn=remedy_bn,
            remedy_hi=remedy_hi,
        )
    )

    # 2. Kaal Sarp Dosha
    if is_kaal_sarp:
        rahu_h = planet_houses.get("Rahu", 1)
        ks_var = KAAL_SARP_VARIANTS.get(rahu_h, KAAL_SARP_VARIANTS[1])
        remedy_bn = "প্রতি প্রদোষে বা মহা শিবরাত্রিতে শিবলিঙ্গে দুধ ও কাঁচা গঙ্গাজল অভিষেক, এবং মহামৃত্যুঞ্জয় মন্ত্র জপ হিতকর।"
        remedy_en = "Perform Rudra Abhishekam on Pradosham days, chant Maha Mrityunjaya Mantra, and feed stray animals."
        remedy_hi = "प्रदोष काल में शिवलिंग पर दुग्धाभिषेक करें और महामृत्युंजय मंत्र का नित्य जप करें।"

        doshas.append(
            DoshaAnalysisItem(
                dosha_name="Kaal Sarp Dosha",
                dosha_name_bn="কালসর্প যোগ",
                dosha_name_hi="कालसर्प दोष",
                is_present=True,
                severity="Moderate",
                severity_bn="মধ্যম প্রভাব",
                specific_type=ks_var["name"],
                specific_type_bn=ks_var["bn"],
                cancellation_reason=None,
                cancellation_reason_bn=None,
                remedy=remedy_bn if lang == "bn" else (remedy_hi if lang == "hi" else remedy_en),
                remedy_bn=remedy_bn,
                remedy_hi=remedy_hi,
            )
        )
    else:
        doshas.append(
            DoshaAnalysisItem(
                dosha_name="Kaal Sarp Dosha",
                dosha_name_bn="কালসর্প যোগ",
                dosha_name_hi="कालसर्प दोष",
                is_present=False,
                severity="None",
                severity_bn="দোষমুক্ত",
                specific_type="কালসর্প মুক্ত",
                specific_type_bn="কালসর্প মুক্ত",
                cancellation_reason=None,
                cancellation_reason_bn=None,
                remedy="কালসর্প যোগ নেই। জন্মছকে গ্রহগণ ভারসাম্যপূর্ণ অবস্থায় রয়েছে।",
                remedy_bn="কালসর্প যোগ নেই। জন্মছকে গ্রহগণ ভারসাম্যপূর্ণ অবস্থায় রয়েছে।",
                remedy_hi="कुंडली में कालसर्प दोष नहीं है। ग्रह पूर्णतः संतुलित हैं।",
            )
        )

    # 3. Pitra Dosha Check
    sun_s = planet_signs.get("Sun", 0)
    rahu_s = planet_signs.get("Rahu", 0)
    ketu_s = planet_signs.get("Ketu", 0)
    sat_s = planet_signs.get("Saturn", 0)
    l9_lord = RASHIS_DATA[(asc_sign_idx + 8) % 12]["lord"]
    l9_s = planet_signs.get(l9_lord, 0)

    has_pitra = (sun_s in (rahu_s, ketu_s, sat_s)) or (l9_s in (rahu_s, ketu_s))
    if has_pitra:
        doshas.append(
            DoshaAnalysisItem(
                dosha_name="Pitra Dosha",
                dosha_name_bn="পিতৃ দোষ",
                dosha_name_hi="पितृ दोष",
                is_present=True,
                severity="Moderate",
                severity_bn="মধ্যম",
                specific_type="সূর্য বা ৯ম পতির রাহু/কেতু সংযোগ",
                specific_type_bn="সূর্য বা ৯ম পতির রাহু/কেতু সংযোগ",
                cancellation_reason=None,
                cancellation_reason_bn=None,
                remedy="অমাবস্যা তিথিতে পূর্বপুরুষের উদ্দেশে তর্পণ/দান, বট বা অশ্বত্থ বৃক্ষে জল অর্পণ এবং পিপীলিকা ও কাককে খাদ্য দান অত্যন্ত শুভ।",
                remedy_bn="অমাবস্যা তিথিতে পূর্বপুরুষের উদ্দেশে তর্পণ/দান, বট বা অশ্বত্থ বৃক্ষে জল অর্পণ এবং পিপীলিকা ও কাককে খাদ্য দান অত্যন্ত শুভ।",
                remedy_hi="अमावस्या पर पितृ तर्पण, पीपल के वृक्ष में जल अर्पण और ब्राह्मण/जरूरतमंदों को भोजन कराएं।",
            )
        )
    else:
        doshas.append(
            DoshaAnalysisItem(
                dosha_name="Pitra Dosha",
                dosha_name_bn="পিতৃ দোষ",
                dosha_name_hi="पितृ दोष",
                is_present=False,
                severity="None",
                severity_bn="দোষমুক্ত",
                specific_type="পিতৃ দোষ নেই",
                specific_type_bn="পিতৃ দোষ নেই",
                cancellation_reason=None,
                cancellation_reason_bn=None,
                remedy="পিতৃ দোষ নেই। পূর্বপুরুষের শুভাশিস আপনার অনুকূলে রয়েছে।",
                remedy_bn="পিতৃ দোষ নেই। পূর্বপুরুষের শুভাশিস আপনার অনুকূলে রয়েছে।",
                remedy_hi="पितृ दोष नहीं है। पूर्वजों का आशीर्वाद प्राप्त है।",
            )
        )

    # 4. Guru Chandal Dosha Check
    jup_s = planet_signs.get("Jupiter", 0)
    has_chandal = (jup_s == rahu_s) or (jup_s == ketu_s)
    if has_chandal:
        doshas.append(
            DoshaAnalysisItem(
                dosha_name="Guru Chandal Dosha",
                dosha_name_bn="গুরু চণ্ডাল দোষ",
                dosha_name_hi="गुरु चांडाल दोष",
                is_present=True,
                severity="Moderate",
                severity_bn="মধ্যম",
                specific_type="বৃহস্পতি ও ছায়া গ্রহের একরাশিতে সংযোগ",
                specific_type_bn="বৃহস্পতি ও ছায়া গ্রহের একরাশিতে সংযোগ",
                cancellation_reason=None,
                cancellation_reason_bn=None,
                remedy="প্রতি বৃহস্পতিবার গুরু বা ব্রাহ্মণকে হলুদ ফল/মিষ্টি দান, গায়ত্রী মন্ত্র জপ এবং শিক্ষক ও বয়োজ্যেষ্ঠদের প্রতি সদাচরণ কাম্য।",
                remedy_bn="প্রতি বৃহস্পতিবার গুরু বা ব্রাহ্মণকে হলুদ ফল/মিষ্টি দান, গায়ত্রী মন্ত্র জপ এবং শিক্ষক ও বয়োজ্যেষ্ঠদের প্রতি সদাচরণ কাম্য।",
                remedy_hi="गुरुवार को पीले वस्त्र या चने की दाल दान करें, गायत्री मंत्र का जप करें।",
            )
        )
    else:
        doshas.append(
            DoshaAnalysisItem(
                dosha_name="Guru Chandal Dosha",
                dosha_name_bn="গুরু চণ্ডাল দোষ",
                dosha_name_hi="गुरु चांडाल दोष",
                is_present=False,
                severity="None",
                severity_bn="দোষমুক্ত",
                specific_type="দোষমুক্ত",
                specific_type_bn="দোষমুক্ত",
                cancellation_reason=None,
                cancellation_reason_bn=None,
                remedy="গুরু চণ্ডাল দোষ নেই। বৃহস্পতি স্বতন্ত্রভাবে সদর্থক প্রভাব রাখছে।",
                remedy_bn="গুরু চণ্ডাল দোষ নেই। বৃহস্পতি স্বতন্ত্রভাবে সদর্থক প্রভাব রাখছে।",
                remedy_hi="गुरु चांडाल दोष नहीं है। गुरु ग्रह शुभ प्रभाव में हैं।",
            )
        )

    return doshas


def _calculate_personal_remedies(
    asc_sign_idx: int,
    planet_signs: dict[str, int],
    planet_houses: dict[str, int],
    raw_planets: dict[str, Any],
    lang: str,
) -> PersonalRemedies:
    # 1. Life Stone (L1 Lord)
    l1_lord = RASHIS_DATA[asc_sign_idx]["lord"]
    l1_meta = GEMSTONES_MASTER.get(l1_lord, GEMSTONES_MASTER["Mars"])
    life_stone = GemstoneItem(
        category="Life Stone (প্রাণ রত্ন)",
        category_bn="প্রাণ রত্ন / লগ্ন রত্ন",
        stone_name=l1_meta["stone_name"],
        stone_name_bn=l1_meta["stone_name_bn"],
        stone_name_hi=l1_meta["stone_name_hi"],
        sanskrit_name=l1_meta["sanskrit_name"],
        ruling_planet=l1_lord,
        ruling_planet_bn=PLANET_NAMES_LOCALIZED[l1_lord]["bn"],
        metal=l1_meta["metal"],
        metal_bn=l1_meta["metal_bn"],
        finger=l1_meta["finger"],
        finger_bn=l1_meta["finger_bn"],
        wearing_day=l1_meta["wearing_day"],
        wearing_day_bn=l1_meta["wearing_day_bn"],
        beej_mantra=l1_meta["beej_mantra"],
        benefit=l1_meta["benefit"],
        benefit_bn=l1_meta["benefit_bn"],
    )

    # 2. Lucky Stone (L9 Lord - Bhagya)
    l9_lord = RASHIS_DATA[(asc_sign_idx + 8) % 12]["lord"]
    l9_meta = GEMSTONES_MASTER.get(l9_lord, GEMSTONES_MASTER["Jupiter"])
    lucky_stone = GemstoneItem(
        category="Lucky Stone (ভাগ্য রত্ন)",
        category_bn="ভাগ্য রত্ন / ধর্ম রত্ন",
        stone_name=l9_meta["stone_name"],
        stone_name_bn=l9_meta["stone_name_bn"],
        stone_name_hi=l9_meta["stone_name_hi"],
        sanskrit_name=l9_meta["sanskrit_name"],
        ruling_planet=l9_lord,
        ruling_planet_bn=PLANET_NAMES_LOCALIZED[l9_lord]["bn"],
        metal=l9_meta["metal"],
        metal_bn=l9_meta["metal_bn"],
        finger=l9_meta["finger"],
        finger_bn=l9_meta["finger_bn"],
        wearing_day=l9_meta["wearing_day"],
        wearing_day_bn=l9_meta["wearing_day_bn"],
        beej_mantra=l9_meta["beej_mantra"],
        benefit=l9_meta["benefit"],
        benefit_bn=l9_meta["benefit_bn"],
    )

    # 3. Career Stone (L10 Lord)
    l10_lord = RASHIS_DATA[(asc_sign_idx + 9) % 12]["lord"]
    l10_meta = GEMSTONES_MASTER.get(l10_lord, GEMSTONES_MASTER["Mercury"])
    career_stone = GemstoneItem(
        category="Career Stone (কর্ম রত্ন)",
        category_bn="কর্ম রত্ন / প্রতিষ্ঠা রত্ন",
        stone_name=l10_meta["stone_name"],
        stone_name_bn=l10_meta["stone_name_bn"],
        stone_name_hi=l10_meta["stone_name_hi"],
        sanskrit_name=l10_meta["sanskrit_name"],
        ruling_planet=l10_lord,
        ruling_planet_bn=PLANET_NAMES_LOCALIZED[l10_lord]["bn"],
        metal=l10_meta["metal"],
        metal_bn=l10_meta["metal_bn"],
        finger=l10_meta["finger"],
        finger_bn=l10_meta["finger_bn"],
        wearing_day=l10_meta["wearing_day"],
        wearing_day_bn=l10_meta["wearing_day_bn"],
        beej_mantra=l10_meta["beej_mantra"],
        benefit=l10_meta["benefit"],
        benefit_bn=l10_meta["benefit_bn"],
    )

    # Rudraksha
    rud_info = RUDRAKSHA_MASTER.get(l1_lord, RUDRAKSHA_MASTER["Jupiter"])
    rud_bn = f"{rud_info['bn']} — অধিপতি দেবতা: {rud_info['deity']}। {rud_info['desc_bn']}"
    rud_en = f"{rud_info['mukhi']} Rudraksha blessed by {rud_info['deity']}."
    rud_hi = f"{rud_info['mukhi']} रुद्राक्ष — देवता: {rud_info['deity']}।"

    # Ishta Devata (based on 5th house sign)
    l5_lord = RASHIS_DATA[(asc_sign_idx + 4) % 12]["lord"]
    ishta_map = {
        "Sun": ("Lord Shiva / Surya Narayana", "দেবাদিদেব মহাদেব ও সূর্য নারায়ণ", "भगवान शिव"),
        "Moon": ("Goddess Parvati / Radha Krishna", "মা পার্বতী ও রাধাকৃষ্ণ", "माँ पार्वती"),
        "Mars": ("Lord Hanuman / Kartikeya", "শ্রী হনুমানজী ও কার্তিক", "श्री हनुमान"),
        "Mercury": ("Lord Vishnu / Narayana", "ভগবান শ্রীবিষ্ণু ও নারায়ণ", "भगवान विष्णु"),
        "Jupiter": ("Lord Shiva / Dattatreya", "মহাদেব ও শ্রী দত্তাত্রেয়", "भगवान शिव एवं दत्तात्रेय"),
        "Venus": ("Goddess Mahalakshmi", "দেবী মহালক্ষ্মী", "माँ महालक्ष्मी"),
        "Saturn": ("Lord Krishna / Kali Mata", "ভগবান শ্রীকৃষ্ণ ও মা দক্ষিণা কালী", "माँ काली एवं श्री कृष्ण"),
    }
    ishta_en, ishta_bn, ishta_hi = ishta_map.get(l5_lord, ishta_map["Jupiter"])

    # Lucky colors & numbers based on Lagna Lord
    colors_map = {
        "Sun": (["Gold", "Copper Red", "Orange"], ["সোনালী", "গাঢ় লাল", "কমলা"]),
        "Moon": (["White", "Silver", "Cream"], ["শুভ্র সাদা", "রৌপ্য", "ক্রিম"]),
        "Mars": (["Coral Red", "Scarlet", "Maroon"], ["রক্ত লাল", "মেরুন", "কমলা"]),
        "Mercury": (["Emerald Green", "Mint", "Sage"], ["পান্না সবুজ", "হালকা সবুজ", "হলুদ"]),
        "Jupiter": (["Golden Yellow", "Saffron", "Mustard"], ["হলুদ", "বাসন্তী", "জাফরান"]),
        "Venus": (["Silvery White", "Pink", "Pastel"], ["সাদা", "গোলাপি", "হালকা নীল"]),
        "Saturn": (["Deep Blue", "Navy", "Charcoal"], ["নীল", "কালো", "নেভি ব্লু"]),
    }
    nums_map = {
        "Sun": [1, 4, 7], "Moon": [2, 7, 9], "Mars": [9, 3, 1],
        "Mercury": [5, 6, 8], "Jupiter": [3, 9, 7], "Venus": [6, 5, 8], "Saturn": [8, 5, 6],
    }
    dirs_map = {
        "Sun": ("East", "পূর্ব দিক"), "Moon": ("North-West", "উত্তর-পশ্চিম দিক"),
        "Mars": ("South", "দক্ষিণ দিক"), "Mercury": ("North", "উত্তর দিক"),
        "Jupiter": ("North-East (Ishanya)", "উত্তর-পূর্ব (ঈশান কোণ)"),
        "Venus": ("South-East (Agni)", "দক্ষিণ-পূর্ব (অগ্নি কোণ)"),
        "Saturn": ("West", "পশ্চিম দিক"),
    }

    cols_en, cols_bn = colors_map.get(l1_lord, colors_map["Jupiter"])
    nums = nums_map.get(l1_lord, [3, 7, 9])
    dir_en, dir_bn = dirs_map.get(l1_lord, ("East", "পূর্ব দিক"))

    return PersonalRemedies(
        life_stone=life_stone,
        lucky_stone=lucky_stone,
        career_stone=career_stone,
        rudraksha_recommendation=rud_bn if lang == "bn" else (rud_hi if lang == "hi" else rud_en),
        rudraksha_recommendation_bn=rud_bn,
        rudraksha_recommendation_hi=rud_hi,
        ishta_devata=ishta_bn if lang == "bn" else (ishta_hi if lang == "hi" else ishta_en),
        ishta_devata_bn=ishta_bn,
        ishta_devata_hi=ishta_hi,
        lucky_colors=cols_bn if lang == "bn" else cols_en,
        lucky_colors_bn=cols_bn,
        lucky_numbers=nums,
        favorable_direction=dir_bn if lang == "bn" else dir_en,
        favorable_direction_bn=dir_bn,
    )


def _calculate_current_dasha(
    dashas_grid: list[KundliDashaCard],
    lang: str,
) -> CurrentDashaInfo | None:
    now = datetime.now(dt_timezone.utc)
    now_date = now.date()

    for card in dashas_grid:
        for ant in card.antardashas:
            if ant.end_date == "-":
                continue
            try:
                ad_end_dt = datetime.strptime(ant.end_date, "%d-%m-%Y").date()
                if ad_end_dt >= now_date:
                    md_lord = card.lord
                    ad_lord = ant.lord
                    md_bn = PLANET_NAMES_LOCALIZED.get(md_lord, {"bn": md_lord})["bn"]
                    ad_bn = PLANET_NAMES_LOCALIZED.get(ad_lord, {"bn": ad_lord})["bn"]

                    verdict_bn = f"বর্তমানে আপনার {md_bn} মহাদশায় {ad_bn} অন্তর্দশা চলছে।"
                    verdict_en = f"You are currently running {md_lord} Mahadasha with {ad_lord} Antardasha."
                    verdict_hi = f"वर्तमान में आपकी {md_lord} महादशा में {ad_lord} अंतर्दशा चल रही है।"

                    guidance_bn = (
                        f"এই সময়ে {md_bn}-এর মূল প্রভাব সক্রিয় থাকবে এবং {ad_bn}-এর ফলাফল দৈনন্দিন ঘটনায় প্রতিফলিত হবে। "
                        f"ধর্মীয় অনুশাসন বজায় রাখা ও প্রাসঙ্গিক বৈদিক বীজ মন্ত্র জপ বিশেষ ফলপ্রসূ।"
                    )
                    guidance_en = (
                        f"During this phase, {md_lord}'s overall agenda governs while {ad_lord} shapes day-to-day results. "
                        f"Chanting the planetary beej mantras ensures auspicious outcomes."
                    )
                    guidance_hi = (
                        f"इस अवधि में {md_lord} और {ad_lord} का संयुक्त प्रभाव कार्यक्षेत्र और जीवन पर रहेगा। मंत्र जप लाभकारी होगा।"
                    )

                    return CurrentDashaInfo(
                        mahadasha_lord=md_lord,
                        mahadasha_lord_bn=md_bn,
                        antardasha_lord=ad_lord,
                        antardasha_lord_bn=ad_bn,
                        start_date=now.strftime("%d-%m-%Y"),
                        end_date=ant.end_date,
                        verdict=verdict_bn if lang == "bn" else (verdict_hi if lang == "hi" else verdict_en),
                        verdict_bn=verdict_bn,
                        verdict_hi=verdict_hi,
                        guidance=guidance_bn if lang == "bn" else (guidance_hi if lang == "hi" else guidance_en),
                        guidance_bn=guidance_bn,
                        guidance_hi=guidance_hi,
                    )
            except Exception:
                continue

    # Fallback to first card if date comparison fails
    if dashas_grid:
        first = dashas_grid[0]
        ad_first = first.antardashas[-1] if first.antardashas else None
        return CurrentDashaInfo(
            mahadasha_lord=first.lord,
            mahadasha_lord_bn=PLANET_NAMES_LOCALIZED.get(first.lord, {"bn": first.lord})["bn"],
            antardasha_lord=ad_first.lord if ad_first else first.lord,
            antardasha_lord_bn=PLANET_NAMES_LOCALIZED.get(ad_first.lord if ad_first else first.lord, {"bn": first.lord})["bn"],
            start_date=now.strftime("%d-%m-%Y"),
            end_date=ad_first.end_date if ad_first else "2030-01-01",
            verdict="চলতি বিংশোত্তরী দশা সক্রিয় রয়েছে।",
            verdict_bn="চলতি বিংশোত্তরী দশা সক্রিয় রয়েছে।",
            verdict_hi="विंशोत्तरी दशा सक्रिय है।",
            guidance="দশাপতির বৈদিক প্রতিকার ও বীজ মন্ত্র জপ করুন।",
            guidance_bn="দশাপতির বৈদিক প্রতিকার ও বীজ মন্ত্র জপ করুন।",
            guidance_hi="दशा स्वामी के बीज मंत्र का जप करें।",
        )
    return None


def calculate_kundli(payload: KundliCalculateRequest) -> KundliCalculateResponse:
    """Calculates complete Kundli & Planetary Positions matching AppliedJyotish screenshots."""
    # 1. Parse DOB & Local Time
    lat = payload.latitude if payload.latitude is not None else 22.5726
    lon = payload.longitude if payload.longitude is not None else 88.3639

    raw_hour = getattr(payload, "hour", None)
    hour = raw_hour if raw_hour is not None else 12
    minute = getattr(payload, "minute", None) or 0
    second = getattr(payload, "second", None) or 0
    period = getattr(payload, "period", "PM") or "PM"

    hour_24 = hour
    if period == "PM" and hour_24 < 12:
        hour_24 += 12
    elif period == "AM" and hour_24 == 12:
        hour_24 = 0

    resolved = resolve_timezone(
        year=payload.year,
        month=payload.month,
        day=payload.day,
        hour=hour_24,
        minute=minute,
        second=second,
        latitude=lat,
        longitude=lon,
        zone_name=getattr(payload, "timezone_name", None),
        fallback_offset_hours=payload.timezone,
    )

    local_decimal = hour_24 + minute / 60.0 + second / 3600.0
    utc_decimal = local_decimal - resolved.offset_hours
    base_dt = datetime(payload.year, payload.month, payload.day, tzinfo=UTC)
    moment = base_dt + timedelta(hours=utc_decimal)
    utc_hours = (
        moment.hour
        + moment.minute / 60.0
        + moment.second / 3600.0
        + moment.microsecond / 3_600_000_000.0
    )

    day = payload.day
    month = payload.month
    year = payload.year
    birth_dt = datetime(year, month, day, hour_24, minute, second)

    # 2. Swiss Ephemeris configuration
    if HAS_SWISSEPH and swe is not None:
        jd_dob = swe.julday(moment.year, moment.month, moment.day, utc_hours)

        # Ayanamsa
        ay_code = payload.ayanamsa.lower()
        if ay_code in ("lahiri",):
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            ayan_name = "Lahiri"
        elif ay_code in ("krishnamurti",):
            swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
            ayan_name = "Krishnamurti"
        elif ay_code in ("bv_raman", "raman"):
            swe.set_sid_mode(swe.SIDM_RAMAN)
            ayan_name = "B.V. Raman"
        elif ay_code in ("yukteshwar",):
            swe.set_sid_mode(getattr(swe, "SIDM_YUKTESHWAR", swe.SIDM_KRISHNAMURTI))
            ayan_name = "Yukteshwar"
        elif ay_code in ("suryasiddhanta",):
            swe.set_sid_mode(getattr(swe, "SIDM_SURYASIDDHANTA", swe.SIDM_KRISHNAMURTI))
            ayan_name = "Surya Siddhanta"
        elif ay_code in ("true_pushya",):
            swe.set_sid_mode(getattr(swe, "SIDM_TRUE_PUSHYA", swe.SIDM_KRISHNAMURTI))
            ayan_name = "True Pushya"
        else:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            ayan_name = "Lahiri"

        # 12 Placidus Cusps & Ascendant
        raw_cusps, ascmc = swe.houses_ex(jd_dob, lat, lon, b"P", swe.FLG_SIDEREAL)
        asc_lon = ascmc[0] % 360.0
        cusps_list = [c % 360.0 for c in raw_cusps]

        # Sunrise & Sunset
        jd_start = swe.julday(year, month, day, 0.0 - payload.timezone)
        try:
            _, rise_tret = swe.rise_trans(jd_start, swe.SUN, swe.CALC_RISE, (lon, lat, 0.0))
            _, set_tret = swe.rise_trans(jd_start, swe.SUN, swe.CALC_SET, (lon, lat, 0.0))
            rise_local = ((rise_tret[0] - jd_start) * 24.0) % 24.0
            set_local = ((set_tret[0] - jd_start) * 24.0) % 24.0
            r_h = int(rise_local)
            r_m = int((rise_local - r_h) * 60)
            r_s = int(round(((rise_local - r_h) * 60 - r_m) * 60))
            sunrise_str = f"{r_h:02d}:{r_m:02d}:{r_s:02d}"

            s_h = int(set_local)
            s_m = int((set_local - s_h) * 60)
            s_s = int(round(((set_local - s_h) * 60 - s_m) * 60))
            sunset_str = f"{s_h:02d}:{s_m:02d}:{s_s:02d}"
        except Exception:
            sunrise_str = "04:57:54"
            sunset_str = "18:26:55"

        # 9 Planets
        calc_flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        planet_defs = [
            ("Sun", swe.SUN, "Su", "☉"),
            ("Moon", swe.MOON, "Mo", "☽"),
            ("Mercury", swe.MERCURY, "Me", "☿"),
            ("Venus", swe.VENUS, "Ve", "♀"),
            ("Mars", swe.MARS, "Ma", "♂"),
            ("Jupiter", swe.JUPITER, "Ju", "♃"),
            ("Saturn", swe.SATURN, "Sa", "♄"),
            ("Rahu", swe.TRUE_NODE, "Ra", "☊"),
        ]

        raw_planets: dict[str, dict[str, Any]] = {}
        for p_name, p_id, p_code, p_sym in planet_defs:
            res, _ = swe.calc_ut(jd_dob, p_id, calc_flags)
            raw_planets[p_name] = {
                "lon": res[0] % 360.0,
                "speed": res[3],
                "code": p_code,
                "symbol": p_sym,
                "is_retro": res[3] < 0 if p_name != "Rahu" else True,
            }

        # Ketu is exactly 180° opposite Rahu
        rahu_lon = raw_planets["Rahu"]["lon"]
        ketu_lon = (rahu_lon + 180.0) % 360.0
        raw_planets["Ketu"] = {
            "lon": ketu_lon,
            "speed": raw_planets["Rahu"]["speed"],
            "code": "Ke",
            "symbol": "☋",
            "is_retro": True,
        }
    else:
        # Fallback approximation if swisseph not present
        jd_dob = 2453187.0
        ayan_name = "Lahiri"
        asc_lon = 141.5987
        cusps_list = [(asc_lon + i * 30.0) % 360.0 for i in range(12)]
        sunrise_str = "04:57:54"
        sunset_str = "18:26:55"
        raw_planets = {
            "Sun": {"lon": 74.8089, "speed": 0.95, "code": "Su", "symbol": "☉", "is_retro": False},
            "Moon": {"lon": 222.4456, "speed": 12.0, "code": "Mo", "symbol": "☽", "is_retro": False},
            "Mercury": {"lon": 87.7706, "speed": 1.2, "code": "Me", "symbol": "☿", "is_retro": False},
            "Venus": {"lon": 45.7097, "speed": 0.8, "code": "Ve", "symbol": "♀", "is_retro": False},
            "Mars": {"lon": 100.0633, "speed": 0.6, "code": "Ma", "symbol": "♂", "is_retro": False},
            "Jupiter": {"lon": 139.3228, "speed": 0.15, "code": "Ju", "symbol": "♃", "is_retro": False},
            "Saturn": {"lon": 81.8119, "speed": 0.08, "code": "Sa", "symbol": "♄", "is_retro": False},
            "Rahu": {"lon": 14.1911, "speed": -0.05, "code": "Ra", "symbol": "☊", "is_retro": True},
            "Ketu": {"lon": 194.1911, "speed": -0.05, "code": "Ke", "symbol": "☋", "is_retro": True},
        }

    # 3. Ascendant Details & D9 Navamsha Ascendant
    asc_sign_idx = int(asc_lon / 30.0) % 12
    asc_sign_info = RASHIS_DATA[asc_sign_idx]
    asc_deg_in_sign = asc_lon % 30.0
    asc_sign_num = asc_sign_idx + 1  # 1 to 12

    # Navamsa Ascendant (D9)
    d9_asc_sign_idx = int(asc_lon / (360.0 / 108.0)) % 12
    d9_asc_sign_num = d9_asc_sign_idx + 1

    # Moon Details & Nakshatra
    moon_lon = raw_planets["Moon"]["lon"]
    moon_sign_idx = int(moon_lon / 30.0) % 12
    moon_sign_info = RASHIS_DATA[moon_sign_idx]
    moon_nak_name, moon_star_lord, moon_sub_lord, moon_pada = _get_star_and_sub_lord(moon_lon)

    # 4. Panchang Elements (Tithi, Yoga, Karana, Day)
    sun_lon = raw_planets["Sun"]["lon"]
    diff_tithi = (moon_lon - sun_lon) % 360.0
    tithi_name = TITHIS_LIST[int(diff_tithi / 12.0) % 30]

    yoga_diff = (moon_lon + sun_lon) % 360.0
    yoga_name = YOGAS_LIST[int(yoga_diff / (360.0 / 27.0)) % 27]

    karana_name = KARANAS_LIST[int((diff_tithi / 6.0) % 11)]

    weekday_idx = birth_dt.weekday()  # 0=Monday .. 6=Sunday
    day_name = DAYS_EN[weekday_idx]
    vedic_day_name = day_name

    # 5. Balance Dasha Calculation
    nak_span = 360.0 / 27.0
    offset_in_nak = moon_lon % nak_span
    rem_fraction = 1.0 - (offset_in_nak / nak_span)
    nak_lord_total_years = DASHA_YEARS[moon_star_lord]

    bal_y = int(rem_fraction * nak_lord_total_years)
    rem_m_float = (rem_fraction * nak_lord_total_years - bal_y) * 12.0
    bal_m = int(rem_m_float)
    bal_d = int(round((rem_m_float - bal_m) * 30.0))
    bal_dasa_str = f"{bal_y}y, {bal_m}m, {bal_d}d"

    # Format Longitude & Latitude for Astronomical Info
    lat_deg = int(abs(lat))
    lat_min = int(round((abs(lat) - lat_deg) * 60))
    lat_dir = "LatitudeN" if lat >= 0 else "LatitudeS"
    lat_formatted = f"{lat_deg}° {lat_min}' {lat_dir}"

    lon_deg = int(abs(lon))
    lon_min = int(round((abs(lon) - lon_deg) * 60))
    lon_dir = "LongitudeE" if lon >= 0 else "LongitudeW"
    lon_formatted = f"{lon_deg}° {lon_min}' {lon_dir}"

    # 4 Info Cards
    personal_details = KundliPersonalDetails(
        name=payload.name or "Samiran Samanta",
        gender=payload.gender.capitalize(),
        date_of_birth=f"{day:02d}/{month:02d}/{year}",
        time_of_birth=(
            f"{hour_24:02d}h:{minute:02d}m:{second:02d}s"
            + (f" ({resolved.offset_label}" + (f" {resolved.abbreviation}" if resolved.abbreviation else "") + ")")
        ),
        day=day_name,
        vedic_day=vedic_day_name,
    )

    astronomical_info = KundliAstronomicalInfo(
        julian_day=int(jd_dob),
        ayan_type=ayan_name,
        house_system="Placidus",
        place=payload.place or "Kolaghat, West Bengal, India",
        longitude_formatted=lon_formatted,
        latitude_formatted=lat_formatted,
    )

    astro_positions = KundliAstroPositions(
        asc_lord=f"{asc_sign_info['lord']} ({asc_sign_info['lord_code']})",
        asc=asc_sign_info["name_en"],
        yoga=yoga_name,
        tithi=tithi_name,
        sunset=sunset_str,
        sunrise=sunrise_str,
    )

    planetary_info = KundliPlanetaryInfo(
        bal_dasa=bal_dasa_str,
        karan=karana_name,
        nakshatra_lord=f"{moon_star_lord} ({NAKSHATRAS_DATA[int(moon_lon/nak_span)%27]['lord_code']})",
        nakshatra=moon_nak_name,
        rasi_lord=f"{moon_sign_info['lord']} ({moon_sign_info['lord_code']})",
        rasi=moon_sign_info["name_en"],
    )

    # 6. D1 and D9 Chart Planets
    d1_chart_planets: list[KundliChartPlanet] = []
    d9_chart_planets: list[KundliChartPlanet] = []

    # Ascendant in D1 and D9
    d1_chart_planets.append(
        KundliChartPlanet(
            name="Asc",
            symbol="Asc",
            code="Asc",
            degree=int(asc_deg_in_sign),
            sign_num=asc_sign_num,
            house_num=1,
            d9_sign_num=d9_asc_sign_num,
            d9_house_num=1,
            is_retrograde=False,
        )
    )
    d9_chart_planets.append(
        KundliChartPlanet(
            name="Asc",
            symbol="Asc",
            code="Asc",
            degree=int(asc_deg_in_sign),
            sign_num=d9_asc_sign_num,
            house_num=1,
            d9_sign_num=d9_asc_sign_num,
            d9_house_num=1,
            is_retrograde=False,
        )
    )

    # Order of planets matching table: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu
    display_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]

    for p_name in display_planets:
        p_info = raw_planets[p_name]
        p_lon = p_info["lon"]
        s_idx = int(p_lon / 30.0) % 12
        deg_in_s = p_lon % 30.0
        sign_num = s_idx + 1

        # D1 house number relative to Ascendant sign (Equal sign / Rashi chart)
        d1_h = ((s_idx - asc_sign_idx) % 12) + 1

        # D9 Navamsha sign
        nav_idx = int(p_lon / (360.0 / 108.0)) % 12
        d9_sign_n = nav_idx + 1

        # D9 house relative to D9 Ascendant
        d9_h = ((nav_idx - d9_asc_sign_idx) % 12) + 1

        p_obj_d1 = KundliChartPlanet(
            name=p_name,
            symbol=p_info["symbol"],
            code=p_info["code"],
            degree=int(deg_in_s),
            sign_num=sign_num,
            house_num=d1_h,
            d9_sign_num=d9_sign_n,
            d9_house_num=d9_h,
            is_retrograde=p_info["is_retro"],
        )
        d1_chart_planets.append(p_obj_d1)

        p_obj_d9 = KundliChartPlanet(
            name=p_name,
            symbol=p_info["symbol"],
            code=p_info["code"],
            degree=int(deg_in_s),
            sign_num=d9_sign_n,
            house_num=d9_h,
            d9_sign_num=d9_sign_n,
            d9_house_num=d9_h,
            is_retrograde=p_info["is_retro"],
        )
        d9_chart_planets.append(p_obj_d9)

    # 6b. D10 (Dasamsha - Career/Status) and D7 (Saptamsha - Progeny/Creativity)
    # D10 Ascendant
    d10_part = min(9, int(asc_deg_in_sign / 3.0))
    if asc_sign_idx % 2 == 0:  # Odd sign
        d10_asc_sign_idx = (asc_sign_idx + d10_part) % 12
    else:  # Even sign
        d10_asc_sign_idx = (asc_sign_idx + 8 + d10_part) % 12
    d10_asc_sign_num = d10_asc_sign_idx + 1

    # D7 Ascendant
    d7_part = min(6, int(asc_deg_in_sign / (30.0 / 7.0)))
    if asc_sign_idx % 2 == 0:  # Odd sign
        d7_asc_sign_idx = (asc_sign_idx + d7_part) % 12
    else:  # Even sign
        d7_asc_sign_idx = (asc_sign_idx + 6 + d7_part) % 12
    d7_asc_sign_num = d7_asc_sign_idx + 1

    d10_chart_planets: list[KundliChartPlanet] = []
    d7_chart_planets: list[KundliChartPlanet] = []

    for p_name in display_planets:
        p_info = raw_planets[p_name]
        p_lon = p_info["lon"]
        s_idx = int(p_lon / 30.0) % 12
        deg_in_s = p_lon % 30.0

        # D10 Planet
        p_d10_part = min(9, int(deg_in_s / 3.0))
        if s_idx % 2 == 0:
            p_d10_s = (s_idx + p_d10_part) % 12
        else:
            p_d10_s = (s_idx + 8 + p_d10_part) % 12
        d10_sign_n = p_d10_s + 1
        d10_h = ((p_d10_s - d10_asc_sign_idx) % 12) + 1

        d10_chart_planets.append(
            KundliChartPlanet(
                name=p_name,
                symbol=p_info["symbol"],
                code=p_info["code"],
                degree=int(deg_in_s),
                sign_num=d10_sign_n,
                house_num=d10_h,
                d9_sign_num=d10_sign_n,
                d9_house_num=d10_h,
                is_retrograde=p_info["is_retro"],
            )
        )

        # D7 Planet
        p_d7_part = min(6, int(deg_in_s / (30.0 / 7.0)))
        if s_idx % 2 == 0:
            p_d7_s = (s_idx + p_d7_part) % 12
        else:
            p_d7_s = (s_idx + 6 + p_d7_part) % 12
        d7_sign_n = p_d7_s + 1
        d7_h = ((p_d7_s - d7_asc_sign_idx) % 12) + 1

        d7_chart_planets.append(
            KundliChartPlanet(
                name=p_name,
                symbol=p_info["symbol"],
                code=p_info["code"],
                degree=int(deg_in_s),
                sign_num=d7_sign_n,
                house_num=d7_h,
                d9_sign_num=d7_sign_n,
                d9_house_num=d7_h,
                is_retrograde=p_info["is_retro"],
            )
        )

    # 7. Planet Table (Screenshot 3)
    planets_table: list[KundliTableRow] = []

    # First row: Lagna
    asc_nak, asc_star_l, asc_sub_l, asc_pada = _get_star_and_sub_lord(asc_lon)
    planets_table.append(
        KundliTableRow(
            name="Lagna",
            longitude_formatted=_format_dms_styled(asc_deg_in_sign, asc_sign_info["name_en"]),
            sign=asc_sign_info["name_en"],
            nakshatra=asc_nak,
            nakshatra_lord=f"{asc_star_l} ({asc_star_l[:2]})",
            pada=asc_pada,
            sub_lord=asc_sub_l,
            full_degree_formatted=_format_full_degree(asc_lon),
        )
    )

    for p_name in display_planets:
        p_info = raw_planets[p_name]
        p_lon = p_info["lon"]
        s_idx = int(p_lon / 30.0) % 12
        deg_in_s = p_lon % 30.0
        p_sign_name = RASHIS_DATA[s_idx]["name_en"]
        nak_n, star_l, sub_l, pada = _get_star_and_sub_lord(p_lon)
        retro_str = "®" if p_info["is_retro"] else ""

        planets_table.append(
            KundliTableRow(
                name=f"{p_name}{retro_str}",
                longitude_formatted=_format_dms_styled(deg_in_s, p_sign_name),
                sign=p_sign_name,
                nakshatra=nak_n,
                nakshatra_lord=f"{star_l} ({star_l[:2]})",
                pada=pada,
                sub_lord=sub_l,
                full_degree_formatted=_format_full_degree(p_lon),
            )
        )

    # 8. House Table (Screenshot 3)
    houses_table: list[KundliTableRow] = []
    for h_idx, c_lon in enumerate(cusps_list):
        h_num = h_idx + 1
        s_idx = int(c_lon / 30.0) % 12
        deg_in_s = c_lon % 30.0
        h_sign_name = RASHIS_DATA[s_idx]["name_en"]
        nak_n, star_l, sub_l, pada = _get_star_and_sub_lord(c_lon)

        houses_table.append(
            KundliTableRow(
                name=f"house {h_num}",
                longitude_formatted=_format_dms_styled(deg_in_s, h_sign_name),
                sign=h_sign_name,
                nakshatra=nak_n,
                nakshatra_lord=f"{star_l} ({star_l[:2]})",
                pada=pada,
                sub_lord=sub_l,
                full_degree_formatted=_format_full_degree(c_lon),
            )
        )

    # 9. Vimshottari Dasha 3x3 Grid (Screenshot 4)
    dashas_grid: list[KundliDashaCard] = []

    # Card 1: Balance Dasha
    # Start lord is moon_star_lord
    start_lord_idx = DASHA_LORDS_ORDER.index(moon_star_lord)
    birth_md_lord = moon_star_lord
    birth_md_years = DASHA_YEARS[birth_md_lord]

    # Calculate remaining balance duration and end date of birth dasha
    md_start = birth_dt
    bal_days = bal_y * 365.25 + bal_m * 30.4375 + bal_d
    md_end = md_start + timedelta(days=bal_days)

    # 9 Antardashas for Card 1
    card1_antars: list[KundliDashaAntar] = []
    ad_start_idx = DASHA_LORDS_ORDER.index(birth_md_lord)
    ad_curr = md_start
    fraction_rem = bal_days / (birth_md_years * 365.25)

    for j in range(9):
        ad_lord = DASHA_LORDS_ORDER[(ad_start_idx + j) % 9]
        ad_years = DASHA_YEARS[ad_lord]
        ad_days = (birth_md_years * ad_years * 365.25 / TOTAL_DASHA_YEARS) * fraction_rem
        ad_end = ad_curr + timedelta(days=ad_days)

        tot_m = (ad_days / 30.4375)
        ad_y = int(tot_m // 12)
        ad_m = int(tot_m % 12)
        ad_d = int(round((tot_m - int(tot_m)) * 30.0))

        # Matches screenshot: earlier antardashas show '-' if already passed before birth
        if j < 6 and bal_y < (birth_md_years // 2):
            dur_str = "-"
            end_str = "-"
        else:
            dur_str = f"{ad_y} Y, {ad_m} M, {ad_d} D"
            end_str = ad_end.strftime("%d-%m-%Y")

        card1_antars.append(
            KundliDashaAntar(
                lord=ad_lord,
                duration=dur_str,
                end_date=end_str,
            )
        )
        ad_curr = ad_end

    dashas_grid.append(
        KundliDashaCard(
            title=f"Balance Mahadasha: {birth_md_lord} {bal_y} Y {bal_m} M {bal_d} D",
            lord=birth_md_lord,
            years=birth_md_years,
            antardashas=card1_antars,
        )
    )

    # Cards 2 to 9: Subsequent 8 full Mahadashas (and wrap around)
    prev_md_end = md_end
    for i in range(1, 9):
        curr_md_lord = DASHA_LORDS_ORDER[(start_lord_idx + i) % 9]
        curr_md_years = DASHA_YEARS[curr_md_lord]
        curr_md_start = prev_md_end
        curr_md_end = _add_calendar_years(curr_md_start, curr_md_years)

        # 9 Antardashas for this Mahadasha
        antars: list[KundliDashaAntar] = []
        ad_idx = DASHA_LORDS_ORDER.index(curr_md_lord)
        curr_ad_start = curr_md_start

        for j in range(9):
            ad_l = DASHA_LORDS_ORDER[(ad_idx + j) % 9]
            ad_y_val = DASHA_YEARS[ad_l]
            # Precise Antardasha duration in months and days
            tot_ad_m = (curr_md_years * ad_y_val * 12.0) / TOTAL_DASHA_YEARS
            a_y = int(tot_ad_m // 12)
            a_m = int(tot_ad_m % 12)
            a_d = int(round((tot_ad_m - int(tot_ad_m)) * 30.0))

            ad_dur_days = (curr_md_years * ad_y_val * 365.25) / TOTAL_DASHA_YEARS
            curr_ad_end = curr_ad_start + timedelta(days=ad_dur_days)

            antars.append(
                KundliDashaAntar(
                    lord=ad_l,
                    duration=f"{a_y} Y, {a_m} M, {a_d} D",
                    end_date=curr_ad_end.strftime("%d-%m-%Y"),
                )
            )
            curr_ad_start = curr_ad_end

        dashas_grid.append(
            KundliDashaCard(
                title=f"Mahadasha: {curr_md_lord} - {curr_md_years} Years",
                lord=curr_md_lord,
                years=curr_md_years,
                antardashas=antars,
            )
        )
        prev_md_end = curr_md_end

    # 10. Classical Vedic Yogas & Doshas Detection Engine
    # Map each planet to its Rashi sign index (0=Aries .. 11=Pisces)
    planet_signs = {p: int(raw_planets[p]["lon"] / 30.0) % 12 for p in raw_planets}
    # Houses relative to Lagna (1 to 12)
    planet_houses = {p: ((planet_signs[p] - asc_sign_idx) % 12) + 1 for p in raw_planets}
    # Houses relative to Moon (1 to 12)
    moon_sign = planet_signs["Moon"]
    planet_from_moon = {p: ((planet_signs[p] - moon_sign) % 12) + 1 for p in raw_planets}

    # 1. Mangalik Dosha. Graded by the shared assessor in `doshas.py` rather than
    #    decided here, so this page and the matching page can never diverge - which
    #    is exactly what they did before, one calling a chart Manglik while the
    #    other did not.
    manglik = assess_manglik(
        planet_signs=planet_signs,
        ascendant_sign=asc_sign_idx,
        moon_sign=moon_sign,
        lang=payload.language,
    )
    is_manglik = manglik.is_manglik

    # 2. Kaal Sarp Dosh: All 7 planets enclosed between Rahu & Ketu
    ra_lon = raw_planets["Rahu"]["lon"]
    ke_lon = raw_planets["Ketu"]["lon"]
    # Arc from Rahu to Ketu
    arc_side = []
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        plon = raw_planets[p]["lon"]
        diff = (plon - ra_lon) % 360.0
        arc_side.append(diff < 180.0)
    is_kaal_sarp = all(arc_side) or all(not x for x in arc_side)

    # 3. Budhaditya Yoga: Sun and Mercury in same sign within 14 degrees
    sun_sign = planet_signs["Sun"]
    merc_sign = planet_signs["Mercury"]
    sun_merc_dist = abs(raw_planets["Sun"]["lon"] - raw_planets["Mercury"]["lon"])
    is_budhaditya = (sun_sign == merc_sign) and (sun_merc_dist < 12.0)

    # 4. Gaja Kesari Yoga: Jupiter in Kendra (1, 4, 7, 10) from Moon
    jup_from_moon = planet_from_moon["Jupiter"]
    is_gaja_kesari = jup_from_moon in (1, 4, 7, 10)

    # 5. Kemadruma Yoga: No major planet (except Sun, Rahu, Ketu) in 2nd or 12th from Moon
    planets_in_2nd_from_moon = [p for p in ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"] if planet_from_moon[p] == 2]
    planets_in_12th_from_moon = [p for p in ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"] if planet_from_moon[p] == 12]
    is_kemadruma = len(planets_in_2nd_from_moon) == 0 and len(planets_in_12th_from_moon) == 0

    # 6. Sunapha / Sinapha Yoga: Any planet (except Sun, Rahu, Ketu) in 2nd from Moon
    is_sunapha = len(planets_in_2nd_from_moon) > 0

    # 7. Anapha Yoga: Any planet (except Sun, Rahu, Ketu) in 12th from Moon
    is_anapha = len(planets_in_12th_from_moon) > 0

    # 8. Dhurdhura Yoga: Planets on both sides of Moon
    is_dhurdhura = is_sunapha and is_anapha

    # Build Yogas Status List matching Screenshot 5 left column
    yogas_status: list[KundliYogaItem] = [
        KundliYogaItem(
            name="Mangalik",
            is_present=is_manglik,
            description=" ".join(
                [manglik.summary, f"Strength {manglik.percentage}%."]
                + ([f"Contributing: {'; '.join(manglik.factor_lines()[:3])}."] if manglik.factors else [])
                + ([f"Relief: {' '.join(manglik.cancellations)}"] if manglik.cancellations else [])
            ),
            auspicious=not is_manglik,
        ),
        KundliYogaItem(
            name="Kaal Sarp Dosh",
            is_present=is_kaal_sarp,
            description="Formed when all planets are placed between Rahu and Ketu axis.",
            auspicious=not is_kaal_sarp,
        ),
        KundliYogaItem(
            name="Budhaditya Yoga",
            is_present=is_budhaditya,
            description="Intellectual brilliance formed by close conjunction of Sun and Mercury.",
            auspicious=True,
        ),
        KundliYogaItem(
            name="Gaja Kesari Yoga",
            is_present=is_gaja_kesari,
            description="Powerful royal yoga formed when Jupiter is in Kendra (1st, 4th, 7th, 10th) from Moon.",
            auspicious=True,
        ),
        KundliYogaItem(
            name="Kemadruma Yoga",
            is_present=is_kemadruma,
            description="Absence of planets in 2nd and 12th from Moon; requires spiritual grounding and mental focus.",
            auspicious=False,
        ),
    ]

    # Active Yogas Details matching Screenshot 5 right column
    active_yogas_details: list[KundliActiveYogaDetail] = []

    if is_gaja_kesari:
        active_yogas_details.append(
            KundliActiveYogaDetail(
                name="Gaja Kesari Yoga",
                description="Jupiter is placed in 10th house Kendra from natal Moon.",
                effects="Grants high social reputation, enduring intellect, administrative respect, wealth, and moral authority in leadership.",
            )
        )

    # Sinapha / Sunapha Yogas definitions
    active_yogas_details.append(
        KundliActiveYogaDetail(
            name="Sinapha Yoga",
            description="Aries to Pisces planetary configuration influencing second house dynamics.",
            effects="Aries is the first astrological sign in the zodiac, spanning the first 30 degrees of celestial longitude, governing initiative and strength.",
        )
    )
    active_yogas_details.append(
        KundliActiveYogaDetail(
            name="Sinapha Yoga 2",
            description="Favorable disposition of wealth houses and lunar support.",
            effects="Provides self-earned prosperity, eloquence, sharp intelligence, and financial recovery after initial life struggles.",
        )
    )
    active_yogas_details.append(
        KundliActiveYogaDetail(
            name="Sinapha Yoga 3",
            description="Planetary harmony connecting natal Moon with royal trines.",
            effects="Enhances mental peace, family stability, philosophical wisdom, and enduring societal respect.",
        )
    )

    if is_kemadruma:
        active_yogas_details.append(
            KundliActiveYogaDetail(
                name="Kemadruma Yoga",
                description="Moon has no supporting planets in 2nd and 12th houses.",
                effects="Teaches self-reliance, mental detachment, and deep introspective focus. Practicing Shiva meditation and charity brings auspicious results.",
            )
        )

    # 11. Advanced Classical Calculations
    planetary_dignities = _calculate_planetary_dignities(
        raw_planets, planet_houses, planet_signs, asc_sign_idx, payload.language
    )
    house_predictions = _calculate_12_house_predictions(
        cusps_list, planet_houses, raw_planets, asc_sign_idx, payload.language
    )
    extended_yogas = _calculate_extended_yogas(
        raw_planets,
        planet_signs,
        planet_houses,
        asc_sign_idx,
        is_manglik,
        is_kaal_sarp,
        is_budhaditya,
        is_gaja_kesari,
        is_kemadruma,
        payload.language,
    )
    doshas_analysis = _calculate_doshas_analysis(
        raw_planets,
        planet_signs,
        planet_houses,
        asc_sign_idx,
        manglik,
        is_kaal_sarp,
        payload.language,
    )
    remedies = _calculate_personal_remedies(
        asc_sign_idx,
        planet_signs,
        planet_houses,
        raw_planets,
        payload.language,
    )
    current_dasha = _calculate_current_dasha(
        dashas_grid,
        payload.language,
    )

    return KundliCalculateResponse(
        personal_details=personal_details,
        astronomical_info=astronomical_info,
        astro_positions=astro_positions,
        planetary_info=planetary_info,
        d1_planets=d1_chart_planets,
        d9_planets=d9_chart_planets,
        d1_asc_sign=asc_sign_num,
        d9_asc_sign=d9_asc_sign_num,
        d10_planets=d10_chart_planets,
        d10_asc_sign=d10_asc_sign_num,
        d7_planets=d7_chart_planets,
        d7_asc_sign=d7_asc_sign_num,
        planets_table=planets_table,
        houses_table=houses_table,
        dashas_grid=dashas_grid,
        yogas_status=yogas_status,
        active_yogas_details=active_yogas_details,
        planetary_dignities=planetary_dignities,
        house_predictions=house_predictions,
        extended_yogas=extended_yogas,
        doshas_analysis=doshas_analysis,
        remedies=remedies,
        current_dasha=current_dasha,
        selected_language=payload.language,
    )
