from fastapi import Request, Depends, HTTPException, status


def get_current_user(request: Request) -> dict:
    """
    Placeholder: returns a stub user dict.

    Will be replaced with real JWT/session validation.
    The return type will become a proper User model.
    """
    # For testing AAROH roles: USER, COUNSELLOR, DISTRICT_OFFICIAL, STATE_OFFICIAL, NATIONAL_OFFICIAL, ADMIN, SYSTEM_SERVICE
    mock_role = request.headers.get("X-Mock-Role", "ADMIN")
    return {
        "id": "stub-user-id",
        "role": mock_role,
    }


def require_role(*roles: str):
    """
    Enforces role-based access control.
    
    Usage:
        @router.post("/admin-only", dependencies=[Depends(require_role("ADMIN"))])
    """

    def _check(user: dict = Depends(get_current_user)) -> None:
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {roles}"
            )

    return _check
