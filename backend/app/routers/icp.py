from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.icp_config import ICPConfig

router = APIRouter()


@router.get("")
async def get_icp(db: AsyncSession = Depends(get_db)):
    config = (await db.execute(
        select(ICPConfig).where(ICPConfig.is_active == True).order_by(ICPConfig.created_at.desc())
    )).scalar_one_or_none()
    if not config:
        return None
    return _serialize(config)


@router.post("")
async def save_icp(payload: dict, db: AsyncSession = Depends(get_db)):
    # Deactivate existing
    existing = (await db.execute(
        select(ICPConfig).where(ICPConfig.is_active == True)
    )).scalars().all()
    for e in existing:
        e.is_active = False

    config = ICPConfig(
        name=payload.get("name", "My ICP"),
        company_size_min=payload.get("company_size_min", 10),
        company_size_max=payload.get("company_size_max", 500),
        target_industries=payload.get("target_industries", []),
        required_tech_stack=payload.get("required_tech_stack", []),
        min_seniority=payload.get("min_seniority", "Manager"),
        disqualifiers=payload.get("disqualifiers", []),
        scoring_weights=payload.get("scoring_weights", {"icp_fit": 0.6, "buying_signals": 0.4}),
        criterion_weights=payload.get("criterion_weights", {
            "company_size": 25, "industry": 25, "tech_stack": 20, "seniority": 20, "disqualifier_penalty": 10
        }),
        score_threshold=payload.get("score_threshold", 60),
        product_description=payload.get("product_description", ""),
        value_proposition=payload.get("value_proposition", ""),
        is_active=True,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return _serialize(config)


@router.post("/preview")
async def preview_icp(payload: dict, db: AsyncSession = Depends(get_db)):
    """Score a sample lead dict against active ICP config."""
    icp = (await db.execute(
        select(ICPConfig).where(ICPConfig.is_active == True)
    )).scalar_one_or_none()
    if not icp:
        raise HTTPException(400, "No active ICP config. Please configure your ICP first.")

    sample = payload.get("sample_lead", {})
    from app.pipeline.icp_scorer import score_lead
    result = score_lead(sample, _serialize(icp))
    return result


def _serialize(config: ICPConfig) -> dict:
    return {
        "id": str(config.id),
        "name": config.name,
        "company_size_min": config.company_size_min,
        "company_size_max": config.company_size_max,
        "target_industries": config.target_industries,
        "required_tech_stack": config.required_tech_stack,
        "min_seniority": config.min_seniority,
        "disqualifiers": config.disqualifiers,
        "scoring_weights": config.scoring_weights,
        "criterion_weights": config.criterion_weights,
        "score_threshold": config.score_threshold,
        "product_description": config.product_description,
        "value_proposition": config.value_proposition,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat(),
    }
