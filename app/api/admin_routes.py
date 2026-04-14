"""
admin_routes.py
Admin-only endpoints for complaint management.

All routes require a valid JWT token whose payload carries role == "admin".
Attempting access with any other role returns HTTP 403.

Routes
------
GET  /admin/complaints                     List all complaints (newest first)
GET  /admin/complaints/{complaint_id}      Detailed single complaint
PATCH /admin/complaints/{complaint_id}     Update status / resolution / dept / priority
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.complaint import Complaint
from app.models.user import User
from app.schemas.complaint_schema import AdminComplaintUpdate, AdminComplaintDetail
from app.services.resolution_api_endpoints import router as resolution_router
from app.services.resolution_ai_service import generate_resolution as generate_resolution_for_complaint

router = APIRouter(prefix="/admin", tags=["Admin"])

router.include_router(resolution_router)

# ── Allowed status values ──────────────────────────────────────────────────────

VALID_STATUSES = {
    "FILED",
    "UNDER_REVIEW",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
}


# ── Admin guard helper ─────────────────────────────────────────────────────────

def _require_admin(current_user: User) -> None:
    """Raise 403 if the authenticated user is not an admin."""
    if str(current_user.role).lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


# ── GET /admin/complaints ─────────────────────────────────────────────────────

@router.get("/complaints", response_model=List[AdminComplaintDetail])
def list_all_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return every complaint in the system, ordered newest → oldest.

    Access: admin only.
    """
    _require_admin(current_user)

    complaints = (
        db.query(Complaint)
        .order_by(Complaint.created_at.desc())
        .all()
    )
    return complaints


# ── GET /admin/complaints/{complaint_id} ──────────────────────────────────────

@router.get("/complaints/{complaint_id}", response_model=AdminComplaintDetail)
def get_complaint_detail(
    complaint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single complaint with full detail including AI fields.

    Access: admin only.
    """
    _require_admin(current_user)

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint

@router.get("/complaints/{complaint_id}/resolution", response_model=dict)
def get_or_generate_resolution(
    complaint_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get resolution for complaint (auto-generates if not exists).
    
    Access: admin only.
    """
    _require_admin(current_user)
    
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # If already has resolution, return it
    if complaint.resolution:
        return {
            "resolution": complaint.resolution,
            "status": "existing"
        }
    
    # Auto-generate resolution
    try:
        resolution = generate_resolution_for_complaint(complaint)
        complaint.resolution = resolution
        complaint.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(complaint)
        
        return {
            "resolution": resolution,
            "status": "generated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate resolution: {str(e)}")

# ── PATCH /admin/complaints/{complaint_id} ────────────────────────────────────

@router.patch("/complaints/{complaint_id}", response_model=AdminComplaintDetail)
def update_complaint(
    complaint_id: UUID,
    payload: AdminComplaintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update a complaint.

    Updatable fields
    ----------------
    status              — must be one of FILED | UNDER_REVIEW | IN_PROGRESS | RESOLVED | CLOSED
    resolution          — free-text resolution note written by admin
    assigned_department — reassign to a different department
    priority_score      — integer 1-10

    Access: admin only.
    """
    _require_admin(current_user)

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # ── Validate and apply status ──────────────────────────────────────────────
    if payload.status is not None:
        normalised_status = payload.status.strip().upper()
        if normalised_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid status '{payload.status}'. "
                    f"Allowed values: {', '.join(sorted(VALID_STATUSES))}"
                ),
            )
        complaint.status = normalised_status

    # ── Apply remaining optional fields ───────────────────────────────────────
    if payload.resolution is not None:
        complaint.resolution = payload.resolution.strip()

    if payload.assigned_department is not None:
        complaint.assigned_department = payload.assigned_department.strip()

    if payload.priority_score is not None:
        if not (1 <= payload.priority_score <= 10):
            raise HTTPException(
                status_code=422,
                detail="priority_score must be between 1 and 10"
            )
        complaint.priority_score = payload.priority_score

    # ── Stamp updated_at explicitly (SQLAlchemy onupdate fires on flush) ───────
    complaint.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(complaint)

    return complaint


