"""
AAROH — RBAC Row-Level Tests

Proves that roles are properly restricted based on resource attributes.
Each test class uses a specific non-ADMIN FakeAuthProvider role.

Test matrix:
  - VICTIM:            can access own case / cannot access another person's case
  - DISTRICT_OFFICIAL: can access own district's case / cannot access another district's case
  - COUNSELLOR:        can access assigned case / cannot access unassigned case
  - COUNSELLOR role:   rejected from ADMIN-only delete endpoint (403)
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base
from backend.models import Case, Intervention
from backend.core.auth_provider import FakeAuthProvider, AuthenticatedUser
from backend.core.security import get_auth_provider
from backend.api.v1.cases import get_db

# ---------------------------------------------------------------------------
# Isolated in-memory DB for this module
# ---------------------------------------------------------------------------

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
def setup_rbac_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Module-scoped shared fixture — created once, reused by all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def seeded_cases():
    """
    Create two cases in two different districts, and one Intervention
    assigning counsellor 'Couns-1' only to case 1.

    Returns:
        (victim1_case_id, victim2_case_id, db_case1_id, db_case2_id)
    """
    # Use unique string IDs so this module's fixture never clashes
    uid1 = f"RBAC-V1-{uuid.uuid4().hex[:8]}"
    uid2 = f"RBAC-V2-{uuid.uuid4().hex[:8]}"

    db = TestingSessionLocal()
    try:
        c1 = Case(
            case_id=uid1,
            language="en",
            district_type="urban",
            district="Pune",
            priority_use_case="dv",
            current_stage="active",
        )
        c2 = Case(
            case_id=uid2,
            language="en",
            district_type="rural",
            district="Mumbai",
            priority_use_case="dv",
            current_stage="active",
        )
        db.add_all([c1, c2])
        db.commit()
        db.refresh(c1)
        db.refresh(c2)

        # Counsellor-1 is assigned to Case 1 only
        inv = Intervention(
            case_id=c1.id,
            intervention_type="ROUTINE_MONITORING",
            status="PENDING",
            assigned_to="Couns-1",
        )
        db.add(inv)
        db.commit()

        return uid1, uid2, c1.id, c2.id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Auth helper: override for one test, then restore global ADMIN override
# ---------------------------------------------------------------------------

def _as_role(role: str, *, user_id: str = "test-user", district: str = None):
    """Temporarily set the auth provider to the given role."""
    user = AuthenticatedUser(id=user_id, role=role, district=district)
    app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(user)


def _restore_admin():
    """Restore the global ADMIN override (from conftest)."""
    from backend.tests.conftest import get_admin_provider
    app.dependency_overrides[get_auth_provider] = get_admin_provider


# ---------------------------------------------------------------------------
# VICTIM / USER row-level tests
# ---------------------------------------------------------------------------

class TestVictimRBAC:

    def test_victim_can_access_own_case(self, seeded_cases):
        victim1_case_id, _, db_case1_id, _ = seeded_cases
        _as_role("VICTIM", user_id=victim1_case_id)
        r = client.get(f"/api/v1/cases/{db_case1_id}")
        _restore_admin()
        assert r.status_code == 200, r.text

    def test_victim_cannot_access_another_persons_case(self, seeded_cases):
        victim1_case_id, _, _, db_case2_id = seeded_cases
        _as_role("VICTIM", user_id=victim1_case_id)   # victim1 tries to GET victim2's case
        r = client.get(f"/api/v1/cases/{db_case2_id}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "another person's case" in r.json()["error"]["message"]


# ---------------------------------------------------------------------------
# DISTRICT_OFFICIAL row-level tests
# ---------------------------------------------------------------------------

class TestDistrictOfficialRBAC:

    def test_official_can_access_own_district_case(self, seeded_cases):
        _, _, db_case1_id, _ = seeded_cases   # Case 1 is in Pune
        _as_role("DISTRICT_OFFICIAL", district="Pune")
        r = client.get(f"/api/v1/cases/{db_case1_id}")
        _restore_admin()
        assert r.status_code == 200, r.text

    def test_official_cannot_access_other_district_case(self, seeded_cases):
        _, _, _, db_case2_id = seeded_cases   # Case 2 is in Mumbai
        _as_role("DISTRICT_OFFICIAL", district="Pune")  # Official is from Pune
        r = client.get(f"/api/v1/cases/{db_case2_id}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "outside district: Pune" in r.json()["error"]["message"]


# ---------------------------------------------------------------------------
# COUNSELLOR row-level tests
# ---------------------------------------------------------------------------

class TestCounsellorRBAC:

    def test_counsellor_can_access_assigned_case(self, seeded_cases):
        _, _, db_case1_id, _ = seeded_cases   # Couns-1 is assigned to Case 1
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.get(f"/api/v1/cases/{db_case1_id}")
        _restore_admin()
        assert r.status_code == 200, r.text

    def test_counsellor_cannot_access_unassigned_case(self, seeded_cases):
        _, _, _, db_case2_id = seeded_cases   # Couns-1 has no assignment to Case 2
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.get(f"/api/v1/cases/{db_case2_id}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "not assigned" in r.json()["error"]["message"]


# ---------------------------------------------------------------------------
# Admin-only endpoint boundary tests
# ---------------------------------------------------------------------------

class TestAdminOnlyBoundary:

    def test_counsellor_rejected_from_admin_only_delete(self, seeded_cases):
        _, _, db_case1_id, _ = seeded_cases
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.delete(f"/api/v1/cases/{db_case1_id}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "Insufficient permissions" in r.json()["error"]["message"]

    def test_victim_rejected_from_admin_only_delete(self, seeded_cases):
        victim1_case_id, _, db_case1_id, _ = seeded_cases
        _as_role("VICTIM", user_id=victim1_case_id)
        r = client.delete(f"/api/v1/cases/{db_case1_id}")
        _restore_admin()
        assert r.status_code == 403, r.text

    def test_district_official_rejected_from_admin_only_delete(self, seeded_cases):
        _, _, db_case1_id, _ = seeded_cases
        _as_role("DISTRICT_OFFICIAL", district="Pune")
        r = client.delete(f"/api/v1/cases/{db_case1_id}")
        _restore_admin()
        assert r.status_code == 403, r.text

    def test_prediction_create_restricted_to_system_service_and_admin(self, seeded_cases):
        """POST /predictions is SYSTEM_SERVICE|ADMIN only — verify COUNSELLOR is rejected."""
        _, _, db_case1_id, _ = seeded_cases
        _as_role("COUNSELLOR", user_id="Couns-1")
        from datetime import datetime
        payload = {
            "case_id": db_case1_id,
            "prediction_date": datetime.utcnow().isoformat(),
            "escalation_probability": 0.5,
            "target_horizon_days": 7,
            "confidence": 0.8,
            "risk_level": "MEDIUM",
            "explanation": {}
        }
        r = client.post("/api/v1/predictions", json=payload)
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "Insufficient permissions" in r.json()["error"]["message"]
