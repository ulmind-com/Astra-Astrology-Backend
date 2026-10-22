import math
from datetime import datetime, timedelta, UTC
from loguru import logger
from app.schemas.astrology import (
    AvakahadaChakra,
    BirthPanchang,
    CalculationMeta,
    ClientNakshatraRules,
    DisputedValue,
    HouseCusp,
    NakshatraCalculateRequest,
    NakshatraCalculateResponse,
    NakshatraPadaDetail,
    NakshatraTraits,
    PlanetPosition,
    RashiCalculateRequest,
    RashiCalculateResponse,
    RashiTraits,
    TarabalaItem,
    TimezoneResolution,
)
from app.services.astrology import client_nakshatra_rules, client_rules
from app.services.astrology.panchang import build_panchang
from app.services.astrology.nakshatra_rules import (
    NAKSHATRAS_MASTER,
    RASHI_TATVA,
    RASHI_VARNA,
    RASHI_VASHYA,
    calculate_paya,
    calculate_tarabala_table,
)
from app.services.astrology.rashi_rules import (
    NAKSHATRAS_DATA,
    RASHIS_DATA,
    calculate_kp_sub_lord,
)
from app.services.astrology.rashi_translations import get_rashi_translations
from app.services.astrology.timezone_resolver import resolve as resolve_timezone

# Swiss Ephemeris is a hard requirement for correct positions. It is imported
# defensively so that a host missing the compiled extension raises a clear,
# actionable error at request time instead of crashing the process at startup or,
# worse, silently serving positions from a reduced engine. See
# EphemerisUnavailable and _require_swisseph below.
try:
    import swisseph as swe

    HAS_SWISSEPH = True
    _SWISSEPH_IMPORT_ERROR: str | None = None
except Exception as exc:  # pragma: no cover - import guard only
    swe = None  # type: ignore[assignment]
    HAS_SWISSEPH = False
    _SWISSEPH_IMPORT_ERROR = str(exc)
    logger.error(
        f"Swiss Ephemeris (pyswisseph) could not be imported: {exc}. "
        "Astrology calculations will return HTTP 503 until this is fixed. "
        "The container needs build-essential and python3-dev to compile it."
    )


class EphemerisUnavailable(RuntimeError):
    """Raised when positions cannot be computed to the accuracy we promise.

    The previous build carried a 13-term pure-Python lunar series as a fallback.
    It returned only the Sun and the Moon - no Mars, Jupiter, Saturn, Rahu or
    Ketu, and no house data - with nothing in the response to say so, so a
    degraded chart was indistinguishable from a complete one. Refusing is the
    honest behaviour: a wrong horoscope served confidently is worse than an
    error the operator can see and fix.
    """


def _require_swisseph() -> None:
    if not HAS_SWISSEPH:
        raise EphemerisUnavailable(
            "Swiss Ephemeris is not available on this server, so an accurate chart "
            "cannot be calculated. Details: "
            f"{_SWISSEPH_IMPORT_ERROR or 'pyswisseph missing'}"
        )


if HAS_SWISSEPH and swe is not None:
    AYANAMSA_MAP = {
        "lahiri": (swe.SIDM_LAHIRI, "Lahiri (Chitra Paksha)"),
        "bv_raman": (swe.SIDM_RAMAN, "B.V. Raman"),
        "krishnamurti": (swe.SIDM_KRISHNAMURTI, "Krishnamurti (KP)"),
        "yukteshwar": (swe.SIDM_YUKTESHWAR, "Sri Yukteshwar"),
        "suryasiddhanta": (swe.SIDM_SURYASIDDHANTA, "Surya Siddhanta"),
        "true_pushya": (swe.SIDM_TRUE_PUSHYA, "True Pushya (PVRN Rao)"),
        "true_mula": (swe.SIDM_TRUE_MULA, "True Mula (Chandra Hari)"),
    }
    PLANET_IDS = [
        (swe.SUN, "Sun", "\u2609"),
        (swe.MOON, "Moon", "\u263d"),
        (swe.MARS, "Mars", "\u2642"),
        (swe.MERCURY, "Mercury", "\u263f"),
        (swe.JUPITER, "Jupiter", "\u2643"),
        (swe.VENUS, "Venus", "\u2640"),
        (swe.SATURN, "Saturn", "\u2644"),
    ]
