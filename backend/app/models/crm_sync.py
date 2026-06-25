import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CRMType(str, enum.Enum):
    notion = "notion"


class CRMSyncStatus(str, enum.Enum):
    synced = "synced"
    pending = "pending"
    failed = "failed"
    skipped_duplicate = "skipped_duplicate"


class CRMSync(Base):
    __tablename__ = "crm_syncs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    crm_type = Column(
        SAEnum(CRMType, name="crmtype", create_type=True),
        default=CRMType.notion,
        nullable=False,
    )
    status = Column(
        SAEnum(CRMSyncStatus, name="crmsyncstatus", create_type=True),
        default=CRMSyncStatus.pending,
        nullable=False,
    )
    crm_record_id = Column(String(512), nullable=True)
    synced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationship
    lead = relationship("Lead", back_populates="crm_syncs")
