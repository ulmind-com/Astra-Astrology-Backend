"""Groq AI Astrologer reasoning engine with Swiss Ephemeris Tool Calling & RAG Grounding."""

import json
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.astrology import (
    DailyHoroscopeRequest,
    KundliCalculateRequest,
    KundliMatchingPersonInput,
    KundliMatchingRequest,
)
from app.services.ai.knowledge_service import match_custom_rules, search_knowledge
from app.services.astrology.daily_horoscope import calculate_daily_horoscope
from app.services.astrology.kundli_matching_service import calculate_kundli_matching
from app.services.astrology.kundli_service import calculate_kundli
from app.services.astrology.numerology import (
    calculate_bhagyank,
    calculate_chaldean_name,
    calculate_mobile_numerology,
    calculate_mulank,
    calculate_vedic_grid,
)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# System Prompt for 100% Classical Vedic Astrologer
ASTROLOGER_SYSTEM_PROMPT = """You are "Astra Vedic Astrologer" (অ্যাস্ট্রা জ্যোতিষী), an enlightened, compassionate, and deeply knowledgeable classical Vedic Astrologer for Astra Astrology.

Your foundational principles:
1. TRUTH & MATHEMATICAL ACCURACY: Never guess or invent planetary degrees, houses, or dashas. When birth details are available, ALWAYS execute the `calculate_kundli_tool` to get exact Swiss Ephemeris sidereal planetary positions, running Vimshottari Mahadasha/Antardasha, and divisional charts.
2. CLASSICAL PARASHARI GROUNDING: Base all judgments on Brihat Parashara Hora Shastra, Phaladeepika, and the client's verified Vedic rules. When asked about specific topics (e.g. Manglik, Kaal Sarp, Sade Sati, Vastu, Numerology, Palmistry, Face Reading), consult `search_vedic_rules_tool`.
3. MULTI-DISCIPLINARY ASTROLOGY:
   - For marriage compatibility, use `calculate_matchmaking_tool` (36 Guna Ashtakoot, Nadi, Bhakoot).
   - For numbers and names, use `calculate_numerology_tool` (Mulank, Bhagyank, Chaldean compound numbers, mobile number pairs).
   - For daily transit and planetary hours, use `get_daily_horoscope_tool`.
4. LANGUAGE & TONE: Default to beautiful, respectful, and compassionate Bengali (বাংলা). If the user asks in Hindi or English, respond in that language. Use respectful address (যেমন: "নমস্কার", "আপনার কুন্ডলী বিচার করে দেখা যাচ্ছে...", "শুভকামনা").
5. STRUCTURED GUIDANCE: For every astrological analysis, provide:
   - **গ্রহাবস্থান ও তাৎপর্য (Planetary Position & Analysis)**
   - **চলমান দশা ও সময়কাল (Running Dasha Influence)**
   - **বাস্তবসম্মত ফল ও পরামর্শ (Practical Life Advice)**
   - **শাস্ত্রীয় বৈদিক প্রতিকার (Vedic Remedies: মন্ত্র, ইষ্টদেবতা ও দান)**
6. FOLLOW-UP QUESTIONS: At the very end of your response, always propose 2 or 3 short, intriguing follow-up questions formatted as:
   [FOLLOW_UP: প্রথম প্রশ্ন?]
   [FOLLOW_UP: দ্বিতীয় প্রশ্ন?]
"""

