"""Tests for AI Astrologer voice transcription endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_voice_transcribe_empty_file_rejected(client: AsyncClient):
    """Empty or tiny audio clips return 400 Bad Request."""
    files = {"file": ("recording.m4a", b"short", "audio/m4a")}
    res = await client.post("/api/v1/ai-chat/voice-transcribe", files=files)
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["error_code"] == "audio_too_short"


@pytest.mark.asyncio
async def test_voice_transcribe_success_mocked(client: AsyncClient):
    """Valid audio files are successfully transcribed via Whisper."""
    # Dummy audio bytes with length >= 50 bytes
    dummy_audio = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 60
    files = {"file": ("recording.m4a", dummy_audio, "audio/m4a")}

    with patch("app.services.ai.speech.transcribe", new=AsyncMock(return_value="আমার কুম্ভ রাশির আজকের দিনটি কেমন যাবে?")):
        res = await client.post("/api/v1/ai-chat/voice-transcribe", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["text"] == "আমার কুম্ভ রাশির আজকের দিনটি কেমন যাবে?"


@pytest.mark.asyncio
async def test_voice_transcribe_alias_route(client: AsyncClient):
    """Both /ai-chat/voice-transcribe and /ai-astrologer/transcribe route correctly."""
    dummy_audio = b"\x1aE\xdf\xa3" + b"\x00" * 60
    files = {"file": ("speech.webm", dummy_audio, "audio/webm")}

    with patch("app.services.ai.speech.transcribe", new=AsyncMock(return_value="Tell me about Jupiter transit")):
        res = await client.post("/api/v1/ai-astrologer/transcribe", files=files)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["text"] == "Tell me about Jupiter transit"
