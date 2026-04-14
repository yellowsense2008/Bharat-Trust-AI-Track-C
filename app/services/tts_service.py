"""
tts_service.py — Text-to-speech using Indic Parler TTS on GCP VM.

Calls the TTS server running on 35.244.58.187:8888
"""

import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)

# GCP VM endpoint
VM_URL = "http://35.244.58.187:8888/synthesize"


async def _generate(text: str, language: str = "hi") -> str | None:
    """Call Indic Parler TTS on GCP VM."""
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"text": text, "language": language}
            async with session.post(
                VM_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("audio")
                else:
                    error = await response.text()
                    logger.error(f"VM TTS error {response.status}: {error}")
                    return None
    except Exception as exc:
        logger.error("TTS error: %s", exc)
        return None


def generate_tts(text: str, language: str = "hi") -> str | None:
    """
    Synchronous wrapper around the async TTS core.
    
    Args:
        text: Text to convert to speech
        language: Language code (hi, ta, gu, te, kn, mr, etc.)
    
    Returns a base64-encoded audio string, or None on failure.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _generate(text, language))
                return future.result()
        except RuntimeError:
            return asyncio.run(_generate(text, language))

    except Exception as exc:
        logger.error("TTS error: %s", exc)
        return None