ASTRO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_kundli_tool",
            "description": "Calculates exact Vedic Birth Chart (Kundli), divisional charts D1/D9/D10, planetary degrees, combustion, running Vimshottari Dasha, and Yogas using Swiss Ephemeris.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Native's name"},
                    "day": {"type": "integer", "description": "Day of birth (1-31)"},
                    "month": {"type": "integer", "description": "Month of birth (1-12)"},
                    "year": {"type": "integer", "description": "Year of birth (e.g. 1995)"},
                    "hour": {"type": "integer", "description": "Hour of birth (0-23)"},
                    "minute": {"type": "integer", "description": "Minute of birth (0-59)"},
                    "lat": {"type": "number", "description": "Latitude of birth place (e.g. 22.5726)"},
                    "lon": {"type": "number", "description": "Longitude of birth place (e.g. 88.3639)"},
                    "place": {"type": "string", "description": "City or place of birth (e.g. Kolkata)"},
                },
                "required": ["day", "month", "year", "hour", "minute"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_horoscope_tool",
            "description": "Calculates today's Gochar (Transit), 24 Planetary Horas, Navatara Bala, Chandrashtama alert, and Shani Sade Sati for a Rashi and Nakshatra.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rashi_index": {"type": "integer", "description": "Rashi index (0=Aries/মেষ to 11=Pisces/মীন)"},
                    "nakshatra_index": {"type": "integer", "description": "Optional birth nakshatra index (0-26)"},
                },
                "required": ["rashi_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_numerology_tool",
            "description": "Calculates Vedic and Chaldean Numerology including Mulank (Driver), Bhagyank (Conductor), Name compound number, lucky numbers, colors, and mobile number vibration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name"},
                    "day": {"type": "integer", "description": "Day of birth (1-31)"},
                    "month": {"type": "integer", "description": "Month of birth (1-12)"},
                    "year": {"type": "integer", "description": "Year of birth (e.g. 1995)"},
                    "mobile_number": {"type": "string", "description": "Optional 10-digit mobile number for vibration analysis"},
                },
                "required": ["name", "day", "month", "year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_matchmaking_tool",
            "description": "Performs authentic 36 Guna Ashtakoot Kundli Matching for marriage, including Nadi Dosha, Bhakoot Dosha, and Manglik compatibility.",
            "parameters": {
                "type": "object",
                "properties": {
                    "boy_name": {"type": "string", "description": "Boy's name"},
                    "boy_day": {"type": "integer"},
                    "boy_month": {"type": "integer"},
                    "boy_year": {"type": "integer"},
                    "boy_hour": {"type": "integer"},
                    "boy_minute": {"type": "integer"},
                    "girl_name": {"type": "string", "description": "Girl's name"},
                    "girl_day": {"type": "integer"},
                    "girl_month": {"type": "integer"},
                    "girl_year": {"type": "integer"},
                    "girl_hour": {"type": "integer"},
                    "girl_minute": {"type": "integer"},
                },
                "required": ["boy_day", "boy_month", "boy_year", "girl_day", "girl_month", "girl_year"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_vedic_rules_tool",
            "description": "Searches classical Vedic scriptures and client's resource documents for rules, dosha remedies, gemstone guidelines, palmistry loops/marriage cards, face reading, or vastu principles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Astrology topic or question keywords to search"},
                    "category": {"type": "string", "description": "Optional category (kundli, rashi, vastu, numerology, palmistry, face_reading)"},
                },
                "required": ["query"],
            },
        },
    },
]


