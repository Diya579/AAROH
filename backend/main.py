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

import uuid
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.config import settings
from backend.api.v1.router import router as v1_router

# ---------------------------------------------------------------------------
# Global Middleware
# ---------------------------------------------------------------------------

async def request_id_middleware(request: Request, call_next):
    # Generate a unique correlation ID for the request
    request_id = str(uuid.uuid4())
    # Attach to the request state so routes and exception handlers can access it
    request.state.request_id = request_id
    
    # Process the request
    response = await call_next(request)
    
    # Attach the correlation ID to the response headers
    response.headers["X-Request-ID"] = request_id
    return response

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

app.middleware("http")(request_id_middleware)

# ---------------------------------------------------------------------------
# Global Exception Handlers (Standard Error Contract)
# ---------------------------------------------------------------------------

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Preserve headers from the original exception (e.g. WWW-Authenticate for 401)
    headers = dict(exc.headers) if exc.headers else {}
    req_id = getattr(request.state, "request_id", "UNKNOWN")
    headers["X-Request-ID"] = req_id
    code = getattr(exc, "code", "HTTP_EXCEPTION")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail),
                "request_id": getattr(request.state, "request_id", "UNKNOWN")
            }
        },
        headers=headers,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request payload",
                "request_id": getattr(request.state, "request_id", "UNKNOWN")
            }
        },
        headers={"X-Request-ID": getattr(request.state, "request_id", "UNKNOWN")},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the exception stacktrace internally here in a real app
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": getattr(request.state, "request_id", "UNKNOWN")
            }
        },
        headers={"X-Request-ID": getattr(request.state, "request_id", "UNKNOWN")},
    )
