"""What the assistant remembers about a person between visits.

An astrologer who forgets you the moment you leave is a search box. One who
opens with "last month you asked about your job — that Venus period I mentioned
starts in nine days" is something else entirely, and the difference is a few
hundred characters of storage.

Two design choices carry this file.

**Facts are written by the model, for free.** Asking a second model to
summarise the conversation would double the cost of every message against a
budget of 8,000 tokens a minute. Instead the model emits `[REMEMBER: ...]`
inline in its reply, exactly as it already emits `[FOLLOW_UP: ...]`, and those
lines are stripped out before the reader sees them. One call, no extra tokens.

**What comes back is strictly bounded.** Memory is prepended to the system
context on every request, so an unbounded store would quietly eat the token
budget until readings started failing. `MAX_FACTS` and `MAX_FACT_CHARS` are the
ceiling, and they are enforced on write as well as on read.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

#: How many remembered facts are kept and replayed. Enough to feel known,
#: small enough that the cost is noise against a reading.
MAX_FACTS = 12

#: Longest a single fact may be. A model asked to remember something sometimes
#: tries to remember a paragraph.
MAX_FACT_CHARS = 160

#: Total characters of memory allowed into the system context. The hard ceiling
#: that stops this growing into the token budget whatever else happens.
MAX_CONTEXT_CHARS = 900

#: A fact older than this is dropped. Charts do not change, but circumstances
#: do: "looking for a job" is useful for a while and then it is wrong.
FACT_TTL_DAYS = 180

#: The tag the model writes to remember something. Mirrors [FOLLOW_UP: …].
REMEMBER_RE = re.compile(r"\[REMEMBER:\s*(.+?)\]", re.IGNORECASE | re.DOTALL)

#: Things that must never be written down, however the model phrases them.
#: Astrology invites people to type intimate things, and a memory file is the
#: wrong place for any of it.
_FORBIDDEN = re.compile(
    r"\b(password|otp|pin|cvv|card\s*number|account\s*number|aadhaar|aadhar"
    r"|pan\s*card|passport|bank)\b",
    re.IGNORECASE,
)


def extract(reply: str) -> tuple[str, list[str]]:
    """Pull `[REMEMBER: …]` out of a reply.

    Returns the reply with the tags removed and the facts found. The tags are
    an instruction to us, not something a reader should ever see.
    """
    facts: list[str] = []
    for match in REMEMBER_RE.finditer(reply or ""):
        fact = " ".join(match.group(1).split())
        if not fact or _FORBIDDEN.search(fact):
            continue
        facts.append(fact[:MAX_FACT_CHARS])
    cleaned = REMEMBER_RE.sub("", reply or "")
    # Collapse the blank lines the removed tags leave behind.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned, facts


def merge(existing: list[dict[str, Any]], new_facts: list[str]) -> list[dict[str, Any]]:
    """Add new facts to what is already known, newest last, bounded.

    A fact that repeats is refreshed rather than duplicated — people ask about
    the same worry more than once, and a memory listing it five times reads as
    broken.
    """
    now = datetime.now(UTC)
    kept: list[dict[str, Any]] = []
    cutoff = now - timedelta(days=FACT_TTL_DAYS)

    for item in existing:
        when = item.get("at")
        if isinstance(when, datetime):
            when_aware = when if when.tzinfo else when.replace(tzinfo=UTC)
            if when_aware < cutoff:
                continue
        kept.append(item)

    for fact in new_facts:
        lowered = fact.lower().strip()
        kept = [k for k in kept if k.get("fact", "").lower().strip() != lowered]
        kept.append({"fact": fact, "at": now})

    return kept[-MAX_FACTS:]


def _ago(when: Any) -> str | None:
    """"three weeks ago", roughly. Precision here would be false precision."""
    if not isinstance(when, datetime):
        return None
    aware = when if when.tzinfo else when.replace(tzinfo=UTC)
    days = (datetime.now(UTC) - aware).days
    if days <= 0:
        return "earlier today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 14:
        return "last week"
    if days < 60:
        return f"{days // 7} weeks ago"
    return f"{days // 30} months ago"


def to_context(facts: list[dict[str, Any]], last_seen: Any = None) -> str:
    """The block handed to the model, or "" when there is nothing to say.

    Truncated to `MAX_CONTEXT_CHARS` from the newest end: if something has to
    be dropped it should be the oldest fact, not the most recent one.
    """
    if not facts:
        return ""

    lines: list[str] = []
    total = 0
    for item in reversed(facts):
        fact = item.get("fact", "").strip()
        if not fact:
            continue
        line = f"- {fact}"
        if total + len(line) > MAX_CONTEXT_CHARS:
            break
        lines.append(line)
        total += len(line)

    if not lines:
        return ""

    header = "\n[WHAT YOU REMEMBER ABOUT THIS USER]"
    seen = _ago(last_seen)
    if seen:
        header += f" (you last spoke {seen})"
    # Oldest first reads more naturally as a history.
    return header + ":\n" + "\n".join(reversed(lines)) + "\n"


async def load(user_id: Any) -> tuple[list[dict[str, Any]], Any]:
    """This user's remembered facts and when they were last seen."""
    if not user_id:
        return [], None
    try:
        from app.models.ai_astrologer import AIUserMemory

        record = await AIUserMemory.find_one(AIUserMemory.user_id == user_id)
        if record is None:
            return [], None
        return list(record.facts or []), record.last_seen_at
    except Exception as exc:  # noqa: BLE001 - memory must never break a reading
        logger.warning("Could not load AI memory: {}", exc)
        return [], None


