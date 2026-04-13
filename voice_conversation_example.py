"""
voice_conversation_example.py

Example integration of Conversational Intake Engine with Voice (STT/TTS)
This demonstrates how to create a complete voice-based complaint filing system.

NOTE: This is a reference implementation. Actual voice routes already exist
in app/api/voice_routes.py
"""

import requests
from typing import Optional

class VoiceConversationClient:
    """
    Example client showing how to integrate voice with conversational intake.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        self.base_url = base_url
        self.token = token
        self.session_id: Optional[str] = None
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Convert voice to text using Groq Whisper API.
        
        Endpoint: POST /voice/transcribe
        """
        with open(audio_file_path, 'rb') as audio_file:
            response = requests.post(
                f"{self.base_url}/voice/transcribe",
                headers={"Authorization": f"Bearer {self.token}"},
                files={"audio": audio_file}
            )
        
        if response.status_code == 200:
            return response.json()["transcription"]
        else:
            raise Exception(f"Transcription failed: {response.text}")
    
    def start_conversation(self, message: str) -> dict:
        """
        Start conversational intake with transcribed text.
        
        Endpoint: POST /conversation/start
        """
        response = requests.post(
            f"{self.base_url}/conversation/start",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"message": message}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get("session_id")
            return data
        else:
            raise Exception(f"Start conversation failed: {response.text}")
    
    def send_message(self, message: str) -> dict:
        """
        Continue conversation with transcribed text.
        
        Endpoint: POST /conversation/message
        """
        response = requests.post(
            f"{self.base_url}/conversation/message",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"message": message}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Send message failed: {response.text}")
    
    def synthesize_speech(self, text: str, language: str = "en") -> bytes:
        """
        Convert AI response to voice using Edge TTS.
        
        Endpoint: POST /voice/synthesize
        """
        response = requests.post(
            f"{self.base_url}/voice/synthesize",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"text": text, "language": language}
        )
        
        if response.status_code == 200:
            return response.content  # Audio bytes
        else:
            raise Exception(f"Speech synthesis failed: {response.text}")
    
    def voice_conversation_flow(self, audio_input_path: str, audio_output_path: str):
        """
        Complete voice conversation flow:
        1. User speaks (audio file)
        2. Convert to text (STT)
        3. Process through conversation engine
        4. Convert response to speech (TTS)
        5. Play audio response
        """
        
        # Step 1: Transcribe user's voice
        print("🎤 Transcribing user audio...")
        user_text = self.transcribe_audio(audio_input_path)
        print(f"💬 User said: {user_text}")
        
        # Step 2: Process through conversation engine
        print("🤖 Processing through AI...")
        if not self.session_id:
            response = self.start_conversation(user_text)
        else:
            response = self.send_message(user_text)
        
        ai_response = response.get("ai_response", "")
        print(f"🤖 AI response: {ai_response}")
        
        # Step 3: Convert AI response to speech
        print("🔊 Synthesizing speech...")
        audio_bytes = self.synthesize_speech(ai_response)
        
        # Step 4: Save audio response
        with open(audio_output_path, 'wb') as f:
            f.write(audio_bytes)
        print(f"✅ Audio saved to: {audio_output_path}")
        
        return response


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_voice_complaint_filing():
    """
    Example: Complete voice-based complaint filing workflow
    """
    
    # Initialize client
    client = VoiceConversationClient(
        base_url="http://localhost:8000",
        token="your_jwt_token_here"
    )
    
    # Conversation flow
    conversation_steps = [
        ("user_audio_1.wav", "ai_response_1.mp3"),  # Initial complaint
        ("user_audio_2.wav", "ai_response_2.mp3"),  # Bank name
        ("user_audio_3.wav", "ai_response_3.mp3"),  # Transaction type
        ("user_audio_4.wav", "ai_response_4.mp3"),  # Amount
        ("user_audio_5.wav", "ai_response_5.mp3"),  # Date
        ("user_audio_6.wav", "ai_response_6.mp3"),  # Transaction ID
        ("user_audio_7.wav", "ai_response_7.mp3"),  # Issue description
    ]
    
    for input_audio, output_audio in conversation_steps:
        response = client.voice_conversation_flow(input_audio, output_audio)
        
        # Check if conversation is complete
        if response.get("conversation_complete"):
            print("\n✅ Complaint filed successfully!")
            complaint = response.get("complaint", {})
            print(f"📋 Reference ID: {complaint.get('reference_id')}")
            print(f"🏢 Department: {complaint.get('department')}")
            print(f"⚡ Priority: {complaint.get('priority')}")
            break
        
        # Play audio response to user (implementation depends on platform)
        # play_audio(output_audio)
        
        print("\n" + "="*60 + "\n")


# ============================================================================
# ALTERNATIVE: Real-time Voice Conversation
# ============================================================================

