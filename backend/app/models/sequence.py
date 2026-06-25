import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Sequence(Base):
    __tablename__ = "sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, default="Outreach Sequence")

    # steps: [{step: 1, delay_days: 0, subject, body, tone}, ...]
    steps = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    lead = relationship("Lead", back_populates="sequences")
