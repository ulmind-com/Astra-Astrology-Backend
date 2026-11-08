"""Tests for the in-app product guide.

The guide is what answers "how do I use the kundli feature?". It has to be
right about three things that are easy to get wrong: which feature a question
is about, what the feature costs *right now*, and whether this particular user
can pay for it.
"""

from __future__ import annotations

import pytest

from app.services.ai import product_guide
from app.services.ai.product_guide import FEATURES, describe, find, index


class Settings:
    """Stand-in for platform settings, so these need no database."""

    kundli_coins = 20
    kundli_enabled = True
    kundli_matching_coins = 20
    kundli_matching_enabled = True
    palm_reading_coins = 25
    palm_reading_enabled = True
    daily_horoscope_coins = 0
    daily_horoscope_enabled = True
    vastu_coins = 25
    vastu_enabled = False  # switched off, to prove it is reported


# ---------------------------------------------------------------------------
# Finding the right feature
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "question,expected",
    [
        ("Kundli features ta kivabe use korbo?", "kundli"),
        ("how do I get my birth chart", "kundli"),
        ("আমার কুন্ডলী কীভাবে বানাবো", "kundli"),
        ("how does palm reading work", "palm"),
        ("where is the vastu compass", "vastu"),
        ("how do I recharge my wallet", "wallet"),
        ("what does numerology cost", "numerology"),
        ("how do I book an appointment", "appointments"),
        ("how do I talk to an astrologer", "astrologers"),
        ("how do I save my birth details", "birth_details"),
    ],
)
def test_finds_the_feature(question, expected):
    feature = find(question)
    assert feature is not None, question
    assert feature.key == expected


def test_longest_alias_wins():
    """"kundli matching" must not be answered with the kundli page."""
    assert find("how do I do kundli matching").key == "kundli_matching"
    assert find("kundli milan kaise kare").key == "kundli_matching"


def test_unrelated_question_matches_nothing():
    assert find("what is my dasha") is None or find("what is my dasha").key == "dasha"
    assert find("hello there") is None


# ---------------------------------------------------------------------------
# Describing it
# ---------------------------------------------------------------------------
def test_describe_carries_steps_and_route():
    out = describe(product_guide.BY_KEY["kundli"], Settings(), balance=100)
    assert out["where"] == "/kundli"
    assert len(out["steps"]) >= 3
    assert out["cost_coins"] == 20


def test_affordable_when_balance_is_enough():
    out = describe(product_guide.BY_KEY["kundli"], Settings(), balance=50)
    assert out["can_afford"] is True
    assert "short_by_coins" not in out


def test_says_how_many_coins_short():
    out = describe(product_guide.BY_KEY["palm"], Settings(), balance=10)
    assert out["can_afford"] is False
    assert out["short_by_coins"] == 15
    assert out["recharge_at"] == "/account/wallet"


def test_exact_balance_is_affordable():
    out = describe(product_guide.BY_KEY["kundli"], Settings(), balance=20)
    assert out["can_afford"] is True


def test_signed_out_is_told_to_sign_in_not_to_recharge():
    """Telling a visitor to top up an account they do not have reads as broken."""
    out = describe(product_guide.BY_KEY["kundli"], Settings(), balance=None)
    assert out["wallet"] == "not signed in"
    assert "can_afford" not in out
    assert "short_by_coins" not in out
    assert "Sign in" in out["note"]


def test_free_feature_is_marked_free():
    out = describe(product_guide.BY_KEY["daily_horoscope"], Settings(), balance=0)
    assert out["cost_coins"] == 0
    assert out["is_free"] is True
    # Nothing to afford, so no shortfall even on an empty wallet.
    assert "short_by_coins" not in out


def test_disabled_feature_is_reported():
    out = describe(product_guide.BY_KEY["vastu"], Settings(), balance=100)
    assert out["currently_unavailable"] is True


