import re
from typing import Optional, Tuple


SIZE_RANGES = [
    (1, 10, "1-10"),
    (11, 50, "11-50"),
    (51, 200, "51-200"),
    (201, 500, "201-500"),
    (501, 1000, "501-1000"),
    (1001, 5000, "1001-5000"),
    (5001, float("inf"), "5000+"),
]

EMPLOYEE_PATTERNS = [
    r"([\d,]+)\s+employees?",
    r"team\s+of\s+([\d,]+)",
    r"([\d,]+)\s+people\b",
    r"([\d,]+)\s+engineers?",
    r"([\d,]+)\s+staff",
    r"over\s+([\d,]+)\s+(?:employees|people|engineers)",
    r"more\s+than\s+([\d,]+)\s+(?:employees|people|engineers)",
    r"nearly\s+([\d,]+)\s+(?:employees|people)",
]

SIZE_LABEL_PATTERNS = {
    r"\bstartup\b": (1, 50),
    r"\bsmall\s+(?:business|company|team)\b": (1, 50),
    r"\bsmb\b": (10, 500),
    r"\bmid-?market\b": (100, 1000),
    r"\benterprise\b": (500, float("inf")),
    r"\bbootstrapped\b": (1, 100),
    r"\bboutique\b": (5, 100),
}


def _num_to_range(n: int) -> str:
    for lo, hi, label in SIZE_RANGES:
        if lo <= n <= hi:
            return label
    return "5000+"


def infer_company_size(
    text: str,
    employee_hints: list = None,
    job_count: int = 0,
) -> Tuple[Optional[str], str]:
    """
    Returns (size_range_str, confidence).
    confidence: 'high' | 'medium' | 'low'
    """
    if not text and not employee_hints and not job_count:
        return None, "low"

    combined_text = text or ""

    # Priority 1: explicit numeric hints from website scraper
    all_nums = list(employee_hints or [])

    # Priority 2: regex from text
    for pattern in EMPLOYEE_PATTERNS:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for m in matches:
            try:
                num = int(str(m).replace(",", ""))
                if 1 <= num <= 1_000_000:
                    all_nums.append(num)
            except (ValueError, TypeError):
                pass

    if all_nums:
        # Use median
        all_nums.sort()
        median_num = all_nums[len(all_nums) // 2]
        return _num_to_range(median_num), "high"

    # Priority 3: label-based inference from text
    text_lower = combined_text.lower()
    for pattern, (lo, hi) in SIZE_LABEL_PATTERNS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            mid = (lo + min(hi, 1000)) // 2
            return _num_to_range(mid), "medium"

    # Priority 4: infer from job count
    if job_count > 20:
        return "51-200", "low"
    elif job_count > 5:
        return "11-50", "low"
    elif job_count > 0:
        return "1-10", "low"

    return None, "low"


def parse_company_size_number(size_range: str) -> Optional[int]:
    """Convert '51-200' -> midpoint 125 for ICP numeric comparison."""
    if not size_range:
        return None
    nums = re.findall(r"\d+", size_range.replace(",", ""))
    if len(nums) == 2:
        return (int(nums[0]) + int(nums[1])) // 2
    elif len(nums) == 1:
        return int(nums[0])
    return None
