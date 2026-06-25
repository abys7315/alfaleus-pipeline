"""
Semantic ICP Scorer using sentence-transformers.

Uses cosine similarity between embedded text representations — NOT keyword matching.
Example: "boutique software consultancy with 40 engineers" correctly matches
         "20 to 100 employees" because both describe a small tech team.
"""
import logging
import re
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Model loaded once at module level ──────────────────────────────────────────
_model = None


def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model all-MiniLM-L6-v2...")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Model loaded.")
        except Exception as e:
            logger.warning(f"Could not load sentence-transformers: {e}. Falling back to keyword scoring.")
            _model = None
    return _model


def _cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


def semantic_similarity(text1: str, text2: str, threshold: float = 0.0) -> float:
    """Compute cosine similarity between two text embeddings. Returns 0.0-1.0."""
    if not text1 or not text2:
        return 0.0
    model = get_model()
    if model is None:
        # Fallback: keyword overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / max(len(words1), len(words2))
    try:
        embeddings = model.encode([text1, text2], show_progress_bar=False)
        sim = _cosine_similarity(embeddings[0], embeddings[1])
        return max(0.0, sim - threshold)
    except Exception as e:
        logger.debug(f"Embedding error: {e}")
        return 0.0


# ── Criterion Scorers ──────────────────────────────────────────────────────────

def score_company_size(lead_size_text: Optional[str], icp_min: int, icp_max: int) -> float:
    """
    Score company size match. Returns 0.0-1.0.
    First tries numeric extraction, then semantic similarity as fallback.
    """
    if not lead_size_text:
        return 0.3  # Partial credit for unknown

    # Try numeric extraction first
    nums = re.findall(r"\d[\d,]*", lead_size_text.replace(",", ""))
    if nums:
        try:
            n = int(nums[0])
            if icp_min <= n <= icp_max:
                return 1.0
            elif n < icp_min:
                ratio = n / icp_min
                return max(0.0, ratio)
            else:
                ratio = icp_max / n
                return max(0.0, ratio)
        except ValueError:
            pass

    # Semantic fallback
    target_desc = f"company with {icp_min} to {icp_max} employees"
    sim = semantic_similarity(lead_size_text, target_desc)
    return min(1.0, sim * 1.3)  # Slight boost since semantic is harder


def score_industry(lead_industry: Optional[str], target_industries: list) -> float:
    """
    Score industry match using semantic similarity against all target industries.
    Returns 0.0-1.0 (best match across all targets).
    """
    if not target_industries:
        return 1.0  # No restriction = full score
    if not lead_industry:
        return 0.2  # Unknown industry = low score

    best = 0.0
    for target in target_industries:
        sim = semantic_similarity(lead_industry, target)
        best = max(best, sim)

    # Boost near-perfect matches
    if best > 0.85:
        return 1.0
    return min(1.0, best * 1.2)


def score_tech_stack(lead_tech: list, required_tech: list) -> float:
    """
    Score tech stack match using synonym-aware overlap + semantic similarity.
    Returns 0.0-1.0.
    """
    if not required_tech:
        return 1.0
    if not lead_tech:
        return 0.0

    from app.pipeline.enrichers.tech_stack import tech_overlap_score
    overlap = tech_overlap_score(lead_tech, required_tech)

    # Semantic bonus: embed full stacks as descriptions
    lead_desc = f"tech stack includes {', '.join(lead_tech[:10])}"
    req_desc = f"requires {', '.join(required_tech[:10])}"
    semantic_score = semantic_similarity(lead_desc, req_desc)

    return min(1.0, (overlap * 0.7) + (semantic_score * 0.3))


SENIORITY_RANK = {
    "intern": 0, "student": 0,
    "individual contributor": 1, "ic": 1, "engineer": 1, "analyst": 1, "associate": 1,
    "senior": 2, "staff": 2, "lead": 2,
    "manager": 3, "team lead": 3,
    "senior manager": 4, "senior lead": 4,
    "director": 5, "head of": 5,
    "senior director": 6, "principal": 6,
    "vp": 7, "vice president": 7,
    "svp": 8, "senior vp": 8, "senior vice president": 8,
    "evp": 9, "executive vp": 9,
    "c-level": 10, "ceo": 10, "cto": 10, "coo": 10, "cfo": 10, "cpo": 10,
    "cro": 10, "chief": 10, "founder": 10, "co-founder": 10,
}


def _get_seniority_rank(title: str) -> int:
    """Get numeric rank for a job title."""
    if not title:
        return 0
    title_lower = title.lower()
    best_rank = 0
    for keyword, rank in SENIORITY_RANK.items():
        if keyword in title_lower:
            best_rank = max(best_rank, rank)
    return best_rank


