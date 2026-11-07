"""Scheduled appointments.

The hard part here is not the price, it is making a double booking impossible.
Two people asking for overlapping times must not both succeed, and checking
"is this free?" before writing does not achieve that — both requests can read
"free" before either writes.

So a booking claims the five-minute units it needs, one row each, against a
unique index on (astrologer, start). The second claim on any shared unit fails
at the database. The insert is the lock; nothing here relies on being the only
request in flight.

Order matters too: the units are claimed **before** the wallet is touched. A
clash is the ordinary failure, and it should happen before anyone's money
moves rather than after.
"""

import asyncio
from datetime import UTC, date as date_type, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any

from beanie import PydanticObjectId
from beanie.operators import GTE, LT, And, In, Or
from loguru import logger
from pymongo.errors import DuplicateKeyError

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.appointment import (
    SLOT_MINUTES,
    Appointment,
    AppointmentSlot,
    AvailabilityWindow,
    PrivateInviteLink,
)
from app.models.astrologer import Astrologer
from app.models.base import utcnow
from app.models.enums import AppointmentStatus, TransactionReason
from app.models.user import User

# Bookings that still hold their time. A cancelled one has given it back.
LIVE_STATUSES = [AppointmentStatus.BOOKED, AppointmentStatus.COMPLETED]


# --------------------------------------------------------------- the grid
def _aligned(moment: datetime) -> bool:
    """Does this land on the five-minute grid everything is snapped to?"""
    return moment.second == 0 and moment.microsecond == 0 and moment.minute % SLOT_MINUTES == 0


def slot_starts(starts_at: datetime, minutes: int) -> list[datetime]:
    """Every five-minute unit a booking of this length occupies."""
    count = minutes // SLOT_MINUTES
    return [starts_at + timedelta(minutes=SLOT_MINUTES * i) for i in range(count)]


# ------------------------------------------------ Vedic Choghadiya & Muhurat
DAY_CHOGHADIYA = [
    # 0 = Monday
    ["amrit", "kaal", "shubh", "rog", "udveg", "char", "labh", "amrit"],
    # 1 = Tuesday
    ["rog", "udveg", "char", "labh", "amrit", "kaal", "shubh", "rog"],
    # 2 = Wednesday
    ["labh", "amrit", "kaal", "shubh", "rog", "udveg", "char", "labh"],
    # 3 = Thursday
    ["shubh", "rog", "udveg", "char", "labh", "amrit", "kaal", "shubh"],
    # 4 = Friday
    ["char", "labh", "amrit", "kaal", "shubh", "rog", "udveg", "char"],
    # 5 = Saturday
    ["kaal", "shubh", "rog", "udveg", "char", "labh", "amrit", "kaal"],
    # 6 = Sunday
    ["udveg", "char", "labh", "amrit", "kaal", "shubh", "rog", "udveg"],
]

NIGHT_CHOGHADIYA = [
    # 0 = Monday
    ["char", "rog", "kaal", "labh", "udveg", "shubh", "amrit", "char"],
    # 1 = Tuesday
    ["kaal", "labh", "udveg", "shubh", "amrit", "char", "rog", "kaal"],
    # 2 = Wednesday
    ["udveg", "shubh", "amrit", "char", "rog", "kaal", "labh", "udveg"],
    # 3 = Thursday
    ["amrit", "char", "rog", "kaal", "labh", "udveg", "shubh", "amrit"],
    # 4 = Friday
    ["rog", "kaal", "labh", "udveg", "shubh", "amrit", "char", "rog"],
    # 5 = Saturday
    ["labh", "udveg", "shubh", "amrit", "char", "rog", "kaal", "labh"],
    # 6 = Sunday
    ["shubh", "amrit", "char", "rog", "kaal", "labh", "udveg", "shubh"],
]

RAHU_KAAL_WINDOWS = {
    0: (7.5, 9.0),    # Mon 07:30 - 09:00
    1: (15.0, 16.5),  # Tue 15:00 - 16:30
    2: (12.0, 13.5),  # Wed 12:00 - 13:30
    3: (13.5, 15.0),  # Thu 13:30 - 15:00
    4: (10.5, 12.0),  # Fri 10:30 - 12:00
    5: (9.0, 10.5),   # Sat 09:00 - 10:30
    6: (16.5, 18.0),  # Sun 16:30 - 18:00
}

YAMAGHANTA_WINDOWS = {
    0: (10.5, 12.0),  # Mon 10:30 - 12:00
    1: (9.0, 10.5),   # Tue 09:00 - 10:30
    2: (7.5, 9.0),    # Wed 07:30 - 09:00
    3: (6.0, 7.5),    # Thu 06:00 - 07:30
    4: (15.0, 16.5),  # Fri 15:00 - 16:30
    5: (13.5, 15.0),  # Sat 13:30 - 15:00
    6: (12.0, 13.5),  # Sun 12:00 - 13:30
}

GULIKA_WINDOWS = {
    0: (13.5, 15.0),  # Mon 13:30 - 15:00
    1: (12.0, 13.5),  # Tue 12:00 - 13:30
    2: (10.5, 12.0),  # Wed 10:30 - 12:00
    3: (9.0, 10.5),   # Thu 09:00 - 10:30
    4: (7.5, 9.0),    # Fri 07:30 - 09:00
    5: (6.0, 7.5),    # Sat 06:00 - 07:30
    6: (15.0, 16.5),  # Sun 15:00 - 16:30
}


def _format_decimal_hours_ist(dec: float) -> str:
    h = int(dec)
    m = int(round((dec - h) * 60))
    if m >= 60:
        h += 1
        m = 0
    period = "AM" if h < 12 else "PM"
    display_h = 12 if h in (0, 12) else (h % 12)
    return f"{display_h}:{m:02d} {period}"


def calculate_slot_muhurat(moment_utc: datetime) -> dict[str, Any]:
    """Computes Vedic Choghadiya, Hora, Rahu Kaal, Yamaghanta & Gulika quality for any time slot."""
    # Convert UTC to Indian Standard Time (+05:30)
    ist = moment_utc + timedelta(hours=5, minutes=30)
    weekday = ist.weekday()  # Monday = 0, Sunday = 6
    hour_decimal = ist.hour + ist.minute / 60.0

    is_rahu = False
    if weekday in RAHU_KAAL_WINDOWS:
        r_start, r_end = RAHU_KAAL_WINDOWS[weekday]
        if r_start <= hour_decimal < r_end:
            is_rahu = True

    is_yamaghanta = False
    if weekday in YAMAGHANTA_WINDOWS:
        y_start, y_end = YAMAGHANTA_WINDOWS[weekday]
        if y_start <= hour_decimal < y_end:
            is_yamaghanta = True

    is_gulika = False
    if weekday in GULIKA_WINDOWS:
        g_start, g_end = GULIKA_WINDOWS[weekday]
        if g_start <= hour_decimal < g_end:
            is_gulika = True

    is_abhijit = 11.75 <= hour_decimal < 12.58  # ~11:45 AM - 12:35 PM

    # Day Choghadiya: 06:00 to 18:00 (8 parts of 1.5h = 90m)
    # Night Choghadiya: 18:00 to 06:00
    if 6.0 <= hour_decimal < 18.0:
        part_idx = int((hour_decimal - 6.0) / 1.5)
        part_idx = max(0, min(7, part_idx))
        choghadiya = DAY_CHOGHADIYA[weekday][part_idx]
    else:
        night_hours = (hour_decimal - 18.0) if hour_decimal >= 18.0 else (hour_decimal + 6.0)
        part_idx = int(night_hours / 1.5)
        part_idx = max(0, min(7, part_idx))
        choghadiya = NIGHT_CHOGHADIYA[weekday][part_idx]

    is_amrit = (choghadiya == "amrit")
    is_ravi_yoga = (choghadiya in ("shubh", "labh") and not is_rahu and not is_yamaghanta)

    # Precedence: Abhijit > Amrit > Rahu Kaal (Alert) > Yamaghanta (Alert) > Gulika > Shubh/Labh > Char > Normal
    if is_abhijit:
        quality = "super_auspicious"
        tag_color = "gold"
        badge_bn = "অভিজিৎ মুহূর্ত (সর্বাধিক শুভ)"
        badge_hi = "अभिजित मुहूर्त (परम शुभ)"
        badge_en = "Abhijit Muhurat (Highest Auspicious)"
        short_tag_bn = "অভিজিৎ"
        short_tag_en = "Abhijit"
    elif is_amrit:
        quality = "super_auspicious"
        tag_color = "gold"
        badge_bn = "অমৃত মুহূর্ত (পরম শুভ)"
        badge_hi = "अमृत मुहूर्त (परम शुभ)"
        badge_en = "Amrit Muhurat (Divine Best)"
        short_tag_bn = "অমৃত কাল"
        short_tag_en = "Amrit Kaal"
    elif is_rahu:
        quality = "inauspicious"
        tag_color = "red"
        badge_bn = "রাহু কাল (অশুভ সময় / প্রতিকার অনুকূল)"
        badge_hi = "राहु काल (अशुभ समय)"
        badge_en = "Rahu Kaal (Inauspicious / Remedial Only)"
        short_tag_bn = "রাহুকাল"
        short_tag_en = "Rahu Kaal"
    elif is_yamaghanta:
        quality = "inauspicious"
        tag_color = "amber"
        badge_bn = "যমঘণ্ট কাল (অশুভ সময়)"
        badge_hi = "यमघंट काल (अशुभ समय)"
        badge_en = "Yamaghanta Kaal (Inauspicious)"
        short_tag_bn = "যমঘণ্ট"
        short_tag_en = "Yamaghanta"
    elif is_gulika:
        quality = "inauspicious"
        tag_color = "amber"
        badge_bn = "গুলিকা কাল (সতর্ক সময়)"
        badge_hi = "गुलिका काल (अशुभ समय)"
        badge_en = "Gulika Kaal (Cautionary)"
        short_tag_bn = "গুলিকা"
        short_tag_en = "Gulika"
    elif choghadiya in ("shubh", "labh"):
        quality = "auspicious"
        tag_color = "green"
        name_bn = "শুভ" if choghadiya == "shubh" else "লাভ"
        name_hi = "शुभ" if choghadiya == "shubh" else "लाभ"
        name_en = "Shubh" if choghadiya == "shubh" else "Labh"
        badge_bn = f"{name_bn} চোঘড়িয়া / রবি যোগ (কল্যাণকর)"
        badge_hi = f"{name_hi} मुहूर्त / रवि योग (शुभ)"
        badge_en = f"{name_en} Muhurat / Ravi Yoga (Auspicious)"
        short_tag_bn = f"{name_bn} যোগ"
        short_tag_en = f"{name_en} Yoga"
    elif choghadiya == "char":
        quality = "neutral"
        tag_color = "slate"
        badge_bn = "চর মুহূর্ত (গতিশীল)"
        badge_hi = "चर मुहूर्त (गतिशील)"
        badge_en = "Char Muhurat (Active)"
        short_tag_bn = "চর কাল"
        short_tag_en = "Char Kaal"
    else:
        quality = "normal"
        tag_color = "slate"
        badge_bn = "সাধারণ সময়"
        badge_hi = "सामान्य समय"
        badge_en = "Standard Slot"
        short_tag_bn = "সাধারণ"
        short_tag_en = "Standard"

    return {
        "choghadiya": choghadiya,
        "quality": quality,
        "tag_color": tag_color,
        "is_rahu_kaal": is_rahu,
        "is_yamaghanta": is_yamaghanta,
        "is_gulika": is_gulika,
        "is_abhijit": is_abhijit,
        "is_amrit": is_amrit,
        "is_ravi_yoga": is_ravi_yoga,
        "badge_bn": badge_bn,
        "badge_hi": badge_hi,
        "badge_en": badge_en,
        "short_tag_bn": short_tag_bn,
        "short_tag_en": short_tag_en,
    }


