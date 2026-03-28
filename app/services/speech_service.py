import os
from groq import Groq


def transcribe_audio(file_path: str):
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    try:
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3"
            )

        return transcription.text

    except Exception as e:
        return f"Speech error: {str(e)}"