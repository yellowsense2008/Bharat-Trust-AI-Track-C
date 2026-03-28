"""
flow_engine.py
Rule-based, 4-step complaint intake flow controller.

FLOW:
  Step 1 → detect_category    (keyword match)
  Step 2 → ask_subcategory    (store raw user input)
  Step 3 → extract_amount_time (call extraction_service)
  Step 4 → confirm_issue      (finalise and mark complete)

Each step handler returns:
    { reply: str, next_step: int, meta: { confidence: float, source: str } }
"""

import re
from app.services import extraction_service

# ─── Flow map ─────────────────────────────────────────────────────────────────

FLOW = {
    1: "detect_category",
    2: "ask_subcategory",
    3: "extract_amount_time",
    4: "confirm_issue",
}

# ─── Hinglish normalisation table ─────────────────────────────────────────────

_HINGLISH_MAP: dict[str, str] = {
    "mera payment fail ho gaya": "payment failed",
    "paisa nahi aaya": "money not received",
    "paise nahi aaye": "money not received",
    "transaction fail": "transaction failed",
    "paise kat gaye": "amount deducted",
    "upi fail": "upi failed",
    "nahi mila": "not received",
    "kal": "yesterday",
    "aaj": "today",
    "abhi": "just now",
    "subah": "morning",
    "raat": "night",
    "shaam": "evening",
    "ghante": "hours",
    "rupaye": "rupees",
    "rupee": "rupees",
}


def normalize_text(text: str) -> str:
    """
    Lowercase and apply Hinglish→English phrase substitutions.
    Works left-to-right; longer phrases are matched before shorter ones.
    """
    text = text.lower().strip()
    for hindi, english in sorted(_HINGLISH_MAP.items(), key=lambda x: -len(x[0])):
        text = text.replace(hindi, english)
    return text


# ─── Step helpers ─────────────────────────────────────────────────────────────

_PAYMENT_KEYWORDS = {
    "payment", "upi", "money", "transfer", "paytm", "gpay",
    "phonepe", "rupees", "rupee", "₹", "debit", "credit",
    "transaction", "bank",
}


def _detect_category(text: str) -> str | None:
    tokens = set(re.findall(r"\w+", text.lower()))
    if tokens & _PAYMENT_KEYWORDS:
        return "Payments"
    return None


# ─── Core dispatcher ──────────────────────────────────────────────────────────

def process_step(session: dict, raw_message: str) -> dict:
    """
    Advance *session* one step.

    Returns:
        {
            "reply": str,
            "next_step": int,
            "completed": bool,
            "meta": { "confidence": float, "source": "rule|llm" },
            "complaint": dict | None,   # set only when completed
        }
    """
    message = normalize_text(raw_message)
    step = session["step"]

    # ─ Already completed guard ────────────────────────────────────────────────
    if session.get("completed"):
        return {
            "reply": "Aapki complaint pehle hi register ho chuki hai.",
            "next_step": step,
            "completed": True,
            "meta": {"confidence": 1.0, "source": "rule"},
            "complaint": None,
        }

    # ─ Step 1: detect category ────────────────────────────────────────────────
    if step == 1:
        category = _detect_category(message)
        if category:
            session["data"]["category"] = category
            session["step"] = 2
            return {
                "reply": "Aapka payment kis type ka tha? (UPI / Card / Net Banking / Loan)",
                "next_step": 2,
                "completed": False,
                "meta": {"confidence": 0.9, "source": "rule"},
                "complaint": None,
            }
        else:
            return {
                "reply": (
                    "Mujhe samajh nahi aaya. Kya aapki shikayat payment, UPI, "
                    "ya money se related hai? Please thoda aur batayein."
                ),
                "next_step": 1,
                "completed": False,
                "meta": {"confidence": 0.0, "source": "rule"},
                "complaint": None,
            }

    # ─ Step 2: store subcategory ──────────────────────────────────────────────
    elif step == 2:
        session["data"]["subcategory"] = raw_message.strip()
        session["step"] = 3
        return {
            "reply": "Kitni amount thi aur kab fail hua? (e.g. ₹500, yesterday)",
            "next_step": 3,
            "completed": False,
            "meta": {"confidence": 1.0, "source": "rule"},
            "complaint": None,
        }

    # ─ Step 3: extract amount + time via LLM ─────────────────────────────────
    elif step == 3:
        extracted = extraction_service.extract_amount_time(raw_message)
        session["data"]["amount"] = extracted.get("amount")
        session["data"]["time"] = extracted.get("time")
        session["step"] = 4
        return {
            "reply": "Kya aapko amount debit hua tha ya transaction pending hai?",
            "next_step": 4,
            "completed": False,
            "meta": {
                "confidence": extracted.get("confidence", 0.8),
                "source": extracted.get("source", "rule"),
            },
            "complaint": None,
        }

    # ─ Step 4: finalise issue ─────────────────────────────────────────────────
    elif step == 4:
        from app.services.complaint_builder import build_complaint
        session["data"]["issue"] = raw_message.strip()
        session["completed"] = True
        complaint = build_complaint(session["data"])
        return {
            "reply": "Complaint registered successfully. Aapki shikayat note kar li gayi hai.",
            "next_step": 4,
            "completed": True,
            "meta": {"confidence": 1.0, "source": "rule"},
            "complaint": complaint,
        }

    # ─ Invalid state ──────────────────────────────────────────────────────────
    else:
        return {
            "reply": "Invalid session state. Please start a new session.",
            "next_step": step,
            "completed": False,
            "meta": {"confidence": 0.0, "source": "rule"},
            "complaint": None,
        }