def get_auspicious_transit_for_date(target_date: date_type) -> dict[str, Any]:
    """Detects auspicious Vedic tithis and celestial transits for dynamic Tatkal surge pricing.

    Identifies:
    - Amavasya (মহাপবিত্র অমাবস্যা - 10x remedial demand for Kaal Sarp & Pitru Dosha)
    - Purnima (পবিত্র পূর্ণিমা তিথি - Satyanarayan, Chandra Shanti, prosperity)
    - Shani Pradosh (মহাদুর্লভ শনি প্রদোষ - Saturday Trayodashi, Shani Sadesati & Mahadeva relief)
    - Pradosh Vrat (প্রদোষ ব্রত তিথি - Trayodashi on other weekdays)
    - Ekadashi (পবিত্র একাদশী ব্রত তিথি - Vishnu devotion & karma cleansing)
    - Surya Grahan (সূর্যগ্রহণ মহাযোগ - Solar Eclipse)
    - Chandra Grahan (চন্দ্রগ্রহণ মহালগ্ন - Lunar Eclipse)
    - Masa Shivratri (মাসিক শিবরাত্রি - Krishna Chaturdashi)
    - Guru / Ravi Pushya Yoga (বৃহস্পতি/রবি পুষ্য নক্ষত্র মহাযোগ)
    """
    import swisseph as swe
    from zoneinfo import ZoneInfo

    IST = ZoneInfo("Asia/Kolkata")
    dt = datetime(target_date.year, target_date.month, target_date.day, 12, 0, tzinfo=IST)
    weekday = dt.weekday()  # Monday = 0, Saturday = 5, Sunday = 6

    # 1. Sidereal longitudes at 12:00 PM IST (06:30 UTC)
    try:
        jd = swe.julday(target_date.year, target_date.month, target_date.day, 6.5)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        sun_res = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
        sun_lon = float(sun_res[0][0]) % 360.0
        moon_res = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        moon_lon = float(moon_res[0][0]) % 360.0
        rahu_res = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
        rahu_lon = float(rahu_res[0][0]) % 360.0
        ketu_lon = (rahu_lon + 180.0) % 360.0
    except Exception as exc:
        logger.warning("Could not calculate exact planetary positions with swisseph: {}", exc)
        sun_lon = 0.0
        moon_lon = 0.0
        rahu_lon = 0.0
        ketu_lon = 180.0

    elongation = (moon_lon - sun_lon) % 360.0
    tithi_index = int(elongation / 12.0)  # 0..29
    tithi_num = (tithi_index % 15) + 1    # 1..15
    is_shukla = tithi_index < 15
    paksha_bn = "শুক্লপক্ষ" if is_shukla else "কৃষ্ণপক্ষ"
    paksha_en = "Shukla Paksha" if is_shukla else "Krishna Paksha"

    # Pushya Nakshatra check (Cancer 3°20' - 16°40' -> index 7 in 0-indexed nakshatras)
    nak_idx = int(moon_lon / (360.0 / 27.0)) % 27
    is_pushya = nak_idx == 7

    # Node proximities for Eclipse detection
    sun_rahu_dist = min(abs((sun_lon - rahu_lon + 180) % 360 - 180), abs((sun_lon - ketu_lon + 180) % 360 - 180))
    moon_rahu_dist = min(abs((moon_lon - rahu_lon + 180) % 360 - 180), abs((moon_lon - ketu_lon + 180) % 360 - 180))

    is_auspicious = False
    event_key = None
    event_name_bn = None
    event_name_en = None
    recommended_multiplier = 1.0
    remedy_focus_bn = None
    remedy_focus_en = None
    spiritual_reason_bn = None
    spiritual_reason_en = None
    demand_factor = "1x"

    # Evaluation priority
    if tithi_index == 29 and sun_rahu_dist < 12.5:
        # Solar Eclipse
        is_auspicious = True
        event_key = "surya_grahan"
        event_name_bn = "সূর্যগ্রহণ মহাযোগ (Surya Grahan)"
        event_name_en = "Solar Eclipse (Surya Grahan)"
        recommended_multiplier = 2.0
        demand_factor = "10x"
        remedy_focus_bn = "গ্রহণদোষ শান্তি, তীব্র মহাকবচ ধারণ ও মন্ত্রসিদ্ধি"
        remedy_focus_en = "Eclipse Dosha Shanti, Sacred Protection Kavach & Mantra Siddhi"
        spiritual_reason_bn = "সূর্যগ্রহণের দিনে গ্রহদোষ শান্তি ও রক্ষাকবচ গ্রহণের চাহিদা সাধারণ দিনের চেয়ে বহু গুণ বেশি থাকে।"
        spiritual_reason_en = "Demand surges up to 10x during Solar Eclipse for planetary remediation and protective talismans."

    elif tithi_index == 14 and moon_rahu_dist < 12.5:
        # Lunar Eclipse
        is_auspicious = True
        event_key = "chandra_grahan"
        event_name_bn = "চন্দ্রগ্রহণ মহালগ্ন (Chandra Grahan)"
        event_name_en = "Lunar Eclipse (Chandra Grahan)"
        recommended_multiplier = 2.0
        demand_factor = "10x"
        remedy_focus_bn = "চন্দ্রদোষ নিবৃত্তি, মানসিক উদ্বেগ শান্তি ও আধ্যাত্মিক দীক্ষা"
        remedy_focus_en = "Chandra Dosha Relief, Mental Anxiety Relief & Spiritual Initiation"
        spiritual_reason_bn = "চন্দ্রগ্রহণের সময় বিশেষ মানসিক শান্তি ও চন্দ্র প্রতিকার নেওয়ার আধ্যাত্মিক চাহিদা ১০ গুণ বৃদ্ধি পায়।"
        spiritual_reason_en = "Surging spiritual demand during Lunar Eclipse for mental tranquility and Moon remediation."

    elif tithi_index == 29:
        # Amavasya (New Moon)
        is_auspicious = True
        event_key = "amavasya"
        event_name_bn = "মহাপবিত্র অমাবস্যা তিথি (Amavasya)"
        event_name_en = "Sacred Amavasya (New Moon)"
        recommended_multiplier = 2.0
        demand_factor = "10x"
        remedy_focus_bn = "কালসর্প দোষ খণ্ডন, পিতৃ তর্পণ, রাহু-কেতু শান্তিকবচ"
        remedy_focus_en = "Kaal Sarp Dosha Remediation, Ancestral Pitru Tarpana & Rahu-Ketu Shanti"
        spiritual_reason_bn = "অমাবস্যা তিথিতে কালসর্প ও পিতৃদোষ প্রতিকার নেওয়ার চাহিদা সাধারণ দিনের চেয়ে ১০ গুণ বেশি থাকে।"
        spiritual_reason_en = "Remedial consultation demand surges up to 10x during Amavasya for Kaal Sarp and Pitru Dosha remedies."

    elif tithi_index == 14:
        # Purnima (Full Moon)
        is_auspicious = True
        event_key = "purnima"
        event_name_bn = "পবিত্র পূর্ণিমা তিথি (Purnima)"
        event_name_en = "Sacred Purnima (Full Moon)"
        recommended_multiplier = 1.5
        demand_factor = "8x"
        remedy_focus_bn = "সত্যনারায়ণ পূজা সংকল্প, চন্দ্র শান্তি ও পারিবারিক শ্রীবৃদ্ধি"
        remedy_focus_en = "Satyanarayan Sankalpa, Chandra Shanti & Family Prosperity"
        spiritual_reason_bn = "পূর্ণিমা তিথিতে সত্যনারায়ণ, চন্দ্র শান্তি ও সমৃদ্ধির প্রতিকার নেওয়ার পরম শুভ চাহিদা থাকে।"
        spiritual_reason_en = "Remedial consultations surge significantly during Purnima for prosperity, relationships and emotional clarity."

    elif tithi_num == 13 and weekday == 5:
        # Shani Pradosh (Saturday Trayodashi)
        is_auspicious = True
        event_key = "shani_pradosh"
        event_name_bn = "মহাদুর্লভ শনি প্রদোষ মহাযোগ (Shani Pradosh)"
        event_name_en = "Sacred Shani Pradosh (Saturday Trayodashi)"
        recommended_multiplier = 2.0
        demand_factor = "10x"
        remedy_focus_bn = "শনির সাড়েসাতি ও ধাইয়া নিবৃত্তি, মহামৃত্যুঞ্জয় ও শিবকৃপা কবচ"
        remedy_focus_en = "Shani Sadesati & Dhaiya Relief, Mahamrityunjaya & Shiva Blessings"
        spiritual_reason_bn = "শনিবার ত্রয়োদশী তিথি পড়ায় এটি শনি প্রদোষ—শনির সাড়েসাতি ও দীর্ঘস্থায়ী কর্মবাধা কাটানোর বিরলতম সংযোগ।"
        spiritual_reason_en = "Trayodashi falling on Saturday forms rare Shani Pradosh — unmatched demand for relieving Saturn affliction."

    elif tithi_num == 11:
        # Ekadashi
        is_auspicious = True
        event_key = "ekadashi"
        event_name_bn = "পবিত্র একাদশী ব্রত তিথি (Ekadashi)"
        event_name_en = "Sacred Ekadashi Vrat Tithi"
        recommended_multiplier = 1.5
        demand_factor = "6x"
        remedy_focus_bn = "শ্রীবিষ্ণু আরাধনা, পাপমোচন সংকল্প ও আত্মিক কল্যাণ"
        remedy_focus_en = "Lord Vishnu Devotion, Karma Cleansing & Spiritual Vows"
        spiritual_reason_bn = "একাদশীর পবিত্র দিনে ব্রত সংকল্প ও বৃহস্পতি-বিষ্ণু প্রতিকার নেওয়ার ব্যাপক ভক্তিমূলক চাহিদা থাকে।"
        spiritual_reason_en = "Spiritual demand surges on Ekadashi for devotional discipline and Jupiterian karmic resolutions."

    elif is_pushya and weekday == 3:
        # Guru Pushya Yoga
        is_auspicious = True
        event_key = "guru_pushya"
        event_name_bn = "মহা শুভ গুরু পুষ্য যোগ (Guru Pushya Yoga)"
        event_name_en = "Supreme Guru Pushya Mahayoga"
        recommended_multiplier = 2.0
        demand_factor = "10x"
        remedy_focus_bn = "রত্ন ধারণ, স্বর্ণ ক্রয়, ধনপ্রাপ্তি ও সিদ্ধি সংকল্প"
        remedy_focus_en = "Gemstone Consecration, Gold Acquisition & Wealth Siddhi"
        spiritual_reason_bn = "বৃহস্পতিবার পুষ্য নক্ষত্রের সংযোগে তৈরি হওয়া গুরু পুষ্য যোগে রত্ন ও প্রতিকার ধারণে সর্বাধিক ফল লাভ হয়।"
        spiritual_reason_en = "Guru Pushya Yoga is the most auspicious planetary alignment for gemstone activation and wealth remedies."

    elif is_pushya and weekday == 6:
        # Ravi Pushya Yoga
        is_auspicious = True
        event_key = "ravi_pushya"
        event_name_bn = "মহা শুভ রবি পুষ্য যোগ (Ravi Pushya Yoga)"
        event_name_en = "Supreme Ravi Pushya Mahayoga"
        recommended_multiplier = 2.0
        demand_factor = "10x"
        remedy_focus_bn = "সূর্য প্রতিকার, মাণিক্য রত্ন ধারণ ও রাজ্যসুখ সংকল্প"
        remedy_focus_en = "Sun Remediation, Ruby Gemstone Consecration & Leadership Siddhi"
        spiritual_reason_bn = "রবিবার পুষ্য নক্ষত্রের সংযোগে গঠিত রবি পুষ্য যোগে প্রতিকার গ্রহণের চরম শুভ প্রভাব বিদ্যমান।"
        spiritual_reason_en = "Ravi Pushya alignment grants immense planetary power for Solar remedies and executive breakthroughs."

    elif tithi_num == 13:
        # General Pradosh
        is_auspicious = True
        event_key = "pradosh"
        event_name_bn = "পবিত্র প্রদোষ ব্রত তিথি (Pradosh Vrat)"
        event_name_en = "Sacred Pradosh Vrat Tithi"
        recommended_multiplier = 1.5
        demand_factor = "5x"
        remedy_focus_bn = "মহাদেব আরাধনা ও শারীরিক-মানসিক রোগ শান্তি"
        remedy_focus_en = "Lord Shiva Worship & Health Dosha Remediation"
        spiritual_reason_bn = "ত্রয়োদশীর প্রদোষ কালে মহাদেব আরাধনা ও গ্রহশান্তির বিশেষ চাহিদা থাকে।"
        spiritual_reason_en = "Pradosh twilight window brings elevated seeker interest in health and emotional peace remedies."

    elif tithi_index == 27:
        # Masa Shivratri
        is_auspicious = True
        event_key = "shivratri"
        event_name_bn = "পবিত্র মাসিক শিবরাত্রি (Masa Shivratri)"
        event_name_en = "Sacred Masa Shivratri"
        recommended_multiplier = 1.5
        demand_factor = "7x"
        remedy_focus_bn = "রুদ্রাভিষেক, শনি-রাহু উপশম ও আত্মিক সুরক্ষাকবচ"
        remedy_focus_en = "Rudrabhishekam, Saturn-Rahu Mitigation & Protective Armor"
        spiritual_reason_bn = "মাসিক শিবরাত্রিতে রুদ্রাভিষেক ও গ্রহদোষ নিবৃত্তির প্রবল ভক্তিমূলক চাহিদা পরিলক্ষিত হয়।"
        spiritual_reason_en = "Elevated seeker demand during monthly Shivratri for profound spiritual protection."

    return {
        "date": target_date.isoformat(),
        "is_auspicious_transit_day": is_auspicious,
        "event_key": event_key,
        "event_name_bn": event_name_bn,
        "event_name_en": event_name_en,
        "recommended_multiplier": recommended_multiplier,
        "surge_multipliers": [1.5, 2.0] if is_auspicious else [1.0],
        "demand_factor": demand_factor,
        "remedy_focus_bn": remedy_focus_bn,
        "remedy_focus_en": remedy_focus_en,
        "spiritual_reason_bn": spiritual_reason_bn,
        "spiritual_reason_en": spiritual_reason_en,
        "tithi_index": tithi_index,
        "tithi_num": tithi_num,
        "paksha_bn": paksha_bn,
        "paksha_en": paksha_en,
    }


def get_daily_panchang_shield(target_date: date_type) -> dict[str, Any]:
    """Generates a complete Vedic Panchang & Rahu Kaal Shield summary for a calendar day."""
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
    dt = datetime(target_date.year, target_date.month, target_date.day, 12, 0, tzinfo=IST)
    weekday = dt.weekday()

    r_start, r_end = RAHU_KAAL_WINDOWS.get(weekday, (16.5, 18.0))
    y_start, y_end = YAMAGHANTA_WINDOWS.get(weekday, (12.0, 13.5))
    g_start, g_end = GULIKA_WINDOWS.get(weekday, (15.0, 16.5))

    rahu_label = f"{_format_decimal_hours_ist(r_start)} – {_format_decimal_hours_ist(r_end)}"
    yama_label = f"{_format_decimal_hours_ist(y_start)} – {_format_decimal_hours_ist(y_end)}"
    gulika_label = f"{_format_decimal_hours_ist(g_start)} – {_format_decimal_hours_ist(g_end)}"
    abhijit_label = "11:45 AM – 12:35 PM"

    # Generate 24-hour breakdown (0..23 in IST)
    hourly = []
    for h in range(24):
        slot_dt = datetime(target_date.year, target_date.month, target_date.day, h, 0, tzinfo=IST)
        utc_dt = slot_dt.astimezone(UTC)
        muhurat = calculate_slot_muhurat(utc_dt)
        hourly.append({
            "hour": h,
            "time_ist": f"{12 if h in (0, 12) else h % 12}:00 {'AM' if h < 12 else 'PM'}",
            **muhurat,
        })

    auspicious_transit = get_auspicious_transit_for_date(target_date)

    return {
        "date": target_date.isoformat(),
        "weekday": weekday,
        "auspicious_transit": auspicious_transit,
        "rahu_kaal": {
            "start_decimal": r_start,
            "end_decimal": r_end,
            "formatted_ist": rahu_label,
            "warning_bn": f"আজকের রাহুকাল {rahu_label}। এই সময়ে নতুন কোনো শুভ কাজ বর্জনীয়।",
            "warning_en": f"Today {rahu_label} is Rahu Kaal. Inauspicious for initiating new activities.",
        },
        "yamaghanta_kaal": {
            "start_decimal": y_start,
            "end_decimal": y_end,
            "formatted_ist": yama_label,
            "warning_bn": f"আজকের যমঘণ্ট কাল {yama_label}।",
            "warning_en": f"Today {yama_label} is Yamaghanta Kaal.",
        },
        "gulika_kaal": {
            "start_decimal": g_start,
            "end_decimal": g_end,
            "formatted_ist": gulika_label,
            "warning_bn": f"আজকের গুলিকা কাল {gulika_label}।",
            "warning_en": f"Today {gulika_label} is Gulika Kaal.",
        },
        "abhijit_muhurat": {
            "start_decimal": 11.75,
            "end_decimal": 12.58,
            "formatted_ist": abhijit_label,
            "blessing_bn": "অভিজিৎ মুহূর্ত সর্বকার্য সিদ্ধিদায়ক পরম শুভ মুহূর্ত।",
            "blessing_en": "Abhijit Muhurat grants supreme victory and clears all doshas.",
        },
        "hourly_muhurat": hourly,
    }


# ----------------------------------------------------------------- pricing
def price_for(
    card,
    minutes: int,
    *,
    tatkal_multiplier: float | None = None,
    tatkal_fixed_paise: int | None = None,
    custom_price_paise: int | None = None,
    discount_percent: float | None = None,
) -> int:
    """What a booking of this length costs, in paise.

    Pro rata from the astrologer's block price, so "thirty minutes for two
    hundred and fifty" also prices forty minutes without them having to say
    so. Supports custom price overrides, discount percentages, and Tatkal multipliers.
    """
    if card.block_minutes <= 0:
        return 0

    if custom_price_paise is not None and custom_price_paise >= 0:
        base = round(custom_price_paise * minutes / card.block_minutes)
    else:
        base = round(card.price_paise * minutes / card.block_minutes)

    if discount_percent and 0 < discount_percent <= 100:
        base = int(base * (1.0 - discount_percent / 100.0))

    if tatkal_fixed_paise is not None and tatkal_fixed_paise > 0:
        base = round(tatkal_fixed_paise * minutes / card.block_minutes)
    elif tatkal_multiplier and tatkal_multiplier > 1.0:
        base = int(base * tatkal_multiplier)

    return max(base, 0)


def deposit_for(price_paise: int, commission_percent: float) -> int:
    """The platform's share, taken up front and not returned.

    Rounded down, so the deposit is never a paisa more than the share the
    platform is owed.
    """
    return int(price_paise * commission_percent / 100)