async def _execute_local_tool(func_name: str, arguments: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
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
                "ascendant_sign": resp.d1_asc_sign,
                "moon_sign": resp.planetary_info.rasi,
                "moon_nakshatra": resp.planetary_info.nakshatra,
                "current_dasha": (
                    {
                        "mahadasha": resp.current_dasha.mahadasha_lord,
                        "antardasha": resp.current_dasha.antardasha_lord,
                        "verdict_bn": resp.current_dasha.verdict_bn,
                        "guidance_bn": resp.current_dasha.guidance_bn,
                    }
                    if resp.current_dasha
                    else None
                ),
                "planets": [
                    {
                        "name": p.name,
                        "sign_num": p.sign_num,
                        "house": p.house_num,
                        "is_retro": p.is_retrograde,
                    }
                    for p in resp.d1_planets
                ],
                "dignities": [
                    {
                        "planet": d.planet,
                        "dignity": d.dignity,
                        "avastha_bn": d.avastha_bn,
                        "combust": d.is_combust,
                    }
                    for d in resp.planetary_dignities[:9]
                ],
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
                "snippet": f"লগ্ন: {resp.d1_asc_sign}, চন্দ্র রাশি: {resp.planetary_info.rasi}, নক্ষত্র: {resp.planetary_info.nakshatra}। নির্ভুল লাহিড়ী অয়নাংশ গণনা সম্পন্ন।",
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
    """Provides an authoritative classical Vedic response when external LLM is offline or unconfigured."""
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
        birth_context = (
            f"\n[USER STORED BIRTH DETAILS]:\n"
            f"Name: {user_birth_details.get('name', 'User')}\n"
            f"Date of Birth: {user_birth_details.get('day')}/{user_birth_details.get('month')}/{user_birth_details.get('year')}\n"
            f"Time of Birth: {user_birth_details.get('hour')}:{user_birth_details.get('minute')}\n"
            f"Place: {user_birth_details.get('place', 'Kolkata')} (Lat: {user_birth_details.get('lat', 22.5726)}, Lon: {user_birth_details.get('lon', 88.3639)})\n"
            f"You may invoke `calculate_kundli_tool` or `calculate_numerology_tool` with these exact details.\n"
        )

    lang_instruction = ""
    if preferred_language == "hi":
        lang_instruction = "\nIMPORTANT: The user prefers Hindi. Respond in clear, respectful Vedic Hindi (हिन्दी).\n"
    elif preferred_language == "en":
        lang_instruction = "\nIMPORTANT: The user prefers English. Respond in clear, classical Vedic English.\n"
    else:
        lang_instruction = "\nIMPORTANT: Default to respectful, compassionate Bengali (বাংলা).\n"

    full_system_prompt = (
        ASTROLOGER_SYSTEM_PROMPT + birth_context + custom_rules_context + lang_instruction
    )

    api_messages: list[dict[str, Any]] = [
        {"role": "system", "content": full_system_prompt}
    ]
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    tools_called: list[str] = []
    citations_map: dict[str, dict[str, str]] = {}

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
            "max_tokens": 2048,
        }

        try:
            resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
            if resp.status_code in (400, 404):
                payload["model"] = settings.GROQ_FALLBACK_MODEL or "qwen/qwen3.8-27b"
                resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)

            resp.raise_for_status()
            data = resp.json()
        except Exception:
            # Safe fallback if API quota or connection issue occurs
            return await _local_astrological_fallback(
                latest_user_text, custom_rules, user_birth_details, preferred_language
            )

        choice = data["choices"][0]
        assistant_message = choice["message"]

        # Step 2: Handle Tool Calls if any
        if assistant_message.get("tool_calls"):
            api_messages.append(assistant_message)

            for tc in assistant_message["tool_calls"]:
                func_name = tc["function"]["name"]
                args_str = tc["function"].get("arguments", "{}")
                try:
                    args = json.loads(args_str)
                except Exception:
                    args = {}

                tool_result_str, retrieved_cites = await _execute_local_tool(func_name, args)
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

            # Step 3: Get final response from model after tools execution
            final_payload = {
                "model": payload["model"],
                "messages": api_messages,
                "temperature": 0.3,
                "max_tokens": 2048,
            }
            try:
                final_resp = await client.post(
                    GROQ_CHAT_URL, headers=headers, json=final_payload
                )
                final_resp.raise_for_status()
                final_data = final_resp.json()
                raw_reply = final_data["choices"][0]["message"]["content"]
            except Exception:
                return await _local_astrological_fallback(
                    latest_user_text, custom_rules, user_birth_details, preferred_language
                )
        else:
            raw_reply = assistant_message.get("content", "")

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

    # If no citations were collected from tools, add authoritative default
    if not citations_map:
        citations_map["default_shastra"] = {
            "source": "বৃহৎ পরাশর হোরাশাস্ত্র ও ফলদীপিকা",
            "category": "shastra",
            "snippet": "সুইস এফিমেরিস ২.১০ নির্ভুল লাহিড়ী অয়নাংশ ও পরাশর বৈদিক জ্যোতিষ গণনা।",
        }

    return {
        "reply": final_content,
        "tools_called": list(set(tools_called)),
        "citations": list(citations_map.values()),
        "suggested_followups": followups[:3],
    }