else:
    AYANAMSA_MAP = {
        "lahiri": (1, "Lahiri (Chitra Paksha)"),
        "bv_raman": (2, "B.V. Raman"),
        "krishnamurti": (3, "Krishnamurti (KP)"),
        "yukteshwar": (4, "Sri Yukteshwar"),
        "suryasiddhanta": (5, "Surya Siddhanta"),
        "true_pushya": (6, "True Pushya (PVRN Rao)"),
        "true_mula": (7, "True Mula (Chandra Hari)"),
    }
    PLANET_IDS = []

# Nakshatra name -> index, so a PlanetPosition's nakshatra string can be mapped
# back to the index the technique rules are keyed on.
NAKSHATRA_INDEX_BY_NAME = {n["name"]: i for i, n in enumerate(NAKSHATRAS_DATA)}

HOUSE_SYSTEM_MAP = {
    "placidus": b"P",
    "koch": b"K",
    "equal": b"A",
    "whole_sign": b"W",
}


def _lang(block: dict, code: str) -> object:
    """One language out of a translated block, falling back to English.

    A gap in the translation tables used to raise KeyError here, and because the
    response bundles all three languages at once, a single missing phrase took down
    every request for that nakshatra regardless of the language asked for. One
    Hindi entry was in fact missing, so roughly one birth in twenty-seven returned a
    500. Falling back keeps the reading whole and leaves the gap visible in the logs.
    """
    if code in block:
        return block[code]
    logger.warning(f"translation missing for language {code!r}; falling back to English")
    return block.get("en", "")


def _format_dms(deg_val: float) -> str:
    d = int(deg_val)
    rem = (deg_val - d) * 60
    m = int(rem)
    s = int((rem - m) * 60)
    return f"{d}° {m:02d}' {s:02d}\""


def _sign_of(lon: float) -> int:
    return int(lon / 30.0) % 12


def _nak_of(lon: float) -> tuple[int, int, float]:
    """Nakshatra index, pada (1-4), and the offset within the nakshatra."""
    span = 360.0 / 27.0
    offset = lon % span
    return int(lon / span) % 27, int(offset / (span / 4.0)) + 1, offset


def _house_from_cusps(longitude: float, cusps: list[float]) -> int:
    """House number for a longitude, using the real cusp boundaries.

    The previous build computed Placidus / Koch / Equal cusps and then discarded
    them, assigning houses as ((planet_sign - ascendant_sign) % 12) + 1 - whole-sign
    always. The House System selector therefore had no effect on any output; all
    four options produced byte-identical charts. This walks the actual cusps, so
    Placidus, Koch and Equal now differ from each other and from whole-sign, as the
    selector promises.

    `cusps` is the twelve house starting longitudes in ascending house order.
    """
    lon = longitude % 360.0
    for i in range(12):
        start = cusps[i] % 360.0
        end = cusps[(i + 1) % 12] % 360.0
        # A house wraps past 0 Aries when its end longitude is below its start.
        span = (end - start) % 360.0
        if span == 0.0:
            span = 360.0
        if (lon - start) % 360.0 < span:
            return i + 1
    return 1


def _build_cusps(
    jd_ut: float, lat: float, lon: float, house_system_key: str
) -> tuple[list[float], float, list[str]]:
    """Twelve house cusps and the ascendant, with any degradation reported.

    Placidus and Koch are undefined inside the polar circles - the required
    intersection does not exist - and Swiss Ephemeris silently substitutes
    Porphyry there. Rather than let that pass unremarked, the substitution is
    detected and returned as a warning the response carries.
    """
    warnings: list[str] = []
    requested = house_system_key
    if house_system_key in {"placidus", "koch"} and abs(lat) > 66.0:
        warnings.append(
            f"{requested.capitalize()} houses are undefined above 66 degrees "
            f"latitude (birth latitude {lat:.2f}). Equal houses were used instead."
        )
        house_system_key = "equal"

    hsys = HOUSE_SYSTEM_MAP.get(house_system_key, b"P")
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, hsys, swe.FLG_SIDEREAL)
    return [c % 360.0 for c in cusps[:12]], ascmc[0] % 360.0, warnings


