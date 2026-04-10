"""
speech_service.py — Lightweight STT + TTS for the grievance voice pipeline.

STT: Groq Whisper API (whisper-large-v3)
     ✅ No local model
     ✅ No torch / transformers
     ✅ Fast real-time transcription
     ✅ Multilingual (EN / HI / TA / KN / GU auto-detected)

TTS: edge-tts
     ✅ No local model
     ✅ HTTPS-only
     ✅ Returns raw MP3 bytes
"""

from __future__ import annotations

import logging
import os
import re
import tempfile
import unicodedata

from groq import Groq
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


def validate_startup() -> None:
    """
    Call this from the FastAPI lifespan handler.
    Logs a WARNING (not a crash) if required env vars are absent,
    so the container starts and health checks pass, but operators
    can see the problem immediately in Cloud Run logs.
    """
    required = ["GROQ_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        logger.warning(
            "⚠️  Missing environment variable(s): %s — "
            "voice transcription will fail on first request. "
            "Set them via: gcloud run services update <SERVICE> "
            "--region asia-south1 --set-env-vars %s=<VALUE>",
            ", ".join(missing),
            "=", 
        )
    else:
        logger.info("✅ All required env vars present (GROQ_API_KEY).")

# ── Constants ─────────────────────────────────────────────────────────────────

VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",
    "hi": "en-IN-NeerjaNeural",
    "ta": "en-IN-NeerjaNeural",
    "gu": "en-IN-NeerjaNeural",
    "kn": "en-IN-NeerjaNeural",
}

# Lazy-initialised Groq client — avoids crash at import time if GROQ_API_KEY is missing
_groq_client: Groq | None = None


def _get_groq_client() -> Groq:
    """Return the Groq singleton, creating it on first call."""
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set in this container's environment. "
                "Fix with: "
                "gcloud run services update rbi-track-c-api "
                "--region asia-south1 "
                "--set-env-vars GROQ_API_KEY=<your-key>  "
                "OR use --set-secrets for Secret Manager."
            )
        _groq_client = Groq(api_key=api_key)
        logger.info("Groq client initialised successfully.")
    return _groq_client

# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_for_tts(text: str) -> str:
    """Sanitise text before sending to edge-tts."""
    text = unicodedata.normalize("NFC", text)

    text = re.sub(r"[\u0000-\u001f\u007f\u2028\u2029\ufeff]", " ", text)

    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
    }

    for src, dst in replacements.items():
        text = text.replace(src, dst)

    return " ".join(text.split()).strip()


# ── Language Detection (Unicode based) ────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Detect Indian language using unicode script ranges.
    """

    for char in text:
        code = ord(char)

        if 0x0A80 <= code <= 0x0AFF:
            return "gu"

        if 0x0900 <= code <= 0x097F:
            return "hi"

        if 0x0B80 <= code <= 0x0BFF:
            return "ta"

        if 0x0C80 <= code <= 0x0CFF:
            return "kn"

    return "en"


# ── Translation Helper ────────────────────────────────────────────────────────

def translate_text(text: str, target_lang: str) -> str:
    """
    Translate text into the target language script.
    """

    try:
        if target_lang == "en":
            return text

        translated = GoogleTranslator(
            source="en",
            target=target_lang
        ).translate(text)

        return translated

    except Exception as exc:
        logger.warning("Translation failed: %s", exc)
        return text


# ── Speech-to-Text ────────────────────────────────────────────────────────────

def transcribe_audio(file_bytes: bytes) -> dict:
    """
    Transcribe raw audio bytes to text using Groq Whisper.
    """

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir="/tmp") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcription = _get_groq_client().audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3"
            )

        text = transcription.text.strip()

        language = detect_language(text)

        logger.info("STT raw transcript → %s", text)
        logger.info("🌍 Detected language → %s", language)

        return {
            "text": text,
            "language": language
        }

    except Exception as exc:
        logger.error("STT error: %s", exc)
        return {"text": "", "language": "unknown"}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── Text-to-Speech ────────────────────────────────────────────────────────────

async def text_to_speech(text: str, language: str = "en") -> bytes | None:
    """
    Convert text to speech using edge-tts (Microsoft Neural voices).
    Returns raw MP3 bytes or None on failure.
    """
    import edge_tts

    voice = VOICE_MAP.get(language, VOICE_MAP["en"])
    clean_text = _clean_for_tts(text)

    if not clean_text:
        logger.warning("TTS received empty text after sanitisation")
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir="/tmp") as tmp:
            tmp_path = tmp.name

        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(tmp_path)

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        logger.info("TTS produced %d bytes (voice=%s)", len(audio_bytes), voice)
        return audio_bytes

    except Exception as exc:
        logger.error("TTS error: %s", exc)
        return None

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)