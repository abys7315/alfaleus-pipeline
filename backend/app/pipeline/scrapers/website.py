import asyncio
import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

COMMON_PAGES = ["/", "/about", "/about-us", "/team", "/company", "/pricing", "/careers", "/jobs"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

TECH_KEYWORDS = [
    "React", "Vue", "Angular", "Next.js", "Nuxt", "Svelte",
    "Node.js", "Express", "Django", "Flask", "FastAPI", "Rails", "Laravel",
    "Python", "Ruby", "Java", "Go", "Rust", "TypeScript", "JavaScript",
    "AWS", "GCP", "Azure", "Kubernetes", "Docker", "Terraform",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Snowflake",
    "Salesforce", "HubSpot", "Stripe", "Twilio", "Slack", "Notion", "Airtable",
    "Figma", "GitHub", "GitLab", "Jira", "Confluence", "Linear",
    "Datadog", "Sentry", "Mixpanel", "Segment", "Amplitude",
]

FUNDING_PATTERNS = [
    r"series\s+[a-e]\b", r"seed\s+round", r"raised\s+\$[\d.]+\s*[mb]",
    r"\$[\d.]+\s*(million|billion|m|b)\s+funding",
    r"pre-?[ipo|series]", r"acquired\s+by", r"ipo",
    r"funding\s+round", r"venture\s+capital", r"bootstrapped",
]

EMPLOYEE_PATTERNS = [
    r"(\d[\d,]+)\s+employees?",
    r"team\s+of\s+(\d[\d,]+)",
    r"(\d[\d,]+)\s+people",
    r"(\d[\d,]+)\s+engineers?",
    r"over\s+(\d[\d,]+)\s+",
    r"more\s+than\s+(\d[\d,]+)\s+",
]


async def scrape_company_website(domain: str) -> dict:
    """
    Scrape the company website for enrichment data.
    Returns a dict with all findings; NEVER raises an exception.
    """
    if not domain:
        return {"error": "no domain provided", "pages_scraped": 0}

    base_url = f"https://{domain}"
    result = {
        "domain": domain,
        "pages_scraped": 0,
        "raw_text": "",
        "tech_hints": [],
        "employee_hints": [],
        "funding_hints": [],
        "job_count": 0,
        "meta_description": "",
        "error": None,
    }

    scraped_text_parts = []
    tech_found = set()

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=15,
        follow_redirects=True,
        verify=False,
    ) as client:
        for path in COMMON_PAGES:
            url = f"{base_url}{path}"
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Extract meta description from homepage
                if path == "/" and not result["meta_description"]:
                    meta = soup.find("meta", attrs={"name": "description"})
                    if meta:
                        result["meta_description"] = meta.get("content", "")[:500]

                # Gather page text
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                text = soup.get_text(separator=" ", strip=True)[:3000]
                scraped_text_parts.append(text)
                result["pages_scraped"] += 1

                # Tech hints from script src / link href
                for script in soup.find_all("script", src=True):
                    src = script.get("src", "")
                    for tech in TECH_KEYWORDS:
                        if tech.lower() in src.lower():
                            tech_found.add(tech)

                # Tech hints from page text and job listings
                full_page_text = text.lower()
                for tech in TECH_KEYWORDS:
                    if tech.lower() in full_page_text:
                        tech_found.add(tech)

                # Count job listings
                if path in ("/careers", "/jobs"):
                    job_items = soup.find_all(["li", "div", "article"], class_=re.compile(r"job|position|role|opening", re.I))
                    result["job_count"] = max(result["job_count"], len(job_items))

            except Exception as e:
                logger.debug(f"Failed to scrape {url}: {e}")
                continue

    full_text = " ".join(scraped_text_parts)
    result["raw_text"] = full_text[:5000]

    # Extract employee hints
    for pattern in EMPLOYEE_PATTERNS:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        for m in matches:
            num_str = m.replace(",", "")
            try:
                num = int(num_str)
                if 1 <= num <= 1_000_000:
                    result["employee_hints"].append(num)
            except ValueError:
                pass

    # Extract funding hints
    for pattern in FUNDING_PATTERNS:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        result["funding_hints"].extend(matches)

    result["tech_hints"] = list(tech_found)

    if result["pages_scraped"] == 0:
        result["error"] = "Could not reach any page on the domain"

    return result
