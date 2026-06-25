"""
Email finder: generates permutations and verifies MX records.
Bonus feature — no paid APIs used.
"""
import asyncio
import logging
import re
from typing import List, Dict, Optional

import dns.resolver
import dns.asyncresolver

logger = logging.getLogger(__name__)

COMMON_PATTERNS = [
    "{first}.{last}@{domain}",
    "{first}@{domain}",
    "{f}{last}@{domain}",
    "{first}{last}@{domain}",
    "{last}@{domain}",
    "{first}.{l}@{domain}",
    "{f}.{last}@{domain}",
    "{first}_{last}@{domain}",
]

PATTERN_CONFIDENCE = {
    "{first}.{last}@{domain}": "high",
    "{first}@{domain}": "high",
    "{f}{last}@{domain}": "medium",
    "{first}{last}@{domain}": "medium",
    "{last}@{domain}": "medium",
    "{first}.{l}@{domain}": "low",
    "{f}.{last}@{domain}": "low",
    "{first}_{last}@{domain}": "low",
}


def _parse_name(full_name: str) -> Dict[str, str]:
    """Split name into parts for pattern substitution."""
    parts = full_name.strip().lower().split()
    if len(parts) >= 2:
        first = parts[0]
        last = parts[-1]
    elif len(parts) == 1:
        first = parts[0]
        last = parts[0]
    else:
        return {}
    return {
        "first": re.sub(r"[^a-z]", "", first),
        "last": re.sub(r"[^a-z]", "", last),
        "f": re.sub(r"[^a-z]", "", first)[:1],
        "l": re.sub(r"[^a-z]", "", last)[:1],
    }


async def verify_mx_record(domain: str) -> bool:
    """Check if domain has valid MX records."""
    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 5
        answers = await resolver.resolve(domain, "MX")
        return len(answers) > 0
    except Exception:
        return False


async def find_email_candidates(
    name: Optional[str],
    domain: Optional[str],
) -> List[Dict]:
    """
    Generate email permutations and verify MX record.
    Returns [{email, pattern, confidence, mx_verified}]
    """
    if not name or not domain:
        return []

    parts = _parse_name(name)
    if not parts or not parts.get("first") or not parts.get("last"):
        return []

    clean_domain = domain.lower().strip().lstrip("www.")
    if not clean_domain or "." not in clean_domain:
        return []

    # Verify MX record once
    mx_ok = await verify_mx_record(clean_domain)

    candidates = []
    seen = set()
    for pattern in COMMON_PATTERNS:
        try:
            email = pattern.format(domain=clean_domain, **parts)
        except KeyError:
            continue

        if email in seen:
            continue
        seen.add(email)

        raw_confidence = PATTERN_CONFIDENCE.get(pattern, "low")

        # Upgrade confidence if MX verified + common pattern
        if mx_ok and raw_confidence == "high":
            final_confidence = "high"
        elif mx_ok:
            final_confidence = "medium"
        else:
            final_confidence = "low"

        candidates.append({
            "email": email,
            "pattern": pattern,
            "confidence": final_confidence,
            "mx_verified": mx_ok,
        })

    return candidates
