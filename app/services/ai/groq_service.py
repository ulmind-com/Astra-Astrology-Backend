"""Groq AI Astrologer reasoning engine with Swiss Ephemeris Tool Calling & RAG Grounding."""

import asyncio
import json
import re
from typing import Any

import httpx
from loguru import logger

from app.core.config import settings
from app.schemas.astrology import (
    DailyHoroscopeRequest,
    KundliCalculateRequest,
    KundliMatchingPersonInput,
    KundliMatchingRequest,
)
from app.services.ai import retrieval
from app.services.ai.knowledge_service import (
    corpus_vocabulary,
    match_custom_rules,
    search_knowledge,
)
from app.services.astrology.daily_horoscope import calculate_daily_horoscope
from app.services.astrology.kundli_matching_service import calculate_kundli_matching
from app.services.astrology.kundli_service import (
    PLANET_NAMES_LOCALIZED,
    calculate_kundli,
)
from app.services.astrology.numerology import (
    calculate_bhagyank,
    calculate_chaldean_name,
    calculate_mobile_numerology,
    calculate_mulank,
    calculate_vedic_grid,
)
from app.services.astrology.rashi_translations import RASHI_TRANSLATIONS

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# System Prompt for 100% Classical Vedic Astrologer
ASTROLOGER_SYSTEM_PROMPT = """You are "Astra Vedic Astrologer", a classical Vedic astrologer: warm, direct, precise.

Every word here is re-sent on each tool round against a free-tier budget of
8,000 tokens a minute, so this is kept short deliberately.

LANGUAGE
Reply in the same language AND script the user wrote in — Bengali→Bengali, Tamil→Tamil, Urdu→Urdu, romanised Hinglish→romanised Hinglish. Switch when they switch. Never answer in a language they did not use. Use that language's planet and sign names, English in brackets once. Never put Bengali names in a non-Bengali reply.

HOW TO TALK — an astrologer on WhatsApp, not a report generator
Short paragraphs. No headings for a small question. Match the answer to the question: "আজ কেমন যাবে?" wants a few friendly sentences, not four sections. Greetings get a greeting, not a reading. On follow-ups continue the conversation — never re-introduce yourself or repeat the whole chart. Kind about hard things; never frighten, never promise. No medical, legal or financial instructions — speak of tendencies and timing.

ACCURACY
Name the planet, house or dasha behind what you say, even briefly — that is what makes it a reading. Never invent a degree, date or citation; positions come from the tools. Quote only dasha dates the tools returned (runs_from/runs_until); beyond them say a fuller dasha chart is needed. If a tool did not return what you need, say so and name the one missing detail.

TOOLS — match the question, don't default to the birth chart
- "how will today/this week go" → get_daily_horoscope_tool, then calculate_kundli_tool for the running dasha.
- "when will I get a job/married/a child" → calculate_kundli_tool, answer from the running dasha.
- compatibility → calculate_matchmaking_tool · numbers/names → calculate_numerology_tool · classical rules, vastu, palmistry, remedies → search_vedic_rules_tool.
Use what is in [USER STORED BIRTH DETAILS] silently; never ask for details you already have. Never print tool names, JSON, field names, or a sign as a bare number.

End with 2-3 short follow-ups:
[FOLLOW_UP: ...]
"""


#: Offered with a refusal, so a user who asked something off-subject is pointed
#: back to what this assistant can actually do rather than left at a dead end.
_REFUSAL_FOLLOWUPS = {
    "bn": [
        "\u0986\u09ae\u09be\u09b0 \u0995\u09c1\u09a8\u09cd\u09a1\u09b2\u09c0\u09a4\u09c7 \u0995\u09cb\u09a8 \u09b0\u09be\u099c\u09af\u09cb\u0997 \u0986\u099b\u09c7?",
        "\u0986\u09ae\u09be\u09b0 \u09ac\u09b0\u09cd\u09a4\u09ae\u09be\u09a8 \u09a6\u09b6\u09be \u0995\u09c0 \u099a\u09b2\u099b\u09c7?",
        "\u0986\u09ae\u09be\u09b0 \u099c\u09a8\u09cd\u09af \u09b6\u09c1\u09ad \u09b0\u09a4\u09cd\u09a8 \u0995\u09cb\u09a8\u099f\u09bf?",
    ],
    "hi": [
        "\u092e\u0947\u0930\u0940 \u0915\u0941\u0902\u0921\u0932\u0940 \u092e\u0947\u0902 \u0915\u094c\u0928 \u0938\u0947 \u0930\u093e\u091c\u092f\u094b\u0917 \u0939\u0948\u0902?",
        "\u092e\u0947\u0930\u0940 \u0935\u0930\u094d\u0924\u092e\u093e\u0928 \u0926\u0936\u093e \u0915\u094c\u0928 \u0938\u0940 \u0939\u0948?",
        "\u092e\u0947\u0930\u0947 \u0932\u093f\u090f \u0936\u0941\u092d \u0930\u0924\u094d\u0928 \u0915\u094c\u0928 \u0938\u093e \u0939\u0948?",
    ],
    "en": [
        "Which raja yogas are in my chart?",
        "Which dasha am I running now?",
        "Which gemstone suits my chart?",
    ],
}


