from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class ICPConfigCreate(BaseModel):
    name: str = "Default ICP"
    company_size_min: Optional[int] = 1
    company_size_max: Optional[int] = 10000
    target_industries: Optional[List[str]] = []
    required_tech_stack: Optional[List[str]] = []
    min_seniority: Optional[str] = "Manager"
    disqualifiers: Optional[List[str]] = []
    scoring_weights: Optional[Dict[str, float]] = {"icp_fit": 0.6, "buying_signals": 0.4}
    criterion_weights: Optional[Dict[str, int]] = {
        "company_size": 25,
        "industry": 25,
        "tech_stack": 20,
        "seniority": 20,
        "disqualifier_penalty": 10,
    }
    score_threshold: int = 60
    product_description: Optional[str] = ""
    value_proposition: Optional[str] = ""
    is_active: bool = True


class ICPConfigResponse(BaseModel):
    id: UUID
    name: str
    company_size_min: Optional[int] = None
    company_size_max: Optional[int] = None
    target_industries: Optional[List[str]] = []
    required_tech_stack: Optional[List[str]] = []
    min_seniority: Optional[str] = None
    disqualifiers: Optional[List[str]] = []
    scoring_weights: Optional[Dict[str, float]] = {}
    criterion_weights: Optional[Dict[str, int]] = {}
    score_threshold: int
    product_description: Optional[str] = None
    value_proposition: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CriterionScore(BaseModel):
    score: float
    weight: int
    matched: Optional[Any] = None


class ICPScoreBreakdown(BaseModel):
    icp_fit_score: float
    buying_signal_score: float
    total_score: float
    breakdown: Dict[str, Any]
    disqualified: bool = False
    qualified: bool = False


class ICPPreviewRequest(BaseModel):
    company: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    tech_stack: Optional[List[str]] = []
    contact_role: Optional[str] = None
    buying_signals: Optional[List[dict]] = []
    funding_status: Optional[str] = None
