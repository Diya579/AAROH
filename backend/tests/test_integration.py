"""
AAROH — Integration tests for voice ingestion flow.

Uses FakeAuthProvider (installed by conftest.py) instead of X-Mock-Role headers.
For tests that need a specific role, we use a context-scoped override helper.
"""

import os
import tempfile
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base
from backend import models
from backend.core.security import get_auth_provider
from backend.core.auth_provider import AuthenticatedUser, FakeAuthProvider

from backend.api.v1.cases import get_db as get_cases_db
from backend.api.v1.interactions import get_db as get_interactions_db
from backend.api.v1.consents import get_db as get_consents_db
from backend.api.v1.predictions import get_db as get_predictions_db
from backend.api.v1.interventions import get_db as get_interventions_db
from backend.api.v1.events import get_db as get_events_db

# ---------------------------------------------------------------------------
# In-memory SQLite DB for integration tests
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_cases_db] = override_get_db
app.dependency_overrides[get_interactions_db] = override_get_db
app.dependency_overrides[get_consents_db] = override_get_db
app.dependency_overrides[get_predictions_db] = override_get_db
app.dependency_overrides[get_interventions_db] = override_get_db
app.dependency_overrides[get_events_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helper: temporarily override auth with a specific role
# ---------------------------------------------------------------------------

@contextmanager
def as_role(role: str, district: str = None, state: str = None):
    """Context manager to run requests under a specific fake role."""
    user = AuthenticatedUser(id=f"test-{role.lower()}", role=role,
                             district=district, state=state)
    app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(user)
    try:
        yield
    finally:
        # Restore the default ADMIN fake from conftest
        from backend.tests.conftest import DEFAULT_TEST_USER
        app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(DEFAULT_TEST_USER)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_voice_ingestion_flow():
    """Full flow: create case → grant consent → create interaction → upload voice."""

    # 1. Create a case (as ADMIN via conftest default)
    case_payload = {
        "case_id": "CASE-TEST-INT-1",
        "language": "hi-IN",
        "district_type": "rural",
        "district": "Pune",
        "priority_use_case": "domestic_violence",
        "current_stage": "intake",
    }
    response = client.post("/api/v1/cases", json=case_payload)
    assert response.status_code == 201, response.text
    db_case_id = response.json()["id"]

    # 2. Grant voice consent
    consent_payload = {"voice_analysis_consent": True}
    resp = client.put(f"/api/v1/consents/{db_case_id}", json=consent_payload)
    assert resp.status_code == 200, resp.text

    # 3. Create interaction
    interaction_payload = {
        "case_id": db_case_id,
        "interaction_date": "2026-09-03T12:00:00Z",
        "channel": "voice",
        "language": "hi-IN",
    }
    resp = client.post("/api/v1/interactions", json=interaction_payload)
    assert resp.status_code == 201, resp.text
    interaction_id = resp.json()["id"]

    # 4. Upload voice file
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_audio.write(b"fake audio content")
    temp_audio.close()

    try:
        with open(temp_audio.name, "rb") as f:
            files = {"file": ("test.wav", f, "audio/wav")}
            resp = client.post(
                f"/api/v1/interactions/{interaction_id}/voice",
                files=files,
            )
        assert resp.status_code == 202, resp.text
        assert resp.json()["status"] == "RECEIVED"
    finally:
        os.unlink(temp_audio.name)
