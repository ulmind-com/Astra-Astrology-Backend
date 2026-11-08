"""Turning what someone said into text.

This matters more here than it would elsewhere. A great many of the people this
product is for cannot type Bengali or Hindi comfortably on a phone — the
keyboards are awkward, and for older users they are a wall. Being able to hold
a button and *speak* to the astrologer is the difference between the app being
usable and not.

Groq serves Whisper on the same key that runs the chat, and on a separate
budget: audio is metered in seconds per hour (7,200 of them) rather than
against the 8,000 tokens a minute the readings compete for. Voice therefore
costs nothing that the chat needs.

No language is passed. Whisper detects it, and detection is better than our
guess — a user whose app is set to Bengali may well ask in Hindi, and the
reply language is decided from the transcript afterwards anyway.
"""

from __future__ import annotations

import httpx
from loguru import logger

from app.core.config import settings

GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

#: Turbo is roughly as accurate as the full model on short clips and markedly
#: faster, which is what a held-button recording wants.
MODEL = "whisper-large-v3-turbo"

#: Longest clip accepted. A spoken question is seconds long; anything much
#: past this is either a mistake or someone leaving the button pressed.
MAX_SECONDS = 120

#: Hard ceiling on the upload. Protects the request path regardless of what the
#: browser believes it is sending.
MAX_BYTES = 25 * 1024 * 1024

#: What browsers actually produce from MediaRecorder, plus the common uploads.
ALLOWED_SUFFIXES = (
    ".webm", ".ogg", ".oga", ".mp3", ".mp4", ".m4a", ".wav", ".flac", ".mpga", ".mpeg",
)


class SpeechError(RuntimeError):
    """Transcription did not produce usable text."""


def is_configured() -> bool:
    return bool(settings.GROQ_API_KEY)


async def transcribe(audio: bytes, filename: str = "audio.webm") -> str:
    """The words in this recording.

    Raises `SpeechError` with something a user can act on rather than letting a
    transport error reach them.
    """
    if not settings.GROQ_API_KEY:
        raise SpeechError("Voice input is not configured on this server.")
    if not audio:
        raise SpeechError("The recording was empty.")
    if len(audio) > MAX_BYTES:
        raise SpeechError("That recording is too long. Please keep it under two minutes.")

    name = filename or "audio.webm"
    if not name.lower().endswith(ALLOWED_SUFFIXES):
        # MediaRecorder names vary and some browsers send none at all. The
        # content is what matters to Whisper; the extension only tells it how
        # to open the bytes, so webm is the right default for a browser clip.
        name = "audio.webm"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GROQ_TRANSCRIBE_URL,
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                files={"file": (name, audio, "application/octet-stream")},
                data={"model": MODEL, "response_format": "json"},
            )
    except Exception as exc:  # noqa: BLE001 - network, DNS, timeout
        logger.warning("Whisper call failed: {}", exc)
        raise SpeechError("Could not reach the voice service. Please try again.") from exc

    if response.status_code == 429:
        logger.warning("Whisper rate limited: {}", response.text[:300])
        raise SpeechError("Voice input is busy right now. Please try again in a moment.")
    if response.status_code >= 400:
        logger.error("Whisper rejected the clip ({}): {}", response.status_code, response.text[:300])
        raise SpeechError("That recording could not be read. Please try again.")

    try:
        text = (response.json().get("text") or "").strip()
    except Exception as exc:  # noqa: BLE001
        raise SpeechError("The voice service returned something unreadable.") from exc

    if not text:
        raise SpeechError("Nothing was heard in that recording. Please speak a little louder.")
    return text