async def save(user_id: Any, facts: list[dict[str, Any]]) -> None:
    """Write the merged facts back."""
    if not user_id:
        return
    try:
        from app.models.ai_astrologer import AIUserMemory

        now = datetime.now(UTC)
        record = await AIUserMemory.find_one(AIUserMemory.user_id == user_id)
        if record is None:
            record = AIUserMemory(user_id=user_id, facts=facts, last_seen_at=now)
            await record.insert()
            return
        record.facts = facts
        record.last_seen_at = now
        await record.save()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not save AI memory: {}", exc)


async def forget(user_id: Any) -> bool:
    """Erase everything remembered about this person.

    Exists because they are entitled to ask, and because an assistant that
    cannot forget is one people stop telling things to.
    """
    if not user_id:
        return False
    try:
        from app.models.ai_astrologer import AIUserMemory

        record = await AIUserMemory.find_one(AIUserMemory.user_id == user_id)
        if record is None:
            return False
        await record.delete()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not clear AI memory: {}", exc)
        return False


class TagShield:
    """Holds back text that might turn out to be a tag.

    Streaming makes the control tags a problem. `[FOLLOW_UP: …]` and
    `[REMEMBER: …]` arrive at the end of a reply like any other tokens, so a
    naive stream shows the reader the machinery — and `[REMEMBER:` in
    particular is a note the assistant writes to itself about them, which is
    the last thing to put on screen.

    So any text after an unclosed `[` is withheld until the bracket closes. If
    it closes into a tag, the tag is dropped; if it closes into ordinary prose
    — "[see note]" — it is released intact. Normal text is never delayed,
    because text with no open bracket in it has nothing to wait for.
    """

    def __init__(self) -> None:
        self._pending = ""

    def feed(self, chunk: str) -> str:
        """Text safe to show now."""
        self._pending += chunk
        out = ""
        while True:
            start = self._pending.find("[")
            if start == -1:
                out += self._pending
                self._pending = ""
                break
            end = self._pending.find("]", start)
            if end == -1:
                # Unclosed: release what precedes it, hold the rest back.
                out += self._pending[:start]
                self._pending = self._pending[start:]
                break
            segment = self._pending[start : end + 1]
            out += self._pending[:start]
            if not REMEMBER_RE.fullmatch(segment) and not _FOLLOW_UP_RE.fullmatch(segment):
                out += segment
            self._pending = self._pending[end + 1 :]
        return out

    def flush(self) -> str:
        """Whatever is left once the stream ends.

        An unclosed bracket at the end was never a tag, so it is released
        rather than swallowed.
        """
        rest, self._pending = self._pending, ""
        return rest


#: The other tag the reply carries. Matched here so the shield knows both.
_FOLLOW_UP_RE = re.compile(r"\[FOLLOW_UP:\s*(.+?)\]", re.IGNORECASE | re.DOTALL)
