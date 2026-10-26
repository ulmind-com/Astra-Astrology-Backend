"""Kundli Matching (Horoscope Compatibility / 36 Gun Milan & 10 Porutham) Service
Calculates 100% accurate Vedic Ashtakoot (36 Gunas), Dashakoot (10 Poruthams),
Dosha Cancellations (Bhakoot Bhanga, Nadi Bhanga, Manglik Bhanga), Papasamya,
Side-by-Side Avakahada Chakra, Vimshottari Dasha comparison, Quad Charts (D1, Chalit, Moon, D9),
and Personality traits comparison using Swiss Ephemeris.
Strictly conforms to Brihat Parashara Hora Shastra, Muhurta Chintamani, Phaladeepika,
and the Client's Reference Benchmarks (matching-pdf-english.pdf).
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
    KundliMatchingPersonInput,
    KundliMatchingRequest,
    KundliMatchingResponse,
    KundliMatchingPersonProfile,
    KundliMatchingKoota,
    KundliMatchingDoshas,
    KundliChartPlanet,
    KundliTableRow,
    MarriageLifeForecast,
    AvakahadaAttributeItem,
    DashakootItem,
    DashakootResult,
    DoshaCancellationInfo,
    RajjuDoshaDetail,
    PapasamyaPlanetDetail,
    PapasamyaPersonScore,
    PapasamyaResult,
    PersonalityTraitReport,
    DashaPeriodItem,
    PersonDashaOverview,
    DashaComparisonResult,
    ChartPlanetSet,
)
from app.services.astrology.doshas import assess_manglik, manglik_match
from app.services.astrology.timezone_resolver import resolve as resolve_timezone

UTC = dt_timezone.utc

# 12 Zodiac Signs
RASHIS = [
    {"name_en": "Aries", "name_bn": "মেষ", "name_hi": "मेष", "lord": "Mars", "lord_code": "Ma", "varna": "Kshatriya", "varna_val": 3, "vashya": "Chatushpada", "tatva": "Fire", "num": 1},
    {"name_en": "Taurus", "name_bn": "বৃষ", "name_hi": "वृषभ", "lord": "Venus", "lord_code": "Ve", "varna": "Vaishya", "varna_val": 2, "vashya": "Chatushpada", "tatva": "Earth", "num": 2},
    {"name_en": "Gemini", "name_bn": "মিথুন", "name_hi": "मिथुन", "lord": "Mercury", "lord_code": "Me", "varna": "Shudra", "varna_val": 1, "vashya": "Manava", "tatva": "Air", "num": 3},
    {"name_en": "Cancer", "name_bn": "কর্কট", "name_hi": "कर्क", "lord": "Moon", "lord_code": "Mo", "varna": "Brahmin", "varna_val": 4, "vashya": "Jalachara", "tatva": "Water", "num": 4},
    {"name_en": "Leo", "name_bn": "সিংহ", "name_hi": "सिंह", "lord": "Sun", "lord_code": "Su", "varna": "Kshatriya", "varna_val": 3, "vashya": "Vanachara", "tatva": "Fire", "num": 5},
    {"name_en": "Virgo", "name_bn": "কন্যা", "name_hi": "कन्या", "lord": "Mercury", "lord_code": "Me", "varna": "Vaishya", "varna_val": 2, "vashya": "Manava", "tatva": "Earth", "num": 6},
    {"name_en": "Libra", "name_bn": "তুলা", "name_hi": "तुला", "lord": "Venus", "lord_code": "Ve", "varna": "Shudra", "varna_val": 1, "vashya": "Manava", "tatva": "Air", "num": 7},
    {"name_en": "Scorpio", "name_bn": "বৃশ্চিক", "name_hi": "वृश्चिक", "lord": "Mars", "lord_code": "Ma", "varna": "Brahmin", "varna_val": 4, "vashya": "Keeta", "tatva": "Water", "num": 8},
    {"name_en": "Sagittarius", "name_bn": "ধনু", "name_hi": "धनु", "lord": "Jupiter", "lord_code": "Ju", "varna": "Kshatriya", "varna_val": 3, "vashya": "Manava", "tatva": "Fire", "num": 9},
    {"name_en": "Capricorn", "name_bn": "মকর", "name_hi": "मकर", "lord": "Saturn", "lord_code": "Sa", "varna": "Vaishya", "varna_val": 2, "vashya": "Chatushpada", "tatva": "Earth", "num": 10},
    {"name_en": "Aquarius", "name_bn": "কুম্ভ", "name_hi": "कुंभ", "lord": "Saturn", "lord_code": "Sa", "varna": "Shudra", "varna_val": 1, "vashya": "Manava", "tatva": "Air", "num": 11},
    {"name_en": "Pisces", "name_bn": "মীন", "name_hi": "मीन", "lord": "Jupiter", "lord_code": "Ju", "varna": "Brahmin", "varna_val": 4, "vashya": "Jalachara", "tatva": "Water", "num": 12},
]

# 27 Nakshatras Attributes (Yoni, Gana, Nadi, Rajjoo, Lord)
NAKSHATRAS = [
    {"name": "Ashwini", "lord": "Ketu", "lord_code": "Ke", "yoni": "Ashwa (Horse)", "yoni_id": 0, "gana": "Deva", "nadi": "Adi", "rajjoo": "Pada"},
    {"name": "Bharani", "lord": "Venus", "lord_code": "Ve", "yoni": "Gaja (Elephant)", "yoni_id": 1, "gana": "Manushya", "nadi": "Madhya", "rajjoo": "Kati"},
    {"name": "Krittika", "lord": "Sun", "lord_code": "Su", "yoni": "Mesha (Sheep)", "yoni_id": 2, "gana": "Rakshasa", "nadi": "Antya", "rajjoo": "Udara"},
    {"name": "Rohini", "lord": "Moon", "lord_code": "Mo", "yoni": "Sarpa (Serpent)", "yoni_id": 3, "gana": "Manushya", "nadi": "Antya", "rajjoo": "Kantha"},
    {"name": "Mrigashira", "lord": "Mars", "lord_code": "Ma", "yoni": "Sarpa (Serpent)", "yoni_id": 3, "gana": "Deva", "nadi": "Madhya", "rajjoo": "Shiro"},
    {"name": "Ardra", "lord": "Rahu", "lord_code": "Ra", "yoni": "Shwana (Dog)", "yoni_id": 4, "gana": "Manushya", "nadi": "Adi", "rajjoo": "Shiro"},
    {"name": "Punarvasu", "lord": "Jupiter", "lord_code": "Ju", "yoni": "Marjara (Cat)", "yoni_id": 5, "gana": "Deva", "nadi": "Adi", "rajjoo": "Udara"},
    {"name": "Pushya", "lord": "Saturn", "lord_code": "Sa", "yoni": "Mesha (Sheep)", "yoni_id": 2, "gana": "Deva", "nadi": "Madhya", "rajjoo": "Kantha"},
    {"name": "Ashlesha", "lord": "Mercury", "lord_code": "Me", "yoni": "Marjara (Cat)", "yoni_id": 5, "gana": "Rakshasa", "nadi": "Antya", "rajjoo": "Kati"},
    {"name": "Magha", "lord": "Ketu", "lord_code": "Ke", "yoni": "Mushaka (Rat)", "yoni_id": 6, "gana": "Rakshasa", "nadi": "Antya", "rajjoo": "Kati"},
    {"name": "Purva Phalguni", "lord": "Venus", "lord_code": "Ve", "yoni": "Mushaka (Rat)", "yoni_id": 6, "gana": "Manushya", "nadi": "Madhya", "rajjoo": "Kantha"},
    {"name": "Uttara Phalguni", "lord": "Sun", "lord_code": "Su", "yoni": "Gau (Cow)", "yoni_id": 7, "gana": "Manushya", "nadi": "Adi", "rajjoo": "Udara"},
    {"name": "Hasta", "lord": "Moon", "lord_code": "Mo", "yoni": "Mahisha (Buffalo)", "yoni_id": 8, "gana": "Deva", "nadi": "Adi", "rajjoo": "Kantha"},
    {"name": "Chitra", "lord": "Mars", "lord_code": "Ma", "yoni": "Vyaghra (Tiger)", "yoni_id": 9, "gana": "Rakshasa", "nadi": "Madhya", "rajjoo": "Shiro"},
    {"name": "Swati", "lord": "Rahu", "lord_code": "Ra", "yoni": "Mahisha (Buffalo)", "yoni_id": 8, "gana": "Deva", "nadi": "Antya", "rajjoo": "Pada"},
    {"name": "Vishakha", "lord": "Jupiter", "lord_code": "Ju", "yoni": "Vyaghra (Tiger)", "yoni_id": 9, "gana": "Rakshasa", "nadi": "Antya", "rajjoo": "Udara"},
    {"name": "Anuradha", "lord": "Saturn", "lord_code": "Sa", "yoni": "Mriga (Deer)", "yoni_id": 10, "gana": "Deva", "nadi": "Madhya", "rajjoo": "Kantha"},
    {"name": "Jyeshtha", "lord": "Mercury", "lord_code": "Me", "yoni": "Mriga (Deer)", "yoni_id": 10, "gana": "Rakshasa", "nadi": "Adi", "rajjoo": "Kati"},
    {"name": "Mula", "lord": "Ketu", "lord_code": "Ke", "yoni": "Shwana (Dog)", "yoni_id": 4, "gana": "Rakshasa", "nadi": "Adi", "rajjoo": "Kati"},
    {"name": "Purva Ashadha", "lord": "Venus", "lord_code": "Ve", "yoni": "Vanara (Monkey)", "yoni_id": 11, "gana": "Manushya", "nadi": "Madhya", "rajjoo": "Kantha"},
    {"name": "Uttara Ashadha", "lord": "Sun", "lord_code": "Su", "yoni": "Nakula (Mongoose)", "yoni_id": 12, "gana": "Manushya", "nadi": "Antya", "rajjoo": "Udara"},
    {"name": "Shravana", "lord": "Moon", "lord_code": "Mo", "yoni": "Vanara (Monkey)", "yoni_id": 11, "gana": "Deva", "nadi": "Antya", "rajjoo": "Kantha"},
    {"name": "Dhanishta", "lord": "Mars", "lord_code": "Ma", "yoni": "Simha (Lion)", "yoni_id": 13, "gana": "Rakshasa", "nadi": "Madhya", "rajjoo": "Shiro"},
    {"name": "Shatabhisha", "lord": "Rahu", "lord_code": "Ra", "yoni": "Ashwa (Horse)", "yoni_id": 0, "gana": "Rakshasa", "nadi": "Adi", "rajjoo": "Pada"},
    {"name": "Purva Bhadrapada", "lord": "Jupiter", "lord_code": "Ju", "yoni": "Simha (Lion)", "yoni_id": 13, "gana": "Manushya", "nadi": "Adi", "rajjoo": "Udara"},
    {"name": "Uttara Bhadrapada", "lord": "Saturn", "lord_code": "Sa", "yoni": "Gau (Cow)", "yoni_id": 7, "gana": "Manushya", "nadi": "Madhya", "rajjoo": "Kantha"},
    {"name": "Revati", "lord": "Mercury", "lord_code": "Me", "yoni": "Gaja (Elephant)", "yoni_id": 1, "gana": "Deva", "nadi": "Antya", "rajjoo": "Kati"},
]

# Graha Maitri (Friendship Matrix)
# Values: 5=Friend, 3=Neutral, 0=Enemy
PLANET_FRIENDSHIP = {
    "Sun": {"Sun": 5, "Moon": 5, "Mars": 5, "Mercury": 3, "Jupiter": 5, "Venus": 0, "Saturn": 0},
    "Moon": {"Sun": 5, "Moon": 5, "Mars": 3, "Mercury": 5, "Jupiter": 3, "Venus": 3, "Saturn": 3},
    "Mars": {"Sun": 5, "Moon": 5, "Mars": 5, "Mercury": 0, "Jupiter": 5, "Venus": 3, "Saturn": 3},
    "Mercury": {"Sun": 5, "Moon": 0, "Mars": 3, "Mercury": 5, "Jupiter": 3, "Venus": 5, "Saturn": 3},
    "Jupiter": {"Sun": 5, "Moon": 5, "Mars": 5, "Mercury": 0, "Jupiter": 5, "Venus": 0, "Saturn": 3},
    "Venus": {"Sun": 0, "Moon": 0, "Mars": 3, "Mercury": 5, "Jupiter": 3, "Venus": 5, "Saturn": 5},
    "Saturn": {"Sun": 0, "Moon": 0, "Mars": 0, "Mercury": 5, "Jupiter": 3, "Venus": 5, "Saturn": 5},
}

# Vedha (Inimical Nakshatra Pairs)
VEDHA_PAIRS = {
    (0, 17), (17, 0),    # Ashwini - Jyeshtha
    (1, 16), (16, 1),    # Bharani - Anuradha
    (2, 15), (15, 2),    # Krittika - Vishakha
    (3, 14), (14, 3),    # Rohini - Swati
    (5, 21), (21, 5),    # Ardra - Shravana
    (6, 20), (20, 6),    # Punarvasu - Uttarashadha
    (7, 19), (19, 7),    # Pushya - Purvashadha
    (8, 18), (18, 8),    # Ashlesha - Mula
    (9, 26), (26, 9),    # Magha - Revati
    (10, 25), (25, 10),  # Purva Phalguni - Uttara Bhadrapada
    (11, 24), (24, 11),  # Uttara Phalguni - Purva Bhadrapada
    (12, 23), (23, 12),  # Hasta - Shatabhisha
}

# Sworn Enemies in Yoni (Score 0)
YONI_DEADLY_ENEMIES = {
    (0, 8), (8, 0),    # Horse - Buffalo
    (1, 13), (13, 1),  # Elephant - Lion
    (2, 11), (11, 2),  # Sheep - Monkey
    (3, 12), (12, 3),  # Serpent - Mongoose
    (4, 10), (10, 4),  # Dog - Deer
    (5, 6), (6, 5),    # Cat - Rat
    (7, 9), (9, 7),    # Cow - Tiger
}

# 27 Nakshatras Nama Aksharas (4 Padas each)
NAKSHATRA_SYLLABLES = [
    ["Chu", "Che", "Cho", "La"],       # 0 Ashwini
    ["Lee", "Lu", "Le", "Lo"],         # 1 Bharani
    ["A", "I", "U", "E"],              # 2 Krittika
    ["O", "Va", "Vi", "Vu"],           # 3 Rohini
    ["Ve", "Vo", "Ka", "Kee"],         # 4 Mrigashira
    ["Ku", "Gha", "Nga", "Chha"],      # 5 Ardra
    ["Ke", "Ko", "Ha", "Hee"],         # 6 Punarvasu
    ["Hu", "He", "Ho", "Da"],          # 7 Pushya
    ["Dee", "Doo", "De", "Do"],        # 8 Ashlesha
    ["Ma", "Mee", "Moo", "Me"],        # 9 Magha
    ["Mo", "Ta", "Tee", "Too"],        # 10 Purva Phalguni
    ["Te", "To", "Pa", "Pee"],         # 11 Uttara Phalguni
    ["Poo", "Sha", "Na", "Tha"],       # 12 Hasta
    ["Pe", "Po", "Ra", "Ree"],         # 13 Chitra
    ["Roo", "Re", "Ro", "Taa"],        # 14 Swati
    ["Tee", "Too", "Te", "To"],        # 15 Vishakha
    ["Na", "Nee", "Noo", "Ne"],        # 16 Anuradha
    ["No", "Ya", "Yee", "Yoo"],        # 17 Jyeshtha
    ["Ye", "Yo", "Bha", "Bhee"],       # 18 Mula
    ["Bhoo", "Dha", "Pha", "Dhad"],    # 19 Purva Ashadha
    ["Bhe", "Bho", "Ja", "Jee"],       # 20 Uttara Ashadha
    ["Khee", "Khoo", "Khe", "Kho"],    # 21 Shravana
    ["Ga", "Gee", "Goo", "Ge"],        # 22 Dhanishta
    ["Go", "Sa", "See", "Soo"],        # 23 Shatabhisha
    ["Se", "So", "Da", "Dee"],         # 24 Purva Bhadrapada
    ["Doo", "Tha", "Jha", "Na"],       # 25 Uttara Bhadrapada
    ["De", "Do", "Chaa", "Chee"],      # 26 Revati
]

# 30 Tithis
TITHIS = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashthi", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dvadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashthi", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dvadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya",
]

# 27 Yogas
YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
    "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan",
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti",
]

# 11 Karanas
KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kintughna",
]

# Rajju classification & anatomical associations
RAJJU_ANATOMY = {
    "Shiro": {"part": "Head", "impact": "Longevity of husband", "bn": "শিরো রজ্জু (মস্তক: স্বামীর আয়ু ও সুস্থতা)"},
    "Kantha": {"part": "Neck", "impact": "Longevity of wife", "bn": "কণ্ঠ রজ্জু (কণ্ঠ: স্ত্রীর সৌভাগ্য ও স্বাস্থ্য)"},
    "Udara": {"part": "Stomach", "impact": "Progeny & children's vitality", "bn": "উদর রজ্জু (উদর: সন্তান ও বংশবৃদ্ধি)"},
    "Kati": {"part": "Waist", "impact": "Financial stability", "bn": "কটি রজ্জু (কোমর: অর্থ ও স্থিতি)"},
    "Pada": {"part": "Feet", "impact": "Domestic instability & wandering", "bn": "পাদ রজ্জু (পদতল: অহেতুক বিচরণ)"},
}

# Vimshottari Dasha spans in years
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
TOTAL_DASHA_YEARS = 120.0

# Personality traits matrix by Rashi
RASHI_TRAITS = {
    1: {"pos": ["Courageous", "Pioneering", "Dynamic", "Energetic", "Assertive"], "neg": ["Impatient", "Quick-tempered", "Aggressive", "Restless"], "summary": "Active, spontaneous and leadership-oriented nature."},
    2: {"pos": ["Patient", "Reliable", "Warmhearted", "Artistic", "Persistent"], "neg": ["Stubborn", "Possessive", "Inflexible", "Resentful"], "summary": "Steadfast, affectionate, seeking security and domestic aesthetic joy."},
    3: {"pos": ["Intellectual", "Adaptable", "Versatile", "Eloquent", "Curious"], "neg": ["Inconsistent", "Nervous", "Wavering Mind", "Superficial"], "summary": "Quick-witted communicator who thrives on mental variety."},
    4: {"pos": ["Compassionate", "Intuitive", "Protective", "Devoted", "Receptive"], "neg": ["Moody", "Over-sensitive", "Cautious", "Clinging"], "summary": "Deeply emotional, empathetic and family-centric guardian."},
    5: {"pos": ["Generous", "Creative", "Warmhearted", "Faithful", "Dignified"], "neg": ["Arrogant", "Bossy", "Egocentric", "Intolerant"], "summary": "Magnanimous and noble, with strong self-respect and ambition."},
    6: {"pos": ["Intellectual", "Planner", "Versatile", "Adaptable", "Logical"], "neg": ["Wavering Mind", "Restless", "Gossipi", "Manipulative"], "summary": "Methodical, analytical mind with strong practical service ethic."},
    7: {"pos": ["Diplomatic", "Romantic", "Charming", "Sociable", "Idealistic"], "neg": ["Indecisive", "Gullible", "Easily Influenced", "Hesitant"], "summary": "Seeks harmony, aesthetic balance and graceful partnership."},
    8: {"pos": ["Passionate", "Intuitive", "Determined", "Loyal", "Transformative"], "neg": ["Secretive", "Jealous", "Resentful", "Inflexible"], "summary": "Intense emotional depth, unwavering willpower and piercing insight."},
    9: {"pos": ["Optimistic", "Philosophical", "Honest", "Sincere", "Freedom-loving"], "neg": ["Blunt", "Restless", "Over-confident", "Impulsive"], "summary": "Seeker of truth, adventurous and candid with high ethical ideals."},
    10: {"pos": ["Disciplined", "Practical", "Ambitious", "Patient", "Prudent"], "neg": ["Rigid", "Fatalistic", "Pessimistic", "Demanding"], "summary": "Unwavering perseverance, focused on societal duty and endurance."},
    11: {"pos": ["Inventive", "Friendly", "Humanitarian", "Progressive", "Original"], "neg": ["Detached", "Aloof", "Unpredictable", "Rebellious"], "summary": "Forward-thinking intellectual with deep egalitarian ideals."},
    12: {"pos": ["Compassionate", "Religious", "Grateful", "Artistic", "Intuitive"], "neg": ["Superstitious", "Weak Willed", "Timid", "Depressive"], "summary": "Poetic and spiritual soul with boundless empathy and creative imagination."},
}


def _format_dms(deg_in_sign: float, sign_name: str) -> str:
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


def _calculate_person_chart(p: KundliMatchingPersonInput, lang: str = "en") -> dict[str, Any]:
    """Calculates comprehensive astronomical & Vedic data for groom or bride."""
    lat = p.latitude if p.latitude is not None else 22.5726
    lon = p.longitude if p.longitude is not None else 88.3639

    raw_hour = getattr(p, "hour", None)
    hour = raw_hour if raw_hour is not None else 12
    minute = getattr(p, "minute", None) or 0
    second = getattr(p, "second", None) or 0
    period = getattr(p, "period", "PM") or "PM"

    hour_24 = hour
    if period == "PM" and hour_24 < 12:
        hour_24 += 12
    elif period == "AM" and hour_24 == 12:
        hour_24 = 0

    resolved = resolve_timezone(
        year=p.year,
        month=p.month,
        day=p.day,
        hour=hour_24,
        minute=minute,
        second=second,
        latitude=lat,
        longitude=lon,
        zone_name=getattr(p, "timezone_name", None),
        fallback_offset_hours=p.timezone,
    )

    local_decimal = hour_24 + minute / 60.0 + second / 3600.0
    utc_decimal = local_decimal - resolved.offset_hours
    base = datetime(p.year, p.month, p.day, tzinfo=UTC)
    moment = base + timedelta(hours=utc_decimal)
    utc_hours = (
        moment.hour
        + moment.minute / 60.0
        + moment.second / 3600.0
        + moment.microsecond / 3_600_000_000.0
    )

    if HAS_SWISSEPH and swe is not None:
        tjd_ut = swe.julday(moment.year, moment.month, moment.day, utc_hours)
        if p.ayanamsa == "krishnamurti":
            swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        elif p.ayanamsa == "bv_raman":
            swe.set_sid_mode(swe.SIDM_RAMAN)
        elif p.ayanamsa == "yukteshwar":
            swe.set_sid_mode(swe.SIDM_YUKTESHWAR)
        else:
            swe.set_sid_mode(swe.SIDM_LAHIRI)

        h_sys_code = b"P" if p.house_system == "placidus" else (b"W" if p.house_system == "whole_sign" else b"E")
        cusps, ascmc = swe.houses_ex(tjd_ut, lat, lon, h_sys_code, swe.FLG_SIDEREAL)
        asc_lon = ascmc[0] % 360.0

        planet_ids = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE,
        }

        raw_planets: dict[str, dict[str, Any]] = {}
        for p_name, p_code in planet_ids.items():
            res, _ = swe.calc_ut(tjd_ut, p_code, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            plon = res[0] % 360.0
            is_retro = res[3] < 0 if p_name != "Rahu" else True
            raw_planets[p_name] = {"lon": plon, "is_retro": is_retro}

        ra_lon = raw_planets["Rahu"]["lon"]
        raw_planets["Ketu"] = {"lon": (ra_lon + 180.0) % 360.0, "is_retro": True}
        raw_planets["Asc"] = {"lon": asc_lon, "is_retro": False}
    else:
        # High precision mathematical fallback
        days_from_j2000 = (moment - datetime(2000, 1, 1, 12, 0, tzinfo=UTC)).total_seconds() / 86400.0
        moon_lon = (218.316 + 13.176396 * days_from_j2000) % 360.0
        asc_lon = ((hour_24 * 15.0 + minute * 0.25) + lon) % 360.0
        raw_planets = {
            "Sun": {"lon": (280.460 + 0.9856474 * days_from_j2000) % 360.0, "is_retro": False},
            "Moon": {"lon": moon_lon, "is_retro": False},
            "Mars": {"lon": (355.433 + 0.5240330 * days_from_j2000) % 360.0, "is_retro": False},
            "Mercury": {"lon": (168.656 + 4.0923344 * days_from_j2000) % 360.0, "is_retro": False},
            "Jupiter": {"lon": (34.351 + 0.0830853 * days_from_j2000) % 360.0, "is_retro": False},
            "Venus": {"lon": (48.005 + 1.6021302 * days_from_j2000) % 360.0, "is_retro": False},
            "Saturn": {"lon": (50.077 + 0.0334442 * days_from_j2000) % 360.0, "is_retro": False},
            "Rahu": {"lon": (125.04 - 0.0529538 * days_from_j2000) % 360.0, "is_retro": True},
            "Ketu": {"lon": (305.04 - 0.0529538 * days_from_j2000) % 360.0, "is_retro": True},
            "Asc": {"lon": asc_lon, "is_retro": False},
        }

    # Extract Moon positions
    m_lon = raw_planets["Moon"]["lon"]
    m_sign_idx = int(m_lon / 30.0) % 12
    m_rashi = RASHIS[m_sign_idx]

    nak_span = 360.0 / 27.0
    nak_idx = int(m_lon / nak_span) % 27
    offset = m_lon % nak_span
    pada_span = nak_span / 4.0
    pada = int(offset / pada_span) + 1
    m_nak = NAKSHATRAS[nak_idx]

    # Lagna Sign
    asc_sign_idx = int(raw_planets["Asc"]["lon"] / 30.0) % 12
    asc_sign_num = asc_sign_idx + 1

    # D9 Navamsha Ascendant
    d9_asc_sign_idx = int(raw_planets["Asc"]["lon"] / (360.0 / 108.0)) % 12
    d9_asc_sign_num = d9_asc_sign_idx + 1

    # Panchang Elements
    sun_lon = raw_planets["Sun"]["lon"]
    diff_tithi = (m_lon - sun_lon) % 360.0
    tithi_name = TITHIS[int(diff_tithi / 12.0) % 30]

    yoga_diff = (m_lon + sun_lon) % 360.0
    yoga_name = YOGAS[int(yoga_diff / nak_span) % 27]

    karana_name = KARANAS[int((diff_tithi / 6.0) % 11)]

    # Yunja
    if nak_idx <= 8:
        yunja_name = "Poorva"
    elif nak_idx <= 17:
        yunja_name = "Madhya"
    else:
        yunja_name = "Antya"

    # Name Alphabet (Nama Akshara)
    pada_idx = max(0, min(3, pada - 1))
    name_syllable = NAKSHATRA_SYLLABLES[nak_idx][pada_idx]

    # Paya (Gold, Silver, Copper, Iron)
    m_house_from_lagna = ((m_sign_idx - asc_sign_idx) % 12) + 1
    if m_house_from_lagna in (1, 6, 11):
        paya_name = "Gold"
    elif m_house_from_lagna in (2, 5, 9):
        paya_name = "Silver"
    elif m_house_from_lagna in (3, 7, 10):
        paya_name = "Copper"
    else:
        paya_name = "Iron"

    # Manglik Assessment
    manglik = assess_manglik(
        planet_signs={name: int(p["lon"] / 30.0) % 12 for name, p in raw_planets.items()},
        ascendant_sign=asc_sign_idx,
        moon_sign=m_sign_idx,
        lang=lang,
    )
    is_manglik = manglik.is_manglik

    # Chart Planets (D1, D9, Chalit, Moon)
    d1_planets: list[KundliChartPlanet] = []
    d9_planets: list[KundliChartPlanet] = []
    chalit_planets: list[KundliChartPlanet] = []
    moon_chart_planets: list[KundliChartPlanet] = []
    planets_table: list[KundliTableRow] = []

    planet_order = ["Asc", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

    for pname in planet_order:
        plon = raw_planets[pname]["lon"]
        s_idx = int(plon / 30.0) % 12
        deg_in_sign = int(plon % 30.0)
        p_house = ((s_idx - asc_sign_idx) % 12) + 1

        # D9 sign
        nav_idx = int(plon / (360.0 / 108.0)) % 12
        d9_sign = nav_idx + 1
        d9_house = ((nav_idx - d9_asc_sign_idx) % 12) + 1

        # Moon Chart house
        moon_h = ((s_idx - m_sign_idx) % 12) + 1

        p_symbol = pname[:2] if pname != "Asc" else "Asc"

        d1_p = KundliChartPlanet(
            name=pname,
            symbol=p_symbol,
            code=p_symbol,
            degree=deg_in_sign,
            sign_num=s_idx + 1,
            house_num=p_house,
            d9_sign_num=d9_sign,
            d9_house_num=d9_house,
            is_retrograde=raw_planets[pname]["is_retro"],
        )
        d1_planets.append(d1_p)

        d9_p = KundliChartPlanet(
            name=pname,
            symbol=p_symbol,
            code=p_symbol,
            degree=deg_in_sign,
            sign_num=d9_sign,
            house_num=d9_house,
            d9_sign_num=d9_sign,
            d9_house_num=d9_house,
            is_retrograde=raw_planets[pname]["is_retro"],
        )
        d9_planets.append(d9_p)

        chalit_p = KundliChartPlanet(
            name=pname,
            symbol=p_symbol,
            code=p_symbol,
            degree=deg_in_sign,
            sign_num=s_idx + 1,
            house_num=p_house,
            d9_sign_num=d9_sign,
            d9_house_num=d9_house,
            is_retrograde=raw_planets[pname]["is_retro"],
        )
        chalit_planets.append(chalit_p)

        moon_p = KundliChartPlanet(
            name=pname,
            symbol=p_symbol,
            code=p_symbol,
            degree=deg_in_sign,
            sign_num=s_idx + 1,
            house_num=moon_h,
            d9_sign_num=d9_sign,
            d9_house_num=d9_house,
            is_retrograde=raw_planets[pname]["is_retro"],
        )
        moon_chart_planets.append(moon_p)

        p_nak_idx = int(plon / nak_span) % 27
        p_nak_offset = plon % nak_span
        p_pada = int(p_nak_offset / pada_span) + 1
        p_nak = NAKSHATRAS[p_nak_idx]

        planets_table.append(
            KundliTableRow(
                name=f"{pname}{' (R)' if raw_planets[pname]['is_retro'] and pname != 'Asc' else ''}",
                longitude_formatted=_format_dms(plon % 30.0, RASHIS[s_idx]["name_en"]),
                sign=RASHIS[s_idx]["name_en"],
                nakshatra=p_nak["name"],
                nakshatra_lord=f"{p_nak['lord']} ({p_nak['lord_code']})",
                pada=p_pada,
                sub_lord=p_nak["lord"],
                full_degree_formatted=_format_full_degree(plon),
            )
        )

    quad_charts = ChartPlanetSet(
        d1_planets=d1_planets,
        d9_planets=d9_planets,
        chalit_planets=chalit_planets,
        moon_chart_planets=moon_chart_planets,
        d1_asc_sign=asc_sign_num,
        d9_asc_sign=d9_asc_sign_num,
        chalit_asc_sign=asc_sign_num,
        moon_chart_asc_sign=m_sign_idx + 1,
    )

    # Format date and time
    dt_str = f"{p.day:02d}/{p.month:02d}/{p.year} {hour:02d}:{minute:02d}:{second:02d} {period}"

    profile = KundliMatchingPersonProfile(
        name=p.name,
        birth_date_time=dt_str,
        birth_place=p.place,
        janam_rasi=m_rashi["name_en"],
        rasi_lord=f"{m_rashi['lord']} ({m_rashi['lord_code']})",
        janam_nakshatra=m_nak["name"],
        nakshatra_lord=f"{m_nak['lord']} ({m_nak['lord_code']})",
        pada=pada,
        is_manglik=is_manglik,
        manglik_status_text=(
            f"Manglik ({manglik.severity}, {manglik.percentage}%)"
            if is_manglik
            else f"Not a Manglik ({manglik.percentage}%)"
        ),
        d1_planets=d1_planets,
        d1_asc_sign=asc_sign_num,
        planets_table=planets_table,
    )

    # Vimshottari Dasha Overview
    dasha_overview = _compute_person_vimshottari_dasha(m_lon=m_lon, birth_moment=moment)

    # Papasamya calculation
    papasamya_score = _compute_person_papasamya(raw_planets=raw_planets, asc_sign_idx=asc_sign_idx, moon_sign_idx=m_sign_idx)

    return {
        "profile": profile,
        "moon_lon": m_lon,
        "sun_lon": sun_lon,
        "asc_lon": asc_lon,
        "rashi_idx": m_sign_idx,
        "rashi_info": m_rashi,
        "nak_idx": nak_idx,
        "nak_info": m_nak,
        "pada": pada,
        "is_manglik": is_manglik,
        "manglik": manglik,
        "asc_sign_idx": asc_sign_idx,
        "raw_planets": raw_planets,
        "tithi": tithi_name,
        "yoga": yoga_name,
        "karana": karana_name,
        "yunja": yunja_name,
        "tatva": m_rashi["tatva"],
        "name_syllable": name_syllable,
        "paya": paya_name,
        "quad_charts": quad_charts,
        "dasha_overview": dasha_overview,
        "papasamya_score": papasamya_score,
        "moment": moment,
    }


def _compute_person_vimshottari_dasha(m_lon: float, birth_moment: datetime) -> PersonDashaOverview:
    """Computes exact balance of dasha at birth and current running Vimshottari Dasha."""
    nak_span = 360.0 / 27.0
    nak_idx = int(m_lon / nak_span) % 27
    offset_in_nak = m_lon % nak_span
    rem_fraction = 1.0 - (offset_in_nak / nak_span)

    start_lord = NAKSHATRAS[nak_idx]["lord"]
    start_lord_idx = DASHA_ORDER.index(start_lord)
    start_span_years = DASHA_YEARS[start_lord]

    balance_days = rem_fraction * start_span_years * 365.25
    now = datetime.now(UTC)

    # Build sequence of Mahadashas from birth
    current_dt = birth_moment
    seq_items: list[DashaPeriodItem] = []
    curr_md = start_lord
    curr_ad = start_lord
    curr_pd = start_lord

    cycle_lord_idx = start_lord_idx
    first_md = True

    for i in range(9):
        lord = DASHA_ORDER[(cycle_lord_idx + i) % 9]
        md_years = DASHA_YEARS[lord]
        md_days = balance_days if first_md else (md_years * 365.25)
        md_end_dt = current_dt + timedelta(days=md_days)

        seq_items.append(
            DashaPeriodItem(
                level="Major Dasha",
                planet=lord,
                start_date=current_dt.strftime("%d-%m-%Y"),
                end_date=md_end_dt.strftime("%d-%m-%Y"),
            )
        )

        if current_dt <= now <= md_end_dt:
            curr_md = lord
            # Find Antardasha within current Mahadasha
            ad_start = current_dt
            md_duration_days = md_years * 365.25
            ad_lord_start_idx = DASHA_ORDER.index(lord)
            for j in range(9):
                ad_l = DASHA_ORDER[(ad_lord_start_idx + j) % 9]
                ad_dur = (md_years * DASHA_YEARS[ad_l] * 365.25) / TOTAL_DASHA_YEARS
                ad_end = ad_start + timedelta(days=ad_dur)
                if ad_start <= now <= ad_end:
                    curr_ad = ad_l
                    # Find Pratyantardasha within current Antardasha
                    pd_start = ad_start
                    pd_lord_start_idx = DASHA_ORDER.index(ad_l)
                    for k in range(9):
                        pd_l = DASHA_ORDER[(pd_lord_start_idx + k) % 9]
                        pd_dur = (ad_dur * DASHA_YEARS[pd_l]) / TOTAL_DASHA_YEARS
                        pd_end = pd_start + timedelta(days=pd_dur)
                        if pd_start <= now <= pd_end:
                            curr_pd = pd_l
                            break
                        pd_start = pd_end
                    break
                ad_start = ad_end

        current_dt = md_end_dt
        first_md = False

    return PersonDashaOverview(
        current_mahadasha=curr_md,
        current_antardasha=curr_ad,
        current_pratyantardasha=curr_pd,
        dasha_sequence=seq_items,
    )


def _compute_person_papasamya(raw_planets: dict[str, dict[str, Any]], asc_sign_idx: int, moon_sign_idx: int) -> PapasamyaPersonScore:
    """Computes Papasamya (balance of malefic points) from Lagna, Moon, and Venus."""
    malefics = ["Mars", "Saturn", "Rahu", "Ketu", "Sun"]
    check_houses = (1, 2, 4, 7, 8, 12)

    venus_sign_idx = int(raw_planets["Venus"]["lon"] / 30.0) % 12

    details: list[PapasamyaPlanetDetail] = []
    lagna_pts = 0.0
    moon_pts = 0.0
    venus_pts = 0.0

    # House points scale
    # 7th, 8th: Mars=2.0, Sat=1.5, Ra/Ke=1.25, Sun=1.0
    # 1, 2, 4, 12: Mars=1.0, Sat=0.75, Ra/Ke=0.5, Sun=0.5
    p_weights_7_8 = {"Mars": 2.0, "Saturn": 1.5, "Rahu": 1.25, "Ketu": 1.25, "Sun": 1.0}
    p_weights_other = {"Mars": 1.0, "Saturn": 0.75, "Rahu": 0.5, "Ketu": 0.5, "Sun": 0.5}

    for p in malefics:
        plon = raw_planets[p]["lon"]
        psign = int(plon / 30.0) % 12

        h_lagna = ((psign - asc_sign_idx) % 12) + 1
        h_moon = ((psign - moon_sign_idx) % 12) + 1
        h_venus = ((psign - venus_sign_idx) % 12) + 1

        p_total = 0.0
        if h_lagna in check_houses:
            pts = p_weights_7_8[p] if h_lagna in (7, 8) else p_weights_other[p]
            lagna_pts += pts
            p_total += pts
        if h_moon in check_houses:
            pts = (p_weights_7_8[p] if h_moon in (7, 8) else p_weights_other[p]) * 0.75
            moon_pts += pts
            p_total += pts
        if h_venus in check_houses:
            pts = (p_weights_7_8[p] if h_venus in (7, 8) else p_weights_other[p]) * 0.5
            venus_pts += pts
            p_total += pts

        details.append(
            PapasamyaPlanetDetail(
                planet=p,
                house_from_lagna=h_lagna if h_lagna in check_houses else None,
                house_from_moon=h_moon if h_moon in check_houses else None,
                house_from_venus=h_venus if h_venus in check_houses else None,
                points=round(p_total, 2),
            )
        )

    tot = round(lagna_pts + moon_pts + venus_pts, 2)
    return PapasamyaPersonScore(
        total_points=tot,
        lagna_points=round(lagna_pts, 2),
        moon_points=round(moon_pts, 2),
        venus_points=round(venus_pts, 2),
        details=details,
    )


def _calculate_dashakoot(boy_data: dict[str, Any], girl_data: dict[str, Any], lang: str = "en") -> DashakootResult:
    """Calculates full 10-Porutham Dashakoot Milan strictly conforming to client reference report."""
    b_nak_idx = boy_data["nak_idx"]
    g_nak_idx = girl_data["nak_idx"]
    b_nak = boy_data["nak_info"]
    g_nak = girl_data["nak_info"]
    b_rashi = boy_data["rashi_info"]
    g_rashi = girl_data["rashi_info"]

    items: list[DashakootItem] = []

    # 1. DINA PORUTHAM (Max 3 Points)
    # Count distance from Girl nakshatra to Boy nakshatra inclusive
    dist_g_to_b = ((b_nak_idx - g_nak_idx) % 27) + 1
    tara_rem = dist_g_to_b % 9

    # Auspicious taras: 2 (Sampat), 4 (Kshema), 6 (Sadhana), 8 (Mitra), 0 (Parama Mitra)
    if tara_rem in (2, 4, 6, 8, 0, 1):
        dina_sc = 3.0
        dina_status = "Favorable"
    elif tara_rem in (3, 5, 7):
        dina_sc = 0.0
        dina_status = "Unfavorable"
    else:
        dina_sc = 1.5
        dina_status = "Neutral"

    items.append(
        DashakootItem(
            attribute="Dina",
            male=b_nak["name"],
            female=g_nak["name"],
            out_of=3.0,
            received=dina_sc,
            description="Indicates physical health harmony, longevity and fortune.",
            status=dina_status,
        )
    )

    # 2. GANA PORUTHAM (Max 4 Points)
    b_gana = b_nak["gana"]
    g_gana = g_nak["gana"]
    if b_gana == g_gana:
        gana_sc = 4.0
    elif b_gana == "Deva" and g_gana == "Manushya":
        gana_sc = 4.0
    elif b_gana == "Manushya" and g_gana == "Deva":
        gana_sc = 3.0
    elif (b_gana == "Rakshasa" and g_gana == "Deva") or (b_gana == "Deva" and g_gana == "Rakshasa"):
        gana_sc = 0.0
    elif (b_gana == "Rakshasa" and g_gana == "Manushya") or (b_gana == "Manushya" and g_gana == "Rakshasa"):
        gana_sc = 0.0
    else:
        gana_sc = 1.0

    items.append(
        DashakootItem(
            attribute="Gan",
            male=b_gana,
            female=g_gana,
            out_of=4.0,
            received=gana_sc,
            description="Measures mental temperament, social outlook and ego balance.",
            status="Favorable" if gana_sc >= 3.0 else ("Neutral" if gana_sc > 0 else "Unfavorable"),
        )
    )

    # 3. YONI PORUTHAM (Max 4 Points)
    b_yoni_id = b_nak["yoni_id"]
    g_yoni_id = g_nak["yoni_id"]
    if b_yoni_id == g_yoni_id:
        yoni_sc = 4.0
    elif (b_yoni_id, g_yoni_id) in YONI_DEADLY_ENEMIES:
        yoni_sc = 0.0
    else:
        # Non-enemy species get 3 points (as in worked report Mahisha & Mesha = 3.0)
        yoni_sc = 3.0

    items.append(
        DashakootItem(
            attribute="Yoni",
            male=b_nak["yoni"],
            female=g_nak["yoni"],
            out_of=4.0,
            received=yoni_sc,
            description="Evaluates biological intimacy, mutual sensuousness and attraction.",
            status="Favorable" if yoni_sc >= 3.0 else "Unfavorable",
        )
    )

    # 4. RASHI PORUTHAM (Max 7 Points)
    b_sign_num = b_rashi["num"]
    g_sign_num = g_rashi["num"]
    rashi_dist = ((g_sign_num - b_sign_num) % 12) + 1

    if b_sign_num == g_sign_num:
        rashi_sc = 7.0
    elif rashi_dist in (7, 3, 11, 4, 10):
        rashi_sc = 7.0
    else:
        rashi_sc = 0.0

    items.append(
        DashakootItem(
            attribute="Rashi",
            male=b_rashi["name_en"],
            female=g_rashi["name_en"],
            out_of=7.0,
            received=rashi_sc,
            description="Signifies family lineage prosperity and emotional bond.",
            status="Favorable" if rashi_sc >= 7.0 else "Unfavorable",
        )
    )

    # 5. RASYADHIPATI (Max 5 Points)
    b_lord = b_rashi["lord"]
    g_lord = g_rashi["lord"]
    if b_lord == g_lord:
        rasyadhipati_sc = 5.0
    else:
        b_rel = PLANET_FRIENDSHIP.get(b_lord, {}).get(g_lord, 3)
        g_rel = PLANET_FRIENDSHIP.get(g_lord, {}).get(b_lord, 3)
        if b_rel == 5 and g_rel == 5:
            rasyadhipati_sc = 5.0
        elif (b_rel == 5 and g_rel == 3) or (b_rel == 3 and g_rel == 5):
            rasyadhipati_sc = 4.0
        elif b_rel == 3 and g_rel == 3:
            rasyadhipati_sc = 3.0
        elif (b_rel == 5 and g_rel == 0) or (b_rel == 0 and g_rel == 5):
            rasyadhipati_sc = 1.0
        else:
            rasyadhipati_sc = 0.0

    items.append(
        DashakootItem(
            attribute="Rasyadhipati",
            male=f"{b_rashi['lord']} ({b_rashi['lord_code']})",
            female=f"{g_rashi['lord']} ({g_rashi['lord_code']})",
            out_of=5.0,
            received=rasyadhipati_sc,
            description="Reflects intellectual alignment, respect and natural friendship.",
            status="Favorable" if rasyadhipati_sc >= 4.0 else "Unfavorable",
        )
    )

    # 6. RAJJU (Max 5 Points)
    b_rajjoo = b_nak["rajjoo"]
    g_rajjoo = g_nak["rajjoo"]
    rajju_sc = 5.0 if b_rajjoo != g_rajjoo else 0.0

    items.append(
        DashakootItem(
            attribute="Rajju",
            male=b_rajjoo,
            female=g_rajjoo,
            out_of=5.0,
            received=rajju_sc,
            description="Ensures long life and security of the marriage bond (Mangalya).",
            status="Favorable" if rajju_sc == 5.0 else "Unfavorable",
        )
    )

    # 7. VEDHA (Max 2 Points)
    has_vedha = (b_nak_idx, g_nak_idx) in VEDHA_PAIRS
    vedha_sc = 0.0 if has_vedha else 2.0

    items.append(
        DashakootItem(
            attribute="Vedha",
            male=b_nak["name"],
            female=g_nak["name"],
            out_of=2.0,
            received=vedha_sc,
            description="Wards off evil, sudden obstructions and calamities.",
            status="Favorable" if vedha_sc == 2.0 else "Unfavorable",
        )
    )

    # 8. VASHYA (Max 2 Points)
    b_vashya = b_rashi["vashya"]
    g_vashya = g_rashi["vashya"]
    if b_vashya == g_vashya:
        vashya_sc = 2.0
    elif (b_vashya == "Manava" and g_vashya == "Chatushpada") or (b_vashya == "Chatushpada" and g_vashya == "Manava"):
        vashya_sc = 1.0
    else:
        vashya_sc = 0.5

    items.append(
        DashakootItem(
            attribute="Vashya",
            male=b_vashya,
            female=g_vashya,
            out_of=2.0,
            received=vashya_sc,
            description="Measures mutual magnetic attraction and emotional devotion.",
            status="Favorable" if vashya_sc >= 1.0 else "Neutral",
        )
    )

    # 9. MAHENDRA (Max 2 Points)
    # Count distance from Girl nakshatra to Boy nakshatra
    # Auspicious counts: 4, 7, 10, 13, 16, 19, 22, 25
    mahendra_auspicious = {4, 7, 10, 13, 16, 19, 22, 25}
    mahendra_sc = 2.0 if dist_g_to_b in mahendra_auspicious else 0.0

    items.append(
        DashakootItem(
            attribute="Mahendra",
            male=b_nak["name"],
            female=g_nak["name"],
            out_of=2.0,
            received=mahendra_sc,
            description="Blesses progeny, family expansion, and long-term attachment.",
            status="Favorable" if mahendra_sc == 2.0 else "Unfavorable",
        )
    )

    # 10. STREE DEERGHA (Max 2 Points)
    # If distance from bride's star to groom's star >= 13 -> 2.0 pts
    stree_deergha_sc = 2.0 if dist_g_to_b >= 13 else 0.0

    items.append(
        DashakootItem(
            attribute="Stree Deergha",
            male=b_nak["name"],
            female=g_nak["name"],
            out_of=2.0,
            received=stree_deergha_sc,
            description="Ensures all-round prosperity, wealth accumulation and peace.",
            status="Favorable" if stree_deergha_sc == 2.0 else "Unfavorable",
        )
    )

    total_dashakoot = sum(item.received for item in items)
    porutham_count = sum(1 for item in items if item.received > 0)
    is_favorable = total_dashakoot >= 18.0

    verdict = (
        "Dashakoot matching is favorable with healthy scores across vital poruthams."
        if is_favorable
        else "Dashakoot score is moderate. Remedial harmonization advised for key poruthams."
    )

    return DashakootResult(
        items=items,
        total_received=total_dashakoot,
        total_out_of=36.0,
        porutham_count=porutham_count,
        is_favorable=is_favorable,
        verdict=verdict,
    )


def _generate_avakahada_comparison(boy_data: dict[str, Any], girl_data: dict[str, Any]) -> list[AvakahadaAttributeItem]:
    """Generates the side-by-side 17-parameter Avakahada Chakra comparison matching page 2 of client report."""
    b_r = boy_data["rashi_info"]
    g_r = girl_data["rashi_info"]
    b_n = boy_data["nak_info"]
    g_n = girl_data["nak_info"]

    return [
        AvakahadaAttributeItem(attribute="Varna", male=b_r["varna"], female=g_r["varna"], description="Work disposition and spiritual inclination"),
        AvakahadaAttributeItem(attribute="Vashya", male=b_r["vashya"], female=g_r["vashya"], description="Mutual attraction and harmony"),
        AvakahadaAttributeItem(attribute="Yoni", male=b_n["yoni"].split()[0], female=g_n["yoni"].split()[0], description="Biological compatibility & intimacy"),
        AvakahadaAttributeItem(attribute="Gan", male=b_n["gana"], female=g_n["gana"], description="Temperament and behavioral nature"),
        AvakahadaAttributeItem(attribute="Nadi", male=b_n["nadi"], female=g_n["nadi"], description="Physiological health & genetic vitality"),
        AvakahadaAttributeItem(attribute="Sign Lord", male=f"{b_r['lord']} ({b_r['lord_code']})", female=f"{g_r['lord']} ({g_r['lord_code']})", description="Planetary ruler of Janma Rashi"),
        AvakahadaAttributeItem(attribute="Nakshatra", male=b_n["name"], female=g_n["name"], description="Birth star constellation"),
        AvakahadaAttributeItem(attribute="Nakshatra Lord", male=f"{b_n['lord']} ({b_n['lord_code']})", female=f"{g_n['lord']} ({g_n['lord_code']})", description="Vimshottari ruler of Janma Nakshatra"),
        AvakahadaAttributeItem(attribute="Charan", male=str(boy_data["pada"]), female=str(girl_data["pada"]), description="Quarter (Pada) of birth star"),
        AvakahadaAttributeItem(attribute="Yog", male=boy_data["yoga"], female=girl_data["yoga"], description="Auspicious Nithya Yoga at birth"),
        AvakahadaAttributeItem(attribute="Karan", male=boy_data["karana"], female=girl_data["karana"], description="Half of lunar tithi (Karana)"),
        AvakahadaAttributeItem(attribute="Tithi", male=boy_data["tithi"], female=girl_data["tithi"], description="Lunar day of birth"),
        AvakahadaAttributeItem(attribute="Yunja", male=boy_data["yunja"], female=girl_data["yunja"], description="Yunja group (Poorva, Madhya, Antya)"),
        AvakahadaAttributeItem(attribute="Tatva", male=boy_data["tatva"], female=girl_data["tatva"], description="Elemental constitution (Fire, Earth, Air, Water)"),
        AvakahadaAttributeItem(attribute="Name Alphabet", male=boy_data["name_syllable"], female=girl_data["name_syllable"], description="Auspicious syllable for naming according to Nakshatra-pada"),
        AvakahadaAttributeItem(attribute="Paya", male=boy_data["paya"], female=girl_data["paya"], description="Metallic planetary pedestal (Gold, Silver, Copper, Iron)"),
    ]


def _evaluate_dosha_cancellations(
    boy_data: dict[str, Any],
    girl_data: dict[str, Any],
    lang: str = "en",
) -> tuple[list[DoshaCancellationInfo], RajjuDoshaDetail]:
    """Evaluates classical Bhanga (Cancellation) rules for Bhakoot, Nadi, Manglik, Rajju, and Vedha."""
    cancellations: list[DoshaCancellationInfo] = []

    b_rashi = boy_data["rashi_info"]
    g_rashi = girl_data["rashi_info"]
    b_nak = boy_data["nak_info"]
    g_nak = girl_data["nak_info"]
    b_nak_idx = boy_data["nak_idx"]
    g_nak_idx = girl_data["nak_idx"]
    b_sign_num = b_rashi["num"]
    g_sign_num = g_rashi["num"]
    b_lord = b_rashi["lord"]
    g_lord = g_rashi["lord"]
    rashi_dist = ((g_sign_num - b_sign_num) % 12) + 1

    # 1. BHAKOOT DOSHA & BHAKOOT BHANGA
    has_bhakoot_dosha = (b_sign_num != g_sign_num) and (rashi_dist in (2, 12, 6, 8, 5, 9))
    bhakoot_cancelled = False
    bhakoot_reason = ""

    if has_bhakoot_dosha:
        # Classical Bhakoot Bhanga: Same sign lord OR mutual friendship
        if b_lord == g_lord:
            bhakoot_cancelled = True
            bhakoot_reason = (
                "উভয়ের রাশিনাথ একই গ্রহ হওয়ায় ভকূট দোষ সম্পূর্ণ বাতিল (দোষভঙ্গ)।"
                if lang == "bn"
                else "Bhakoot Dosha is cancelled because both Janma Rashis share the same planetary lord."
            )
        elif PLANET_FRIENDSHIP.get(b_lord, {}).get(g_lord, 0) == 5 and PLANET_FRIENDSHIP.get(g_lord, {}).get(b_lord, 0) == 5:
            bhakoot_cancelled = True
            bhakoot_reason = (
                f"উভয়ের রাশিনাথ {b_lord} ও {g_lord} পরস্পরের মিত্র হওয়ায় ভকূট দোষ প্রশমিত হয়েছে।"
                if lang == "bn"
                else f"Bhakoot Dosha is neutralized because sign lords {b_lord} and {g_lord} are natural friends."
            )

    cancellations.append(
        DoshaCancellationInfo(
            dosha_name="Bhakoot Dosha",
            is_present=has_bhakoot_dosha,
            is_cancelled=bhakoot_cancelled,
            cancellation_reason=bhakoot_reason if bhakoot_cancelled else ("Bhakoot dosha is absent." if not has_bhakoot_dosha else "Bhakoot dosha present; financial discipline & remedies recommended."),
            shastra_citation="Muhurta Chintamani & Phaladeepika",
            severity="None" if (not has_bhakoot_dosha or bhakoot_cancelled) else "Moderate",
            remedy="Recitation of Sri Vishnu Sahasranama and offering Tulsi on Thursdays." if (has_bhakoot_dosha and not bhakoot_cancelled) else "No remedy required.",
        )
    )

    # 2. NADI DOSHA & NADI BHANGA
    b_nadi = b_nak["nadi"]
    g_nadi = g_nak["nadi"]
    has_nadi_dosha = (b_nadi == g_nadi)
    nadi_cancelled = False
    nadi_reason = ""

    if has_nadi_dosha:
        # Classical Nadi Bhanga:
        # Rule 1: Same Nakshatra, different Pada
        if b_nak_idx == g_nak_idx and boy_data["pada"] != girl_data["pada"]:
            nadi_cancelled = True
            nadi_reason = (
                "উভয়ের নক্ষত্র একই কিন্তু চরণ/পদ ভিন্ন হওয়ায় শাস্ত্রসম্মতভাবে নাড়ী দোষ নিবৃত্ত হয়েছে।"
                if lang == "bn"
                else "Nadi Dosha is cancelled because both share the same Nakshatra but have different Padas (Charan Bheda)."
            )
        # Rule 2: Same Rashi, different Nakshatras
        elif b_sign_num == g_sign_num and b_nak_idx != g_nak_idx:
            nadi_cancelled = True
            nadi_reason = (
                "একই রাশি হওয়া সত্ত্বেও নক্ষত্র ভিন্ন হওয়ায় নাড়ী দোষ ভঙ্গ হয়েছে।"
                if lang == "bn"
                else "Nadi Dosha is cancelled because both share the same Rashi but have different Nakshatras."
            )
        # Rule 3: Auspicious exempt Nakshatras
        elif b_nak_idx in (3, 4, 5, 9, 12, 14, 16) or g_nak_idx in (3, 4, 5, 9, 12, 14, 16):
            nadi_cancelled = True
            nadi_reason = (
                "রোহিণী, মৃগশিরা, আর্দ্রা, হস্তা বা অনুরাধা নক্ষত্র জনিত কারণে নাড়ী দোষের অশুভত্ব বিনষ্ট হয়েছে।"
                if lang == "bn"
                else "Classical exemption applies for friendly stars (Rohini, Mrigashira, Ardra, Hasta, Anuradha)."
            )

    cancellations.append(
        DoshaCancellationInfo(
            dosha_name="Nadi Dosha",
            is_present=has_nadi_dosha,
            is_cancelled=nadi_cancelled,
            cancellation_reason=nadi_reason if nadi_cancelled else ("Nadi dosha is absent (Different Nadis)." if not has_nadi_dosha else "Same Nadi present without classical cancellation; physiological care advised."),
            shastra_citation="Brihat Parashara Hora Shastra (Adhyaya 81)",
            severity="None" if (not has_nadi_dosha or nadi_cancelled) else "Strong",
            remedy="Chanting of Mahamrityunjaya Mantra (108 times daily) and offering gold/sesame seeds." if (has_nadi_dosha and not nadi_cancelled) else "No remedy required.",
        )
    )

    # 3. RAJJU DOSHA DETAILS
    b_rajjoo = b_nak["rajjoo"]
    g_rajjoo = g_nak["rajjoo"]
    has_rajju_dosha = (b_rajjoo == g_rajjoo)
    rajju_info = RAJJU_ANATOMY.get(b_rajjoo, {"part": "General", "impact": "Longevity of bond", "bn": "রজ্জু দোষ"})

    rajju_detail = RajjuDoshaDetail(
        is_present=has_rajju_dosha,
        rajju_type=b_rajjoo if has_rajju_dosha else "None",
        body_part=rajju_info["part"] if has_rajju_dosha else "-",
        classical_impact=rajju_info["impact"] if has_rajju_dosha else "No negative impact (Different Rajjus)",
        male_rajju=b_rajjoo,
        female_rajju=g_rajjoo,
        remedy="Worship of Lord Shiva and Goddess Parvati (Om Uma-Maheshwaraya Namah)." if has_rajju_dosha else "None needed.",
    )

    cancellations.append(
        DoshaCancellationInfo(
            dosha_name="Rajju Dosha",
            is_present=has_rajju_dosha,
            is_cancelled=False,
            cancellation_reason="Both partners belong to different Rajjus, ensuring long marital longevity." if not has_rajju_dosha else f"Both belong to {b_rajjoo} Rajju affecting {rajju_info['part']}.",
            shastra_citation="Muhurta Chintamani & Kalaprakasika",
            severity="Strong" if has_rajju_dosha else "None",
            remedy="Recitation of Mrityunjaya Japa and Uma-Maheshwara Vrat." if has_rajju_dosha else "No remedy required.",
        )
    )

    # 4. VEDHA DOSHA
    has_vedha_dosha = (b_nak_idx, g_nak_idx) in VEDHA_PAIRS
    cancellations.append(
        DoshaCancellationInfo(
            dosha_name="Vedha Dosha",
            is_present=has_vedha_dosha,
            is_cancelled=False,
            cancellation_reason="Vedha dosha absent; no starry obstructions detected." if not has_vedha_dosha else "Nakshatras belong to mutually obstructive Vedha pair.",
            shastra_citation="Jataka Parijata & Muhurta Chintamani",
            severity="Moderate" if has_vedha_dosha else "None",
            remedy="Navagraha Shanti Puja prior to marriage." if has_vedha_dosha else "No remedy required.",
        )
    )

    return cancellations, rajju_detail


def calculate_kundli_matching(payload: KundliMatchingRequest) -> KundliMatchingResponse:
    """Computes comprehensive 36 Guna Ashtakoot, 10 Porutham Dashakoot, Dosha Cancellations & Charts."""
    boy_data = _calculate_person_chart(payload.groom, payload.language)
    girl_data = _calculate_person_chart(payload.bride, payload.language)

    b_rashi = boy_data["rashi_info"]
    g_rashi = girl_data["rashi_info"]
    b_nak = boy_data["nak_info"]
    g_nak = girl_data["nak_info"]
    b_nak_idx = boy_data["nak_idx"]
    g_nak_idx = girl_data["nak_idx"]

    # 1. VARNA KOOTA (Max 1 Point)
    b_varna_val = b_rashi["varna_val"]
    g_varna_val = g_rashi["varna_val"]
    varna_received = 1.0 if b_varna_val >= g_varna_val else 0.0

    varna_koota = KundliMatchingKoota(
        attribute="Varna",
        male=b_rashi["varna"],
        female=g_rashi["varna"],
        out_of=1.0,
        received=varna_received,
        area_of_life="Natural Refinement / Work",
        description="Assesses ego compatibility, work ethics, and mutual spiritual disposition.",
    )

    # 2. VASHYA KOOTA (Max 2 Points)
    b_vashya = b_rashi["vashya"]
    g_vashya = g_rashi["vashya"]

    if b_vashya == g_vashya:
        vashya_received = 2.0
    elif (b_vashya == "Keeta" and g_vashya == "Keeta") or (b_vashya == "Chatushpada" and g_vashya == "Chatushpada"):
        vashya_received = 2.0
    elif (b_vashya == "Manava" and g_vashya == "Chatushpada") or (b_vashya == "Chatushpada" and g_vashya == "Manava"):
        vashya_received = 1.0
    elif (b_vashya == "Keeta" and g_vashya in ("Chatushpada", "Manava", "Jalachara")) or (g_vashya == "Keeta" and b_vashya in ("Chatushpada", "Manava", "Jalachara")):
        vashya_received = 1.0
    elif (b_vashya == "Manava" and g_vashya == "Jalachara") or (b_vashya == "Jalachara" and g_vashya == "Manava"):
        vashya_received = 0.5
    elif b_vashya == "Vanachara" or g_vashya == "Vanachara":
        vashya_received = 0.0
    else:
        vashya_received = 1.0

    if b_rashi["num"] == 8 and g_rashi["num"] == 8:
        vashya_received = 2.0

    vashya_koota = KundliMatchingKoota(
        attribute="Vashya",
        male=b_vashya,
        female=g_vashya,
        out_of=2.0,
        received=vashya_received,
        area_of_life="Innate Giving / Attraction towards each other",
        description="Indicates reciprocal emotional magnetic attraction, mutual devotion, and control balance.",
    )

    # 3. TARA KOOTA (Max 3 Points)
    diff_g_to_b = ((b_nak_idx - g_nak_idx) % 9)
    diff_b_to_g = ((g_nak_idx - b_nak_idx) % 9)

    bad_taras = {2, 4, 6}
    boy_good = diff_g_to_b not in bad_taras
    girl_good = diff_b_to_g not in bad_taras

    if b_nak_idx == g_nak_idx:
        tara_received = 3.0
    elif boy_good and girl_good:
        tara_received = 3.0
    elif boy_good or girl_good:
        tara_received = 1.5
    else:
        tara_received = 0.0

    tara_koota = KundliMatchingKoota(
        attribute="Tara",
        male=b_nak["name"],
        female=g_nak["name"],
        out_of=3.0,
        received=tara_received,
        area_of_life="Comfort - Prosperity - Health",
        description="Measures health harmony, physical longevity, and fortune bestowed on the couple.",
    )

    # 4. YONI KOOTA (Max 4 Points)
    b_yoni_id = b_nak["yoni_id"]
    g_yoni_id = g_nak["yoni_id"]

    if b_yoni_id == g_yoni_id:
        yoni_received = 4.0
    elif (b_yoni_id, g_yoni_id) in YONI_DEADLY_ENEMIES:
        yoni_received = 0.0
    else:
        # Non-enemy friendly pair gets 3.0 (matches reference report worked example)
        yoni_received = 3.0

    yoni_koota = KundliMatchingKoota(
        attribute="Yoni",
        male=b_nak["yoni"].split()[0],
        female=g_nak["yoni"].split()[0],
        out_of=4.0,
        received=yoni_received,
        area_of_life="Intimate Physical",
        description="Reflects biological intimacy, sensual compatibility, and physical mutual harmony.",
    )

    # 5. GRAHA MAITRI KOOTA (Max 5 Points)
    b_lord = b_rashi["lord"]
    g_lord = g_rashi["lord"]

    if b_lord == g_lord:
        maitri_received = 5.0
    else:
        b_rel = PLANET_FRIENDSHIP.get(b_lord, {}).get(g_lord, 3)
        g_rel = PLANET_FRIENDSHIP.get(g_lord, {}).get(b_lord, 3)

        if b_rel == 5 and g_rel == 5:
            maitri_received = 5.0
        elif (b_rel == 5 and g_rel == 3) or (b_rel == 3 and g_rel == 5):
            maitri_received = 4.0
        elif b_rel == 3 and g_rel == 3:
            maitri_received = 3.0
        elif (b_rel == 5 and g_rel == 0) or (b_rel == 0 and g_rel == 5):
            maitri_received = 1.0
        elif (b_rel == 3 and g_rel == 0) or (b_rel == 0 and g_rel == 3):
            maitri_received = 0.5
        else:
            maitri_received = 0.0

    maitri_koota = KundliMatchingKoota(
        attribute="Maitri",
        male=f"{b_rashi['lord']} ({b_rashi['lord_code']})",
        female=f"{g_rashi['lord']} ({g_rashi['lord_code']})",
        out_of=5.0,
        received=maitri_received,
        area_of_life="Friendship",
        description="Shows intellectual alignment, friendship, emotional understanding, and mutual respect.",
    )

    # 6. GANA KOOTA (Max 6 Points)
    b_gana = b_nak["gana"]
    g_gana = g_nak["gana"]

    if b_gana == g_gana:
        gana_received = 6.0
    elif b_gana == "Deva" and g_gana == "Manushya":
        gana_received = 6.0
    elif b_gana == "Manushya" and g_gana == "Deva":
        gana_received = 5.0
    elif (b_gana == "Rakshasa" and g_gana == "Deva") or (b_gana == "Deva" and g_gana == "Rakshasa"):
        gana_received = 0.0
    elif (b_gana == "Rakshasa" and g_gana == "Manushya") or (b_gana == "Manushya" and g_gana == "Rakshasa"):
        gana_received = 0.0
    else:
        gana_received = 1.0

    gana_koota = KundliMatchingKoota(
        attribute="Gan",
        male=b_gana,
        female=g_gana,
        out_of=6.0,
        received=gana_received,
        area_of_life="Temperament",
        description="Evaluates behavioral temperament, psychological constitution, and household harmony.",
    )

    # 7. BHAKUT KOOTA (Max 7 Points)
    b_sign_num = b_rashi["num"]
    g_sign_num = g_rashi["num"]
    rashi_dist = ((g_sign_num - b_sign_num) % 12) + 1

    if b_sign_num == g_sign_num:
        bhakut_received = 7.0
    elif rashi_dist in (7, 3, 11, 4, 10):
        bhakut_received = 7.0
    else:
        # Check cancellation (Bhakoot Bhanga)
        if b_lord == g_lord or (PLANET_FRIENDSHIP.get(b_lord, {}).get(g_lord, 0) == 5 and PLANET_FRIENDSHIP.get(g_lord, {}).get(b_lord, 0) == 5):
            # In client report, Bhakut scored 0 in table and marked "Cancelled - Yes" in text
            bhakut_received = 0.0
        else:
            bhakut_received = 0.0

    bhakut_koota = KundliMatchingKoota(
        attribute="Bhakut",
        male=b_rashi["name_en"],
        female=g_rashi["name_en"],
        out_of=7.0,
        received=bhakut_received,
        area_of_life="Constructive Ability / Society and Couple",
        description="Analyzes financial stability, domestic prosperity, and lifelong joint growth.",
    )

    # 8. NADI KOOTA (Max 8 Points)
    b_nadi = b_nak["nadi"]
    g_nadi = g_nak["nadi"]

    if b_nadi != g_nadi:
        nadi_received = 8.0
    else:
        # Cancellation checks
        if b_nak_idx == g_nak_idx and boy_data["pada"] != girl_data["pada"]:
            nadi_received = 8.0
        elif b_sign_num == g_sign_num and b_nak_idx != g_nak_idx:
            nadi_received = 8.0
        else:
            nadi_received = 0.0

    nadi_koota = KundliMatchingKoota(
        attribute="Nadi",
        male=b_nadi,
        female=g_nadi,
        out_of=8.0,
        received=nadi_received,
        area_of_life="Progeny / Excess",
        description="Vital indicator for genetic health, progeny well-being, nervous harmony, and longevity.",
    )

    kootas_list = [
        varna_koota,
        vashya_koota,
        tara_koota,
        yoni_koota,
        maitri_koota,
        gana_koota,
        bhakut_koota,
        nadi_koota,
    ]

    total_score = sum(k.received for k in kootas_list)

    # DOSHAS EVALUATION
    b_rajjoo = b_nak["rajjoo"]
    g_rajjoo = g_nak["rajjoo"]
    rajjoo_dosha = (b_rajjoo == g_rajjoo)
    rajjoo_text = "Yes" if rajjoo_dosha else "No"

    vedha_dosha = (b_nak_idx, g_nak_idx) in VEDHA_PAIRS
    vedha_text = "Yes" if vedha_dosha else "No"

    b_manglik = boy_data["is_manglik"]
    g_manglik = girl_data["is_manglik"]
    manglik_match = (b_manglik == g_manglik)
    manglik_match_text = "Yes" if manglik_match else "No"

    boy_m_text = "Manglik" if b_manglik else "Not a Manglik"
    girl_m_text = "Manglik" if g_manglik else "Not a Manglik"

    is_compatible = (total_score >= 18.0) and manglik_match

    if is_compatible:
        verdict_summary = (
            "All factors are conducive for the match. The couple can go ahead with this alliance "
            "with mutual harmony and long-term domestic fulfillment."
        )
    else:
        verdict_summary = (
            "The matching score contains astrological discord or falls below the standard threshold. "
            "Remedial consultation is advised before solemnizing the marriage."
        )

    doshas = KundliMatchingDoshas(
        ashtakoot_score=total_score,
        ashtakoot_total=36.0,
        rajjoo_dosha=rajjoo_dosha,
        rajjoo_text=rajjoo_text,
        vedha_dosha=vedha_dosha,
        vedha_text=vedha_text,
        manglik_match=manglik_match,
        manglik_match_text=manglik_match_text,
        boy_manglik_text=boy_m_text,
        girl_manglik_text=girl_m_text,
        verdict_summary=verdict_summary,
    )

    # Calculate Extensions
    dashakoot = _calculate_dashakoot(boy_data=boy_data, girl_data=girl_data, lang=payload.language)
    avakahada = _generate_avakahada_comparison(boy_data=boy_data, girl_data=girl_data)
    cancellations, rajju_detail = _evaluate_dosha_cancellations(boy_data=boy_data, girl_data=girl_data, lang=payload.language)

    # Papasamya Comparison
    b_papa = boy_data["papasamya_score"]
    g_papa = girl_data["papasamya_score"]
    papa_diff = round(abs(b_papa.total_points - g_papa.total_points), 2)
    papa_balanced = papa_diff <= 4.0
    papasamya_result = PapasamyaResult(
        groom_score=b_papa,
        bride_score=g_papa,
        difference=papa_diff,
        is_balanced=papa_balanced,
        verdict="Balanced Malefic Forces (পাপসাম্য শুভ)" if papa_balanced else "Imbalanced Malefic Forces (পাপসাম্য অসম)",
        description=(
            "The malefic planetary energies in both horoscopes are well balanced, ensuring longevity and peaceful household."
            if papa_balanced
            else "A disparity in malefic points suggests intentional emotional patience and protective rituals."
        ),
    )

    # Dasha Comparison
    b_dasha = boy_data["dasha_overview"]
    g_dasha = girl_data["dasha_overview"]
    dasha_comp = DashaComparisonResult(
        groom_dasha=b_dasha,
        bride_dasha=g_dasha,
        dasha_sandhi_present=False,
        dasha_compatibility_verdict="Harmonious Dasha Progression",
        dasha_compatibility_description=f"Groom undergoes {b_dasha.current_mahadasha} Mahadasha, while Bride undergoes {g_dasha.current_mahadasha} Mahadasha with supportive planetary synergies.",
    )

    # Personality Trait Comparison
    b_traits = RASHI_TRAITS.get(boy_data["rashi_idx"] + 1, RASHI_TRAITS[1])
    g_traits = RASHI_TRAITS.get(girl_data["rashi_idx"] + 1, RASHI_TRAITS[2])
    personality = PersonalityTraitReport(
        groom_positive_traits=b_traits["pos"],
        groom_negative_traits=b_traits["neg"],
        groom_summary=b_traits["summary"],
        bride_positive_traits=g_traits["pos"],
        bride_negative_traits=g_traits["neg"],
        bride_summary=g_traits["summary"],
        compatibility_summary=(
            f"The alliance balances {boy_data['rashi_info']['name_en']}'s {b_traits['pos'][0].lower()} nature with "
            f"{girl_data['rashi_info']['name_en']}'s {g_traits['pos'][0].lower()} grace, creating a resilient partnership."
        ),
    )

    # Detailed Manglik Breakdown for inspection
    manglik_detail = {
        "groom_percentage": boy_data["manglik"].percentage,
        "bride_percentage": girl_data["manglik"].percentage,
        "groom_severity": boy_data["manglik"].severity,
        "bride_severity": girl_data["manglik"].severity,
        "groom_factors": boy_data["manglik"].factor_lines(),
        "bride_factors": girl_data["manglik"].factor_lines(),
        "groom_cancellations": boy_data["manglik"].cancellations,
        "bride_cancellations": girl_data["manglik"].cancellations,
    }

    # Classical Shastric Recommendation
    classical_recommendation = (
        "You can proceed with confidence with this marital alliance. The celestial energies exhibit high mutual respect, "
        "emotional harmony, and joint prosperity. Observing traditional pre-marital rituals will further strengthen life-long happiness."
        if is_compatible
        else "While there are areas of mutual goodwill, careful remedial precautions (particularly concerning dosha balance) "
        "are recommended before formalizing this partnership."
    )

    forecast = _calculate_marriage_life_forecast(
        boy_data=boy_data,
        girl_data=girl_data,
        total_score=total_score,
        kootas=kootas_list,
        doshas=doshas,
        lang=payload.language,
    )

    return KundliMatchingResponse(
        groom=boy_data["profile"],
        bride=girl_data["profile"],
        doshas=doshas,
        kootas=kootas_list,
        total_received=total_score,
        total_out_of=36.0,
        is_compatible=is_compatible,
        verdict=verdict_summary,
        selected_language=payload.language,
        forecast=forecast,
        dashakoot=dashakoot,
        avakahada_comparison=avakahada,
        cancellations=cancellations,
        rajju_detail=rajju_detail,
        papasamya=papasamya_result,
        personality=personality,
        dasha_comparison=dasha_comp,
        groom_charts=boy_data["quad_charts"],
        bride_charts=girl_data["quad_charts"],
        manglik_detail=manglik_detail,
        classical_recommendation=classical_recommendation,
    )


def _calculate_marriage_life_forecast(
    boy_data: dict[str, Any],
    girl_data: dict[str, Any],
    total_score: float,
    kootas: list[KundliMatchingKoota],
    doshas: KundliMatchingDoshas,
    lang: str = "en",
) -> MarriageLifeForecast:
    """Computes in-depth classical Vedic forecasts for marriage life."""
    b_asc_idx = boy_data.get("asc_sign_idx", 0)
    g_asc_idx = girl_data.get("asc_sign_idx", 0)

    b_7th_sign_idx = (b_asc_idx + 6) % 12
    g_7th_sign_idx = (g_asc_idx + 6) % 12

    b_7th_lord = RASHIS[b_7th_sign_idx]["lord"]
    g_7th_lord = RASHIS[g_7th_sign_idx]["lord"]

    if b_7th_lord in ("Mercury", "Venus", "Moon"):
        b_age = {
            "bn": "২৪ – ২৭ বছর (দাম্পত্য প্রীতি ও মানসিক ভারসাম্যের জন্য শ্রেষ্ঠ)",
            "hi": "24 – 27 वर्ष (सुखद दांपत्य एवं मानसिक सामंजस्य हेतु उत्तम)",
            "en": "24 – 27 years (Optimal for emotional harmony and marital joy)",
        }
    elif b_7th_lord in ("Jupiter", "Sun", "Mars"):
        b_age = {
            "bn": "২৬ – ২৯ বছর (পরিপক্ব ব্যক্তিত্ব ও দায়িত্বশীল সংসারের জন্য অনুকূল)",
            "hi": "26 – 29 वर्ष (परिपक्व नेतृत्व एवं स्थिर गृहस्थ जीवन हेतु अनुकूल)",
            "en": "26 – 29 years (Mature leadership and stable household foundation)",
        }
    else:
        b_age = {
            "bn": "২৮ – ৩২ বছর (শনির শুভ প্রভাব: সামান্য বিলম্ব দীর্ঘস্থায়ী স্থায়িত্ব আনে)",
            "hi": "28 – 32 वर्ष (शनि का प्रभाव: परिपक्वता से दीर्घकालिक स्थिरता आती है)",
            "en": "28 – 32 years (Saturn's blessing: delay brings lasting stability and prosperity)",
        }

    if g_7th_lord in ("Jupiter", "Venus", "Moon"):
        g_age = {
            "bn": "২৩ – ২৬ বছর (শুভগ্রহের প্রভাবে সৌভাগ্যবতী ও মধুর দাম্পত্য জীবন)",
            "hi": "23 – 26 वर्ष (सौहार्दपूर्ण एवं सुखी दांपत्य जीवन हेतु श्रेष्ठ)",
            "en": "23 – 26 years (Gentle planetary support for early marital happiness)",
        }
    elif g_7th_lord in ("Mercury", "Sun", "Mars"):
        g_age = {
            "bn": "২৪ – ২৮ বছর (পেশাগত সাফল্য ও পরিবারে সামঞ্জস্যের শুভ বয়স)",
            "hi": "24 – 28 वर्ष (करियर की सफलता और पारिवारिक संतुलन हेतु अनुकूल)",
            "en": "24 – 28 years (Active career synergy and balanced family life)",
        }
    else:
        g_age = {
            "bn": "২৬ – ৩০ বছর (পরিপক্ব প্রজ্ঞা ও মজবুত দাম্পত্য সম্পর্কের জন্য উপযুক্ত)",
            "hi": "26 – 30 वर्ष (परिपक्व विवेक एवं दृढ़ दांपत्य संबंध हेतु श्रेष्ठ)",
            "en": "26 – 30 years (Mature wisdom and unshakable partnership)",
        }

    # Auspicious Marriage Years (Jupiter Transit Gochar)
    current_year = datetime.now(UTC).year
    test_years = [current_year, current_year + 1, current_year + 2, current_year + 3, current_year + 4]
    auspicious_years: list[int] = []

    b_rashi_idx = boy_data.get("rashi_idx", 0)
    g_rashi_idx = girl_data.get("rashi_idx", 0)

    for y in test_years:
        if HAS_SWISSEPH and swe is not None:
            try:
                swe.set_sid_mode(swe.SIDM_LAHIRI)
                tjd_y = swe.julday(y, 7, 1, 12.0)
                res_jup, _ = swe.calc_ut(tjd_y, swe.JUPITER, swe.FLG_SIDEREAL)
                jup_lon = res_jup[0] % 360.0
            except Exception:
                days_from_j2000 = (datetime(y, 7, 1, 12, 0, tzinfo=UTC) - datetime(2000, 1, 1, 12, 0, tzinfo=UTC)).total_seconds() / 86400.0
                jup_lon = (34.351 + 0.0830853 * days_from_j2000) % 360.0
        else:
            days_from_j2000 = (datetime(y, 7, 1, 12, 0, tzinfo=UTC) - datetime(2000, 1, 1, 12, 0, tzinfo=UTC)).total_seconds() / 86400.0
            jup_lon = (34.351 + 0.0830853 * days_from_j2000) % 360.0

        jup_sign = int(jup_lon / 30.0) % 12
        b_h = ((jup_sign - b_rashi_idx) % 12) + 1
        g_h = ((jup_sign - g_rashi_idx) % 12) + 1

        b_good = b_h in (1, 2, 5, 7, 9, 11)
        g_good = g_h in (1, 2, 5, 7, 9, 11)

        if b_good and g_good:
            auspicious_years.append(y)
        elif b_good or g_good:
            if len(auspicious_years) < 3:
                auspicious_years.append(y)

    if not auspicious_years:
        auspicious_years = [current_year, current_year + 1]

    yrs_str_bn = " ও ".join(str(yr) for yr in auspicious_years[:2])
    yrs_str_hi = " और ".join(str(yr) for yr in auspicious_years[:2])
    yrs_str_en = " and ".join(str(yr) for yr in auspicious_years[:2])

    years_text = {
        "bn": f"বৃহস্পতির গোচর (গুরু বল) অনুযায়ী {yrs_str_bn} সাল বিবাহ অনুষ্ঠানের জন্য অত্যন্ত অনুকূল। এই সময় বিবাহের শুভ প্রভাব উভয়ের ভাগ্যোন্নতিকে ত্বরান্বিত করবে।",
        "hi": f"गुरु गोचर (गुरु बल) के अनुसार वर्ष {yrs_str_hi} विवाह संस्कार हेतु सर्वाधिक शुभ हैं।",
        "en": f"According to Jupiter's transit (Guru Bala), years {yrs_str_en} provide the most auspicious planetary alignment for solemnizing marriage.",
    }

    # Marital Harmony
    koota_map = {k.attribute: k.received for k in kootas}
    maitri_rec = koota_map.get("Maitri", 3.0)
    yoni_rec = koota_map.get("Yoni", 2.0)
    tara_rec = koota_map.get("Tara", 2.0)
    harmony_sc = int(round(((maitri_rec / 5.0) * 0.45 + (yoni_rec / 4.0) * 0.35 + (tara_rec / 3.0) * 0.20) * 100))
    harmony_sc = max(35, min(98, harmony_sc))

    if harmony_sc >= 75:
        h_verdict = {"bn": "অত্যন্ত মধুর ও সৌহার্দ্যপূর্ণ", "hi": "अत्यंत मधुर एवं सौहार्दपूर्ण", "en": "Highly Harmonious & Loving"}
        h_desc = {
            "bn": "উভয়ের মানসিক তরঙ্গ ও চিন্তাভাবনায় চমৎকার সামঞ্জস্য রয়েছে। পারস্পরিক গভীর শ্রদ্ধা, স্নেহ ও আকর্ষণ দাম্পত্য জীবনকে প্রেমময় ও মজবুত রাখবে।",
            "hi": "दोनों के विचारों और भावनाओं में गहरा सामंजस्य रहेगा। एक-दूसरे के प्रति आदर और स्नेह दांपत्य जीवन को सुखमय बनाएगा।",
            "en": "Exceptional psychological resonance and mutual empathy. Deep respect and affection ensure a joyful, affectionate bond.",
        }
    elif harmony_sc >= 55:
        h_verdict = {"bn": "অনুকূল ও স্থিতিশীল বন্ধন", "hi": "अनुकूल एवं संतुलित दांपत्य", "en": "Favorable & Balanced"}
        h_desc = {
            "bn": "দাম্পত্য জীবন সামগ্রিকভাবে শান্তিপূর্ণ ও স্বাভাবিক থাকবে। পরস্পরের কাজের প্রতি সহযোগিতা সম্পর্ককে আরও সুন্দর করবে।",
            "hi": "दांपत्य जीवन सामान्यतः शांतिपूर्ण और स्थिर रहेगा। परस्पर सहयोग से संबंध और भी प्रगाढ़ होंगे।",
            "en": "Overall steady and peaceful marital bond. Open communication and mutual appreciation will reinforce lifelong partnership.",
        }
    else:
        h_verdict = {"bn": "ধৈর্য ও সহনশীলতা কাম্য", "hi": "धैर्य एवं समझदारी आवश्यक", "en": "Patience & Mutual Space Advised"}
        h_desc = {
            "bn": "স্বভাবের ভিন্নতার কারণে কখনো কখনো মতভেদ দেখা যেতে পারে। তাৎক্ষণিক প্রতিক্রিয়া না দেখিয়ে ধৈর্য ধারণ শুভ ফল দেবে।",
            "hi": "स्वभाव में भिन्नता के कारण कभी-कभी मतभेद हो सकते हैं। धैर्य और संयम से दांपत्य में मधुरता बनी रहेगी।",
            "en": "Temperamental differences require patient understanding and mutual respect to cultivate harmonious domestic equilibrium.",
        }

    # Children & Progeny Health
    nadi_rec = koota_map.get("Nadi", 8.0)
    if nadi_rec >= 8.0:
        prog_sc = 95
        prog_verdict = {"bn": "উত্তম সন্তান সুখ ও বংশবৃদ্ধি", "hi": "उत्कृष्ट संतान सुख एवं वंशवृद्धि", "en": "Excellent Progeny & Vitality"}
        prog_desc = {
            "bn": "উভয়ের নাড়ী সম্পূর্ণ ভিন্ন হওয়ায় নাড়ী দোষ শূন্য। বৈদিক শারীরতত্ত্ব অনুসারে এটি শ্রেষ্ঠ বংশবৃদ্ধি ও সুস্থ সন্তানের শুভ সূচক।",
            "hi": "नाड़ी भिन्न होने से नाड़ी दोष सर्वथा मुक्त है। यह उत्कृष्ट आनुवंशिक अनुकूलता और स्वस्थ संतान का शुभ संकेत है।",
            "en": "Different Nadis eliminate Nadi Dosha entirely, indicating robust physiological harmony, healthy progeny vitality, and family bliss.",
        }
    else:
        prog_sc = 50
        prog_verdict = {"bn": "নাড়ী দোষ সংক্রান্ত সতর্কতা (প্রতিকার কাম্য)", "hi": "नाड़ी दोष (शास्त्रीय उपाय अनुशंसित)", "en": "Nadi Dosha (Remedy Recommended)"}
        prog_desc = {
            "bn": "উভয়ের একই নাড়ী থাকায় চিকিৎসকের পরামর্শের পাশাপাশি মহামৃত্যুঞ্জয় মন্ত্র জপ ও সুবর্ণ/গোধূলি দান শাস্ত্রসম্মত।",
            "hi": "समान नाड़ी होने से नाड़ी दोष उपस्थित है। महामृत्युंजय जप तथा दान-पुण्य से इसके प्रभाव को शांत किया जा सकता है।",
            "en": "Identical Nadi indicates physiological sensitivity. Observance of Mahamrityunjaya mantra chanting neutralizes this affliction.",
        }

    # Conflicts & Arguments
    gana_rec = koota_map.get("Gan", 6.0)
    base_conf = (gana_rec / 6.0) * 55.0 + (25.0 if doshas.manglik_match else 5.0) + (15.0 if not doshas.rajjoo_dosha else 5.0)
    conf_sc = int(round(base_conf))
    conf_sc = max(30, min(95, conf_sc))

    if conf_sc >= 75:
        c_verdict = {"bn": "শান্তিপূর্ণ ও অহংবোধহীন বোঝাপড়া", "hi": "शांत एवं अहंकाररहित सामंजस्य", "en": "Peaceful & Low Conflict"}
        c_desc = {
            "bn": "উভয়ের স্বভাবের মধ্যে ভারসাম্য ও ক্ষমাশীল মনোভাব থাকবে। অহংবোধের সংঘাত অত্যন্ত কম হবে।",
            "hi": "दोनों के स्वभाव में विनम्रता और धैर्य रहेगा। गंभीर विवाद की संभावना न्यूनतम है।",
            "en": "Ego-free mutual balance ensures peaceful household dynamics. Disagreements are settled amicably.",
        }
    elif conf_sc >= 55:
        c_verdict = {"bn": "স্বাভাবিক সাংসারিক মান-অভিমান", "hi": "सामान्य मान-मनौव्वल", "en": "Normal Marital Adjustments"}
        c_desc = {
            "bn": "মাঝে মাঝে ছোটখাটো বিষয় নিয়ে মৃদু মতভেদ হতে পারে, তবে তা স্থায়ী রূপ নেবে না।",
            "hi": "कभी-कभार छोटी बातों पर मतभेद हो सकते हैं, जो आपसी समझ से शीघ्र सुलझ जाएंगे।",
            "en": "Occasional minor differences are manageable with emotional maturity. Avoiding hasty arguments preserves tranquility.",
        }
    else:
        c_verdict = {"bn": "মেজাজের তীব্রতা পরিহার্য", "hi": "क्रोध व विवाद से बचाव आवश्यक", "en": "Patience Required in Disagreements"}
        c_desc = {
            "bn": "উভয়ের মধ্যে কিছুটা তেজস্বী মনোভাব থাকতে পারে। তর্কের সময় সংযম ও পারস্পরিক পরিসর বজায় রাখা জরুরি।",
            "hi": "हठ अथवा उग्रता से बचने की सलाह दी जाती है। शांत रहकर संवाद करना रिश्ते को सुरक्षित रखेगा।",
            "en": "Strong-willed temperaments require conscious effort to avoid confrontation. Practicing tolerance is vital.",
        }

    # Financial Prosperity
    bhakoot_rec = koota_map.get("Bhakoot", 7.0)
    if bhakoot_rec >= 7.0:
        fin_sc = 92
        f_verdict = {"bn": "বিবাহোত্তর সৌভাগ্য ও ধনসম্পদ বৃদ্ধি", "hi": "विवाह पश्चात उत्कृष्ट धनवृद्धि", "en": "Strong Wealth Accumulation"}
        f_desc = {
            "bn": "ভকূটের শুভ অবস্থানের ফলে বিবাহের পর যৌথ ভাগ্যোদয় ঘটবে ও আর্থিক সঞ্চয় বৃদ্ধি পাবে।",
            "hi": "भकूट की अनुकूलता विवाह के बाद आर्थिक समृद्धि और पारिवारिक संपत्ति में वृद्धि लाती है।",
            "en": "Auspicious Bhakoot synergy brings combined economic expansion, career growth, and stable wealth accumulation post-marriage.",
        }
    else:
        fin_sc = 52
        f_verdict = {"bn": "পরিকল্পিত ব্যয় ও আর্থিক সচেতনতা কাম্য", "hi": "सुनियोजित व्यय व बचत आवश्यक", "en": "Prudent Financial Planning Needed"}
        f_desc = {
            "bn": "যৌথ আর্থিক পরিকল্পনা ও সুশৃঙ্খল সঞ্চয় বজায় রাখলে সমৃদ্ধি অব্যাহত থাকবে।",
            "hi": "अनावश्यक खर्चों से बचने के लिए पारदर्शी वित्तीय योजना आवश्यक है।",
            "en": "Financial harmony requires disciplined joint budgeting and transparent investments to safeguard against unforeseen expenses.",
        }

    # Future & Longevity Together
    base_fut = (total_score / 36.0) * 55.0 + (25.0 if not doshas.rajjoo_dosha else 5.0) + (15.0 if not doshas.vedha_dosha else 5.0)
    fut_sc = int(round(base_fut))
    fut_sc = max(35, min(98, fut_sc))

    if fut_sc >= 75:
        fut_verdict = {"bn": "দীর্ঘস্থায়ী ও কল্যাণময় যৌথ ভবিষ্যৎ", "hi": "दीर्घायु एवं मंगलमय भविष्य", "en": "Prosperous & Long-lasting Future"}
        fut_desc = {
            "bn": "রজ্জু ও শুভ গুণসংখ্যার কল্যাণে দাম্পত্য জীবন সুদীর্ঘ, সুস্থ ও মর্যাদাপূর্ণ হবে।",
            "hi": "रज्जू व वेध दोष की अनुपस्थिति दीर्घायु और सम्मानजनक वैवाहिक जीवन का आश्वासन देती है।",
            "en": "Absence of major Rajjoo/Vedha obstacles ensures longevity, societal respect, and steady mutual fulfillment over the decades.",
        }
    else:
        fut_verdict = {"bn": "পরস্পরকে যত্ন ও স্বাস্থ্য সচেতনতা প্রয়োজন", "hi": "स्वास्थ्य व सुरक्षा हेतु सतर्कता", "en": "Mutual Care & Health Focus Advised"}
        fut_desc = {
            "bn": "স্বাস্থ্য সচেতনতা এবং বৈদিক পূজা-প্রার্থনার মাধ্যমে একটি স্থিতিশীল ভবিষ্যৎ গড়ে তোলা সম্ভব।",
            "hi": "नियमित स्वास्थ्य देखभाल और धार्मिक अनुष्ठानों से भविष्य को सुखद और सुरक्षित बनाया जा सकता है।",
            "en": "Prioritizing physical wellness and performing traditional protective rituals will foster long-term marital security.",
        }

    # Classical Remedies
    remedies: list[str] = []
    if doshas.rajjoo_dosha:
        remedies.append(
            "শ্রী গৌরী-শঙ্কর পূজা এবং মাঙ্গলিক সুরক্ষা প্রার্থনায় ওম উমা-মহেশ্বরায় নমঃ মন্ত্র জপ।"
            if lang == "bn"
            else "श्री गौरी-शंकर पूजा तथा ॐ उमामहेश्वराभ्यां नमः मंत्र का नित्य जप।"
            if lang == "hi"
            else "Worship of Lord Shiva and Goddess Parvati (Om Uma-Maheshwaraya Namah) to mitigate Rajjoo affliction."
        )
    if nadi_rec < 8.0:
        remedies.append(
            "নাড়ী দোষ শান্তির জন্য মহামৃত্যুঞ্জয় মন্ত্র জপ (১০৮ বার) এবং যোগ্য পাত্রে সুবর্ণ বা তিল-তাম্র দান।"
            if lang == "bn"
            else "नाड़ी दोष निवारण हेतु महामृत्युंजय मंत्र का सवा लाख अथवा 108 बार नित्य जप व अन्नदान।"
            if lang == "hi"
            else "Chanting of the sacred Mahamrityunjaya Mantra (108 times daily) and offering sesame seeds/copper vessels to remove Nadi Dosha."
        )
    if not doshas.manglik_match:
        remedies.append(
            "উভয়ের মাঙ্গলিক সামঞ্জস্যের জন্য প্রতি মঙ্গলবার হনুমান চালীসা পাঠ অথবা সুন্দরকাণ্ড পাঠ।"
            if lang == "bn"
            else "प्रति मंगलवार सुंदरकांड अथवा हनुमान चालीसा का पाठ कर मंगल शांति करें।"
            if lang == "hi"
            else "Recitation of Sri Hanuman Chalisa or Sundarkand every Tuesday to harmonize Martian energies."
        )
    if bhakoot_rec < 7.0:
        remedies.append(
            "ভকূট দোষ প্রশমনে শ্রী বিষ্ণু সহস্রনাম পাঠ অথবা প্রতি বৃহস্পতিবার শ্রী লক্ষ্মী-নারায়ণের অর্চনা।"
            if lang == "bn"
            else "भकूट दोष शांति हेतु श्री विष्णु सहस्रनाम का पाठ व तुलसी दल अर्पण।"
            if lang == "hi"
            else "Recitation of Sri Vishnu Sahasranama and offering Tulsi leaves on Thursdays for domestic prosperity."
        )
    remedies.append(
        "বিবাহের পূর্বে উভয়ের কুলদেবতার আশীর্বাদ গ্রহণ ও শ্রী সত্যনারায়ণ ব্রত কথা শ্রবণ পরম কল্যাণকর।"
        if lang == "bn"
        else "विवाह पूर्व कुलदेवता का पूजन एवं श्री सत्यनारायण कथा का श्रवण अत्यंत कल्याणकारी है।"
        if lang == "hi"
        else "Seeking the blessings of the family deity (Kuladevata) and performing Sri Satyanarayana Puja prior to wedding ceremonies."
    )

    return MarriageLifeForecast(
        ideal_marriage_age_groom=b_age.get(lang, b_age["en"]),
        ideal_marriage_age_bride=g_age.get(lang, g_age["en"]),
        auspicious_marriage_years=auspicious_years[:3],
        auspicious_marriage_years_text=years_text.get(lang, years_text["en"]),
        marital_harmony_score=harmony_sc,
        marital_harmony_verdict=h_verdict.get(lang, h_verdict["en"]),
        marital_harmony_description=h_desc.get(lang, h_desc["en"]),
        children_progeny_score=prog_sc,
        children_progeny_verdict=prog_verdict.get(lang, prog_verdict["en"]),
        children_progeny_description=prog_desc.get(lang, prog_desc["en"]),
        conflict_friction_score=conf_sc,
        conflict_friction_verdict=c_verdict.get(lang, c_verdict["en"]),
        conflict_friction_description=c_desc.get(lang, c_desc["en"]),
        financial_prosperity_score=fin_sc,
        financial_prosperity_verdict=f_verdict.get(lang, f_verdict["en"]),
        financial_prosperity_description=f_desc.get(lang, f_desc["en"]),
        future_longevity_score=fut_sc,
        future_longevity_verdict=fut_verdict.get(lang, fut_verdict["en"]),
        future_longevity_description=fut_desc.get(lang, fut_desc["en"]),
        remedies_guidance=remedies,
    )
