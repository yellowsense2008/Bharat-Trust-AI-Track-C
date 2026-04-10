"""
stt_service.py — Speech-to-Text via HuggingFace Inference API.

Uses openai/whisper-large-v3 hosted on HuggingFace.
No local model. No torch. No file downloads.

This module is a thin wrapper — most callers should use speech_service.py
which provides both STT and TTS in one place.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

_HF_API_URL = (
    "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
)


def transcribe_audio(file_bytes: bytes) -> str:
    """
    Send raw audio bytes to HuggingFace Whisper and return the transcript.

    Parameters
    ----------
    file_bytes : bytes
        Raw audio data in any format Whisper accepts (wav, mp3, m4a, ogg …).

    Returns
    -------
    str
        Transcribed text, or empty string on failure.
    """
    api_key = os.getenv("HF_API_KEY", "")
    if not api_key:
        logger.warning("HF_API_KEY not set — STT will fail authentication.")

    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(
            _HF_API_URL,
            headers=headers,
            data=file_bytes,
            timeout=60,
        )

        # HF returns 503 while the model warms up — retry once
        if response.status_code == 503:
            import time  # noqa: PLC0415
            logger.info("HF model warming up — retrying in 20s …")
            time.sleep(20)
            response = requests.post(
                _HF_API_URL,
                headers=headers,
                data=file_bytes,
                timeout=60,
            )

        response.raise_for_status()
        return response.json().get("text", "").strip()

    except Exception as exc:
        logger.error("STT error: %s", exc)
        return ""