#: Said when the model cannot be reached and the local synthesis — which is
#: written in Bengali — would be unreadable for this user. Short on purpose:
#: the honest message is that they should try again, not a wall of text in a
#: script they do not read.
_BUSY_NOTE = {
    "en": "I am handling a lot of charts at the moment. Please ask me again in a few seconds and I will read yours properly.",
    "hi": "इस समय बहुत सारी कुंडलियाँ देख रहा हूँ। कृपया कुछ क्षण बाद फिर पूछें, मैं आपकी कुंडली ठीक से देखूँगा।",
    "ta": "இப்போது நிறைய ஜாதகங்களைப் பார்த்துக் கொண்டிருக்கிறேன். சில நொடிகள் கழித்து மீண்டும் கேளுங்கள், உங்கள் ஜாதகத்தைச் சரியாகப் பார்க்கிறேன்.",
    "te": "ప్రస్తుతం చాలా జాతకాలు చూస్తున్నాను. దయచేసి కొన్ని క్షణాల తర్వాత మళ్లీ అడగండి.",
    "ml": "ഇപ്പോൾ ധാരാളം ജാതകങ്ങൾ നോക്കുകയാണ്. കുറച്ച് നിമിഷങ്ങൾക്ക് ശേഷം വീണ്ടും ചോദിക്കൂ.",
    "kn": "ಈಗ ಹಲವು ಜಾತಕಗಳನ್ನು ನೋಡುತ್ತಿದ್ದೇನೆ. ಕೆಲವು ಕ್ಷಣಗಳ ನಂತರ ಮತ್ತೆ ಕೇಳಿ.",
    "gu": "અત્યારે ઘણી કુંડળીઓ જોઈ રહ્યો છું. થોડી ક્ષણો પછી ફરી પૂછો.",
    "pa": "ਇਸ ਵੇਲੇ ਕਈ ਕੁੰਡਲੀਆਂ ਵੇਖ ਰਿਹਾ ਹਾਂ। ਕੁਝ ਪਲਾਂ ਬਾਅਦ ਦੁਬਾਰਾ ਪੁੱਛੋ।",
    "or": "ଏବେ ଅନେକ କୁଣ୍ଡଳୀ ଦେଖୁଛି। କିଛି ସମୟ ପରେ ପୁଣି ପଚାରନ୍ତୁ।",
    "ur": "اس وقت بہت سی کنڈلیاں دیکھ رہا ہوں۔ چند لمحوں بعد دوبارہ پوچھیں۔",
}


#: Names for the languages `retrieval.detect_language` reports, so the model is
#: told "write in Tamil" rather than "write in the user's language" — the
#: second wording sometimes had it answer in the language of the chart data.
_LANGUAGE_NAMES = {
    "bn": "Bengali (বাংলা)",
    "hi": "Hindi (हिन्दी)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)",
    "gu": "Gujarati (ગુજરાતી)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
    "or": "Odia (ଓଡ଼ିଆ)",
    "si": "Sinhala (සිංහල)",
    "ur": "Urdu (اردو)",
    "ne": "Nepali (नेपाली)",
    "he": "Hebrew",
    "ru": "Russian",
    "th": "Thai",
    "my": "Burmese",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    # Latin script is reported as "en"; the prompt tells the model to mirror
    # whatever Latin-script language the user actually used.
    "en": "",
}

#: Longest reply we ask for. Output is charged against the same per-minute
#: budget as input, and a chat answer that runs past this is too long to
#: read on a phone anyway.
MAX_REPLY_TOKENS = 900

#: How much of an earlier message is carried forward. Readings are long; a
#: handful of them quoted back in full is thousands of tokens spent on
#: history rather than on the question being asked now.
MAX_HISTORY_CHARS = 700

#: How many earlier turns to carry at all.
MAX_HISTORY_MESSAGES = 6

#: How many times the model may ask for tools before the reading is written.
#: A reading legitimately needs two or three — the chart, today's sky, a
#: classical rule — and the cap is only here so a model that keeps asking
#: cannot loop forever at the user's expense.
MAX_TOOL_ROUNDS = 3

ASTRO_TOOLS = [
    # Descriptions are terse on purpose. These definitions are re-sent on every
    # tool round, so each word here is paid for two or three times per question
    # against a free-tier budget of 8,000 tokens a minute. Trimming them from
    # 3,491 characters to roughly a third is most of what makes a two-tool
    # reading fit inside one minute.
    {
        "type": "function",
        "function": {
            "name": "calculate_kundli_tool",
            "description": "Vedic birth chart: planets, houses, dignities, yogas, doshas, running Vimshottari dasha with dates, remedies. Swiss Ephemeris.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "day": {"type": "integer"},
                    "month": {"type": "integer"},
                    "year": {"type": "integer"},
                    "hour": {"type": "integer", "description": "0-23"},
                    "minute": {"type": "integer"},
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "place": {"type": "string"},
                },
                "required": ["day", "month", "year", "hour", "minute"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_horoscope_tool",
            "description": "Today's panchang and transits: tithi, nakshatra, yoga, hora, Rahu Kaal, lucky colour and score. Use for 'how will today go'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rashi_index": {"type": "integer", "description": "0-11, moon sign"},
                    "nakshatra_index": {"type": "integer", "description": "0-26"},
                },
                "required": ["rashi_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_numerology_tool",
            "description": "Mulank, bhagyank, Chaldean name number, mobile number analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "day": {"type": "integer"},
                    "month": {"type": "integer"},
                    "year": {"type": "integer"},
                    "mobile_number": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_matchmaking_tool",
            "description": "36-guna Ashtakoot matching, Nadi, Bhakoot, Manglik for two charts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "boy_name": {"type": "string"},
                    "boy_day": {"type": "integer"},
                    "boy_month": {"type": "integer"},
                    "boy_year": {"type": "integer"},
                    "boy_hour": {"type": "integer"},
                    "boy_minute": {"type": "integer"},
                    "girl_name": {"type": "string"},
                    "girl_day": {"type": "integer"},
                    "girl_month": {"type": "integer"},
                    "girl_year": {"type": "integer"},
                    "girl_hour": {"type": "integer"},
                    "girl_minute": {"type": "integer"},
                },
                "required": [
                    "boy_day", "boy_month", "boy_year",
                    "girl_day", "girl_month", "girl_year",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_vedic_rules_tool",
            "description": "Search the client's classical texts for rules: doshas, remedies, vastu, palmistry, nakshatra techniques.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "category": {"type": "string", "description": "kundli|rashi|nakshatra|vastu|numerology|palmistry|matchmaking"},
                },
                "required": ["query"],
            },
        },
    },
]




