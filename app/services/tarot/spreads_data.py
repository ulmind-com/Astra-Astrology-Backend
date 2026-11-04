"""Tarot Spreads Definition and Position Architecture."""

from __future__ import annotations
from typing import Any

ALL_SPREADS: list[dict[str, Any]] = [
    {
        "id": "daily_guidance",
        "name": "Card of the Day",
        "category": "general",
        "card_count": 1,
        "description": "Daily single-card divine reflection illuminating your prevailing cosmic atmosphere, key challenge, and actionable blessing.",
        "ideal_for": "Morning contemplation, daily meditation, or quick focal clarity.",
        "positions": [
            {
                "index": 1,
                "title": "Daily Cosmic Atmosphere",
                "role": "core_energy",
                "description": "The dominant energetic theme, opportunity, and conscious mindset for today.",
            }
        ],
    },
    {
        "id": "past_present_future",
        "name": "Past – Present – Future",
        "category": "general",
        "card_count": 3,
        "description": "The classic tripartite timeline showing the karmic genesis of your situation, its present manifestation, and where the momentum leads.",
        "ideal_for": "General life questions, situational audits, understanding the flow of events.",
        "positions": [
            {
                "index": 1,
                "title": "The Foundation (Past)",
                "role": "root_cause",
                "description": "Past events, subconscious choices, or karmic influences that created this situation.",
            },
            {
                "index": 2,
                "title": "The Crucible (Present)",
                "role": "current_state",
                "description": "Where you stand right now, the active energy at play, and what requires your conscious attention.",
            },
            {
                "index": 3,
                "title": "The Horizon (Future)",
                "role": "projected_outcome",
                "description": "The likely outcome if current momentum continues, along with the lesson awaiting you.",
            },
        ],
    },
    {
        "id": "two_choices",
        "name": "Two Choices Crossroad",
        "category": "general",
        "card_count": 4,
        "description": "Invaluable spread when torn between two job offers, two partners, or two major life directions.",
        "ideal_for": "Decision-making, career crossroads, relocation choices, or strategic dilemmas.",
        "positions": [
            {
                "index": 1,
                "title": "The Core Dilemma",
                "role": "central_theme",
                "description": "The true underlying question and psychological state driving this decision.",
            },
            {
                "index": 2,
                "title": "Path A: First Option",
                "role": "option_one",
                "description": "Energy, challenges, and long-term implications of choosing the first path.",
            },
            {
                "index": 3,
                "title": "Path B: Second Option",
                "role": "option_two",
                "description": "Energy, challenges, and long-term implications of choosing the second path.",
            },
            {
                "index": 4,
                "title": "The Harmonizing Factor",
                "role": "higher_guidance",
                "description": "What you need to know to make the highest soul-aligned choice with peace of mind.",
            },
        ],
    },
    {
        "id": "love_soulmate",
        "name": "Love & Soulmate Mirror",
        "category": "love",
        "card_count": 5,
        "description": "Illuminates the sacred energetic mirror between two souls: feelings, unspoken thoughts, karmic friction, and the future bond.",
        "ideal_for": "Romantic relationships, marriage questions, reconciling conflicts, or twin flame dynamics.",
        "positions": [
            {
                "index": 1,
                "title": "Your True Emotional Energy",
                "role": "self_feeling",
                "description": "How you truly feel deep in your heart, including your conscious and unconscious desires.",
            },
            {
                "index": 2,
                "title": "Their Heart & Hidden Perspective",
                "role": "partner_feeling",
                "description": "How your partner perceives the bond, their emotional state, and what they may not say aloud.",
            },
            {
                "index": 3,
                "title": "The Sacred Bond (The Bridge)",
                "role": "connection_dynamic",
                "description": "The collective dynamic between both of you, chemistry, and shared karmic purpose.",
            },
            {
                "index": 4,
                "title": "The Karmic Shadow (The Obstacle)",
                "role": "challenge",
                "description": "Fears, communication blocks, or external interference testing the bond.",
            },
            {
                "index": 5,
                "title": "The Union's Destiny (Future)",
                "role": "outcome",
                "description": "Where this relationship is heading and how to nurture it into highest harmony.",
            },
        ],
    },
    {
        "id": "career_wealth",
        "name": "Career & Wealth Pathway",
        "category": "career",
        "card_count": 5,
        "description": "Direct, practical, and strategic diagnostic of your professional status, financial traps, and prosperous breakthrough action.",
        "ideal_for": "Job changes, promotion audits, business launches, investments, and wealth building.",
        "positions": [
            {
                "index": 1,
                "title": "Current Professional Stance",
                "role": "current_career",
                "description": "Your current career standing, reputation, and energetic foundation.",
            },
            {
                "index": 2,
                "title": "Hidden Asset / Unseen Opportunity",
                "role": "hidden_advantage",
                "description": "A talent, ally, market shift, or opportunity you might be overlooking.",
            },
            {
                "index": 3,
                "title": "The Career Obstacle",
                "role": "vulnerability",
                "description": "What is holding back your promotion, income, or professional expansion.",
            },
            {
                "index": 4,
                "title": "The Strategic Action",
                "role": "action_step",
                "description": "The exact bold, intelligent move you must make right now to shift momentum.",
            },
            {
                "index": 5,
                "title": "Financial & Professional Harvest",
                "role": "material_outcome",
                "description": "The financial reward, authority, and status outcome waiting on this trajectory.",
            },
        ],
    },
    {
        "id": "celtic_cross",
        "name": "The Grand Celtic Cross",
        "category": "general",
        "card_count": 10,
        "description": "The historic, legendary 10-card esoteric spread providing an exhaustive 360° audit of your destiny, psychology, environment, and ultimate resolution.",
        "ideal_for": "Deep spiritual inquiries, life-defining transitions, major turning points.",
        "positions": [
            {
                "index": 1,
                "title": "The Present (Heart of the Matter)",
                "role": "core_present",
                "description": "The central situation or energetic reality you are experiencing right now.",
            },
            {
                "index": 2,
                "title": "The Cross (Immediate Challenge)",
                "role": "crossing_force",
                "description": "The immediate obstacle, opposition, or friction crossing your path.",
            },
            {
                "index": 3,
                "title": "The Root (Unconscious Foundation)",
                "role": "subconscious_basis",
                "description": "Deep-seated beliefs, past karma, or unconscious drivers anchoring this issue.",
            },
            {
                "index": 4,
                "title": "The Recent Past (Passing Energy)",
                "role": "departing_influence",
                "description": "Events or feelings that have just occurred and are now receding.",
            },
            {
                "index": 5,
                "title": "The Crown (Higher Potential)",
                "role": "aspirational_goal",
                "description": "The best possible outcome and what you consciously aspire to achieve.",
            },
            {
                "index": 6,
                "title": "The Near Future (Imminent Arrival)",
                "role": "incoming_event",
                "description": "The next significant event or emotional shift arriving in the coming weeks.",
            },
            {
                "index": 7,
                "title": "The Self (Internal Attitude)",
                "role": "self_view",
                "description": "How you perceive yourself, your personal power, and your current mindset.",
            },
            {
                "index": 8,
                "title": "The Environment (External Forces)",
                "role": "external_influence",
                "description": "How friends, family, coworkers, and external environments impact your journey.",
            },
            {
                "index": 9,
                "title": "Hopes and Fears (The Secret Mind)",
                "role": "hopes_and_fears",
                "description": "Your deepest hopes and secret anxieties surrounding this situation.",
            },
            {
                "index": 10,
                "title": "The Culmination (Karmic Resolution)",
                "role": "ultimate_outcome",
                "description": "The final outcome, synthesis of all energies, and ultimate lesson of this chapter.",
            },
        ],
    },
]

SPREADS_BY_ID: dict[str, dict[str, Any]] = {s["id"]: s for s in ALL_SPREADS}

