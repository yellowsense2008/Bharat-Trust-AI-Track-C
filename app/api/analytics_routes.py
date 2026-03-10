from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.complaint import Complaint

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ---------------- CLUSTER ANALYTICS ----------------
@router.get("/clusters")
def get_complaint_clusters(db: Session = Depends(get_db)):

    clusters = db.query(
        Complaint.category,
        Complaint.assigned_department,
        func.count(Complaint.id).label("complaint_count")
    ).group_by(
        Complaint.category,
        Complaint.assigned_department
    ).all()

    result = []

    for cluster in clusters:
        result.append({
            "category": cluster.category,
            "department": cluster.assigned_department,
            "complaint_count": cluster.complaint_count
        })

    return result

# ---------------- RECURRING ISSUE DETECTION ----------------
@router.get("/recurring-issues")
def get_recurring_issues(db: Session = Depends(get_db)):

    results = db.query(
        Complaint.category,
        Complaint.assigned_department,
        func.count(Complaint.id).label("complaint_count")
    ).group_by(
        Complaint.category,
        Complaint.assigned_department
    ).having(
        func.count(Complaint.id) > 1
    ).all()

    recurring = []

    for issue in results:
        recurring.append({
            "issue_category": issue.category,
            "department": issue.assigned_department,
            "complaint_count": issue.complaint_count,
            "status": "recurring"
        })

    return recurring

# ---------------- ADMIN DASHBOARD ----------------
@router.get("/dashboard")
def get_admin_dashboard(db: Session = Depends(get_db)):

    total_complaints = db.query(func.count(Complaint.id)).scalar()

    resolved_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.status == "closed"
    ).scalar()

    pending_complaints = db.query(func.count(Complaint.id)).filter(
        Complaint.status != "closed"
    ).scalar()

    top_category = db.query(
        Complaint.category,
        func.count(Complaint.id).label("count")
    ).group_by(
        Complaint.category
    ).order_by(
        func.count(Complaint.id).desc()
    ).first()

    department_load = db.query(
        Complaint.assigned_department,
        func.count(Complaint.id).label("count")
    ).group_by(
        Complaint.assigned_department
    ).all()

    return {
        "total_complaints": total_complaints,
        "resolved_complaints": resolved_complaints,
        "pending_complaints": pending_complaints,
        "top_category": top_category.category if top_category else None,
        "department_workload": [
            {
                "department": d.assigned_department,
                "complaints": d.count
            }
            for d in department_load
        ]
    }