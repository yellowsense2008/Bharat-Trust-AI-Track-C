"""conversation_routes.py
Conversational Complaint Intake API endpoints.
Supports natural language complaint filing with emotion detection.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.complaint_schema import ComplaintCreate
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
        
        return {
            "session_id": str(current_user.id),
            "ai_response": ai_response,
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
                "complaint_id": str(complaint['id']),
                "show_reference_prominently": True  # ✅ Signal frontend to show this ID
            }
        
        # Conversation continues
        return {
            "conversation_complete": False,
            "ai_response": result
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
    
    # Filter to show only relevant fields
    filtered = get_citizen_friendly_resolution({
        "reference_id": complaint.reference_id,
        "title": complaint.title,
        "resolution": complaint.resolution,
        "timeline": complaint.resolution  # Extract timeline from resolution text
    })
    
    return filtered