def coins_for_paise(paise: int, coins_per_rupee: int) -> int:
    """Paise to coins, rounded up.

    Up rather than down: rounding down would let a booking be paid for with
    fewer coins than it is worth, and across enough bookings that is the
    platform quietly giving money away.
    """
    return -(-paise * coins_per_rupee // 100)


# ------------------------------------------------------------ availability
async def _windows_for(
    astrologer_id: PydanticObjectId,
    start: datetime,
    end: datetime,
    *,
    include_private: bool = False,
) -> list[AvailabilityWindow]:
    windows = await (
        AvailabilityWindow.find(
            {
                "astrologer_id": astrologer_id,
                "starts_at": {"$lt": end},
                "ends_at": {"$gte": start},
            }
        )
        .sort(+AvailabilityWindow.starts_at)
        .to_list()
    )
    if not include_private:
        windows = [w for w in windows if not getattr(w, "is_private", False)]
    return windows


async def booked_between(
    astrologer_id: PydanticObjectId, start: datetime, end: datetime
) -> list[Appointment]:
    """Bookings that touch this range, soonest first."""
    return (
        await Appointment.find(
            And(
                Appointment.astrologer_id == astrologer_id,
                In(Appointment.status, LIVE_STATUSES),
                LT(Appointment.starts_at, end),
                GTE(Appointment.ends_at, start),
            )
        )
        .sort(+Appointment.starts_at)
        .to_list()
    )


async def day_view(
    *,
    astrologer: Astrologer,
    day_start: datetime,
    day_end: datetime,
    invite_code: str | None = None,
) -> dict:
    """What a user needs to pick a time: open hours, what is gone, Vedic Muhurat ratings, and VIP Tatkal metadata."""
    assert astrologer.id is not None
    include_private = False
    if invite_code:
        invite_link = await PrivateInviteLink.find_one(
            {"invite_code": invite_code, "astrologer_id": astrologer.id, "is_active": True}
        )
        if invite_link:
            include_private = True

    windows = await _windows_for(astrologer.id, day_start, day_end, include_private=include_private)
    taken = await booked_between(astrologer.id, day_start, day_end)

    # Pre-calculate Vedic Muhurat ratings for windows
    muhurat_ratings: dict[str, dict] = {}
    for w in windows:
        cur = w.starts_at
        while cur < w.ends_at:
            time_key = cur.isoformat()
            muhurat_ratings[time_key] = calculate_slot_muhurat(cur)
            cur += timedelta(minutes=15)

    buffer_mins = getattr(astrologer.appointment, "buffer_minutes", 0) or 0
    booked_ranges: list[dict] = []
    for a in taken:
        blocked_end = a.ends_at + timedelta(minutes=buffer_mins)
        booked_ranges.append({"starts_at": a.starts_at, "ends_at": blocked_end})

    # If astrologer is currently on Brahma Pause, block the pause interval
    now = utcnow()
    if astrologer.brahma_pause_until and now < astrologer.brahma_pause_until:
        pause_start = max(day_start, astrologer.brahma_pause_activated_at or now)
        pause_end = min(day_end, astrologer.brahma_pause_until)
        if pause_start < pause_end:
            booked_ranges.append({"starts_at": pause_start, "ends_at": pause_end})

    # Two-Way Google Calendar Sync: Block external personal & doctor commitments
    gc = getattr(astrologer, "google_calendar", None)
    if gc and gc.connected and gc.sync_enabled:
        for b in getattr(gc, "busy_intervals", []):
            try:
                b_start = datetime.fromisoformat(b["starts_at"]) if isinstance(b["starts_at"], str) else b["starts_at"]
                b_end = datetime.fromisoformat(b["ends_at"]) if isinstance(b["ends_at"], str) else b["ends_at"]
                if b_start.tzinfo is None:
                    b_start = b_start.replace(tzinfo=UTC)
                if b_end.tzinfo is None:
                    b_end = b_end.replace(tzinfo=UTC)

                if b_start < day_end and b_end > day_start:
                    booked_ranges.append({
                        "starts_at": b_start,
                        "ends_at": b_end,
                        "source": "google_calendar",
                        "title": b.get("title", "Google Calendar: Busy / Private Event"),
                        "is_external": True,
                    })
            except Exception as g_err:
                logger.debug("Failed to parse google busy interval: {}", g_err)

    return {
        "windows": [
            {
                "starts_at": w.starts_at,
                "ends_at": w.ends_at,
                "is_tatkal": getattr(w, "is_tatkal", False),
                "tatkal_multiplier": getattr(w, "tatkal_multiplier", 1.5),
                "tatkal_fixed_paise": getattr(w, "tatkal_fixed_paise", None),
                "custom_title": getattr(w, "custom_title", None),
                "is_private": getattr(w, "is_private", False),
            }
            for w in windows
        ],
        "booked": booked_ranges,
        "muhurat_ratings": muhurat_ratings,
        "buffer_minutes": buffer_mins,
        "is_on_brahma_pause": bool(astrologer.brahma_pause_until and now < astrologer.brahma_pause_until),
        "brahma_pause_until": astrologer.brahma_pause_until.isoformat() if astrologer.brahma_pause_until and now < astrologer.brahma_pause_until else None,
        "brahma_pause_reason": astrologer.brahma_pause_reason if astrologer.brahma_pause_until and now < astrologer.brahma_pause_until else None,
        "google_sync": {
            "connected": bool(gc and gc.connected),
            "email": getattr(gc, "email", None),
            "sync_enabled": bool(gc and gc.sync_enabled),
            "last_synced_at": gc.last_synced_at.isoformat() if gc and gc.last_synced_at else None,
        },
        "auspicious_transit": get_auspicious_transit_for_date(day_start.date()),
    }


def _find_covering_window(
    windows: list[AvailabilityWindow], starts_at: datetime, ends_at: datetime
) -> AvailabilityWindow | None:
    for w in windows:
        if w.starts_at <= starts_at and ends_at <= w.ends_at:
            return w
    return None


def _covered_by_a_window(
    windows: list[AvailabilityWindow], starts_at: datetime, ends_at: datetime
) -> bool:
    """Is the whole booking inside one window?

    One window, not several stitched together: two adjoining windows are two
    separate stretches the astrologer offered, and a booking running across
    the join would span a gap they did not agree to.
    """
    return _find_covering_window(windows, starts_at, ends_at) is not None


# ------------------------------------------------------------------ booking
_USER_BOOKING_LOCKS: dict[str, asyncio.Lock] = {}
_USER_LOCKS_MUTEX = asyncio.Lock()


async def _get_user_booking_lock(user_id: Any) -> asyncio.Lock:
    uid_str = str(user_id)
    async with _USER_LOCKS_MUTEX:
        if len(_USER_BOOKING_LOCKS) > 5000:
            for k in list(_USER_BOOKING_LOCKS.keys()):
                lock = _USER_BOOKING_LOCKS[k]
                if not lock.locked():
                    _USER_BOOKING_LOCKS.pop(k, None)
        if uid_str not in _USER_BOOKING_LOCKS:
            _USER_BOOKING_LOCKS[uid_str] = asyncio.Lock()
        return _USER_BOOKING_LOCKS[uid_str]


async def book(
    *,
    user: User,
    astrologer: Astrologer,
    starts_at: datetime,
    minutes: int,
    note: str | None = None,
    consultation_pillar: str | None = None,
    kundli_id: PydanticObjectId | None = None,
    birth_details: dict[str, Any] | None = None,
    invite_code: str | None = None,
    invite_passcode: str | None = None,
) -> Appointment:
    """Takes a slot, takes the deposit, and writes the booking."""
    user_lock = await _get_user_booking_lock(user.id)
    async with user_lock:
        return await _book_locked(
            user=user,
            astrologer=astrologer,
            starts_at=starts_at,
            minutes=minutes,
            note=note,
            consultation_pillar=consultation_pillar,
            kundli_id=kundli_id,
            birth_details=birth_details,
            invite_code=invite_code,
            invite_passcode=invite_passcode,
        )


async def _book_locked(
    *,
    user: User,
    astrologer: Astrologer,
    starts_at: datetime,
    minutes: int,
    note: str | None = None,
    consultation_pillar: str | None = None,
    kundli_id: PydanticObjectId | None = None,
    birth_details: dict[str, Any] | None = None,
    invite_code: str | None = None,
    invite_passcode: str | None = None,
) -> Appointment:
    from app.services import settings as settings_service
    from app.services import wallet as wallet_service

    assert astrologer.id is not None
    platform = await settings_service.get_settings()
    card = astrologer.appointment

    # --- is this even on offer? ------------------------------------------
    if not card.enabled or card.price_paise <= 0:
        raise BadRequestError(
            "This astrologer is not taking appointments.",
            error_code="appointments_not_offered",
        )

    starts_at = starts_at.astimezone(UTC).replace(second=0, microsecond=0)
    if not _aligned(starts_at):
        raise BadRequestError(
            f"Pick a time on a {SLOT_MINUTES}-minute mark.", error_code="unaligned_start"
        )

    if minutes % SLOT_MINUTES:
        raise BadRequestError(
            f"Book in multiples of {SLOT_MINUTES} minutes.", error_code="unaligned_length"
        )
    if not platform.min_appointment_minutes <= minutes <= platform.max_appointment_minutes:
        raise BadRequestError(
            f"Appointments run from {platform.min_appointment_minutes} to "
            f"{platform.max_appointment_minutes} minutes.",
            error_code="bad_duration",
        )

    now = utcnow()
    if starts_at <= now:
        raise BadRequestError("That time has passed.", error_code="in_the_past")
    horizon = now + timedelta(days=platform.appointment_booking_days_ahead)
    if starts_at > horizon:
        raise BadRequestError(
            f"Bookings open {platform.appointment_booking_days_ahead} days ahead.",
            error_code="beyond_horizon",
        )

    # --- Client Screening & Abuse Shield: Blacklist enforcement -------
    if user.id in (getattr(astrologer, "blacklisted_user_ids", None) or []):
        raise BadRequestError(
            "This astrologer is currently unavailable for your account. Please select another certified astrologer from our directory.",
            error_code="client_blacklisted",
        )

    # --- Rule 1: Single active appointment limit -------------------------
    active_count = await Appointment.find(
        And(
            Appointment.user_id == user.id,
            In(Appointment.status, [AppointmentStatus.BOOKED]),
            GTE(Appointment.ends_at, now),
        )
    ).count()
    if active_count > 0:
        raise BadRequestError(
            "You already have an active appointment booked. Astra policy permits only one active appointment at a time.",
            error_code="single_appointment_limit",
        )

    buffer_mins = getattr(card, "buffer_minutes", 0) or 0
    ends_at = starts_at + timedelta(minutes=minutes)
    needed_ends_at = ends_at + timedelta(minutes=buffer_mins)

    windows = await _windows_for(astrologer.id, starts_at, needed_ends_at, include_private=True)
    covering_window = _find_covering_window(windows, starts_at, needed_ends_at)
    if not covering_window:
        raise BadRequestError(
            "The astrologer is not available for that whole time (including required meditation buffer).",
            error_code="outside_availability",
        )

    # --- Two-Way Google Calendar Conflict Check ---
    gc = getattr(astrologer, "google_calendar", None)
    if gc and gc.connected and gc.sync_enabled:
        for b in getattr(gc, "busy_intervals", []):
            try:
                b_start = datetime.fromisoformat(b["starts_at"]) if isinstance(b["starts_at"], str) else b["starts_at"]
                b_end = datetime.fromisoformat(b["ends_at"]) if isinstance(b["ends_at"], str) else b["ends_at"]
                if b_start.tzinfo is None:
                    b_start = b_start.replace(tzinfo=UTC)
                if b_end.tzinfo is None:
                    b_end = b_end.replace(tzinfo=UTC)

                if starts_at < b_end and needed_ends_at > b_start:
                    raise BadRequestError(
                        "The astrologer has an external commitment scheduled on their Google Calendar during this time. Please select another slot.",
                        error_code="google_calendar_busy_conflict",
                    )
            except BadRequestError:
                raise
            except Exception as g_err:
                logger.debug("Failed checking google busy collision: {}", g_err)

    # --- Private Link Validation ---
    invite_link: PrivateInviteLink | None = None
    if invite_code:
        invite_link = await PrivateInviteLink.find_one(
            {"invite_code": invite_code, "astrologer_id": astrologer.id, "is_active": True}
        )
        if not invite_link:
            raise BadRequestError(
                "Invalid or expired private invitation link.",
                error_code="invalid_invite_link",
            )
        if invite_link.expires_at and now > invite_link.expires_at:
            raise BadRequestError(
                "This private invitation link has expired.",
                error_code="invite_link_expired",
            )
        if invite_link.uses_count >= invite_link.max_uses:
            raise BadRequestError(
                "This private invitation link has reached its maximum allowed uses.",
                error_code="invite_link_exhausted",
            )
        if invite_link.has_passcode and invite_link.passcode_hash:
            if not invite_passcode:
                raise BadRequestError(
                    "This private consultation requires a passcode.",
                    error_code="passcode_required",
                )
            from app.core.security import verify_password

            if not verify_password(invite_passcode, invite_link.passcode_hash):
                raise BadRequestError(
                    "Incorrect passcode for private consultation.",
                    error_code="invalid_passcode",
                )
    elif getattr(covering_window, "is_private", False):
        raise BadRequestError(
            "This slot is reserved for private invitation only. Please use your private booking link.",
            error_code="private_slot_restricted",
        )

    # --- the money, worked out before anything is claimed -----------------
    is_tatkal_slot = bool(
        getattr(covering_window, "is_tatkal", False) or (invite_link and invite_link.is_tatkal)
    )
    tatkal_multiplier = (
        getattr(covering_window, "tatkal_multiplier", None)
        if getattr(covering_window, "is_tatkal", False)
        else None
    )
    tatkal_fixed_paise = (
        getattr(covering_window, "tatkal_fixed_paise", None)
        if getattr(covering_window, "is_tatkal", False)
        else None
    )
    custom_price_paise = getattr(invite_link, "custom_price_paise", None) if invite_link else None
    discount_percent = getattr(invite_link, "discount_percent", None) if invite_link else None

    standard_price_paise = price_for(card, minutes)
    price_paise = price_for(
        card,
        minutes,
        tatkal_multiplier=tatkal_multiplier,
        tatkal_fixed_paise=tatkal_fixed_paise,
        custom_price_paise=custom_price_paise,
        discount_percent=discount_percent,
    )
    tatkal_premium_paise = max(0, price_paise - standard_price_paise) if is_tatkal_slot else 0
    tatkal_premium_coins = coins_for_paise(tatkal_premium_paise, platform.coins_per_rupee)

    commission = platform.appointment_commission_percent
    deposit_paise = deposit_for(price_paise, commission)
    deposit_coins = coins_for_paise(deposit_paise, platform.coins_per_rupee)
    balance_due_paise = max(price_paise - deposit_paise, 0)
    balance_due_coins = coins_for_paise(balance_due_paise, platform.coins_per_rupee)
    total_coins_needed = deposit_coins + balance_due_coins

    # --- Rule 2: Verify user can afford the FULL session fee --------------
    user_wallet = await wallet_service.get_or_create_wallet(user.id)
    spendable = user_wallet.available_coins
    if spendable < total_coins_needed:
        raise BadRequestError(
            f"Insufficient wallet balance. Total consultation fee is {total_coins_needed} coins "
            f"({deposit_coins} booking deposit + {balance_due_coins} session reserve). "
            f"Your spendable balance is {spendable} coins. Please recharge and try again.",
            error_code="insufficient_balance",
            details={
                "total_coins_needed": total_coins_needed,
                "deposit_coins": deposit_coins,
                "balance_due_coins": balance_due_coins,
                "available_coins": spendable,
                "balance_coins": user_wallet.balance_coins,
            },
        )

    # Calculate Vedic Muhurat
    muhurat_data = calculate_slot_muhurat(starts_at)
    muhurat_type = muhurat_data.get("quality", "normal")

    # Calculate Cosmic Synergy / Planetary Resonance
    cosmic_synergy_score = 88
    try:
        from app.services.cosmic_intelligence import calculate_cosmic_synergy
        synergy = calculate_cosmic_synergy(birth_details, astrologer.id)
        cosmic_synergy_score = synergy.get("score", 88)
    except Exception as syn_err:
        logger.debug("Synergy calculation skipped: {}", syn_err)

    # --- Brahma Pause check ----------------------------------------------
    if (
        astrologer.brahma_pause_until
        and now < astrologer.brahma_pause_until
        and starts_at < astrologer.brahma_pause_until
    ):
        pause_str = astrologer.brahma_pause_until.strftime("%I:%M %p, %d %b")
        reason_str = f" Reason: {astrologer.brahma_pause_reason}." if astrologer.brahma_pause_reason else ""
        raise BadRequestError(
            f"This astrologer is currently on Brahma Pause (emergency break) until {pause_str}.{reason_str} "
            "Please select a slot after the pause period.",
            error_code="astrologer_on_brahma_pause",
        )

    # --- claim the time ---------------------------------------------------
    # Before the wallet, because a clash is the ordinary failure and nobody's
    # money should move for it.
    appointment_id = PydanticObjectId()
    claimed: list[AppointmentSlot] = []
    try:
        buffer_mins = getattr(card, "buffer_minutes", 0) or 0
        total_blocked_minutes = minutes + buffer_mins
        for moment in slot_starts(starts_at, total_blocked_minutes):
            slot = AppointmentSlot(
                astrologer_id=astrologer.id,
                appointment_id=appointment_id,
                starts_at=moment,
            )
            await slot.insert()
            claimed.append(slot)
    except DuplicateKeyError:
        await _release(claimed)
        raise ConflictError(
            "Someone has just booked part of that time. Please pick another slot.",
            error_code="slot_taken",
        )
    except Exception:
        await _release(claimed)
        raise

    # --- the deposit debit & balance escrow hold --------------------------
    cancellation_window = getattr(card, "cancellation_window_minutes", 30) or 30
    cancel_deadline = now + timedelta(minutes=cancellation_window)
    deposit_debited = False
    balance_held = False

    try:
        if deposit_coins > 0:
            await wallet_service.debit(
                user_id=user.id,
                amount_coins=deposit_coins,
                reason=TransactionReason.APPOINTMENT_DEPOSIT,
                idempotency_key=f"appointment:{appointment_id}:deposit",
                note=f"Appointment deposit with {astrologer.display_name}",
            )
            deposit_debited = True

        if balance_due_coins > 0:
            await wallet_service.hold_coins(
                user_id=user.id,
                amount_coins=balance_due_coins,
                appointment_id=appointment_id,
                note=f"Reserved balance for appointment with {astrologer.display_name}",
            )
            balance_held = True
    except Exception:
        # Rollback money and slots if anything fails
        if deposit_debited:
            try:
                await wallet_service.credit(
                    user_id=user.id,
                    amount_coins=deposit_coins,
                    reason=TransactionReason.REFUND,
                    idempotency_key=f"appointment:{appointment_id}:deposit_rollback",
                    note="Rollback failed booking deposit",
                )
            except Exception as r_err:
                logger.error("Failed to credit deposit on abort: {}", r_err)
        if balance_held:
            try:
                await wallet_service.release_held_coins(
                    user_id=user.id,
                    amount_coins=balance_due_coins,
                    appointment_id=appointment_id,
                )
            except Exception as r_err:
                logger.error("Failed to release held coins on abort: {}", r_err)
        await _release(claimed)
        raise

    appointment = Appointment(
        id=appointment_id,
        astrologer_id=astrologer.id,
        astrologer_user_id=astrologer.user_id,
        user_id=user.id,
        starts_at=starts_at,
        ends_at=ends_at,
        minutes=minutes,
        price_paise=price_paise,
        commission_percent=commission,
        deposit_paise=deposit_paise,
        deposit_coins=deposit_coins,
        coins_per_rupee=platform.coins_per_rupee,
        balance_due_paise=balance_due_paise,
        held_coins=balance_due_coins,
        held_status="held" if balance_due_coins > 0 else "none",
        cancellation_window_minutes=cancellation_window,
        cancel_deadline=cancel_deadline,
        user_note=note,
        consultation_pillar=consultation_pillar,
        kundli_id=kundli_id,
        birth_details=birth_details,
        muhurat_type=muhurat_type,
        cosmic_synergy_score=cosmic_synergy_score,
        is_tatkal=is_tatkal_slot,
        tatkal_multiplier=tatkal_multiplier,
        tatkal_premium_paise=tatkal_premium_paise,
        tatkal_premium_coins=tatkal_premium_coins,
        is_private=bool(invite_link or getattr(covering_window, "is_private", False)),
        invite_code=invite_code if invite_link else None,
    )
    try:
        await appointment.insert()
        if invite_link:
            invite_link.uses_count += 1
            if invite_link.uses_count >= invite_link.max_uses:
                invite_link.is_active = False
            await invite_link.save()
    except DuplicateKeyError:
        # If user concurrently attempted to book a second appointment
        if deposit_debited:
            try:
                await wallet_service.credit(
                    user_id=user.id,
                    amount_coins=deposit_coins,
                    reason=TransactionReason.REFUND,
                    idempotency_key=f"appointment:{appointment_id}:duplicate_deposit_rollback",
                    note="Rollback duplicate booking deposit",
                )
            except Exception as r_err:
                logger.error("Failed to credit deposit on duplicate abort: {}", r_err)
        if balance_held:
            try:
                await wallet_service.release_held_coins(
                    user_id=user.id,
                    amount_coins=balance_due_coins,
                    appointment_id=appointment_id,
                )
            except Exception as r_err:
                logger.error("Failed to release held coins on duplicate abort: {}", r_err)
        await _release(claimed)
        raise BadRequestError(
            "You already have an active appointment booked. Astra policy permits only one active appointment at a time.",
            error_code="single_appointment_limit",
        )
    except Exception:
        # Rollback money and slots if anything fails during appointment creation
        if deposit_debited:
            try:
                await wallet_service.credit(
                    user_id=user.id,
                    amount_coins=deposit_coins,
                    reason=TransactionReason.REFUND,
                    idempotency_key=f"appointment:{appointment_id}:deposit_rollback",
                    note="Rollback failed booking deposit",
                )
            except Exception as r_err:
                logger.error("Failed to credit deposit on abort: {}", r_err)
        if balance_held:
            try:
                await wallet_service.release_held_coins(
                    user_id=user.id,
                    amount_coins=balance_due_coins,
                    appointment_id=appointment_id,
                )
            except Exception as r_err:
                logger.error("Failed to release held coins on abort: {}", r_err)
        await _release(claimed)
        raise

    logger.info(
        "Appointment {} booked: {} with {} for {} min, deposit {} coins",
        appointment_id,
        user.email,
        astrologer.display_name,
        minutes,
        deposit_coins,
    )
    await _notify(appointment)

    # AI Pre-Flight Cosmic Dossier: Generate immediately upon booking so astrologer has it ready
    try:
        from app.services.cosmic_intelligence import generate_preflight_dossier
        await generate_preflight_dossier(appointment)
    except Exception as exc:
        logger.warning("Auto-generation of pre-flight dossier on booking skipped for {}: {}", appointment_id, exc)

    # Two-Way Google Calendar Sync: Push booking to astrologer's connected Google Calendar
    try:
        from app.services import google_calendar as gcal_service
        await gcal_service.push_appointment_to_google(appointment, astrologer)
    except Exception as g_push_err:
        logger.warning("Could not push appointment {} to Google Calendar: {}", appointment_id, g_push_err)

    # Realtime notification to both client and astrologer
    try:
        from app.services import realtime
        appointment_data = {
            "id": str(appointment_id),
            "status": "booked",
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "minutes": minutes,
            "consultation_pillar": consultation_pillar,
            "muhurat_type": muhurat_type,
            "client_name": getattr(user, "display_name", None) or getattr(user, "name", None) or "Client",
        }
        await realtime.publish_appointment_event(
            user.id, astrologer.user_id, "booked", appointment_data
        )
    except Exception as exc:
        logger.debug("Realtime booking publish skipped: {}", exc)

    return appointment


async def _release(slots: list[AppointmentSlot]) -> None:
    for slot in slots:
        try:
            await slot.delete()
        except Exception as exc:  # noqa: BLE001 - best effort; see release_orphans
            logger.error("Could not release slot {}: {}", slot.starts_at, exc)


async def release_orphans() -> int:
    """Frees time claimed by bookings that do not exist.

    Only reachable if a release failed midway through an aborted booking. Left
    alone, those units would block an astrologer's calendar for ever with
    nothing to show for it.
    """
    orphans = 0
    async for slot in AppointmentSlot.find_all():
        if await Appointment.get(slot.appointment_id) is None:
            await slot.delete()
            orphans += 1
    if orphans:
        logger.warning("Released {} orphaned appointment slot(s).", orphans)
    return orphans


# --------------------------------------------------------------- cancelling
async def cancel(
    *, appointment: Appointment, by: User, reason: str | None = None
) -> Appointment:
    """Cancels appointment according to client grace period and refund rules."""
    from app.services import wallet as wallet_service

    if appointment.status is not AppointmentStatus.BOOKED:
        raise BadRequestError(
            "This appointment is not open.", error_code="appointment_not_open"
        )
    if by.id not in (appointment.user_id, appointment.astrologer_user_id):
        if getattr(by, "role", None) != "admin":
            raise ForbiddenError("This is not your appointment.", error_code="not_yours")

    now = utcnow()
    is_client = by.id == appointment.user_id

    # If client cancels, verify session has not started and grace period is active (Rule 5)
    if is_client:
        if now >= appointment.starts_at:
            raise BadRequestError(
                "The scheduled consultation has already started and can no longer be cancelled by the client.",
                error_code="session_already_started",
            )
        window_mins = getattr(appointment, "cancellation_window_minutes", 30) or 30
        deadline = appointment.cancel_deadline or (
            appointment.created_at + timedelta(minutes=window_mins)
        )
        if now > deadline:
            raise BadRequestError(
                f"The cancellation window of {window_mins} minutes has expired. "
                "This appointment can no longer be cancelled by the client.",
                error_code="cancellation_window_expired",
            )
    elif getattr(by, "role", None) != "admin" and now > appointment.ends_at:
        raise BadRequestError(
            "This appointment has already concluded and cannot be cancelled by the astrologer. Please mark it as completed.",
            error_code="session_already_concluded",
        )

    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = now
    appointment.cancelled_by = by.id
    appointment.cancel_reason = reason
    await appointment.save()

    assert appointment.id is not None
    await AppointmentSlot.find(
        AppointmentSlot.appointment_id == appointment.id
    ).delete()

    # --- Handle Escrow and Refunds (Rules 3 & 4) ---
    if is_client:
        # Rule 3: Client cancelled voluntarily (within grace window)
        # - Deposit is NOT returned.
        # - Blocked balance coins are RELEASED back to user's spendable wallet.
        if getattr(appointment, "held_coins", 0) > 0 and getattr(appointment, "held_status", "") == "held":
            try:
                await wallet_service.release_held_coins(
                    user_id=appointment.user_id,
                    amount_coins=appointment.held_coins,
                    appointment_id=appointment.id,
                )
                appointment.held_status = "released"
                await appointment.save()
                logger.info(
                    "User cancelled: released {} held coins for appointment {}",
                    appointment.held_coins,
                    appointment.id,
                )
            except Exception as exc:
                logger.error("Failed to release held coins on user cancel: {}", exc)
    else:
        # Rule 4: Astrologer / Admin cancelled
        # - Blocked balance coins are RELEASED back to user.
        # - 100% of upfront deposit is REFUNDED to user's wallet. User loses 0 coins!
        if getattr(appointment, "held_coins", 0) > 0 and getattr(appointment, "held_status", "") == "held":
            try:
                await wallet_service.release_held_coins(
                    user_id=appointment.user_id,
                    amount_coins=appointment.held_coins,
                    appointment_id=appointment.id,
                )
                appointment.held_status = "released"
            except Exception as exc:
                logger.error("Failed to release held coins on provider cancel: {}", exc)

        if appointment.deposit_coins > 0:
            try:
                await wallet_service.credit(
                    user_id=appointment.user_id,
                    amount_coins=appointment.deposit_coins,
                    reason=TransactionReason.REFUND,
                    idempotency_key=f"appointment:{appointment.id}:provider_cancel_refund",
                    note=f"Full refund for appointment cancelled by astrologer ({reason or 'Session unavailable'})",
                )
                logger.info(
                    "Provider cancelled: 100% refunded {} deposit coins to user {}",
                    appointment.deposit_coins,
                    appointment.user_id,
                )
            except Exception as refund_err:
                logger.error(
                    "Failed to auto-refund deposit coins for appointment {}: {}",
                    appointment.id,
                    refund_err,
                )

        await appointment.save()

    logger.info("Appointment {} cancelled by {}", appointment.id, by.email)
    await _notify(appointment)

    # Notify seekers waiting in Cosmic Standby Queue
    try:
        from app.services.cosmic_intelligence import notify_standby_waitlist
        await notify_standby_waitlist(appointment)
    except Exception as standby_err:
        logger.error("Standby queue notification failed: {}", standby_err)

    # Realtime notification to both client and astrologer
    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "cancelled",
            {
                "id": str(appointment.id),
                "status": "cancelled",
                "cancel_reason": reason,
            },
        )
    except Exception as exc:
        logger.debug("Realtime cancel publish skipped: {}", exc)

    # Two-Way Google Calendar Sync: Delete synced event from Google Calendar
    if getattr(appointment, "google_calendar_event_id", None):
        try:
            from app.services import google_calendar as gcal_service
            astro = await Astrologer.get(appointment.astrologer_id)
            if astro:
                await gcal_service.delete_google_event(appointment, astro)
        except Exception as g_del_err:
            logger.warning("Could not delete Google Calendar event for {}: {}", appointment.id, g_del_err)

    return appointment


