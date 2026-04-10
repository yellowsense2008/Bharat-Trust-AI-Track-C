from sqlalchemy.orm import Session
from app.models.complaint import Complaint


def get_complaint_status(db: Session, reference_id: str):

    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id
    ).first()

    if not complaint:
        return {
            "found": False,
            "message": "Complaint not found. Please check your reference number."
        }

    return {
        "found": True,
        "reference_id": complaint.reference_id,
        "status": complaint.status,
        "category": complaint.category,
        "department": complaint.assigned_department
    }