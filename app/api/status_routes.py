from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.complaint import Complaint
from app.schemas.complaint_schema import ComplaintStatusResponse

router = APIRouter(prefix="/status", tags=["Complaint Status"])


@router.get("/{reference_id}", response_model=ComplaintStatusResponse)
def get_complaint_status(reference_id: str, db: Session = Depends(get_db)):
    """
    Public endpoint to check complaint status using reference ID.
    """

    complaint = (
        db.query(Complaint)
        .filter(Complaint.reference_id == reference_id)
        .first()
    )

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return ComplaintStatusResponse(
        reference_id=complaint.reference_id,
        status=complaint.status,
        category=complaint.category,
        department=complaint.assigned_department,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        resolution=complaint.resolution,
    )