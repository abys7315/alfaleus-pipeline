import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class ICPConfig(Base):
    __tablename__ = "icp_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, default="Default ICP")

    # Company size targeting
    company_size_min = Column(Integer, nullable=True, default=1)
    company_size_max = Column(Integer, nullable=True, default=10000)

    # Industry and tech
    target_industries = Column(JSON, nullable=True, default=list)     # ["SaaS", "FinTech"]
    required_tech_stack = Column(JSON, nullable=True, default=list)   # ["React", "AWS"]

    # Seniority
    min_seniority = Column(String(100), nullable=True, default="Manager")

    # Disqualifiers
    disqualifiers = Column(JSON, nullable=True, default=list)         # ["competitor", "non-profit"]

    # Scoring weights
    scoring_weights = Column(
        JSON,
        nullable=False,
        default=lambda: {"icp_fit": 0.6, "buying_signals": 0.4},
    )
    criterion_weights = Column(
        JSON,
        nullable=False,
        default=lambda: {
            "company_size": 25,
            "industry": 25,
            "tech_stack": 20,
            "seniority": 20,
            "disqualifier_penalty": 10,
        },
    )

    # Thresholds and descriptions
    score_threshold = Column(Integer, default=60, nullable=False)
    product_description = Column(Text, nullable=True, default="")
    value_proposition = Column(Text, nullable=True, default="")

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
