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
    Enforces row-level access control for a specific Case row.
    Raises HTTP 403 if the user is not authorised to access this case.

    FIELD USAGE NOTES — two distinct identifier columns exist on the Case model:
    ─────────────────────────────────────────────────────────────────────────────
      Case.id        Integer auto-increment PRIMARY KEY (e.g. 1, 2, 3…)
                     Used everywhere in FK relationships (Intervention.case_id
                     is an Integer FK referencing cases.id).

      Case.case_id   String(50) human-readable external identifier
                     (e.g. "CASE-001", "VICTIM-1"). This is what the victim
                     knows as their "case ID" and maps to user.id for victims.

    VICTIM/USER check: compares Case.case_id (the human string) to user.id
                       because the victim's user identity IS their case_id string.

    COUNSELLOR check:  queries Intervention.case_id (the Integer FK → cases.id)
                       matched against Case.id (the Integer PK) — correctly using
                       the integer primary key for the FK join, not the string.
    ─────────────────────────────────────────────────────────────────────────────
    """
    if user.role == "ADMIN":
        return

    if user.role in ("USER", "VICTIM"):
        # Case.case_id is the human-readable string identifier that victims
        # receive as their "case number". user.id is also set to this string
        # when a victim authenticates. We compare the string fields deliberately.
        if case.case_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorised to access another person's case."
            )

    elif user.role == "DISTRICT_OFFICIAL":
        # Scoped to their assigned district only.
        if case.district != user.district:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorised to access cases outside district: {user.district}"
            )

    elif user.role == "STATE_OFFICIAL":
        # Scoped to their assigned state only.
        # Case.state must be populated for this check to be meaningful.
        if not user.state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="STATE_OFFICIAL identity has no state attribute configured."
            )
        if case.state != user.state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorised to access cases outside state: {user.state}"
            )

    elif user.role == "NATIONAL_OFFICIAL":
        # Unscoped — national mandate covers all states and districts.
        return

    elif user.role == "COUNSELLOR":
        # Counsellor can only access a case if they are listed as assigned_to
        # on at least one Intervention row for that case.
        # Note: Intervention.case_id is an Integer FK referencing cases.id
        #       (the integer PK), NOT cases.case_id (the string).
        from backend.models import Intervention
        assigned = db.query(Intervention).filter(
            Intervention.case_id == case.id,   # Integer PK join — correct
            Intervention.assigned_to == user.id
        ).first()
        if not assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorised: you are not assigned to any interventions for this case."
            )

    elif user.role == "SYSTEM_SERVICE":
        # Internal service account — full access.
        return

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role}' is not mapped for case-level access control."
        )

