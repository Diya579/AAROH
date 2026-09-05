"""
AAROH — Scope Isolation Tests

Proves that cross-scope data access is impossible for collection endpoints and analytics.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

from backend.main import app
from backend.database import Base
from backend.models import Case, Interaction, Prediction, Intervention, Outcome, CaseEvent
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
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[cases_get_db] = override_get_db
    app.dependency_overrides[analytics_get_db] = override_get_db
    # Also override for interactions, events, predictions, interventions
    from backend.api.v1.interactions import get_db as interactions_get_db
    from backend.api.v1.events import get_db as events_get_db
    from backend.api.v1.predictions import get_db as predictions_get_db
    from backend.api.v1.interventions import get_db as interventions_get_db
    app.dependency_overrides[interactions_get_db] = override_get_db
    app.dependency_overrides[events_get_db] = override_get_db
    app.dependency_overrides[predictions_get_db] = override_get_db
    app.dependency_overrides[interventions_get_db] = override_get_db
    yield
    app.dependency_overrides.pop(cases_get_db, None)
    app.dependency_overrides.pop(analytics_get_db, None)
    app.dependency_overrides.pop(interactions_get_db, None)
    app.dependency_overrides.pop(events_get_db, None)
    app.dependency_overrides.pop(predictions_get_db, None)
    app.dependency_overrides.pop(interventions_get_db, None)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def seeded_data():
    db = TestingSessionLocal()
    try:
        uid1 = f"ISO-{uuid.uuid4().hex[:8]}"
        uid2 = f"ISO-{uuid.uuid4().hex[:8]}"

        # Case 1: Maharashtra, Pune
        c1 = Case(
            case_id=uid1, language="en", district_type="urban",
            district="Pune", state="Maharashtra",
            priority_use_case="dv", current_stage="active",
        )
        # Case 2: Gujarat, Ahmedabad
        c2 = Case(
            case_id=uid2, language="en", district_type="urban",
            district="Ahmedabad", state="Gujarat",
            priority_use_case="dv", current_stage="active",
        )
        db.add_all([c1, c2])
        db.commit()
        db.refresh(c1); db.refresh(c2)

        # Add child resources
        i1 = Interaction(case_id=c1.id, interaction_date=datetime.utcnow(), channel="voice", language="en")
        i2 = Interaction(case_id=c2.id, interaction_date=datetime.utcnow(), channel="text", language="en")
        
        inv1 = Intervention(case_id=c1.id, intervention_type="ROUTINE", status="PENDING", assigned_to="Couns-1")
        inv2 = Intervention(case_id=c2.id, intervention_type="EMERGENCY", status="PENDING", assigned_to="Couns-2")
        
        db.add_all([i1, i2, inv1, inv2])
        db.commit()

        return {
            "c1_db_id": c1.id, "c2_db_id": c2.id,
            "c1_case_id": uid1, "c2_case_id": uid2,
            "c1_state": "Maharashtra", "c2_state": "Gujarat",
            "c1_district": "Pune", "c2_district": "Ahmedabad",
        }
    finally:
        db.close()

def _as_role(role: str, user_id="test", state=None, district=None):
    user = AuthenticatedUser(id=user_id, role=role, state=state, district=district)
    app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(user)

def _restore_admin():
    from backend.tests.conftest import get_admin_provider
    app.dependency_overrides[get_auth_provider] = get_admin_provider

class TestStateOfficialScopeIsolation:
    def test_can_access_own_state(self, seeded_data):
        _as_role("STATE_OFFICIAL", state=seeded_data["c1_state"])
        r = client.get("/api/v1/cases")
        _restore_admin()
        assert r.status_code == 200
        cases = r.json()
        assert len(cases) == 1
        assert cases[0]["state"] == seeded_data["c1_state"]

    def test_cannot_access_other_state_via_query_param(self, seeded_data):
        _as_role("STATE_OFFICIAL", state=seeded_data["c1_state"])
        # Attempts to fetch Gujarat cases while authenticated as Maharashtra
        r = client.get(f"/api/v1/cases?state={seeded_data['c2_state']}")
        _restore_admin()
        assert r.status_code == 200
        cases = r.json()
        assert len(cases) == 0  # Intersection of scopes should be empty

    def test_cannot_access_other_state_analytics(self, seeded_data):
        _as_role("STATE_OFFICIAL", state=seeded_data["c1_state"])
        r = client.get(f"/api/v1/analytics/state/{seeded_data['c2_state']}")
        _restore_admin()
        assert r.status_code == 403

class TestDistrictOfficialScopeIsolation:
    def test_can_access_own_district(self, seeded_data):
        _as_role("DISTRICT_OFFICIAL", district=seeded_data["c1_district"])
        r = client.get("/api/v1/cases")
        _restore_admin()
        assert r.status_code == 200
        cases = r.json()
        assert len(cases) == 1
        assert cases[0]["district"] == seeded_data["c1_district"]

    def test_cannot_access_other_district_via_query_param(self, seeded_data):
        _as_role("DISTRICT_OFFICIAL", district=seeded_data["c1_district"])
        r = client.get(f"/api/v1/cases?district={seeded_data['c2_district']}")
        _restore_admin()
        assert r.status_code == 200
        cases = r.json()
        assert len(cases) == 0

class TestCounsellorScopeIsolation:
    def test_can_access_assigned_case_interactions(self, seeded_data):
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.get("/api/v1/interactions")
        _restore_admin()
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["case_id"] == seeded_data["c1_db_id"]

    def test_cannot_access_unassigned_case_interactions(self, seeded_data):
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.get(f"/api/v1/interactions?case_id={seeded_data['c2_db_id']}")
        _restore_admin()
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 0

class TestVictimScopeIsolation:
    def test_can_access_own_case(self, seeded_data):
        """VICTIM role should be able to access their own case."""
        _as_role("VICTIM", user_id=seeded_data["c1_case_id"])
        
        # Accessing c1 (which belongs to c1_case_id)
        r = client.get(f"/api/v1/cases/{seeded_data['c1_db_id']}")
        _restore_admin()
        
        assert r.status_code == 200
        data = r.json()
        assert data["case_id"] == seeded_data["c1_case_id"]

    def test_cannot_access_other_case(self, seeded_data):
        """VICTIM role should be blocked from accessing a different case."""
        _as_role("VICTIM", user_id=seeded_data["c1_case_id"])
        
        # Accessing c2 (which belongs to c2_case_id)
        r = client.get(f"/api/v1/cases/{seeded_data['c2_db_id']}")
        _restore_admin()
        
        # 403 Forbidden is expected from verify_case_id_access
        assert r.status_code == 403

class TestMockRoleIsolation:
    def test_mock_role_header_ignored(self, seeded_data):
        # Even if client sends X-Mock-Role, the AuthProvider (FakeAuthProvider here)
        # dictates the role.
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.delete(f"/api/v1/cases/{seeded_data['c1_db_id']}", headers={"X-Mock-Role": "ADMIN"})
        _restore_admin()
        assert r.status_code == 403
