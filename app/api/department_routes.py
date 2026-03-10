from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.complaint import Complaint
from app.models.user import User
from app.schemas.complaint_schema import ComplaintResponse

router = APIRouter(prefix="/department", tags=["Department"])


# ---------------- GET COMPLAINTS BY DEPARTMENT ----------------
@router.get("/{department_name}/complaints", response_model=List[ComplaintResponse])
def get_department_complaints(
    department_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    complaints = db.query(Complaint).filter(
        Complaint.assigned_department == department_name
    ).all()

    return complaints