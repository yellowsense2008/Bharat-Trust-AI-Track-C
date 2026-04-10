"""
chat_flow_service.py
Thin orchestration layer for the 4-step complaint intake chatbot.

Delegates to:
  - session_manager  → session lifecycle & TTL
  - flow_engine      → step logic, Hinglish normalisation, complaint assembly
  - extraction_service (via flow_engine Step 3) → Groq LLM + regex fallback

Public API (extended but backward compatible):
    process_message(session_id: str, message: str, language: str = "en") -> dict

Response shape — extended with `meta`, `complaint`, and `language`
while keeping the original `reply / step / data / completed` keys.
"""

from app.services import session_manager, flow_engine


def process_message(session_id: str, message: str, language: str = "en") -> dict:
    """
    Advance the complaint intake conversation by one step.

    Parameters
    ----------
    session_id : str
        Unique identifier for the user session.

    message : str
        User message text (already transcribed from voice).

    language : str
        Detected language code ("en", "hi", "gu", "ta", "kn").
        Used to ensure replies are generated in the same language.
    """

    # Retrieve or initialise session
    session = session_manager.get_or_create(session_id)

    # Store language in the session
    session["language"] = language

    # Run chatbot step
    result = flow_engine.process_step(session, message)

    # Persist session changes
    session_manager.update(session_id, session)

    return {
        "reply": result["reply"],
        "step": session["step"],
        "completed": result["completed"],
        "data": session["data"],
        "meta": result["meta"],
        "complaint": result.get("complaint"),
        "language": session.get("language", language),
    }