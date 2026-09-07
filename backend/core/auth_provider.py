"""
AAROH — Authentication Provider Abstraction

This module defines the AuthProvider protocol and concrete implementations.

Architecture:
    Request
        │
        ▼
    AuthProvider.authenticate(request) ──► AuthenticatedUser  (or raises 401)
        │
        ▼
    AuthenticatedUser.role  (backend-set, never client-supplied)
        │
        ▼
    require_role(...)  ──► RBAC enforcement
        │
        ▼
    Endpoint

IMPORTANT:
    - The client NEVER supplies its own role.
    - The role comes from the identity the backend resolved.
    - Production code must use DevAuthProvider (or a real OIDC/JWT provider).
    - Tests override `get_auth_provider` with FakeAuthProvider via dependency_overrides.
    - FakeAuthProvider MUST NOT be imported or used outside of tests.
"""

from __future__ import annotations

import json
import os
from typing import Optional, Protocol, runtime_checkable

from fastapi import Request
from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Authenticated identity model
# ---------------------------------------------------------------------------

class AuthenticatedUser(BaseModel):
    """
    Backend-resolved authenticated identity.

    All fields are set by the auth provider after verifying the credential.
    The client cannot influence any field here.
    """
    model_config = ConfigDict(frozen=True)

    id: str
    role: str
    district: Optional[str] = None   # Populated for DISTRICT_OFFICIAL
    state: Optional[str] = None       # Populated for STATE_OFFICIAL


# ---------------------------------------------------------------------------
# AuthProvider protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class AuthProvider(Protocol):
    """
    Interface for authentication providers.

    Swap implementations by overriding `get_auth_provider` in FastAPI's
    dependency system. This keeps production code completely decoupled from
    test infrastructure.
    """

    def authenticate(self, request: Request) -> AuthenticatedUser:
        """
        Verify the credential in the request and return an AuthenticatedUser.

        Raises:
            HTTPException(401)  — if no credential is present or it is invalid.
        """
        ...


# ---------------------------------------------------------------------------
# DevAuthProvider — bearer token mapped via environment variable
# ---------------------------------------------------------------------------

class DevAuthProvider:
    """
    Development authentication provider.

    Reads a Bearer token from the Authorization header and maps it to a
    pre-configured user identity via the AAROH_DEV_TOKENS environment variable.

    AAROH_DEV_TOKENS must be a JSON object mapping token → user dict, e.g.:

        {
            "dev-counsellor-token": {
                "id": "dev-counsellor-001",
                "role": "COUNSELLOR",
                "district": "Pune"
            },
            "dev-admin-token": {
                "id": "dev-admin-001",
                "role": "ADMIN"
            }
        }

    If no token is present, or the token is not in the map → HTTP 401.

    This provider is intentionally simple. Replace with a real OIDC/JWT
    provider for production deployment by swapping get_auth_provider().

    SECURITY NOTE:
        The role is looked up from the server-side token map.
        The client cannot self-assign a role by sending any header.
    """

    def __init__(self) -> None:
        raw = os.environ.get("AAROH_DEV_TOKENS", "{}")
        try:
            self._token_map: dict[str, dict] = json.loads(raw)
        except json.JSONDecodeError:
            self._token_map = {}

    def authenticate(self, request: Request) -> AuthenticatedUser:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide a Bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.removeprefix("Bearer ").strip()
        user_data = self._token_map.get(token)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthenticatedUser(**user_data)


# ---------------------------------------------------------------------------
# FakeAuthProvider — TEST USE ONLY
# ---------------------------------------------------------------------------

class FakeAuthProvider:
    """
    Test-only authentication provider.

    Injects a pre-set AuthenticatedUser without any real credential check.
    Used exclusively via FastAPI dependency_overrides in the test suite.

    NEVER import or use this in production application code.

    Usage in tests:
        from backend.core.auth_provider import FakeAuthProvider, AuthenticatedUser
        from backend.core.security import get_auth_provider

        fake_user = AuthenticatedUser(id="test-user", role="COUNSELLOR")
        app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(fake_user)
    """

    def __init__(self, user: AuthenticatedUser) -> None:
        self._user = user

    def authenticate(self, request: Request) -> AuthenticatedUser:
        return self._user


# ---------------------------------------------------------------------------
# SessionAuthProvider — production auth provider
# ---------------------------------------------------------------------------

class SessionAuthProvider:
    """
    Production authentication provider.
    
    Reads the aaroh_session cookie, validates the signed session ID,
    looks up the session in the DB, checks expiry, and resolves
    the User -> AuthenticatedUser.
    """
    
    def authenticate(self, request: Request) -> AuthenticatedUser:
        from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
        from backend.core.config import settings
        from backend.database import SessionLocal
        from backend.models import SessionRecord, User
        from datetime import datetime

        cookie = request.cookies.get("aaroh_session")
        if not cookie:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. No session cookie found.",
            )

        signer = URLSafeTimedSerializer(settings.session_secret_key)
        try:
            session_id = signer.loads(cookie, max_age=settings.session_expiry_hours * 3600)
        except (BadSignature, SignatureExpired):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session cookie.",
            )

        db = SessionLocal()
        try:
            session_rec = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
            if not session_rec or not session_rec.is_active or session_rec.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session is invalid or expired.",
                )
            
            user = db.query(User).filter(User.id == session_rec.user_id).first()
            if not user or not user.active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive.",
                )
            
            # Map User -> AuthenticatedUser
            auth_id = str(user.id)
            if user.role in ("VICTIM", "USER") and user.case_id_ref:
                auth_id = user.case_id_ref
            elif user.role == "COUNSELLOR":
                auth_id = user.username
                
            return AuthenticatedUser(
                id=auth_id,
                role=user.role,
                district=user.district,
                state=user.state
            )
        finally:
            db.close()
