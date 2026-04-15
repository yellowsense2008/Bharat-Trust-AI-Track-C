import os
"""conversation_routes.py
Conversational Complaint Intake API endpoints.
Supports natural language complaint filing with emotion detection.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.complaint_schema import ComplaintCreate
from app.services.tts_service import generate_tts
from app.services.language_detector import detect_language
from app.services.conversation_service import (
    start_conversation,
    continue_conversation,
    get_session_state
)
from app.services.status_service import get_complaint_status
from app.api.complaint_routes import create_complaint
from app.models.complaint import Complaint  # ✅ ADD THIS

router = APIRouter(prefix="/conversation", tags=["Conversation"])

status_sessions = {}

class ConversationStartRequest(BaseModel):
    message: str

class ConversationMessageRequest(BaseModel):
    message: str

def detect_status_query(text: str) -> bool:
    """Detect if user is asking about complaint status."""
    keywords = [
        "status", "complaint status", "track complaint",
        "reference number", "status kya hai", "where is my complaint"
    ]
    return any(word in text.lower() for word in keywords)

@router.post("/start")
def start_chat(
    request: ConversationStartRequest,
    current_user: User = Depends(get_current_user)
):
    """Start a new conversational complaint intake session.
    
    The AI will:
    - Detect emotional distress and respond empathetically
    - Extract information from natural language
    - Ask relevant follow-up questions
    - Build a structured complaint form
    """
    
    if detect_status_query(request.message):
        status_sessions[current_user.id] = True
        return {
            "session_id": str(current_user.id),
            "ai_response": "I can help you check your complaint status. Please provide your complaint reference number (e.g., GRV-2026-0001).",
            "next_question": "Please provide your complaint reference number",
            "conversation_complete": False
        }
    
    try:
        ai_response = start_conversation(current_user.id, request.message)
        
        # Generate TTS for AI response
        detected_lang = detect_language(request.message)
        audio = generate_tts(ai_response, detected_lang) if ai_response else None
        return {
            "session_id": str(current_user.id),
            "ai_response": ai_response,
            "audio": audio,
            "conversation_complete": False
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/message")
def send_message(
    request: ConversationMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Continue the conversation and process user responses.
    
    When all required information is collected, automatically creates
    a complaint and returns the reference ID.
    """
    
    # Handle status query flow
    if status_sessions.get(current_user.id):
        try:
            result = get_complaint_status(db, request.message)
            status_sessions.pop(current_user.id)
            
            return {
                "conversation_complete": True,
                "status_lookup": True,
                "result": result
            }
        except Exception as e:
            status_sessions.pop(current_user.id, None)
            raise HTTPException(status_code=404, detail=str(e))
    
    # Handle complaint intake flow
    try:
        result = continue_conversation(current_user.id, request.message)
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Check if conversation is complete
        if isinstance(result, dict) and result.get("complete"):
            complaint_data = ComplaintCreate(
                title=result["title"],
                description=result["description"]
            )
            
            complaint = create_complaint(
                complaint_data=complaint_data,
                db=db,
                current_user=current_user
            )
            
            ref_id = complaint['reference_id']
            
            return {
                "conversation_complete": True,
                "ai_response": f"✅ Your complaint has been successfully filed!\n\n📋 Your Reference ID: {ref_id}\n\nYou can track your complaint status using this ID. Our team will review your complaint and get back to you soon.",
                "reference_id": ref_id,
                "complaint_id": complaint.get('reference_id', 'N/A'),
                "show_reference_prominently": True  # ✅ Signal frontend to show this ID
            }
        
        # Conversation continues
        detected_lang = detect_language(request.message)
        audio = generate_tts(result, detected_lang) if isinstance(result, str) else None
        return {
            "conversation_complete": False,
            "ai_response": result,
            "audio": audio
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@router.get("/session")
def get_session(
    current_user: User = Depends(get_current_user)
):
    """Get current conversation session state (for debugging)."""
    session = get_session_state(current_user.id)
    
    if not session:
        return {"message": "No active session found"}
    
    return {
        "session_id": str(current_user.id),
        "form_state": session["form"],
        "conversation_length": len(session["history"])
    }

@router.get("/resolution/{reference_id}")
def get_resolution_for_user(
    reference_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get FILTERED resolution for user (only relevant fields)."""
    from app.services.citizen_response_service import get_citizen_friendly_resolution
    
    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id,
        Complaint.user_id == current_user.id  # ✅ User can only see own complaint
    ).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if not complaint.resolution:
        return {
            "status": "UNDER_REVIEW",
            "message": "Your complaint is being reviewed. Check back soon."
        }
    
    # Get user's language from complaint description
    from app.services.language_detector import detect_language
    from app.services.translation_service import translate_text
    
    user_language = detect_language(complaint.description) if complaint.description else "en"
    
    # Use ai_suggested_resolution if admin resolution not set
    resolution_text = complaint.resolution or complaint.ai_suggested_resolution or ""
    
    # Filter to show only relevant fields
    filtered = get_citizen_friendly_resolution({
        "reference_id": complaint.reference_id,
        "title": complaint.title,
        "resolution": resolution_text,
        "timeline": resolution_text
    })
    
    # Translate simplified resolution back to user language if not English
    if user_language != "en" and filtered.get("resolution"):
        try:
            filtered["resolution"] = translate_text(
                filtered["resolution"],
                source_lang="en",
                target_lang=user_language
            )
        except Exception as e:
            print(f"[Resolution] Translation failed: {e}")
    
    return filtered

@router.get("/resolution/{reference_id}/audio")
def get_resolution_audio(
    reference_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get TTS audio of resolution + satisfaction question in user's language."""
    from app.services.citizen_response_service import get_citizen_friendly_resolution, simplify_resolution
    from app.services.language_detector import detect_language
    from app.services.translation_service import translate_text
    from app.services.tts_service import generate_tts

    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id,
        Complaint.user_id == current_user.id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    resolution_text = complaint.resolution or complaint.ai_suggested_resolution or ""
    if not resolution_text:
        raise HTTPException(status_code=404, detail="No resolution available yet")

    user_language = detect_language(complaint.description) if complaint.description else "en"

    # Simplify resolution
    simplified = simplify_resolution(resolution_text)

    # Translate to user language if needed
    if user_language != "en":
        try:
            simplified = translate_text(simplified, source_lang="en", target_lang=user_language)
        except Exception as e:
            print(f"[ResolutionAudio] Translation failed: {e}")

    # Generate satisfaction question dynamically in user's language using Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={"temperature": 0.3, "max_output_tokens": 100}
        )
        r = model.generate_content(
            f"Ask the user if they are satisfied with the resolution. "
            f"Tell them to say Yes or No. Respond in {user_language} language only. "
            f"Keep it to one short sentence."
        )
        satisfaction_q = r.text.strip()
    except Exception:
        satisfaction_q = "Are you satisfied with this resolution? Please say Yes or No." if user_language == "en" else "क्या आप इस समाधान से संतुष्ट हैं? हाँ या नहीं में जवाब दें।"

    full_text = f"{simplified}. {satisfaction_q}"

    audio = generate_tts(full_text, user_language)

    return {
        "reference_id": reference_id,
        "resolution_text": simplified,
        "satisfaction_question": satisfaction_q,
        "language": user_language,
        "audio": audio
    }


@router.post("/resolution/{reference_id}/feedback")
async def submit_resolution_feedback(
    reference_id: str,
    file: object = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit voice feedback on resolution - YES resolves, NO escalates."""
    from app.services.stt_service import transcribe_audio
    from app.services.language_detector import detect_language
    from app.services.tts_service import generate_tts
    from app.services.translation_service import translate_text
    from datetime import datetime, timezone

    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id,
        Complaint.user_id == current_user.id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    user_language = detect_language(complaint.description) if complaint.description else "en"

    return {
        "reference_id": reference_id,
        "language": user_language,
        "message": "Use /resolution/{reference_id}/feedback/voice to submit voice feedback"
    }


@router.post("/resolution/{reference_id}/feedback/voice")
async def submit_voice_feedback(
    reference_id: str,
    file: UploadFile = File(default=None),
    satisfied: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit voice or text feedback on resolution.
    - file: audio file (WAV/MP3) with user saying yes/no
    - satisfied: text override ('yes' or 'no') if no audio
    """
    from app.services.stt_service import transcribe_audio
    from app.services.language_detector import detect_language
    from app.services.tts_service import generate_tts
    from app.services.translation_service import translate_text
    from datetime import datetime, timezone

    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id,
        Complaint.user_id == current_user.id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    user_language = detect_language(complaint.description) if complaint.description else "en"

    # Get user response - from audio or text
    user_response = ""
    if file:
        try:
            audio_bytes = await file.read()
            user_response = transcribe_audio(audio_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Audio transcription failed: {e}")
    elif satisfied:
        user_response = satisfied
    else:
        raise HTTPException(status_code=400, detail="Provide either audio file or satisfied parameter")

    # Detect satisfaction
    response_lower = user_response.lower().strip()
    yes_keywords = ["yes", "हाँ", "हां", "ஆம்", "હા", "হ্যাঁ", "satisfied", "ok", "okay", "good", "fine", "correct", "ठीक"]
    no_keywords = ["no", "नहीं", "இல்லை", "ના", "না", "not satisfied", "escalate", "wrong", "disagree"]

    is_satisfied = any(kw in response_lower for kw in yes_keywords)
    is_dissatisfied = any(kw in response_lower for kw in no_keywords)

    if is_satisfied:
        # Mark as RESOLVED
        complaint.status = "RESOLVED"
        complaint.resolution_approved = True
        complaint.resolution_approved_by = str(current_user.id)
        complaint.updated_at = datetime.now(timezone.utc)
        db.commit()

        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.3, "max_output_tokens": 100})
            r = model.generate_content(f"Tell the user their complaint has been successfully resolved. Thank them. Respond in {user_language} language only. One sentence.")
            msg = r.text.strip()
        except Exception:
            msg = "Thank you! Your complaint has been successfully resolved." if user_language == "en" else "धन्यवाद! आपकी शिकायत सफलतापूर्वक हल हो गई है।"
        audio = generate_tts(msg, user_language)

        return {
            "status": "RESOLVED",
            "message": msg,
            "audio": audio,
            "transcription": user_response
        }

    elif is_dissatisfied:
        # Escalate to admin
        complaint.status = "ESCALATED"
        complaint.updated_at = datetime.now(timezone.utc)
        db.commit()

        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.3, "max_output_tokens": 100})
            r = model.generate_content(f"Tell the user their complaint has been escalated to a senior officer who will contact them soon. Be empathetic. Respond in {user_language} language only. One sentence.")
            msg = r.text.strip()
        except Exception:
            msg = "We understand. Your complaint has been escalated to a senior officer." if user_language == "en" else "हम समझते हैं। आपकी शिकायत उच्च अधिकारी को भेज दी गई है।"
        audio = generate_tts(msg, user_language)

        return {
            "status": "ESCALATED",
            "message": msg,
            "audio": audio,
            "transcription": user_response
        }

    else:
        # Unclear response - ask again
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"temperature": 0.3, "max_output_tokens": 50})
            r = model.generate_content(f"Ask the user to please say Yes or No clearly. Respond in {user_language} language only.")
            msg = r.text.strip()
        except Exception:
            msg = "Please say Yes or No." if user_language == "en" else "कृपया हाँ या नहीं में जवाब दें।"
        audio = generate_tts(msg, user_language)

        return {
            "status": "UNCLEAR",
            "message": msg,
            "audio": audio,
            "transcription": user_response
        }