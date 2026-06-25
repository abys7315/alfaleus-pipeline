"""
Prompt templates for TinyLlama email draft generation.
Enforces lead-specific facts to prevent generic output.
"""
from typing import Optional


def _build_lead_context(profile: dict) -> str:
    """Build the lead facts section of the prompt."""
    parts = []
    if profile.get("name"):
        parts.append(f"Name: {profile['name']}")
    if profile.get("company"):
        parts.append(f"Company: {profile['company']}")
    if profile.get("role"):
        parts.append(f"Role: {profile['role']}")
    if profile.get("industry"):
        parts.append(f"Industry: {profile['industry']}")
    if profile.get("company_size"):
        parts.append(f"Company Size: {profile['company_size']}")
    if profile.get("funding_status"):
        parts.append(f"Funding: {profile['funding_status']}")

    # Tech stack (top 3)
    tech = profile.get("tech_stack") or []
    if tech:
        parts.append(f"Tech Stack: {', '.join(tech[:3])}")

    # Top buying signal
    signals = profile.get("buying_signals") or []
    if signals:
        parts.append(f"Top Signal: {signals[0].get('signal', '')}")

    # Recent news
    news = profile.get("recent_news") or []
    if news:
        parts.append(f"Recent News: {news[0].get('title', '')}")

    return "\n".join(parts)


def build_direct_prompt(profile: dict, product_desc: str, value_prop: str) -> str:
    """
    Direct and concise tone — under 100 words body.
    MUST reference specific facts from lead profile.
    """
    context = _build_lead_context(profile)
    name = profile.get("name", "").split()[0] if profile.get("name") else "there"
    company = profile.get("company", "your company")

    return f"""<|system|>
You are a B2B sales expert writing a highly personalized outreach email. You MUST reference specific facts from the lead profile. Never write generic emails. Keep the body under 100 words.
</s>
<|user|>
Write a direct, concise cold outreach email using ONLY these facts:

LEAD PROFILE:
{context}

OUR PRODUCT: {product_desc}
VALUE PROP: {value_prop}

FORMAT YOUR RESPONSE EXACTLY AS:
Subject: [subject line]
[email body - 3-4 short sentences, reference at least one specific fact]
CTA: [one clear call to action]

Rules:
- Mention {company} by name
- Reference at least one specific fact (funding/news/tech/signal)
- No fluff, no "I hope this finds you well"
- Body must be under 100 words
</s>
<|assistant|>
Subject:"""


def build_social_proof_prompt(profile: dict, product_desc: str, value_prop: str) -> str:
    """
    Social-proof-led tone — references peer companies and success stories.
    MUST still reference lead-specific facts.
    """
    context = _build_lead_context(profile)
    company = profile.get("company", "your company")
    industry = profile.get("industry", "your industry")

    signals = profile.get("buying_signals") or []
    signal_text = signals[0].get("signal", "your recent growth") if signals else "your momentum"

    return f"""<|system|>
You are a B2B sales expert writing a personalized outreach email with social proof. Reference specific facts and mention how similar companies benefited.
</s>
<|user|>
Write a social-proof-led outreach email using these facts:

LEAD PROFILE:
{context}

OUR PRODUCT: {product_desc}
VALUE PROP: {value_prop}

FORMAT YOUR RESPONSE EXACTLY AS:
Subject: [subject line]
[email body - mention {signal_text}, reference similar {industry} companies that benefited, be specific]
CTA: [one clear call to action]

Rules:
- Open by referencing {company}'s specific situation
- Include one social proof statement ("Similar companies like X achieved Y")
- Keep body under 150 words
- End with a low-friction CTA
</s>
<|assistant|>
Subject:"""


def validate_draft_specificity(draft: str, profile: dict) -> bool:
    """
    Validate that the draft references at least one specific fact.
    Returns True if specific enough, False if too generic.
    """
    if not draft or len(draft) < 50:
        return False

    draft_lower = draft.lower()
    specific_facts = []

    # Check company name
    if profile.get("company") and profile["company"].lower() in draft_lower:
        specific_facts.append("company_name")

    # Check tech stack mention
    for tech in (profile.get("tech_stack") or [])[:5]:
        if tech.lower() in draft_lower:
            specific_facts.append(f"tech:{tech}")
            break

    # Check news mention
    for article in (profile.get("recent_news") or [])[:3]:
        title_words = article.get("title", "").lower().split()
        significant_words = [w for w in title_words if len(w) > 4]
        if any(w in draft_lower for w in significant_words[:3]):
            specific_facts.append("news_mention")
            break

    # Check buying signal
    for sig in (profile.get("buying_signals") or [])[:2]:
        sig_words = sig.get("signal", "").lower().split()
        if any(w in draft_lower for w in sig_words if len(w) > 4):
            specific_facts.append("signal_mention")
            break

    # Check funding
    if profile.get("funding_status") and any(
        w in draft_lower
        for w in ["series", "raised", "funding", "seed", "round"]
    ):
        specific_facts.append("funding_mention")

    return len(specific_facts) >= 1