async def cancel_active_for_astrologer(
    astrologer_id: PydanticObjectId,
    by: User,
    reason: str = "Astrologer account suspended by administration",
) -> int:
    """Cancels all future active bookings for an astrologer, releasing holds and 100% refunding deposits."""
    now = utcnow()
    active_bookings = await Appointment.find({
        "astrologer_id": astrologer_id,
        "status": AppointmentStatus.BOOKED,
        "ends_at": {"$gte": now},
    }).to_list()

    cancelled_count = 0
    for apt in active_bookings:
        try:
            await cancel(appointment=apt, by=by, reason=reason)
            cancelled_count += 1
        except Exception as exc:
            logger.error("Error auto-cancelling appointment {} during astrologer suspension: {}", apt.id, exc)

    try:
        await AppointmentSlot.find({
            "astrologer_id": astrologer_id,
            "starts_at": {"$gte": now},
        }).delete()
    except Exception as exc:
        logger.error("Error clearing future slots for suspended astrologer: {}", exc)

    return cancelled_count


# -------------------------------------------------------------- completing
async def complete(
    *, appointment: Appointment, by: User
) -> Appointment:
    """Marks appointment completed, captures held escrow coins and notifies parties."""
    from app.services import wallet as wallet_service

    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError(
            "This appointment is not open for completion.",
            error_code="appointment_not_open",
        )
    if by.id not in (appointment.astrologer_user_id, appointment.user_id):
        if getattr(by, "role", None) != "admin":
            raise ForbiddenError("Not authorized to complete this appointment.")

    now = utcnow()
    if now < appointment.starts_at:
        raise BadRequestError(
            "Cannot complete a session before it starts.",
            error_code="premature_completion",
        )

    appointment.status = AppointmentStatus.COMPLETED
    appointment.completed_at = now

    # Rule 2: Capture held balance coins
    if getattr(appointment, "held_coins", 0) > 0 and getattr(appointment, "held_status", "") == "held":
        try:
            await wallet_service.capture_held_coins(
                user_id=appointment.user_id,
                amount_coins=appointment.held_coins,
                appointment_id=appointment.id,
                astrologer_user_id=appointment.astrologer_user_id,
                note="Consultation session balance completed",
            )
            appointment.held_status = "captured"
        except Exception as exc:
            logger.error("Failed to capture held coins for appointment {}: {}", appointment.id, exc)

    # Record appointment earnings in astrologer's ledger
    try:
        await record_appointment_earning(appointment)
    except Exception as exc:
        logger.error("Failed to record earnings for appointment {}: {}", appointment.id, exc)

    # Generate consecrated Divya Paramarsha certificate
    try:
        from app.services.cosmic_intelligence import generate_divya_paramarsha_certificate_data
        astrologer_prof = await Astrologer.get(appointment.astrologer_id)
        client_user = await User.get(appointment.user_id)
        if astrologer_prof and client_user:
            appointment.certificate_data = generate_divya_paramarsha_certificate_data(
                appointment, astrologer_prof, client_user
            )
            # Auto-initialize Complimentary Follow-up Window if enabled in astrologer profile
            if getattr(getattr(astrologer_prof, "appointment", None), "follow_up_enabled", True):
                card = astrologer_prof.appointment
                window_days = getattr(card, "follow_up_window_days", 7) or 7
                max_messages = getattr(card, "follow_up_max_messages", 3) or 3
                appointment.follow_up_pass_enabled = True
                appointment.follow_up_window_days = window_days
                appointment.follow_up_expires_at = utcnow() + timedelta(days=window_days)
                appointment.follow_up_max_messages = max_messages
                appointment.follow_up_granted_at = utcnow()
    except Exception as cert_err:
        logger.error("Failed to generate Divya Paramarsha certificate: {}", cert_err)

    await appointment.save()
    logger.info("Appointment {} marked completed and escrow captured", appointment.id)

    # Realtime notification
    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "completed",
            {
                "id": str(appointment.id),
                "status": "completed",
            },
        )
    except Exception as exc:
        logger.debug("Realtime complete publish skipped: {}", exc)

    return appointment


