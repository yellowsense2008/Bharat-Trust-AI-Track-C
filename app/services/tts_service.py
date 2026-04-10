"""
tts_service.py — Text-to-speech using edge-tts with LAZY import.

edge_tts is imported inside the function body so it does not add
any cost to the container startup / import phase.
"""

import asyncio
import base64
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

VOICE = "hi-IN-MadhurNeural"


async def _generate(text: str) -> str:
    """Async core: edge-tts → MP3 bytes → base64 string."""
    import edge_tts  # deferred — keeps startup fast  # noqa: PLC0415

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tmp_path = f.name

        communicate = edge_tts.Communicate(text=text, voice=VOICE)
        await communicate.save(tmp_path)

        with open(tmp_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        return base64.b64encode(audio_bytes).decode("utf-8")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def generate_tts(text: str) -> str | None:
    """
    Synchronous wrapper around the async TTS core.

    Returns a base64-encoded MP3 string, or None on failure.
    Called from synchronous FastAPI route handlers.
    """
    try:
        try:
            # If there is already a running event loop (e.g. in tests),
            # schedule as a coroutine in the existing loop.
            loop = asyncio.get_running_loop()
            import concurrent.futures  # noqa: PLC0415
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _generate(text))
                return future.result()
        except RuntimeError:
            # No running loop — safe to call asyncio.run directly.
            return asyncio.run(_generate(text))

    except Exception as exc:
        logger.error("TTS error: %s", exc)
        return None