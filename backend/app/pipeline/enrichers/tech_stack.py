import re
from typing import List, Tuple

TECH_KEYWORDS = [
    "React", "ReactJS", "Vue", "Vue.js", "Angular", "Next.js", "Nuxt.js", "Svelte", "Ember",
    "Node.js", "NodeJS", "Express", "Django", "Flask", "FastAPI", "Ruby on Rails", "Laravel",
    "Spring Boot", "ASP.NET", ".NET", "Golang", "Go", "Rust", "Kotlin", "Swift",
    "Python", "Ruby", "Java", "TypeScript", "JavaScript", "PHP", "Scala", "Elixir",
    "AWS", "Amazon Web Services", "GCP", "Google Cloud", "Azure", "Microsoft Azure",
    "Kubernetes", "K8s", "Docker", "Terraform", "Ansible", "Helm", "ArgoCD",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "Snowflake", "BigQuery", "Redshift", "dbt", "Databricks", "Spark",
    "Salesforce", "HubSpot", "Marketo", "Pardot", "Stripe", "Twilio",
    "Slack", "Notion", "Airtable", "Figma", "Sketch", "Linear", "Jira",
    "GitHub", "GitLab", "Bitbucket", "CircleCI", "GitHub Actions",
    "Datadog", "Sentry", "New Relic", "PagerDuty", "Grafana",
    "Mixpanel", "Segment", "Amplitude", "Heap", "Intercom",
    "OpenAI", "LangChain", "Pinecone", "Weaviate", "PyTorch", "TensorFlow",
]

# Normalize synonyms
SYNONYMS = {
    "reactjs": "React", "react.js": "React",
    "vuejs": "Vue", "vue.js": "Vue",
    "nodejs": "Node.js", "node js": "Node.js",
    "k8s": "Kubernetes",
    "aws": "AWS", "amazon web services": "AWS",
    "gcp": "GCP", "google cloud": "GCP",
    "azure": "Azure", "microsoft azure": "Azure",
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
    "mongo": "MongoDB", "mongodb": "MongoDB",
    "elastic": "Elasticsearch",
    "rails": "Ruby on Rails",
    "ror": "Ruby on Rails",
    ".net": ".NET", "asp.net": ".NET",
    "golang": "Go",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
}


def extract_tech_stack(html_content: str, job_text: str = "") -> Tuple[List[str], str]:
    """
    Extract tech stack from HTML source and job listings.
    Returns (tech_list, confidence).
    confidence: 'high' if from HTML source/meta, 'medium' if from job text, 'low' if minimal
    """
    found = set()
    html_found = set()
    job_found = set()

    combined_lower = html_content.lower()
    job_lower = job_text.lower()

    for tech in TECH_KEYWORDS:
        tech_lower = tech.lower()
        # Check HTML source (higher confidence)
        if tech_lower in combined_lower:
            # Check if it's in a script src, link href, or data attribute (very high signal)
            if re.search(rf"src=[\"'][^\"']*{re.escape(tech_lower)}[^\"']*[\"']", combined_lower):
                html_found.add(tech)
            elif tech_lower in combined_lower:
                html_found.add(tech)

        # Check job listings
        if tech_lower in job_lower:
            job_found.add(tech)

    # Check synonyms
    for synonym, canonical in SYNONYMS.items():
        if synonym in combined_lower:
            html_found.add(canonical)
        if synonym in job_lower:
            job_found.add(canonical)

    found = html_found | job_found
    tech_list = sorted(found)[:20]  # Cap at 20

    if not tech_list:
        return [], "low"
    if html_found:
        confidence = "high"
    else:
        confidence = "medium"

    return tech_list, confidence


def tech_overlap_score(lead_tech: List[str], required_tech: List[str]) -> float:
    """
    Compute overlap ratio between lead's tech stack and ICP required tech.
    Allows synonyms.
    Returns 0.0-1.0
    """
    if not required_tech:
        return 1.0
    if not lead_tech:
        return 0.0

    lead_normalized = {t.lower() for t in lead_tech}
    # Add synonyms
    lead_expanded = set(lead_normalized)
    for syn, canonical in SYNONYMS.items():
        if canonical.lower() in lead_normalized:
            lead_expanded.add(syn)
        if syn in lead_normalized:
            lead_expanded.add(canonical.lower())

    matched = 0
    for req in required_tech:
        req_lower = req.lower()
        canonical = SYNONYMS.get(req_lower, req_lower)
        if req_lower in lead_expanded or canonical in lead_expanded:
            matched += 1

    return matched / len(required_tech)
