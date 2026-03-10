from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.complaint import Complaint


def detect_systemic_risk(db: Session):

    # -------- TIME WINDOW --------
    time_window = datetime.utcnow() - timedelta(minutes=10)

    # -------- FETCH RECENT COMPLAINTS --------
    recent_complaints = db.query(Complaint).filter(
        Complaint.created_at >= time_window
    ).all()

    category_count = {}

    # -------- COUNT COMPLAINTS PER CATEGORY --------
    for complaint in recent_complaints:

        # Skip complaints that don't have a category
        if not complaint.category:
            continue

        category = complaint.category

        if category not in category_count:
            category_count[category] = 0

        category_count[category] += 1

    alerts = []

    # Minimum complaints required to trigger systemic alert
    threshold = 5

    # -------- DETECT SYSTEMIC PATTERNS --------
    for category, count in category_count.items():

        if count >= threshold:

            alerts.append({
                "category": category,
                "complaints": count,
                "time_window_minutes": 10,
                "risk": "Possible service outage or systemic issue"
            })

    return alerts