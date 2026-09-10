"""
AAROH — Integration tests for voice ingestion flow.

Uses FakeAuthProvider (installed by conftest.py) instead of X-Mock-Role headers.
For tests that need a specific role, we use a context-scoped override helper.
"""

import os
import tempfile
import wave
import io
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


client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    
    app.dependency_overrides[get_cases_db] = override_get_db
    app.dependency_overrides[get_interactions_db] = override_get_db
    app.dependency_overrides[get_consents_db] = override_get_db
    app.dependency_overrides[get_predictions_db] = override_get_db
    app.dependency_overrides[get_interventions_db] = override_get_db
    app.dependency_overrides[get_events_db] = override_get_db
    
    yield
    
    app.dependency_overrides.pop(get_cases_db, None)
    app.dependency_overrides.pop(get_interactions_db, None)
    app.dependency_overrides.pop(get_consents_db, None)
    app.dependency_overrides.pop(get_predictions_db, None)
    app.dependency_overrides.pop(get_interventions_db, None)
    app.dependency_overrides.pop(get_events_db, None)
    
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
    # Generate a valid WAV file (minimum 1 second duration required)
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(temp_audio.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000) # 1 second of silence
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


def test_text_interaction_ml_integration():
    """Tests case->ML pipeline and persistence in Postgres."""
    # 1. Create a case
    case_payload = {
        "case_id": "CASE-TEST-INT-TEXT",
        "language": "hi-IN",
        "district_type": "rural",
        "district": "Pune",
        "priority_use_case": "domestic_violence",
        "current_stage": "intake",
    }
    resp = client.post("/api/v1/cases", json=case_payload)
    assert resp.status_code == 201
    db_case_id = resp.json()["id"]

    # 2. Create interaction with text
    interaction_payload = {
        "case_id": db_case_id,
        "interaction_date": "2026-09-04T12:00:00Z",
        "channel": "whatsapp",
        "language": "en-IN",
        "text_response": "I am feeling very hopeless and want to end my life",
        "safety_response": 5,
    }
    resp = client.post("/api/v1/interactions", json=interaction_payload)
    assert resp.status_code == 201

    # 3. Check persistence of Prediction and DistressState
    from backend.models import Prediction, DistressState
    db = TestingSessionLocal()
    try:
        preds = db.query(Prediction).filter(Prediction.case_id == db_case_id).all()
        assert len(preds) == 1
        assert preds[0].risk_level == "EMERGENCY"
        
        distress = db.query(DistressState).filter(DistressState.case_id == db_case_id).all()
        assert len(distress) == 1
    finally:
        db.close()

