"""
AI-Powered Complaint Resolution Service
========================================
Uses RAG (Retrieval Augmented Generation) over:
  - CPGRAMS financial complaint-resolution pairs
  - RBI regulatory resolution guidelines
"""

import json
import os
import numpy as np
from pathlib import Path
import faiss
import google.generativeai as genai

from app.services.translation_service import translate_text
from app.services.language_detector import detect_language
from app.services.embedding_service import get_embedding

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_PATH = BASE_DIR / "data" / "resolution_knowledge_base.json"
EMBEDDINGS_CACHE_PATH = BASE_DIR / "data" / "kb_embeddings.npy"

# Initialize Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
genai.configure(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# ─────────────────────────────────────────────
# GLOBALS
# ─────────────────────────────────────────────

_kb_entries = None
_kb_embeddings = None
_faiss_index = None

# ─────────────────────────────────────────────
# LOAD KNOWLEDGE BASE
# ─────────────────────────────────────────────


def _load_knowledge_base():
    global _kb_entries, _kb_embeddings, _faiss_index

    if _kb_entries is not None:
        return _kb_entries, _kb_embeddings

    # Handle missing knowledge base gracefully
    if not KNOWLEDGE_BASE_PATH.exists():
        print(f"[ResolutionAI] WARNING: Knowledge base not found at {KNOWLEDGE_BASE_PATH}")
        _kb_entries = []
        return _kb_entries, None

    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        _kb_entries = json.load(f)

    # Load cached embeddings
    if EMBEDDINGS_CACHE_PATH.exists():
        _kb_embeddings = np.load(EMBEDDINGS_CACHE_PATH).astype("float32")

        # Normalize
        faiss.normalize_L2(_kb_embeddings)

        dimension = _kb_embeddings.shape[1]

        index = faiss.IndexFlatIP(dimension)
        index.add(_kb_embeddings)

        _faiss_index = index

        print(f"[ResolutionAI] Loaded {_kb_embeddings.shape[0]} KB embeddings")

        return _kb_entries, _kb_embeddings

    # Don't crash if embeddings missing - use fallback
    print(f"[ResolutionAI] WARNING: KB embeddings file not found at {EMBEDDINGS_CACHE_PATH}")
    return _kb_entries, None


# ─────────────────────────────────────────────
# SIMILARITY SEARCH
# ─────────────────────────────────────────────


def find_similar_complaints(complaint_text: str, top_k: int = 5):
    global _faiss_index

    kb_entries, kb_embeddings = _load_knowledge_base()

    # Handle case where embeddings don't exist
    if _faiss_index is None or kb_embeddings is None:
        print("[ResolutionAI] No embeddings available - using fallback resolution")
        return []

    # Get embedding from API
    query_embedding = get_embedding(complaint_text[:512])

    # HF API may return nested list
    if isinstance(query_embedding[0], list):
        query_embedding = query_embedding[0]

    query_embedding = np.array([query_embedding]).astype("float32")

    faiss.normalize_L2(query_embedding)

    scores, indices = _faiss_index.search(query_embedding, top_k)

    results = []

    for i, idx in enumerate(indices[0]):
        results.append(
            {
                "entry": kb_entries[idx],
                "similarity": float(scores[0][i]),
            }
        )

    return results


# ─────────────────────────────────────────────
# LLM CALL (GEMINI)
# ─────────────────────────────────────────────


def _call_llm(prompt: str):
    """Call Gemini LLM for resolution generation."""
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=(
                "You are an AI resolution assistant for RBI financial complaint handling. "
                "Suggest resolutions grounded in past complaints and RBI regulations. "
                "Be concise and professional."
            ),
            generation_config={"temperature": 0.3, "max_output_tokens": 500}
        )

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"[ResolutionAI] LLM call failed: {e}")
        return None


# ─────────────────────────────────────────────
# RESOLUTION GENERATION
# ─────────────────────────────────────────────


def generate_resolution(
    complaint_text: str,
    category: str = None,
    language: str = "en",
):
    """Generate AI-powered resolution for a complaint."""

    # Language detection
    if not language or language == "auto":
        language = detect_language(complaint_text)
        print(f"[LanguageDetection] Detected language: {language}")

    # Translate → English
    if language != "en":
        try:
            complaint_text = translate_text(
                complaint_text,
                source_lang=language,
                target_lang="en",
            )
            print(f"[Translation] Complaint translated {language} → en")
        except Exception as e:
            print(f"[Translation] Failed: {e}")

    # Find similar complaints
    similar = find_similar_complaints(complaint_text, top_k=5)

    if not similar or (similar and similar[0]["similarity"] < 0.15):
        # Use Gemini for fallback
        fallback_prompt = f"""
Given this banking complaint, suggest a professional resolution:

{complaint_text}

Provide:
1. Resolution action
2. Timeline (in days)
3. Regulatory reference (if applicable)

Keep it concise and customer-friendly."""

        llm_response = _call_llm(fallback_prompt)

        return {
            "suggested_resolution": llm_response or "Your complaint is being reviewed. We will contact you within 7 working days.",
            "confidence": 0.5,
            "estimated_resolution_days": 7,
            "regulatory_reference": "RBI Ombudsman Guidelines",
            "similar_cases_count": 0,
            "source": "AI_Generated_Fallback",
        }

    # Build context
    context_parts = []

    for i, s in enumerate(similar[:3]):
        entry = s["entry"]

        context_parts.append(
            f"""
Similar Case {i+1}
Complaint: {entry['complaint_text'][:300]}
Resolution: {entry['resolution'][:300]}
Timeline: {entry.get('resolution_timeline_days', 'N/A')}
Regulatory Ref: {entry.get('regulatory_reference', 'N/A')}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
Incoming Complaint:
{complaint_text}

Similar Cases:
{context}

Suggest a resolution with timeline and regulatory reference.
Be professional and customer-friendly."""

    # Call LLM
    llm_response = _call_llm(prompt)

    top_similarity = similar[0]["similarity"]
    confidence = min(top_similarity * 1.2, 1.0)

    if llm_response:
        resolution_text = llm_response
        source = "AI_Generated"
    else:
        resolution_text = similar[0]["entry"]["resolution"]
        source = similar[0]["entry"].get("source", "CPGRAMS_Historical")

    # Translate back to user language
    if language != "en":
        try:
            resolution_text = translate_text(
                resolution_text,
                source_lang="en",
                target_lang=language,
            )
        except Exception as e:
            print(f"[Translation] Resolution translation failed: {e}")

    return {
        "suggested_resolution": resolution_text,
        "confidence": round(confidence, 3),
        "estimated_resolution_days": similar[0]["entry"].get(
            "resolution_timeline_days"
        ) or 7,
        "regulatory_reference": similar[0]["entry"].get(
            "regulatory_reference"
        ) or "RBI Guidelines",
        "similar_cases_count": len(
            [s for s in similar if s["similarity"] > 0.3]
        ),
        "source": source,
    }


# ─────────────────────────────────────────────
# PRELOAD
# ─────────────────────────────────────────────


def preload():
    """Preload resolution engine at startup."""
    print("[ResolutionAI] Preloading resolution engine...")

    try:
        kb_entries, kb_embeddings = _load_knowledge_base()
        
        if kb_entries:
            print(f"[ResolutionAI] Loaded {len(kb_entries)} KB entries")
        
        print("[ResolutionAI] Resolution engine ready.")
    except Exception as e:
        print(f"[ResolutionAI] WARNING: Preload failed: {e}")
        print("[ResolutionAI] Will use fallback resolution generation")