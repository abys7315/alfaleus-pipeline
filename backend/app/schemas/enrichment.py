from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class BuyingSignal(BaseModel):
    signal: str
    source: str
    strength: int
    category: Optional[str] = None
    detected_at: Optional[str] = None

    model_config = {"from_attributes": True}


class NewsItem(BaseModel):
    title: str
    url: Optional[str] = None
    date: Optional[str] = None
    signal_type: Optional[str] = None
    source: Optional[str] = None


class EmailCandidate(BaseModel):
    email: str
    confidence: Optional[str] = None
    verified: Optional[bool] = None
    pattern: Optional[str] = None
    mx_verified: Optional[bool] = None


class EnrichedField(BaseModel):
    value: Optional[Any] = None
    confidence: Optional[str] = None


class EnrichmentResponse(BaseModel):
    id: UUID
    lead_id: UUID
    company_size: Optional[str] = None
    company_size_confidence: Optional[str] = None
    tech_stack: Optional[List[str]] = []
    tech_stack_confidence: Optional[str] = None
    funding_status: Optional[str] = None
    funding_confidence: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    industry_confidence: Optional[str] = None
    contact_role: Optional[str] = None
    contact_seniority: Optional[str] = None
    seniority_confidence: Optional[str] = None
    recent_news: Optional[List[NewsItem]] = []
    buying_signals: Optional[List[BuyingSignal]] = []
    enriched_sources: Optional[dict] = {}
    email_candidates: Optional[List[EmailCandidate]] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnrichmentStatusResponse(BaseModel):
    lead_id: str
    status: str
    stages: Optional[dict] = {}
    message: Optional[str] = None
