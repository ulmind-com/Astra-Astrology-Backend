"""Groq AI Astrologer reasoning engine with Swiss Ephemeris Tool Calling & RAG Grounding."""

import json
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.astrology import DailyHoroscopeRequest, KundliCalculateRequest
from app.services.ai.knowledge_service import match_custom_rules, search_knowledge
from app.services.astrology.daily_horoscope import calculate_daily_horoscope
from app.services.astrology.kundli_service import calculate_kundli

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# System Prompt for 100% Classical Vedic Astrologer
ASTROLOGER_SYSTEM_PROMPT = """You are "Astra Vedic Astrologer" (অ্যাস্ট্রা জ্যোতিষী), an enlightened, compassionate, and deeply knowledgeable classical Vedic Astrologer for Astra Astrology.

Your foundational principles:
1. TRUTH & MATHEMATICAL ACCURACY: Never guess or invent planetary degrees, houses, or dashas. When birth details are available, ALWAYS execute the `calculate_kundli_tool` to get the exact Swiss Ephemeris sidereal planetary positions, running Vimshottari Mahadasha/Antardasha, and divisional charts.
2. CLASSICAL PARASHARI GROUNDING: Base all judgments on Brihat Parashara Hora Shastra, Phaladeepika, and the client's verified Vedic rules. When asked about specific topics (e.g. Manglik, Kaal Sarp, Sade Sati, Vastu, Numerology, Palmistry), consult `search_vedic_rules_tool`.
3. LANGUAGE & TONE: Default to beautiful, respectful, and compassionate Bengali (বাংলা). If the user asks in Hindi or English, respond in that language. Use respectful address (যেমন: "নমস্কার", "আপনার কুন্ডলী বিচার করে দেখা যাচ্ছে...", "শুভকামনা").
4. STRUCTURED GUIDANCE: For every astrological analysis, provide:
   - **গ্রহাবস্থান ও তাৎপর্য (Planetary Position & Analysis)**
   - **চলমান দশা ও সময়কাল (Running Dasha Influence)**
   - **বাস্তবসম্মত ফল ও পরামর্শ (Practical Life Advice)**
   - **শাস্ত্রীয় বৈদিক প্রতিকার (Vedic Remedies: মন্ত্র, ইষ্টদেবতা ও দান)**
5. FOLLOW-UP QUESTIONS: At the very end of your response, always propose 2 or 3 short, intriguing follow-up questions formatted as:
   [FOLLOW_UP: প্রথম প্রশ্ন?]
   [FOLLOW_UP: দ্বিতীয় প্রশ্ন?]
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
            "name": "search_vedic_rules_tool",
            "description": "Searches classical Vedic astrology scriptures and client's resource documents for rules, dosha remedies, gemstone guidelines, or vastu principles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Astrology topic or question keywords to search"},
                    "category": {"type": "string", "description": "Optional category (kundli, rashi, vastu, numerology, palmistry)"},
                },
                "required": ["query"],
            },
        },
    },
]


def _execute_local_tool(func_name: str, arguments: dict[str, Any]) -> str:
    """Executes local astrology calculations or RAG knowledge search."""
    try:
        if func_name == "calculate_kundli_tool":
            req = KundliCalculateRequest(
                name=arguments.get("name") or "User",
                gender=arguments.get("gender") or "male",
                day=int(arguments["day"]),
                month=int(arguments["month"]),
                year=int(arguments["year"]),
                hour=int(arguments["hour"]),
                minute=int(arguments["minute"]),
                lat=float(arguments.get("lat") or 22.5726),
                lon=float(arguments.get("lon") or 88.3639),
                tzone=5.5,
                place=arguments.get("place") or "Kolkata",
            )
            resp = calculate_kundli(req)

            # Extract compact essential data for LLM reasoning
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
            return json.dumps(summary, ensure_ascii=False)

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
            return json.dumps(summary, ensure_ascii=False)

        elif func_name == "search_vedic_rules_tool":
            import asyncio

            # Run async search_knowledge synchronously
            query = arguments.get("query", "")
            cat = arguments.get("category")
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In active loop
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    results = pool.submit(
                        asyncio.run, search_knowledge(query, cat, top_k=3)
                    ).result()
            else:
                results = asyncio.run(search_knowledge(query, cat, top_k=3))

            return json.dumps(results, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})

    return json.dumps({"status": "unknown_tool"})


async def generate_astrology_response(
    messages: list[dict[str, Any]],
    user_birth_details: dict[str, Any] | None = None,
    stream: bool = False,
) -> dict[str, Any]:
    """Sends prompt & conversation history to Groq (openai/gpt-oss-120b),

    executes tool calls deterministically, and produces a 100% verified astrological synthesis.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured in backend .env")

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    # Match custom high-priority rules from the latest user message
    latest_user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            latest_user_text = m.get("content", "")
            break

    custom_rules = await match_custom_rules(latest_user_text)
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
            f"You may invoke `calculate_kundli_tool` with these details if the user asks personal horoscope questions.\n"
        )

    full_system_prompt = (
        ASTROLOGER_SYSTEM_PROMPT + birth_context + custom_rules_context
    )

    api_messages: list[dict[str, Any]] = [
        {"role": "system", "content": full_system_prompt}
    ]
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    tools_called: list[str] = []
    citations: list[str] = [r.rule_title for r in custom_rules]

    # Groq API invocation with fallback handling
    model_to_use = settings.GROQ_DEFAULT_MODEL or "openai/gpt-oss-120b"

    async with httpx.AsyncClient(timeout=45.0) as client:
        # Step 1: Initial call with tools
        payload = {
            "model": model_to_use,
            "messages": api_messages,
            "tools": ASTRO_TOOLS,
            "tool_choice": "auto",
            "temperature": 0.3,  # Low temperature for authentic astrological consistency
            "max_tokens": 2048,
        }

        try:
            resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
            if resp.status_code == 400 or resp.status_code == 404:
                # Try fallback model
                payload["model"] = settings.GROQ_FALLBACK_MODEL or "qwen/qwen3.8-27b"
                resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)

            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")

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

                tool_result_str = _execute_local_tool(func_name, args)
                tools_called.append(func_name)
                citations.append(f"Engine: {func_name}")

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
            final_resp = await client.post(
                GROQ_CHAT_URL, headers=headers, json=final_payload
            )
            final_resp.raise_for_status()
            final_data = final_resp.json()
            raw_reply = final_data["choices"][0]["message"]["content"]
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

    # Fallback follow-ups if model didn't provide any
    if not followups:
        followups = [
            "আমার কুন্ডলীতে কোন কোন রাজযোগ আছে?",
            "আমার জন্য সবচেয়ে অনুকূল রত্ন কোনটি?",
            "আজকের দিনে কোন হোরায় গুরুত্বপূর্ণ কাজ করা উচিত?",
        ]

    return {
        "reply": final_content,
        "tools_called": list(set(tools_called)),
        "citations": list(set(citations)),
        "suggested_followups": followups[:3],
    }
