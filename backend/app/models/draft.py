import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class DraftTone(str, enum.Enum):
    direct = "direct"
    social_proof = "social_proof"


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    tone = Column(
        SAEnum(DraftTone, name="drafttone", create_type=True),
        nullable=False,
        default=DraftTone.direct,
    )
    subject = Column(String(512), nullable=True)
    body = Column(Text, nullable=True)
    call_to_action = Column(String(512), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    lead = relationship("Lead", back_populates="drafts")
