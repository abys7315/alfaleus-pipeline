from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.draft import DraftTone


class DraftCreate(BaseModel):
    tone: DraftTone = DraftTone.direct
    subject: Optional[str] = None
    body: Optional[str] = None
    call_to_action: Optional[str] = None


class DraftResponse(BaseModel):
    id: UUID
    lead_id: UUID
    tone: DraftTone
    subject: Optional[str] = None
    body: Optional[str] = None
    call_to_action: Optional[str] = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class DraftGenerateRequest(BaseModel):
    tone: Optional[DraftTone] = None  # If None, generate both tones
    force_regenerate: bool = False
