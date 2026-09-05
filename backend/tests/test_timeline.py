"""
AAROH — Timeline Tests

Verifies that GET /cases/{id}/timeline returns:
  - real DB records from CaseEvent, Interaction, Prediction, Intervention, Outcome
  - items sorted chronologically
  - 404 for missing case
"""

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base
from backend.models import Case, CaseEvent, Interaction, Prediction, Intervention, Outcome
from backend.api.v1.cases import get_db

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


@pytest.fixture(autouse=True, scope="module")
def setup_timeline_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def timeline_case():
    """Seed one case with one of each record type."""
    uid = f"TL-{uuid.uuid4().hex[:8]}"
    now = datetime(2026, 1, 1, 12, 0, 0)

    db = TestingSessionLocal()
    try:
        case = Case(
            case_id=uid,
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

        event = CaseEvent(
            case_id=case.id,
            event_date=now,
            event_type="STAGE_CHANGE",
            description="Case opened",
            case_stage="active",
        )
        interaction = Interaction(
            case_id=case.id,
            interaction_date=now + timedelta(hours=1),
            channel="voice",
            language="en",
            voice_available=True,
            response_completed=True,
        )
        prediction = Prediction(
            case_id=case.id,
            prediction_date=now + timedelta(hours=2),
            escalation_probability=0.72,
            risk_level="HIGH",
            confidence=0.88,
            target_horizon_days=7,
        )
        intervention = Intervention(
            case_id=case.id,
            intervention_type="SAFE_HOUSE_REFERRAL",
            status="PENDING",
            assigned_to="Couns-1",
            created_at=now + timedelta(hours=2, minutes=30),
        )
        db.add_all([event, interaction, prediction, intervention])
        db.commit()
        db.refresh(intervention)

        outcome = Outcome(
            case_id=case.id,
            intervention_id=intervention.id,
            outcome_type="RELOCATED",
            completed=True,
            recorded_at=now + timedelta(hours=3),
        )
        db.add(outcome)
        db.commit()

        return case.id
    finally:
        db.close()


class TestTimeline:

    def test_timeline_returns_200(self, timeline_case):
        r = client.get(f"/api/v1/cases/{timeline_case}/timeline")
        assert r.status_code == 200, r.text

    def test_timeline_has_correct_count(self, timeline_case):
        r = client.get(f"/api/v1/cases/{timeline_case}/timeline")
        data = r.json()
        # 1 event + 1 interaction + 1 prediction + 1 intervention + 1 outcome = 5
        assert data["count"] == 5, f"Expected 5 timeline items, got {data['count']}: {data['timeline']}"

    def test_timeline_contains_all_record_types(self, timeline_case):
        r = client.get(f"/api/v1/cases/{timeline_case}/timeline")
        types = {item["type"] for item in r.json()["timeline"]}
        assert "case_event" in types
        assert "interaction" in types
        assert "prediction" in types
        assert "intervention" in types
        assert "outcome" in types

    def test_timeline_is_sorted_chronologically(self, timeline_case):
        r = client.get(f"/api/v1/cases/{timeline_case}/timeline")
        items = r.json()["timeline"]
        timestamps = [i["timestamp"] for i in items]
        assert timestamps == sorted(timestamps), "Timeline is not sorted chronologically"
        assert None not in timestamps, "All timeline items should now have a timestamp"

    def test_timeline_missing_case_returns_404(self):
        r = client.get("/api/v1/cases/99999/timeline")
        assert r.status_code == 404
        body = r.json()
        assert "error" in body
        assert body["error"]["code"] == "CASE_NOT_FOUND"

    def test_timeline_prediction_fields_present(self, timeline_case):
        r = client.get(f"/api/v1/cases/{timeline_case}/timeline")
        predictions = [i for i in r.json()["timeline"] if i["type"] == "prediction"]
        assert len(predictions) == 1
        p = predictions[0]
        assert p["risk_level"] == "HIGH"
        assert p["escalation_probability"] == pytest.approx(0.72, abs=0.001)
