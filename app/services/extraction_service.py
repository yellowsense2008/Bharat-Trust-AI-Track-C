"""
extraction_service.py
LLM-powered extraction of amount and time from free-text complaint messages.
Uses Groq (llama-3.3-70b-versatile) with a regex fallback.
"""

import os
import re
import json
from groq import Groq

# ─── Model config ─────────────────────────────────────────────────────────────

_MODEL = "llama-3.3-70b-versatile"
_groq_client = None


def _get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            _groq_client = Groq(api_key=api_key)
    return _groq_client


# ─── Regex fallback ───────────────────────────────────────────────────────────

def _regex_fallback(text: str) -> dict:
    """Extract amount and time heuristically using regex."""
    amount_match = re.search(
        r"(\d[\d,]*)(?:\s*(?:rs|rupee|rupees|₹))?",
        text,
        re.IGNORECASE,
    )
    time_keywords = [
        "kal", "aaj", "yesterday", "today", "raat", "subah", "shaam",
        "morning", "night", "evening", "hour", "ghante", "minute", "ago",
    ]
    time_found = next((kw for kw in time_keywords if kw in text.lower()), None)

    return {
        "amount": amount_match.group(1).replace(",", "") if amount_match else None,
        "time": time_found,
        "confidence": 0.5,
        "source": "rule",
    }


# ─── LLM extraction ───────────────────────────────────────────────────────────

def extract_amount_time(text: str) -> dict:
    """
    Use Groq LLM to extract amount and time from the user's message.
    Returns a dict: { amount, time, confidence, source }.
    Falls back to regex on any failure or missing API key.
    """
    client = _get_client()
    if client is None:
        return _regex_fallback(text)

    prompt = f"""Extract the transaction amount and time/date from the following complaint text.
Return ONLY valid JSON with keys "amount" (numeric string or null) and "time" (string or null).
Include a "confidence" field (float 0.0–1.0) for how certain you are.
Do NOT include any explanation.

Text: {text}

Output format:
{{"amount": "", "time": "", "confidence": 0.9}}
"""
    try:
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)

        return {
            "amount": parsed.get("amount") or None,
            "time": parsed.get("time") or None,
            "confidence": float(parsed.get("confidence", 0.85)),
            "source": "llm",
        }
    except Exception as exc:
        print(f"[extraction_service] Groq failed: {exc} — using regex fallback")
        return _regex_fallback(text)
