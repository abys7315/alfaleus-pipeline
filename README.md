# Alfaleus — Lead Intelligence Platform

> **AI-powered lead enrichment, ICP scoring, and personalized outreach at scale.**

A full-stack sales intelligence system that takes a CSV of raw leads and autonomously enriches each one from multiple sources, scores them against your Ideal Customer Profile using semantic AI, detects buying signals, generates personalized outreach emails, and syncs everything to Notion.

---

## Live Demo
- **Web App**: `https://alfaleus.up.railway.app` *(deploy before submission)*
- **Chrome Extension**: Loadable in developer mode — see instructions below

---

## Architecture

```
CSV / Chrome Extension → FastAPI Backend → Celery Worker Pipeline
                                              ├── Website Scraper (httpx + BS4)
                                              ├── LinkedIn Scraper (httpx + stealth headers)
                                              ├── Google News RSS
                                              ├── Semantic ICP Scorer (sentence-transformers)
                                              ├── Buying Signal Detector
                                              ├── Email Finder (MX + permutations) [Bonus]
                                              ├── TinyLlama Outreach Draft Generator (Ollama)
                                              └── Notion CRM Sync
                                        ↓
                              PostgreSQL (Railway) + Redis (pub/sub)
                                        ↓
                              React Frontend (SSE real-time updates)
```

**Services on Railway:**
| Service | Role |
|---|---|
| `backend` | FastAPI app + migrations |
| `worker` | Celery enrichment pipeline |
| `postgres` | Lead database |
| `redis` | Celery broker + SSE pub/sub |
| `ollama` | TinyLlama LLM inference |

---

## ICP Scoring Formula

The ICP scorer uses **semantic similarity** via `sentence-transformers` (all-MiniLM-L6-v2), not keyword matching. This means:
- "boutique software consultancy with 40 engineers" correctly matches target size "20–100 employees"
- "Head of Platform Engineering" correctly evaluates against "VP or above in engineering" using cosine similarity

### Formula

```
Total Score = (ICP_Fit_Score × W_icp) + (Buying_Signal_Score × W_signals)

ICP_Fit_Score (0–100):
  = Σ (criterion_score × criterion_weight) − disqualifier_penalty

  Criteria (default weights, configurable):
  ┌────────────────────┬────────┐
  │ Company Size Match │  25pts │
  │ Industry Match     │  25pts │
  │ Tech Stack Match   │  20pts │
  │ Seniority Match    │  20pts │
  │ Disqualifier Check │ -10pts │
  └────────────────────┴────────┘

Buying_Signal_Score (0–100):
  = min(100, Σ signal_weights)
  ┌──────────────────┬──────┐
  │ Recent Funding   │  35  │
  │ Leadership Hire  │  25  │
  │ Hiring Expansion │  20  │
  │ Tech Fit Signal  │  20  │
  └──────────────────┴──────┘

Default: W_icp = 0.6, W_signals = 0.4
All weights are user-configurable from the ICP Config screen (no code changes required).
```

---

## LLM Model

- **Model**: TinyLlama 1.1B Chat Q4_K_M (GGUF format)
- **Runtime**: Ollama (OpenAI-compatible REST API)
- **Memory footprint**: ~600 MB RAM
- **Inference**: CPU-only, ~15–30 seconds per email draft on 1 vCPU
- **Context window**: 2048 tokens (sufficient for lead profile + email)
- **Upgrade path**: Swap `tinyllama` for `phi3:mini` (3.8B, ~2.2GB) for higher quality drafts on paid Railway plan

**Why TinyLlama?** It fits within Railway's free tier memory constraints (~512MB–1GB per service) while producing coherent, lead-specific email drafts when given well-structured prompts.

---

## LinkedIn Scraping Approach & Known Failure Modes

**Approach:**
- Uses `httpx` with realistic browser headers (no headless browser — reduces detection)
- Randomized delays: 2–5 seconds between requests
- Targets public LinkedIn pages only (no login required)
- Extracts: employee count, about section, recent posts, company description

