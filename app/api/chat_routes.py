"""
chat_routes.py
POST /chat/message — structured complaint flow endpoint.
No authentication required; session is identified by session_id in the body.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.services.chat_flow_service import process_message
from app.services.tts_service import generate_tts

router = APIRouter(prefix="/chat", tags=["Chat Flow"])


# ─── Request / Response schemas ───────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

    @field_validator("session_id", "message")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty")
        return v.strip()


class MetaField(BaseModel):
    confidence: float
    source: str  # "rule" | "llm"


class ChatMessageResponse(BaseModel):
    # ── Original fields (backward-compatible) ────────────────────────────────
    reply: str
    step: int
    completed: bool
    data: dict

    # ── New fields ────────────────────────────────────────────────────────────
    meta: MetaField
    complaint: Optional[dict] = None

    # 🔊 NEW FIELD
    audio: Optional[str] = None


# ─── Error response helper ────────────────────────────────────────────────────

def _error_response(message: str, code: str, status: int = 500):
    raise HTTPException(
        status_code=status,
        detail={"error": True, "message": message, "code": code}
    )


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/message", response_model=ChatMessageResponse)
def chat_message(body: ChatMessageRequest):
    """
    Advance the complaint intake conversation by one step.

    - Step 1: Detect payment category from user message.
    - Step 2: Collect payment subcategory.
    - Step 3: Extract amount and time (via Groq LLM or regex fallback).
    - Step 4: Save issue details and mark complaint as completed.

    Response always includes:
      reply, step, completed, data, meta { confidence, source }, complaint?
    """

    try:
        # Process chat flow
        result = process_message(body.session_id, body.message)

        # 🔊 Generate voice reply using Indic Parler-TTS
        audio_base64 = generate_tts(result["reply"])

        # Attach audio to response
        result["audio"] = audio_base64

        return result

    except ValueError as exc:
        _error_response(str(exc), "VALIDATION_ERROR", status=422)

    except Exception as exc:
        _error_response(str(exc), "INTERNAL_ERROR", status=500)