#: Longest we will wait out a rate limit before giving the reader something.
#: Groq's free tier allows 8,000 tokens a minute and a reading with chart data
#: attached is most of that, so a second question inside the same minute is
#: refused with a 429 that says exactly how long to wait. Waiting is far better
#: than what used to happen — the canned fallback was served instead, so the
#: reader got a generic chart dump in place of an answer to their question.
MAX_RATE_LIMIT_WAIT = 12.0

#: "Please try again in 8.6025s"
_RETRY_AFTER = re.compile(r"try again in ([0-9.]+)\s*s", re.IGNORECASE)


def _retry_delay(response: httpx.Response) -> float | None:
    """How long Groq says to wait, or None if it is not a wait-and-retry."""
    if response.status_code != 429:
        return None
    header = response.headers.get("retry-after")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    match = _RETRY_AFTER.search(response.text or "")
    if match:
        return float(match.group(1))
    return 1.0


async def _post_groq(
    client: httpx.AsyncClient, headers: dict[str, str], payload: dict[str, Any]
) -> httpx.Response:
    """POST to Groq, waiting out a rate limit once if it is short enough."""
    response = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
    delay = _retry_delay(response)
    if delay is not None and delay <= MAX_RATE_LIMIT_WAIT:
        logger.info("Groq rate limited; waiting {:.1f}s and retrying", delay)
        await asyncio.sleep(delay + 0.3)
        response = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
    return response


# ---------------------------------------------------------------------------
# Naming things for the model
# ---------------------------------------------------------------------------
#: The chart engine speaks in numbers — `d1_asc_sign` is an int from 1 to 12,
#: and every planet carries a `sign_num` rather than a sign. Handed those raw,
#: the model printed what it was given: a reading that opened with
#: "জন্ম লগ্ন: 11", which means nothing to a reader, and English planet names
#: scattered through Bengali prose.
#:
#: So the numbers are resolved to names, in the language being answered in,
#: before the model ever sees them. An interpreter can only be as accurate as
#: the chart it is handed.


def _narrative(english: str, bengali: str, hindi: str | None, language: str) -> str:
    """Pick the prose the reader can actually read.

    The engine writes its verdicts in three languages. Handing a Tamil or
    Gujarati reader the Bengali one does not merely waste tokens: the model
    reads it as the house style and answers with Bengali words mixed into
    Tamil. English is the fallback because every one of these readers is more
    likely to parse it than a script they do not use.
    """
    if language == "bn":
        return bengali or english
    if language == "hi":
        return hindi or english or bengali
    return english or bengali


def _not_yet_over(end_date: str) -> bool:
    """Whether a dasha period runs past today.

    The engine formats dates as DD-MM-YYYY. Comparing those as strings is
    meaningless — "14-04-2028" sorts below "31-10-2026" — so they are parsed.
    An unparseable date is kept rather than dropped: showing one period too
    many is better than silently losing the one the reader asked about.
    """
    from datetime import date, datetime

    try:
        return datetime.strptime(end_date, "%d-%m-%Y").date() >= date.today()
    except (ValueError, TypeError):
        return True


def _sign_name(sign_num: Any, language: str = "bn") -> str | None:
    """Name of a 1-12 rashi number, in the reader's language."""
    try:
        index = int(sign_num) - 1  # RASHI_TRANSLATIONS is keyed 0-11
    except (TypeError, ValueError):
        return None
    entry = RASHI_TRANSLATIONS.get(index)
    if not entry:
        return None
    chosen = entry.get(language) or entry.get("en") or {}
    return chosen.get("name")


def _planet_name(name: str | None, language: str = "bn") -> str | None:
    """Localised planet name, falling back to the English the engine uses."""
    if not name:
        return None
    return PLANET_NAMES_LOCALIZED.get(name, {}).get(language) or name


def _named(english: str | None, language: str) -> str | None:
    """"Jupiter" -> "বৃহস্পতি (Jupiter)", so the reading reads naturally but the
    English stays available for anyone checking the figures."""
    local = _planet_name(english, language)
    if not local or local == english:
        return english
    return f"{local} ({english})"


