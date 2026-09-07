"""
AAROH — Authentication Schemas

IMPORTANT:
    LoginRequest contains ONLY username and password.
    The role is NEVER accepted from the client — it is resolved
    server-side from the User record after authentication.
"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login payload. Only username and password are accepted."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Safe user identity returned to the client. No password_hash or tokens."""
    username: str
    role: str


class AuthMeResponse(BaseModel):
    """Response for GET /auth/me."""
    id: str
    role: str
    district: str | None = None
    state: str | None = None