def example_realtime_voice_conversation():
    """
    Example: Real-time voice conversation using microphone input
    
    This would require additional libraries:
    - pyaudio (for microphone input)
    - pydub (for audio processing)
    """
    
    import pyaudio  # pip install pyaudio
    import wave
    
    # Initialize
    client = VoiceConversationClient(token="your_token")
    
    # Audio recording settings
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    p = pyaudio.PyAudio()
    
    print("🎤 Voice Complaint Filing System")
    print("="*60)
    
    while True:
        # Record user audio
        print("\n🎤 Listening... (Press Ctrl+C to stop)")
        
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        frames = []
        for i in range(0, int(RATE / CHUNK * 5)):  # 5 seconds
            data = stream.read(CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Save temporary audio file
        temp_audio = "temp_user_audio.wav"
        wf = wave.open(temp_audio, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        # Process through conversation engine
        response = client.voice_conversation_flow(
            temp_audio,
            "ai_response.mp3"
        )
        
        # Play AI response
        # play_audio("ai_response.mp3")
        
        # Check if complete
        if response.get("conversation_complete"):
            print("\n✅ Complaint filed successfully!")
            break
    
    p.terminate()


# ============================================================================
# INTEGRATION WITH EXISTING VOICE ROUTES
# ============================================================================

def example_using_existing_voice_routes():
    """
    Example: Using existing voice routes in the system
    
    The system already has:
    - POST /voice/transcribe (Groq Whisper STT)
    - POST /voice/synthesize (Edge TTS)
    - POST /voice/complaint (Voice complaint submission)
    """
    
    import requests
    
    token = "your_jwt_token"
    base_url = "http://localhost:8000"
    
    # Method 1: Direct voice complaint (existing route)
    with open("user_complaint.wav", "rb") as audio:
        response = requests.post(
            f"{base_url}/voice/complaint",
            headers={"Authorization": f"Bearer {token}"},
            files={"audio": audio}
        )
    
    print("Direct voice complaint:", response.json())
    
    # Method 2: Conversational voice (new approach)
    # Step 1: Transcribe
    with open("user_complaint.wav", "rb") as audio:
        transcribe_response = requests.post(
            f"{base_url}/voice/transcribe",
            headers={"Authorization": f"Bearer {token}"},
            files={"audio": audio}
        )
    
    transcribed_text = transcribe_response.json()["transcription"]
    
    # Step 2: Start conversation
    conv_response = requests.post(
        f"{base_url}/conversation/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": transcribed_text}
    )
    
    ai_response = conv_response.json()["ai_response"]
    
    # Step 3: Synthesize AI response
    tts_response = requests.post(
        f"{base_url}/voice/synthesize",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": ai_response, "language": "en"}
    )
    
    # Save audio response
    with open("ai_response.mp3", "wb") as f:
        f.write(tts_response.content)
    
    print("Conversational voice response saved to ai_response.mp3")


# ============================================================================
# MULTILINGUAL VOICE CONVERSATION
# ============================================================================

def example_multilingual_voice_conversation():
    """
    Example: Voice conversation in multiple languages
    
    Supported languages:
    - English (en)
    - Hindi (hi)
    - Tamil (ta)
    - Gujarati (gu)
    """
    
    client = VoiceConversationClient(token="your_token")
    
    # User speaks in Hindi
    hindi_audio = "user_hindi_complaint.wav"
    
    # Transcribe (Groq Whisper auto-detects language)
    transcribed = client.transcribe_audio(hindi_audio)
    
    # Process through conversation (AI responds in detected language)
    response = client.start_conversation(transcribed)
    
    # Synthesize response in Hindi
    audio_bytes = client.synthesize_speech(
        response["ai_response"],
        language="hi"
    )
    
    with open("ai_response_hindi.mp3", "wb") as f:
        f.write(audio_bytes)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  Voice Conversation Integration Examples                     ║
    ║  Bharat Trust AI - Track C Grievance System                  ║
    ╚══════════════════════════════════════════════════════════════╝
    
    This file demonstrates how to integrate the Conversational
    Intake Engine with voice (STT/TTS) capabilities.
    
    Available examples:
    1. example_voice_complaint_filing()
    2. example_realtime_voice_conversation()
    3. example_using_existing_voice_routes()
    4. example_multilingual_voice_conversation()
    
    To run an example:
    1. Ensure server is running: docker compose up
    2. Get JWT token from /auth/login
    3. Update token in example functions
    4. Run: python voice_conversation_example.py
    
    For production use, integrate with:
    - Mobile app (iOS/Android voice input)
    - Web app (Web Speech API)
    - IVR system (telephony integration)
    - Smart speakers (Alexa/Google Home)
    """)
    
    # Uncomment to run an example:
    # example_using_existing_voice_routes()
