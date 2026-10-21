"""Astrology calculation engine utilizing Swiss Ephemeris (pyswisseph)
for high-precision astronomical and Vedic / KP astrological positioning.
"""

from datetime import datetime, UTC
import swisseph as swe
from app.schemas.astrology import (
    PlanetPosition,
    RashiCalculateRequest,
    RashiCalculateResponse,
    RashiTraits,
)
from app.services.astrology.rashi_rules import (
    NAKSHATRAS_DATA,
    RASHIS_DATA,
    calculate_kp_sub_lord,
)

# Map requested ayanamsa string to Swiss Ephemeris sidereal constants
AYANAMSA_MAP = {
    "lahiri": (swe.SIDM_LAHIRI, "Lahiri (Chitra Paksha)"),
    "bv_raman": (swe.SIDM_RAMAN, "B.V. Raman"),
    "krishnamurti": (swe.SIDM_KRISHNAMURTI, "Krishnamurti (KP)"),
    "yukteshwar": (swe.SIDM_YUKTESHWAR, "Sri Yukteshwar"),
    "suryasiddhanta": (swe.SIDM_SURYASIDDHANTA, "Surya Siddhanta"),
    "true_pushya": (swe.SIDM_TRUE_PUSHYA, "True Pushya (PVRN Rao)"),
    "true_mula": (swe.SIDM_TRUE_MULA, "True Mula (Chandra Hari)"),
}

HOUSE_SYSTEM_MAP = {
    "placidus": b"P",
    "koch": b"K",
    "equal": b"A",
    "whole_sign": b"W",
}

PLANET_IDS = [
    (swe.SUN, "Sun", "☉"),
    (swe.MOON, "Moon", "☽"),
    (swe.MARS, "Mars", "♂"),
    (swe.MERCURY, "Mercury", "☿"),
    (swe.JUPITER, "Jupiter", "♃"),
    (swe.VENUS, "Venus", "♀"),
    (swe.SATURN, "Saturn", "♄"),
    (swe.MEAN_NODE, "Rahu", "☊"),
]


def _format_dms(deg_val: float) -> str:
    d = int(deg_val)
    rem = (deg_val - d) * 60
    m = int(rem)
    s = int((rem - m) * 60)
    return f"{d}° {m:02d}' {s:02d}\""


