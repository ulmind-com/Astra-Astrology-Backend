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