def _planet_position(
    name: str,
    symbol: str,
    longitude: float,
    cusps: list[float],
    is_retrograde: bool,
) -> PlanetPosition:
    sign_idx = _sign_of(longitude)
    nak_idx, pada, _ = _nak_of(longitude)
    return PlanetPosition(
        name=name,
        symbol=symbol,
        sign=RASHIS_DATA[sign_idx]["name_en"],
        sign_index=sign_idx,
        degree_in_sign=round(longitude % 30.0, 4),
        degree_formatted=_format_dms(longitude % 30.0),
        nakshatra=NAKSHATRAS_DATA[nak_idx]["name"],
        pada=pada,
        house=_house_from_cusps(longitude, cusps),
        is_retrograde=is_retrograde,
    )


def _resolve_birth_instant(payload) -> tuple[float, float, float, TimezoneResolution, float, float]:
    """Julian Day UT for the birth, plus the coordinates and offset actually used.

    Three separate problems in the previous build are fixed here. The offset was a
    longitude guess (round(lon / 15) / 2) made by the geocoding endpoint, which
    produced offsets that exist nowhere (UTC-5.5 for London, Ontario) and forced a
    crude 68E-97.5E box to +05:30, so every birth in Bangladesh, Nepal, Bhutan,
    Pakistan and Myanmar was computed in Indian time. Daylight saving was ignored
    entirely. Historical changes were ignored entirely. All three are now handled by
    resolving the IANA zone for the birth coordinates and asking the tz database for
    the offset at that exact local instant.
    """
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

    lat = payload.latitude if payload.latitude is not None else 22.5726
    lon = payload.longitude if payload.longitude is not None else 88.3639

    resolved = resolve_timezone(
        year=payload.year,
        month=payload.month,
        day=payload.day,
        hour=hour_24,
        minute=minute,
        second=second,
        latitude=payload.latitude,
        longitude=payload.longitude,
        zone_name=getattr(payload, "timezone_name", None),
        fallback_offset_hours=payload.timezone,
    )

    tz_info = TimezoneResolution(
        offset_hours=round(resolved.offset_hours, 6),
        offset_label=resolved.offset_label,
        zone_name=resolved.zone_name,
        abbreviation=resolved.abbreviation,
        source=resolved.source,
        is_dst=resolved.is_dst,
        note=resolved.note,
    )

    local_decimal = hour_24 + minute / 60.0 + second / 3600.0
    utc_decimal = local_decimal - resolved.offset_hours
    base = datetime(payload.year, payload.month, payload.day, tzinfo=UTC)
    moment = base + timedelta(hours=utc_decimal)
    utc_hours = (
        moment.hour
        + moment.minute / 60.0
        + moment.second / 3600.0
        + moment.microsecond / 3_600_000_000.0
    )
    jd_ut = swe.julday(moment.year, moment.month, moment.day, utc_hours)
    return jd_ut, lat, lon, tz_info, float(hour_24), resolved.offset_hours