async def record_appointment_earning(appointment: Appointment) -> None:
    """Creates a consolidated EarningEntry for a completed appointment.

    Guarantees the astrologer is credited for the appointment in their
    earnings ledger, and the platform commission is recorded.
    """
    from app.models.earning import EarningEntry
    from app.models.enums import ConsultationMode

    existing = await EarningEntry.find_one({"session_id": appointment.id})
    if existing:
        return

    gross_paise = appointment.price_paise or 0
    if gross_paise <= 0:
        return

    commission_percent = getattr(appointment, "commission_percent", 0.0) or 0.0
    commission_paise = round(gross_paise * commission_percent / 100)
    earning_paise = max(0, gross_paise - commission_paise)

    deposit_coins = getattr(appointment, "deposit_coins", 0) or 0
    held_coins = getattr(appointment, "held_coins", 0) or 0
    total_coins = deposit_coins + held_coins
    if total_coins <= 0:
        total_coins = max(1, gross_paise // 100)

    now = appointment.completed_at or utcnow()
    await EarningEntry(
        astrologer_id=appointment.astrologer_id,
        astrologer_user_id=appointment.astrologer_user_id,
        user_id=appointment.user_id,
        mode=ConsultationMode.APPOINTMENT,
        session_id=appointment.id,
        minute_index=max(1, appointment.minutes),
        coins_charged=total_coins,
        gross_paise=gross_paise,
        commission_percent=commission_percent,
        commission_paise=commission_paise,
        earning_paise=earning_paise,
        created_at=now,
    ).insert()
    logger.info(
        "Created EarningEntry for appointment {}: gross={} paise, astrologer_earned={} paise",
        appointment.id,
        gross_paise,
        earning_paise,
    )


async def backfill_completed_appointment_earnings(
    astrologer_user_id: PydanticObjectId | None = None,
) -> int:
    """Backfills any completed appointments that may be missing an EarningEntry."""
    from app.models.earning import EarningEntry
    from app.models.enums import AppointmentStatus

    q: dict[str, Any] = {"status": AppointmentStatus.COMPLETED}
    if astrologer_user_id:
        q["astrologer_user_id"] = astrologer_user_id

    completed_appts = await Appointment.find(q).to_list()
    count = 0
    for appt in completed_appts:
        existing = await EarningEntry.find_one({"session_id": appt.id})
        if not existing:
            try:
                await record_appointment_earning(appt)
                count += 1
            except Exception as e:
                logger.error("Failed to backfill appointment earning {}: {}", appt.id, e)
    return count


# ------------------------------------------------------------------ prescription
async def update_prescription(
    *,
    appointment: Appointment,
    astrologer_user_id: PydanticObjectId,
    prescription_data: dict,
) -> Appointment:
    """Saves the astrologer's sacred prescription and pushes it to client in realtime."""
    if appointment.astrologer_user_id != astrologer_user_id:
        raise ForbiddenError(
            "Only the consulting astrologer can write a prescription.",
            error_code="not_consulting_astrologer",
        )

    appointment.prescription = {
        **prescription_data,
        "updated_at": utcnow().isoformat(),
    }
    await appointment.save()

    # Automatically generate or refresh Divya Paramarsha Certificate
    try:
        from app.models.astrologer import Astrologer
        from app.models.user import User
        from app.services.cosmic_intelligence import generate_divya_paramarsha_certificate_data

        astro = await Astrologer.get(appointment.astrologer_id)
        client_u = await User.get(appointment.user_id)
        if astro and client_u:
            appointment.certificate_data = generate_divya_paramarsha_certificate_data(
                appointment, astro, client_u
            )
            await appointment.save()
    except Exception as exc:
        logger.warning("Could not auto-generate certificate data on prescription update: {}", exc)

    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "prescription_updated",
            {
                "id": str(appointment.id),
                "prescription": appointment.prescription,
                "certificate_data": appointment.certificate_data,
            },
        )
    except Exception as exc:
        logger.debug("Realtime prescription publish skipped: {}", exc)

    return appointment


# ------------------------------------------------------------- private vault notes
async def update_private_notes(
    *,
    appointment: Appointment,
    astrologer_user_id: PydanticObjectId,
    notes: str,
) -> Appointment:
    """Saves the astrologer's confidential dossier notes (strictly hidden from seeker)."""
    if appointment.astrologer_user_id != astrologer_user_id:
        raise ForbiddenError(
            "Only the consulting astrologer can edit confidential vault notes.",
            error_code="not_consulting_astrologer",
        )

    appointment.astrologer_private_notes = notes.strip() if notes and notes.strip() else None
    appointment.astrologer_private_notes_updated_at = utcnow()
    await appointment.save()
    return appointment


# ------------------------------------------------------------------ reading
async def get(appointment_id: PydanticObjectId) -> Appointment:
    appointment = await Appointment.get(appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.", error_code="appointment_not_found")
    return appointment


def may_see(appointment: Appointment, user: User) -> bool:
    return user.id in (appointment.user_id, appointment.astrologer_user_id)


async def for_user(user_id: PydanticObjectId, *, upcoming_only: bool = False):
    query = [Appointment.user_id == user_id]
    if upcoming_only:
        query.append(GTE(Appointment.ends_at, utcnow()))
        query.append(In(Appointment.status, [AppointmentStatus.BOOKED]))
    return await Appointment.find(And(*query)).sort(+Appointment.starts_at).to_list()


async def for_astrologer(
    astrologer_user_id: PydanticObjectId, *, upcoming_only: bool = False
):
    profile = await Astrologer.find_one(Astrologer.user_id == astrologer_user_id)
    if profile and profile.id:
        astro_match = Or(
            Appointment.astrologer_user_id == astrologer_user_id,
            Appointment.astrologer_id == profile.id,
        )
    else:
        astro_match = Appointment.astrologer_user_id == astrologer_user_id

    query = [astro_match]
    if upcoming_only:
        query.append(GTE(Appointment.ends_at, utcnow()))
        query.append(In(Appointment.status, [AppointmentStatus.BOOKED]))
        return await Appointment.find(And(*query)).sort(+Appointment.starts_at).to_list()
    return await Appointment.find(And(*query)).sort(-Appointment.starts_at).to_list()


async def _notify(appointment: Appointment) -> None:
    """Tells both sides their calendar moved. Never fails the booking."""
    try:
        from app.services import realtime

        payload = {
            "type": "appointment",
            "data": {
                "id": str(appointment.id),
                "status": appointment.status.value,
                "starts_at": appointment.starts_at.isoformat(),
                "ends_at": appointment.ends_at.isoformat(),
                "minutes": appointment.minutes,
            },
        }
        for who in (appointment.user_id, appointment.astrologer_user_id):
            await realtime.publish_chat(who, payload)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Appointment push skipped: {}", exc)


async def reschedule(
    *,
    appointment: Appointment,
    by: User,
    new_starts_at: datetime,
    reason: str | None = None,
) -> Appointment:
    """Astrologer courtesy reschedule: 1-time free reschedule to another open window."""
    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError(
            "Only booked appointments can be rescheduled.",
            error_code="appointment_not_open",
        )
    if by.id != appointment.astrologer_user_id and getattr(by, "role", None) != "admin":
        raise ForbiddenError(
            "Only the consulting astrologer or admin can grant a courtesy reschedule.",
            error_code="not_consulting_astrologer",
        )

    # 1. Enforce 1-time courtesy reschedule limit (Rule: Option B)
    if getattr(appointment, "rescheduled_count", 0) >= 1:
        raise BadRequestError(
            "This appointment has already been rescheduled once. Astra policy permits only one courtesy reschedule per booking.",
            error_code="reschedule_limit_reached",
        )

    # 2. Validate timing and alignment
    now = utcnow()
    new_starts_at = new_starts_at.astimezone(UTC).replace(second=0, microsecond=0)
    if not _aligned(new_starts_at):
        raise BadRequestError(
            f"Pick a time on a {SLOT_MINUTES}-minute mark.", error_code="unaligned_start"
        )
    if new_starts_at <= now:
        raise BadRequestError("New appointment time must be in the future.", error_code="in_the_past")

    platform = await settings_service.get_platform_settings()
    horizon = now + timedelta(days=platform.appointment_booking_days_ahead)
    if new_starts_at > horizon:
        raise BadRequestError(
            f"Bookings open {platform.appointment_booking_days_ahead} days ahead.",
            error_code="beyond_horizon",
        )

    astro_profile = await Astrologer.get(appointment.astrologer_id)
    buffer_mins = getattr(getattr(astro_profile, "appointment", None), "buffer_minutes", 0) or 0
    new_ends_at = new_starts_at + timedelta(minutes=appointment.minutes)
    needed_ends_at = new_ends_at + timedelta(minutes=buffer_mins)

    # 3. Verify target falls inside an open AvailabilityWindow (including meditation buffer)
    windows = await _windows_for(appointment.astrologer_id, new_starts_at, needed_ends_at)
    if not _covered_by_a_window(windows, new_starts_at, needed_ends_at):
        raise BadRequestError(
            "The selected slot is outside your availability windows (including required meditation buffer). Please pick a time within your open schedule.",
            error_code="outside_availability",
        )

    # 4. Atomic slot swap: release old slots, claim new slots
    if (
        astro_profile
        and astro_profile.brahma_pause_until
        and now < astro_profile.brahma_pause_until
        and new_starts_at < astro_profile.brahma_pause_until
    ):
        raise BadRequestError(
            "Cannot reschedule into an active Brahma Pause emergency break.",
            error_code="slot_during_brahma_pause",
        )

    old_slots = await AppointmentSlot.find(
        AppointmentSlot.appointment_id == appointment.id
    ).to_list()
    await AppointmentSlot.find(
        AppointmentSlot.appointment_id == appointment.id
    ).delete()

    total_blocked_minutes = appointment.minutes + buffer_mins

    new_claimed: list[AppointmentSlot] = []
    try:
        for moment in slot_starts(new_starts_at, total_blocked_minutes):
            slot = AppointmentSlot(
                astrologer_id=appointment.astrologer_id,
                appointment_id=appointment.id,
                starts_at=moment,
            )
            await slot.insert()
            new_claimed.append(slot)
    except DuplicateKeyError:
        # Conflict: rollback new slots and re-insert old slots
        await _release(new_claimed)
        for os in old_slots:
            try:
                await os.insert()
            except Exception:
                pass
        raise ConflictError(
            "Someone has just booked part of that time. Please pick another slot.",
            error_code="slot_taken",
        )
    except Exception:
        await _release(new_claimed)
        for os in old_slots:
            try:
                await os.insert()
            except Exception:
                pass
        raise

    # 5. Update appointment details
    appointment.previous_starts_at = appointment.starts_at
    appointment.starts_at = new_starts_at
    appointment.ends_at = new_ends_at
    appointment.rescheduled_count = getattr(appointment, "rescheduled_count", 0) + 1
    appointment.rescheduled_at = now
    appointment.reschedule_reason = reason
    appointment.reminded_at = None  # Reset reminder so 5-min prior worker alerts for new time

    # Re-evaluate Vedic Muhurat
    muhurat_data = calculate_slot_muhurat(new_starts_at)
    appointment.muhurat_type = muhurat_data.get("quality", "normal")

    await appointment.save()
    logger.info(
        "Appointment {} courtesy rescheduled by {} to {}",
        appointment.id,
        by.email,
        new_starts_at,
    )

    # Notify via email
    try:
        from app.services import email as email_service
        from app.services.email_templates import (
            appointment_rescheduled_client_email_html,
            generate_google_calendar_url,
        )
        from app.services.reminders import _format_ist_timing

        client_user = await User.get(appointment.user_id)
        astrologer_prof = await Astrologer.get(appointment.astrologer_id)
        if client_user and client_user.email and astrologer_prof:
            timing_str = _format_ist_timing(new_starts_at, new_ends_at)
            frontend_url = settings.FRONTEND_URL.rstrip("/") if settings.FRONTEND_URL else "https://astra-astrology-web.vercel.app"
            chamber_url = f"{frontend_url}/account/appointments"
            gcal_url = generate_google_calendar_url(
                title=f"Sacred Consultation with {astrologer_prof.display_name}",
                description=f"Consultation on {appointment.consultation_pillar or 'Vedic Astrology'}. Join link: {chamber_url}",
                starts_at=new_starts_at,
                ends_at=new_ends_at,
                location=chamber_url,
            )
            html = appointment_rescheduled_client_email_html(
                client_name=client_user.full_name or client_user.first_name or "Valued Client",
                astrologer_name=astrologer_prof.display_name,
                consultation_pillar=appointment.consultation_pillar or "Vedic Astrology",
                new_starts_at_str=timing_str,
                chamber_url=chamber_url,
                reason=reason,
                calendar_url=gcal_url,
            )
            await email_service.send_email(
                to=client_user.email,
                subject=f"🗓️ Appointment Rescheduled: Consultation with {astrologer_prof.display_name}",
                html=html,
            )
    except Exception as mail_err:
        logger.error("Failed to dispatch reschedule email: {}", mail_err)

    # Realtime notification
    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "rescheduled",
            {
                "id": str(appointment.id),
                "starts_at": new_starts_at.isoformat(),
                "ends_at": new_ends_at.isoformat(),
                "rescheduled_count": appointment.rescheduled_count,
            },
        )
    except Exception as exc:
        logger.debug("Realtime reschedule push skipped: {}", exc)

    return appointment


