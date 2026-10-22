"""Panchang elements: Tithi, Nithya Yoga, Karana, Yunja, sunrise and sunset.

These are here because the client's own reference report - the matchmaking sample
under `Resource Documents/`, generated before this project started - lists them
alongside the Avakahada Chakra, and the calculator did not produce any of them.
The sample gives a pair of fully worked charts, so each function below is checked
against real expected output rather than against a definition alone; see
`tests/test_astrology_nakshatra.py`.

Each element is a straightforward function of the two luminaries' sidereal
longitudes, except sunrise and sunset, which Swiss Ephemeris computes directly:

    Tithi   the Moon's elongation from the Sun in 12 degree steps, 30 per lunar month
    Yoga    the sum of the two longitudes in 13 degree 20 minute steps, 27 in all
    Karana  half a tithi, 60 per month drawn from an 11 name cycle
    Yunja   which third of the 27 nakshatras the birth star falls in
"""

from __future__ import annotations

from datetime import datetime, timedelta, UTC
from typing import Any, Literal

Lang = Literal["en", "bn", "hi"]

TITHI_NAMES = [
    ("Pratipada", "প্রতিপদ", "प्रतिपदा"), ("Dwitiya", "দ্বিতীয়া", "द्वितीया"),
    ("Tritiya", "তৃতীয়া", "तृतीया"), ("Chaturthi", "চতুর্থী", "चतुर्थी"),
    ("Panchami", "পঞ্চমী", "पंचमी"), ("Shashthi", "ষষ্ঠী", "षष्ठी"),
    ("Saptami", "সপ্তমী", "सप्तमी"), ("Ashtami", "অষ্টমী", "अष्टमी"),
    ("Navami", "নবমী", "नवमी"), ("Dashami", "দশমী", "दशमी"),
    ("Ekadashi", "একাদশী", "एकादशी"), ("Dwadashi", "দ্বাদশী", "द्वादशी"),
    ("Trayodashi", "ত্রয়োদশী", "त्रयोदशी"), ("Chaturdashi", "চতুর্দশী", "चतुर्दशी"),
]

YOGA_NAMES = [
    ("Vishkambha", "বিষ্কম্ভ", "विष्कम्भ"), ("Priti", "প্রীতি", "प्रीति"),
    ("Ayushman", "আয়ুষ্মান", "आयुष्मान"), ("Saubhagya", "সৌভাগ্য", "सौभाग्य"),
    ("Shobhana", "শোভন", "शोभन"), ("Atiganda", "অতিগণ্ড", "अतिगण्ड"),
    ("Sukarma", "সুকর্মা", "सुकर्मा"), ("Dhriti", "ধৃতি", "धृति"),
    ("Shula", "শূল", "शूल"), ("Ganda", "গণ্ড", "गण्ड"),
    ("Vriddhi", "বৃদ্ধি", "वृद्धि"), ("Dhruva", "ধ্রুব", "ध्रुव"),
    ("Vyaghata", "ব্যাঘাত", "व्याघात"), ("Harshana", "হর্ষণ", "हर्षण"),
    ("Vajra", "বজ্র", "वज्र"), ("Siddhi", "সিদ্ধি", "सिद्धि"),
    ("Vyatipata", "ব্যতীপাত", "व्यतीपात"), ("Variyan", "বরীয়ান", "वरीयान"),
    ("Parigha", "পরিঘ", "परिघ"), ("Shiva", "শিব", "शिव"),
    ("Siddha", "সিদ্ধ", "सिद्ध"), ("Sadhya", "সাধ্য", "साध्य"),
    ("Shubha", "শুভ", "शुभ"), ("Shukla", "শুক্ল", "शुक्ल"),
    ("Brahma", "ব্রহ্ম", "ब्रह्म"), ("Indra", "ইন্দ্র", "इन्द्र"),
    ("Vaidhriti", "বৈধৃতি", "वैधृति"),
]

# Karana cycle. The first half-tithi of the lunar month is Kimstughna; then the
# seven movable karanas repeat eight times; the last three half-tithis are the
# fixed karanas Shakuni, Chatushpada and Naga.
MOVABLE_KARANAS = [
    ("Bava", "বব", "बव"), ("Balava", "বালব", "बालव"), ("Kaulava", "কৌলব", "कौलव"),
    ("Taitila", "তৈতিল", "तैतिल"), ("Gara", "গর", "गर"), ("Vanija", "বণিজ", "वणिज"),
    ("Vishti", "বিষ্টি", "विष्टि"),
]
FIXED_KARANAS = {
    0: ("Kimstughna", "কিংস্তুঘ্ন", "किंस्तुघ्न"),
    57: ("Shakuni", "শকুনি", "शकुनि"),
    58: ("Chatushpada", "চতুষ্পদ", "चतुष्पद"),
    59: ("Naga", "নাগ", "नाग"),
}

YUNJA_NAMES = [
    ("Poorva (first third)", "পূর্ব", "पूर्व"),
    ("Madhya (middle third)", "মধ্য", "मध्य"),
    ("Antya (last third)", "অন্ত্য", "अन्त्य"),
]

PAKSHA_NAMES = [
    ("Shukla (waxing)", "শুক্ল পক্ষ", "शुक्ल पक्ष"),
    ("Krishna (waning)", "কৃষ্ণ পক্ষ", "कृष्ण पक्ष"),
]


