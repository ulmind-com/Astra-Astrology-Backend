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


# ---------------------------------------------------------------------------
# Name Correction & Spelling Harmonizer Schemas
# ---------------------------------------------------------------------------

class NameCorrectionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    mulank: int = Field(default=1, ge=1, le=9)
    bhagyank: int = Field(default=1, ge=1, le=9)
    target_compound: int | None = Field(default=None, description="Optional target compound like 19, 23, 37, 46, 55")


class NameCorrectionSuggestion(BaseModel):
    suggested_spelling: str
    added_letters: list[str]
    new_compound: int
    new_single_digit: int
    compound_title: str
    compound_quality: str
    sound_harmony: str
    why_auspicious: str


class NameCorrectionResponse(BaseModel):
    original_name: str
    original_compound: int
    original_quality: str
    negative_syllables: list[str]
    suggestions: list[NameCorrectionSuggestion]
    general_guidance: str


# ---------------------------------------------------------------------------
# Mobile Sim Comparison Suite Schemas
# ---------------------------------------------------------------------------

class MobileCompareRequest(BaseModel):
    numbers: list[str] = Field(..., min_length=1, max_length=6, description="List of mobile numbers to compare")
    mulank: int = Field(default=1, ge=1, le=9)
    bhagyank: int = Field(default=1, ge=1, le=9)
    profession: str | None = Field(default=None, description="Native's profession e.g. 'it', 'business', 'medicine'")
    birth_date: str | None = Field(default=None, description="Optional DOB YYYY-MM-DD")


class MobileComparisonItem(BaseModel):
    mobile_number: str
    single_digit: int
    compound_number: int
    compound_quality: str
    compatibility_score: int
    grade: str
    positive_pairs: list[str]
    negative_pairs: list[str]
    profession_match: bool
    verdict_bn: str


class MobileCompareResponse(BaseModel):
    best_number: str
    items: list[MobileComparisonItem]
    recommendations_bn: list[str]


# ---------------------------------------------------------------------------
# Business, Brand & Company Name Evaluator Schemas
# ---------------------------------------------------------------------------

class BusinessNumerologyRequest(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., description="e.g. 'technology', 'real_estate', 'finance', 'luxury_fashion', 'health', 'food'")
    owner_mulank: int | None = Field(default=None, ge=1, le=9)
    owner_bhagyank: int | None = Field(default=None, ge=1, le=9)


class BusinessNumerologyResponse(BaseModel):
    brand_name: str
    industry: str
    chaldean_compound: int
    single_digit: int
    compound_meaning: str
    industry_suitability: str
    industry_fit_score: int
    owner_harmony_score: int
    favorable_business_numbers: list[int]
    actionable_recommendations: list[str]


# ---------------------------------------------------------------------------
# Vehicle Plate & Bank Account Numerology Audit Schemas
# ---------------------------------------------------------------------------

class VehicleBankAuditRequest(BaseModel):
    audit_type: str = Field(default="vehicle", pattern=r"^(vehicle|bank)$")
    input_string: str = Field(..., min_length=3, max_length=50)
    mulank: int = Field(default=1, ge=1, le=9)
    bhagyank: int = Field(default=1, ge=1, le=9)


class VehicleBankAuditResponse(BaseModel):
    input_string: str
    audit_type: str
    extracted_digits: str
    total_sum: int
    single_digit: int
    compound_number: int
    compound_quality: str
    safety_rating: str
    risk_alert: str | None = None
    remedy_bn: str

