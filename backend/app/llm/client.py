"""
Ollama HTTP client for TinyLlama inference.
Model: tinyllama:1.1b-chat-v1.0-q4_K_M (~600MB RAM, CPU-only)
"""
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MODEL = "tinyllama"
TIMEOUT = 120  # seconds — CPU inference is slow


async def generate_email_draft(prompt: str, max_tokens: int = 500) -> str:
    """
    Generate text via Ollama API.
    Returns raw LLM output string. Never raises — returns fallback on error.
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "stop": ["</s>", "Human:", "User:"],
        },
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except httpx.TimeoutException:
        logger.warning("Ollama request timed out")
        return _fallback_draft(prompt)
    except Exception as e:
        logger.warning(f"Ollama error: {e}")
        return _fallback_draft(prompt)


async def check_ollama_health() -> bool:
    """Return True if Ollama is running with TinyLlama loaded."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return any("tinyllama" in m.lower() for m in models)
    except Exception:
        pass
    return False


def _fallback_draft(prompt: str) -> str:
    """
    Template-based fallback when Ollama is unavailable.
    Extracts facts from the prompt to keep output specific.
    """
    import re
    company_match = re.search(r"Company:\s*(.+)", prompt)
    name_match = re.search(r"Name:\s*(.+)", prompt)
    signal_match = re.search(r"Top Signal:\s*(.+)", prompt)

    company = company_match.group(1).strip() if company_match else "your company"
    name = name_match.group(1).strip().split()[0] if name_match else "there"
    signal = signal_match.group(1).strip() if signal_match else "your recent growth"

    return f"""Subject: Quick question for {company}

Hi {name},

I came across {company} and noticed {signal} — impressive momentum.

I wanted to reach out because we help companies like yours [value proposition here].

Would you be open to a 15-minute call this week to explore if there's a fit?

Best,
[Your Name]

CTA: Book a 15-minute call: [calendar link]"""
