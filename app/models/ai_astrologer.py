"""Models for Astra AI Astrologer: Knowledge Base, Custom Rules, Sessions, and Feedback."""

from datetime import datetime
from typing import Literal

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.base import TimestampedDocument


class AIKnowledgeDoc(TimestampedDocument):
    """Vedic astrology knowledge chunk extracted from client documents, classical shastras, and literature."""

    title: str = Field(..., max_length=200)
    category: str = Field(..., max_length=60)  # "kundli", "rashi", "nakshatra", "vastu", "numerology", "palmistry", "matchmaking", "general"
    content: str
    tags: list[str] = Field(default_factory=list)
    source_file: str = Field(default="")
    is_active: bool = True

    class Settings:
        name = "ai_knowledge_docs"
        indexes = [
            pymongo.IndexModel([("category", pymongo.ASCENDING)]),
            pymongo.IndexModel([("tags", pymongo.ASCENDING)]),
            pymongo.IndexModel([("is_active", pymongo.ASCENDING)]),
            pymongo.IndexModel([("title", pymongo.TEXT), ("content", pymongo.TEXT)]),
        ]


class AICustomRule(TimestampedDocument):
    """Admin-configured explicit Q&A rules, verified remedies, and priority guidelines."""

    rule_title: str
    trigger_keywords: list[str] = Field(default_factory=list)
    category: str = Field(default="general")
    response_bn: str
    response_en: str = ""
    remedy_bn: str = ""
    priority: int = 1  # Higher priority gets matched first
    is_active: bool = True

    class Settings:
        name = "ai_custom_rules"
        indexes = [
            pymongo.IndexModel([("trigger_keywords", pymongo.ASCENDING)]),
            pymongo.IndexModel([("priority", pymongo.DESCENDING)]),
            pymongo.IndexModel([("is_active", pymongo.ASCENDING)]),
        ]


class ChatMessageItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    citations: list[str] = Field(default_factory=list)
    tools_called: list[str] = Field(default_factory=list)
    suggested_followups: list[str] = Field(default_factory=list)


class AIChatSession(TimestampedDocument):
    """A user conversation session with Astra AI Astrologer."""

    session_id: str = Field(...)
    user_id: PydanticObjectId | None = None
    title: str = "নতুন জ্যোতিষী পরামর্শ"
    birth_details: dict | None = None
    messages: list[ChatMessageItem] = Field(default_factory=list)
    is_active: bool = True

    class Settings:
        name = "ai_chat_sessions"
        indexes = [
            pymongo.IndexModel([("session_id", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel([("user_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("updated_at", pymongo.DESCENDING)]),
        ]


class AIChatFeedback(TimestampedDocument):
    """User feedback on AI responses for continuous self-learning & Human-in-the-Loop review."""

    session_id: str
    message_index: int
    user_query: str
    ai_response: str
    rating: int  # 1 = thumbs up, -1 = thumbs down
    feedback_reason: str = ""
    reviewed_by_admin: bool = False
    admin_corrected_response: str = ""
    added_to_knowledge: bool = False

    class Settings:
        name = "ai_chat_feedback"
        indexes = [
            pymongo.IndexModel([("session_id", pymongo.ASCENDING)]),
            pymongo.IndexModel([("rating", pymongo.ASCENDING)]),
            pymongo.IndexModel([("reviewed_by_admin", pymongo.ASCENDING)]),
            pymongo.IndexModel([("created_at", pymongo.DESCENDING)]),
        ]