async def mark_no_show(
    *,
    appointment: Appointment,
    by: User,
    reason: str | None = None,
) -> Appointment:
    """Marks appointment as Client No-Show after astrologer waited 10-15m in chamber."""
    from app.services import wallet as wallet_service

    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError(
            "Only active booked appointments can be marked as No-Show.",
            error_code="appointment_not_open",
        )
    if by.id != appointment.astrologer_user_id and getattr(by, "role", None) != "admin":
        raise ForbiddenError(
            "Only the consulting astrologer or admin can mark a client no-show.",
            error_code="not_consulting_astrologer",
        )

    now = utcnow()
    # Check grace wait period (must wait at least 10 minutes into scheduled session)
    wait_min_time = appointment.starts_at + timedelta(minutes=10)
    if now < wait_min_time:
        raise BadRequestError(
            f"You must wait at least 10 minutes into the scheduled consultation before marking a client no-show. "
            f"Session started at {appointment.starts_at.strftime('%I:%M %p')}.",
            error_code="no_show_too_early",
        )

    appointment.status = AppointmentStatus.COMPLETED
    appointment.completed_at = now
    appointment.is_no_show = True
    appointment.no_show_marked_at = now
    appointment.no_show_wait_minutes = 15
    appointment.cancel_reason = reason or "Client did not attend consultation chamber after 15m wait."

    # Capture held coins to compensate astrologer for their reserved time
    if getattr(appointment, "held_coins", 0) > 0 and getattr(appointment, "held_status", "") == "held":
        try:
            await wallet_service.capture_held_coins(
                user_id=appointment.user_id,
                amount_coins=appointment.held_coins,
                appointment_id=appointment.id,
                astrologer_user_id=appointment.astrologer_user_id,
                note="Consultation completed (Client No-Show compensation)",
            )
            appointment.held_status = "captured"
        except Exception as exc:
            logger.error("Failed to capture held coins on no-show: {}", exc)

    # Release claimed slot so availability is cleaned
    await AppointmentSlot.find(
        AppointmentSlot.appointment_id == appointment.id
    ).delete()

    await appointment.save()
    logger.info("Appointment {} marked as Client No-Show by {}", appointment.id, by.email)

    # Email notification to client
    try:
        from app.services import email as email_service
        from app.services.email_templates import appointment_no_show_client_email_html
        from app.services.reminders import _format_ist_timing

        client_user = await User.get(appointment.user_id)
        astrologer_prof = await Astrologer.get(appointment.astrologer_id)
        if client_user and client_user.email and astrologer_prof:
            timing_str = _format_ist_timing(appointment.starts_at, appointment.ends_at)
            frontend_url = settings.FRONTEND_URL.rstrip("/") if settings.FRONTEND_URL else "https://astra-astrology-web.vercel.app"
            html = appointment_no_show_client_email_html(
                client_name=client_user.full_name or client_user.first_name or "Valued Client",
                astrologer_name=astrologer_prof.display_name,
                consultation_pillar=appointment.consultation_pillar or "Vedic Astrology",
                starts_at_str=timing_str,
                support_url=f"{frontend_url}/support",
                wait_minutes=15,
            )
            await email_service.send_email(
                to=client_user.email,
                subject=f"⚠️ Consultation Notice: Marked Missed (No-Show) with {astrologer_prof.display_name}",
                html=html,
            )
    except Exception as mail_err:
        logger.error("Failed to send no-show notification email: {}", mail_err)

    # Realtime notification
    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "no_show_marked",
            {
                "id": str(appointment.id),
                "is_no_show": True,
                "status": "completed",
            },
        )
    except Exception as exc:
        logger.debug("Realtime no-show push skipped: {}", exc)

    return appointment


# ------------------------------------------------------------- Brahma Pause
async def activate_brahma_pause(
    *,
    astrologer: Astrologer,
    duration_hours: int,
    reason: str | None = None,
) -> dict:
    """Activates Brahma Pause (emergency break), takes astrologer offline,
    identifies affected bookings, flags them, and notifies seekers with 1-click rescue choices.
    """
    from app.core.config import settings
    from app.services import email as email_service
    from app.services.email_templates import appointment_brahma_pause_client_email_html
    from app.services.reminders import _format_ist_timing
    from app.services import realtime

    now = utcnow()
    pause_until = now + timedelta(hours=duration_hours)
    astrologer.brahma_pause_until = pause_until
    astrologer.brahma_pause_reason = reason
    astrologer.brahma_pause_activated_at = now
    astrologer.availability.is_online = False
    astrologer.availability.last_seen_at = None
    await astrologer.save()

    try:
        await realtime.publish_astrologer(astrologer)
    except Exception as exc:
        logger.debug("Failed to publish astrologer offline state: {}", exc)

    # Find affected bookings
    impacted = await Appointment.find({
        "astrologer_id": astrologer.id,
        "status": AppointmentStatus.BOOKED,
        "starts_at": {"$lt": pause_until},
        "ends_at": {"$gte": now},
    }).to_list()

    affected_count = 0
    frontend_url = settings.FRONTEND_URL.rstrip("/") if settings.FRONTEND_URL else "https://astra-astrology-web.vercel.app"
    appointments_url = f"{frontend_url}/account/appointments"

    for apt in impacted:
        apt.brahma_pause_affected = True
        apt.brahma_pause_reason = reason
        apt.brahma_pause_until = pause_until
        apt.rescue_deadline = min(pause_until + timedelta(hours=24), apt.starts_at)
        await apt.save()
        affected_count += 1

        # Send email to seeker
        try:
            client_u = await User.get(apt.user_id)
            if client_u and client_u.email:
                scheduled_str = _format_ist_timing(apt.starts_at, apt.ends_at)
                pause_until_str = _format_ist_timing(pause_until, pause_until)
                html = appointment_brahma_pause_client_email_html(
                    client_name=client_u.full_name or client_u.first_name or "Valued Seeker",
                    astrologer_name=astrologer.display_name,
                    consultation_pillar=apt.consultation_pillar or "Vedic Astrology",
                    scheduled_starts_at_str=scheduled_str,
                    pause_until_str=pause_until_str,
                    reason=reason,
                    appointments_url=appointments_url,
                )
                await email_service.send_email(
                    to=client_u.email,
                    subject=f"🕊️ Important Notice: Pandit {astrologer.display_name} on Brahma Pause",
                    html=html,
                )
        except Exception as mail_err:
            logger.error("Failed to send Brahma Pause alert to seeker: {}", mail_err)

        # Realtime event
        try:
            await realtime.publish_appointment_event(
                apt.user_id,
                apt.astrologer_user_id,
                "brahma_pause_activated",
                {
                    "id": str(apt.id),
                    "brahma_pause_affected": True,
                    "pause_until": pause_until.isoformat(),
                    "reason": reason,
                },
            )
        except Exception as rt_err:
            logger.debug("Realtime Brahma Pause push skipped: {}", rt_err)

    logger.info(
        "Astrologer {} activated Brahma Pause until {} ({} impacted appointments)",
        astrologer.id,
        pause_until,
        affected_count,
    )
    return {
        "pause_until": pause_until.isoformat(),
        "affected_appointments_count": affected_count,
        "reason": reason,
    }


async def resume_brahma_pause(*, astrologer: Astrologer) -> dict:
    """Ends Brahma Pause early and restores normal availability."""
    from app.services import realtime

    astrologer.brahma_pause_until = None
    astrologer.brahma_pause_reason = None
    astrologer.brahma_pause_activated_at = None
    await astrologer.save()

    try:
        await realtime.publish_astrologer(astrologer)
    except Exception as exc:
        logger.debug("Failed to publish astrologer resume state: {}", exc)

    logger.info("Astrologer {} resumed from Brahma Pause early", astrologer.id)
    return {"message": "Brahma Pause ended successfully."}


async def handle_brahma_pause_rescue_action(
    *,
    appointment: Appointment,
    user: User,
    action: str,
    new_starts_at: datetime | None = None,
    reason: str | None = None,
) -> Appointment:
    """Processes seeker's 1-click choice during Brahma Pause:
    Option A: 'reschedule' (100% free shift to a new open slot).
    Option B: 'refund' (instant cancellation, held coins released, 100% deposit refunded).
    """
    from app.services import wallet as wallet_service

    if appointment.user_id != user.id and getattr(user, "role", None) != "admin":
        raise ForbiddenError("Not authorized to manage this appointment.")
    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError("This appointment is not active.", error_code="appointment_not_open")
    if not getattr(appointment, "brahma_pause_affected", False):
        raise BadRequestError(
            "This appointment is not currently affected by Brahma Pause.",
            error_code="not_brahma_pause_affected",
        )

    now = utcnow()

    if action == "reschedule":
        if not new_starts_at:
            raise BadRequestError("New starts at timestamp is required for reschedule.", error_code="missing_new_starts_at")

        new_starts_at = new_starts_at.astimezone(UTC).replace(second=0, microsecond=0)
        if not _aligned(new_starts_at):
            raise BadRequestError(f"Pick a time on a {SLOT_MINUTES}-minute mark.", error_code="unaligned_start")
        if new_starts_at <= now:
            raise BadRequestError("New appointment time must be in the future.", error_code="in_the_past")

        astro_profile = await Astrologer.get(appointment.astrologer_id)
        if (
            astro_profile
            and astro_profile.brahma_pause_until
            and now < astro_profile.brahma_pause_until
            and new_starts_at < astro_profile.brahma_pause_until
        ):
            raise BadRequestError("Cannot reschedule into active Brahma Pause emergency break.", error_code="slot_during_brahma_pause")

        buffer_mins = getattr(getattr(astro_profile, "appointment", None), "buffer_minutes", 0) or 0
        new_ends_at = new_starts_at + timedelta(minutes=appointment.minutes)
        needed_ends_at = new_ends_at + timedelta(minutes=buffer_mins)
        windows = await _windows_for(appointment.astrologer_id, new_starts_at, needed_ends_at)
        if not _covered_by_a_window(windows, new_starts_at, needed_ends_at):
            raise BadRequestError("Selected slot is outside the astrologer's open schedule (including required meditation buffer).", error_code="outside_availability")

        # Slot swap
        old_slots = await AppointmentSlot.find({"appointment_id": appointment.id}).to_list()
        await AppointmentSlot.find({"appointment_id": appointment.id}).delete()

        total_blocked_minutes = appointment.minutes + buffer_mins

        new_claimed: list[AppointmentSlot] = []
        try:
            for moment in slot_starts(new_starts_at, total_blocked_minutes):
                slot = AppointmentSlot(
                    astrologer_id=appointment.astrologer_id,
                    appointment_id=appointment.id,
                    starts_at=moment,
                )
                await slot.insert()
                new_claimed.append(slot)
        except DuplicateKeyError:
            await _release(new_claimed)
            for os in old_slots:
                try:
                    await os.insert()
                except Exception:
                    pass
            raise ConflictError("That slot was just taken by another seeker. Please pick another time.", error_code="slot_taken")

        appointment.previous_starts_at = appointment.starts_at
        appointment.starts_at = new_starts_at
        appointment.ends_at = new_ends_at
        appointment.brahma_pause_affected = False
        appointment.rescheduled_count = getattr(appointment, "rescheduled_count", 0) + 1
        appointment.rescheduled_at = now
        appointment.reschedule_reason = reason or "Seeker rescheduled during Brahma Pause"
        await appointment.save()

        # Realtime event
        try:
            from app.services import realtime
            await realtime.publish_appointment_event(
                appointment.user_id,
                appointment.astrologer_user_id,
                "rescheduled",
                {
                    "id": str(appointment.id),
                    "starts_at": new_starts_at.isoformat(),
                    "ends_at": new_ends_at.isoformat(),
                },
            )
        except Exception as exc:
            logger.debug("Realtime reschedule push skipped: {}", exc)

        return appointment

    elif action == "refund":
        # 100% full refund
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = now
        appointment.cancelled_by = user.id
        appointment.cancel_reason = reason or "Seeker selected 100% refund during Brahma Pause"
        appointment.brahma_pause_affected = False
        await appointment.save()

        # Delete slots
        await AppointmentSlot.find({"appointment_id": appointment.id}).delete()

        # Release held coins
        if getattr(appointment, "held_coins", 0) > 0 and getattr(appointment, "held_status", "") == "held":
            try:
                await wallet_service.release_held_coins(
                    user_id=appointment.user_id,
                    amount_coins=appointment.held_coins,
                    appointment_id=appointment.id,
                )
                appointment.held_status = "released"
                await appointment.save()
            except Exception as exc:
                logger.error("Failed to release held coins during Brahma Pause refund: {}", exc)

        # Refund deposit 100%
        if appointment.deposit_coins > 0:
            try:
                await wallet_service.credit(
                    user_id=appointment.user_id,
                    amount_coins=appointment.deposit_coins,
                    reason=TransactionReason.REFUND,
                    idempotency_key=f"appointment:{appointment.id}:brahma_pause_refund",
                    note="100% refund for consultation cancelled during Brahma Pause",
                )
            except Exception as ref_err:
                logger.error("Failed to credit deposit refund during Brahma Pause: {}", ref_err)

        # Realtime event
        try:
            from app.services import realtime
            await realtime.publish_appointment_event(
                appointment.user_id,
                appointment.astrologer_user_id,
                "cancelled",
                {
                    "id": str(appointment.id),
                    "status": "cancelled",
                    "cancel_reason": appointment.cancel_reason,
                },
            )
        except Exception as exc:
            logger.debug("Realtime cancel push skipped: {}", exc)

        return appointment
    else:
        raise BadRequestError(f"Invalid action '{action}'. Must be 'reschedule' or 'refund'.", error_code="invalid_action")


async def red_flag_appointment(
    *,
    appointment_id: PydanticObjectId,
    by: User,
    reason: str,
    notes: str | None = None,
    blacklist_client: bool = True,
    terminate_call: bool = True,
) -> Appointment:
    """Terminates session on misconduct, captures escrow fee, files an AbuseReport, and optionally blacklists client."""
    from app.models.abuse_report import AbuseReport
    from app.models.call import CallSession
    from app.models.enums import CallParty, CallStatus
    from app.services import wallet as wallet_service

    appointment = await Appointment.get(appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.", error_code="appointment_not_found")

    astrologer_prof = await Astrologer.get(appointment.astrologer_id)
    if astrologer_prof is None:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    if by.id not in (appointment.astrologer_user_id, astrologer_prof.user_id):
        if getattr(by, "role", None) != "admin":
            raise ForbiddenError("Not authorized to red-flag this appointment.")

    # 1. Update appointment abuse state
    appointment.abuse_flagged = True
    appointment.abuse_reason = reason
    appointment.abuse_flagged_at = utcnow()
    appointment.abuse_notes = notes

    # If currently booked, complete the session and capture compensation
    if appointment.status == AppointmentStatus.BOOKED:
        appointment.status = AppointmentStatus.COMPLETED
        appointment.completed_at = utcnow()

        # Release claimed slot so calendar isn't blocked
        await AppointmentSlot.find({"appointment_id": appointment.id}).delete()

        # Capture escrow coins as earned session compensation for astrologer
        if getattr(appointment, "held_coins", 0) > 0 and getattr(appointment, "held_status", "") == "held":
            try:
                await wallet_service.capture_held_coins(
                    user_id=appointment.user_id,
                    amount_coins=appointment.held_coins,
                    appointment_id=appointment.id,
                    astrologer_user_id=appointment.astrologer_user_id,
                    note=f"Consultation ended due to client policy violation: {reason}",
                )
                appointment.held_status = "captured"
            except Exception as exc:
                logger.error("Failed to capture held coins on red-flag for appointment {}: {}", appointment.id, exc)

        try:
            await record_appointment_earning(appointment)
        except Exception as exc:
            logger.error("Failed to record earnings on red-flag for appointment {}: {}", appointment.id, exc)

    await appointment.save()

    # 2. Terminate live call room if active
    if terminate_call and getattr(appointment, "call_session_id", None):
        try:
            call = await CallSession.get(appointment.call_session_id)
            if call and call.status in (CallStatus.RINGING, CallStatus.ACCEPTED, CallStatus.ACTIVE):
                call.status = CallStatus.ENDED
                call.ended_at = utcnow()
                call.ended_by = CallParty.ASTROLOGER
                call.end_reason = f"terminated_due_to_misconduct: {reason}"
                await call.save()
        except Exception as call_err:
            logger.error("Failed to terminate call session {}: {}", appointment.call_session_id, call_err)

    # 3. Add to astrologer's personal blacklist
    if blacklist_client:
        existing_blacklist = getattr(astrologer_prof, "blacklisted_user_ids", None) or []
        if appointment.user_id not in existing_blacklist:
            existing_blacklist.append(appointment.user_id)
            astrologer_prof.blacklisted_user_ids = existing_blacklist
            await astrologer_prof.save()
            logger.info("Client {} blacklisted by astrologer {}", appointment.user_id, astrologer_prof.id)

    # 4. File an official AbuseReport for platform trust & safety audit
    try:
        report = AbuseReport(
            astrologer_id=astrologer_prof.id,
            astrologer_user_id=appointment.astrologer_user_id,
            client_user_id=appointment.user_id,
            appointment_id=appointment.id,
            call_id=appointment.call_session_id,
            reason=reason,
            notes=notes,
            action_taken="blacklisted" if blacklist_client else "flagged_only",
            status="pending",
        )
        await report.save()
    except Exception as rep_err:
        logger.error("Failed to log AbuseReport: {}", rep_err)

    # 5. Realtime event
    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "abuse_flagged",
            {
                "id": str(appointment.id),
                "status": appointment.status,
                "abuse_reason": reason,
                "blacklisted": blacklist_client,
            },
        )
    except Exception as exc:
        logger.debug("Realtime abuse event push skipped: {}", exc)

    return appointment


