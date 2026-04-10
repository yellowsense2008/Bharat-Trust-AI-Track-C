from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

from app.schemas.complaint_schema import ComplaintCreate

from app.services.conversation_service import (
    start_conversation,
    continue_conversation
)

from app.services.status_service import get_complaint_status

from app.api.complaint_routes import create_complaint


router = APIRouter(prefix="/conversation", tags=["Conversation"])


status_sessions = {}


def detect_status_query(text: str):

    keywords = [
        "status",
        "complaint status",
        "track complaint",
        "reference number",
        "status kya hai"
    ]

    text = text.lower()

    return any(word in text for word in keywords)


@router.post("/start")
def start_chat(
    message: str,
    current_user: User = Depends(get_current_user)
):

    if detect_status_query(message):

        status_sessions[current_user.id] = True

        return {
            "next_question": "Please provide your complaint reference number"
        }

    question = start_conversation(current_user.id, message)

    return {
        "next_question": question
    }


@router.post("/answer")
def answer_chat(
    answer: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if status_sessions.get(current_user.id):

        result = get_complaint_status(db, answer)

        status_sessions.pop(current_user.id)

        return {
            "status_lookup": True,
            "result": result
        }

    result = continue_conversation(current_user.id, answer)

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

        return {
            "conversation_complete": True,
            "complaint_response": complaint
        }

    return {
        "conversation_complete": False,
        "next_question": result
    }