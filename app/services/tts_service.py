"""
tts_service.py — Text-to-speech using Google Cloud Text-to-Speech API.
Supports all major Indian languages with natural Wavenet voices.
"""

import logging
import requests
import subprocess

logger = logging.getLogger(__name__)

# Language code to Google Cloud TTS voice mapping
VOICE_MAP = {
    "hi": {"languageCode": "hi-IN", "name": "hi-IN-Wavenet-D"},
    "ta": {"languageCode": "ta-IN", "name": "ta-IN-Wavenet-D"},
    "gu": {"languageCode": "gu-IN", "name": "gu-IN-Wavenet-B"},
    "bn": {"languageCode": "bn-IN", "name": "bn-IN-Wavenet-B"},
    "mr": {"languageCode": "mr-IN", "name": "mr-IN-Wavenet-C"},
    "pa": {"languageCode": "pa-IN", "name": "pa-IN-Wavenet-A"},
    "te": {"languageCode": "te-IN", "name": "te-IN-Wavenet-D"},
    "kn": {"languageCode": "kn-IN", "name": "kn-IN-Wavenet-D"},
    "ml": {"languageCode": "ml-IN", "name": "ml-IN-Wavenet-D"},
    "en": {"languageCode": "en-IN", "name": "en-IN-Wavenet-D"},
}

GCP_TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
GCP_PROJECT = "build-for-bharat-yellowsense"


def _get_access_token() -> str:
    """Get GCP access token using metadata server (works in Cloud Run automatically)."""
    try:
        # Cloud Run metadata server
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
            headers={"Metadata-Flavor": "Google"},
            timeout=5
        )
        return response.json()["access_token"]
    except Exception:
        # Fallback to gcloud CLI
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()


def generate_tts(text: str, language: str = "hi") -> str | None:
    """
    Convert text to speech using Google Cloud TTS.

    Args:
        text: Text to convert to speech
        language: ISO language code (hi, ta, gu, bn, mr, pa, te, kn, ml, en)

    Returns:
        Base64-encoded MP3 audio string, or None on failure.
    """
    try:
        voice = VOICE_MAP.get(language, VOICE_MAP["hi"])
        token = _get_access_token()

        payload = {
            "input": {"text": text},
            "voice": voice,
            "audioConfig": {"audioEncoding": "MP3"}
        }

        response = requests.post(
            GCP_TTS_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "x-goog-user-project": GCP_PROJECT
            },
            timeout=15
        )

        if response.status_code == 200:
            audio = response.json().get("audioContent")
            if audio:
                return audio
            logger.error("GCP TTS returned no audioContent")
            return None
        else:
            logger.error(f"GCP TTS error {response.status_code}: {response.text}")
            return None

    except Exception as exc:
        logger.error("TTS error: %s", exc)
        return None