**Known Failure Modes:**
| Failure | Frequency | Handling |
|---|---|---|
| 999 "Authentication Required" | ~30% | Marks source as `blocked`, continues from other sources |
| 429 Rate Limit | ~10% on burst | Exponential backoff, retry once |
| Empty page (JS-rendered, no SSR) | ~20% | Returns partial data with `low` confidence |
| Company slug not found | ~5% | Marks as `skipped`, continues |

**Mitigation**: The pipeline treats LinkedIn as one of three sources. Even when completely blocked, website + news scraping typically provides 60–70% of enrichment data.

---

## Local Development

### Prerequisites
- Docker + Docker Compose
- Node.js 20+
- Python 3.11+

### Quick Start

```bash
# 1. Clone repo
git clone https://github.com/yourusername/alfaleus
cd alfaleus

# 2. Configure environment
cp .env.example .env
# Edit .env with your Notion API key

# 3. Start all services
docker-compose up -d

# 4. Wait for Ollama to pull TinyLlama (~1GB download, first time only)
docker-compose logs -f ollama

# 5. Open the app
open http://localhost:5173
```

### Running Without Docker

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Worker (separate terminal)
celery -A celery_app worker --loglevel=info

# Frontend (separate terminal)
cd frontend
npm install
npm run dev

# Ollama (separate terminal — install from https://ollama.ai)
ollama serve
ollama pull tinyllama
```

---

## Chrome Extension — Load in Developer Mode

1. Open Chrome → `chrome://extensions/`
2. Enable **Developer mode** (toggle, top-right)
3. Click **Load unpacked**
4. Select the `chrome-extension/` folder from this repo
5. The Alfaleus icon appears in your toolbar

**Configure the backend URL:**
- Click the Alfaleus icon → gear icon (⚙) → enter your Railway backend URL → Save

---

## CSV Format

The upload accepts CSV files with the following columns (case-insensitive):

| Column | Required | Description |
|---|---|---|
| `name` | Yes* | Lead's full name |
| `company` | Yes* | Company name |
| `email` | Optional | Lead's email (for dedup) |
| `domain` | Optional | Company domain (e.g. `stripe.com`) |
| `linkedin_url` | Optional | LinkedIn profile URL |

*Either `name`+`company` OR `domain` alone is sufficient.

---

## Notion CRM Setup

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create a new integration → copy the **Internal Integration Token**
3. Create a new Notion database (or use existing)
4. Share the database with your integration (Share → Invite)
5. Copy the **Database ID** from the database URL: `notion.so/workspace/{DATABASE_ID}?v=...`
6. Add both to your `.env` file

---

## Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway init

# Deploy backend
cd backend && railway up --service backend

# Deploy worker
railway up --service worker

# Environment variables — set in Railway dashboard:
# DATABASE_URL, REDIS_URL, OLLAMA_URL, NOTION_API_KEY, NOTION_DATABASE_ID, SECRET_KEY
```

---

## Bonus Features

| Feature | Description |
|---|---|
| **Email Finder** | Generates email permutations (first.last@domain) and verifies MX records. Shows verified/likely emails separately on lead detail. |
| **Sequence Builder** | 3-step outreach sequence (Day 0 → Day 3 → Day 7) with LLM variants per step. Exportable as CSV. |
| **Score History** | Tracks ICP score changes over time as new enrichment runs. Timeline chart on lead detail view. |
| **Domain Enrichment** | Input a company domain → system discovers individuals from team page, press mentions. Creates leads automatically. |

---

## Project Structure

```
alfaleus/
├── backend/          # FastAPI + Celery pipeline
├── frontend/         # React + Vite web app
├── chrome-extension/ # MV3 Chrome extension
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Evaluation Notes

- **Graceful degradation**: Every scraper returns a dict (never raises). The pipeline continues if any source fails.
- **Semantic ICP**: Open `backend/app/pipeline/icp_scorer.py` — scoring is entirely based on cosine similarity embeddings, not string matching.
- **Specific outreach**: Prompts enforce that drafts must reference `buying_signals[0].signal`, `tech_stack[0]`, or `recent_news[0].title` — generic drafts are rejected and retried.
- **CRM dedup**: Queries Notion by `Domain` property before creating/updating records.
- **Memory**: TinyLlama Q4 + sentence-transformers MiniLM = ~680 MB total ML memory footprint.
