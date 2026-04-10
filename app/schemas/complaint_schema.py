from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class ComplaintCreate(BaseModel):
    title: str
    description: str


class ComplaintResponse(BaseModel):
    id: UUID
    reference_id: str
    title: str
    description: str
    status: str
    category: str | None = None
    assigned_department: str | None = None
    priority_score: int | None = None
    ai_confidence: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Admin schemas ──────────────────────────────────────────────────────────────

class AdminComplaintUpdate(BaseModel):
    """
    Partial-update body for PATCH /admin/complaints/{id}.
    All fields are optional; only provided fields are applied.
    """
    status: Optional[str] = Field(
        default=None,
        description="One of: FILED, UNDER_REVIEW, IN_PROGRESS, RESOLVED, CLOSED",
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Admin resolution note (free text).",
    )
    assigned_department: Optional[str] = Field(
        default=None,
        description="Reassign to a different department.",
    )
    priority_score: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Priority score 1 (lowest) – 10 (highest).",
    )


class AdminComplaintDetail(BaseModel):
    """
    Full complaint detail returned by admin GET / PATCH endpoints.
    Includes AI enrichment fields, resolution note, and timestamps.
    """
    id: UUID
    reference_id: str
    user_id: UUID
    title: str
    description: str
    status: str

    # AI enrichment
    category: Optional[str] = None
    assigned_department: Optional[str] = None
    priority_score: Optional[int] = None
    ai_confidence: Optional[float] = None
    duplicate_of: Optional[str] = None

    # Admin resolution
    resolution: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 

# ── Public status check schema ────────────────────────────────────────────────

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ComplaintStatusResponse(BaseModel):
    reference_id: str
    status: str
    category: Optional[str]
    department: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolution: Optional[str]