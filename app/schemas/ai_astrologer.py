"""Schemas for Astra AI Astrologer chat, custom rules, and feedback review."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BirthDetailsSchema(BaseModel):
    name: str = "User"
    gender: str = "male"
    day: int = Field(..., ge=1, le=31)
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=1900, le=2100)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)
    place: str = "Kolkata"
    lat: float = 22.5726
    lon: float = 88.3639


class AIChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=2000)
    birth_details: BirthDetailsSchema | None = None


class AIChatResponse(BaseModel):
    session_id: str
    reply: str
    tools_called: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    suggested_followups: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIFeedbackRequest(BaseModel):
    session_id: str
    message_index: int = 0
    rating: int = Field(..., ge=-1, le=1)  # 1 for up, -1 for down
    feedback_reason: str = ""


class AICustomRuleCreateRequest(BaseModel):
    rule_title: str = Field(..., min_length=3, max_length=150)
    trigger_keywords: list[str] = Field(..., min_length=1)
    category: str = "general"
    response_bn: str = Field(..., min_length=10)
    response_en: str = ""
    remedy_bn: str = ""
    priority: int = 1


class AICustomRuleUpdateRequest(BaseModel):
    rule_title: str | None = None
    trigger_keywords: list[str] | None = None
    category: str | None = None
    response_bn: str | None = None
    response_en: str | None = None
    remedy_bn: str | None = None
    priority: int | None = None
    is_active: bool | None = None


class AIFeedbackApproveRequest(BaseModel):
    admin_corrected_response: str = Field(..., min_length=10)
    rule_title: str | None = None
    keywords: list[str] | None = None
