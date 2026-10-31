"""Deciding what a question actually needs, before the model is called.

The free tier allows 8,000 tokens a minute, and the whole request is re-sent on
every tool round. Measured on the live service, the fixed overhead was the same
whatever was asked:

    "নমস্কার"                     2,342 input tokens
    "how do I use the kundli?"    2,351
    "আমার রাশি কী?"               2,984

Saying hello cost 2,342 tokens because every tool schema and the whole system
prompt went along with it. A handful of questions a minute exhausted the
allowance, and once it did every user got canned fallback text — which is what
"the AI is not answering properly" actually was. In an evaluation of 28
realistic questions, **every one of the six failures was a rate limit**, not a
mistake in the reasoning.

So the shape of the request is chosen here, locally, with no model call:

* which tools are plausibly needed, if any;
* whether the chart is worth computing and attaching.

The bias is deliberate. Offering a tool that goes unused costs its schema;
*failing* to offer one the question needed costs the answer. So anything
uncertain gets the full set, and only the clear cases are trimmed.
"""

from __future__ import annotations

from typing import Any

from app.services.ai import product_guide, retrieval

#: Tools that answer questions about the product rather than the sky.
GUIDE_TOOLS = ("app_guide_tool",)

#: Always worth offering when the question is about astrology at all: the
#: chart answers most things, and the rule search is the smallest schema here.
CORE_TOOLS = ("calculate_kundli_tool", "search_vedic_rules_tool")

#: Words that make a specific tool worth its schema.
_TRIGGERS: dict[str, tuple[str, ...]] = {
    "get_daily_horoscope_tool": (
        "today", "tomorrow", "aaj", "aj", "ajke", "ajker", "din", "day",
        "week", "now", "tonight", "panchang", "hora", "muhurta", "muhurat",
        "rahu", "tithi", "auspicious", "shubh",
        "আজ", "আজকে", "আজকের", "দিন", "সপ্তাহ", "এখন", "পঞ্চাং", "হোরা",
        "মুহূর্ত", "তিথি", "শুভ", "রাহুকাল",
        "आज", "दिन", "सप्ताह", "अभी", "पंचांग", "होरा", "मुहूर्त", "तिथि", "शुभ",
    ),
    "calculate_numerology_tool": (
        "numerology", "mulank", "bhagyank", "number", "numbers", "name",
        "mobile", "phone", "chaldean", "ank",
        "সংখ্যাতত্ত্ব", "মূলাঙ্ক", "ভাগ্যাঙ্ক", "সংখ্যা", "নাম", "মোবাইল", "নম্বর",
        "अंक", "मूलांक", "भाग्यांक", "संख्या", "नाम", "मोबाइल", "नंबर",
    ),
    "calculate_matchmaking_tool": (
        "matching", "match", "milan", "compatibility", "guna", "gun",
        "ashtakoot", "kundli milan", "partner", "groom", "bride",
        "মিলন", "গুণ", "মিলান", "পাত্র", "পাত্রী", "সামঞ্জস্য",
        "मिलान", "गुण", "कुंडली मिलान", "वर", "वधू",
    ),
    "find_astrologer_tool": (
        "astrologer", "talk", "consult", "expert", "human", "real", "live",
        "call", "chat with",
        "জ্যোতিষী", "কথা", "পরামর্শ", "বিশেষজ্ঞ", "সরাসরি",
        "ज्योतिषी", "बात", "परामर्श", "विशेषज्ञ",
    ),
}

#: A question of this many meaningful words or fewer, naming no subject, is a
#: greeting or an acknowledgement — "নমস্কার", "ok", "thanks", "tell me more".
_CONVERSATIONAL_WORDS = 3


def _terms(question: str) -> set[str]:
    return set(retrieval.tokenize(question))


def is_conversational(question: str) -> bool:
    """Whether this is a greeting or an acknowledgement rather than a question.

    These need no tools and no chart. Sending the full apparatus to answer
    "নমস্কার" cost 2,342 tokens and produced one sentence.
    """
    terms = _terms(question)
    if len(terms) > _CONVERSATIONAL_WORDS:
        return False
    # `_subject_hits` rather than a plain set intersection: it also resolves
    # the translation table and Indic compounds, so "আমার মূলাঙ্ক কত" is seen
    # as a numerology question rather than as small talk. A bare intersection
    # missed it and answered with no tools at all.
    return not retrieval._subject_hits(terms)


def is_about_the_app(question: str) -> bool:
    """Whether this is about using the product rather than about the sky."""
    feature = product_guide.find(question)
    if feature is None:
        return False
    # A feature matched — but "my kundli" matches the kundli page while plainly
    # asking for a reading. Only treat it as a product question when the
    # wording is about *using* something.
    terms = _terms(question)
    return bool(terms & _APP_INTENT)


#: Words that turn "kundli" from a reading into a question about the screen.
_APP_INTENT = frozenset(
    {
        "how", "where", "use", "using", "open", "find", "work", "works",
        "cost", "costs", "price", "charge", "coin", "coins", "wallet",
        "balance", "recharge", "free", "feature", "features", "app", "page",
        "steps", "step", "guide", "help", "button", "menu", "account",
        "kivabe", "kibhabe", "kemne", "kothay", "kaise", "kahan",
        "কীভাবে", "কিভাবে", "কোথায়", "ব্যবহার", "খরচ", "কয়েন", "ওয়ালেট",
        "রিচার্জ", "ফিচার", "অ্যাপ", "পেজ", "ধাপ", "সাহায্য", "ব্যালেন্স",
        "कैसे", "कहाँ", "इस्तेमाल", "खर्च", "कॉयन", "वॉलेट", "रिचार्ज",
        "फीचर", "ऐप", "मदद", "बैलेंस",
    }
)


def select_tool_names(question: str) -> tuple[str, ...]:
    """Which tools to offer for this question.

    Returns an empty tuple when none are worth their schema.
    """
    if is_conversational(question):
        return ()

    if is_about_the_app(question):
        # A product question may still mention an astrologer worth offering.
        names = list(GUIDE_TOOLS)
        if _terms(question) & set(_TRIGGERS["find_astrologer_tool"]):
            names.append("find_astrologer_tool")
        return tuple(names)

    terms = _terms(question)
    names = list(CORE_TOOLS)
    for tool, triggers in _TRIGGERS.items():
        if terms & set(triggers):
            names.append(tool)

    # The guide is cheap and people mix questions: "what's my rashi and how do
    # I see my chart" is one message. Offered whenever any app word appears.
    if terms & _APP_INTENT:
        names.extend(GUIDE_TOOLS)

    return tuple(dict.fromkeys(names))


def select_tools(question: str, all_tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The subset of tool definitions this question justifies sending."""
    wanted = set(select_tool_names(question))
    if not wanted:
        return []
    return [t for t in all_tools if t.get("function", {}).get("name") in wanted]


def needs_chart(question: str) -> bool:
    """Whether the birth chart is worth computing and attaching.

    It costs about 550 tokens in the system context and saves a whole tool
    round when the question is about the chart — but it is pure waste on
    "how do I recharge my wallet", which was being sent the native's full
    planetary positions.
    """
    if is_conversational(question):
        return False
    return not is_about_the_app(question)
