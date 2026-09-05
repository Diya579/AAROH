"""
Integration tests for AAROH backend focusing on new integration boundaries.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base
from backend import models

from backend.api.v1.cases import get_db as get_cases_db
from backend.api.v1.interactions import get_db as get_interactions_db
from backend.api.v1.consents import get_db as get_consents_db
from backend.api.v1.predictions import get_db as get_predictions_db
from backend.api.v1.interventions import get_db as get_interventions_db
from backend.api.v1.events import get_db as get_events_db

import os
import tempfile

from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
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

import pytest

@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_auth_boundary_victim_role():
    # Victim creates a case? No, victim cannot create case, only COUNSELLOR / ADMIN can.
    # Let's try to access /api/v1/cases with USER role and it should fail
    response = client.get("/api/v1/cases", headers={"X-Mock-Role": "USER"})
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["error"]["message"]

def test_auth_boundary_counsellor_role():
    # Counsellor can get cases
    Base.metadata.create_all(bind=engine)
    response = client.get("/api/v1/cases", headers={"X-Mock-Role": "COUNSELLOR"})
    assert response.status_code == 200

def test_voice_ingestion_flow():
    Base.metadata.create_all(bind=engine)
    
    # 1. Create a case
    case_payload = {
        "case_id": "CASE-TEST-1",
        "language": "hi-IN",
        "district_type": "rural",
        "district": "Pune",
        "priority_use_case": "domestic_violence",
        "current_stage": "intake"
    }
    response = client.post("/api/v1/cases", json=case_payload, headers={"X-Mock-Role": "ADMIN"})
    assert response.status_code == 201
    db_case_id = response.json()["id"]
    
    # 2. Grant voice consent
    consent_payload = {
        "voice_analysis_consent": True
    }
    client.put(f"/api/v1/consents/{db_case_id}", json=consent_payload, headers={"X-Mock-Role": "ADMIN"})
    
    # 3. Create interaction
    interaction_payload = {
        "case_id": db_case_id,
        "interaction_date": "2026-09-03T12:00:00Z",
        "channel": "voice",
        "language": "hi-IN"
    }
    resp = client.post("/api/v1/interactions", json=interaction_payload, headers={"X-Mock-Role": "COUNSELLOR"})
    interaction_id = resp.json()["id"]
    
    # 4. Upload voice file
    # Create temp audio file
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_audio.write(b"fake audio content")
    temp_audio.close()
    
    try:
        with open(temp_audio.name, "rb") as f:
            files = {"file": ("test.wav", f, "audio/wav")}
            resp = client.post(
                f"/api/v1/interactions/{interaction_id}/voice",
                files=files,
                headers={"X-Mock-Role": "USER"}
            )
        assert resp.status_code == 202
        assert resp.json()["status"] == "RECEIVED"
    finally:
        os.unlink(temp_audio.name)
