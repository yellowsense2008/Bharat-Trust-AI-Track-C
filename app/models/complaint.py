import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    reference_id = Column(String, unique=True, index=True, nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    # Lifecycle
    status = Column(String, default="submitted")  # submitted → categorized → assigned → in_progress → resolved → closed

    # -------- AI ENRICHMENT FIELDS --------
    category = Column(String, nullable=True)
    priority_score = Column(Integer, nullable=True)
    assigned_department = Column(String, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    duplicate_of = Column(String, nullable=True)

    # -------- ADMIN RESOLUTION --------
    resolution = Column(Text, nullable=True)  # Free-text note written by admin

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())