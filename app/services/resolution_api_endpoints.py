"""
Resolution API Endpoints
========================
Provides AI-powered resolution suggestions for complaints on the admin dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user

from app.models.complaint import Complaint
from app.models.user import User

from app.services.resolution_ai_service import generate_resolution

router = APIRouter()


# ---------------------------------------------------------
# GET AI RESOLUTION SUGGESTION
# ---------------------------------------------------------
@router.get("/complaints/{complaint_id}/ai-resolution")
def get_ai_resolution(
    complaint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if current_user.role.lower() not in ["admin", "regulator", "officer"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch complaint
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint_text = f"{complaint.title} {complaint.description}"

    # Generate resolution
    result = generate_resolution(
        complaint_text,
        category=complaint.category,
        language="auto"
    )

    # ---- STORE AI RESULT IN DATABASE ----
    complaint.ai_suggested_resolution = result["suggested_resolution"]
    complaint.ai_resolution_confidence = result["confidence"]
    complaint.estimated_resolution_days = result["estimated_resolution_days"]

    db.commit()
    db.refresh(complaint)

    return {
        "complaint_id": complaint.reference_id,
        "complaint_title": complaint.title,
        "ai_resolution": result,
    }


# ---------------------------------------------------------
# ADMIN APPROVES RESOLUTION
# ---------------------------------------------------------
@router.post("/complaints/{complaint_id}/approve-resolution")
def approve_resolution(
    complaint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin approves the AI-suggested resolution.
    After approval, response can be sent to citizen.
    """

    if current_user.role.lower() not in ["admin", "regulator", "officer"]:
        raise HTTPException(status_code=403, detail="Access denied")

    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if not complaint.ai_suggested_resolution:
        raise HTTPException(
            status_code=400,
            detail="No AI resolution available to approve",
        )

    # Approve resolution
    complaint.resolution_approved = True
    complaint.resolution_approved_by = str(current_user.id)
    complaint.status = "action_in_progress"  # Not resolved yet - bank needs to process
    complaint.resolution = complaint.ai_suggested_resolution

    db.commit()
    db.refresh(complaint)

    return {
        "message": "Resolution approved. Complaint status set to action in progress.",
        "reference_id": complaint.reference_id,
        "resolution": complaint.resolution,
        "status": complaint.status,
    }