def test_prices_come_from_settings_not_from_here():
    """An admin changing a price must change what the guide quotes."""
    cheap = Settings()
    cheap.kundli_coins = 5
    out = describe(product_guide.BY_KEY["kundli"], cheap, balance=10)
    assert out["cost_coins"] == 5
    assert out["can_afford"] is True


def test_describe_works_without_settings():
    out = describe(product_guide.BY_KEY["kundli"], None, None)
    assert out["steps"]
    assert "cost_coins" not in out


# ---------------------------------------------------------------------------
# The index
# ---------------------------------------------------------------------------
def test_index_lists_every_feature_with_a_route():
    rows = index(Settings())
    assert len(rows) == len(FEATURES)
    for row in rows:
        assert row["where"].startswith("/")
        assert row["feature"]


def test_index_stays_small():
    """It goes into a model's context against a per-minute token budget."""
    import json

    assert len(json.dumps(index(Settings()))) < 1800


# ---------------------------------------------------------------------------
# The catalogue itself
# ---------------------------------------------------------------------------
def test_every_feature_is_well_formed():
    keys = set()
    for f in FEATURES:
        assert f.key not in keys, f"duplicate key {f.key}"
        keys.add(f.key)
        assert f.route.startswith("/"), f.key
        assert f.steps, f.key
        assert f.does.endswith("."), f.key
        assert f.aliases, f.key


def test_aliases_are_lowercase():
    # `find` lowercases the question, so an uppercase alias could never match.
    for f in FEATURES:
        for alias in f.aliases:
            assert alias == alias.lower(), f"{f.key}: {alias}"


# ---------------------------------------------------------------------------
# Full coverage of the app
#
# The catalogue is the assistant's only knowledge of the product. A feature
# missing from it is a feature the assistant will deny exists.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "question,expected",
    [
        ("how do I use the live chat", "live_chat"),
        ("live chat kivabe korbo", "live_chat"),
        ("how do I change my password", "security"),
        ("I forgot my password what do I do", "security"),
        ("পাসওয়ার্ড ভুলে গেছি কী করব", "security"),
        ("how does billing work here", "billing"),
        ("koto coin kata hobe", "billing"),
        ("আমার কত খরচ হবে", "billing"),
        ("how do I add a delivery address", "addresses"),
        ("what are you", "ai_astrologer"),
        ("why does my palm scan keep failing", "palm"),
        ("কম্পাস ঠিক কাজ করছে না কেন", "vastu"),
    ],
)
def test_finds_the_newer_topics(question, expected):
    feature = find(question)
    assert feature is not None, question
    assert feature.key == expected, f"{question!r} -> {feature.key}"


def test_troubleshooting_notes_are_available():
    """"Why does my palm scan fail" needs more than a list of clicks."""
    class S:
        palm_reading_coins = 25
        palm_reading_enabled = True

    out = describe(product_guide.BY_KEY["palm"], S(), balance=100)
    assert out["good_to_know"]
    joined = " ".join(out["good_to_know"]).lower()
    assert "glare" in joined or "flat" in joined


def test_live_session_billing_rule_is_stated():
    """Users must know they need the whole amount up front, not per minute."""
    out = describe(product_guide.BY_KEY["live_chat"], None, None)
    joined = " ".join(out["good_to_know"]).lower()
    assert "up front" in joined or "×" in joined


def test_every_user_facing_route_is_covered():
    """Each page a user can land on should be something the guide can explain."""
    routes = {f.route for f in FEATURES}
    for expected in [
        "/kundli", "/kundli-matching", "/daily-horoscope", "/dasha-calculator",
        "/rashi-calculator", "/nakshatra-calculator", "/kp-calculator",
        "/numerology", "/vastu", "/palm-reading", "/face-reading",
        "/astrologers", "/appointments", "/ai-astrologer",
        "/account/wallet", "/account/birth-details", "/account/security",
        "/account/addresses",
    ]:
        assert expected in routes, f"no feature explains {expected}"