def test_rbac_on_interactions_and_predictions():
    """Test RBAC for interactions (which implicitly covers predictions if endpoint exists)."""
    # Create a case for Pune
    case_payload = {
        "case_id": "CASE-TEST-RBAC-1",
        "language": "hi-IN",
        "district_type": "rural",
        "district": "Pune",
        "priority_use_case": "domestic_violence",
        "current_stage": "intake",
    }
    resp = client.post("/api/v1/cases", json=case_payload)
    db_case_id = resp.json()["id"]
    
    # Interaction
    client.post("/api/v1/interactions", json={
        "case_id": db_case_id,
        "interaction_date": "2026-09-04T12:00:00Z",
        "channel": "whatsapp",
        "language": "en-IN",
        "text_response": "I am okay today.",
    })
    
    # Test read access for correct district official
    with as_role("DISTRICT_OFFICIAL", district="Pune"):
        resp = client.get(f"/api/v1/interactions?case_id={db_case_id}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        
        # Test direct fetch to prediction endpoint
        resp = client.get(f"/api/v1/predictions/{db_case_id}")
        assert resp.status_code == 200

    # Test read access for wrong district official
    with as_role("DISTRICT_OFFICIAL", district="Mumbai"):
        resp = client.get(f"/api/v1/interactions?case_id={db_case_id}")
        assert resp.status_code == 200
        assert len(resp.json()) == 0 # Scope filter hides it
        
        # Test direct fetch to prediction endpoint (should return 403 Forbidden)
        resp = client.get(f"/api/v1/predictions/{db_case_id}")
        assert resp.status_code == 403

def test_ml_failure_error_handling(monkeypatch):
    """Test that an ML pipeline failure does not prevent interaction creation."""
    case_payload = {
        "case_id": "CASE-TEST-FAIL-1",
        "language": "hi-IN",
        "district_type": "rural",
        "district": "Pune",
        "priority_use_case": "domestic_violence",
        "current_stage": "intake",
    }
    db_case_id = client.post("/api/v1/cases", json=case_payload).json()["id"]

    # Force a failure in the ML pipeline
    from backend.services import interaction_service
    
    def mock_run_case(*args, **kwargs):
        raise Exception("Simulated ML Failure")
        
    monkeypatch.setattr(interaction_service._ml_pipeline, "run_case", mock_run_case)
    
    # Interaction creation should succeed despite ML failure
    interaction_payload = {
        "case_id": db_case_id,
        "interaction_date": "2026-09-05T12:00:00Z",
        "channel": "whatsapp",
        "language": "en-IN",
        "text_response": "Checking failure mode",
    }
    resp = client.post("/api/v1/interactions", json=interaction_payload)
    assert resp.status_code == 201
    
    # DB should have interaction and an error-state prediction
    from backend.models import Prediction, Interaction
    db = TestingSessionLocal()
    try:
        interactions = db.query(Interaction).filter(Interaction.case_id == db_case_id).all()
        assert len(interactions) == 1
        
        preds = db.query(Prediction).filter(Prediction.case_id == db_case_id).all()
        assert len(preds) == 1
        assert preds[0].risk_level == "SYSTEM_ERROR"
        assert "ML pipeline failed" in preds[0].explanation["message"]
    finally:
        db.close()


def test_api_outcome_recording_end_to_end():
    from backend.tests.test_integration import client, as_role
    import uuid

    # 1. Create a case
    case_payload = {
        "case_id": "CASE-TEST-OUTCOME-" + uuid.uuid4().hex[:8],
        "language": "en",
        "district_type": "urban",
        "district": "Pune",
        "state": "Maharashtra",
        "priority_use_case": "dv",
        "current_stage": "intake"
    }
    c_res = client.post("/api/v1/cases", json=case_payload)
    assert c_res.status_code == 201
    case_id_int = c_res.json()["id"]

    # 2. Create an intervention manually to have an intervention_id
    with as_role("ADMIN"):
        inv_res = client.post("/api/v1/interventions", json={
            "case_id": case_id_int,
            "intervention_type": "ROUTINE_MONITORING",
            "status": "IN_PROGRESS"
        })
        assert inv_res.status_code == 201
        inv_id_int = inv_res.json()["id"]

    # 3. Record an outcome using the API
    with as_role("ADMIN"):
        out_res = client.post("/api/v1/outcomes", json={
            "case_id": case_id_int,
            "intervention_id": inv_id_int,
            "outcome_type": "CONTACTED",
            "completed": True,
            "follow_up_required": True,
            "notes": "Spoke to victim. Needs follow up tomorrow."
        })
        assert out_res.status_code == 201
        out_json = out_res.json()
        assert out_json["outcome_type"] == "CONTACTED"
        assert out_json["completed"] is True
        assert out_json["follow_up_required"] is True
        assert out_json["notes"] == "Spoke to victim. Needs follow up tomorrow."

    # 4. Verify no downstream interventions were created (demonstrating the gap)
    with as_role("ADMIN"):
        invs_res = client.get(f"/api/v1/interventions?case_id={case_id_int}")
        assert invs_res.status_code == 200
        invs = invs_res.json()
        assert len(invs) == 1, "follow_up_required=True incorrectly spawned a new intervention"