def calculate_rashi(payload: RashiCalculateRequest) -> RashiCalculateResponse:
    # 1. Normalize hour if 12-hour AM/PM clock was selected
    hour = payload.hour
    if payload.period == "PM" and hour < 12:
        hour += 12
    elif payload.period == "AM" and hour == 12:
        hour = 0

    # 2. Convert local date/time + timezone offset to UTC decimal hours
    # UTC = local_time - timezone
    minute = payload.minute
    second = payload.second
    local_decimal_hour = hour + minute / 60.0 + second / 3600.0
    utc_decimal_hour = local_decimal_hour - payload.timezone

    # Handle day shift if utc_decimal_hour crosses midnight
    day = payload.day
    month = payload.month
    year = payload.year

    # Use python datetime to safely handle boundary rollovers
    try:
        from datetime import timedelta
        base_dt = datetime(year, month, day, 0, 0, 0, tzinfo=UTC)
        adjusted_dt = base_dt + timedelta(hours=utc_decimal_hour)
        calc_year = adjusted_dt.year
        calc_month = adjusted_dt.month
        calc_day = adjusted_dt.day
        calc_hour_utc = (
            adjusted_dt.hour
            + adjusted_dt.minute / 60.0
            + adjusted_dt.second / 3600.0
            + adjusted_dt.microsecond / 3600000000.0
        )
    except Exception:
        calc_year, calc_month, calc_day = year, month, day
        calc_hour_utc = utc_decimal_hour % 24

    # 3. Calculate Julian Day in UT
    jd_ut = swe.julday(calc_year, calc_month, calc_day, calc_hour_utc)

    # 4. Configure Ayanamsa
    sidm_constant, ayanamsa_display_name = AYANAMSA_MAP.get(
        payload.ayanamsa, (swe.SIDM_LAHIRI, "Lahiri (Chitra Paksha)")
    )
    swe.set_sid_mode(sidm_constant)
    ayanamsa_deg = swe.get_ayanamsa_ut(jd_ut)

    # 5. Calculate Sidereal Moon Longitude
    calc_flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    moon_res, _ = swe.calc_ut(jd_ut, swe.MOON, calc_flags)
    moon_lon = moon_res[0] % 360.0

    # Moon Sign (Rashi) index 0-11
    rashi_idx = int(moon_lon / 30.0) % 12
    deg_in_sign = moon_lon % 30.0
    moon_deg_formatted = _format_dms(deg_in_sign)

    # 6. Calculate Nakshatra (0-26) and Pada (1-4)
    nak_span_deg = 360.0 / 27.0  # 13.33333333°
    nak_idx = int(moon_lon / nak_span_deg) % 27
    offset_in_nak = moon_lon % nak_span_deg
    pada_span_deg = nak_span_deg / 4.0  # 3.33333333°
    pada = int(offset_in_nak / pada_span_deg) + 1

    nakshatra_info = NAKSHATRAS_DATA[nak_idx]
    nakshatra_name = nakshatra_info["name"]
    nakshatra_lord = nakshatra_info["lord"]

    # KP Sub-Lord
    kp_sub_lord = calculate_kp_sub_lord(nakshatra_lord, offset_in_nak)

    # 7. Coordinates & Ascendant (Lagna)
    lat = payload.latitude if payload.latitude is not None else 22.5726  # Default to Kolkata if not provided
    lon = payload.longitude if payload.longitude is not None else 88.3639

    hsys = HOUSE_SYSTEM_MAP.get(payload.house_system, b"P")
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, hsys, swe.FLG_SIDEREAL)
    asc_lon = ascmc[0] % 360.0
    asc_rashi_idx = int(asc_lon / 30.0) % 12
    asc_deg_formatted = _format_dms(asc_lon % 30.0)

    # 8. Calculate Planet Positions for Kundali
    planets_list: list[PlanetPosition] = []
    for pid, pname, psymbol in PLANET_IDS:
        pres, _ = swe.calc_ut(jd_ut, pid, calc_flags)
        plon = pres[0] % 360.0
        psign_idx = int(plon / 30.0) % 12
        pdeg_in_sign = plon % 30.0
        pnak_idx = int(plon / nak_span_deg) % 27
        ppada = int((plon % nak_span_deg) / pada_span_deg) + 1
        is_retro = pres[3] < 0 if len(pres) > 3 else False

        # Calculate approximate house from Ascendant (1 to 12)
        house_num = ((psign_idx - asc_rashi_idx) % 12) + 1

        planets_list.append(
            PlanetPosition(
                name=pname,
                symbol=psymbol,
                sign=RASHIS_DATA[psign_idx]["name_en"],
                sign_index=psign_idx,
                degree_in_sign=round(pdeg_in_sign, 4),
                degree_formatted=_format_dms(pdeg_in_sign),
                nakshatra=NAKSHATRAS_DATA[pnak_idx]["name"],
                pada=ppada,
                house=house_num,
                is_retrograde=is_retro,
            )
        )

    # Ketu is exactly 180° opposite to Rahu
    rahu_obj = next((p for p in planets_list if p.name == "Rahu"), None)
    if rahu_obj:
        rahu_pres, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, calc_flags)
        ketu_lon = (rahu_pres[0] + 180.0) % 360.0
        ksign_idx = int(ketu_lon / 30.0) % 12
        kdeg_in_sign = ketu_lon % 30.0
        knak_idx = int(ketu_lon / nak_span_deg) % 27
        kpada = int((ketu_lon % nak_span_deg) / pada_span_deg) + 1
        k_house = ((ksign_idx - asc_rashi_idx) % 12) + 1
        planets_list.append(
            PlanetPosition(
                name="Ketu",
                symbol="☋",
                sign=RASHIS_DATA[ksign_idx]["name_en"],
                sign_index=ksign_idx,
                degree_in_sign=round(kdeg_in_sign, 4),
                degree_formatted=_format_dms(kdeg_in_sign),
                nakshatra=NAKSHATRAS_DATA[knak_idx]["name"],
                pada=kpada,
                house=k_house,
                is_retrograde=True,
            )
        )

    # 9. Extract Rashi Metadata & Traits
    rashi_info = RASHIS_DATA[rashi_idx]
    traits = RashiTraits(
        element=rashi_info["element"],
        modality=rashi_info["modality"],
        polarity=rashi_info["polarity"],
        body_parts=rashi_info["body_parts"],
        nature=rashi_info["nature"],
        overview=rashi_info["overview"],
        strengths=rashi_info["strengths"],
        cautions_and_pitfalls=rashi_info["cautions_and_pitfalls"],
        beneficial_actions_and_remedies=rashi_info["beneficial_actions_and_remedies"],
        career_fields=rashi_info["career_fields"],
        lucky_color=rashi_info["lucky_color"],
        lucky_numbers=rashi_info["lucky_numbers"],
        lucky_gemstone=rashi_info["lucky_gemstone"],
        lucky_day=rashi_info["lucky_day"],
        ruling_deity=rashi_info["ruling_deity"],
        compatible_rashis=rashi_info["compatible_rashis"],
    )

    # Format human-readable date & time
    b_date_str = f"{payload.day:02d}-{payload.month:02d}-{payload.year}"
    b_time_str = f"{hour:02d}:{payload.minute:02d}:{payload.second:02d} (UTC{'+' if payload.timezone >= 0 else ''}{payload.timezone}h)"

    return RashiCalculateResponse(
        name=payload.name.strip() or "Seeker",
        gender=payload.gender.capitalize(),
        birth_date_formatted=b_date_str,
        birth_time_formatted=b_time_str,
        birth_place=payload.place.strip() or "Custom Coordinates",
        latitude=round(lat, 4),
        longitude=round(lon, 4),
        timezone=payload.timezone,
        ayanamsa_name=ayanamsa_display_name,
        ayanamsa_degrees=round(ayanamsa_deg, 4),
        rashi_index=rashi_idx,
        rashi_name_en=rashi_info["name_en"],
        rashi_name_hi=rashi_info["name_hi"],
        rashi_name_bn=rashi_info["name_bn"],
        rashi_symbol=rashi_info["symbol"],
        rashi_lord=rashi_info["lord"],
        moon_sidereal_longitude=round(moon_lon, 4),
        moon_degree_in_sign=round(deg_in_sign, 4),
        moon_degree_formatted=moon_deg_formatted,
        nakshatra_index=nak_idx,
        nakshatra_name=nakshatra_name,
        nakshatra_pada=pada,
        nakshatra_lord=nakshatra_lord,
        kp_sub_lord=kp_sub_lord,
        ascendant_longitude=round(asc_lon, 4),
        ascendant_rashi_index=asc_rashi_idx,
        ascendant_rashi_name_en=RASHIS_DATA[asc_rashi_idx]["name_en"],
        ascendant_degree_formatted=asc_deg_formatted,
        traits=traits,
        planets=planets_list,
        house_system=payload.house_system.capitalize(),
        chart_style=payload.chart_style,
    )
