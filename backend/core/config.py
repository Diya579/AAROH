"""
AAROH — Application Configuration

Reads environment variables via python-dotenv.
Credentials are NEVER hard-coded here.

Dependency chain:
    Environment (.env)
        ↓
    Settings (this module)
        ↓
    FastAPI (backend/main.py)
        ↓
    backend/database.py  ← sole database authority, not duplicated here
        ↓
    PostgreSQL
"""

import os

from dotenv import load_dotenv

# Load .env from the project root.
# backend/database.py also calls load_dotenv(), so this is idempotent.
load_dotenv()

aaroh_env_val = os.environ.get("AAROH_ENV", "development").lower()
auth_mode_val = os.environ.get("AAROH_AUTH_MODE", "session").lower()

if aaroh_env_val == "production" and auth_mode_val == "dev":
    raise RuntimeError("FATAL: AAROH_AUTH_MODE=dev cannot be used when AAROH_ENV=production")


class Settings:
    """Central settings object for the FastAPI application layer."""

    # Application metadata
    app_name: str = "AAROH API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    # The database URL is owned by backend/database.py.
    # This property exists only to confirm it is set — it is never stored
    # as an attribute to avoid accidental serialisation or logging.
    @property
    def database_url_is_configured(self) -> bool:
        return bool(os.getenv("DATABASE_URL"))

    @property
    def aaroh_env(self) -> str:
        return os.environ.get("AAROH_ENV", "development").lower()

    @property
    def auth_mode(self) -> str:
        return os.environ.get("AAROH_AUTH_MODE", "session").lower()

    _generated_secret: str | None = None

    @property
    def session_secret_key(self) -> str:
        # In dev, we can fallback to a generated one if not set, but better to require it or generate a temporary one
        secret = os.environ.get("AAROH_SESSION_SECRET")
        if not secret:
            if self.aaroh_env == "production":
                raise ValueError("AAROH_SESSION_SECRET must be set in production.")
            if self._generated_secret is None:
                import secrets
                self._generated_secret = secrets.token_hex(32)
            return self._generated_secret
        return secret

    @property
    def session_expiry_hours(self) -> int:
        return int(os.environ.get("AAROH_SESSION_EXPIRY_HOURS", "8"))

    @property
    def cors_origins(self) -> list[str]:
        origins_str = os.environ.get(
            "AAROH_CORS_ORIGINS", 
            "http://localhost:3000,http://localhost:5173"
        )
        return [o.strip() for o in origins_str.split(",") if o.strip()]

    @property
    def secure_cookies(self) -> bool:
        return self.aaroh_env == "production"

settings = Settings()