def calculate_rashi(payload: RashiCalculateRequest) -> RashiCalculateResponse:
    _require_swisseph()

    jd_ut, lat, lon, tz_info, hour, offset_hours = _resolve_birth_instant(payload)
    warnings: list[str] = []
    if tz_info.note:
        warnings.append(tz_info.note)

    sidm_constant, ayanamsa_display_name = AYANAMSA_MAP.get(
        payload.ayanamsa, (swe.SIDM_LAHIRI, "Lahiri (Chitra Paksha)")
    )
    swe.set_sid_mode(sidm_constant)
    ayanamsa_deg = swe.get_ayanamsa_ut(jd_ut)

    # The page presents a KP sub-lord. KP practice is to cast on the Krishnamurti
    # ayanamsa, which differs from Lahiri by roughly 6 arc minutes - enough to move
    # a sub-lord boundary, since the narrowest sub division spans only 0.67 degrees.
    # Rather than quietly mixing the two, the mismatch is stated.
    if payload.ayanamsa != "krishnamurti":
        warnings.append(
            "The KP sub-lord shown was derived on the "
            f"{ayanamsa_display_name} ayanamsa. KP practice is to cast on the "
            "Krishnamurti ayanamsa; the two differ by about 6 arc minutes, which can "
            "move a sub-lord boundary. Select the Krishnamurti ayanamsa for strict KP work."
        )

    calc_flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    cusps, asc_lon, cusp_warnings = _build_cusps(jd_ut, lat, lon, payload.house_system)
    warnings.extend(cusp_warnings)

    moon_res, _ = swe.calc_ut(jd_ut, swe.MOON, calc_flags)
    moon_lon = moon_res[0] % 360.0

    planets_list: list[PlanetPosition] = []
    for pid, pname, psymbol in PLANET_IDS:
        pres, _ = swe.calc_ut(jd_ut, pid, calc_flags)
        planets_list.append(
            _planet_position(
                pname,
                psymbol,
                pres[0] % 360.0,
                cusps,
                is_retrograde=bool(len(pres) > 3 and pres[3] < 0),
            )
        )

    # Rahu and Ketu are always a retrograde axis 180 degrees apart. The mean node
    # is used, which is both the classical Vedic and the original KP convention;
    # node_type is recorded in the response so the choice is never a guess.
    rahu_res, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, calc_flags)
    rahu_lon = rahu_res[0] % 360.0
    planets_list.append(
        _planet_position("Rahu", "\u260a", rahu_lon, cusps, is_retrograde=True)
    )
    planets_list.append(
        _planet_position(
            "Ketu", "\u260b", (rahu_lon + 180.0) % 360.0, cusps, is_retrograde=True
        )
    )

    rashi_idx = _sign_of(moon_lon)
    deg_in_sign = moon_lon % 30.0
    nak_idx, pada, offset_in_nak = _nak_of(moon_lon)

    nakshatra_info = NAKSHATRAS_DATA[nak_idx]
    nakshatra_lord = nakshatra_info["lord"]
    kp_sub_lord = calculate_kp_sub_lord(nakshatra_lord, offset_in_nak)

    asc_rashi_idx = _sign_of(asc_lon)

    rashi_info = RASHIS_DATA[rashi_idx]
    lang_pref = getattr(payload, "language", "en") or "en"
    trans_data = get_rashi_translations(rashi_idx, lang_pref)
    sel = trans_data["selected"]

    traits = RashiTraits(
        element=sel.get("element", rashi_info["element"]),
        modality=sel.get("modality", rashi_info["modality"]),
        polarity=sel.get("polarity", rashi_info["polarity"]),
        body_parts=sel.get("body_parts", rashi_info["body_parts"]),
        nature=sel.get("nature", rashi_info["nature"]),
        overview=sel.get("overview", rashi_info["overview"]),
        strengths=sel.get("strengths", rashi_info["strengths"]),
        cautions_and_pitfalls=sel.get(
            "cautions_and_pitfalls", rashi_info["cautions_and_pitfalls"]
        ),
        beneficial_actions_and_remedies=sel.get(
            "beneficial_actions_and_remedies",
            rashi_info["beneficial_actions_and_remedies"],
        ),
        career_fields=sel.get("career_fields", rashi_info["career_fields"]),
        lucky_color=sel.get("lucky_color", rashi_info["lucky_color"]),
        lucky_numbers=rashi_info["lucky_numbers"],
        lucky_gemstone=sel.get("lucky_gemstone", rashi_info["lucky_gemstone"]),
        lucky_day=sel.get("lucky_day", rashi_info["lucky_day"]),
        ruling_deity=sel.get("ruling_deity", rashi_info["ruling_deity"]),
        compatible_rashis=sel.get("compatible_rashis", rashi_info["compatible_rashis"]),
    )

    house_cusps = [
        HouseCusp(
            house=i + 1,
            longitude=round(c, 4),
            sign=RASHIS_DATA[_sign_of(c)]["name_en"],
            sign_index=_sign_of(c),
            degree_in_sign=round(c % 30.0, 4),
            degree_formatted=_format_dms(c % 30.0),
        )
        for i, c in enumerate(cusps)
    ]

    offset_label = tz_info.offset_label
    min_val = getattr(payload, "minute", None) or 0
    sec_val = getattr(payload, "second", None) or 0
    b_date_str = f"{payload.day:02d}-{payload.month:02d}-{payload.year}"
    b_time_str = (
        f"{int(hour):02d}:{min_val:02d}:{sec_val:02d} ({offset_label}"
        + (f" {tz_info.abbreviation}" if tz_info.abbreviation else "")
        + ")"
    )

    return RashiCalculateResponse(
        name=payload.name.strip() or "Seeker",
        gender=payload.gender.capitalize(),
        birth_date_formatted=b_date_str,
        birth_time_formatted=b_time_str,
        birth_place=payload.place.strip() or "Custom Coordinates",
        latitude=round(lat, 4),
        longitude=round(lon, 4),
        timezone=round(offset_hours, 6),
        ayanamsa_name=ayanamsa_display_name,
        ayanamsa_degrees=round(ayanamsa_deg, 4),
        rashi_index=rashi_idx,
        rashi_name_en=rashi_info["name_en"],
        rashi_name_hi=client_rules.SIGN_NAMES[rashi_idx]["hi"],
        rashi_name_bn=client_rules.SIGN_NAMES[rashi_idx]["bn"],
        rashi_symbol=rashi_info["symbol"],
        rashi_lord=client_rules.get_sign_lord(rashi_idx),
        moon_sidereal_longitude=round(moon_lon, 4),
        moon_degree_in_sign=round(deg_in_sign, 4),
        moon_degree_formatted=_format_dms(deg_in_sign),
        nakshatra_index=nak_idx,
        nakshatra_name=nakshatra_info["name"],
        nakshatra_pada=pada,
        nakshatra_lord=nakshatra_lord,
        kp_sub_lord=kp_sub_lord,
        ascendant_longitude=round(asc_lon, 4),
        ascendant_rashi_index=asc_rashi_idx,
        ascendant_rashi_name_en=RASHIS_DATA[asc_rashi_idx]["name_en"],
        ascendant_degree_formatted=_format_dms(asc_lon % 30.0),
        traits=traits,
        planets=planets_list,
        house_system=payload.house_system.replace("_", " ").title(),
        chart_style=payload.chart_style,
        selected_language=lang_pref,
        translations=trans_data["all"],
        client_rules=client_rules.get_sign_profile(rashi_idx, lang_pref),
        ascendant_client_rules=client_rules.get_sign_profile(asc_rashi_idx, lang_pref),
        kp_reference=client_rules.get_kp_reference(lang_pref),
        timezone_resolution=tz_info,
        house_cusps=house_cusps,
        calculation=CalculationMeta(
            engine="swiss_ephemeris",
            engine_version=getattr(swe, "version", None),
            ephemeris="Swiss Ephemeris built-in (Moshier analytical, sub-arcsecond)",
            ayanamsa_key=payload.ayanamsa,
            house_system_key=payload.house_system,
            node_type="mean",
            julian_day_ut=round(jd_ut, 6),
            warnings=warnings,
        ),
    )


