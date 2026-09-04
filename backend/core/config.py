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


settings = Settings()
