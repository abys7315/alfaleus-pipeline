import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ConfidenceLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Enrichment(Base):
    __tablename__ = "enrichments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Company size
    company_size = Column(String(100), nullable=True)
    company_size_confidence = Column(
        SAEnum(ConfidenceLevel, name="confidencelevel", create_type=True),
        nullable=True,
    )

    # Tech stack
    tech_stack = Column(JSON, nullable=True, default=list)
    tech_stack_confidence = Column(String(50), nullable=True)

    # Funding
    funding_status = Column(String(255), nullable=True)
    funding_confidence = Column(String(50), nullable=True)

    # Industry
    industry = Column(String(255), nullable=True)
    sub_industry = Column(String(255), nullable=True)
    industry_confidence = Column(String(50), nullable=True)

    # Contact info
    contact_role = Column(String(255), nullable=True)
    contact_seniority = Column(String(100), nullable=True)
    seniority_confidence = Column(String(50), nullable=True)

    # News and signals
    recent_news = Column(JSON, nullable=True, default=list)  # [{title, url, date, signal_type}]
    buying_signals = Column(JSON, nullable=True, default=list)  # [{signal, source, strength, detected_at}]

    # Source tracking
    enriched_sources = Column(JSON, nullable=True, default=dict)  # {website: success/failed/skipped, ...}

    # Raw scraped data
    raw_data = Column(JSON, nullable=True, default=dict)

    # Bonus: email candidates
    email_candidates = Column(JSON, nullable=True, default=list)  # [{email, confidence, verified}]

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    lead = relationship("Lead", back_populates="enrichment")