def _pick(triple: tuple[str, str, str], lang: Lang) -> str:
    return {"en": triple[0], "bn": triple[1], "hi": triple[2]}.get(lang, triple[0])


def calculate_tithi(sun_longitude: float, moon_longitude: float, lang: Lang = "en") -> dict[str, Any]:
    """Tithi, its paksha, and how far through it the Moon has travelled.

    A tithi is 12 degrees of the Moon's elongation from the Sun. The first fifteen
    make the waxing fortnight, the next fifteen the waning one. Number 15 is
    Purnima and number 30 is Amavasya; both are named rather than numbered.
    """
    elongation = (moon_longitude - sun_longitude) % 360.0
    index = int(elongation / 12.0)  # 0..29
    completed = (elongation % 12.0) / 12.0 * 100.0

    paksha_index = 0 if index < 15 else 1
    within = index % 15

    if index == 14:
        name = ("Purnima (Full Moon)", "পূর্ণিমা", "पूर्णिमा")
    elif index == 29:
        name = ("Amavasya (New Moon)", "অমাবস্যা", "अमावस्या")
    else:
        name = TITHI_NAMES[within]

    return {
        "index": index + 1,
        "name": _pick(name, lang),
        "name_en": name[0],
        "paksha": _pick(PAKSHA_NAMES[paksha_index], lang),
        "paksha_en": PAKSHA_NAMES[paksha_index][0],
        "percentage_elapsed": round(completed, 2),
    }


def calculate_yoga(sun_longitude: float, moon_longitude: float, lang: Lang = "en") -> dict[str, Any]:
    """Nithya Yoga: the sum of the two longitudes, in 27 equal parts."""
    total = (sun_longitude + moon_longitude) % 360.0
    span = 360.0 / 27.0
    index = int(total / span)
    name = YOGA_NAMES[index]
    return {
        "index": index + 1,
        "name": _pick(name, lang),
        "name_en": name[0],
        "percentage_elapsed": round((total % span) / span * 100.0, 2),
    }


def calculate_karana(sun_longitude: float, moon_longitude: float, lang: Lang = "en") -> dict[str, Any]:
    """Karana: half a tithi, so 60 across the lunar month."""
    elongation = (moon_longitude - sun_longitude) % 360.0
    index = int(elongation / 6.0)  # 0..59
    if index in FIXED_KARANAS:
        name = FIXED_KARANAS[index]
    else:
        name = MOVABLE_KARANAS[(index - 1) % 7]
    return {
        "index": index + 1,
        "name": _pick(name, lang),
        "name_en": name[0],
        "percentage_elapsed": round((elongation % 6.0) / 6.0 * 100.0, 2),
    }


def calculate_yunja(nakshatra_index: int, lang: Lang = "en") -> dict[str, Any]:
    """Yunja: which third of the 27 nakshatras the birth star falls in."""
    third = min(nakshatra_index // 9, 2)
    name = YUNJA_NAMES[third]
    return {"index": third + 1, "name": _pick(name, lang), "name_en": name[0]}


def calculate_sun_times(
    swe: Any, jd_ut: float, latitude: float, longitude: float, offset_hours: float
) -> dict[str, str | None]:
    """Local sunrise and sunset for the birth day.

    Swiss Ephemeris returns these as Julian Days in UT; they are converted back to
    the birth place's own local clock so they read the way a panchang prints them.
    """

    def _search(flag: int) -> str | None:
        try:
            # Start searching from local midnight so the result belongs to the
            # birth date rather than to the following day.
            start = jd_ut - 0.5
            result, times = swe.rise_trans(
                start, swe.SUN, longitude, latitude, 0.0, 0.0, 0.0, flag
            )
            if result < 0 or not times or not times[0]:
                return None
            local_jd = times[0] + offset_hours / 24.0
            year, month, day, hour = swe.revjul(local_jd)
            total_seconds = int(round(hour * 3600))
            # revjul can land a hair past midnight; wrap rather than print 24:00.
            total_seconds %= 86400
            return (
                f"{total_seconds // 3600:02d}:"
                f"{(total_seconds % 3600) // 60:02d}:"
                f"{total_seconds % 60:02d}"
            )
        except Exception:
            # Inside the polar circles the Sun may not rise or set at all. A missing
            # time is reported as missing rather than guessed.
            return None

    return {
        "sunrise": _search(swe.CALC_RISE | swe.BIT_DISC_CENTER),
        "sunset": _search(swe.CALC_SET | swe.BIT_DISC_CENTER),
    }


def build_panchang(
    swe: Any,
    jd_ut: float,
    sun_longitude: float,
    moon_longitude: float,
    nakshatra_index: int,
    latitude: float,
    longitude: float,
    offset_hours: float,
    lang: Lang = "en",
) -> dict[str, Any]:
    """Every panchang element the client's reference report lists."""
    times = calculate_sun_times(swe, jd_ut, latitude, longitude, offset_hours)
    return {
        "tithi": calculate_tithi(sun_longitude, moon_longitude, lang),
        "yoga": calculate_yoga(sun_longitude, moon_longitude, lang),
        "karana": calculate_karana(sun_longitude, moon_longitude, lang),
        "yunja": calculate_yunja(nakshatra_index, lang),
        "sunrise": times["sunrise"],
        "sunset": times["sunset"],
    }
