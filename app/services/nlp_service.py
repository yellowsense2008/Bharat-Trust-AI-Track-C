# sklearn imported lazily inside detect_duplicate_complaint() only.
from sqlalchemy.orm import Session
from app.models.complaint import Complaint


def detect_duplicate_complaint(db: Session, new_description: str):
    """
    Detect similar complaints using TF-IDF similarity.
    Returns reference_id if duplicate found.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: PLC0415
    from sklearn.metrics.pairwise import cosine_similarity        # noqa: PLC0415

    complaints = db.query(Complaint).all()

    if not complaints:
        return None

    descriptions = [c.description for c in complaints]
    reference_ids = [c.reference_id for c in complaints]

    descriptions.append(new_description)

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(descriptions)

    similarity_matrix = cosine_similarity(vectors)

    new_index = len(descriptions) - 1
    similarities = similarity_matrix[new_index][:-1]

    max_similarity = max(similarities)
    max_index = similarities.argmax()

    if max_similarity > 0.75:
        return reference_ids[max_index]

    return None