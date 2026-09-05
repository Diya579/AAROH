"""
AAROH — Analytics API Tests

Verifies aggregate counts endpoints:
  - Role-based access (403 for wrong roles)
  - Response structure correctness
  - Per-case, district, state, and national aggregates
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base
from backend.models import Case, Interaction, Prediction
from backend.core.auth_provider import FakeAuthProvider, AuthenticatedUser
from backend.core.security import get_auth_provider
from backend.api.v1.cases import get_db as cases_get_db
from backend.api.v1.analytics import get_db as analytics_get_db

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
def setup_analytics_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[cases_get_db] = override_get_db
    app.dependency_overrides[analytics_get_db] = override_get_db
    yield
    app.dependency_overrides.pop(cases_get_db, None)
    app.dependency_overrides.pop(analytics_get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def seeded_analytics():
    db = TestingSessionLocal()
    try:
        c1 = Case(
            case_id=f"ANA-{uuid.uuid4().hex[:8]}",
            language="en", district_type="urban",
            district="Pune", state="Maharashtra",
            priority_use_case="dv", current_stage="active",
        )
        c2 = Case(
            case_id=f"ANA-{uuid.uuid4().hex[:8]}",
            language="en", district_type="rural",
            district="Nagpur", state="Maharashtra",
            priority_use_case="dv", current_stage="active",
        )
        db.add_all([c1, c2])
        db.commit()
        db.refresh(c1); db.refresh(c2)

        from datetime import datetime
        i = Interaction(
            case_id=c1.id, interaction_date=datetime.utcnow(),
            channel="voice", language="en",
        )
        p = Prediction(
            case_id=c1.id, prediction_date=datetime.utcnow(),
            escalation_probability=0.5, confidence=0.8, target_horizon_days=7,
            risk_level="MEDIUM",
        )
        db.add_all([i, p])
        db.commit()

        return {"c1_id": c1.id, "c2_id": c2.id, "district": "Pune", "state": "Maharashtra"}
    finally:
        db.close()


def _as_role(role, *, state=None, district=None):
    user = AuthenticatedUser(id="test", role=role, state=state, district=district)
    app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(user)


def _restore_admin():
    from backend.tests.conftest import get_admin_provider
    app.dependency_overrides[get_auth_provider] = get_admin_provider


class TestAnalyticsCasesSummary:

    def test_admin_can_access_cases_summary(self, seeded_analytics):
        r = client.get("/api/v1/analytics/cases")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "totals" in body
        assert "by_district" in body
        assert "by_state" in body

    def test_counsellor_rejected_from_cases_summary(self, seeded_analytics):
        _as_role("COUNSELLOR")
        r = client.get("/api/v1/analytics/cases")
        _restore_admin()
        assert r.status_code == 403

    def test_totals_are_non_negative(self, seeded_analytics):
        r = client.get("/api/v1/analytics/cases")
        totals = r.json()["totals"]
        for key, val in totals.items():
            assert val >= 0, f"Negative total for {key}"


class TestAnalyticsCaseDetail:

    def test_per_case_returns_counts(self, seeded_analytics):
        c1_id = seeded_analytics["c1_id"]
        r = client.get(f"/api/v1/analytics/cases/{c1_id}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["case_id"] == c1_id
        assert "counts" in body
        # Should have at least 1 interaction and 1 prediction seeded
        assert body["counts"]["interactions"] >= 1
        assert body["counts"]["predictions"] >= 1

    def test_per_case_missing_returns_404(self, seeded_analytics):
        r = client.get("/api/v1/analytics/cases/99999")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "CASE_NOT_FOUND"

    def test_district_official_can_access_per_case(self, seeded_analytics):
        _as_role("DISTRICT_OFFICIAL", district="Pune")
        r = client.get(f"/api/v1/analytics/cases/{seeded_analytics['c1_id']}")
        _restore_admin()
        assert r.status_code == 200


class TestAnalyticsDistrict:

    def test_district_aggregate_returns_counts(self, seeded_analytics):
        _as_role("DISTRICT_OFFICIAL", district="Pune")
        r = client.get(f"/api/v1/analytics/district/{seeded_analytics['district']}")
        _restore_admin()
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["district"] == "Pune"
        assert body["total_cases"] >= 1

    def test_counsellor_rejected_from_district_analytics(self, seeded_analytics):
        _as_role("COUNSELLOR")
        r = client.get(f"/api/v1/analytics/district/{seeded_analytics['district']}")
        _restore_admin()
        assert r.status_code == 403

    def test_empty_district_returns_zero(self, seeded_analytics):
        r = client.get("/api/v1/analytics/district/NonexistentDistrict")
        assert r.status_code == 200
        assert r.json()["total_cases"] == 0


class TestAnalyticsState:

    def test_state_aggregate_returns_counts(self, seeded_analytics):
        _as_role("STATE_OFFICIAL", state="Maharashtra")
        r = client.get(f"/api/v1/analytics/state/{seeded_analytics['state']}")
        _restore_admin()
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["state"] == "Maharashtra"
        assert body["total_cases"] >= 2

    def test_district_official_rejected_from_state_analytics(self, seeded_analytics):
        _as_role("DISTRICT_OFFICIAL", district="Pune")
        r = client.get(f"/api/v1/analytics/state/{seeded_analytics['state']}")
        _restore_admin()
        assert r.status_code == 403


class TestAnalyticsNational:

    def test_national_aggregate_accessible_to_admin(self, seeded_analytics):
        r = client.get("/api/v1/analytics/national")
        assert r.status_code == 200
        body = r.json()
        assert body["scope"] == "national"
        assert "totals" in body

    def test_state_official_rejected_from_national(self, seeded_analytics):
        _as_role("STATE_OFFICIAL", state="Maharashtra")
        r = client.get("/api/v1/analytics/national")
        _restore_admin()
        assert r.status_code == 403