async def get_astrologer_blacklist(
    astrologer_user: User,
) -> list[dict[str, Any]]:
    """Fetches the list of clients blacklisted by this astrologer with incident summary."""
    from app.models.abuse_report import AbuseReport

    prof = await Astrologer.find_one(Astrologer.user_id == astrologer_user.id)
    if prof is None:
        raise NotFoundError("Astrologer profile not found.", error_code="astrologer_not_found")

    blacklisted_ids = getattr(prof, "blacklisted_user_ids", None) or []
    if not blacklisted_ids:
        return []

    users = await User.find(In(User.id, blacklisted_ids)).to_list()
    user_map = {u.id: u for u in users}

    # Fetch latest abuse reports for these users by this astrologer
    reports = await AbuseReport.find(
        And(
            AbuseReport.astrologer_id == prof.id,
            In(AbuseReport.client_user_id, blacklisted_ids),
        )
    ).sort(-AbuseReport.created_at).to_list()

    report_map: dict[PydanticObjectId, AbuseReport] = {}
    report_counts: dict[PydanticObjectId, int] = {}
    for r in reports:
        report_counts[r.client_user_id] = report_counts.get(r.client_user_id, 0) + 1
        if r.client_user_id not in report_map:
            report_map[r.client_user_id] = r

    results = []
    for uid in blacklisted_ids:
        u = user_map.get(uid)
        r = report_map.get(uid)
        name = u.full_name if u else "Unknown Client"
        email_masked = (u.email[:3] + "***@" + u.email.split("@")[1]) if (u and u.email and "@" in u.email) else None
        phone_masked = (u.phone[:3] + "****" + u.phone[-3:]) if (u and u.phone and len(u.phone) >= 7) else None

        results.append({
            "user_id": str(uid),
            "name": name,
            "email_masked": email_masked,
            "phone_masked": phone_masked,
            "avatar_url": None,
            "blacklisted_at": r.created_at if r else None,
            "last_reason": r.reason if r else "Policy violation / Astrologer screening",
            "notes": r.notes if r else None,
            "total_reports": report_counts.get(uid, 1),
        })

    return results


async def unblock_astrologer_client(
    astrologer_user: User,
    client_user_id: PydanticObjectId,
) -> bool:
    """Removes a client from the astrologer's personal blacklist."""
    prof = await Astrologer.find_one(Astrologer.user_id == astrologer_user.id)
    if prof is None:
        raise NotFoundError("Astrologer profile not found.", error_code="astrologer_not_found")

    existing = getattr(prof, "blacklisted_user_ids", None) or []
    if client_user_id in existing:
        prof.blacklisted_user_ids = [uid for uid in existing if uid != client_user_id]
        await prof.save()
        logger.info("Client {} unblocked by astrologer {}", client_user_id, prof.id)
        return True
    return False


async def request_birth_time_rectification(
    *,
    appointment_id: PydanticObjectId,
    by: User,
    note: str | None = None,
) -> Appointment:
    """Astrologer requests exact birth time clarification/rectification from the client."""
    from app.services import email as email_service
    from app.services.email_templates import appointment_btr_requested_client_email_html

    appointment = await Appointment.get(appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.", error_code="appointment_not_found")

    if by.id != appointment.astrologer_user_id and getattr(by, "role", None) != "admin":
        raise ForbiddenError("Not authorized to request BTR for this appointment.")

    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError("BTR can only be requested for active booked appointments.", error_code="appointment_not_booked")

    appointment.btr_requested = True
    appointment.btr_request_note = note
    appointment.btr_requested_at = utcnow()
    appointment.btr_fulfilled = False
    await appointment.save()

    # Dispatch notification email to seeker
    try:
        client_user = await User.get(appointment.user_id)
        astrologer_prof = await Astrologer.get(appointment.astrologer_id)
        if client_user and client_user.email and astrologer_prof:
            frontend_url = settings.FRONTEND_URL.rstrip("/")
            appts_url = f"{frontend_url}/account/appointments"
            timing_str = appointment.starts_at.strftime("%d %b %Y, %I:%M %p UTC")

            html = appointment_btr_requested_client_email_html(
                client_name=client_user.full_name or "Seeker",
                astrologer_name=astrologer_prof.display_name,
                scheduled_starts_at_str=timing_str,
                astrologer_note=note,
                appointments_url=appts_url,
            )
            await email_service.send_email(
                to=client_user.email,
                subject=f"🧭 Action Needed: Exact Birth Time Verification with {astrologer_prof.display_name}",
                html=html,
            )
    except Exception as mail_err:
        logger.error("Failed to dispatch BTR email: {}", mail_err)

    # Realtime notification
    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "btr_requested",
            {
                "id": str(appointment.id),
                "btr_requested": True,
                "note": note,
            },
        )
    except Exception as exc:
        logger.debug("Realtime BTR push skipped: {}", exc)

    return appointment


async def update_birth_time_rectification(
    *,
    appointment_id: PydanticObjectId,
    by: User,
    birth_date: str,
    birth_time: str,
    birth_place: str,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone_offset: float | None = None,
    notes: str | None = None,
) -> Appointment:
    """Client submits corrected/verified exact birth time for the consultation."""
    from app.services import email as email_service
    from app.services.email_templates import appointment_btr_updated_astrologer_email_html

    appointment = await Appointment.get(appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.", error_code="appointment_not_found")

    if by.id != appointment.user_id and getattr(by, "role", None) != "admin":
        raise ForbiddenError("Not authorized to update birth details for this appointment.")

    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError("Birth details can only be updated for active bookings.", error_code="appointment_not_booked")

    existing_details = appointment.birth_details or {}
    updated_details = {
        **existing_details,
        "date_of_birth": birth_date,
        "time_of_birth": birth_time,
        "place_of_birth": birth_place,
        "latitude": latitude if latitude is not None else existing_details.get("latitude"),
        "longitude": longitude if longitude is not None else existing_details.get("longitude"),
        "timezone_offset": timezone_offset if timezone_offset is not None else existing_details.get("timezone_offset"),
        "rectified_by_client": True,
        "rectified_at": utcnow().isoformat(),
        "client_btr_notes": notes,
    }

    appointment.birth_details = updated_details
    appointment.btr_fulfilled = True
    appointment.btr_updated_at = utcnow()
    appointment.preflight_dossier = None
    await appointment.save()

    # Notify astrologer via email
    try:
        client_user = await User.get(appointment.user_id)
        astrologer_user = await User.get(appointment.astrologer_user_id)
        astrologer_prof = await Astrologer.get(appointment.astrologer_id)
        if astrologer_user and astrologer_user.email and client_user and astrologer_prof:
            admin_url = (getattr(settings, "ADMIN_URL", None) or "http://localhost:3001").rstrip("/")
            dossier_url = f"{admin_url}/appointments"
            timing_str = appointment.starts_at.strftime("%d %b %Y, %I:%M %p UTC")

            html = appointment_btr_updated_astrologer_email_html(
                astrologer_name=astrologer_prof.display_name,
                client_name=client_user.full_name or "Seeker",
                scheduled_starts_at_str=timing_str,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                client_notes=notes,
                dossier_url=dossier_url,
            )
            await email_service.send_email(
                to=astrologer_user.email,
                subject=f"🌟 Birth Time Rectified: {client_user.full_name} submitted exact birth parameters",
                html=html,
            )
    except Exception as mail_err:
        logger.error("Failed to notify astrologer of BTR update: {}", mail_err)

    # Realtime notification
    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "btr_fulfilled",
            {
                "id": str(appointment.id),
                "btr_fulfilled": True,
                "birth_details": updated_details,
            },
        )
    except Exception as exc:
        logger.debug("Realtime BTR update push skipped: {}", exc)

    return appointment


# ------------------------------------------------ in-chamber session extension
async def offer_session_extension(
    *,
    appointment: Appointment,
    by: User,
    extra_minutes: int = 10,
) -> Appointment:
    """Astrologer offers an in-chamber consultation extension (+10/15 mins)."""
    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError(
            "This appointment is not active.", error_code="appointment_not_open"
        )
    if by.id != appointment.astrologer_user_id and getattr(by, "role", None) != "admin":
        raise ForbiddenError("Only the consulting astrologer can offer a session extension.")

    astro = await Astrologer.get(appointment.astrologer_id)
    if astro is None:
        raise NotFoundError("Astrologer profile not found.", error_code="astrologer_not_found")

    # Safety Check: Schedule conflict with future appointments
    buffer_mins = getattr(getattr(astro, "appointment", None), "buffer_minutes", 0) or 0
    clash_window_start = appointment.ends_at
    clash_window_end = appointment.ends_at + timedelta(minutes=extra_minutes + buffer_mins)

    clashing_slot = await AppointmentSlot.find({
        "astrologer_id": appointment.astrologer_id,
        "appointment_id": {"$ne": appointment.id},
        "starts_at": {"$gte": clash_window_start, "$lt": clash_window_end},
    }).first_or_none()

    if clashing_slot:
        raise BadRequestError(
            f"Cannot extend: You have another consultation scheduled starting at "
            f"{clashing_slot.starts_at.strftime('%I:%M %p')}. Extension would cause a booking overlap.",
            error_code="extension_clash_with_future_booking",
        )

    # Price calculation
    extra_price_paise = price_for(astro.appointment, extra_minutes) if getattr(astro, "appointment", None) else 0
    if extra_price_paise <= 0 and appointment.minutes > 0:
        extra_price_paise = round(appointment.price_paise * extra_minutes / appointment.minutes)

    coins_per_rupee = appointment.coins_per_rupee or 1
    extra_cost_coins = coins_for_paise(extra_price_paise, coins_per_rupee)

    appointment.extension_offered = True
    appointment.extension_offered_minutes = extra_minutes
    appointment.extension_cost_paise = extra_price_paise
    appointment.extension_cost_coins = extra_cost_coins
    appointment.extension_offered_at = utcnow()
    appointment.extension_status = "pending"
    await appointment.save()

    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "extension_offered",
            {
                "appointment_id": str(appointment.id),
                "status": "pending",
                "extra_minutes": extra_minutes,
                "cost_coins": extra_cost_coins,
                "cost_paise": extra_price_paise,
                "offered_at": appointment.extension_offered_at.isoformat(),
            },
        )
    except Exception as exc:
        logger.debug("Failed to publish extension offer event: {}", exc)

    return appointment


async def handle_session_extension_action(
    *,
    appointment: Appointment,
    by: User,
    action: str,
) -> Appointment:
    """Client agrees to or declines the in-chamber extension offer."""
    from app.models.call import CallSession
    from app.models.enums import CallStatus
    from app.models.wallet import TransactionRef
    from app.services import wallet as wallet_service

    if appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError(
            "This appointment is not active.", error_code="appointment_not_open"
        )
    if by.id != appointment.user_id and getattr(by, "role", None) != "admin":
        raise ForbiddenError("Only the consulting client can respond to the extension offer.")

    if not appointment.extension_offered or appointment.extension_status != "pending":
        raise BadRequestError(
            "No pending extension offer found for this appointment.",
            error_code="no_pending_offer",
        )

    act = action.lower().strip()
    if act not in ("accept", "decline"):
        raise BadRequestError("Action must be 'accept' or 'decline'.", error_code="invalid_action")

    if act == "decline":
        appointment.extension_status = "declined"
        appointment.extension_offered = False
        await appointment.save()

        try:
            from app.services import realtime
            await realtime.publish_appointment_event(
                appointment.user_id,
                appointment.astrologer_user_id,
                "extension_declined",
                {
                    "appointment_id": str(appointment.id),
                    "status": "declined",
                },
            )
        except Exception as exc:
            logger.debug("Failed to publish extension decline event: {}", exc)

        return appointment

    # act == "accept"
    astro = await Astrologer.get(appointment.astrologer_id)
    if astro is None:
        raise NotFoundError("Astrologer profile not found.", error_code="astrologer_not_found")

    extra_minutes = appointment.extension_offered_minutes or 10
    cost_coins = appointment.extension_cost_coins or 0
    cost_paise = appointment.extension_cost_paise or 0

    # 1. Check client wallet balance
    user_wallet = await wallet_service.get_or_create_wallet(appointment.user_id)
    if user_wallet.available_coins < cost_coins:
        raise BadRequestError(
            f"Insufficient coins. Extension requires {cost_coins} coins, but your available balance is "
            f"{user_wallet.available_coins} coins. Please recharge your wallet to continue.",
            error_code="insufficient_balance",
            details={
                "needed_coins": cost_coins,
                "available_coins": user_wallet.available_coins,
            },
        )

    # 2. Check and lock extra slots
    buffer_mins = getattr(getattr(astro, "appointment", None), "buffer_minutes", 0) or 0
    new_ends_at = appointment.ends_at + timedelta(minutes=extra_minutes)
    total_blocked_minutes = appointment.minutes + extra_minutes + buffer_mins

    # Existing slots claimed for this appointment
    existing_slots = await AppointmentSlot.find(
        {"appointment_id": appointment.id}
    ).to_list()
    existing_starts = {s.starts_at for s in existing_slots}

    # Desired slot starts
    all_starts = set(slot_starts(appointment.starts_at, total_blocked_minutes))
    slots_to_add = all_starts - existing_starts

    new_slots: list[AppointmentSlot] = []
    try:
        for moment in sorted(slots_to_add):
            slot = AppointmentSlot(
                astrologer_id=appointment.astrologer_id,
                appointment_id=appointment.id,
                starts_at=moment,
            )
            await slot.insert()
            new_slots.append(slot)
    except DuplicateKeyError:
        for s in new_slots:
            try:
                await s.delete()
            except Exception:
                pass
        raise ConflictError(
            "Cannot extend: A time slot during the extension period was just booked by another user.",
            error_code="slot_clash",
        )

    # 3. Debit wallet
    if cost_coins > 0:
        await wallet_service.debit(
            user_id=appointment.user_id,
            amount_coins=cost_coins,
            reason=TransactionReason.CONSULTATION,
            idempotency_key=f"appointment:{appointment.id}:ext:{int(appointment.extension_offered_at.timestamp())}",
            ref=TransactionRef(
                session_id=appointment.id,
                astrologer_id=appointment.astrologer_id,
                astrologer_name=astro.display_name,
                astrologer_image_url=astro.profile_image_url,
                consultation_mode="video",
            ),
            note=f"In-chamber consultation extension (+{extra_minutes}m) with {astro.display_name}",
        )

    # 4. Update appointment
    appointment.minutes += extra_minutes
    appointment.ends_at = new_ends_at
    appointment.price_paise += cost_paise
    appointment.extension_status = "accepted"
    appointment.extension_offered = False
    appointment.extension_total_extended_minutes = (
        getattr(appointment, "extension_total_extended_minutes", 0) + extra_minutes
    )
    await appointment.save()

    # 5. Update CallSession if connected
    if getattr(appointment, "call_session_id", None):
        try:
            call_session = await CallSession.get(appointment.call_session_id)
            if call_session and call_session.status == CallStatus.ACTIVE:
                call_session.requested_minutes += extra_minutes
                await call_session.save()
        except Exception as exc:
            logger.error("Failed to update call_session duration on extension: {}", exc)

    # 6. Publish realtime update
    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "extension_accepted",
            {
                "appointment_id": str(appointment.id),
                "status": "accepted",
                "extra_minutes": extra_minutes,
                "minutes": appointment.minutes,
                "ends_at": appointment.ends_at.isoformat(),
                "cost_coins": cost_coins,
            },
        )
    except Exception as exc:
        logger.debug("Failed to publish extension accepted event: {}", exc)

    logger.info(
        "Appointment {} extended by {} minutes for client {} with astrologer {}",
        appointment.id,
        extra_minutes,
        appointment.user_id,
        appointment.astrologer_id,
    )
    return appointment


