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
