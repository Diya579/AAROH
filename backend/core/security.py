"""
AAROH — Security: RBAC and dependency injection

get_auth_provider  → returns the active AuthProvider (swappable for tests)
get_current_user   → calls provider.authenticate(); raises 401 if unauthenticated
require_role(...)  → enforces RBAC; raises 403 if role not permitted

IMPORTANT:
    - The client NEVER supplies its own role.
    - Production code calls get_auth_provider() which returns DevAuthProvider.
    - Tests override get_auth_provider with a FakeAuthProvider via
      app.dependency_overrides — no X-Mock-Role header, no header tricks.
"""

from fastapi import Depends, HTTPException, Request, status

from backend.core.auth_provider import (
    AuthenticatedUser,
    AuthProvider,
    DevAuthProvider,
)


# ---------------------------------------------------------------------------
# Provider dependency — the single point to swap auth implementations
# ---------------------------------------------------------------------------

def get_auth_provider() -> AuthProvider:
    """
    Returns the active authentication provider.

    In production this returns DevAuthProvider.
    Tests override this via:
        app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(user)
    """
    return DevAuthProvider()


# ---------------------------------------------------------------------------
# Current user dependency
# ---------------------------------------------------------------------------

def get_current_user(
    request: Request,
    provider: AuthProvider = Depends(get_auth_provider),
) -> AuthenticatedUser:
    """
    Resolves the current authenticated user from the request.

    Raises HTTP 401 if the request is unauthenticated or the credential
    is invalid. The role on the returned AuthenticatedUser is set by the
    provider — never by the client.
    """
    return provider.authenticate(request)


# ---------------------------------------------------------------------------
# RBAC dependency factory
# ---------------------------------------------------------------------------

def require_role(*roles: str):
    """
    Returns a FastAPI dependency that enforces role-based access control.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("ADMIN"))])

    Raises:
        HTTP 401 — if the request is unauthenticated (propagated from get_current_user)
        HTTP 403 — if the authenticated user's role is not in the allowed list
    """

    def _check(user: AuthenticatedUser = Depends(get_current_user)) -> None:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient permissions. "
                    f"Required one of: {list(roles)}"
                ),
            )

    return _check


# ---------------------------------------------------------------------------
# Row-level RBAC enforcement
# ---------------------------------------------------------------------------

def verify_case_access(case, user: AuthenticatedUser, db) -> None:
    """
    Enforces row-level access control for a specific Case.
    Raises HTTP 403 if the user is not authorized to access this case.
    """
    if user.role == "ADMIN":
        return
        
    if user.role in ("USER", "VICTIM"):
        # Victim can only access their own case.
        # Assuming user.id corresponds to case.case_id
        if case.case_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access another person's case."
            )
            
    elif user.role == "DISTRICT_OFFICIAL":
        if case.district != user.district:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to access cases outside district: {user.district}"
            )
            
    elif user.role == "COUNSELLOR":
        # Check if an intervention for this case is assigned to this counsellor
        from backend.models import Intervention
        assigned = db.query(Intervention).filter(
            Intervention.case_id == case.id,
            Intervention.assigned_to == user.id
        ).first()
        if not assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: you are not assigned to any interventions for this case."
            )
            
    elif user.role in ("STATE_OFFICIAL", "NATIONAL_OFFICIAL", "SYSTEM_SERVICE"):
        # Assumed full read access across all cases for these roles
        return
        
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role {user.role} is not mapped for case access."
        )
