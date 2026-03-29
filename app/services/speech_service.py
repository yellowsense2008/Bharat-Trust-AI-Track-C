from faster_whisper import WhisperModel
import tempfile
import os
import asyncio
import edge_tts

# ── Lazy singleton ──────────────────────────────────────────────────────────
# Do NOT load the model at import time.
# Cloud Run must bind to $PORT within a few seconds; a blocking model load
# here will cause the container health-check to time out and the deployment
# to fail with "container failed to start and listen on the port".
_whisper_model = None


def _get_whisper_model() -> WhisperModel:
    """Return the global Whisper model, loading it on first call."""
    global _whisper_model
    if _whisper_model is None:
        # "base" is ~150 MB – reasonable for Cloud Run with enough memory
        _whisper_model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",   # lower RAM, faster CPU inference
        )
    return _whisper_model


def normalize_text(text: str) -> str:
    text = text.lower()

    replacements = {
        "پیمین": "payment",
        "پےمنٹ": "payment",
        "فیل": "fail",
        "ہو گیا": "ho gaya",
        "میرا": "mera",
        "ہے": "hai"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


def transcribe_audio(file_bytes: bytes) -> str:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(file_bytes)
            temp_audio_path = temp_audio.name

        model = _get_whisper_model()   # lazy: loads on first call only
        segments, _ = model.transcribe(
            temp_audio_path,
            task="transcribe",
        )

        text = " ".join([seg.text for seg in segments]).strip()

        os.remove(temp_audio_path)

        # Normalize Hinglish
        text = normalize_text(text)

        return text

    except Exception as e:
        print("Whisper error:", e)
        return ""


def clean_text_for_tts(text: str) -> str:
    import re

    # Remove problematic unicode
    for ch in [
        "\u2028", "\u2029", "\u200b", "\u200c", "\u200d",
        "\u200e", "\u200f", "\u202a", "\u202b", "\u202c",
        "\u202d", "\u202e", "\ufeff",
    ]:
        text = text.replace(ch, " ")

    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")

    # Keep ASCII only (safe)
    text = text.encode("ascii", errors="ignore").decode("ascii")

    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    text = re.sub(r" +", " ", text).strip()

    return text


async def text_to_speech(text: str) -> bytes:
    try:
        text = clean_text_for_tts(text)

        print(f"📝 TTS text ({len(text)} chars): {text}")

        if not text:
            print("⚠️ Empty text for TTS")
            return None

        voice = "en-IN-NeerjaNeural"

        communicate = edge_tts.Communicate(text, voice)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            temp_path = f.name

        await communicate.save(temp_path)

        with open(temp_path, "rb") as f:
            audio = f.read()

        os.remove(temp_path)

        print(f"✅ TTS audio generated: {len(audio)} bytes")

        return audio

    except Exception as e:
        print("❌ TTS ERROR:", e)
        return None