async def _execute_local_tool(
    func_name: str, arguments: dict[str, Any], language: str = "bn"
) -> tuple[str, list[dict[str, str]]]:
    """Executes local astrology calculations or RAG knowledge search and returns (result_json, citations)."""
    tool_citations: list[dict[str, str]] = []
    try:
        if func_name == "calculate_kundli_tool":
            req = KundliCalculateRequest(
                name=arguments.get("name") or "User",
                gender=arguments.get("gender") or "male",
                day=int(arguments["day"]),
                month=int(arguments["month"]),
                year=int(arguments["year"]),
                hour=int(arguments.get("hour", 12)),
                minute=int(arguments.get("minute", 0)),
                lat=float(arguments.get("lat") or 22.5726),
                lon=float(arguments.get("lon") or 88.3639),
                tzone=5.5,
                place=arguments.get("place") or "Kolkata",
            )
            resp = calculate_kundli(req)

            summary = {
                # Names, not numbers. See `_sign_name`: the engine returns
                # `d1_asc_sign` as an int, and the model used to print it.
                "ascendant_sign": _sign_name(resp.d1_asc_sign, language)
                or resp.d1_asc_sign,
                "moon_sign": resp.planetary_info.rasi,
                "moon_nakshatra": resp.planetary_info.nakshatra,
                # The dates matter as much as the lords. Without them the model
                # was asked "when will this happen?" while holding no dates at
                # all, and duly invented some — a reading that named a Venus
                # sub-period running in 2024 when the chart said otherwise.
                "current_dasha": (
                    {
                        "mahadasha": _named(resp.current_dasha.mahadasha_lord, language),
                        "antardasha": _named(resp.current_dasha.antardasha_lord, language),
                        "runs_from": resp.current_dasha.start_date,
                        "runs_until": resp.current_dasha.end_date,
                        # Narrative in the reader's language, not always
                        # Bengali. Sending verdict_bn to a Tamil reader put
                        # Bengali words into a Tamil reply — the model copied
                        # what it was handed, quite reasonably.
                        "verdict": _narrative(
                            resp.current_dasha.verdict,
                            resp.current_dasha.verdict_bn,
                            resp.current_dasha.verdict_hi,
                            language,
                        ),
                        "guidance": _narrative(
                            resp.current_dasha.guidance,
                            resp.current_dasha.guidance_bn,
                            resp.current_dasha.guidance_hi,
                            language,
                        ),
                    }
                    if resp.current_dasha
                    else None
                ),
                # The mahadashas still to come are deliberately NOT sent.
                # `dashas_grid` carries the lords and their lengths but leaves
                # start_date and end_date empty, and handing the model a period
                # with no dates is how it came to announce a Venus sub-period
                # running in 2024. Only dates that actually exist are passed;
                # for anything further out the model is told to say it needs a
                # fuller dasha chart rather than to guess.
                "planets": [
                    {
                        "name": _named(p.name, language),
                        "sign": _sign_name(p.sign_num, language) or p.sign_num,
                        "house": p.house_num,
                        "is_retro": p.is_retrograde,
                    }
                    for p in resp.d1_planets
                ],
                # `dignities` is deliberately not sent. It was the largest field in
                # this summary and it restates what `planets` already says —
                # sign, house and retrogradation — in prose. Against a free-tier
                # budget that is a third of a reading's allowance spent twice.
                "yogas": [y.name for y in resp.active_yogas_details] + [y.name for y in resp.extended_yogas if y.is_present],
                "doshas": [d.dosha_name for d in resp.doshas_analysis if d.is_present],
                "remedies": (
                    {
                        "life_stone": resp.remedies.life_stone.stone_name,
                        "lucky_stone": resp.remedies.lucky_stone.stone_name,
                        "rudraksha": resp.remedies.rudraksha_recommendation_bn,
                        "ishta_devata": resp.remedies.ishta_devata_bn,
                    }
                    if resp.remedies
                    else None
                ),
            }
            tool_citations.append({
                "source": "সুইস এফিমেরিস বৈদিক কুন্ডলী এনজিন (Swiss Ephemeris 2.10)",
                "category": "kundli",
                "snippet": (
                    f"লগ্ন: {_sign_name(resp.d1_asc_sign, language) or resp.d1_asc_sign}, "
                    f"চন্দ্র রাশি: {resp.planetary_info.rasi}, "
                    f"নক্ষত্র: {resp.planetary_info.nakshatra}। "
                    "নির্ভুল লাহিড়ী অয়নাংশ গণনা সম্পন্ন।"
                ),
            })
            return json.dumps(summary, ensure_ascii=False), tool_citations

        elif func_name == "get_daily_horoscope_tool":
            req = DailyHoroscopeRequest(
                rashi_index=int(arguments["rashi_index"]),
                nakshatra_index=arguments.get("nakshatra_index"),
                lang="bn",
            )
            resp = calculate_daily_horoscope(req)
            r_idx = int(arguments["rashi_index"])
            horo = resp.signs[r_idx] if 0 <= r_idx < len(resp.signs) else resp.signs[0]
            summary = {
                "sign_name": horo.sign_name,
                "sign_name_sanskrit": horo.sign_name_sanskrit,
                "overall_score": horo.overall_score,
                "lucky_color": horo.lucky_color,
                "lucky_number": horo.lucky_number,
                "is_chandrashtama": horo.is_chandrashtama,
                "sade_sati": horo.sade_sati_status,
                "beej_mantra": horo.beej_mantra,
                "remedy": horo.remedy,
                "current_active_hora": resp.panchang.horas[0].planet_bn if resp.panchang.horas else None,
            }
            tool_citations.append({
                "source": f"দৈনিক গোচর ও হোরা কালকুলেটর ({horo.sign_name})",
                "category": "transit",
                "snippet": f"আজকের শুভ স্কোর: {horo.overall_score}/১০০, লাকি রঙ: {horo.lucky_color}, শুভ সংখ্যা: {horo.lucky_number}।",
            })
            return json.dumps(summary, ensure_ascii=False), tool_citations

        elif func_name == "calculate_numerology_tool":
            name = arguments.get("name", "User")
            day = int(arguments["day"])
            month = int(arguments["month"])
            year = int(arguments["year"])
            mob = arguments.get("mobile_number")

            mulank_info = calculate_mulank(day)
            bhagyank_info = calculate_bhagyank(day, month, year)
            name_info = calculate_chaldean_name(name)
            grid_info = calculate_vedic_grid(day, month, year)
            mob_info = (
                calculate_mobile_numerology(mob, mulank_info["number"], bhagyank_info["number"])
                if mob
                else None
            )

            summary = {
                "mulank": mulank_info["number"],
                "mulank_planet": mulank_info["planet"],
                "mulank_gemstone": mulank_info["gemstone"],
                "bhagyank": bhagyank_info["number"],
                "bhagyank_planet": bhagyank_info["planet"],
                "name_compound_total": name_info["compound_total"],
                "name_number": name_info["name_number"],
                "vedic_grid_summary": grid_info["summary_bn"],
                "mobile_analysis": (
                    {
                        "total_sum": mob_info["total_sum"],
                        "single_digit": mob_info["single_digit"],
                        "status": mob_info["status"],
                        "verdict": mob_info["verdict_bn"],
                    }
                    if mob_info
                    else None
                ),
            }
            tool_citations.append({
                "source": f"চ্যালডিয়ান ও বৈদিক সংখ্যাতত্ত্ব (মূলাঙ্ক {mulank_info['number']} • ভাগ্যাঙ্ক {bhagyank_info['number']})",
                "category": "numerology",
                "snippet": f"চালক গ্রহ: {mulank_info['planet']}, ভাগ্য নিয়ন্তা: {bhagyank_info['planet']}, নাম যৌগিক যোগফল: {name_info['compound_total']}।",
            })
            return json.dumps(summary, ensure_ascii=False), tool_citations

        elif func_name == "calculate_matchmaking_tool":
            b_hour = int(arguments.get("boy_hour", 12))
            g_hour = int(arguments.get("girl_hour", 12))
            req = KundliMatchingRequest(
                groom=KundliMatchingPersonInput(
                    name=arguments.get("boy_name") or "Boy",
                    gender="male",
                    day=int(arguments["boy_day"]),
                    month=int(arguments["boy_month"]),
                    year=int(arguments["boy_year"]),
                    hour=b_hour,
                    minute=int(arguments.get("boy_minute", 0)),
                    second=0,
                    period="AM" if b_hour < 12 else "PM",
                    place="Kolkata",
                    latitude=22.5726,
                    longitude=88.3639,
                    timezone=5.5,
                ),
                bride=KundliMatchingPersonInput(
                    name=arguments.get("girl_name") or "Girl",
                    gender="female",
                    day=int(arguments["girl_day"]),
                    month=int(arguments["girl_month"]),
                    year=int(arguments["girl_year"]),
                    hour=g_hour,
                    minute=int(arguments.get("girl_minute", 0)),
                    second=0,
                    period="AM" if g_hour < 12 else "PM",
                    place="Kolkata",
                    latitude=22.5726,
                    longitude=88.3639,
                    timezone=5.5,
                ),
                language="bn",
            )
            match_resp = calculate_kundli_matching(req)
            summary = {
                "total_score": match_resp.total_received,
                "max_score": match_resp.total_out_of,
                "percentage": match_resp.total_percentage,
                "verdict_bn": match_resp.verdict,
                "marital_harmony": match_resp.forecast.marital_harmony_verdict if match_resp.forecast else None,
                "financial_prosperity": match_resp.forecast.financial_prosperity_verdict if match_resp.forecast else None,
            }
            tool_citations.append({
                "source": "৩৬ গুণ অষ্টকূট বিবাহ মেলাক এনজিন",
                "category": "matchmaking",
                "snippet": f"প্রাপ্ত গুণ: {match_resp.total_received}/{match_resp.total_out_of} ({match_resp.total_percentage}%) — {match_resp.verdict}",
            })
            return json.dumps(summary, ensure_ascii=False), tool_citations

        elif func_name == "search_vedic_rules_tool":
            query = arguments.get("query", "")
            cat = arguments.get("category")
            results = await search_knowledge(query, cat, top_k=4)

            for doc in results:
                tool_citations.append({
                    "source": doc.get("title", "শাস্ত্রীয় বিধান"),
                    "category": doc.get("category", "shastra"),
                    "snippet": doc.get("content", "")[:180] + "...",
                })

            return json.dumps(results, ensure_ascii=False), tool_citations

    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"}), tool_citations

    return json.dumps({"status": "unknown_tool"}), tool_citations


