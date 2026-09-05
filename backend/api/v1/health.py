"""
AAROH — Health & Readiness Endpoints

GET /api/v1/health
    Liveness check — is the FastAPI process running?
    Never touches the database.

GET /api/v1/ready
    Readiness check — can the application reach PostgreSQL?
    Returns 503 if the database is unavailable.
    Never exposes connection strings, passwords, or stack traces.
"""

import logging

from backend.schemas.error import common_responses
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Re-use the single SessionLocal from the existing backend/database.py.
# This is the ONLY database engine in the project — we do NOT create another.
from backend.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


# ---------------------------------------------------------------------------
# GET /health  — liveness probe
# ---------------------------------------------------------------------------

@router.get(
    "/health", responses=common_responses,
    summary="Liveness check",
    description="Returns 200 if the FastAPI process is running.",
)
def health() -> JSONResponse:
    """
    Liveness probe.
    No database interaction. If this endpoint responds, the process is alive.
    """
    return JSONResponse(content={"status": "ok"}, status_code=200)


# ---------------------------------------------------------------------------
# GET /ready  — readiness probe
# ---------------------------------------------------------------------------

@router.get(
    "/ready", responses=common_responses,
    summary="Readiness check",
    description=(
        "Returns 200 when the application can reach PostgreSQL. "
        "Returns 503 when PostgreSQL is unavailable."
    ),
)
def ready() -> JSONResponse:
    """
    Readiness probe.
    Performs a minimal SELECT 1 against PostgreSQL to confirm connectivity.
    Error details remain server-side only — never exposed to the caller.
    """
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return JSONResponse(content={"status": "ready"}, status_code=200)

    except SQLAlchemyError:
        # Log at WARNING so operators can see it.
        # exc_info=False ensures the traceback (which may reference the
        # connection string) is not emitted.
        logger.warning(
            "Readiness check: PostgreSQL is not reachable.",
            exc_info=False,
        )
        return JSONResponse(
            content={"status": "not_ready"},
            status_code=503,
        )

    except Exception:  # noqa: BLE001 — safety net; no raw tracebacks in responses
        db.rollback()
        logger.warning(
            "Readiness check: unexpected error during database probe.",
            exc_info=False,
        )
        return JSONResponse(
            content={"status": "not_ready"},
            status_code=503,
        )

    finally:
        db.close()
