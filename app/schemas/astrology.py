"""Schemas for Rashi (Moon Sign), Nakshatra & Astrology calculation."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class RashiCalculateRequest(BaseModel):
    name: str = Field(default="", description="Name of the person")
    gender: Literal["male", "female", "other"] = Field(default="male", description="Gender")
    day: int = Field(ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(ge=1, le=12, description="Month of birth (1-12)")
    year: int = Field(ge=1800, le=2100, description="Year of birth (e.g. 2004)")
    hour: int = Field(default=12, ge=0, le=23, description="Hour of birth (0-23 in 24hr or 1-12 with period)")
    minute: int = Field(ge=0, le=59, default=0, description="Minute of birth (0-59)")
    second: int = Field(ge=0, le=59, default=0, description="Second of birth (0-59)")
    period: Literal["AM", "PM", "24H"] = Field(default="24H", description="Period if 12-hour clock used")
    place: str = Field(default="", description="Birth place name (e.g. Kolkata, West Bengal)")
    latitude: float | None = Field(default=None, description="Decimal latitude (-90 to +90)")
    longitude: float | None = Field(default=None, description="Decimal longitude (-180 to +180)")
    timezone: float = Field(default=5.5, description="Timezone offset from UTC in hours (e.g. +5.5 for IST)")
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


# =============================================================================
# Birth Star & Nakshatra Calculator Schemas
# =============================================================================


class NakshatraCalculateRequest(BaseModel):
    name: str = Field(default="", description="Name of the native")
    gender: Literal["male", "female", "other"] = Field(default="male", description="Gender")
    day: int = Field(ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(ge=1, le=12, description="Month of birth (1-12)")
    year: int = Field(ge=1800, le=2100, description="Year of birth (e.g. 2004)")
    hour: int = Field(default=12, ge=0, le=23, description="Hour of birth (0-23 in 24hr or 1-12 with period)")
    minute: int = Field(ge=0, le=59, default=0, description="Minute of birth (0-59)")
    second: int = Field(ge=0, le=59, default=0, description="Second of birth (0-59)")
    period: Literal["AM", "PM", "24H"] = Field(default="PM", description="Period if 12-hour clock used")
    place: str = Field(default="", description="Birth place name (e.g. Kolkata, West Bengal)")
    latitude: float | None = Field(default=None, description="Decimal latitude (-90 to +90)")
    longitude: float | None = Field(default=None, description="Decimal longitude (-180 to +180)")
    timezone: float = Field(default=5.5, description="Timezone offset from UTC in hours (e.g. +5.5 for IST)")
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


class AvakahadaChakra(BaseModel):
    gana: str  # Deva (দেব), Manushya (মনুষ্য), Rakshasa (রাক্ষস)
    yoni: str  # e.g. Horse, Elephant, Serpent, Lion, etc.
    yoni_animal: str  # Male / Female animal classification
    nadi: str  # Aadi (আদি), Madhya (মধ্য), Antya (অন্ত্য)
    varna: str  # Brahmin, Kshatriya, Vaishya, Shudra
    vashya: str  # Chatuspada, Dwipada/Nara, Jalachara, Keeta, Vanachara
    tatva: str  # Prithvi, Jala, Agni, Vayu, Akasha
    paya: str  # Gold (স্বর্ণ), Silver (রৌপ্য), Copper (তাম্র), Iron (লৌহ)


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


# =============================================================================
# KP Astrology (Krishnamurti Paddhati) Schemas
# =============================================================================


class KPCalculateRequest(BaseModel):
    name: str = Field(default="", description="Name of the native")
    gender: Literal["male", "female", "other"] = Field(default="male", description="Gender")
    day: int = Field(ge=1, le=31, description="Day of birth (1-31)")
    month: int = Field(ge=1, le=12, description="Month of birth (1-12)")
    year: int = Field(ge=1800, le=2100, description="Year of birth (e.g. 2004)")
    hour: int = Field(default=12, ge=0, le=23, description="Hour of birth (0-23 in 24hr or 1-12 with period)")
    minute: int = Field(ge=0, le=59, default=0, description="Minute of birth (0-59)")
    second: int = Field(ge=0, le=59, default=0, description="Second of birth (0-59)")
    period: Literal["AM", "PM", "24H"] = Field(default="PM", description="Period if 12-hour clock used")
    place: str = Field(default="", description="Birth place name (e.g. Kolkata, West Bengal)")
    latitude: float | None = Field(default=None, description="Decimal latitude (-90 to +90)")
    longitude: float | None = Field(default=None, description="Decimal longitude (-180 to +180)")
    timezone: float = Field(default=5.5, description="Timezone offset from UTC in hours")
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


class KPCuspDetail(BaseModel):
    cusp: int  # 1 to 12
    longitude: float
    degree_formatted: str
    sign: str
    sign_index: int
    sign_lord: str
    star_lord: str
    sub_lord: str


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
    rashi_house: int  # 1 to 12 in Rashi chart
    bhav_house: int  # 1 to 12 in Nirayana Bhava Chalit chart
    is_retrograde: bool = False


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
    level: int  # 1: Mahadasha, 2: Antardasha, 3: Pratyantardasha
    start_date: str
    end_date: str
    duration: str
    is_current: bool = False
    insight: KPDashaInsight | None = None
    sub_periods: list["KPDashaPeriod"] = Field(default_factory=list)


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

    selected_language: str = "en"
    translations: dict[str, Any] = Field(default_factory=dict)


