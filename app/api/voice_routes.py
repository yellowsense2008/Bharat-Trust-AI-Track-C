import asyncio
import os
import base64

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.complaint_routes import create_complaint
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.complaint_schema import ComplaintCreate
from app.services.chat_flow_service import process_message
from app.services.complaint_ai_service import extract_complaint_details
from app.services.speech_service import text_to_speech, transcribe_audio, translate_text

router = APIRouter(prefix="/voice", tags=["Voice"])


# =========================================
# 🎤 TRANSCRIBE ONLY
# =========================================
@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Upload audio → transcribe via Groq Whisper → extract complaint fields.
    No authentication required.
    """

    audio_bytes = await file.read()

    # Speech → Text
    result = await asyncio.to_thread(transcribe_audio, audio_bytes)

    transcript = result.get("text")
    language = result.get("language")

    if transcript is None or transcript == "":
        raise HTTPException(
            status_code=422,
            detail="Could not transcribe audio. Ensure the file contains clear speech.",
        )

    structured = await asyncio.to_thread(extract_complaint_details, transcript)

    # Translate complaint fields to user's language
    structured["title"] = translate_text(structured.get("title", ""), language)
    structured["description"] = translate_text(structured.get("description", ""), language)

    return {
        "transcript": transcript,
        "language": language,
        "ai_complaint": structured,
    }


# =========================================
# 🧾 VOICE → COMPLAINT SUBMISSION
# =========================================
@router.post("/submit")
async def voice_submit(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload audio → transcribe → run AI pipeline → save complaint to DB.
    JWT authentication required.
    """

    audio_bytes = await file.read()

    # Speech → Text
    result = await asyncio.to_thread(transcribe_audio, audio_bytes)

    transcript = result.get("text")
    language = result.get("language")

    if not transcript:
        raise HTTPException(
            status_code=422,
            detail="Could not transcribe audio. Please try again with a clearer recording.",
        )

    # AI Extraction
    ai_data = await asyncio.to_thread(extract_complaint_details, transcript)

    title = ai_data.get("title") or "Voice Complaint"
    description = ai_data.get("description") or transcript

    complaint_data = ComplaintCreate(
        title=title,
        description=description + f"\n\nVoice Transcript: {transcript}"
    )

    result = await asyncio.to_thread(
        create_complaint, complaint_data, db, current_user
    )

    if isinstance(result, dict) and "complaint" in result:
        complaint = result["complaint"]

        return {
            "transcript": transcript,
            "language": language,
            "complaint": {
                "id": str(complaint.id),
                "reference_id": complaint.reference_id,
                "title": complaint.title,
                "category": complaint.category,
                "description": complaint.description,
                "status": complaint.status,
            },
        }

    return {
        "transcript": transcript,
        "language": language,
        "message": result.get("message"),
        "auto_resolution": result.get("auto_resolution"),
    }


# =========================================
# 🔥 REAL-TIME VOICE CHAT
# =========================================
@router.post("/chat")
async def voice_chat(file: UploadFile = File(...)):
    try:
        # 1. Read audio
        audio_bytes = await file.read()

        # 2. Speech → Text
        result = await asyncio.to_thread(transcribe_audio, audio_bytes)

        text = result.get("text")
        language = result.get("language")

        if not text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        # 3. Chat flow
        chat_result = process_message(
            session_id="voice_user",
            message=text,
            language=language
        )

        reply_en = chat_result["reply"]

        # 4. Translate reply
        if language in ["hi", "gu", "ta", "kn"]:
            reply_local = translate_text(reply_en, language)
        else:
            reply_local = reply_en

        print("CHAT REPLY:", reply_local)

        # 5. Generate TTS
        from app.services.tts_service import generate_tts
        
        tts_audio_base64 = generate_tts(reply_local, language)
        
        if tts_audio_base64:
            print("TTS SUCCESS")
        else:
            print("TTS FAILED - will return text only")

        return {
            "user_text": text,
            "language": language,
            "reply": reply_local,
            "audio": tts_audio_base64,  # ✅ Returns base64 string (can be played by frontend)
            "step": chat_result.get("step"),
            "completed": chat_result.get("completed"),
            "data": chat_result.get("data"),
            "complaint": chat_result.get("complaint")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# =========================================
# 🔊 TEXT-TO-SPEECH SYNTHESIS
# =========================================
@router.post("/synthesize")
async def synthesize(request: dict):
    """Text-to-Speech synthesis using HuggingFace AI4Bharat."""
    from app.services.tts_service import generate_tts
    
    text = request.get("text", "")
    language = request.get("language", "hi")
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    audio_base64 = generate_tts(text, language)
    
    if not audio_base64:
        raise HTTPException(status_code=500, detail="TTS generation failed")
    
    return {
        "audio": audio_base64,
        "language": language,
        "text": text
    }
