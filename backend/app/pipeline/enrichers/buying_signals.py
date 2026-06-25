from typing import List, Dict, Optional
from datetime import datetime, timezone


def detect_buying_signals(
    enrichment_data: dict,
    icp_config: dict,
) -> List[Dict]:
    """
    Detect buying signals from enriched data.
    Returns list of {signal, source, strength, category, detected_at}
    """
    signals = []
    now = datetime.now(timezone.utc).isoformat()

    # 1. Recent funding signal
    funding = enrichment_data.get("funding_status")
    if funding:
        from app.pipeline.enrichers.funding import get_funding_signal_strength
        strength = get_funding_signal_strength(funding)
        if strength > 20:
            signals.append({
                "signal": f"Recent funding: {funding}",
                "source": "website + news analysis",
                "strength": strength,
                "category": "recent_funding",
                "detected_at": now,
            })

    # 2. Hiring expansion signal
    job_count = enrichment_data.get("job_count", 0)
    news = enrichment_data.get("recent_news", [])
    hiring_news = [a for a in news if a.get("signal_type") == "hiring"]
    if job_count > 5 or hiring_news:
        strength = min(80, 40 + job_count * 2 + len(hiring_news) * 10)
        signal_text = f"Actively hiring ({job_count} open roles)" if job_count > 0 else "Recent leadership hire detected"
        if hiring_news:
            signal_text = hiring_news[0]["title"][:100]
        signals.append({
            "signal": signal_text,
            "source": "job listings + news",
            "strength": min(strength, 80),
            "category": "hiring_expansion",
            "detected_at": now,
        })

    # 3. Tech fit signal (tech stack matches ICP required tech)
    lead_tech = enrichment_data.get("tech_stack", []) or []
    required_tech = icp_config.get("required_tech_stack", []) or []
    if lead_tech and required_tech:
        from app.pipeline.enrichers.tech_stack import tech_overlap_score
        overlap = tech_overlap_score(lead_tech, required_tech)
        if overlap > 0.3:
            matched = [t for t in lead_tech if any(r.lower() in t.lower() or t.lower() in r.lower() for r in required_tech)]
            signals.append({
                "signal": f"Tech stack fit: {', '.join(matched[:3])} matches your target stack",
                "source": "website scraper",
                "strength": int(overlap * 100),
                "category": "tech_fit",
                "detected_at": now,
            })

    # 4. Growth/expansion news
    growth_news = [a for a in news if a.get("signal_type") in ("expansion", "growth", "launch")]
    if growth_news:
        latest = growth_news[0]
        signals.append({
            "signal": latest["title"][:120],
            "source": f"Google News ({latest.get('source', 'news')})",
            "strength": 55,
            "category": "growth_news",
            "detected_at": now,
        })

    # 5. Leadership hire (very strong signal for SaaS tools)
    leadership_keywords = ["cto", "cpo", "cro", "vp of sales", "vp of marketing",
                           "head of", "chief", "director of"]
    for article in news:
        title_lower = article.get("title", "").lower()
        if any(kw in title_lower for kw in leadership_keywords) and article.get("signal_type") == "hiring":
            signals.append({
                "signal": f"Leadership hire: {article['title'][:100]}",
                "source": f"Google News ({article.get('source', '')})",
                "strength": 75,
                "category": "leadership_hire",
                "detected_at": now,
            })
            break  # Only take one leadership hire signal

    # Sort by strength descending
    signals.sort(key=lambda x: x["strength"], reverse=True)
    return signals


def calculate_buying_signal_score(signals: List[Dict]) -> float:
    """Compute buying signal score 0-100 from list of signals."""
    if not signals:
        return 0.0
    total = sum(s["strength"] for s in signals)
    return min(100.0, total * 0.8)  # Diminishing returns
