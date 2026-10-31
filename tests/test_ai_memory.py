"""Tests for what the assistant remembers, and for the tag shield.

Both are pure functions over text, so they run without MongoDB or Groq.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.ai import memory
from app.services.ai.memory import TagShield, extract, merge, to_context


# ---------------------------------------------------------------------------
# Extracting facts
# ---------------------------------------------------------------------------
def test_extracts_facts_and_removes_the_tags():
    reply, facts = extract("Your reading.\n\n[REMEMBER: worried about a job change]\n\nGood luck.")
    assert facts == ["worried about a job change"]
    assert "REMEMBER" not in reply
    assert "Your reading." in reply and "Good luck." in reply


def test_extracts_several_facts():
    _, facts = extract("[REMEMBER: works in IT]\n[REMEMBER: Jupiter-Venus until Apr 2028]")
    assert len(facts) == 2


def test_a_reply_with_no_tags_is_untouched():
    reply, facts = extract("Just a reading, nothing to note.")
    assert facts == []
    assert reply == "Just a reading, nothing to note."


def test_secrets_are_never_remembered():
    """Astrology invites intimate disclosure; a memory file is the wrong place."""
    for secret in [
        "[REMEMBER: password is hunter2]",
        "[REMEMBER: card number 4111 1111 1111 1111]",
        "[REMEMBER: his aadhaar is 1234]",
        "[REMEMBER: OTP was 998211]",
        "[REMEMBER: bank account 00123456]",
    ]:
        _, facts = extract(secret)
        assert facts == [], secret


def test_a_long_fact_is_truncated():
    _, facts = extract("[REMEMBER: " + "x" * 500 + "]")
    assert len(facts[0]) <= memory.MAX_FACT_CHARS


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------
def test_merge_keeps_newest_and_caps():
    existing = []
    for i in range(30):
        existing = merge(existing, [f"fact {i}"])
    assert len(existing) == memory.MAX_FACTS
    assert existing[-1]["fact"] == "fact 29"


def test_repeating_a_fact_refreshes_rather_than_duplicates():
    facts = merge([], ["worried about job"])
    facts = merge(facts, ["worried about job"])
    assert len(facts) == 1


def test_stale_facts_are_dropped():
    old = datetime.now(timezone.utc) - timedelta(days=memory.FACT_TTL_DAYS + 5)
    facts = merge([{"fact": "ancient", "at": old}], ["fresh"])
    assert [f["fact"] for f in facts] == ["fresh"]


# ---------------------------------------------------------------------------
# The context block
# ---------------------------------------------------------------------------
def test_no_memory_produces_no_block():
    assert to_context([]) == ""


def test_context_is_bounded():
    """It rides along on every request against an 8,000-token minute."""
    facts = merge([], [f"a fact number {i} with some length to it" for i in range(40)])
    block = to_context(facts)
    assert len(block) <= memory.MAX_CONTEXT_CHARS + 120


def test_context_mentions_when_they_were_last_seen():
    facts = merge([], ["asked about career"])
    block = to_context(facts, datetime.now(timezone.utc) - timedelta(days=30))
    assert "weeks ago" in block or "month" in block


# ---------------------------------------------------------------------------
# The tag shield
# ---------------------------------------------------------------------------
def feed_all(shield: TagShield, chunks: list[str]) -> str:
    return "".join(shield.feed(c) for c in chunks) + shield.flush()


def test_shield_hides_tags_split_across_chunks():
    """Streaming splits tokens anywhere, including inside a tag."""
    out = feed_all(TagShield(), ["Reading.", "\n\n[REMEM", "BER: asked ab", "out job]", "\nDone."])
    assert "REMEMBER" not in out
    assert "Reading." in out and "Done." in out


def test_shield_hides_followups():
    out = feed_all(TagShield(), ["Text ", "[FOLLOW_UP: What next?]"])
    assert "FOLLOW_UP" not in out
    assert out.strip() == "Text"


def test_shield_passes_ordinary_brackets_through():
    out = feed_all(TagShield(), ["See the note ", "[in brackets]", " here"])
    assert out == "See the note [in brackets] here"


def test_shield_releases_an_unclosed_bracket_at_the_end():
    out = feed_all(TagShield(), ["trailing [unclosed"])
    assert out == "trailing [unclosed"


def test_shield_does_not_delay_ordinary_text():
    """Text with no bracket must appear immediately, or streaming stutters."""
    shield = TagShield()
    assert shield.feed("hello ") == "hello "
    assert shield.feed("world") == "world"


def test_shield_handles_many_tags():
    out = feed_all(
        TagShield(),
        ["A", "[REMEMBER: one]", "B", "[FOLLOW_UP: q1]", "C", "[REMEMBER: two]", "D"],
    )
    assert out == "ABCD"