def score_seniority(contact_role: Optional[str], min_seniority: Optional[str]) -> float:
    """
    Score seniority match. Returns 0.0-1.0.
    Uses both rank-based and semantic comparison.
    """
    if not min_seniority:
        return 1.0
    if not contact_role:
        return 0.3

    # Rank-based scoring
    lead_rank = _get_seniority_rank(contact_role)
    required_rank = _get_seniority_rank(min_seniority)

    if lead_rank >= required_rank:
        rank_score = 1.0
    elif required_rank > 0:
        rank_score = lead_rank / required_rank
    else:
        rank_score = 1.0

    # Semantic scoring as secondary signal
    sim = semantic_similarity(
        f"{contact_role} is a leadership position",
        f"{min_seniority} or above in the company",
    )
    semantic_score = min(1.0, sim * 1.5)  # Amplify semantic signal

    # Weighted combination
    combined = (rank_score * 0.7) + (semantic_score * 0.3)
    return min(1.0, combined)


def check_disqualifiers(lead_data: dict, disqualifiers: list) -> bool:
    """
    Return True if any disqualifier semantically matches the lead.
    Uses threshold of 0.75 for a positive disqualification.
    """
    if not disqualifiers:
        return False

    lead_text = " ".join(filter(None, [
        lead_data.get("company", ""),
        lead_data.get("industry", ""),
        str(lead_data.get("tech_stack", "")),
        lead_data.get("contact_role", ""),
    ]))

    if not lead_text.strip():
        return False

    for disq in disqualifiers:
        sim = semantic_similarity(lead_text, disq)
        if sim > 0.75:
            return True
        # Also do exact keyword check
        if disq.lower() in lead_text.lower():
            return True

    return False


# ── Main Scoring Function ──────────────────────────────────────────────────────

def score_lead(enrichment: dict, icp_config: dict) -> dict:
    """
    Score a lead against the ICP config.

    Returns:
    {
        icp_fit_score: 0-100,
        buying_signal_score: 0-100,
        total_score: 0-100,
        breakdown: {
            company_size: {score, weight, matched},
            industry: {score, weight, matched},
            tech_stack: {score, weight, matched},
            seniority: {score, weight, matched},
            disqualified: bool,
        }
    }
    """
    cw = icp_config.get("criterion_weights", {})
    w_size = cw.get("company_size", 25)
    w_industry = cw.get("industry", 25)
    w_tech = cw.get("tech_stack", 20)
    w_seniority = cw.get("seniority", 20)
    w_disq_penalty = cw.get("disqualifier_penalty", 10)
    total_weight = w_size + w_industry + w_tech + w_seniority

    # Score each criterion
    size_score = score_company_size(
        enrichment.get("company_size"),
        icp_config.get("company_size_min", 10),
        icp_config.get("company_size_max", 500),
    )
    industry_score = score_industry(
        enrichment.get("industry"),
        icp_config.get("target_industries", []),
    )
    tech_score = score_tech_stack(
        enrichment.get("tech_stack") or [],
        icp_config.get("required_tech_stack") or [],
    )
    seniority_score = score_seniority(
        enrichment.get("contact_role") or enrichment.get("contact_seniority"),
        icp_config.get("min_seniority"),
    )
    disqualified = check_disqualifiers(enrichment, icp_config.get("disqualifiers") or [])

    # Weighted ICP fit score
    if total_weight > 0:
        icp_fit_raw = (
            (size_score * w_size) +
            (industry_score * w_industry) +
            (tech_score * w_tech) +
            (seniority_score * w_seniority)
        ) / total_weight
    else:
        icp_fit_raw = 0.5

    # Apply disqualifier penalty
    if disqualified:
        icp_fit_raw = max(0.0, icp_fit_raw - (w_disq_penalty / 100.0))

    icp_fit_score = round(icp_fit_raw * 100, 1)

    # Buying signal score
    from app.pipeline.enrichers.buying_signals import calculate_buying_signal_score
    signals = enrichment.get("buying_signals") or []
    buying_signal_score = round(calculate_buying_signal_score(signals), 1)

    # Combined total
    weights = icp_config.get("scoring_weights", {})
    w_fit = weights.get("icp_fit", 0.6)
    w_signals = weights.get("buying_signals", 0.4)
    total_score = round((icp_fit_score * w_fit) + (buying_signal_score * w_signals), 1)

    return {
        "icp_fit_score": icp_fit_score,
        "buying_signal_score": buying_signal_score,
        "total_score": total_score,
        "breakdown": {
            "company_size": {
                "score": round(size_score * 100, 1),
                "weight": w_size,
                "matched": size_score > 0.7,
            },
            "industry": {
                "score": round(industry_score * 100, 1),
                "weight": w_industry,
                "matched": industry_score > 0.7,
            },
            "tech_stack": {
                "score": round(tech_score * 100, 1),
                "weight": w_tech,
                "matched": tech_score > 0.5,
            },
            "seniority": {
                "score": round(seniority_score * 100, 1),
                "weight": w_seniority,
                "matched": seniority_score > 0.65,
            },
            "disqualified": disqualified,
        },
    }
