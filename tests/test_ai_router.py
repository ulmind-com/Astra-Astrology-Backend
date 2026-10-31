"""Tests for the request router.

The router decides what a question needs *before* the model is called, which
is what keeps the service inside the free tier's 8,000 tokens a minute. Its
bias is deliberate and is what these tests pin down: offering a tool that goes
unused costs only its schema, while failing to offer one the question needed
costs the answer.
"""

from __future__ import annotations

import pytest

from app.services.ai import router
from app.services.ai.groq_service import ASTRO_TOOLS
from app.services.ai.router import is_conversational, needs_chart, select_tool_names


# ---------------------------------------------------------------------------
# Small talk needs nothing
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "message",
    ["নমস্কার", "ধন্যবাদ", "hello", "thanks", "ok", "আর কিছু বলুন", "tell me more"],
)
def test_small_talk_gets_no_tools_and_no_chart(message):
    assert is_conversational(message)
    assert select_tool_names(message) == ()
    assert not needs_chart(message)


def test_a_short_astrology_question_is_not_small_talk():
    """Brevity is not the test — "আমার মূলাঙ্ক কত" is three words and a reading."""
    for q in ["আমার রাশি?", "মাঙ্গলিক?", "আমার মূলাঙ্ক কত?", "my dasha?"]:
        assert not is_conversational(q), q
        assert select_tool_names(q), q


# ---------------------------------------------------------------------------
# Product questions need the guide, not the ephemeris
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "message",
    [
        "কুন্ডলী ফিচারটা কীভাবে ব্যবহার করব?",
        "how do I use the kundli feature",
        "ওয়ালেট রিচার্জ কীভাবে করব?",
        "what does palm reading cost",
    ],
)
def test_product_questions_get_the_guide_only(message):
    names = select_tool_names(message)
    assert "app_guide_tool" in names
    assert "calculate_kundli_tool" not in names
    # Computing a birth chart to answer "how do I recharge" is pure waste.
    assert not needs_chart(message)


def test_a_reading_is_not_mistaken_for_a_product_question():
    """"my kundli" matches the kundli page but is plainly asking for a reading."""
    names = select_tool_names("আমার কুন্ডলীতে কোন রাজযোগ আছে?")
    assert "calculate_kundli_tool" in names
    assert needs_chart("আমার কুন্ডলীতে কোন রাজযোগ আছে?")


# ---------------------------------------------------------------------------
# The right specialist tool
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "message,expected",
    [
        ("আজকের দিনটা কেমন যাবে?", "get_daily_horoscope_tool"),
        ("how will today go for me", "get_daily_horoscope_tool"),
        ("আমার মূলাঙ্ক কত?", "calculate_numerology_tool"),
        ("what is my life path number", "calculate_numerology_tool"),
        ("কুন্ডলী মিলন করে দিন", "calculate_matchmaking_tool"),
        ("জ্যোতিষীর সাথে কথা বলতে চাই", "find_astrologer_tool"),
        ("I want to talk to a real astrologer", "find_astrologer_tool"),
    ],
)
def test_specialist_tools_are_offered_when_relevant(message, expected):
    assert expected in select_tool_names(message), message


def test_the_core_pair_is_always_offered_for_a_reading():
    """When in doubt the chart and the rule search go along: missing one costs
    the answer, carrying one costs only its schema."""
    for q in ["আমার স্বাস্থ্য কেমন?", "will I go abroad", "আমার শত্রু আছে কি?"]:
        names = select_tool_names(q)
        assert "calculate_kundli_tool" in names, q
        assert "search_vedic_rules_tool" in names, q


# ---------------------------------------------------------------------------
# What it costs
# ---------------------------------------------------------------------------
def test_select_tools_returns_real_definitions():
    tools = router.select_tools("আজকের দিনটা কেমন যাবে?", ASTRO_TOOLS)
    assert tools
    names = {t["function"]["name"] for t in tools}
    assert names == set(select_tool_names("আজকের দিনটা কেমন যাবে?"))


def test_small_talk_sends_no_schemas_at_all():
    assert router.select_tools("নমস্কার", ASTRO_TOOLS) == []


def test_routing_never_offers_a_tool_that_does_not_exist():
    known = {t["function"]["name"] for t in ASTRO_TOOLS}
    for q in [
        "আমার রাশি কী?", "আজ কেমন যাবে?", "কুন্ডলী মিলন", "মূলাঙ্ক",
        "how do I recharge", "নমস্কার", "জ্যোতিষীর সাথে কথা",
    ]:
        assert set(select_tool_names(q)) <= known, q


# ---------------------------------------------------------------------------
# The model chain
#
# The free tier meters two things. A per-minute limit is a pause; a per-day
# limit is not — the allowance does not come back today, and waiting only
# delays the same refusal. Each model has its own daily bucket, so a spent
# model must be stepped over rather than waited for. This is what made the
# assistant go quiet for the rest of the day once the budget ran out.
# ---------------------------------------------------------------------------
from app.services.ai import groq_service  # noqa: E402


def test_a_daily_limit_is_told_apart_from_a_per_minute_one():
    daily = (
        '{"error":{"message":"Rate limit reached for model `openai/gpt-oss-120b` '
        'on tokens per day (TPD): Limit 200000, Used 199168"}}'
    )
    per_minute = (
        '{"error":{"message":"Rate limit reached on tokens per minute (TPM): '
        'Limit 8000, Used 5295. Please try again in 8.6025s"}}'
    )
    assert groq_service._is_daily_limit(daily)
    assert not groq_service._is_daily_limit(per_minute)


def test_a_spent_model_is_stepped_over():
    groq_service._exhausted_until.clear()
    first = groq_service.MODEL_CHAIN[0]
    assert groq_service._available_models(first)[0] == first

    groq_service._mark_exhausted(first)
    remaining = groq_service._available_models(first)
    assert first not in remaining
    assert remaining, "stepping over one model must leave others to try"
    groq_service._exhausted_until.clear()


def test_the_preferred_model_is_tried_first():
    groq_service._exhausted_until.clear()
    second = groq_service.MODEL_CHAIN[1]
    assert groq_service._available_models(second)[0] == second


def test_every_model_spent_still_returns_something_to_try():
    """A cooldown is a guess. Refusing outright because of one would turn a
    stale guess into an outage."""
    groq_service._exhausted_until.clear()
    for model in groq_service.MODEL_CHAIN:
        groq_service._mark_exhausted(model)
    assert groq_service._available_models(groq_service.MODEL_CHAIN[0])
    groq_service._exhausted_until.clear()


def test_the_chain_only_names_models_this_account_has():
    """Checked against the live model list on 31 Oct 2026. A name that 404s
    costs a wasted call on every request that reaches it."""
    assert set(groq_service.MODEL_CHAIN) <= {
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
    }
