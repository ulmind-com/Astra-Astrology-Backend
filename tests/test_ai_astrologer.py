import json
import pytest
from app.services.ai.knowledge_service import _chunk_text, _clean_text
from app.services.ai.groq_service import _execute_local_tool


def test_text_cleaning_and_chunking():
    raw_sample = "  বৃহৎ পরাশর হোরাশাস্ত্র মতে লগ্ন বিচার।\n\n\n  মঙ্গল যদি ৪র্থ বা ৭ম ভাবে থাকে তবে মাঙ্গলিক যোগ হয়।  "
    cleaned = _clean_text(raw_sample)
    assert "বৃহৎ পরাশর" in cleaned
    assert "\n\n\n" not in cleaned

    long_text = "\n\n".join([f"প্যারাগ্রাফ {i}: বৃহস্পতি গ্রহ জ্ঞান ও ধর্মের কারক। নবম ও পঞ্চম ভাবে শুভ দৃষ্টি।" for i in range(20)])
    chunks = _chunk_text(long_text, chunk_size=300, overlap=50)
    assert len(chunks) > 1
    assert "বৃহস্পতি" in chunks[0]


@pytest.mark.asyncio
async def test_local_tool_execution():
    # 1. Test kundli tool execution
    kundli_args = {
        "name": "Arjun",
        "day": 10,
        "month": 5,
        "year": 1992,
        "hour": 14,
        "minute": 20,
        "lat": 22.5726,
        "lon": 88.3639,
        "place": "Kolkata",
    }
    raw_res, citations = await _execute_local_tool("calculate_kundli_tool", kundli_args)
    data = json.loads(raw_res)
    assert "ascendant_sign" in data
    assert "moon_sign" in data
    assert "current_dasha" in data
    assert len(citations) > 0

    # 2. Test daily horoscope tool execution
    horo_args = {"rashi_index": 0}  # Aries
    horo_res, horo_citations = await _execute_local_tool("get_daily_horoscope_tool", horo_args)
    horo_data = json.loads(horo_res)
    assert "sign_name" in horo_data
    assert "beej_mantra" in horo_data


@pytest.mark.asyncio
async def test_groq_astrology_response():
    from app.services.ai.groq_service import generate_astrology_response

    messages = [
        {"role": "user", "content": "জ্যোতিষ শাস্ত্রে সূর্য গ্রহের মূল কারকতা কি কি?"}
    ]
    res = await generate_astrology_response(messages)
    assert "reply" in res
    assert len(res["reply"]) > 20
    assert "suggested_followups" in res

