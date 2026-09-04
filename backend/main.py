"""
AAROH — FastAPI Application Entry Point

Architecture:
    Frontend
        │
        ▼
    FastAPI  (this file)
        │
        ├── /api/v1  →  v1 router  →  health router
        │
        └── backend/database.py  →  SQLAlchemy  →  PostgreSQL

Run locally (from the project root  d:/SIH PROJECT AAROH/AAROH/):
    python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI

from backend.core.config import settings
from backend.api.v1.router import router as v1_router

# ---------------------------------------------------------------------------
# Create the FastAPI application instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AAROH — AI-powered dynamic mental-health monitoring "
        "and distress-prediction system for victims of atrocities."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Mount the versioned API router.
# All health/readiness endpoints live at:
#   GET /api/v1/health
#   GET /api/v1/ready
# ---------------------------------------------------------------------------

app.include_router(v1_router, prefix=settings.api_v1_prefix)
