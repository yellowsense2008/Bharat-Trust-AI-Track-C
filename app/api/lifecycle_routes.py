from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.complaint import Complaint
from app.models.user import User

router = APIRouter(prefix="/lifecycle", tags=["Lifecycle"])


# ---------------- START WORK ----------------
@router.patch("/start/{reference_id}")
def start_complaint_work(
    reference_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = "in_progress"

    db.commit()
    db.refresh(complaint)

    return {
        "message": "Work started",
        "reference_id": reference_id,
        "status": complaint.status
    }


# ---------------- RESOLVE COMPLAINT ----------------
@router.patch("/resolve/{reference_id}")
def resolve_complaint(
    reference_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = "resolved"

    db.commit()
    db.refresh(complaint)

    return {
        "message": "Complaint resolved",
        "reference_id": reference_id,
        "status": complaint.status
    }


# ---------------- CLOSE COMPLAINT ----------------
@router.patch("/close/{reference_id}")
def close_complaint(
    reference_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    complaint = db.query(Complaint).filter(
        Complaint.reference_id == reference_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = "closed"

    db.commit()
    db.refresh(complaint)

    return {
        "message": "Complaint closed",
        "reference_id": reference_id,
        "status": complaint.status
    }