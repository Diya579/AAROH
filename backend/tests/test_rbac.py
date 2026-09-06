"""
AAROH — RBAC Row-Level Tests

Proves that roles are properly restricted based on resource attributes.
Each test class uses a specific non-ADMIN FakeAuthProvider role.

Test matrix:
  - VICTIM:            can access own case / cannot access another person's case
  - DISTRICT_OFFICIAL: can access own district's case / cannot access another district's case
  - STATE_OFFICIAL:    can access own state's case / cannot access another state's case
  - COUNSELLOR:        can access assigned case / cannot access unassigned case
  - NATIONAL_OFFICIAL: can access any case (no state/district restriction)
  - Non-ADMIN:         rejected from ADMIN-only endpoints

Identifier field correctness:
  - Case.id       is the Integer PK used by Intervention.case_id FK
  - Case.case_id  is the String human-readable ID used for VICTIM identity check
  - These are verified in TestIdentifierFieldCorrectness to ensure they cannot
    be silently swapped (they hold different values in every row).
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
from backend.api.v1.consents import get_db as consents_get_db
from backend.api.v1.events import get_db as events_get_db
from backend.api.v1.interactions import get_db as interactions_get_db
from backend.api.v1.interventions import get_db as interventions_get_db

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
    # Wire the shared in-memory DB into every router that is tested here
    for _get_db in (get_db, consents_get_db, events_get_db,
                    interactions_get_db, interventions_get_db):
        app.dependency_overrides[_get_db] = override_get_db
    yield
    for _get_db in (get_db, consents_get_db, events_get_db,
                    interactions_get_db, interventions_get_db):
        app.dependency_overrides.pop(_get_db, None)
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Module-scoped fixture — created once, reused by all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def seeded_cases():
    """
    Creates:
      Case 1 — district=Pune, state=Maharashtra, case_id=<unique string>
      Case 2 — district=Mumbai, state=Gujarat,   case_id=<unique string>

    Also creates an Intervention assigning 'Couns-1' only to Case 1.

    Returns a dict with all identifiers needed to write unambiguous tests.
    """
    uid1 = f"RBAC-V1-{uuid.uuid4().hex[:8]}"   # Case.case_id for case 1
    uid2 = f"RBAC-V2-{uuid.uuid4().hex[:8]}"   # Case.case_id for case 2

    db = TestingSessionLocal()
    try:
        c1 = Case(
            case_id=uid1,
            language="en",
            district_type="urban",
            district="Pune",
            state="Maharashtra",
            priority_use_case="dv",
            current_stage="active",
        )
        c2 = Case(
            case_id=uid2,
            language="en",
            district_type="rural",
            district="Mumbai",
            state="Gujarat",
            priority_use_case="dv",
            current_stage="active",
        )
        db.add_all([c1, c2])
        db.commit()
        db.refresh(c1)
        db.refresh(c2)

        # Sanity check: Case.id (int PK) and Case.case_id (string) must be different types/values
        assert isinstance(c1.id, int), "Case.id must be an Integer PK"
        assert isinstance(c1.case_id, str), "Case.case_id must be a String"
        assert str(c1.id) != c1.case_id, (
            f"Case.id={c1.id!r} and Case.case_id={c1.case_id!r} must not be equal — "
            "they are separate columns with different semantics."
        )

        # Counsellor-1 is assigned to Case 1 only (via Integer PK FK)
        inv = Intervention(
            case_id=c1.id,       # Integer FK → cases.id, NOT cases.case_id
            intervention_type="ROUTINE_MONITORING",
            status="PENDING",
            assigned_to="Couns-1",
        )
        db.add(inv)
        db.commit()

        return {
            "c1_db_id": c1.id,         # Integer PK
            "c2_db_id": c2.id,         # Integer PK
            "c1_case_id": uid1,         # String human-readable ID
            "c2_case_id": uid2,         # String human-readable ID
            "c1_district": "Pune",
            "c2_district": "Mumbai",
            "c1_state": "Maharashtra",
            "c2_state": "Gujarat",
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _as_role(role: str, *, user_id: str = "test-user",
             district: str = None, state: str = None):
    user = AuthenticatedUser(id=user_id, role=role,
                             district=district, state=state)
    app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(user)


def _restore_admin():
    from backend.tests.conftest import get_admin_provider
    app.dependency_overrides[get_auth_provider] = get_admin_provider


# ---------------------------------------------------------------------------
# Issue #1 — Identifier field correctness
# ---------------------------------------------------------------------------

class TestIdentifierFieldCorrectness:
    """
    Proves that Case.id (Integer PK) and Case.case_id (String) hold different
    values. This test would fail if verify_case_access swapped them.
    """

    def test_case_id_and_db_id_are_different_values(self, seeded_cases):
        """
        The Integer PK (db_id) and the human-readable string (case_id) must not
        be equal. If they were, VICTIM/COUNSELLOR checks would be indistinguishable.
        """
        c1_db_id = seeded_cases["c1_db_id"]       # e.g. 1  (int)
        c1_case_id = seeded_cases["c1_case_id"]   # e.g. "RBAC-V1-abcd1234"
        assert str(c1_db_id) != c1_case_id, (
            f"Case.id={c1_db_id} and Case.case_id={c1_case_id!r} are equal — "
            "the test fixture would be unable to detect field swaps."
        )

    def test_victim_using_db_int_id_is_rejected(self, seeded_cases):
        """
        If verify_case_access mistakenly compared Case.id (int) to user.id instead
        of Case.case_id (string), a victim claiming user_id=str(db_id) would
        incorrectly gain access. This test proves the check uses the string field.
        """
        c1_db_id = seeded_cases["c1_db_id"]
        # Victim claims identity = the numeric PK as a string (e.g. "1")
        _as_role("VICTIM", user_id=str(c1_db_id))
        r = client.get(f"/api/v1/cases/{c1_db_id}")
        _restore_admin()
        # Must be 403 — the victim's real ID is the case_id string, not the int PK
        assert r.status_code == 403, (
            f"VICTIM with user.id={str(c1_db_id)!r} (the Integer PK) should not "
            f"match Case.case_id={seeded_cases['c1_case_id']!r}. "
            "If this passes as 200, verify_case_access is comparing the wrong field."
        )

    def test_victim_using_correct_case_id_string_is_accepted(self, seeded_cases):
        """
        Victim using the correct human-readable case_id string must be accepted.
        """
        c1_db_id = seeded_cases["c1_db_id"]
        c1_case_id = seeded_cases["c1_case_id"]
        _as_role("VICTIM", user_id=c1_case_id)   # correct string field
        r = client.get(f"/api/v1/cases/{c1_db_id}")
        _restore_admin()
        assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# VICTIM / USER row-level tests
# ---------------------------------------------------------------------------

class TestVictimRBAC:

    def test_victim_can_access_own_case(self, seeded_cases):
        _as_role("VICTIM", user_id=seeded_cases["c1_case_id"])
        r = client.get(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 200, r.text

    def test_victim_cannot_access_another_persons_case(self, seeded_cases):
        # Victim 1 tries to access Case 2's endpoint
        _as_role("VICTIM", user_id=seeded_cases["c1_case_id"])
        r = client.get(f"/api/v1/cases/{seeded_cases['c2_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "another person's case" in r.json()["error"]["message"]


# ---------------------------------------------------------------------------
# DISTRICT_OFFICIAL row-level tests
# ---------------------------------------------------------------------------

class TestDistrictOfficialRBAC:

    def test_official_can_access_own_district_case(self, seeded_cases):
        _as_role("DISTRICT_OFFICIAL", district=seeded_cases["c1_district"])
        r = client.get(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 200, r.text

    def test_official_cannot_access_other_district_case(self, seeded_cases):
        # Official from Pune tries to access Mumbai case
        _as_role("DISTRICT_OFFICIAL", district=seeded_cases["c1_district"])
        r = client.get(f"/api/v1/cases/{seeded_cases['c2_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert f"outside district: {seeded_cases['c1_district']}" in r.json()["error"]["message"]


# ---------------------------------------------------------------------------
# STATE_OFFICIAL row-level tests (Issue #2)
# ---------------------------------------------------------------------------

class TestStateOfficialRBAC:

    def test_state_official_can_access_own_state_case(self, seeded_cases):
        _as_role("STATE_OFFICIAL", state=seeded_cases["c1_state"])
        r = client.get(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 200, r.text

    def test_state_official_cannot_access_other_state_case(self, seeded_cases):
        # Maharashtra official tries to access a Gujarat case
        _as_role("STATE_OFFICIAL", state=seeded_cases["c1_state"])
        r = client.get(f"/api/v1/cases/{seeded_cases['c2_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert f"outside state: {seeded_cases['c1_state']}" in r.json()["error"]["message"]

    def test_state_official_without_state_attribute_is_rejected(self, seeded_cases):
        # STATE_OFFICIAL with no state configured in identity → must fail
        _as_role("STATE_OFFICIAL", state=None)
        r = client.get(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "no state attribute" in r.json()["error"]["message"]


# ---------------------------------------------------------------------------
# NATIONAL_OFFICIAL — unscoped (national mandate)
# ---------------------------------------------------------------------------

class TestNationalOfficialRBAC:

    def test_national_official_can_access_any_state_case(self, seeded_cases):
        _as_role("NATIONAL_OFFICIAL")
        r1 = client.get(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        r2 = client.get(f"/api/v1/cases/{seeded_cases['c2_db_id']}")
        _restore_admin()
        assert r1.status_code == 200, r1.text
        assert r2.status_code == 200, r2.text


# ---------------------------------------------------------------------------
# COUNSELLOR row-level tests
# ---------------------------------------------------------------------------

class TestCounsellorRBAC:

    def test_counsellor_can_access_assigned_case(self, seeded_cases):
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.get(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 200, r.text

    def test_counsellor_cannot_access_unassigned_case(self, seeded_cases):
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.get(f"/api/v1/cases/{seeded_cases['c2_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "not assigned" in r.json()["error"]["message"]


# ---------------------------------------------------------------------------
# Admin-only endpoint boundary tests
# ---------------------------------------------------------------------------

class TestAdminOnlyBoundary:

    def test_counsellor_rejected_from_admin_only_delete(self, seeded_cases):
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.delete(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text
        assert "Insufficient permissions" in r.json()["error"]["message"]

    def test_victim_rejected_from_admin_only_delete(self, seeded_cases):
        _as_role("VICTIM", user_id=seeded_cases["c1_case_id"])
        r = client.delete(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text

    def test_district_official_rejected_from_admin_only_delete(self, seeded_cases):
        _as_role("DISTRICT_OFFICIAL", district=seeded_cases["c1_district"])
        r = client.delete(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text

    def test_state_official_rejected_from_admin_only_delete(self, seeded_cases):
        _as_role("STATE_OFFICIAL", state=seeded_cases["c1_state"])
        r = client.delete(f"/api/v1/cases/{seeded_cases['c1_db_id']}")
        _restore_admin()
        assert r.status_code == 403, r.text

    def test_prediction_create_restricted_to_system_service_and_admin(self, seeded_cases):
        """POST /predictions is SYSTEM_SERVICE|ADMIN only — verify COUNSELLOR is rejected."""
        _as_role("COUNSELLOR", user_id="Couns-1")
        from datetime import datetime
        payload = {
            "case_id": seeded_cases["c1_db_id"],
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


# ---------------------------------------------------------------------------
# End-to-end cross-scope mutation 403 tests
# Proves that verify_case_id_access blocks actual unauthorized writes
# with real role/case data — NO mocking of verify_case_id_access.
# ---------------------------------------------------------------------------

class TestMutationCrossScope:
    """
    Each test below:
      - Seeds two real cases in two different states (Maharashtra / Gujarat).
      - Authenticates as a role that legitimately OWNS case 1 (Maharashtra).
      - Attempts to WRITE to case 2 (Gujarat) through its integer PK.
      - Asserts a hard 403, proving the whole auth chain fires,
        not just the exception-handling shim.
    """

    CONSENT_PAYLOAD = {
        "monitoring_consent": True,
        "text_analysis_consent": True,
        "voice_analysis_consent": False,
        "case_linkage_consent": True,
        "safe_channel": "sms",
        "safe_time": "evening",
    }

    def test_victim_cannot_write_consent_to_another_case(self, seeded_cases):
        """VICTIM owning case 1 attempts PUT /consents/{case_2_id} — must get 403."""
        _as_role("VICTIM", user_id=seeded_cases["c1_case_id"])
        r = client.put(
            f"/api/v1/consents/{seeded_cases['c2_db_id']}",
            json=self.CONSENT_PAYLOAD,
        )
        _restore_admin()
        assert r.status_code == 403, (
            f"VICTIM for case 1 should not be able to write consent for case 2. "
            f"Got {r.status_code}: {r.text}"
        )

    def test_district_official_cannot_write_consent_to_out_of_district_case(self, seeded_cases):
        """DISTRICT_OFFICIAL from Pune attempts PUT /consents/{case_2_id} (Mumbai) — must get 403."""
        _as_role("DISTRICT_OFFICIAL", district=seeded_cases["c1_district"])
        r = client.put(
            f"/api/v1/consents/{seeded_cases['c2_db_id']}",
            json=self.CONSENT_PAYLOAD,
        )
        _restore_admin()
        assert r.status_code == 403, (
            f"DISTRICT_OFFICIAL for Pune should not write consent for a Mumbai case. "
            f"Got {r.status_code}: {r.text}"
        )

    def test_victim_cannot_create_event_on_another_case(self, seeded_cases):
        """VICTIM owning case 1 attempts POST /events for case 2 — must get 403."""
        from datetime import datetime
        _as_role("VICTIM", user_id=seeded_cases["c1_case_id"])
        r = client.post("/api/v1/events", json={
            "case_id": seeded_cases["c2_db_id"],
            "event_type": "ESCALATION",
            "event_date": datetime.utcnow().isoformat(),
            "description": "cross-scope injection attempt",
        })
        _restore_admin()
        assert r.status_code == 403, (
            f"VICTIM for case 1 must not create events on case 2. "
            f"Got {r.status_code}: {r.text}"
        )

    def test_counsellor_cannot_create_interaction_on_unassigned_case(self, seeded_cases):
        """COUNSELLOR assigned to case 1 attempts POST /interactions for case 2 — must get 403."""
        from datetime import datetime
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.post("/api/v1/interactions", json={
            "case_id": seeded_cases["c2_db_id"],
            "interaction_date": datetime.utcnow().isoformat(),
            "channel": "voice",
            "language": "en",
        })
        _restore_admin()
        assert r.status_code == 403, (
            f"COUNSELLOR assigned only to case 1 must not create interactions for case 2. "
            f"Got {r.status_code}: {r.text}"
        )

    def test_district_official_cannot_create_intervention_for_out_of_district_case(self, seeded_cases):
        """DISTRICT_OFFICIAL from Pune attempts POST /interventions for Mumbai case 2 — must get 403."""
        _as_role("DISTRICT_OFFICIAL", district=seeded_cases["c1_district"])
        r = client.post("/api/v1/interventions", json={
            "case_id": seeded_cases["c2_db_id"],
            "intervention_type": "ROUTINE_MONITORING",
            "status": "PENDING",
        })
        _restore_admin()
        assert r.status_code == 403, (
            f"DISTRICT_OFFICIAL for Pune must not create interventions on a Mumbai case. "
            f"Got {r.status_code}: {r.text}"
        )

    def test_counsellor_cannot_read_prediction_for_unassigned_case(self, seeded_cases):
        """COUNSELLOR assigned to case 1 attempts GET /predictions/{case_id} for case 2 — must get 403."""
        _as_role("COUNSELLOR", user_id="Couns-1")
        r = client.get(f"/api/v1/predictions/{seeded_cases['c2_db_id']}")
        _restore_admin()
        assert r.status_code == 403, (
            f"COUNSELLOR for case 1 must not read predictions for case 2. "
            f"Got {r.status_code}: {r.text}"
        )

    def test_victim_cannot_create_outcome_on_another_case(self, seeded_cases):
        """VICTIM owning case 1 attempts POST /outcomes for case 2 — must get 403."""
        _as_role("VICTIM", user_id=seeded_cases["c1_case_id"])
        r = client.post("/api/v1/outcomes", json={
            "case_id": seeded_cases["c2_db_id"],
            "outcome_type": "RESOLVED",
            "completed": True
        })
        _restore_admin()
        assert r.status_code == 403, (
            f"VICTIM for case 1 must not create outcomes for case 2. "
            f"Got {r.status_code}: {r.text}"
        )