def calculate_nakshatra(payload: NakshatraCalculateRequest) -> NakshatraCalculateResponse:
    """Janma Nakshatra (birth star), Pada, Avakahada Chakra, Tarabala and KP Sub-Lord.

    Shares the birth-instant resolution used by calculate_rashi, so the timezone is
    taken from the IANA zone for the birth coordinates at the birth instant rather
    than from a caller-supplied offset that cannot know about daylight saving or
    historical changes.
    """
    _require_swisseph()

    jd_ut, lat, lon, tz_info, hour, offset_hours = _resolve_birth_instant(payload)
    nak_span_deg = 360.0 / 27.0
    pada_span_deg = nak_span_deg / 4.0
    minute = payload.minute if payload.minute is not None else 0
    second = payload.second if payload.second is not None else 0

    sidm_constant, ayanamsa_display_name = AYANAMSA_MAP.get(
        payload.ayanamsa, (swe.SIDM_LAHIRI, "Lahiri (Chitra Paksha)")
    )
    swe.set_sid_mode(sidm_constant)
    ayanamsa_deg = swe.get_ayanamsa_ut(jd_ut)

    calc_flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    moon_res, _ = swe.calc_ut(jd_ut, swe.MOON, calc_flags)
    moon_lon = moon_res[0] % 360.0

    cusps, asc_lon, _cusp_warnings = _build_cusps(jd_ut, lat, lon, "whole_sign")

    # The client's nakshatra techniques are conditional on placements - "if the 9th
    # lord sits here", "if a malefic aspects it" - so the whole chart has to be
    # computed, not just the Moon. Whole-sign houses are used because that is the
    # frame Vedic technique rules assume.
    sun_res, _ = swe.calc_ut(jd_ut, swe.SUN, calc_flags)
    sun_lon = sun_res[0] % 360.0

    chart_planets: list[PlanetPosition] = []
    for pid, pname, psymbol in PLANET_IDS:
        pres, _ = swe.calc_ut(jd_ut, pid, calc_flags)
        chart_planets.append(
            _planet_position(
                pname, psymbol, pres[0] % 360.0, cusps,
                is_retrograde=bool(len(pres) > 3 and pres[3] < 0),
            )
        )
    _rahu_res, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, calc_flags)
    _rahu_lon = _rahu_res[0] % 360.0
    chart_planets.append(_planet_position("Rahu", "\u260a", _rahu_lon, cusps, is_retrograde=True))
    chart_planets.append(
        _planet_position("Ketu", "\u260b", (_rahu_lon + 180.0) % 360.0, cusps, is_retrograde=True)
    )

    nak_idx = int(moon_lon / nak_span_deg) % 27
    offset_in_nak = moon_lon % nak_span_deg
    pada = int(offset_in_nak / pada_span_deg) + 1
    offset_in_pada = offset_in_nak % pada_span_deg
    elapsed_percent = round((offset_in_nak / nak_span_deg) * 100.0, 2)

    rashi_idx = int(moon_lon / 30.0) % 12
    rashi_info = RASHIS_DATA[rashi_idx]
    asc_rashi_idx = int(asc_lon / 30.0) % 12
    moon_house_from_lagna = ((rashi_idx - asc_rashi_idx) % 12) + 1

    nak_meta = NAKSHATRAS_MASTER[nak_idx]
    star_lord = nak_meta["lord"]
    kp_sub_lord = calculate_kp_sub_lord(star_lord, offset_in_nak)

    lang_pref = getattr(payload, "language", "en") or "en"
    if lang_pref not in ("en", "bn", "hi"):
        lang_pref = "en"

    # 4. Build Padas List
    padas_list: list[NakshatraPadaDetail] = []
    for p in nak_meta["padas"]:
        p_rashi_idx = p["rashi_idx"]
        p_rashi = RASHIS_DATA[p_rashi_idx]
        p_num = p["pada"]
        padas_list.append(
            NakshatraPadaDetail(
                pada=p_num,
                rashi_index=p_rashi_idx,
                rashi_name_en=p_rashi["name_en"],
                rashi_name_bn=p_rashi["name_bn"],
                rashi_name_hi=p_rashi["name_hi"],
                navamsha_sign=p["navamsha"],
                namakshar=p[f"namakshar_{lang_pref}"],
                namakshar_en=p["namakshar_en"],
                namakshar_bn=p["namakshar_bn"],
                namakshar_hi=p["namakshar_hi"],
                is_native_pada=(p_num == pada),
            )
        )

    # 5. Avakahada Chakra
    paya_dict = calculate_paya(moon_house_from_lagna)
    avakahada = AvakahadaChakra(
        gana=nak_meta[f"gana_{lang_pref}"],
        yoni=nak_meta[f"yoni_{lang_pref}"],
        yoni_animal=nak_meta[f"yoni_{lang_pref}"],
        nadi=nak_meta[f"nadi_{lang_pref}"],
        varna=RASHI_VARNA[rashi_idx][lang_pref],
        vashya=RASHI_VASHYA[rashi_idx][lang_pref],
        tatva=RASHI_TATVA[rashi_idx][lang_pref],
        paya=paya_dict[lang_pref],
    )

    # 6. Tarabala
    raw_tarabala = calculate_tarabala_table(nak_idx)
    tarabala_list: list[TarabalaItem] = []
    for t in raw_tarabala:
        tarabala_list.append(
            TarabalaItem(
                tara_index=t["tara_index"],
                tara_name=t["tara_name"] if lang_pref == "en" else (t["tara_name_bn"] if lang_pref == "bn" else t["tara_name_hi"]),
                tara_name_bn=t["tara_name_bn"],
                tara_name_hi=t["tara_name_hi"],
                is_auspicious=t["is_auspicious"],
                significance=t["significance"] if lang_pref == "en" else (t["significance_bn"] if lang_pref == "bn" else t["significance_hi"]),
                nakshatras=t["nakshatras"],
            )
        )

    # 7. Traits & Interpretations
    current_namakshar = nak_meta["padas"][pada - 1][f"namakshar_{lang_pref}"]
    traits = NakshatraTraits(
        overview=_lang(nak_meta["overview"], lang_pref),
        strengths=_lang(nak_meta["strengths"], lang_pref),
        cautions_and_pitfalls=_lang(nak_meta["cautions_and_pitfalls"], lang_pref),
        beneficial_actions_and_remedies=_lang(nak_meta["beneficial_actions_and_remedies"], lang_pref),
        career_fields=_lang(nak_meta["career_fields"], lang_pref),
        lucky_color=nak_meta[f"lucky_color_{lang_pref}"],
        lucky_numbers=nak_meta["lucky_numbers"],
        lucky_gemstone=nak_meta[f"lucky_gemstone_{lang_pref}"],
        ruling_deity=nak_meta[f"deity_{lang_pref}"],
        symbol=nak_meta[f"symbol_{lang_pref}"],
        sacred_tree=nak_meta[f"sacred_tree_{lang_pref}"],
        beej_mantra=nak_meta["beej_mantra"],
    )

    # 8. Full multi-language bundles for instantaneous client-side tab switching
    translations_bundle: dict[str, Any] = {}
    for l_code in ("en", "bn", "hi"):
        translations_bundle[l_code] = {
            "nakshatra_name": nak_meta[f"name_{l_code}"],
            "deity": nak_meta[f"deity_{l_code}"],
            "symbol": nak_meta[f"symbol_{l_code}"],
            "sacred_tree": nak_meta[f"sacred_tree_{l_code}"],
            "lucky_color": nak_meta[f"lucky_color_{l_code}"],
            "lucky_gemstone": nak_meta[f"lucky_gemstone_{l_code}"],
            "gana": nak_meta[f"gana_{l_code}"],
            "yoni": nak_meta[f"yoni_{l_code}"],
            "nadi": nak_meta[f"nadi_{l_code}"],
            "varna": RASHI_VARNA[rashi_idx][l_code],
            "vashya": RASHI_VASHYA[rashi_idx][l_code],
            "tatva": RASHI_TATVA[rashi_idx][l_code],
            "paya": paya_dict[l_code],
            "current_namakshar": nak_meta["padas"][pada - 1][f"namakshar_{l_code}"],
            "overview": _lang(nak_meta["overview"], l_code),
            "strengths": _lang(nak_meta["strengths"], l_code),
            "cautions_and_pitfalls": _lang(nak_meta["cautions_and_pitfalls"], l_code),
            "beneficial_actions_and_remedies": _lang(nak_meta["beneficial_actions_and_remedies"], l_code),
            "career_fields": _lang(nak_meta["career_fields"], l_code),
            "rashi_name": rashi_info[f"name_{l_code}"],
        }

    # --- Panchang -----------------------------------------------------------
    panchang_data = build_panchang(
        swe, jd_ut, sun_lon, moon_lon, nak_idx, lat, lon, offset_hours, lang_pref
    )
    panchang = BirthPanchang(**panchang_data)

    # --- Paya ---------------------------------------------------------------
    # Paya is not defined in any document the client supplied, and the rule in use
    # here - the Moon's house counted from the lagna - disagrees with the client's
    # own reference report on both of the worked charts in it. The value is still
    # shown, because removing it would be a silent change, but it is marked
    # disputed and carries the evidence so nobody treats it as settled.
    _PAYA_NOTICE = {
        "en": (
            "Paya is not defined in any of the supplied resource documents, and this "
            "value disagrees with the client's own reference report on both of its "
            "worked charts. Treat it as unconfirmed until the intended rule is supplied."
        ),
        "bn": (
            "প্রদত্ত কোনো নথিতে পায়ার সংজ্ঞা নেই, এবং এই মান ক্লায়েন্টের নিজস্ব নমুনা "
            "রিপোর্টের দুটি কুণ্ডলীতেই মেলে না। সঠিক নিয়ম না পাওয়া পর্যন্ত এটি অনিশ্চিত ধরুন।"
        ),
        "hi": (
            "प्रदत्त किसी भी दस्तावेज़ में पाया की परिभाषा नहीं है, तथा यह मान क्लाइंट की "
            "अपनी संदर्भ रिपोर्ट की दोनों कुंडलियों से मेल नहीं खाता। सही नियम मिलने तक "
            "इसे अपुष्ट मानें।"
        ),
    }
    paya = DisputedValue(
        value=paya_dict[lang_pref],
        is_disputed=True,
        notice=_PAYA_NOTICE.get(lang_pref, _PAYA_NOTICE["en"]),
        evidence=[
            "Client reference chart 1 (Moon in Hasta, 4th from lagna): report gives Silver, this rule gives Iron.",
            "Client reference chart 2 (Moon in Krittika, 3rd from lagna): report gives Iron, this rule gives Copper.",
            "Every other Avakahada field matches that reference exactly on both charts.",
        ],
    )

    # --- The client's own nakshatra techniques, applied to this chart --------
    asc_nak_idx = int(asc_lon / nak_span_deg) % 27
    chart_facts = client_nakshatra_rules.build_chart_facts(
        planets=[
            {
                "name": p.name,
                "sign_index": p.sign_index,
                "nakshatra_index": NAKSHATRA_INDEX_BY_NAME.get(p.nakshatra, 0),
                "house": p.house,
            }
            for p in chart_planets
        ],
        ascendant_sign_index=asc_rashi_idx,
        ascendant_nakshatra_index=asc_nak_idx,
    )
    technique_result = client_nakshatra_rules.evaluate_techniques(
        nak_idx, chart_facts, lang_pref
    )

    b_date_str = f"{payload.day:02d}-{payload.month:02d}-{payload.year}"
    b_time_str = (
        f"{int(hour):02d}:{minute:02d}:{second:02d} ({tz_info.offset_label}"
        + (f" {tz_info.abbreviation}" if tz_info.abbreviation else "")
        + ")"
    )

    return NakshatraCalculateResponse(
        name=payload.name.strip() or "Seeker",
        gender=payload.gender.capitalize(),
        birth_date_formatted=b_date_str,
        birth_time_formatted=b_time_str,
        birth_place=payload.place.strip() or "Custom Coordinates",
        latitude=round(lat, 4),
        longitude=round(lon, 4),
        timezone=round(offset_hours, 6),
        ayanamsa_name=ayanamsa_display_name,
        ayanamsa_degrees=round(ayanamsa_deg, 4),
        nakshatra_index=nak_idx,
        nakshatra_name_en=nak_meta["name_en"],
        nakshatra_name_bn=nak_meta["name_bn"],
        nakshatra_name_hi=nak_meta["name_hi"],
        pada=pada,
        star_lord=star_lord,
        kp_sub_lord=kp_sub_lord,
        moon_sidereal_longitude=round(moon_lon, 4),
        moon_degree_in_nakshatra=round(offset_in_nak, 4),
        moon_degree_in_nakshatra_formatted=_format_dms(offset_in_nak),
        moon_degree_in_pada=round(offset_in_pada, 4),
        moon_degree_in_pada_formatted=_format_dms(offset_in_pada),
        nakshatra_elapsed_percentage=elapsed_percent,
        rashi_index=rashi_idx,
        rashi_name_en=rashi_info["name_en"],
        rashi_name_bn=rashi_info["name_bn"],
        rashi_name_hi=rashi_info["name_hi"],
        rashi_lord=rashi_info["lord"],
        symbol=nak_meta[f"symbol_{lang_pref}"],
        deity=nak_meta[f"deity_{lang_pref}"],
        sacred_tree=nak_meta[f"sacred_tree_{lang_pref}"],
        beej_mantra=nak_meta["beej_mantra"],
        current_namakshar=current_namakshar,
        avakahada=avakahada,
        padas=padas_list,
        tarabala=tarabala_list,
        traits=traits,
        selected_language=lang_pref,
        translations=translations_bundle,
        panchang=panchang,
        paya=paya,
        client_rules=ClientNakshatraRules(**technique_result),
        rashi_client_rules=client_rules.get_sign_profile(rashi_idx, lang_pref),
        timezone_resolution=tz_info,
        planets=chart_planets,
        ascendant_longitude=round(asc_lon, 4),
        ascendant_rashi_name_en=RASHIS_DATA[asc_rashi_idx]["name_en"],
        ascendant_nakshatra_name=NAKSHATRAS_DATA[asc_nak_idx]["name"],
        calculation=CalculationMeta(
            engine="swiss_ephemeris",
            engine_version=getattr(swe, "version", None),
            ephemeris="Swiss Ephemeris built-in (Moshier analytical, sub-arcsecond)",
            ayanamsa_key=payload.ayanamsa,
            house_system_key="whole_sign",
            node_type="mean",
            julian_day_ut=round(jd_ut, 6),
            warnings=[tz_info.note] if tz_info.note else [],
        ),
    )

