"""Pydantic schemas for Vedic, Chaldean, Name, and Mobile Numerology."""

from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core Vedic & Lo Shu Schemas
# ---------------------------------------------------------------------------

class MulankProfile(BaseModel):
    number: int
    planet: str
    planet_hi: str
    deity: str
    metal: str
    colors: list[str]
    unlucky_colors: list[str]
    direction: str
    lucky_numbers: list[int]
    unlucky_numbers: list[int]
    beej_mantra: str
    jap_count: int
    gemstone: str
    lucky_days: list[str]
    lucky_months: list[str]
    grains_daan: str
    health_traits: str
    profession: str


class BhagyankProfile(BaseModel):
    number: int
    planet: str
    life_path_summary: str
    strengths: list[str]
    karmic_lessons: str


class LoShuGridCell(BaseModel):
    digit: int
    count: int
    element: str
    direction: str
    meaning: str


class LoShuPlane(BaseModel):
    name: str
    digits: list[int]
    present_digits: list[int]
    status: str  # "Complete" (100%), "Partial" (33%-66%), "Missing" (0%)
    percentage: int
    significance: str


class MissingNumberRemedy(BaseModel):
    digit: int
    element: str
    impact: str
    remedy: str
    rudraksha: str
    crystal: str


class DigitRepetitionItem(BaseModel):
    digit: int
    count: int
    effect: str


class RajYogaItem(BaseModel):
    name: str
    digits: list[int]
    is_active: bool
    description: str


class NumerologyDashaPeriod(BaseModel):
    level: str  # "MD", "AD", "PD", "SD"
    planet: str
    number: int
    start_date: str
    end_date: str
    duration_days: float
    friendship_score: str  # "Favorable", "Neutral", "Unfavorable"
    guidance: str


# ---------------------------------------------------------------------------
# Name Numerology Schemas
# ---------------------------------------------------------------------------

class LetterSoundProfile(BaseModel):
    letter: str
    value: int
    sound_element: str
    personality_vibration: str
    health_tendency: str
    direction_affinity: str


class NameAnalysisResponse(BaseModel):
    full_name: str
    chaldean_total: int
    single_number: int
    compound_number: int
    compound_name: str
    compound_description: str
    is_favorable_compound: bool
    letters: list[LetterSoundProfile]
    negative_syllables_found: list[str]
    first_letter_vibration: str
    harmony_with_mulank: str
    harmony_with_bhagyank: str
    overall_name_verdict: str
    recommendation: str


# ---------------------------------------------------------------------------
# Mobile Numerology Schemas
# ---------------------------------------------------------------------------

class MobileConjunctionPair(BaseModel):
    pair: str
    first_digit: int
    second_digit: int
    dominance_formula: str  # "First digit (60%) / Second digit (40%)"
    category: str  # "Good", "Neutral", "Malefic"
    manifestation: str
    dob_resonance: bool  # True if pair appears in native's DOB


class MobileLShape(BaseModel):
    corner_digit: int
    arm_digits: list[int]
    shape_code: str
    meaning: str


class MobileAnalysisResponse(BaseModel):
    mobile_number: str
    total_sum: int
    single_digit: int
    compound_number: int
    compound_quality: str
    mulank_compatibility: str
    bhagyank_compatibility: str
    is_recommended: bool
    digit_repetitions: list[DigitRepetitionItem]
    conjunction_pairs: list[MobileConjunctionPair]
    sepharial_grid: dict[str, int]
    l_shapes_formed: list[MobileLShape]
    remedial_injections: list[str]
    profession_affinity: list[str]
    warnings_avoid: list[str]
    overall_verdict: str


# ---------------------------------------------------------------------------
# Main Request / Response Payloads
# ---------------------------------------------------------------------------

class NumerologyCalculateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100, description="Native's full name")
    birth_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Birth date YYYY-MM-DD")
    gender: str = Field(default="male", pattern=r"^(male|female|other)$", description="Native's gender")
    mobile_number: str | None = Field(default=None, description="Optional 10-digit mobile number")
    prediction_year: int | None = Field(default=None, description="Optional target year for yearly forecast")


class NumerologyCalculateResponse(BaseModel):
    name: str
    birth_date: str
    mulank: MulankProfile
    bhagyank: BhagyankProfile
    kua_number: int
    year_prediction_number: int
    year_prediction_summary: str
    lo_shu_grid: list[LoShuGridCell]
    planes: list[LoShuPlane]
    raj_yogas: list[RajYogaItem]
    digit_repetitions: list[DigitRepetitionItem]
    missing_numbers_remedies: list[MissingNumberRemedy]
    dasha_timeline: list[NumerologyDashaPeriod]
    name_analysis: NameAnalysisResponse
    mobile_analysis: MobileAnalysisResponse | None = None
