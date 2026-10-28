"""Schemas for Rashi (Moon Sign), Nakshatra & Astrology calculation."""

import math
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class RashiCalculateRequest(BaseModel):
    name: str = Field(default="", description="Name of the person")
    gender: Literal["male", "female", "other"] = Field(default="male", description="Gender")
    day: int = Field(ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(ge=1, le=12, description="Month of birth (1-12)")
    year: int = Field(ge=1800, le=2100, description="Year of birth (e.g. 2004)")
    hour: int | None = Field(default=12, ge=0, le=23, description="Hour of birth (0-23 in 24hr or 1-12 with period)")
    minute: int | None = Field(ge=0, le=59, default=0, description="Minute of birth (0-59)")
    second: int | None = Field(ge=0, le=59, default=0, description="Second of birth (0-59)")
    period: Literal["AM", "PM", "24H"] | None = Field(default="PM", description="Period if 12-hour clock used")
    place: str = Field(default="", description="Birth place name (e.g. Kolkata, West Bengal)")
    latitude: float | None = Field(
        default=None, ge=-90.0, le=90.0, description="Decimal latitude (-90 to +90)"
    )
    longitude: float | None = Field(
        default=None, ge=-180.0, le=180.0, description="Decimal longitude (-180 to +180)"
    )
    timezone: float = Field(
        default=5.5, ge=-12.0, le=14.0,
        description="Timezone offset from UTC in hours (e.g. +5.5 for IST)",
    )
    timezone_name: str | None = Field(
        default=None,
        description=(
            "IANA timezone name for the birth place, e.g. 'Asia/Dhaka'. When given, the "
            "exact offset is resolved at the birth instant, so daylight saving and "
            "historical changes are accounted for and the `timezone` field is ignored. "
            "When omitted the zone is derived from latitude/longitude; `timezone` is "
            "used only if neither is available."
        ),
    )
    ayanamsa: Literal[
        "lahiri",
        "bv_raman",
        "krishnamurti",
        "yukteshwar",
        "suryasiddhanta",
        "true_pushya",
        "true_mula",
    ] = Field(default="lahiri", description="Ayanamsa system to use for Sidereal calculation")
    house_system: Literal["placidus", "equal", "whole_sign", "koch"] = Field(
        default="placidus", description="House system for chart division"
    )
    chart_style: Literal["north_indian", "south_indian", "east_indian"] = Field(
        default="north_indian", description="Visual chart display style"
    )
    language: Literal["en", "bn", "hi"] = Field(
        default="en", description="Preferred language for output traits, cautions, and remedies (en, bn, hi)"
    )


class PlanetPosition(BaseModel):
    name: str
    symbol: str
    sign: str
    sign_index: int
    degree_in_sign: float
    degree_formatted: str
    nakshatra: str
    pada: int
    house: int
    is_retrograde: bool = False


class RashiTraits(BaseModel):
    element: str  # Fiery / Earthy / Airy / Watery
    modality: str  # Movable (Chara) / Fixed (Sthira) / Dual (Dwisvabhava)
    polarity: str  # Masculine (Positive/Day) / Feminine (Negative/Night)
    body_parts: str
    nature: str
    overview: str
    strengths: list[str]
    cautions_and_pitfalls: list[str]  # কি কি থেকে সাবধান থাকতে হবে
    beneficial_actions_and_remedies: list[str]  # কি করলে ভালো হবে
    career_fields: list[str]
    lucky_color: str
    lucky_numbers: list[int]
    lucky_gemstone: str
    lucky_day: str
    ruling_deity: str
    compatible_rashis: list[str]


class ClientRuleEntry(BaseModel):
    """One classification group from the client's resource documents."""

    key: str
    label: str
    value: str
    definition: str
    source: str  # client file and page this group was transcribed from
    application: str | None = None  # the client's own stated predictive use


class GunaReading(BaseModel):
    source: str
    value: str
    note: str


class DisputedGuna(BaseModel):
    """The client's 01.pdf states the Guna classification twice and the two
    statements disagree for six signs. Both readings are returned rather than
    silently picking one."""

    readings: list[GunaReading] = Field(default_factory=list)
    is_disputed: bool = False
    notice: str | None = None


class ClientSignProfile(BaseModel):
    """Everything about a sign that is traceable to a client-supplied document."""

    index: int
    name_en: str
    name_sa: str
    name_bn: str
    name_hi: str
    lord: str
    classifications: list[ClientRuleEntry] = Field(default_factory=list)
    guna: DisputedGuna = Field(default_factory=DisputedGuna)
    body_parts: str = ""
    places: list[str] = Field(default_factory=list)
    trait_keywords: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class TimezoneResolution(BaseModel):
    """How the UTC offset used for the calculation was arrived at."""

    offset_hours: float
    offset_label: str  # e.g. "UTC+05:30"
    zone_name: str | None = None  # IANA name, e.g. "Asia/Dhaka"
    abbreviation: str | None = None  # e.g. "IST", "BST"
    source: str  # "iana" | "manual" | "default"
    is_dst: bool = False
    note: str | None = None


class HouseCusp(BaseModel):
    house: int
    longitude: float
    sign: str
    sign_index: int
    degree_in_sign: float
    degree_formatted: str


class CalculationMeta(BaseModel):
    """Audit trail for the chart, so nothing about its accuracy is implicit."""

    engine: str  # "swiss_ephemeris"
    engine_version: str | None = None
    ephemeris: str  # which ephemeris the positions came from
    ayanamsa_key: str
    house_system_key: str
    node_type: str  # "mean" | "true"
    julian_day_ut: float
    warnings: list[str] = Field(default_factory=list)


class AvakahadaChakra(BaseModel):
    gana: str  # Deva (দেব), Manushya (মনুষ্য), Rakshasa (রাক্ষস)
    yoni: str  # e.g. Horse, Elephant, Serpent, Lion, etc.
    yoni_animal: str  # Male / Female animal classification
    nadi: str  # Aadi (আদি), Madhya (মধ্য), Antya (অন্ত্য)
    varna: str  # Brahmin, Kshatriya, Vaishya, Shudra
    vashya: str  # Chatuspada, Dwipada/Nara, Jalachara, Keeta, Vanachara
    tatva: str  # Prithvi, Jala, Agni, Vayu, Akasha
    paya: str  # Gold (স্বর্ণ), Silver (রৌপ্য), Copper (তাম্র), Iron (লৌহ)


class RashiPlanetaryDignity(BaseModel):
    """Planetary exaltation, debilitation, and natural friendship matrix from client's Basics of Kundali Reading Explained."""

    exalted_planets: list[str] = Field(default_factory=list)
    debilitated_planets: list[str] = Field(default_factory=list)
    own_lord: str = ""
    moolatrikona: str = ""
    ruler_friends: list[str] = Field(default_factory=list)
    ruler_enemies: list[str] = Field(default_factory=list)
    ruler_neutrals: list[str] = Field(default_factory=list)


class ChandraBalaInfo(BaseModel):
    """Classical Lunar strength in real-time transit relative to Janma Rashi."""

    current_moon_sign_index: int
    current_moon_sign_name: str
    house_from_natal_moon: int
    is_auspicious: bool
    status_label: str
    description: str


class SadeSatiStatus(BaseModel):
    """Saturn Sade Sati & Dhaiya real-time transit status relative to Janma Rashi."""

    is_active: bool
    phase_code: str  # "rising", "peak", "setting", "kantaka", "ashtama", "none"
    phase_title: str
    saturn_sign_index: int
    saturn_sign_name: str
    saturn_house_from_moon: int
    impact_level: str  # "high", "medium", "favorable"
    description: str
    remedy_summary: str


class RashiCalculateResponse(BaseModel):
    name: str
    gender: str
    birth_date_formatted: str
    birth_time_formatted: str
    birth_place: str
    latitude: float
    longitude: float
    timezone: float
    ayanamsa_name: str
    ayanamsa_degrees: float

    # Moon Sign (Rashi) Details
    rashi_index: int  # 0 to 11
    rashi_name_en: str
    rashi_name_hi: str
    rashi_name_bn: str
    rashi_symbol: str
    rashi_lord: str

    # Exact moon coordinates
    moon_sidereal_longitude: float
    moon_degree_in_sign: float
    moon_degree_formatted: str  # e.g. 17° 55' 58"

    # Nakshatra Details
    nakshatra_index: int  # 0 to 26
    nakshatra_name: str
    nakshatra_pada: int  # 1 to 4
    nakshatra_lord: str  # Star Lord (KP)
    kp_sub_lord: str  # Sub Lord (KP)

    # Ascendant (Lagna)
    ascendant_longitude: float
    ascendant_rashi_index: int
    ascendant_rashi_name_en: str
    ascendant_degree_formatted: str

    # Comprehensive traits & client rules
    traits: RashiTraits

    # Chart planets and house placements
    planets: list[PlanetPosition]
    house_system: str
    chart_style: str
    selected_language: str = "en"
    translations: dict[str, Any] = Field(default_factory=dict)

    # Rules traceable to the client's own resource documents
    client_rules: ClientSignProfile | None = None
    ascendant_client_rules: ClientSignProfile | None = None
    kp_reference: dict[str, Any] = Field(default_factory=dict)

    # Extended Classical Precision Fields (Avakahada, Navamsha, Chandra Lagna, Chandra Bala, Sade Sati)
    avakahada_chakra: AvakahadaChakra | None = None
    namakshar: str = ""
    navamsha_rashi_index: int = 0
    navamsha_rashi_name_en: str = ""
    navamsha_rashi_name_bn: str = ""
    navamsha_rashi_name_hi: str = ""
    is_vargottama: bool = False
    planetary_dignity: RashiPlanetaryDignity | None = None
    chandra_lagna_planets: list[PlanetPosition] = Field(default_factory=list)
    chandra_bala: ChandraBalaInfo | None = None
    sade_sati_status: SadeSatiStatus | None = None

    # Transparency: how the offset was derived, the real cusps, and engine details
    timezone_resolution: TimezoneResolution | None = None
    house_cusps: list[HouseCusp] = Field(default_factory=list)
    calculation: CalculationMeta | None = None


# =============================================================================
# Birth Star & Nakshatra Calculator Schemas
# =============================================================================


class NakshatraCalculateRequest(BaseModel):
    name: str = Field(default="", description="Name of the native")
    gender: Literal["male", "female", "other"] = Field(default="male", description="Gender")
    day: int = Field(ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(ge=1, le=12, description="Month of birth (1-12)")
    year: int = Field(ge=1800, le=2100, description="Year of birth (e.g. 2004)")
    hour: int | None = Field(default=12, ge=0, le=23, description="Hour of birth (0-23 in 24hr or 1-12 with period)")
    minute: int | None = Field(ge=0, le=59, default=0, description="Minute of birth (0-59)")
    second: int | None = Field(ge=0, le=59, default=0, description="Second of birth (0-59)")
    period: Literal["AM", "PM", "24H"] | None = Field(default="PM", description="Period if 12-hour clock used")
    place: str = Field(default="", description="Birth place name (e.g. Kolkata, West Bengal)")
    latitude: float | None = Field(
        default=None, ge=-90.0, le=90.0, description="Decimal latitude (-90 to +90)"
    )
    longitude: float | None = Field(
        default=None, ge=-180.0, le=180.0, description="Decimal longitude (-180 to +180)"
    )
    timezone: float = Field(
        default=5.5, ge=-12.0, le=14.0,
        description="Timezone offset from UTC in hours (e.g. +5.5 for IST)",
    )
    timezone_name: str | None = Field(
        default=None,
        description=(
            "IANA timezone name for the birth place, e.g. 'Asia/Dhaka'. When given, the "
            "exact offset is resolved at the birth instant, so daylight saving and "
            "historical changes are accounted for and the `timezone` field is ignored. "
            "When omitted the zone is derived from latitude/longitude; `timezone` is "
            "used only if neither is available."
        ),
    )
    ayanamsa: Literal[
        "lahiri",
        "bv_raman",
        "krishnamurti",
        "yukteshwar",
        "suryasiddhanta",
        "true_pushya",
        "true_mula",
    ] = Field(default="lahiri", description="Ayanamsa system to use for Sidereal calculation")
    language: Literal["en", "bn", "hi"] = Field(
        default="en", description="Preferred language for output traits, cautions, and remedies (en, bn, hi)"
    )




class NakshatraPadaDetail(BaseModel):
    pada: int
    rashi_index: int
    rashi_name_en: str
    rashi_name_bn: str
    rashi_name_hi: str
    navamsha_sign: str
    namakshar: str
    namakshar_en: str
    namakshar_bn: str
    namakshar_hi: str
    is_native_pada: bool = False


class TarabalaItem(BaseModel):
    tara_index: int  # 1 to 9 (Janma, Sampat, Vipat, Kshema, Pratyak, Sadhana, Naidhana, Mitra, Param Mitra)
    tara_name: str
    tara_name_bn: str
    tara_name_hi: str
    is_auspicious: bool
    significance: str
    nakshatras: list[str]


class NakshatraTraits(BaseModel):
    overview: str
    strengths: list[str]
    cautions_and_pitfalls: list[str]  # কি কি থেকে সাবধান থাকতে হবে
    beneficial_actions_and_remedies: list[str]  # কি করলে ভালো হবে
    career_fields: list[str]
    lucky_color: str
    lucky_numbers: list[int]
    lucky_gemstone: str
    ruling_deity: str
    symbol: str
    sacred_tree: str
    beej_mantra: str


class PanchangElement(BaseModel):
    index: int
    name: str
    name_en: str
    percentage_elapsed: float | None = None


class TithiDetail(PanchangElement):
    paksha: str
    paksha_en: str


class BirthPanchang(BaseModel):
    """The panchang elements the client's own reference report lists."""

    tithi: TithiDetail
    yoga: PanchangElement
    karana: PanchangElement
    yunja: PanchangElement
    sunrise: str | None = None
    sunset: str | None = None


class DisputedValue(BaseModel):
    """A value we compute but cannot yet source or verify.

    Used where a rule could not be confirmed against any client document AND our
    computed answer disagrees with the client's own reference output. Showing the
    value with the disagreement attached is more useful than silently showing a
    figure we know is contested.
    """

    value: str
    is_disputed: bool = False
    notice: str | None = None
    evidence: list[str] = Field(default_factory=list)


class NakshatraTechnique(BaseModel):
    """One predictive technique from the client's nakshatra books."""

    technique_no: int
    theme: str
    rule: str
    source: str  # book and technique number
    because: list[str] = Field(default_factory=list)  # why it applies to this chart


class NakshatraBookReference(BaseModel):
    """The chapter-opener block as the client's book prints it."""

    lord: str
    deity: str
    symbol: str
    padas: str
    source: str


class ClientNakshatraRules(BaseModel):
    """Techniques from the client's books, evaluated against this chart."""

    nakshatra_index: int
    nakshatra_name: str
    has_client_source: bool
    matched: list[NakshatraTechnique] = Field(default_factory=list)
    not_matched: list[NakshatraTechnique] = Field(default_factory=list)
    total_available: int = 0
    is_afflicted: bool = False
    affliction_reasons: list[str] = Field(default_factory=list)
    book_reference: NakshatraBookReference | None = None
    unavailable_note: str | None = None


class GandantaInfo(BaseModel):
    is_gandanta: bool = False
    gandanta_type: str | None = None
    junction_name_en: str | None = None
    junction_name_bn: str | None = None
    junction_name_hi: str | None = None
    severity: str | None = None
    description_en: str | None = None
    description_bn: str | None = None
    description_hi: str | None = None
    remedies_en: list[str] = Field(default_factory=list)
    remedies_bn: list[str] = Field(default_factory=list)
    remedies_hi: list[str] = Field(default_factory=list)


class PushkaraInfo(BaseModel):
    is_pushkara_navamsha: bool = False
    is_pushkara_bhaga: bool = False
    navamsha_sign_en: str = ""
    navamsha_sign_bn: str = ""
    navamsha_sign_hi: str = ""
    pada_number: int = 1
    degree_in_sign: float = 0.0
    degree_in_sign_formatted: str = ""
    significance_en: str = ""
    significance_bn: str = ""
    significance_hi: str = ""


class DashaBalanceAtBirth(BaseModel):
    dasha_lord_en: str = ""
    dasha_lord_bn: str = ""
    dasha_lord_hi: str = ""
    total_cycle_years: int = 0
    balance_years: int = 0
    balance_months: int = 0
    balance_days: int = 0
    balance_formatted_en: str = ""
    balance_formatted_bn: str = ""
    balance_formatted_hi: str = ""
    elapsed_percentage: float = 0.0
    remaining_percentage: float = 0.0


class DailyTaraBalaInfo(BaseModel):
    current_moon_nakshatra_index: int = 0
    current_moon_nakshatra_name_en: str = ""
    current_moon_nakshatra_name_bn: str = ""
    current_moon_nakshatra_name_hi: str = ""
    tara_step: int = 1
    tara_name_en: str = ""
    tara_name_bn: str = ""
    tara_name_hi: str = ""
    is_auspicious: bool = True
    status_label_en: str = ""
    status_label_bn: str = ""
    status_label_hi: str = ""
    guidance_en: str = ""
    guidance_bn: str = ""
    guidance_hi: str = ""


class NakshatraDispositionInfo(BaseModel):
    disposition_en: str = ""
    disposition_bn: str = ""
    disposition_hi: str = ""
    gunas_en: str = ""
    gunas_bn: str = ""
    gunas_hi: str = ""
    caste_varna_en: str = ""
    caste_varna_bn: str = ""
    caste_varna_hi: str = ""
    gender_en: str = ""
    gender_bn: str = ""
    gender_hi: str = ""
    direction_en: str = ""
    direction_bn: str = ""
    direction_hi: str = ""
    sacred_bird_en: str = ""
    sacred_bird_bn: str = ""
    sacred_bird_hi: str = ""
    suitable_activities_en: list[str] = Field(default_factory=list)
    suitable_activities_bn: list[str] = Field(default_factory=list)
    suitable_activities_hi: list[str] = Field(default_factory=list)


class NakshatraCalculateResponse(BaseModel):
    name: str
    gender: str
    birth_date_formatted: str
    birth_time_formatted: str
    birth_place: str
    latitude: float
    longitude: float
    timezone: float
    ayanamsa_name: str
    ayanamsa_degrees: float

    # Nakshatra Core
    nakshatra_index: int  # 0 to 26
    nakshatra_name_en: str
    nakshatra_name_bn: str
    nakshatra_name_hi: str
    pada: int  # 1 to 4
    star_lord: str  # Vimshottari Lord (e.g. Ketu, Venus, etc.)
    kp_sub_lord: str  # KP Sub-Lord

    # Astronomical Coordinates
    moon_sidereal_longitude: float
    moon_degree_in_nakshatra: float
    moon_degree_in_nakshatra_formatted: str
    moon_degree_in_pada: float
    moon_degree_in_pada_formatted: str
    nakshatra_elapsed_percentage: float

    # Moon Rashi
    rashi_index: int
    rashi_name_en: str
    rashi_name_bn: str
    rashi_name_hi: str
    rashi_lord: str

    # Sacred & Classical Classifications
    symbol: str
    deity: str
    sacred_tree: str
    beej_mantra: str
    current_namakshar: str

    # Avakahada Chakra
    avakahada: AvakahadaChakra

    # All 4 Padas of this Nakshatra
    padas: list[NakshatraPadaDetail]

    # Tarabala (9 Taras with 27 stars)
    tarabala: list[TarabalaItem]

    # Traits & Remedies in selected language
    traits: NakshatraTraits

    selected_language: str = "en"
    translations: dict[str, Any] = Field(default_factory=dict)

    # Panchang elements the client's reference report lists
    panchang: BirthPanchang | None = None

    # Paya is computed but disputed - see DisputedValue
    paya: DisputedValue | None = None

    # Techniques from the client's own nakshatra books, applied to this chart
    client_rules: ClientNakshatraRules | None = None

    # Classifications for the Moon's rashi, from the client's 01.pdf
    rashi_client_rules: ClientSignProfile | None = None

    # Classical Advancements: Gandanta, Pushkara, Dasha Balance, Daily Live Tara Bala, Disposition
    gandanta: GandantaInfo = Field(default_factory=GandantaInfo)
    pushkara: PushkaraInfo = Field(default_factory=PushkaraInfo)
    dasha_balance: DashaBalanceAtBirth = Field(default_factory=DashaBalanceAtBirth)
    daily_tara_bala: DailyTaraBalaInfo = Field(default_factory=DailyTaraBalaInfo)
    disposition: NakshatraDispositionInfo = Field(default_factory=NakshatraDispositionInfo)

    # Transparency: how the offset was derived and what engine produced the chart
    timezone_resolution: TimezoneResolution | None = None
    calculation: CalculationMeta | None = None

    # The chart the techniques were evaluated against
    planets: list[PlanetPosition] = Field(default_factory=list)
    ascendant_longitude: float | None = None
    ascendant_rashi_name_en: str | None = None
    ascendant_nakshatra_name: str | None = None


# =============================================================================
# KP Astrology (Krishnamurti Paddhati) Schemas
# =============================================================================


class KPCalculateRequest(BaseModel):
    name: str = Field(default="", description="Name of the native")
    gender: Literal["male", "female", "other"] = Field(default="male", description="Gender")
    day: int = Field(ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(ge=1, le=12, description="Month of birth (1-12)")
    year: int = Field(ge=1800, le=2100, description="Year of birth (e.g. 2004)")
    hour: int | None = Field(default=12, ge=0, le=23, description="Hour of birth (0-23 in 24hr or 1-12 with period)")
    minute: int | None = Field(ge=0, le=59, default=0, description="Minute of birth (0-59)")
    second: int | None = Field(ge=0, le=59, default=0, description="Second of birth (0-59)")
    period: Literal["AM", "PM", "24H"] | None = Field(default="PM", description="Period if 12-hour clock used")
    place: str = Field(default="", description="Birth place name (e.g. Kolkata, West Bengal)")
    latitude: float | None = Field(
        default=None, ge=-90.0, le=90.0, description="Decimal latitude (-90 to +90)"
    )
    longitude: float | None = Field(
        default=None, ge=-180.0, le=180.0, description="Decimal longitude (-180 to +180)"
    )
    timezone: float = Field(
        default=5.5, ge=-12.0, le=14.0,
        description="Timezone offset from UTC in hours",
    )
    timezone_name: str | None = Field(
        default=None,
        description=(
            "IANA timezone name for the birth place, e.g. 'Asia/Dhaka'. When given, the "
            "exact offset is resolved at the birth instant, so daylight saving and "
            "historical changes are accounted for and the `timezone` field is ignored. "
            "When omitted the zone is derived from latitude/longitude; `timezone` is "
            "used only if neither is available."
        ),
    )
    ayanamsa: Literal[
        "krishnamurti",
        "lahiri",
        "bv_raman",
        "yukteshwar",
        "suryasiddhanta",
        "true_pushya",
    ] = Field(default="krishnamurti", description="Ayanamsa system (KP Krishnamurti by default)")
    house_system: Literal["placidus", "equal", "whole_sign", "koch"] = Field(
        default="placidus", description="House system (Placidus for KP)"
    )
    language: Literal["en", "bn", "hi"] = Field(
        default="en", description="Output language (en, bn, hi)"
    )
    horary_number: int | None = Field(
        default=None, ge=1, le=249, description="Optional KP Horary Seed Number between 1 and 249"
    )


class KPPanchang(BaseModel):
    julian_day: int
    ayanamsa_name: str
    ayanamsa_degrees: float
    house_system: str
    sunrise: str
    sunset: str
    tithi: str
    yoga: str
    karana: str
    day_name: str
    vedic_day_name: str
    balance_dasha: str
    ascendant_sign: str
    ascendant_lord: str
    ascendant_degree: float
    ascendant_degree_formatted: str
    moon_rashi: str
    moon_rashi_lord: str
    moon_nakshatra: str
    moon_nakshatra_lord: str
    moon_degree_formatted: str


class KPRulingPlanets(BaseModel):
    lagna_rashi_lord: str
    lagna_nakshatra_lord: str
    lagna_sub_lord: str
    moon_rashi_lord: str
    moon_nakshatra_lord: str
    moon_sub_lord: str
    day_lord: str
    date_formatted: str
    time_formatted: str
    is_lagna_star_retrograde: bool = False
    is_moon_star_retrograde: bool = False
    discarded_planets: list[str] = Field(default_factory=list)
    fruitful_planets: list[str] = Field(default_factory=list)


class KPCuspDetail(BaseModel):
    cusp: int  # 1 to 12
    longitude: float
    degree_formatted: str
    sign: str
    sign_index: int
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str = ""


class KPPlanetDetail(BaseModel):
    name: str
    symbol: str
    code: str
    longitude: float
    degree_in_sign: float
    degree_formatted: str
    sign: str
    sign_index: int
    nakshatra: str
    pada: int
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str = ""
    rashi_house: int  # 1 to 12 in Rashi chart
    bhav_house: int  # 1 to 12 in Nirayana Bhava Chalit chart
    is_retrograde: bool = False
    is_untenanted: bool = False


class KPDashaInsight(BaseModel):
    overview: str
    career_and_wealth: str
    favorable_actions: list[str]
    cautions_and_pitfalls: list[str]
    remedies: list[str]
    lucky_day: str
    lucky_color: str
    deity: str
    beej_mantra: str
    gayatri_mantra: str


class KPDashaPeriod(BaseModel):
    lord: str
    level: int  # 1: Mahadasha, 2: Antardasha, 3: Pratyantardasha, 4: Sookshma, 5: Pran
    start_date: str
    end_date: str
    duration: str
    is_current: bool = False
    start_time: str = ""
    end_time: str = ""
    insight: KPDashaInsight | None = None
    sub_periods: list["KPDashaPeriod"] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Advanced KP Models (Significators, CSL Life Events, Horary, Aspects, Badhaka)
# -----------------------------------------------------------------------------

class KPPlanetSignificator(BaseModel):
    planet: str
    level_a: list[int] = Field(default_factory=list)  # Houses occupied by star lord (strongest)
    level_b: list[int] = Field(default_factory=list)  # House occupied by the planet
    level_c: list[int] = Field(default_factory=list)  # Houses owned by star lord
    level_d: list[int] = Field(default_factory=list)  # Houses owned by the planet
    all_signified_houses: list[int] = Field(default_factory=list)


class KPHouseSignificator(BaseModel):
    house: int
    level_a: list[str] = Field(default_factory=list)  # Planets in star of planets in this house
    level_b: list[str] = Field(default_factory=list)  # Planets occupying this house
    level_c: list[str] = Field(default_factory=list)  # Planets in star of house lord
    level_d: list[str] = Field(default_factory=list)  # House lord itself


class KPEventAnalysisItem(BaseModel):
    category: str  # "career", "marriage", "wealth", "property", "health", "foreign"
    title: str
    primary_cusp: int
    cuspal_sub_lord: str
    csl_star_lord: str
    csl_sub_lord: str
    favorable_houses: list[int] = Field(default_factory=list)
    unfavorable_houses: list[int] = Field(default_factory=list)
    signified_houses: list[int] = Field(default_factory=list)
    promise_score: int = 50  # 0 to 100
    verdict: str = ""
    description: str = ""
    timing_hint: str = ""


class KPAspectItem(BaseModel):
    planet_1: str
    planet_2: str
    aspect_name: str  # Conjunction, Sextile, Square, Trine, Opposition
    aspect_symbol: str
    angle_degrees: float
    orb_degrees: float
    nature: str  # Harmonious, Challenging, Neutral
    significance: str


class KPBadhakaMarakaInfo(BaseModel):
    ascendant_type: str  # Movable, Fixed, Dual
    badhaka_house: int  # 11 for Movable, 9 for Fixed, 7 for Dual
    badhaka_sign: str
    badhaka_lord: str
    maraka_houses: list[int] = Field(default_factory=lambda: [2, 7])
    maraka_lords: list[str] = Field(default_factory=list)
    badhaka_planets: list[str] = Field(default_factory=list)
    maraka_planets: list[str] = Field(default_factory=list)
    notes: str = ""


class KPHoraryInfo(BaseModel):
    horary_number: int  # 1 to 249
    sub_start_degree: float
    sub_end_degree: float
    sub_span_formatted: str
    sign: str
    sign_lord: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str


class KPRemedyItem(BaseModel):
    planet: str
    house_involved: int
    problem: str
    lal_kitab_upaya: str
    vedic_mantra: str
    charity_recommendation: str


class CurrentRunningDashaInfo(BaseModel):
    mahadasha: str
    antardasha: str
    pratyantardasha: str
    sookshma_dasha: str = ""
    pran_dasha: str = ""
    active_path: str = ""
    md_start: str = ""
    md_end: str = ""
    ad_start: str = ""
    ad_end: str = ""
    pd_start: str = ""
    pd_end: str = ""
    sd_start: str = ""
    sd_end: str = ""
    pran_start: str = ""
    pran_end: str = ""
    remaining_days_ad: int = 0
    remaining_days_md: int = 0
    percentage_completed_ad: float = 0.0
    percentage_completed_md: float = 0.0
    sookshma_periods: list[KPDashaPeriod] = Field(default_factory=list)
    pran_periods: list[KPDashaPeriod] = Field(default_factory=list)


class DashaSandhiChidraInfo(BaseModel):
    is_in_chidra_dasha: bool = False
    is_in_dasha_sandhi: bool = False
    chidra_message: str = ""
    sandhi_message: str = ""
    current_md_lord: str = ""
    next_md_lord: str = ""
    transition_date: str = ""
    days_to_transition: int = 0
    alert_severity: str = "none"  # "none", "warning", "critical"
    precautions: list[str] = Field(default_factory=list)
    remedial_measures: list[str] = Field(default_factory=list)


class PersonalizedDashaPhalaItem(BaseModel):
    planet: str
    lagna: str
    functional_nature: str  # "Yogakaraka", "Functional Benefic", "Functional Malefic", "Maraka", "Neutral"
    houses_owned: list[int] = Field(default_factory=list)
    house_placed: int = 1
    sign_placed: str = ""
    dignity: str = ""  # "Exalted", "Moolatrikona", "Own Sign", "Friendly", "Neutral", "Enemy", "Debilitated"
    is_retrograde: bool = False
    favorability_score: int = 50  # 0 to 100
    overall_impact: str = ""
    career_impact: str = ""
    wealth_impact: str = ""
    relationship_impact: str = ""
    health_impact: str = ""
    gemstone_warning: str = ""
    recommended_remedy: str = ""


class YoginiPeriodItem(BaseModel):
    name: str
    ruler_planet: str
    duration_years: int
    start_date: str
    end_date: str
    is_current: bool = False
    nature: str = ""  # "Benefic", "Malefic", "Neutral"
    significance: str = ""
    sub_periods: list["YoginiPeriodItem"] = Field(default_factory=list)


class YoginiDashaSystem(BaseModel):
    birth_nakshatra: str = ""
    starting_yogini: str = ""
    balance_str: str = ""
    current_yogini: str = ""
    current_sub_yogini: str = ""
    current_cycle_number: int = 1
    periods: list[YoginiPeriodItem] = Field(default_factory=list)
    verdict: str = ""


class DashaTransitSynergy(BaseModel):
    md_lord: str = ""
    md_transit_sign: str = ""
    md_transit_house_from_moon: int = 1
    md_transit_nature: str = ""
    ad_lord: str = ""
    ad_transit_sign: str = ""
    ad_transit_house_from_moon: int = 1
    ad_transit_nature: str = ""
    sade_sati_active: bool = False
    sade_sati_phase: str = "None"
    sade_sati_description: str = ""
    synergy_verdict: str = ""
    synergy_score: int = 50


class DashaTimelineSegment(BaseModel):
    lord: str
    start_date: str
    end_date: str
    age_start: int
    age_end: int
    duration_years: float
    nature: str = "neutral"  # "favorable", "neutral", "challenging"
    favorability_score: int = 50
    theme: str = ""
    is_current: bool = False


class KPCalculateResponse(BaseModel):
    name: str
    gender: str
    birth_date_formatted: str
    birth_time_formatted: str
    birth_place: str
    latitude: float
    longitude: float
    timezone: float

    # Core KP Sections
    panchang: KPPanchang
    ruling_planets_dob: KPRulingPlanets
    ruling_planets_casting: KPRulingPlanets
    cusps: list[KPCuspDetail]
    planets: list[KPPlanetDetail]
    dashas: list[KPDashaPeriod]

    # Advanced KP Capabilities
    untenanted_planets: list[str] = Field(default_factory=list)
    planet_significators: list[KPPlanetSignificator] = Field(default_factory=list)
    house_significators: list[KPHouseSignificator] = Field(default_factory=list)
    life_events: list[KPEventAnalysisItem] = Field(default_factory=list)
    aspects: list[KPAspectItem] = Field(default_factory=list)
    badhaka_maraka: KPBadhakaMarakaInfo | None = None
    horary_details: KPHoraryInfo | None = None
    remedies: list[KPRemedyItem] = Field(default_factory=list)

    # Advanced Dasha Capabilities
    current_running_dasha: CurrentRunningDashaInfo | None = None
    dasha_sandhi_chidra: DashaSandhiChidraInfo | None = None
    personalized_dasha_phala: list[PersonalizedDashaPhalaItem] = Field(default_factory=list)
    yogini_dasha: YoginiDashaSystem | None = None
    dasha_transit_synergy: DashaTransitSynergy | None = None
    dasha_life_timeline: list[DashaTimelineSegment] = Field(default_factory=list)

    selected_language: str = "en"
    translations: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Kundli & Planetary Position Schemas
# =============================================================================

class KundliCalculateRequest(BaseModel):
    name: str = Field(default="Native", description="Name of native")
    gender: Literal["male", "female", "other"] = Field(default="male")
    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=1800, le=2100)
    hour: int | None = Field(default=12, ge=0, le=23)
    minute: int | None = Field(default=0, ge=0, le=59)
    second: int | None = Field(default=0, ge=0, le=59)
    period: Literal["AM", "PM", "24H"] | None = Field(default="PM")
    place: str = Field(default="Kolkata, West Bengal, India")
    latitude: float | None = Field(default=22.5726, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=88.3639, ge=-180.0, le=180.0)
    timezone: float = Field(default=5.5, ge=-12.0, le=14.0)
    timezone_name: str | None = Field(
        default=None,
        description=(
            "IANA timezone name for the birth place. When given, the exact offset is "
            "resolved at the birth instant and `timezone` is ignored."
        ),
    )
    ayanamsa: Literal[
        "lahiri",
        "krishnamurti",
        "bv_raman",
        "yukteshwar",
        "suryasiddhanta",
        "true_pushya",
    ] = Field(default="lahiri")
    house_system: Literal["placidus", "equal", "whole_sign", "koch"] = Field(default="placidus")
    chart_style: Literal["north_indian", "south_indian", "east_indian", "wheel"] = Field(
        default="north_indian"
    )
    language: Literal["en", "bn", "hi"] = Field(default="en")

    @field_validator("timezone", mode="before")
    @classmethod
    def _coerce_timezone(cls, v: Any) -> float:
        if v is None or v == "":
            return 5.5
        try:
            val = float(v)
            if math.isnan(val):
                return 5.5
            return val
        except (ValueError, TypeError):
            return 5.5

    @field_validator("gender", mode="before")
    @classmethod
    def _coerce_gender(cls, v: Any) -> str:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("male", "m"):
                return "male"
            if v_lower in ("female", "f"):
                return "female"
            if v_lower in ("other", "o"):
                return "other"
        return "male"

    @field_validator("chart_style", mode="before")
    @classmethod
    def _coerce_chart_style(cls, v: Any) -> str:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("north", "north_indian"):
                return "north_indian"
            if v_lower in ("south", "south_indian"):
                return "south_indian"
            if v_lower in ("east", "east_indian"):
                return "east_indian"
            if v_lower == "wheel":
                return "wheel"
        return "north_indian"


class KundliPersonalDetails(BaseModel):
    name: str
    gender: str
    date_of_birth: str
    time_of_birth: str
    day: str
    vedic_day: str


class KundliAstronomicalInfo(BaseModel):
    julian_day: int
    ayan_type: str
    house_system: str
    place: str
    longitude_formatted: str
    latitude_formatted: str


class KundliAstroPositions(BaseModel):
    asc_lord: str
    asc: str
    yoga: str
    tithi: str
    sunset: str
    sunrise: str


class KundliPlanetaryInfo(BaseModel):
    bal_dasa: str
    karan: str
    nakshatra_lord: str
    nakshatra: str
    rasi_lord: str
    rasi: str


class KundliChartPlanet(BaseModel):
    name: str
    symbol: str
    code: str
    degree: int
    sign_num: int  # 1 (Aries) to 12 (Pisces) for D1
    house_num: int  # 1 to 12 in D1 Lagna chart
    d9_sign_num: int  # 1 to 12 in D9 Navamsa chart
    d9_house_num: int  # 1 to 12 relative to D9 Lagna
    is_retrograde: bool = False


class KundliTableRow(BaseModel):
    name: str  # "Lagna", "Sun", "house 1"
    longitude_formatted: str  # "21° Leo 35 ' 55\""
    sign: str
    nakshatra: str
    nakshatra_lord: str
    pada: int
    sub_lord: str
    full_degree_formatted: str  # "141° 35 ' 55\""


class KundliDashaPratyantar(BaseModel):
    lord: str
    lord_bn: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False


class KundliDashaAntar(BaseModel):
    lord: str
    duration: str
    end_date: str
    start_date: str = ""
    is_current: bool = False
    pratyantardashas: list[KundliDashaPratyantar] = Field(default_factory=list)


class KundliDashaCard(BaseModel):
    title: str  # "Balance Mahadasha: Saturn 6 Y 0 M 6 D" or "Mahadasha: Mercury - 17 Years"
    lord: str
    years: int
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    antardashas: list[KundliDashaAntar] = Field(default_factory=list)


class KundliYogaItem(BaseModel):
    name: str  # "Mangalik", "Kaal Sarp Dosh", "Budhaditya Yoga", "Gaja Kesari Yoga", "Kemadruma Yoga"
    is_present: bool
    description: str
    auspicious: bool


class KundliActiveYogaDetail(BaseModel):
    name: str
    description: str
    effects: str


class PlanetaryDignityItem(BaseModel):
    planet: str
    planet_bn: str
    planet_hi: str
    sign: str
    sign_bn: str
    house: int
    degree: float
    degree_formatted: str
    dignity: str  # Exalted, Own, Moolatrikona, Friend, Neutral, Enemy, Debilitated
    dignity_bn: str
    dignity_hi: str
    is_combust: bool = False
    is_retrograde: bool = False
    avastha: str  # Bal, Kumar, Yuva, Vriddha, Mrita
    avastha_bn: str
    avastha_hi: str
    neechabhanga: bool = False
    neechabhanga_reason: str | None = None


class HousePredictionItem(BaseModel):
    house_number: int  # 1 to 12
    house_name: str
    house_name_bn: str
    house_name_hi: str
    sign: str
    sign_bn: str
    sign_lord: str
    sign_lord_bn: str
    lord_placement_house: int
    occupants: list[str] = Field(default_factory=list)
    occupants_bn: list[str] = Field(default_factory=list)
    overview: str
    overview_bn: str
    overview_hi: str
    career_wealth_effect: str
    career_wealth_effect_bn: str
    career_wealth_effect_hi: str
    relationship_family_effect: str
    relationship_family_effect_bn: str
    relationship_family_effect_hi: str


class ExtendedYogaItem(BaseModel):
    name: str
    name_bn: str
    name_hi: str
    category: str  # Pancha Mahapurusha, Raj Yoga, Dhana Yoga, Auspicious, Inauspicious
    category_bn: str
    is_present: bool
    description: str
    description_bn: str
    description_hi: str
    effects: str
    effects_bn: str
    effects_hi: str


class DoshaAnalysisItem(BaseModel):
    dosha_name: str
    dosha_name_bn: str
    dosha_name_hi: str
    is_present: bool
    severity: str  # High, Moderate, Mild, Cancelled, None
    severity_bn: str
    percentage: int = 0  # 0 to 100%
    specific_type: str | None = None
    specific_type_bn: str | None = None
    cancellation_reason: str | None = None
    cancellation_reason_bn: str | None = None
    cancellation_rules_applied: list[str] = Field(default_factory=list)
    cancellation_rules_applied_bn: list[str] = Field(default_factory=list)
    remedy: str
    remedy_bn: str
    remedy_hi: str


# =============================================================================
# Ashtakavarga, Kaal Purusha & Nakshatra Deep Predictive Schemas
# =============================================================================

class AshtakavargaPlanetPoints(BaseModel):
    planet: str
    planet_bn: str
    bindus: list[int]  # 12 houses (1 to 12)
    total: int


class AshtakavargaHouseSummary(BaseModel):
    house_num: int
    sign_name: str
    sign_bn: str
    sarvashtakavarga_points: int  # SAV points (average is 28)
    strength: str  # "Very Strong" (>=32), "Strong" (28-31), "Moderate" (25-27), "Weak" (<25)
    strength_bn: str
    interpretation: str
    interpretation_bn: str


class AshtakavargaResult(BaseModel):
    sav: list[int]  # 12 numbers for houses 1 to 12
    total_sav_bindus: int = 337
    bav_by_planet: list[AshtakavargaPlanetPoints] = Field(default_factory=list)
    houses_summary: list[AshtakavargaHouseSummary] = Field(default_factory=list)


class KaalPurushaInsight(BaseModel):
    house_num: int
    rashi_name: str
    rashi_bn: str
    body_part: str
    body_part_bn: str
    karmic_signification: str
    karmic_signification_bn: str
    planetary_influence: str
    planetary_influence_bn: str
    health_guidance: str
    health_guidance_bn: str


class NakshatraPredictiveInsight(BaseModel):
    planet: str
    planet_bn: str
    nakshatra: str
    nakshatra_bn: str
    pada: int
    rule_title: str
    rule_title_bn: str
    prediction: str
    prediction_bn: str
    remedy: str
    remedy_bn: str


class GemstoneItem(BaseModel):
    category: str  # Life Stone (Lagna Lord), Lucky Stone (9th Lord), Career Stone (5th/10th Lord)
    category_bn: str
    stone_name: str
    stone_name_bn: str
    stone_name_hi: str
    sanskrit_name: str
    ruling_planet: str
    ruling_planet_bn: str
    metal: str
    metal_bn: str
    finger: str
    finger_bn: str
    wearing_day: str
    wearing_day_bn: str
    beej_mantra: str
    benefit: str
    benefit_bn: str


class PersonalRemedies(BaseModel):
    life_stone: GemstoneItem
    lucky_stone: GemstoneItem
    career_stone: GemstoneItem
    rudraksha_recommendation: str
    rudraksha_recommendation_bn: str
    rudraksha_recommendation_hi: str
    ishta_devata: str
    ishta_devata_bn: str
    ishta_devata_hi: str
    lucky_colors: list[str]
    lucky_colors_bn: list[str]
    lucky_numbers: list[int]
    favorable_direction: str
    favorable_direction_bn: str


class CurrentDashaInfo(BaseModel):
    mahadasha_lord: str
    mahadasha_lord_bn: str
    antardasha_lord: str
    antardasha_lord_bn: str
    start_date: str
    end_date: str
    verdict: str
    verdict_bn: str
    verdict_hi: str
    guidance: str
    guidance_bn: str
    guidance_hi: str


class KundliCalculateResponse(BaseModel):
    personal_details: KundliPersonalDetails
    astronomical_info: KundliAstronomicalInfo
    astro_positions: KundliAstroPositions
    planetary_info: KundliPlanetaryInfo

    d1_planets: list[KundliChartPlanet]
    d9_planets: list[KundliChartPlanet]
    d1_asc_sign: int  # 1-12
    d9_asc_sign: int  # 1-12

    # Advanced Divisional Charts
    d10_planets: list[KundliChartPlanet] = Field(default_factory=list)
    d10_asc_sign: int = 1
    d7_planets: list[KundliChartPlanet] = Field(default_factory=list)
    d7_asc_sign: int = 1

    # Chalit Chart (Bhava Chalit) & Chandra Kundli (Moon Chart)
    chalit_planets: list[KundliChartPlanet] = Field(default_factory=list)
    chalit_asc_sign: int = 1
    moon_chart_planets: list[KundliChartPlanet] = Field(default_factory=list)
    moon_chart_asc_sign: int = 1

    planets_table: list[KundliTableRow]
    houses_table: list[KundliTableRow]
    dashas_grid: list[KundliDashaCard]

    yogas_status: list[KundliYogaItem]
    active_yogas_details: list[KundliActiveYogaDetail]

    # Advanced Classical Vedic Additions
    planetary_dignities: list[PlanetaryDignityItem] = Field(default_factory=list)
    house_predictions: list[HousePredictionItem] = Field(default_factory=list)
    extended_yogas: list[ExtendedYogaItem] = Field(default_factory=list)
    doshas_analysis: list[DoshaAnalysisItem] = Field(default_factory=list)
    remedies: PersonalRemedies | None = None
    current_dasha: CurrentDashaInfo | None = None

    # Ashtakavarga (SAV & BAV)
    ashtakavarga: AshtakavargaResult | None = None

    # Kaal Purusha & Nakshatra Deep Predictive Insights
    kaal_purusha_insights: list[KaalPurushaInsight] = Field(default_factory=list)
    nakshatra_predictive_insights: list[NakshatraPredictiveInsight] = Field(default_factory=list)

    selected_language: str = "en"
    translations: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Kundli Matching (Horoscope Compatibility / 36 Gun Milan) Schemas
# =============================================================================

class KundliMatchingPersonInput(BaseModel):
    name: str = Field(default="Native")
    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=1800, le=2100)
    hour: int | None = Field(default=12, ge=0, le=23)
    minute: int | None = Field(default=0, ge=0, le=59)
    second: int | None = Field(default=0, ge=0, le=59)
    period: Literal["AM", "PM", "24H"] | None = Field(default="PM")
    place: str = Field(default="Kolkata, West Bengal, India")
    latitude: float | None = Field(default=22.5726, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=88.3639, ge=-180.0, le=180.0)
    timezone: float = Field(default=5.5, ge=-12.0, le=14.0)
    timezone_name: str | None = Field(
        default=None,
        description=(
            "IANA timezone name for the birth place. When given, the exact offset is "
            "resolved at the birth instant and `timezone` is ignored."
        ),
    )
    ayanamsa: Literal["lahiri", "krishnamurti", "bv_raman", "yukteshwar"] = Field(default="lahiri")
    house_system: Literal["placidus", "equal", "whole_sign"] = Field(default="placidus")

    @field_validator("timezone", mode="before")
    @classmethod
    def _coerce_timezone(cls, v: Any) -> float:
        if v is None or v == "":
            return 5.5
        try:
            val = float(v)
            if math.isnan(val):
                return 5.5
            return val
        except (ValueError, TypeError):
            return 5.5


class KundliMatchingRequest(BaseModel):
    groom: KundliMatchingPersonInput
    bride: KundliMatchingPersonInput
    language: Literal["en", "bn", "hi"] = Field(default="en")


class KundliMatchingPersonProfile(BaseModel):
    name: str
    birth_date_time: str
    birth_place: str
    janam_rasi: str
    rasi_lord: str
    janam_nakshatra: str
    nakshatra_lord: str
    pada: int
    is_manglik: bool
    manglik_status_text: str  # "Not a Manglik" / "Manglik"
    d1_planets: list[KundliChartPlanet]
    d1_asc_sign: int
    planets_table: list[KundliTableRow]


class KundliMatchingKoota(BaseModel):
    attribute: str  # "Varna", "Vashya", "Tara", "Yoni", "Maitri", "Gan", "Bhakut", "Nadi"
    male: str
    female: str
    out_of: float
    received: float
    area_of_life: str
    description: str = ""


class KundliMatchingDoshas(BaseModel):
    ashtakoot_score: float
    ashtakoot_total: float = 36.0
    rajjoo_dosha: bool
    rajjoo_text: str  # "Yes" / "No"
    vedha_dosha: bool
    vedha_text: str  # "Yes" / "No"
    manglik_match: bool
    manglik_match_text: str  # "Yes" / "No"
    boy_manglik_text: str  # "Not a Manglik" / "Manglik"
    girl_manglik_text: str  # "Not a Manglik" / "Manglik"
    verdict_summary: str


class MarriageLifeForecast(BaseModel):
    ideal_marriage_age_groom: str
    ideal_marriage_age_bride: str
    auspicious_marriage_years: list[int]
    auspicious_marriage_years_text: str
    marital_harmony_score: int  # 0 to 100
    marital_harmony_verdict: str
    marital_harmony_description: str
    children_progeny_score: int  # 0 to 100
    children_progeny_verdict: str
    children_progeny_description: str
    conflict_friction_score: int  # 0 to 100
    conflict_friction_verdict: str
    conflict_friction_description: str
    financial_prosperity_score: int  # 0 to 100
    financial_prosperity_verdict: str
    financial_prosperity_description: str
    future_longevity_score: int  # 0 to 100
    future_longevity_verdict: str
    future_longevity_description: str
    remedies_guidance: list[str] = Field(default_factory=list)


class AvakahadaAttributeItem(BaseModel):
    attribute: str
    male: str
    female: str
    description: str = ""


class DashakootItem(BaseModel):
    attribute: str
    male: str
    female: str
    out_of: float
    received: float
    description: str = ""
    status: str = "Favorable"


class DashakootResult(BaseModel):
    items: list[DashakootItem] = Field(default_factory=list)
    total_received: float = 0.0
    total_out_of: float = 36.0
    porutham_count: int = 0
    is_favorable: bool = True
    verdict: str = ""


class DoshaCancellationInfo(BaseModel):
    dosha_name: str
    is_present: bool
    is_cancelled: bool
    cancellation_reason: str = ""
    shastra_citation: str = ""
    severity: str = "None"
    remedy: str = ""


class RajjuDoshaDetail(BaseModel):
    is_present: bool
    rajju_type: str = ""  # "Shiro", "Kantha", "Udara", "Kati", "Pada"
    body_part: str = ""
    classical_impact: str = ""
    male_rajju: str = ""
    female_rajju: str = ""
    remedy: str = ""


class PapasamyaPlanetDetail(BaseModel):
    planet: str
    house_from_lagna: int | None = None
    house_from_moon: int | None = None
    house_from_venus: int | None = None
    points: float = 0.0


class PapasamyaPersonScore(BaseModel):
    total_points: float = 0.0
    lagna_points: float = 0.0
    moon_points: float = 0.0
    venus_points: float = 0.0
    details: list[PapasamyaPlanetDetail] = Field(default_factory=list)


class PapasamyaResult(BaseModel):
    groom_score: PapasamyaPersonScore
    bride_score: PapasamyaPersonScore
    difference: float = 0.0
    is_balanced: bool = True
    verdict: str = ""
    description: str = ""


class PersonalityTraitReport(BaseModel):
    groom_positive_traits: list[str] = Field(default_factory=list)
    groom_negative_traits: list[str] = Field(default_factory=list)
    groom_summary: str = ""
    bride_positive_traits: list[str] = Field(default_factory=list)
    bride_negative_traits: list[str] = Field(default_factory=list)
    bride_summary: str = ""
    compatibility_summary: str = ""


class DashaPeriodItem(BaseModel):
    level: str
    planet: str
    start_date: str
    end_date: str


class PersonDashaOverview(BaseModel):
    current_mahadasha: str = ""
    current_antardasha: str = ""
    current_pratyantardasha: str = ""
    dasha_sequence: list[DashaPeriodItem] = Field(default_factory=list)


class DashaComparisonResult(BaseModel):
    groom_dasha: PersonDashaOverview
    bride_dasha: PersonDashaOverview
    dasha_sandhi_present: bool = False
    dasha_compatibility_verdict: str = ""
    dasha_compatibility_description: str = ""


class ChartPlanetSet(BaseModel):
    d1_planets: list[KundliChartPlanet] = Field(default_factory=list)
    d9_planets: list[KundliChartPlanet] = Field(default_factory=list)
    chalit_planets: list[KundliChartPlanet] = Field(default_factory=list)
    moon_chart_planets: list[KundliChartPlanet] = Field(default_factory=list)
    d1_asc_sign: int = 1
    d9_asc_sign: int = 1
    chalit_asc_sign: int = 1
    moon_chart_asc_sign: int = 1


class KundliMatchingResponse(BaseModel):
    groom: KundliMatchingPersonProfile
    bride: KundliMatchingPersonProfile
    doshas: KundliMatchingDoshas
    kootas: list[KundliMatchingKoota]
    total_received: float
    total_out_of: float = 36.0
    is_compatible: bool
    verdict: str
    selected_language: str = "en"
    translations: dict[str, Any] = Field(default_factory=dict)
    forecast: MarriageLifeForecast | None = None
    dashakoot: DashakootResult | None = None
    avakahada_comparison: list[AvakahadaAttributeItem] = Field(default_factory=list)
    cancellations: list[DoshaCancellationInfo] = Field(default_factory=list)
    rajju_detail: RajjuDoshaDetail | None = None
    papasamya: PapasamyaResult | None = None
    personality: PersonalityTraitReport | None = None
    dasha_comparison: DashaComparisonResult | None = None
    groom_charts: ChartPlanetSet | None = None
    bride_charts: ChartPlanetSet | None = None
    manglik_detail: dict[str, Any] = Field(default_factory=dict)
    classical_recommendation: str = ""



# -----------------------------------------------------------------------------
# Daily Horoscope (100% In-House Swiss Ephemeris Moon Transit & Panchang Engine)
# -----------------------------------------------------------------------------
class DailyHoroscopeRequest(BaseModel):
    date: str | None = Field(default=None, description="Target date in YYYY-MM-DD format (defaults to current date in IST)")
    sign: str | None = Field(default=None, description="Optional sign filter (e.g. 'aries', 'taurus' or None for all 12 signs)")
    language: Literal["en", "bn", "hi"] = Field(default="en", description="Output language (en, bn, hi)")
    latitude: float = Field(default=22.5726, ge=-90.0, le=90.0, description="Observer latitude (default: Kolkata, 22.5726)")
    longitude: float = Field(default=88.3639, ge=-180.0, le=180.0, description="Observer longitude (default: Kolkata, 88.3639)")
    timezone: float = Field(default=5.5, ge=-12.0, le=14.0, description="Timezone offset from UTC (default: +5.5 for IST)")
    # Personalization options
    birth_nakshatra_index: int | None = Field(default=None, ge=0, le=26, description="Native's Janma Nakshatra index 0 to 26")
    birth_date: str | None = Field(default=None, description="Native birth date YYYY-MM-DD for personalized transit chart")
    birth_time: str | None = Field(default=None, description="Native birth time HH:MM")
    birth_rashi_index: int | None = Field(default=None, ge=0, le=11, description="Native Janma Rashi index 0 to 11")
    birth_lagna_index: int | None = Field(default=None, ge=0, le=11, description="Native Janma Lagna index 0 to 11")


class HoraItem(BaseModel):
    hora_index: int  # 1 to 24
    hora_number: int  # 1 to 12 within Day/Night
    is_day: bool
    start_time: str
    end_time: str
    planet: str
    planet_bn: str
    planet_hi: str
    planet_sa: str
    is_auspicious: bool
    category: str
    category_bn: str
    category_hi: str
    verdict: str
    verdict_bn: str = ""
    verdict_hi: str = ""
    best_activities: str
    best_activities_bn: str
    best_activities_hi: str


class ChoghadiyaItem(BaseModel):
    period_index: int  # 1 to 16
    is_day: bool
    name: str  # Amrit, Shubh, Labh, Char, Rog, Kaal, Udveg
    name_bn: str
    name_hi: str
    ruler_planet: str
    start_time: str
    end_time: str
    status: str  # auspicious, neutral, inauspicious
    guidance: str
    guidance_bn: str
    guidance_hi: str


class PlanetaryDrishtiItem(BaseModel):
    aspecting_planet: str
    aspect_type: str
    yoga_name: str
    yoga_name_bn: str
    yoga_name_hi: str
    is_positive: bool
    impact: str
    impact_bn: str
    impact_hi: str
    classical_remedy: str
    classical_remedy_bn: str
    classical_remedy_hi: str


class PanchakStatus(BaseModel):
    is_panchak: bool = False
    panchak_type: str = "None"
    panchak_type_bn: str = "কোনো পঞ্চক নেই"
    panchak_type_hi: str = "कोई पंचक नहीं"
    severity: str = "auspicious"  # auspicious, mild, caution, severe
    description: str = ""
    description_bn: str = ""
    description_hi: str = ""
    prohibited_activities: list[str] = Field(default_factory=list)


class AshtakavargaTransitPoints(BaseModel):
    sign_index: int
    sarvashtakavarga_points: int = 28
    moon_bhinnashtakavarga_points: int = 4
    strength_grade: str = "Medium (Balanced)"
    strength_grade_bn: str = "মধ্যম (ভারসাম্যপূর্ণ)"
    strength_grade_hi: str = "मध्यम (संतुलित)"
    score_multiplier: float = 1.0


class NumerologyDailySynergy(BaseModel):
    mulank: int  # 1 to 9
    bhagyank: int  # 1 to 9
    ruling_planet: str
    day_relationship: str  # Friend, Neutral, Enemy
    day_relationship_bn: str
    day_relationship_hi: str
    synergy_score_pct: int
    advice: str
    advice_bn: str
    advice_hi: str


class BiorhythmHour(BaseModel):
    hour: int  # 0 to 23
    time_label: str  # "06:00 - 07:00"
    energy_score: int  # 0 to 100
    dominant_graha: str
    status: str
    status_bn: str
    status_hi: str


class DualTransitInsight(BaseModel):
    moon_transit_house: int
    lagna_transit_house: int
    lagna_sign_name: str
    emotional_outlook: str
    emotional_outlook_bn: str
    emotional_outlook_hi: str
    physical_event_outlook: str
    physical_event_outlook_bn: str
    physical_event_outlook_hi: str
    synthesis_verdict: str
    synthesis_verdict_bn: str
    synthesis_verdict_hi: str
    dual_harmony_score: int


class TaraBalaSummary(BaseModel):
    tara_index: int  # 1 to 9
    tara_name: str
    tara_name_bn: str
    tara_name_hi: str
    is_auspicious: bool
    score_percent: int
    verdict: str
    verdict_bn: str
    verdict_hi: str
    guidance: str
    guidance_bn: str
    guidance_hi: str


class PersonalizedNakshatraProfile(BaseModel):
    birth_nakshatra_index: int
    birth_nakshatra_name: str
    birth_nakshatra_name_bn: str
    birth_nakshatra_name_hi: str
    birth_nakshatra_lord: str
    birth_nakshatra_deity: str
    sacred_tree: str
    beej_mantra: str
    tara_bala: TaraBalaSummary


class DailySignHoroscope(BaseModel):
    sign_index: int  # 0 = Aries, 11 = Pisces
    sign_name: str
    sign_name_sanskrit: str
    symbol: str
    transit_house: int  # 1 to 12 (Moon's current transit house from Janma Rashi)
    transit_house_name: str  # e.g. "11th House (Labha Bhava)"
    gochar_verdict: str  # "Highly Auspicious", "Favorable", "Neutral", "Caution Advised"
    overall_score: int  # 0 to 100 percentage score
    career_score: int
    love_score: int
    finance_score: int
    health_score: int
    summary: str
    career_prediction: str
    love_prediction: str
    finance_prediction: str
    health_prediction: str
    lucky_number: int
    lucky_color: str
    lucky_time: str
    remedy: str
    favorable_direction: str
    # Classical Vedic expansions
    is_chandrashtama: bool = False
    chandrashtama_advice: str | None = None
    vedha_active: bool = False
    vedha_planet: str | None = None
    vedha_description: str | None = None
    sade_sati_status: str | None = None
    guru_gochar_verdict: str | None = None
    beej_mantra: str = ""
    charity_dana: str = ""
    tara_bala: TaraBalaSummary | None = None
    # Advanced 100% precision additions
    ashtakavarga: AshtakavargaTransitPoints | None = None
    client_classifications: dict[str, Any] = Field(default_factory=dict)
    nakshatra_pada_shift: dict[str, Any] = Field(default_factory=dict)
    planetary_drishtis: list[PlanetaryDrishtiItem] = Field(default_factory=list)


class DailyPanchangSummary(BaseModel):
    tithi: str
    paksha: str
    nakshatra: str
    nakshatra_pada: int
    yoga: str
    karana: str
    vara: str  # Day of week (e.g. Ravivara / Sunday)
    sunrise: str
    sunset: str
    abhijit_muhurat: str
    rahu_kaal: str
    disha_shoola: str = ""
    disha_remedy: str = ""
    favorable_chandra_rashis: list[str] = Field(default_factory=list)
    horas: list[HoraItem] = Field(default_factory=list)
    choghadiya: list[ChoghadiyaItem] = Field(default_factory=list)
    panchak: PanchakStatus = Field(default_factory=PanchakStatus)


class DailyHoroscopeResponse(BaseModel):
    date: str
    day_of_week: str
    vara_lord: str
    moon_sign: str
    moon_sign_sanskrit: str
    moon_degree: str
    sun_sign: str
    panchang: DailyPanchangSummary
    signs: list[DailySignHoroscope]
    personalized_profile: PersonalizedNakshatraProfile | None = None
    numerology_synergy: NumerologyDailySynergy | None = None
    biorhythm_timeline: list[BiorhythmHour] = Field(default_factory=list)
    dual_transit: DualTransitInsight | None = None
    calculation_meta: dict[str, Any] = Field(default_factory=dict)





