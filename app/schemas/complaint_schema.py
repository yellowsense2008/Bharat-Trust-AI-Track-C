from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

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