import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base
from backend.models import Case, IdempotencyRecord
from backend.api.v1.cases import get_db as get_db_cases
from backend.api.v1.interactions import get_db as get_db_interactions
from backend.api.v1.interventions import get_db as get_db_interventions

engine = create_engine(
    "sqlite:///:memory:",
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

# Helper function to generate auth headers for test
def get_auth_headers(role="COUNSELLOR"):
    return {
        "Authorization": "Bearer fake-token",
        "X-Mock-Role": role
    }


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db_cases] = override_get_db
    app.dependency_overrides[get_db_interactions] = override_get_db
    app.dependency_overrides[get_db_interventions] = override_get_db
    yield
    app.dependency_overrides.pop(get_db_cases, None)
    app.dependency_overrides.pop(get_db_interactions, None)
    app.dependency_overrides.pop(get_db_interventions, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def target_case():
    db = TestingSessionLocal()
    try:
        case = Case(
            case_id=f"IDEMP-{uuid.uuid4().hex[:6]}",
            language="en",
            district_type="urban",
            district="Pune",
            state="Maharashtra",
            priority_use_case="dv",
            current_stage="active",
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        return case.id
    finally:
        db.close()

class TestIdempotency:

    def test_interaction_idempotency(self, target_case):
        # 1. First request
        headers = get_auth_headers()
        idem_key = f"key-{uuid.uuid4().hex}"
        headers["Idempotency-Key"] = idem_key
        
        payload1 = {
            "case_id": target_case,
            "interaction_date": "2026-09-06T12:00:00Z",
            "channel": "voice",
            "language": "en"
        }
        r1 = client.post("/api/v1/interactions", json=payload1, headers=headers)
        assert r1.status_code == 201
        data1 = r1.json()

        # 2. Identical retry returns cached data
        r2 = client.post("/api/v1/interactions", json=payload1, headers=headers)
        assert r2.status_code == 201
        data2 = r2.json()
        assert data1 == data2

        # Verify DB only has ONE interaction
        db = TestingSessionLocal()
        from backend.models import Interaction
        count = db.query(Interaction).filter(Interaction.case_id == target_case).count()
        assert count == 1
        
        # Verify idempotency record has the correct response_status
        record = db.query(IdempotencyRecord).filter(IdempotencyRecord.idempotency_key == idem_key).first()
        assert record is not None
        assert record.response_status == 201
        
        db.close()

    def test_interaction_idempotency_rejects_payload_mismatch(self, target_case):
        headers = get_auth_headers()
        idem_key = f"key-{uuid.uuid4().hex}"
        headers["Idempotency-Key"] = idem_key

        payload1 = {
            "case_id": target_case,
            "interaction_date": "2026-09-06T12:00:00Z",
            "channel": "voice",
            "language": "en"
        }
        r1 = client.post("/api/v1/interactions", json=payload1, headers=headers)
        assert r1.status_code == 201

        # Different payload with same key is rejected
        payload2 = {
            "case_id": target_case,
            "interaction_date": "2026-09-06T12:00:00Z",
            "channel": "text",
            "language": "en"
        }
        r2 = client.post("/api/v1/interactions", json=payload2, headers=headers)
        assert r2.status_code == 409
        assert "previously used with a different payload" in r2.text

    def test_intervention_idempotency(self, target_case):
        headers = get_auth_headers()
        idem_key = f"key-{uuid.uuid4().hex}"
        headers["Idempotency-Key"] = idem_key
        
        payload1 = {
            "case_id": target_case,
            "intervention_type": "COUNSELLING",
            "status": "PENDING",
            "assigned_to": "Test"
        }
        r1 = client.post("/api/v1/interventions", json=payload1, headers=headers)
        assert r1.status_code == 201
        data1 = r1.json()

        r2 = client.post("/api/v1/interventions", json=payload1, headers=headers)
        assert r2.status_code == 201
        assert data1 == r2.json()

    def test_intervention_idempotency_rejects_payload_mismatch(self, target_case):
        headers = get_auth_headers()
        idem_key = f"key-{uuid.uuid4().hex}"
        headers["Idempotency-Key"] = idem_key

        payload1 = {
            "case_id": target_case,
            "intervention_type": "COUNSELLING",
            "status": "PENDING",
            "assigned_to": "Test"
        }
        r1 = client.post("/api/v1/interventions", json=payload1, headers=headers)
        assert r1.status_code == 201

        payload2 = {
            "case_id": target_case,
            "intervention_type": "LEGAL_AID",
            "status": "PENDING",
            "assigned_to": "Test"
        }
        r2 = client.post("/api/v1/interventions", json=payload2, headers=headers)
        assert r2.status_code == 409
        assert "previously used with a different payload" in r2.text

    def test_outcome_idempotency(self, target_case):
        headers = get_auth_headers()
        idem_key = f"key-{uuid.uuid4().hex}"
        headers["Idempotency-Key"] = idem_key
        
        payload1 = {
            "case_id": target_case,
            "outcome_type": "RESOLVED",
            "completed": True
        }
        r1 = client.post("/api/v1/outcomes", json=payload1, headers=headers)
        assert r1.status_code == 201
        data1 = r1.json()

        r2 = client.post("/api/v1/outcomes", json=payload1, headers=headers)
        assert r2.status_code == 201
        assert data1 == r2.json()

    def test_voice_upload_idempotency(self, target_case, tmp_path):
        # We need an interaction first with voice consent
        db = TestingSessionLocal()
        try:
            from backend.models import Interaction, Consent
            # add consent
            consent = Consent(case_id=target_case, voice_analysis_consent=True)
            db.add(consent)
            # add interaction
            from datetime import datetime
            interaction = Interaction(case_id=target_case, interaction_date=datetime.utcnow(), channel="voice", language="en")
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            interaction_id = interaction.id
        finally:
            db.close()

        headers = get_auth_headers("USER")
        idem_key = f"key-{uuid.uuid4().hex}"
        headers["Idempotency-Key"] = idem_key

        import wave
        def create_wav(file_path):
            with wave.open(str(file_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(8000)
                wav.writeframes(b"\x00\x00" * 16000)

        wav_path1 = tmp_path / "test1.wav"
        create_wav(wav_path1)

        with open(wav_path1, "rb") as f1:
            r1 = client.post(
                f"/api/v1/interactions/{interaction_id}/voice",
                files={"file": ("test1.wav", f1, "audio/wav")},
                headers=headers
            )
        assert r1.status_code == 202
        data1 = r1.json()

        # Same file retry
        with open(wav_path1, "rb") as f1_retry:
            r2 = client.post(
                f"/api/v1/interactions/{interaction_id}/voice",
                files={"file": ("test1.wav", f1_retry, "audio/wav")},
                headers=headers
            )
        assert r2.status_code == 202
        assert data1 == r2.json()

        db = TestingSessionLocal()
        record = db.query(IdempotencyRecord).filter(IdempotencyRecord.idempotency_key == idem_key).first()
        assert record is not None
        assert record.response_status == 202
        db.close()

        # Different file, same key -> 409
        wav_path2 = tmp_path / "test2.wav"
        create_wav(wav_path2)
        # We'll just write an extra frame to make it different
        with open(wav_path2, "ab") as f_app:
            f_app.write(b"\x00\x00")
            
        with open(wav_path2, "rb") as f2:
            r3 = client.post(
                f"/api/v1/interactions/{interaction_id}/voice",
                files={"file": ("test2.wav", f2, "audio/wav")},
                headers=headers
            )
        assert r3.status_code == 409
