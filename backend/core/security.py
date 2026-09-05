"""
AAROH — Authentication & RBAC Foundation (Stub)

This module provides placeholder dependencies that FastAPI endpoints
can use via Depends(...).  No real authentication or authorization
logic is implemented yet — every request is allowed through.

When real auth is added (Day 3+), these stubs will be replaced with
JWT validation, role checks, etc.  Endpoint signatures will NOT change.

Usage in an endpoint:
    from backend.core.security import get_current_user

    @router.get("/protected")
    def protected(user=Depends(get_current_user)):
        ...
"""

from fastapi import Request, Depends


def get_current_user(request: Request) -> dict:
    """
    Placeholder: returns a stub user dict.

    Will be replaced with real JWT/session validation.
    The return type will become a proper User model.
    """
    return {
        "id": "stub",
        "role": "caseworker",
    }


def require_role(*roles: str):
    """
    Placeholder: returns a dependency that accepts any request.

    Usage:
        @router.post("/admin-only", dependencies=[Depends(require_role("admin"))])
    """

    def _check(user: dict = Depends(get_current_user)) -> None:  # noqa: ARG001
        # No-op until real RBAC is wired.
        pass

    return _check
