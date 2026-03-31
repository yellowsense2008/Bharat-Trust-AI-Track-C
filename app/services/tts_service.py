import asyncio
import base64
import edge_tts
import tempfile
import os


VOICE = "hi-IN-MadhurNeural"


async def _generate(text: str):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tmp_path = f.name

    communicate = edge_tts.Communicate(text=text, voice=VOICE)

    await communicate.save(tmp_path)

    with open(tmp_path, "rb") as audio_file:
        audio_bytes = audio_file.read()

    os.remove(tmp_path)

    return base64.b64encode(audio_bytes).decode("utf-8")


def generate_tts(text: str):
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_generate(text))
    except RuntimeError:
        return asyncio.run(_generate(text))
    except Exception as e:
        print("TTS ERROR:", e)
        return None