"""Schemas for Tarot Card Reading Engine."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


ArcanaType = Literal["major", "minor"]
SuitType = Literal["wands", "cups", "swords", "pentacles"]
OrientationType = Literal["upright", "reversed"]
QuestionCategory = Literal["general", "love", "career", "finance", "spiritual"]


class CardAspectInterpretation(BaseModel):
    general: str
    love: str
    career: str
    finance: str
    spiritual: str
    keywords: list[str] = Field(default_factory=list)


class TarotCardSchema(BaseModel):
    id: str
    name: str
    arcana: ArcanaType
    suit: SuitType | None = None
    number: int
    element: str  # "Fire", "Water", "Air", "Earth", "Spirit"
    astrology: str  # e.g. "Aries", "Uranus", "Venus"
    vedic_graha: str  # e.g. "Surya", "Chandra", "Mangal"
    image_slug: str
    numerology: str | None = None
    timing_window: str | None = None
    timing_season: str | None = None
    timing_speed: str | None = None
    yes_no: str | None = None
    one_liner: str | None = None
    symbols: list[str] = Field(default_factory=list)
    professions: list[str] = Field(default_factory=list)
    upright: CardAspectInterpretation
    reversed: CardAspectInterpretation
    remedy: str
    affirmation: str


class SpreadPosition(BaseModel):
    index: int
    title: str
    role: str
    description: str


class SpreadConfig(BaseModel):
    id: str
    name: str
    category: str
    card_count: int
    description: str
    ideal_for: str
    positions: list[SpreadPosition]


class DrawnCardDetail(BaseModel):
    position_index: int
    position_title: str
    position_role: str
    position_description: str
    card: TarotCardSchema
    orientation: OrientationType
    relevant_interpretation: str
    keywords: list[str]
    advice: str
    elemental_harmony: str | None = None
    numerology: str | None = None
    timing_window: str | None = None
    timing_season: str | None = None
    timing_speed: str | None = None
    yes_no: str | None = None
    one_liner: str | None = None
    symbols: list[str] = Field(default_factory=list)
    professions: list[str] = Field(default_factory=list)


class TarotDrawRequest(BaseModel):
    spread_id: str = Field(default="past_present_future", description="Spread identifier")
    category: QuestionCategory = Field(default="general", description="Focus area of the question")
    language: Literal["en", "bn", "hi"] = Field(default="en", description="Language: 'en', 'bn', or 'hi'")
    question: str | None = Field(default=None, max_length=500, description="User question or intention")
    user_moon_sign: str | None = Field(default=None, description="Optional Moon sign for astrological alignment")
    active_dasha_lord: str | None = Field(default=None, description="Optional active Dasha planet for planetary resonance")
    selected_indices: list[int] | None = Field(
        default=None, description="Optional specific card indices picked interactively by user"
    )
    intention_seed: int | None = Field(default=None, description="Optional tactile timestamp or entropy seed")


class TarotDrawResponse(BaseModel):
    draw_id: str
    timestamp: str
    spread_id: str
    spread_name: str
    category: QuestionCategory
    language: Literal["en", "bn", "hi"] = "en"
    question: str | None = None
    drawn_cards: list[DrawnCardDetail]
    elemental_breakdown: dict[str, int]
    dominant_element: str
    astrological_resonance: dict[str, Any]
    karmic_synthesis: str
    actionable_guidance: str
    prescribed_remedy: str
    vedic_mantra: str
    predicted_timeframe: str | None = None
    divine_verdict: str | None = None
    timing_breakdown: dict[str, Any] | None = None
    favorable_score: int | None = None
    auspicious_day: str | None = None
    auspicious_color: str | None = None


class DailyTarotRequest(BaseModel):
    category: QuestionCategory = Field(default="general")
    language: Literal["en", "bn", "hi"] = Field(default="en")
    date_str: str | None = Field(default=None, description="YYYY-MM-DD or None for today")
    moon_sign: str | None = None

