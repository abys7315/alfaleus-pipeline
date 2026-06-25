import re
from typing import List, Tuple, Optional


FUNDING_STAGES = {
    "pre-seed": 5,
    "pre seed": 5,
    "seed": 10,
    "seed round": 10,
    "series a": 25,
    "series b": 50,
    "series c": 80,
    "series d": 90,
    "series e": 95,
    "growth equity": 75,
    "late stage": 85,
    "pre-ipo": 90,
    "pre ipo": 90,
    "ipo": 95,
    "acquired": 100,
    "acquisition": 100,
    "bootstrapped": 0,
    "profitable": 0,
}

AMOUNT_PATTERN = r"\$\s?([\d.]+)\s?(million|billion|m|b)\b"
ROUND_PATTERN = r"(pre-?seed|seed\s*round|series\s+[a-e]|growth\s*equity|late\s*stage|pre-?ipo|ipo)\b"
RAISED_PATTERN = r"raised?\s+\$?([\d.]+)\s?(million|billion|m|b)"


def extract_funding_status(text: str, news_articles: list = None) -> Tuple[Optional[str], str]:
    """
    Extract funding status from text and news articles.
    Returns (funding_description, confidence).
    """
    all_text = text or ""
    if news_articles:
        for article in news_articles:
            if article.get("signal_type") == "funding":
                all_text += " " + article.get("title", "") + " " + article.get("summary", "")

    all_text_lower = all_text.lower()

    # Find round type
    round_match = re.search(ROUND_PATTERN, all_text_lower, re.IGNORECASE)
    round_type = None
    if round_match:
        round_type = round_match.group(0).strip().title()

    # Find amount
    amount_match = re.search(AMOUNT_PATTERN, all_text, re.IGNORECASE)
    raised_match = re.search(RAISED_PATTERN, all_text, re.IGNORECASE)
    amount_str = None

    match_to_use = amount_match or raised_match
    if match_to_use:
        num = match_to_use.group(1)
        unit = match_to_use.group(2).lower()
        if unit in ("b", "billion"):
            amount_str = f"${num}B"
        else:
            amount_str = f"${num}M"

    # Build description
    if round_type and amount_str:
        description = f"{round_type} ({amount_str})"
        confidence = "high"
    elif round_type:
        description = round_type
        confidence = "medium"
    elif amount_str:
        description = f"Raised {amount_str}"
        confidence = "medium"
    elif "bootstrapped" in all_text_lower or "profitable" in all_text_lower:
        description = "Bootstrapped / Profitable"
        confidence = "medium"
    elif "funding" in all_text_lower or "investor" in all_text_lower:
        description = "Has received funding (details unclear)"
        confidence = "low"
    else:
        description = None
        confidence = "low"

    return description, confidence


def get_funding_signal_strength(funding_description: Optional[str]) -> int:
    """Return buying signal strength for funding status (0-100)."""
    if not funding_description:
        return 0
    desc_lower = funding_description.lower()
    for stage, strength in FUNDING_STAGES.items():
        if stage in desc_lower:
            return strength
    if "raised" in desc_lower or "funding" in desc_lower:
        return 40
    return 0
