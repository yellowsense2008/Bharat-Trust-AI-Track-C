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

from app.services.translation_service import translate_text
from app.services.language_detector import detect_language
from app.services.embedding_service import get_embedding

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_PATH = BASE_DIR / "data" / "resolution_knowledge_base.json"
EMBEDDINGS_CACHE_PATH = BASE_DIR / "data" / "kb_embeddings.npy"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = "llama-3.3-70b-versatile"

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

    raise RuntimeError("KB embeddings file not found. Run embedding script first.")


# ─────────────────────────────────────────────
# SIMILARITY SEARCH
# ─────────────────────────────────────────────


def find_similar_complaints(complaint_text: str, top_k: int = 5):

    global _faiss_index

    kb_entries, kb_embeddings = _load_knowledge_base()

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
# LLM CALL
# ─────────────────────────────────────────────


def _call_llm(prompt: str):

    try:

        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI resolution assistant for RBI financial complaint handling. "
                        "Suggest resolutions grounded in past complaints and RBI regulations."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

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

    if not similar or similar[0]["similarity"] < 0.15:

        return {
            "suggested_resolution": "No similar complaints found. Manual review recommended.",
            "confidence": 0.0,
            "estimated_resolution_days": None,
            "regulatory_reference": None,
            "similar_cases_count": 0,
            "source": "No_Match",
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
"""

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
        ),
        "regulatory_reference": similar[0]["entry"].get(
            "regulatory_reference"
        ),
        "similar_cases_count": len(
            [s for s in similar if s["similarity"] > 0.3]
        ),
        "source": source,
    }


# ─────────────────────────────────────────────
# PRELOAD
# ─────────────────────────────────────────────


def preload():

    print("[ResolutionAI] Preloading resolution engine...")

    _load_knowledge_base()

    print("[ResolutionAI] Resolution engine ready.")