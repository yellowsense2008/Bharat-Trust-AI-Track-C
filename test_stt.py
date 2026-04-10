from app.services.speech_service import transcribe_audio

with open("app/test_audio.wav/english.wav", "rb") as f:
    audio_bytes = f.read()

text = transcribe_audio(audio_bytes)

print("Transcribed text:", text)