# ------------------------------------------------ complimentary follow-up window
async def issue_follow_up_pass(
    *,
    appointment: Appointment,
    by: User,
    window_days: int = 7,
    max_messages: int = 3,
    notes: str | None = None,
) -> Appointment:
    """Astrologer issues or updates the 7-day (or custom days) remedy clarification pass."""
    if by.id != appointment.astrologer_user_id and getattr(by, "role", None) != "admin":
        raise ForbiddenError("Only the consulting astrologer can issue a follow-up pass.")

    if appointment.status != AppointmentStatus.COMPLETED and appointment.status != AppointmentStatus.BOOKED:
        raise BadRequestError("A follow-up pass can only be issued for booked or completed consultations.")

    now = utcnow()
    appointment.follow_up_pass_enabled = True
    appointment.follow_up_window_days = window_days
    appointment.follow_up_expires_at = now + timedelta(days=window_days)
    appointment.follow_up_max_messages = max_messages
    appointment.follow_up_granted_at = now
    if notes:
        appointment.follow_up_notes = notes

    await appointment.save()

    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "follow_up_pass_issued",
            {
                "id": str(appointment.id),
                "follow_up_pass_enabled": True,
                "follow_up_window_days": window_days,
                "follow_up_expires_at": appointment.follow_up_expires_at.isoformat(),
                "follow_up_max_messages": max_messages,
                "follow_up_messages_used": appointment.follow_up_messages_used,
            },
        )
    except Exception as exc:
        logger.debug("Failed to publish follow-up pass event: {}", exc)

    logger.info("Follow-up pass of {} days issued for appointment {} by {}", window_days, appointment.id, by.email)
    return appointment


async def send_follow_up_message(
    *,
    appointment: Appointment,
    by: User,
    text: str,
) -> tuple[Appointment, dict]:
    """Sends a clarification message under the complimentary follow-up pass."""
    if by.id not in (appointment.user_id, appointment.astrologer_user_id) and getattr(by, "role", None) != "admin":
        raise ForbiddenError("You are not a participant in this consultation.")

    is_client = (by.id == appointment.user_id)
    now = utcnow()

    body = text.strip()
    if not body:
        raise BadRequestError("Message cannot be empty.", error_code="empty_message")

    if is_client:
        if not appointment.follow_up_pass_enabled:
            raise BadRequestError(
                "A complimentary follow-up pass has not been active for this session.",
                error_code="pass_not_active",
            )
        if appointment.follow_up_expires_at and now > appointment.follow_up_expires_at:
            raise BadRequestError(
                "Your complimentary follow-up window for this consultation has expired.",
                error_code="follow_up_expired",
            )
        if appointment.follow_up_messages_used >= appointment.follow_up_max_messages:
            raise BadRequestError(
                f"You have used all {appointment.follow_up_max_messages} complimentary questions for this session.",
                error_code="follow_up_limit_reached",
            )
        appointment.follow_up_messages_used += 1

    msg_item = {
        "id": str(PydanticObjectId()),
        "sender_id": str(by.id),
        "sender_role": "user" if is_client else "astrologer",
        "sender_name": getattr(by, "full_name", None) or ("Seeker" if is_client else "Astrologer"),
        "text": body,
        "sent_at": now.isoformat(),
    }

    if appointment.follow_up_thread is None:
        appointment.follow_up_thread = []

    appointment.follow_up_thread.append(msg_item)
    await appointment.save()

    try:
        from app.services import realtime
        await realtime.publish_appointment_event(
            appointment.user_id,
            appointment.astrologer_user_id,
            "follow_up_message",
            {
                "id": str(appointment.id),
                "message": msg_item,
                "follow_up_messages_used": appointment.follow_up_messages_used,
                "follow_up_max_messages": appointment.follow_up_max_messages,
            },
        )
    except Exception as exc:
        logger.debug("Failed to publish follow-up message event: {}", exc)

    logger.info("Follow-up message sent on appointment {} by {}", appointment.id, by.email)
    return appointment, msg_item


# ----------------------------------------------------------------- VIP & Private Links
async def create_private_invite_link(
    *,
    astrologer: Astrologer,
    title: str,
    client_name: str | None = None,
    client_email: str | None = None,
    passcode: str | None = None,
    custom_price_paise: int | None = None,
    discount_percent: float | None = None,
    is_tatkal: bool = False,
    max_uses: int = 1,
    expires_in_hours: int | None = 48,
    notes: str | None = None,
) -> PrivateInviteLink:
    import secrets
    from app.core.security import hash_password

    assert astrologer.id is not None
    # Generate unique code, e.g. "VIP-9A8B7C"
    raw_code = f"VIP-{secrets.token_hex(3).upper()}"
    while await PrivateInviteLink.find_one({"invite_code": raw_code}):
        raw_code = f"VIP-{secrets.token_hex(3).upper()}"

    passcode_hash = None
    has_passcode = False
    if passcode and passcode.strip():
        passcode_hash = hash_password(passcode.strip())
        has_passcode = True

    expires_at = None
    if expires_in_hours and expires_in_hours > 0:
        expires_at = utcnow() + timedelta(hours=expires_in_hours)

    link = PrivateInviteLink(
        astrologer_id=astrologer.id,
        invite_code=raw_code,
        title=title.strip() or "VIP Private Consultation",
        client_name=client_name.strip() if client_name else None,
        client_email=client_email.strip() if client_email else None,
        has_passcode=has_passcode,
        passcode_hash=passcode_hash,
        custom_price_paise=custom_price_paise,
        discount_percent=discount_percent,
        is_tatkal=is_tatkal,
        max_uses=max_uses,
        uses_count=0,
        expires_at=expires_at,
        is_active=True,
        notes=notes.strip() if notes else None,
    )
    await link.insert()
    logger.info(
        "Private invite link {} created for astrologer {} (code: {})",
        link.id,
        astrologer.id,
        raw_code,
    )
    return link


async def list_private_invite_links(
    astrologer_id: PydanticObjectId,
) -> list[PrivateInviteLink]:
    return (
        await PrivateInviteLink.find({"astrologer_id": astrologer_id})
        .sort(-PrivateInviteLink.created_at)
        .to_list()
    )


async def deactivate_private_invite_link(
    link_id: PydanticObjectId, astrologer_id: PydanticObjectId
) -> None:
    link = await PrivateInviteLink.get(link_id)
    if not link or link.astrologer_id != astrologer_id:
        raise NotFoundError("Private invite link not found.", error_code="link_not_found")
    link.is_active = False
    await link.save()
    logger.info("Private invite link {} deactivated by astrologer {}", link_id, astrologer_id)


async def validate_private_invite_link(invite_code: str) -> dict:
    link = await PrivateInviteLink.find_one({"invite_code": invite_code})
    if not link:
        raise NotFoundError("Invitation link does not exist.", error_code="invite_not_found")

    now = utcnow()
    is_expired = bool(link.expires_at and now > link.expires_at)
    is_active = bool(link.is_active and not is_expired and link.uses_count < link.max_uses)

    astrologer = await Astrologer.get(link.astrologer_id)
    if not astrologer:
        raise NotFoundError("Astrologer not found.", error_code="astrologer_not_found")

    return {
        "invite_code": link.invite_code,
        "title": link.title,
        "astrologer_id": str(astrologer.id),
        "astrologer_name": astrologer.name,
        "astrologer_avatar": astrologer.avatar_url,
        "astrologer_slug": astrologer.slug,
        "has_passcode": link.has_passcode,
        "is_active": is_active,
        "is_expired": is_expired,
        "custom_price_paise": link.custom_price_paise,
        "discount_percent": link.discount_percent,
        "is_tatkal": link.is_tatkal,
        "standard_price_paise": astrologer.appointment.price_paise,
        "block_minutes": astrologer.appointment.block_minutes,
    }


async def verify_private_invite_passcode(invite_code: str, passcode: str) -> bool:
    from app.core.security import verify_password

    link = await PrivateInviteLink.find_one({"invite_code": invite_code})
    if not link or not link.is_active:
        raise BadRequestError("Invalid or inactive invitation link.", error_code="invalid_link")
    if not link.has_passcode or not link.passcode_hash:
        return True
    if not verify_password(passcode, link.passcode_hash):
        raise BadRequestError("Incorrect invitation passcode.", error_code="invalid_passcode")
    return True


async def open_quick_tatkal_window(
    *,
    astrologer: Astrologer,
    starts_at: datetime,
    minutes: int = 30,
    multiplier: float = 1.5,
    fixed_paise: int | None = None,
    custom_title: str | None = "VIP Emergency Tatkal Slot",
    is_private: bool = False,
    day: date_type | None = None,
    timezone_name: str | None = None,
) -> AvailabilityWindow:
    assert astrologer.id is not None
    starts = starts_at.astimezone(UTC).replace(second=0, microsecond=0)
    ends = starts + timedelta(minutes=minutes)

    clash = await AvailabilityWindow.find_one(
        {
            "astrologer_id": astrologer.id,
            "starts_at": {"$lt": ends},
            "ends_at": {"$gt": starts},
        }
    )
    if clash is not None:
        raise BadRequestError(
            "That emergency slot overlaps hours you have already opened.",
            error_code="window_overlap",
        )

    IST = ZoneInfo("Asia/Kolkata")
    tz = IST
    if timezone_name:
        try:
            tz = ZoneInfo(timezone_name)
        except Exception:
            tz = IST
    elif starts_at.tzinfo and starts_at.tzinfo not in (UTC, timezone.utc):
        tz = starts_at.tzinfo

    resolved_day = day or starts_at.astimezone(tz).date()

    window = AvailabilityWindow(
        astrologer_id=astrologer.id,
        day=resolved_day,
        starts_at=starts,
        ends_at=ends,
        is_tatkal=True,
        tatkal_multiplier=multiplier,
        tatkal_fixed_paise=fixed_paise,
        custom_title=custom_title,
        is_private=is_private,
    )
    await window.insert()
    logger.info(
        "Quick Tatkal Window {} created for astrologer {} from {} to {} (x{})",
        window.id,
        astrologer.id,
        starts,
        ends,
        multiplier,
    )
    return window


async def activate_auspicious_transit_surge(
    *,
    astrologer: Astrologer,
    target_date: date_type,
    multiplier: float = 1.5,
    custom_title: str | None = None,
    open_surge_window: bool = True,
    from_time: str = "10:00",
    to_time: str = "22:00",
    timezone_name: str | None = "Asia/Kolkata",
) -> dict[str, Any]:
    """1-Click activation of Auspicious Day Tatkal Surge (1.5x / 2.0x).

    Finds existing windows on target_date and turns them into VIP Tatkal windows with
    the dynamic transit multiplier, or opens a new prime-hours window on that day if none exists.
    """
    assert astrologer.id is not None
    transit = get_auspicious_transit_for_date(target_date)
    event_name = transit.get("event_name_bn") or "শুভ তিথি"
    resolved_title = custom_title or f"{event_name} শুভ তিথি তৎকাল সার্জ ({multiplier}x)"

    existing_windows = await AvailabilityWindow.find({
        "astrologer_id": astrologer.id,
        "day": target_date,
    }).to_list()

    affected_windows = 0
    if existing_windows:
        for w in existing_windows:
            w.is_tatkal = True
            w.tatkal_multiplier = multiplier
            w.custom_title = resolved_title
            await w.save()
            affected_windows += 1
    elif open_surge_window:
        from zoneinfo import ZoneInfo
        IST = ZoneInfo("Asia/Kolkata")
        tz = IST
        if timezone_name:
            try:
                tz = ZoneInfo(timezone_name)
            except Exception:
                tz = IST

        try:
            f_h, f_m = [int(p) for p in from_time.split(":")[:2]]
            t_h, t_m = [int(p) for p in to_time.split(":")[:2]]
        except Exception:
            f_h, f_m = 10, 0
            t_h, t_m = 22, 0

        starts_local = datetime(target_date.year, target_date.month, target_date.day, f_h, f_m, tzinfo=tz)
        ends_local = datetime(target_date.year, target_date.month, target_date.day, t_h, t_m, tzinfo=tz)
        starts_utc = starts_local.astimezone(UTC).replace(second=0, microsecond=0)
        ends_utc = ends_local.astimezone(UTC).replace(second=0, microsecond=0)

        clash = await AvailabilityWindow.find_one({
            "astrologer_id": astrologer.id,
            "starts_at": {"$lt": ends_utc},
            "ends_at": {"$gt": starts_utc},
        })
        if clash is None:
            new_w = AvailabilityWindow(
                astrologer_id=astrologer.id,
                day=target_date,
                starts_at=starts_utc,
                ends_at=ends_utc,
                is_tatkal=True,
                tatkal_multiplier=multiplier,
                custom_title=resolved_title,
            )
            await new_w.insert()
            affected_windows += 1

    astrologer.appointment.tatkal_enabled = True
    astrologer.appointment.tatkal_default_multiplier = multiplier
    await astrologer.save()

    logger.info(
        "Auspicious Transit Surge activated for astrologer {} on {} (x{}, {} windows affected)",
        astrologer.id,
        target_date,
        multiplier,
        affected_windows,
    )

    return {
        "success": True,
        "day": target_date.isoformat(),
        "is_auspicious_transit_day": transit.get("is_auspicious_transit_day", False),
        "event_key": transit.get("event_key"),
        "event_name_bn": transit.get("event_name_bn"),
        "event_name_en": transit.get("event_name_en"),
        "multiplier": multiplier,
        "custom_title": resolved_title,
        "windows_affected_count": affected_windows,
        "spiritual_reason_bn": transit.get("spiritual_reason_bn"),
        "remedy_focus_bn": transit.get("remedy_focus_bn"),
        "demand_factor": transit.get("demand_factor", "1x"),
        "message": f"{event_name} শুভ তিথি তৎকাল সার্জ ({multiplier}x) সফলভাবে সক্রিয় করা হয়েছে।",
    }


async def deactivate_auspicious_transit_surge(
    *,
    astrologer: Astrologer,
    target_date: date_type,
) -> dict[str, Any]:
    """1-Click deactivation of Auspicious Day Tatkal Surge, returning windows to standard 1.0x rate."""
    assert astrologer.id is not None
    existing_windows = await AvailabilityWindow.find({
        "astrologer_id": astrologer.id,
        "day": target_date,
    }).to_list()

    affected_windows = 0
    for w in existing_windows:
        if w.is_tatkal:
            w.is_tatkal = False
            w.tatkal_multiplier = 1.0
            w.custom_title = None
            await w.save()
            affected_windows += 1

    logger.info(
        "Auspicious Transit Surge deactivated for astrologer {} on {} ({} windows reverted)",
        astrologer.id,
        target_date,
        affected_windows,
    )

    return {
        "success": True,
        "day": target_date.isoformat(),
        "windows_affected_count": affected_windows,
        "message": "শুভ তিথি তৎকাল সার্জ সফলভাবে নিষ্ক্রিয় করা হয়েছে এবং স্বাভাবিক মূল্যমান পুনঃস্থাপিত হয়েছে।",
    }





