from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.complaint import Complaint
from app.models.user import User
from app.schemas.complaint_schema import ComplaintCreate, ComplaintResponse

from app.services.ai_service import (
    categorize_complaint,
    detect_duplicate,
    assign_department,
    calculate_priority,
    translate_to_english
)

from app.services.response_service import generate_auto_response
from app.services.known_issue_service import detect_known_issue
from app.services.systemic_risk_service import detect_systemic_risk


router = APIRouter(prefix="/complaints", tags=["Complaints"])


# ---------------- GENERATE REFERENCE ID ----------------
def generate_reference_id(db: Session):
    current_year = datetime.utcnow().year
    prefix = f"GRV-{current_year}"

    count = db.query(Complaint).count() + 1
    return f"{prefix}-{str(count).zfill(4)}"


# ---------------- CREATE COMPLAINT ----------------
@router.post("/")
def create_complaint(
    complaint_data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    reference_id = generate_reference_id(db)

    new_complaint = Complaint(
        reference_id=reference_id,
        user_id=current_user.id,
        title=complaint_data.title,
        description=complaint_data.description,
        status="submitted"
    )

    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    # ---------------- COMBINE TEXT ----------------
    combined_text = f"{new_complaint.title} {new_complaint.description}"

    # ---------------- TRANSLATE TO ENGLISH ----------------
    translated_text = translate_to_english(combined_text)

    # ---------------- KNOWN ISSUE DETECTION ----------------
    known_issue = detect_known_issue(translated_text)

    if known_issue:
        return {
            "message": "Known issue detected",
            "auto_resolution": known_issue["message"],
            "category": known_issue["category"]
        }

    # ---------------- AI CATEGORISATION ----------------
    category, confidence = categorize_complaint(translated_text)

    new_complaint.category = category
    new_complaint.ai_confidence = confidence
    new_complaint.status = "categorized"

    # ---------------- ROUTE TO DEPARTMENT ----------------
    new_complaint.assigned_department = assign_department(category)

    # ---------------- PRIORITY SCORING ----------------
    priority = calculate_priority(translated_text, category)
    new_complaint.priority_score = priority

    db.commit()
    db.refresh(new_complaint)

    # ---------------- DUPLICATE DETECTION ----------------
    existing_complaints = db.query(Complaint).filter(
        Complaint.id != new_complaint.id
    ).all()

    existing_texts = [
        f"{c.title} {c.description}" for c in existing_complaints
    ]

    duplicate_index = detect_duplicate(translated_text, existing_texts)

    if duplicate_index is not None:

        duplicate_complaint = existing_complaints[duplicate_index]

        new_complaint.duplicate_of = duplicate_complaint.reference_id
        new_complaint.status = "clustered"

        db.commit()
        db.refresh(new_complaint)

    auto_response = generate_auto_response(new_complaint)

    return {
        "complaint": new_complaint,
        "auto_response": auto_response
    }


# ---------------- GET MY COMPLAINTS ----------------
@router.get("/my", response_model=List[ComplaintResponse])
def get_my_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    complaints = db.query(Complaint).filter(
        Complaint.user_id == current_user.id
    ).all()

    return complaints


# ---------------- GET ALL COMPLAINTS (ADMIN ONLY) ----------------
@router.get("/", response_model=List[ComplaintResponse])
def get_all_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    complaints = db.query(Complaint).all()

    return complaints


# ---------------- UPDATE COMPLAINT STATUS ----------------
@router.put("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: str,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = new_status

    db.commit()
    db.refresh(complaint)

    return {
        "message": "Status updated successfully",
        "reference_id": complaint.reference_id,
        "new_status": complaint.status
    }


# ---------------- FILTER COMPLAINTS ----------------
@router.get("/filter")
def filter_complaints(
    status: str = None,
    department: str = None,
    category: str = None,
    db: Session = Depends(get_db)
):

    query = db.query(Complaint)

    if status:
        query = query.filter(Complaint.status == status)

    if department:
        query = query.filter(Complaint.assigned_department == department)

    if category:
        query = query.filter(Complaint.category == category)

    return query.all()


# ---------------- COMPLAINT TIMELINE ----------------
@router.get("/timeline/{reference_id}")
def get_complaint_timeline(
    reference_id: str,
    db: Session = Depends(get_db)
):

    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    timeline = ["submitted", "categorized"]

    if complaint.duplicate_of:
        timeline.append("clustered")

    if complaint.status in ["assigned", "in_progress", "resolved", "closed"]:
        timeline.append("assigned")

    if complaint.status in ["in_progress", "resolved", "closed"]:
        timeline.append("in_progress")

    if complaint.status in ["resolved", "closed"]:
        timeline.append("resolved")

    if complaint.status == "closed":
        timeline.append("closed")

    return {
        "reference_id": complaint.reference_id,
        "current_status": complaint.status,
        "timeline": timeline
    }


# ---------------- SLA ESCALATION DETECTION ----------------
@router.get("/escalations")
def detect_escalations(db: Session = Depends(get_db)):

    complaints = db.query(Complaint).all()

    escalated = []

    for complaint in complaints:

        if complaint.status in ["resolved", "closed"]:
            continue

        if complaint.priority_score is None:
            continue

        created_time = complaint.created_at
        now = datetime.now(created_time.tzinfo)

        hours_passed = (now - created_time).total_seconds() / 3600

        if complaint.priority_score >= 9:
            expected_hours = 24
        elif complaint.priority_score >= 6:
            expected_hours = 48
        else:
            expected_hours = 72

        if hours_passed > expected_hours:

            escalated.append({
                "reference_id": complaint.reference_id,
                "department": complaint.assigned_department,
                "priority": complaint.priority_score,
                "hours_elapsed": round(hours_passed, 2),
                "sla_limit": expected_hours
            })

    return {
        "escalated_complaints": escalated,
        "count": len(escalated)
    }

@router.get("/systemic-risk")
def systemic_risk_detection(db: Session = Depends(get_db)):

    alerts = detect_systemic_risk(db)

    return {
        "alerts": alerts,
        "alert_count": len(alerts)
    }