import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

import feedparser
import httpx

logger = logging.getLogger(__name__)

SIGNAL_PATTERNS = {
    "funding": [
        r"series [a-e]", r"raised", r"funding", r"investment", r"investor",
        r"venture capital", r"seed round", r"pre-[ipo|seed]", r"\$\d+\s*[mb]illion",
    ],
    "hiring": [
        r"hires?", r"appoints?", r"joins? as", r"welcomes?", r"names?.*as",
        r"head of", r"chief.*officer", r"vp of", r"director of",
    ],
    "launch": [
        r"launches?", r"announces?", r"releases?", r"unveils?", r"introduces?",
        r"debuts?", r"ships?", r"new product", r"new feature",
    ],
    "expansion": [
        r"opens?.*office", r"expands?", r"acquires?", r"acquisition", r"merger",
        r"new market", r"international", r"global expansion",
    ],
    "growth": [
        r"growth", r"revenue", r"customers?", r"users?", r"milestone",
        r"record", r"year-over-year", r"yoy",
    ],
}


def classify_signal(title: str, summary: str = "") -> str:
    text = f"{title} {summary}".lower()
    for signal_type, patterns in SIGNAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return signal_type
    return "news"


async def scrape_google_news(company_name: str) -> list[dict]:
    """
    Scrape Google News RSS for company mentions.
    Returns list of article dicts. NEVER raises an exception.
    """
    if not company_name:
        return []

    encoded = quote_plus(f'"{company_name}"')
    feed_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                feed_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; FeedFetcher/1.0)"},
            )
            feed_content = resp.text
    except Exception as e:
        logger.debug(f"News fetch failed for {company_name}: {e}")
        return []

    try:
        feed = feedparser.parse(feed_content)
    except Exception as e:
        logger.debug(f"Feed parse failed for {company_name}: {e}")
        return []

    articles = []
    for entry in feed.entries[:10]:
        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "")
        link = getattr(entry, "link", "")
        published = getattr(entry, "published", "")

        # Parse date
        date_str = published
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                from time import mktime
                dt = datetime.fromtimestamp(mktime(entry.published_parsed))
                date_str = dt.isoformat()
        except Exception:
            pass

        source = ""
        if hasattr(entry, "source") and hasattr(entry.source, "title"):
            source = entry.source.title

        signal_type = classify_signal(title, summary)

        articles.append({
            "title": title[:200],
            "url": link,
            "date": date_str,
            "signal_type": signal_type,
            "source": source,
            "summary": summary[:300] if summary else "",
        })

    return articles
