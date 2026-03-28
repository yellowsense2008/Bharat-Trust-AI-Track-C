import os
import json
from groq import Groq

_groq_client = None


def _get_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def _keyword_category(transcript: str) -> str:
    """Rule-based category detection from transcript keywords."""
    text = transcript.lower()
    if "upi" in text or "payment" in text or "money" in text:
        return "Payments"
    elif "loan" in text:
        return "Loan"
    elif "fraud" in text or "scam" in text:
        return "Fraud"
    elif "card" in text:
        return "Card"
    return "Other"


def _fallback_response(transcript: str) -> dict:
    """Build a safe fallback response using keyword-detected category."""
    category = _keyword_category(transcript)
    title = "Payment Issue" if category == "Payments" else "Voice Complaint"
    return {
        "title": title,
        "category": category,
        "description": transcript
    }


def extract_complaint_details(transcript: str):
    try:
        prompt = f"""
You are an RBI grievance assistant.

Convert the following user speech transcript into structured complaint JSON.

Rules:
- Detect complaint title
- Detect category (Payments, Loan, Fraud, Card, Banking, Other)
- Prefer specific categories like Payments, Loan, Fraud instead of General
- Do NOT use "General" unless absolutely necessary
- Write short clear description
- Do NOT hallucinate
- Output ONLY JSON

User Speech:
{transcript}

Output format:
{{
"title": "",
"category": "",
"description": ""
}}
"""

        client = _get_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        raw = response.choices[0].message.content
        print(f"[DEBUG] Raw AI response: {raw}")

        cleaned = raw.replace("```json", "").replace("```", "").strip()

        # Parse JSON safely — failures fall through to keyword fallback
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as parse_err:
            print(f"[DEBUG] JSON parse failed: {parse_err} | cleaned={cleaned!r}")
            return _fallback_response(transcript)

        # Rule-based category override (always applied on top of AI response)
        data["category"] = _keyword_category(transcript) or data.get("category", "Other")

        # Improve title if AI left it blank or generic
        if not data.get("title") or data["title"].strip().lower() in ("", "voice complaint"):
            data["title"] = "Payment Issue" if data["category"] == "Payments" else "Voice Complaint"

        return data

    except Exception as e:
        print(f"[DEBUG] extract_complaint_details unexpected error: {e}")
        return _fallback_response(transcript)