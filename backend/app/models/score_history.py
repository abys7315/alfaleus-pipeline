import uuid
from datetime import datetime
from sqlalchemy import Column, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ScoreHistory(Base):
    __tablename__ = "score_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    icp_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    buying_signal_count = Column(Integer, default=0, nullable=False)

    # Full snapshot of enrichment data at time of scoring
    snapshot_data = Column(JSON, nullable=True, default=dict)

    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    lead = relationship("Lead", back_populates="score_history")
