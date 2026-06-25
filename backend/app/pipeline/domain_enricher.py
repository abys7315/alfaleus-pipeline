"""
Domain-level lead discovery.
Bonus feature: given a company domain, discover individual leads from
the team/about page, press mentions, and LinkedIn company employee section.
"""
import logging
import re
from typing import List, Dict
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

TEAM_PAGE_PATHS = [
    "/team", "/about/team", "/company/team", "/people", "/leadership",
    "/about-us/team", "/about", "/our-team", "/company/about",
    "/management", "/founders", "/executives",
]

TITLE_KEYWORDS = [
    "CEO", "CTO", "COO", "CFO", "CPO", "CRO", "CMO",
    "VP", "Vice President", "Director", "Head of",
    "Founder", "Co-Founder", "Partner", "Principal",
    "Manager", "Lead", "Engineer", "Designer", "Analyst",
]

NAME_PATTERN = re.compile(
    r"\b([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,25})\b"
)


def _looks_like_name(text: str) -> bool:
    """Check if text looks like a person's name."""
    parts = text.strip().split()
    if len(parts) < 2 or len(parts) > 4:
        return False
    return all(p[0].isupper() and len(p) >= 2 for p in parts if p)


def _extract_title(context_text: str) -> str:
    """Try to extract a job title from surrounding text."""
    for kw in TITLE_KEYWORDS:
        match = re.search(rf"({re.escape(kw)}[^,\n\.]*)", context_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:100]
    return ""


def _name_to_linkedin_slug(name: str) -> str:
    """Convert 'John Smith' to 'john-smith' for LinkedIn URL guess."""
    return "-".join(name.lower().split())


async def discover_leads_from_domain(domain: str) -> List[Dict]:
    """
    Discover individual leads from a company domain.
    Returns list of {name, title, company, domain, linkedin_url_guess, source}
    """
    base_url = f"https://{domain}"
    discovered = {}  # name -> person dict (deduplicate by name)

    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True, verify=False) as client:
        # Try team/leadership pages
        for path in TEAM_PAGE_PATHS:
            url = f"{base_url}{path}"
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Strategy 1: Find structured team cards
                # Look for divs/articles with a name heading + title
                for container in soup.find_all(["div", "article", "li"], class_=re.compile(
                    r"team|person|member|leader|exec|bio|card", re.I
                )):
                    # Name: first h2/h3/h4/strong
                    name_tag = container.find(["h2", "h3", "h4", "strong", "b"])
                    if not name_tag:
                        continue
                    name = name_tag.get_text(strip=True)
                    if not _looks_like_name(name):
                        continue

                    # Title: next p or span
                    title = ""
                    for sibling in name_tag.find_next_siblings(["p", "span", "div"])[:3]:
                        t = sibling.get_text(strip=True)
                        if t and len(t) < 100 and not _looks_like_name(t):
                            title = t
                            break
                    if not title:
                        container_text = container.get_text(" ", strip=True)
                        title = _extract_title(container_text)

                    slug = _name_to_linkedin_slug(name)
                    if name not in discovered:
                        discovered[name] = {
                            "name": name,
                            "title": title,
                            "company": domain.split(".")[0].title(),
                            "domain": domain,
                            "linkedin_url_guess": f"https://www.linkedin.com/in/{slug}",
                            "source": f"team_page:{path}",
                        }

                # Strategy 2: Regex scan for name patterns in page text
                if len(discovered) < 3:
                    text = soup.get_text(" ")
                    for match in NAME_PATTERN.finditer(text):
                        name = f"{match.group(1)} {match.group(2)}"
                        if name in discovered:
                            continue
                        # Validate: get surrounding context for title
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 100)
                        context = text[start:end]
                        title = _extract_title(context)
                        if title:  # Only include if we found a title
                            slug = _name_to_linkedin_slug(name)
                            discovered[name] = {
                                "name": name,
                                "title": title,
                                "company": domain.split(".")[0].title(),
                                "domain": domain,
                                "linkedin_url_guess": f"https://www.linkedin.com/in/{slug}",
                                "source": f"page_text:{path}",
                            }

                if discovered:
                    break  # Found people, stop searching pages

            except Exception as e:
                logger.debug(f"Team page {url} failed: {e}")
                continue

        # Strategy 3: Google News press mentions that name individuals
        if len(discovered) < 3:
            try:
                from app.pipeline.scrapers.news import scrape_google_news
                articles = await scrape_google_news(domain.split(".")[0])
                for article in articles:
                    title_text = article.get("title", "")
                    for match in NAME_PATTERN.finditer(title_text):
                        name = f"{match.group(1)} {match.group(2)}"
                        if name in discovered or len(name.split()) < 2:
                            continue
                        job_title = _extract_title(title_text)
                        if job_title:
                            slug = _name_to_linkedin_slug(name)
                            discovered[name] = {
                                "name": name,
                                "title": job_title,
                                "company": domain.split(".")[0].title(),
                                "domain": domain,
                                "linkedin_url_guess": f"https://www.linkedin.com/in/{slug}",
                                "source": f"news:{article.get('source', 'google_news')}",
                            }
            except Exception as e:
                logger.debug(f"News discovery failed: {e}")

    return list(discovered.values())[:20]  # Cap at 20 leads per domain
