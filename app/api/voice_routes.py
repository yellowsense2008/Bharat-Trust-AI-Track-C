from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import os
import shutil
import asyncio

from sqlalchemy.orm import Session

from app.services.speech_service import transcribe_audio
from app.services.complaint_ai_service import extract_complaint_details
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.complaint_schema import ComplaintCreate
from app.api.complaint_routes import create_complaint

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_file = f"temp_{file.filename}"

    try:
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        transcript = transcribe_audio(temp_file)
        structured = extract_complaint_details(transcript)

        return {
            "transcript": transcript,
            "ai_complaint": structured
        }

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


@router.post("/submit")
async def voice_submit(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    temp_file = f"temp_submit_{file.filename}"

    try:
        # STEP 0: Save file
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # STEP 1: Speech → Text
        transcript = await asyncio.to_thread(transcribe_audio, temp_file)

        # STEP 2: AI Extraction
        ai_data = await asyncio.to_thread(extract_complaint_details, transcript)

        # STEP 3: Safe fallback values
        title = ai_data.get("title") or "Voice Complaint"
        description = ai_data.get("description") or transcript
        ai_category = ai_data.get("category") or "Other"

        # STEP 4: Create complaint payload
        complaint_data = ComplaintCreate(
            title=title,
            description=description,
            category=ai_category  # pass AI category
        )

        # STEP 5: Create complaint
        result = await asyncio.to_thread(
            create_complaint, complaint_data, db, current_user
        )

        # STEP 6: Handle normal complaint response
        if isinstance(result, dict) and "complaint" in result:
            complaint = result["complaint"]

            return {
                "transcript": transcript,
                "complaint": {
                    "id": str(complaint.id),
                    "title": complaint.title,
                    # 🔥 FORCE AI CATEGORY (FINAL FIX)
                    "category": ai_category,
                    "description": complaint.description,
                    "status": complaint.status
                }
            }

        # STEP 7: Handle auto-resolution / duplicate case
        return {
            "transcript": transcript,
            "message": result.get("message"),
            "auto_resolution": result.get("auto_resolution"),
            "category": ai_category  # 🔥 also force here
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)