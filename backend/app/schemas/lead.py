from __future__ import annotations
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from app.models.lead import LeadStatus, LeadSource


class LeadCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    raw_csv_row: Optional[dict] = None
    source: LeadSource = LeadSource.csv


class LeadExtensionCreate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    url: Optional[str] = None
    linkedin_url: Optional[str] = None


class LeadDomainCreate(BaseModel):
    domain: str


class LeadListItem(BaseModel):
    id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    status: LeadStatus
    source: LeadSource
    icp_score: Optional[float] = None
    total_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    raw_csv_row: Optional[dict] = None
    status: LeadStatus
    source: LeadSource
    icp_score: Optional[float] = None
    total_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadDetail(BaseModel):
    id: UUID
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    raw_csv_row: Optional[dict] = None
    status: LeadStatus
    source: LeadSource
    icp_score: Optional[float] = None
    total_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    enrichment: Optional[Any] = None
    drafts: Optional[List[Any]] = []
    crm_syncs: Optional[List[Any]] = []

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    items: List[LeadListItem]
    total: int
    page: int
    page_size: int
    pages: int