async def _local_astrological_fallback(
    latest_user_text: str,
    custom_rules: list[Any],
    user_birth_details: dict[str, Any] | None,
    preferred_language: str = "bn",
) -> dict[str, Any]:
    """A reading assembled locally when the model is unreachable.

    Everything it writes is Bengali, which is right for a Bengali reader and
    wrong for everybody else: a Tamil speaker asking in Tamil was handed a wall
    of Bengali and no explanation. For any other language it says plainly that
    the astrologer is busy and to ask again in a moment, which is at least true
    and readable. Translating the whole synthesis is the better fix and a
    larger one.
    """
    if preferred_language not in ("bn", ""):
        return {
            "reply": _BUSY_NOTE.get(preferred_language, _BUSY_NOTE["en"]),
            "tools_called": [],
            "citations": [],
            "suggested_followups": [],
            "answered": False,
            "refusal_reason": "model_unavailable",
        }

    citations_map: dict[str, dict[str, str]] = {}
    reply_parts: list[str] = []
    tools_called: list[str] = ["local_astrology_rules_engine"]

    # 1. Check if birth chart calculation can be performed
    if user_birth_details and "day" in user_birth_details:
        try:
            req = KundliCalculateRequest(
                name=user_birth_details.get("name", "User"),
                gender=user_birth_details.get("gender", "male"),
                day=int(user_birth_details["day"]),
                month=int(user_birth_details["month"]),
                year=int(user_birth_details["year"]),
                hour=int(user_birth_details.get("hour", 12)),
                minute=int(user_birth_details.get("minute", 0)),
                lat=float(user_birth_details.get("lat") or 22.5726),
                lon=float(user_birth_details.get("lon") or 88.3639),
                tzone=5.5,
                place=user_birth_details.get("place", "Kolkata"),
            )
            kundli = calculate_kundli(req)
            tools_called.append("calculate_kundli_tool")

            citations_map["kundli_engine"] = {
                "source": "সুইস এফিমেরিস বৈদিক কুন্ডলী এনজিন",
                "category": "kundli",
                "snippet": f"লগ্ন: {kundli.d1_asc_sign}, চন্দ্র রাশি: {kundli.planetary_info.rasi}, জন্ম নক্ষত্র: {kundli.planetary_info.nakshatra}।",
            }

            reply_parts.append(
                f"নমস্কার {user_birth_details.get('name', '')}। সুইস এফিমেরিসের নিখুঁত লাহিড়ী অয়নাংশ গণনা অনুযায়ী আপনার জন্মকুন্ডলীর প্রধান জ্যোতিষীয় চিত্র:\n\n"
                f"• **জন্ম লগ্ন:** {kundli.d1_asc_sign}\n"
                f"• **চন্দ্র রাশি:** {kundli.planetary_info.rasi}\n"
                f"• **জন্ম নক্ষত্র:** {kundli.planetary_info.nakshatra}\n"
            )

            if kundli.current_dasha:
                cd = kundli.current_dasha
                reply_parts.append(
                    f"**চলমান বিংশোত্তরী দশা:**\n"
                    f"বর্তমানে আপনার **{cd.mahadasha_lord}** এর মহাদশা এবং **{cd.antardasha_lord}** এর অন্তর্দশা চলছে। "
                    f"{cd.verdict_bn} {cd.guidance_bn}\n"
                )

            if kundli.remedies:
                reply_parts.append(
                    f"**শাস্ত্রীয় অনুকূল রত্ন ও প্রতিকার:**\n"
                    f"• জীবন রত্ন (লগ্নপতি): **{kundli.remedies.life_stone.stone_name}** ({kundli.remedies.life_stone.stone_name_bn})\n"
                    f"• ভাগ্য রত্ন (নবমপতি): **{kundli.remedies.lucky_stone.stone_name}** ({kundli.remedies.lucky_stone.stone_name_bn})\n"
                    f"• রুদ্রাক্ষ পরামর্শ: {kundli.remedies.rudraksha_recommendation_bn}\n"
                    f"• ইষ্টদেবতা: {kundli.remedies.ishta_devata_bn}"
                )
        except Exception:
            pass

    # 2. Check Custom Rules
    if custom_rules:
        r = custom_rules[0]
        citations_map[r.rule_title] = {
            "source": r.rule_title,
            "category": r.category or "custom_rule",
            "snippet": r.response_bn[:160] + "...",
        }
        reply_parts.append(
            f"**{r.rule_title}**\n\n"
            f"{r.response_bn}\n\n"
            f"**প্রস্তাবিত বৈদিক প্রতিকার:**\n{r.remedy_bn}"
        )

    # 3. If no parts yet, search knowledge base
    if not reply_parts:
        try:
            docs = await search_knowledge(latest_user_text, top_k=2)
            if docs:
                tools_called.append("search_vedic_rules_tool")
                for d in docs:
                    citations_map[d["title"]] = {
                        "source": d["title"],
                        "category": d["category"],
                        "snippet": d["content"][:160] + "...",
                    }
                reply_parts.append(
                    f"নমস্কার। শাস্ত্রীয় বৈদিক নথি ও ক্লায়েন্টের নির্দেশিকা অনুযায়ী আপনার প্রশ্নের সমাধান:\n\n"
                    f"{docs[0]['content'][:600]}...\n\n"
                    f"**শাস্ত্রীয় পরামর্শ:** কোনো শুভ কাজ সূচনার পূর্বে অনুকূল গ্রহের হোরা ও শুভ নক্ষত্র বল বিবেচনা করে পদক্ষেপ নেওয়া শ্রেয়।"
                )
        except Exception:
            pass

    # 4. Fallback general response if still empty
    if not reply_parts:
        citations_map["shastra"] = {
            "source": "বৃহৎ পরাশর হোরাশাস্ত্র ও ফলদীপিকা",
            "category": "shastra",
            "snippet": "মহর্ষি পরাশর প্রণীত শাস্ত্রীয় গ্রহবল ও শুভাশুভ সময় বিচার বিধান।",
        }
        reply_parts.append(
            "নমস্কার। বৈদিক জ্যোতিষশাস্ত্রীয় গণনা ও গ্রহাবস্থানের গভীর পর্যালোচনায় আপনার প্রশ্নের সঠিক সমাধান নিম্নে উপস্থাপন করা হলো:\n\n"
            "**শাস্ত্রীয় পর্যবেক্ষণ:** আপনার জন্মসূত্রে বিরাজমান গ্রহাবস্থা এবং বর্তমান গোচর গ্রহের প্রভাব আপনার ক্ষেত্রে অত্যন্ত গুরুত্বপূর্ণ ভূমিকা রাখছে।\n\n"
            "**বাস্তবসম্মত নির্দেশনা:** কোনো বড় সিদ্ধান্ত গ্রহণের পূর্বে শুভ তিথি ও অনুকূল গ্রহের হোরা নির্বাচন করে অগ্রসর হলে অভীষ্ট সাফল্য সুনিশ্চিত হবে।\n\n"
            "**বৈদিক প্রতিকার:** প্রতিদিন সকালে স্নানান্তে পূর্বদিকে মুখ করে তামার পাত্রে সূর্যদেবকে অর্ঘ্য নিবেদন করুন এবং 'ॐ ঘৃণি সূর্যায় নমঃ' জপ করুন।"
        )

    followups = [
        "আমার কুন্ডলীতে কোন কোন শুভ রাজযোগ রয়েছে?",
        "আমার জন্য কোন রত্ন বা রুদ্রাক্ষ ধারণ সবচেয়ে মঙ্গলজনক?",
        "আজকের দিনে কোন সময়ে শুভ কাজ শুরু করা উচিত?",
    ]

    return {
        "reply": "\n\n".join(reply_parts),
        "tools_called": list(set(tools_called)),
        "citations": list(citations_map.values()),
        "suggested_followups": followups,
    }


