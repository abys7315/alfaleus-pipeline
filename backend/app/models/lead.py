import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class LeadStatus(str, enum.Enum):
    pending = "pending"
    enriching = "enriching"
    enriched = "enriched"
    failed = "failed"


class LeadSource(str, enum.Enum):
    csv = "csv"
    extension = "extension"
    domain = "domain"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    company = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True, index=True)
    linkedin_url = Column(String(512), nullable=True)
    raw_csv_row = Column(JSON, nullable=True)
    status = Column(
        SAEnum(LeadStatus, name="leadstatus", create_type=True),
        default=LeadStatus.pending,
        nullable=False,
        index=True,
    )
    source = Column(
        SAEnum(LeadSource, name="leadsource", create_type=True),
        default=LeadSource.csv,
        nullable=False,
    )
    icp_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    icp_score_breakdown = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    enrichment = relationship("Enrichment", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="lead", cascade="all, delete-orphan")
    sequences = relationship("Sequence", back_populates="lead", cascade="all, delete-orphan")
    score_history = relationship("ScoreHistory", back_populates="lead", cascade="all, delete-orphan")
    crm_syncs = relationship("CRMSync", back_populates="lead", cascade="all, delete-orphan")
