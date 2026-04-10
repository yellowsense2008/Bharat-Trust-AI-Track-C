# sklearn and numpy are imported lazily inside detect_duplicate()
# so this module adds zero cost to the container startup path.

# ---------------- TRANSLATION SUPPORT ----------------

from deep_translator import GoogleTranslator

def translate_to_english(text: str):

    if not text or len(text) < 3:
        return text

    try:
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return translated
    except Exception:
        return text


# ---------------- SIMPLE RULE-BASED CATEGORIZATION ----------------

def categorize_complaint(text: str):

    text_lower = text.lower()

    if "water" in text_lower:
        return "Utilities", 0.90
    elif "electricity" in text_lower:
        return "Utilities", 0.88
    elif "road" in text_lower:
        return "Infrastructure", 0.85
    elif "garbage" in text_lower:
        return "Sanitation", 0.87
    else:
        return "General", 0.70


# ---------------- LIGHTWEIGHT DUPLICATE DETECTION ----------------

def detect_duplicate(new_text: str, existing_texts: list, threshold: float = 0.25):
    # Deferred imports — sklearn takes ~500ms to import; only pay that cost
    # when this function is actually called, not at server startup.
    from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: PLC0415
    from sklearn.metrics.pairwise import cosine_similarity        # noqa: PLC0415
    import numpy as np                                             # noqa: PLC0415

    if not existing_texts:
        return None

    corpus = existing_texts + [new_text]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    similarity_matrix = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

    if similarity_matrix.size == 0:
        return None

    max_score = np.max(similarity_matrix)
    max_index = np.argmax(similarity_matrix)

    if max_score >= threshold:
        return max_index

    return None


# ---------------- DEPARTMENT ROUTING ----------------

def assign_department(category: str) -> str:

    department_map = {
        "Utilities": "Water Department",
        "Electricity": "Electricity Board",
        "Infrastructure": "Public Works Department",
        "Sanitation": "Municipal Sanitation Dept",
        "Transportation": "Traffic Department"
    }

    return department_map.get(category, "General Administration")


# ---------------- PRIORITY SCORING ----------------

def calculate_priority(text: str, category: str) -> int:

    text = text.lower()

    score = 3

    urgent_keywords = [
        "hospital",
        "emergency",
        "fire",
        "flood",
        "accident",
        "danger",
        "injury"
    ]

    medium_keywords = [
        "no water",
        "power outage",
        "electricity",
        "sewage",
        "water leak"
    ]

    for word in urgent_keywords:
        if word in text:
            score += 5

    for word in medium_keywords:
        if word in text:
            score += 2

    if category in ["Utilities", "Electricity"]:
        score += 1

    return min(score, 10)


# ---------------- MAIN AI PIPELINE ----------------

def process_complaint_text(text: str):

    # Translate complaint if user wrote in Hindi/Tamil/etc
    text = translate_to_english(text)

    category, confidence = categorize_complaint(text)

    department = assign_department(category)

    priority = calculate_priority(text, category)

    return category, confidence, department, priority