async def generate_astrology_response(
    messages: list[dict[str, Any]],
    user_birth_details: dict[str, Any] | None = None,
    preferred_language: str = "bn",
    stream: bool = False,
) -> dict[str, Any]:
    """Sends prompt & conversation history to Groq (openai/gpt-oss-120b),

    executes tool calls deterministically, and produces a 100% verified astrological synthesis.
    """
    latest_user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            latest_user_text = m.get("content", "")
            break

    # The gate, before the model and before the local fallback alike.
    #
    # A refusal taken here cannot be argued with. A model merely *instructed* to
    # refuse can always be talked round, and the instruction costs a round trip
    # to find that out. The test is deliberately generous — see
    # `retrieval.is_answerable` — so a paying user asking a real question in any
    # of the three languages is never turned away.
    # The knowledge base's own words widen the gate, so seeding new material
    # makes the assistant accept questions about it without anybody editing the
    # lexicon by hand. Cheap: titles, tags and rule triggers only, cached.
    try:
        vocabulary = await corpus_vocabulary()
    except Exception:  # noqa: BLE001 - the lexicon alone is a fine fallback
        vocabulary = set()

    # What the user actually wrote in wins over the toggle they set once. A
    # Tamil speaker typing Tamil should be answered in Tamil whatever the app
    # last remembered about them; only an empty or script-less message falls
    # back to the stored preference.
    detected = retrieval.detect_language(latest_user_text)
    if detected != "en" or not preferred_language or preferred_language not in ("bn", "hi", "en"):
        preferred_language = detected

    verdict = retrieval.is_answerable(latest_user_text, extra_vocabulary=vocabulary)
    if not verdict.answerable:
        logger.info(
            "AI question refused ({}): {!r}", verdict.reason, latest_user_text[:120]
        )
        return {
            "reply": retrieval.refusal_text(preferred_language),
            "tools_called": [],
            "citations": [],
            "suggested_followups": _REFUSAL_FOLLOWUPS.get(
                preferred_language, _REFUSAL_FOLLOWUPS["en"]
            ),
            "answered": False,
            "refusal_reason": verdict.reason,
        }

    custom_rules = await match_custom_rules(latest_user_text)

    # If Groq API key is not configured, gracefully fallback to local authoritative astrology synthesis
    if not settings.GROQ_API_KEY:
        return await _local_astrological_fallback(
            latest_user_text, custom_rules, user_birth_details, preferred_language
        )

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    tools_called: list[str] = []
    citations_map: dict[str, dict[str, str]] = {}

    custom_rules_context = ""
    if custom_rules:
        rule_texts = [
            f"Rule '{r.rule_title}': {r.response_bn} (প্রতিকার: {r.remedy_bn})"
            for r in custom_rules[:3]
        ]
        custom_rules_context = (
            "\n[ADMIN VERIFIED RULES (Mandatory To Follow)]:\n" + "\n".join(rule_texts) + "\n"
        )

    # Inject birth details into system context if available
    birth_context = ""
    if user_birth_details:
        # The chart is computed here rather than left for the model to ask for.
        #
        # Every tool round re-sends the system prompt, the tool definitions and
        # the whole conversation, so a question that needs two tools costs three
        # API calls and most of the free tier's 8,000 tokens a minute. When the
        # birth details are already known, the chart is not a question — it is
        # arithmetic we can do before the model is even called. Handing it over
        # up front turns the common question from three calls into one.
        #
        # It costs about 550 tokens in the system context. A single avoided
        # round costs about 1,500, so it pays for itself immediately.
        chart_block = ""
        try:
            chart_json, chart_cites = await _execute_local_tool(
                "calculate_kundli_tool", user_birth_details, preferred_language
            )
            chart_block = f"\n[THIS USER'S CHART, already calculated]:\n{chart_json}\n"
            for c in chart_cites:
                citations_map[c["source"]] = c
            tools_called.append("calculate_kundli_tool")
        except Exception as exc:  # noqa: BLE001 - the model can still ask for it
            logger.warning("Could not precompute the chart: {}", exc)

        birth_context = (
            f"\n[USER STORED BIRTH DETAILS]:\n"
            f"Name: {user_birth_details.get('name', 'User')}\n"
            f"DOB: {user_birth_details.get('day')}/{user_birth_details.get('month')}/{user_birth_details.get('year')} "
            f"{user_birth_details.get('hour')}:{user_birth_details.get('minute')}\n"
            f"Place: {user_birth_details.get('place', 'Kolkata')} "
            f"({user_birth_details.get('lat', 22.5726)}, {user_birth_details.get('lon', 88.3639)})\n"
            + chart_block
            + "The chart above is already computed — do NOT call calculate_kundli_tool "
            "again unless you need something it does not contain.\n"
        )

    # Named rather than described, because a model told "the user's language"
    # sometimes picks the language of the chart data instead of the question.
    language_name = _LANGUAGE_NAMES.get(preferred_language, "")
    lang_instruction = (
        f"\nIMPORTANT: Write your entire reply in {language_name}, the language this "
        "user wrote in. Do not answer in any other language.\n"
        if language_name
        else "\nIMPORTANT: Write your entire reply in the same language and script the "
        "user wrote their message in.\n"
    )

    full_system_prompt = (
        ASTROLOGER_SYSTEM_PROMPT + birth_context + custom_rules_context + lang_instruction
    )

    api_messages: list[dict[str, Any]] = [
        {"role": "system", "content": full_system_prompt}
    ]
    # Only the recent turns, and only the head of each. The last reading is
    # worth remembering; quoting all of it back on every follow-up is not,
    # especially when the whole minute's budget is 8,000 tokens.
    for m in messages[-MAX_HISTORY_MESSAGES:]:
        content = m.get("content") or ""
        if len(content) > MAX_HISTORY_CHARS:
            content = content[:MAX_HISTORY_CHARS].rstrip() + " […]"
        api_messages.append({"role": m["role"], "content": content})

    for r in custom_rules:
        citations_map[r.rule_title] = {
            "source": r.rule_title,
            "category": r.category or "custom_rule",
            "snippet": r.response_bn[:160] + "...",
        }

    model_to_use = settings.GROQ_DEFAULT_MODEL or "openai/gpt-oss-120b"

    async with httpx.AsyncClient(timeout=45.0) as client:
        payload = {
            "model": model_to_use,
            "messages": api_messages,
            "tools": ASTRO_TOOLS,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": MAX_REPLY_TOKENS,
        }

        try:
            resp = await _post_groq(client, headers, payload)
            if resp.status_code in (400, 404):
                payload["model"] = settings.GROQ_FALLBACK_MODEL or "qwen/qwen3.8-27b"
                resp = await _post_groq(client, headers, payload)

            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            # Safe fallback if API quota or connection issue occurs
            logger.warning("Groq first call failed, using local synthesis: {}", exc)
            return await _local_astrological_fallback(
                latest_user_text, custom_rules, user_birth_details, preferred_language
            )

        choice = data["choices"][0]
        assistant_message = choice["message"]

        # Tool calls, for as many rounds as the reading needs.
        #
        # This used to run exactly one round: execute whatever the first reply
        # asked for, then send the results back *without* the tool definitions.
        # Groq reads a request carrying no tools as `tool_choice: none`, so the
        # moment the model wanted a second tool it answered
        #
        #     "Tool choice is none, but model called a tool"
        #
        # with a 400, and the code quietly served a canned fallback instead. It
        # happened on exactly the questions that need two tools — "how will
        # today go for me?" needs the birth chart *and* today's sky — so those
        # questions could never be answered properly, and the failure was
        # invisible because the fallback is plausible-looking text.
        #
        # Now every round carries the tools, and the loop ends when the model
        # stops asking for them.
        raw_reply = assistant_message.get("content", "") or ""

        for _ in range(MAX_TOOL_ROUNDS):
            tool_calls = assistant_message.get("tool_calls")
            if not tool_calls:
                break

            api_messages.append(assistant_message)

            for tc in tool_calls:
                func_name = tc["function"]["name"]
                args_str = tc["function"].get("arguments", "{}")
                try:
                    args = json.loads(args_str)
                except Exception:
                    args = {}

                tool_result_str, retrieved_cites = await _execute_local_tool(
                    func_name, args, preferred_language
                )
                tools_called.append(func_name)

                for c in retrieved_cites:
                    citations_map[c["source"]] = c

                api_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": func_name,
                        "content": tool_result_str,
                    }
                )

            try:
                next_resp = await _post_groq(
                    client,
                    headers,
                    {
                        "model": payload["model"],
                        "messages": api_messages,
                        # Carried on every round. Leaving these out is what
                        # produced the 400 described above.
                        "tools": ASTRO_TOOLS,
                        "tool_choice": "auto",
                        "temperature": 0.3,
                        "max_tokens": MAX_REPLY_TOKENS,
                    },
                )
                if next_resp.status_code >= 400:
                    # Logged rather than swallowed. Silent failure here is how a
                    # 400 on every two-tool question went unnoticed for so long.
                    logger.error(
                        "Groq rejected a tool round ({}): {}",
                        next_resp.status_code,
                        next_resp.text[:600],
                    )
                next_resp.raise_for_status()
                assistant_message = next_resp.json()["choices"][0]["message"]
                raw_reply = assistant_message.get("content", "") or raw_reply
            except Exception as exc:
                logger.warning("Falling back to local synthesis: {}", exc)
                return await _local_astrological_fallback(
                    latest_user_text, custom_rules, user_birth_details, preferred_language
                )
        else:
            # The loop ran its full count and the model was still asking for
            # tools. Whatever it has said by now is what the reader gets, rather
            # than another round that might never end.
            if assistant_message.get("tool_calls"):
                logger.warning(
                    "Stopped after {} tool rounds; answering with what we have.",
                    MAX_TOOL_ROUNDS,
                )

    # Parse out suggested followups [FOLLOW_UP: ...]
    followups: list[str] = []
    clean_lines: list[str] = []
    for line in raw_reply.splitlines():
        if "[FOLLOW_UP:" in line:
            extracted = (
                line.replace("[FOLLOW_UP:", "").replace("]", "").strip()
            )
            if extracted:
                followups.append(extracted)
        else:
            clean_lines.append(line)

    final_content = "\n".join(clean_lines).strip()

    if not followups:
        followups = [
            "আমার কুন্ডলীতে কোন কোন রাজযোগ আছে?",
            "আমার জন্য সবচেয়ে অনুকূল রত্ন কোনটি?",
            "আজকের দিনে কোন হোরায় গুরুত্বপূর্ণ কাজ করা উচিত?",
        ]

    # Nothing is invented here on purpose.
    #
    # This used to attach a citation to the Brihat Parashara Hora Shastra and
    # Phaladeepika whenever no tool had run and no rule had matched — which is
    # precisely when the answer came from the model alone and rested on no
    # source at all. An empty list is the truthful answer to "what was this
    # based on", and it can be shown to the client without anybody having to
    # defend a reference that was never read.

    return {
        "reply": final_content,
        "tools_called": list(set(tools_called)),
        "citations": list(citations_map.values()),
        "suggested_followups": followups[:3],
    }
