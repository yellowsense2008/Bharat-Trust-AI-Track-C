"""
chat_flow_service.py
Thin orchestration layer for the 4-step complaint intake chatbot.

Delegates to:
  - session_manager  → session lifecycle & TTL
  - flow_engine      → step logic, Hinglish normalisation, complaint assembly
  - extraction_service (via flow_engine Step 3) → Groq LLM + regex fallback

Public API (unchanged):
    process_message(session_id: str, message: str) -> dict

Response shape — **extended** with `meta` and `complaint` while keeping
the original `reply / step / data / completed` keys for full backward
compatibility with chat_routes.py.
"""

from app.services import session_manager, flow_engine


def process_message(session_id: str, message: str) -> dict:
    """
    Advance the complaint intake conversation by one step.

    Returns a standardised dict:
    {
        "reply":     str,
        "step":      int,
        "completed": bool,
        "data":      dict,
        "meta": {
            "confidence": float,
            "source":     "rule" | "llm"
        },
        "complaint": dict | None   # present only when completed == True
    }
    """
    session = session_manager.get_or_create(session_id)

    result = flow_engine.process_step(session, message)

    # Persist any mutations made inside process_step
    session_manager.update(session_id, session)

    return {
        "reply":     result["reply"],
        "step":      session["step"],
        "completed": result["completed"],
        "data":      session["data"],
        "meta":      result["meta"],
        "complaint": result.get("complaint"),
    }

