import csv
import io
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.draft import Draft
from app.models.lead import Lead
from app.models.enrichment import Enrichment
from app.models.icp_config import ICPConfig
from app.models.sequence import Sequence

router = APIRouter()


@router.get("/{lead_id}")
async def get_drafts(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    drafts = (await db.execute(
        select(Draft).where(Draft.lead_id == lead_id)
    )).scalars().all()
    return [
        {
            "id": str(d.id), "tone": d.tone,
            "subject": d.subject, "body": d.body,
            "call_to_action": d.call_to_action,
            "generated_at": d.generated_at.isoformat(),
        }
        for d in drafts
    ]


@router.post("/{lead_id}/generate")
async def generate_drafts(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")

    enr = (await db.execute(
        select(Enrichment).where(Enrichment.lead_id == lead_id)
    )).scalar_one_or_none()
    if not enr:
        raise HTTPException(400, "Lead not yet enriched. Run enrichment first.")

    icp = (await db.execute(
        select(ICPConfig).where(ICPConfig.is_active == True)
    )).scalar_one_or_none()

    from app.llm.client import generate_email_draft
    from app.llm.prompts import build_direct_prompt, build_social_proof_prompt, validate_draft_specificity
    import json as _json
    from datetime import datetime, timezone

    lead_profile = {
        "name": lead.name, "company": lead.company, "domain": lead.domain,
        "role": enr.contact_role, "seniority": enr.contact_seniority,
        "industry": enr.industry, "tech_stack": enr.tech_stack or [],
        "funding_status": enr.funding_status,
        "buying_signals": enr.buying_signals or [],
        "recent_news": enr.recent_news or [],
        "company_size": enr.company_size,
    }
    product_desc = icp.product_description if icp else "our product"
    value_prop = icp.value_proposition if icp else "helping you grow"

    tones = [
        ("direct", build_direct_prompt(lead_profile, product_desc, value_prop)),
        ("social_proof", build_social_proof_prompt(lead_profile, product_desc, value_prop)),
    ]

    created_drafts = []
    for tone, prompt in tones:
        raw = await generate_email_draft(prompt)
        # Parse subject/body/cta from LLM output
        subject, body, cta = _parse_draft(raw, lead_profile)
        if not validate_draft_specificity(body, lead_profile):
            # Retry with stricter prompt
            raw = await generate_email_draft(prompt + "\nIMPORTANT: You MUST mention specific facts from the lead profile above.")
            subject, body, cta = _parse_draft(raw, lead_profile)

        # Delete existing draft of same tone
        existing = (await db.execute(
            select(Draft).where(Draft.lead_id == lead_id, Draft.tone == tone)
        )).scalar_one_or_none()
        if existing:
            await db.delete(existing)

        draft = Draft(
            lead_id=lead_id,
            tone=tone,
            subject=subject,
            body=body,
            call_to_action=cta,
        )
        db.add(draft)
        await db.flush()
        created_drafts.append(draft)

    await db.commit()
    return [
        {"id": str(d.id), "tone": d.tone, "subject": d.subject,
         "body": d.body, "call_to_action": d.call_to_action}
        for d in created_drafts
    ]


def _parse_draft(raw: str, profile: dict):
    """Parse LLM output into subject/body/cta."""
    lines = raw.strip().split("\n")
    subject = ""
    body_lines = []
    cta = ""
    in_body = False

    for line in lines:
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[-1].strip()
        elif line.lower().startswith("cta:") or line.lower().startswith("call to action:"):
            cta = line.split(":", 1)[-1].strip()
        elif subject and not cta:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    # Fallbacks
    if not subject:
        company = profile.get("company", "your company")
        subject = f"Quick question about {company}"
    if not body:
        body = raw.strip()
    if not cta:
        cta = "Would you be open to a 15-minute call this week?"

    return subject, body, cta


@router.post("/sequence/{lead_id}")
async def generate_sequence(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Bonus: Generate 3-step outreach sequence."""
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")

    enr = (await db.execute(
        select(Enrichment).where(Enrichment.lead_id == lead_id)
    )).scalar_one_or_none()

    icp = (await db.execute(
        select(ICPConfig).where(ICPConfig.is_active == True)
    )).scalar_one_or_none()

    from app.llm.client import generate_email_draft
    from app.llm.prompts import build_direct_prompt, build_social_proof_prompt

    lead_profile = {
        "name": lead.name, "company": lead.company,
        "role": enr.contact_role if enr else None,
        "industry": enr.industry if enr else None,
        "tech_stack": enr.tech_stack if enr else [],
        "buying_signals": enr.buying_signals if enr else [],
        "recent_news": enr.recent_news if enr else [],
    }
    product_desc = icp.product_description if icp else "our product"
    value_prop = icp.value_proposition if icp else ""

    steps_config = [
        {"step": 1, "delay_days": 0, "tone": "direct", "desc": "Initial outreach"},
        {"step": 2, "delay_days": 3, "tone": "consultative", "desc": "Follow-up with value add"},
        {"step": 3, "delay_days": 7, "tone": "social_proof", "desc": "Final bump with social proof"},
    ]

    steps = []
    for sc in steps_config:
        follow_note = ""
        if sc["step"] == 2:
            follow_note = "\nThis is a follow-up to your previous email. Reference that you haven't heard back yet, and add a new piece of value."
        elif sc["step"] == 3:
            follow_note = "\nThis is the final follow-up. Be brief, mention a relevant customer success story, and make it easy to say yes or no."

        prompt = build_direct_prompt(lead_profile, product_desc, value_prop) + follow_note
        raw = await generate_email_draft(prompt, max_tokens=400)
        subject, body, cta = _parse_draft(raw, lead_profile)
        steps.append({
            "step": sc["step"],
            "delay_days": sc["delay_days"],
            "tone": sc["tone"],
            "description": sc["desc"],
            "subject": subject,
            "body": body,
            "call_to_action": cta,
        })

    # Delete old sequence
    old = (await db.execute(select(Sequence).where(Sequence.lead_id == lead_id))).scalar_one_or_none()
    if old:
        await db.delete(old)

    seq = Sequence(lead_id=lead_id, name=f"Sequence for {lead.name or lead.company}", steps=steps)
    db.add(seq)
    await db.commit()
    await db.refresh(seq)

    return {"id": str(seq.id), "name": seq.name, "steps": seq.steps}


@router.get("/sequence/{lead_id}")
async def get_sequence(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    seq = (await db.execute(select(Sequence).where(Sequence.lead_id == lead_id))).scalar_one_or_none()
    if not seq:
        raise HTTPException(404, "No sequence found. Generate one first.")
    return {"id": str(seq.id), "name": seq.name, "steps": seq.steps}


@router.get("/sequence/{lead_id}/export")
async def export_sequence(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Export sequence as CSV importable into any email tool."""
    seq = (await db.execute(select(Sequence).where(Sequence.lead_id == lead_id))).scalar_one_or_none()
    if not seq:
        raise HTTPException(404, "No sequence found.")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["step", "delay_days", "tone", "subject", "body", "call_to_action"])
    writer.writeheader()
    for step in seq.steps:
        writer.writerow(step)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sequence_{lead_id}.csv"},
    )
