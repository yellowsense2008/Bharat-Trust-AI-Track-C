from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import os
import shutil
import asyncio

from sqlalchemy.orm import Session

from app.services.speech_service import transcribe_audio, text_to_speech
from app.services.complaint_ai_service import extract_complaint_details
from app.services.chat_flow_service import process_message

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.complaint_schema import ComplaintCreate
from app.api.complaint_routes import create_complaint

router = APIRouter(prefix="/voice", tags=["Voice"])


# =========================================
# 🎤 TRANSCRIBE ONLY
# =========================================
@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_file = f"temp_{file.filename}"

    try:
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with open(temp_file, "rb") as f:
            transcript = transcribe_audio(f.read())

        structured = extract_complaint_details(transcript)

        return {
            "transcript": transcript,
            "ai_complaint": structured
        }

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


# =========================================
# 🧾 VOICE → COMPLAINT SUBMISSION
# =========================================
@router.post("/submit")
async def voice_submit(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    temp_file = f"temp_submit_{file.filename}"

    try:
        # Save file
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with open(temp_file, "rb") as f:
            audio_bytes = f.read()

        # Speech → Text
        transcript = await asyncio.to_thread(transcribe_audio, audio_bytes)

        # AI Extraction
        ai_data = await asyncio.to_thread(extract_complaint_details, transcript)

        # Fallbacks
        title = ai_data.get("title") or "Voice Complaint"
        description = ai_data.get("description") or transcript
        ai_category = ai_data.get("category") or "Other"

        complaint_data = ComplaintCreate(
            title=title,
            description=description,
            category=ai_category
        )

        result = await asyncio.to_thread(
            create_complaint, complaint_data, db, current_user
        )

        if isinstance(result, dict) and "complaint" in result:
            complaint = result["complaint"]

            return {
                "transcript": transcript,
                "complaint": {
                    "id": str(complaint.id),
                    "title": complaint.title,
                    "category": ai_category,
                    "description": complaint.description,
                    "status": complaint.status
                }
            }

        return {
            "transcript": transcript,
            "message": result.get("message"),
            "auto_resolution": result.get("auto_resolution"),
            "category": ai_category
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


# =========================================
# 🔥 REAL-TIME VOICE CHAT (FINAL)
# =========================================
@router.post("/chat")
async def voice_chat(file: UploadFile = File(...)):
    try:
        # 1. Read audio
        audio_bytes = await file.read()

        # 2. Speech → Text
        text = transcribe_audio(audio_bytes)

        if not text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        # 3. Chat flow
        result = process_message(
            session_id="voice_user",
            message=text
        )

        # 4. Text → Speech (ElevenLabs)
        tts_audio = await text_to_speech(result["reply"])

        return {
            "user_text": text,
            "reply": result["reply"],
            "audio": tts_audio.hex() if tts_audio else None,
            "step": result.get("step"),
            "completed": result.get("completed"),
            "data": result.get("data"),
            "complaint": result.get("complaint")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))