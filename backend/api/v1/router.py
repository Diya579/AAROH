"""
AAROH — API v1 Central Router

Aggregates all v1 sub-routers.
Business logic must NOT live here — only router includes.
"""

from fastapi import APIRouter

from backend.api.v1 import health, cases, interactions

router = APIRouter()

# Include the health/readiness router.
# Routes are prefixed by /api/v1 at the application level (main.py).
router.include_router(health.router)

# Include resource routers
router.include_router(cases.router)
router.include_router(interactions.router)
