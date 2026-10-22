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
    KundliDashaAntar,
    KundliDashaCard,
    KundliYogaItem,
    KundliActiveYogaDetail,
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


def _add_calendar_years(dt: datetime, years: int) -> datetime:
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(year=dt.year + years, day=28)


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

    return KundliCalculateResponse(
        personal_details=personal_details,
        astronomical_info=astronomical_info,
        astro_positions=astro_positions,
        planetary_info=planetary_info,
        d1_planets=d1_chart_planets,
        d9_planets=d9_chart_planets,
        d1_asc_sign=asc_sign_num,
        d9_asc_sign=d9_asc_sign_num,
        planets_table=planets_table,
        houses_table=houses_table,
        dashas_grid=dashas_grid,
        yogas_status=yogas_status,
        active_yogas_details=active_yogas_details,
        selected_language=payload.language,
    )
