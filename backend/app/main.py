from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.routers import leads, icp, enrichment, drafts, crm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Alfaleus backend...")
    await init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Alfaleus API",
    description="Lead Enrichment & Qualification Pipeline",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router, prefix="/api/v1/leads", tags=["leads"])
app.include_router(icp.router, prefix="/api/v1/icp", tags=["icp"])
app.include_router(enrichment.router, prefix="/api/v1/enrichment", tags=["enrichment"])
app.include_router(drafts.router, prefix="/api/v1/drafts", tags=["drafts"])
app.include_router(crm.router, prefix="/api/v1/crm", tags=["crm"])


@app.get("/api/v1/health")
async def health():
    import httpx
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass
    return {"status": "ok", "ollama": ollama_ok}


@app.get("/")
async def root():
    return {"message": "Alfaleus Lead Intelligence API", "docs": "/docs"}
