"""
citizen_routes.py
Public endpoints for citizens to check complaint status and resolution.
No authentication required - uses reference_id for access.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.complaint import Complaint
from app.services.citizen_response_service import simplify_resolution


router = APIRouter(prefix="/complaints", tags=["Citizen"])


# ── Response Schema ───────────────────────────────────────────────────────────

class CitizenResolutionResponse(BaseModel):
    reference_id: str
    resolution: str
    status: str


# ── GET RESOLUTION ────────────────────────────────────────────────────────────

@router.get("/{reference_id}/resolution", response_model=CitizenResolutionResponse)
def get_complaint_resolution(
    reference_id: str,
    db: Session = Depends(get_db),
):
    """
    Public endpoint for citizens to retrieve their complaint resolution.
    
    Access: Public (no authentication required)
    
    Returns only:
    - reference_id
    - resolution text
    - status
    
    Does NOT return AI metadata (confidence, regulatory refs, etc.)
    """
    
    complaint = (
        db.query(Complaint)
        .filter(Complaint.reference_id == reference_id)
        .first()
    )
    
    if not complaint:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found. Please check your reference ID."
        )
    
    # Check if resolution is approved
    if not complaint.resolution_approved:
        return CitizenResolutionResponse(
            reference_id=complaint.reference_id,
            resolution="Your complaint is still under review.",
            status=complaint.status
        )
    
    # Check if resolution exists
    if not complaint.ai_suggested_resolution:
        return CitizenResolutionResponse(
            reference_id=complaint.reference_id,
            resolution="Your complaint is still under review.",
            status=complaint.status
        )
    
    # Simplify resolution for citizen
    simplified = simplify_resolution(complaint.ai_suggested_resolution)
    
    return CitizenResolutionResponse(
        reference_id=complaint.reference_id,
        resolution=simplified,
        status=complaint.status
    )
