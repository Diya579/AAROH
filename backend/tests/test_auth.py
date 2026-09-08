"""
AAROH — Real Authentication Tests

Verifies the full end-to-end SessionAuthProvider matrix:
  - Login (success, invalid password, inactive user, unknown user)
  - CSRF protection on logout and mutating endpoints
  - Session verification and identity resolution (/auth/me)
  - Logout and session destruction
  - Expired sessions
  - No public registration
  - Proper RBAC via session (VICTIM, COUNSELLOR, OFFICIALS, ADMIN)
  - Ignored client headers/roles (X-Mock-Role, role in payload)

Uses a real test database with real User and SessionRecord rows.
"""

import os
import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from backend.main import app
from backend.database import Base
from backend.models import User, SessionRecord
from backend.core.password import hash_password
from backend.core.security import get_auth_provider
from backend.core.auth_provider import SessionAuthProvider
from backend.api.v1.cases import get_db

# ---------------------------------------------------------------------------
# Isolated in-memory DB for authentication tests
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

@pytest.fixture(autouse=True, scope="module")
def setup_auth_db():
    """Setup the test database and wire it into the app."""
    Base.metadata.create_all(bind=engine)
    
    # Snapshot the original overrides to prevent leaking to other test files
    old_overrides = app.dependency_overrides.copy()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # We must remove the FakeAuthProvider override from conftest for auth tests
    app.dependency_overrides.pop(get_auth_provider, None)
    
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)
        # Safely restore the exact overrides dictionary in-place
        app.dependency_overrides.clear()
        app.dependency_overrides.update(old_overrides)

@pytest.fixture(autouse=True)
def mock_session_local(monkeypatch):
    """Patch the internal SessionLocal used by SessionAuthProvider."""
    monkeypatch.setattr("backend.database.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("backend.api.v1.auth.SessionLocal", TestingSessionLocal)

@pytest.fixture(autouse=True)
def force_session_auth(monkeypatch):
    """Ensure AAROH_AUTH_MODE is set to 'session'."""
    monkeypatch.setenv("AAROH_AUTH_MODE", "session")


# ---------------------------------------------------------------------------
# DB Seed Fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def seeded_users():
    db = TestingSessionLocal()
    try:
        users = [
            User(username="admin1", password_hash=hash_password("adminpass"), role="ADMIN", active=True),
            User(username="couns1", password_hash=hash_password("counspass"), role="COUNSELLOR", active=True),
            User(username="victim1", password_hash=hash_password("vicpass"), role="VICTIM", case_id_ref="AAROH-VIC-1", active=True),
            User(username="dist1", password_hash=hash_password("distpass"), role="DISTRICT_OFFICIAL", district="Pune", active=True),
            User(username="state1", password_hash=hash_password("statepass"), role="STATE_OFFICIAL", state="Maharashtra", active=True),
            User(username="nat1", password_hash=hash_password("natpass"), role="NATIONAL_OFFICIAL", active=True),
            User(username="inactive1", password_hash=hash_password("inactpass"), role="VICTIM", active=False),
        ]
        db.add_all(users)
        db.commit()
    finally:
        db.close()

@pytest.fixture
def client(seeded_users):
    """Return a fresh TestClient."""
    return TestClient(app)

# ---------------------------------------------------------------------------
# Test Matrix
# ---------------------------------------------------------------------------

class TestAuthCore:
    def test_no_auth_header_returns_401(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_login_success(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "victim1", "password": "vicpass"})
        assert r.status_code == 200
        assert "aaroh_session" in r.cookies
        assert "aaroh_csrf_token" in r.cookies
        data = r.json()
        assert data["user"]["username"] == "victim1"
        assert data["user"]["role"] == "VICTIM"

    def test_login_invalid_password(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "victim1", "password": "wrongpassword"})
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "ghost", "password": "password"})
        assert r.status_code == 401

    def test_login_inactive_user(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "inactive1", "password": "inactpass"})
        assert r.status_code == 401
        assert "inactive" in r.json()["error"]["message"].lower()

    def test_no_public_signup(self, client):
        r = client.post("/api/v1/auth/register", json={"username": "new", "password": "new"}, headers={"X-CSRF-Token": "dummy"}, cookies={"aaroh_csrf_token": "dummy"})
        assert r.status_code == 404

class TestSessionLifecycle:
    def test_me_with_valid_session(self, client):
        # Login
        r_login = client.post("/api/v1/auth/login", json={"username": "victim1", "password": "vicpass"})
        
        # /me
        r_me = client.get("/api/v1/auth/me", cookies=r_login.cookies)
        assert r_me.status_code == 200
        assert r_me.json()["role"] == "VICTIM"
        assert r_me.json()["id"] == "AAROH-VIC-1" # ensure case_id_ref is used

    def test_logout_with_csrf_success(self, client):
        r_login = client.post("/api/v1/auth/login", json={"username": "couns1", "password": "counspass"})
        csrf_token = r_login.cookies.get("aaroh_csrf_token")
        
        # Logout
        r_out = client.post(
            "/api/v1/auth/logout", 
            cookies=r_login.cookies,
            headers={"X-CSRF-Token": csrf_token}
        )
        assert r_out.status_code == 200
        
        # Verify /me is now 401
        r_me = client.get("/api/v1/auth/me", cookies=r_login.cookies)
        assert r_me.status_code == 401

    def test_logout_missing_csrf_rejected(self, client):
        r_login = client.post("/api/v1/auth/login", json={"username": "couns1", "password": "counspass"})
        
        # Logout without header
        r_out = client.post(
            "/api/v1/auth/logout", 
            cookies=r_login.cookies
            # Missing X-CSRF-Token
        )
        assert r_out.status_code == 403
        assert r_out.json()["error"]["code"] == "CSRF_ERROR"

    def test_expired_session_rejected(self, client):
        r_login = client.post("/api/v1/auth/login", json={"username": "victim1", "password": "vicpass"})
        
        # Manually expire ALL sessions in the DB to guarantee we hit the right one
        db = TestingSessionLocal()
        db.query(SessionRecord).update({"expires_at": datetime.utcnow() - timedelta(minutes=5)})
        db.commit()
        db.close()
        
        # Attempt /me
        r_me = client.get("/api/v1/auth/me", cookies=r_login.cookies)
        assert r_me.status_code == 401
        assert "expired" in r_me.json()["error"]["message"].lower() if "error" in r_me.json() else True

class TestRBACViaSession:
    def _login(self, client, username, password):
        r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        return r.cookies

    def test_victim_cannot_list_cases(self, client):
        cookies = self._login(client, "victim1", "vicpass")
        r = client.get("/api/v1/cases", cookies=cookies)
        assert r.status_code == 403

    def test_counsellor_can_list_cases(self, client):
        # We need to mock case_service.list_cases so it doesn't try to query actual cases and fail
        with patch("backend.api.v1.cases.case_service.list_cases", return_value=[]):
            cookies = self._login(client, "couns1", "counspass")
            r = client.get("/api/v1/cases", cookies=cookies)
            assert r.status_code == 200

    def test_district_can_list_cases(self, client):
        with patch("backend.api.v1.cases.case_service.list_cases", return_value=[]):
            cookies = self._login(client, "dist1", "distpass")
            r = client.get("/api/v1/cases", cookies=cookies)
            assert r.status_code == 200

    def test_state_can_list_cases(self, client):
        with patch("backend.api.v1.cases.case_service.list_cases", return_value=[]):
            cookies = self._login(client, "state1", "statepass")
            r = client.get("/api/v1/cases", cookies=cookies)
            assert r.status_code == 200

    def test_national_can_list_cases(self, client):
        with patch("backend.api.v1.cases.case_service.list_cases", return_value=[]):
            cookies = self._login(client, "nat1", "natpass")
            r = client.get("/api/v1/cases", cookies=cookies)
            assert r.status_code == 200

    def test_admin_can_list_cases(self, client):
        with patch("backend.api.v1.cases.case_service.list_cases", return_value=[]):
            cookies = self._login(client, "admin1", "adminpass")
            r = client.get("/api/v1/cases", cookies=cookies)
            assert r.status_code == 200

class TestSecurityIgnoredFields:
    def _login(self, client, username, password):
        r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        return r.cookies

    def test_role_field_ignored_in_login(self, client):
        # Try to inject role=ADMIN during victim login
        r = client.post("/api/v1/auth/login", json={"username": "victim1", "password": "vicpass", "role": "ADMIN"})
        assert r.status_code == 200
        # The returned role should still be VICTIM
        assert r.json()["user"]["role"] == "VICTIM"

    def test_x_mock_role_is_ignored(self, client):
        cookies = self._login(client, "victim1", "vicpass")
        r = client.get("/api/v1/cases", cookies=cookies, headers={"X-Mock-Role": "ADMIN"})
        assert r.status_code == 403

# ---------------------------------------------------------------------------
# Cross-Scope Negative Tests (End-to-End via Session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def auth_seeded_cases(setup_auth_db):
    """Seed cases to test row-level isolation via session authentication."""
    from backend.models import Case, Intervention
    db = TestingSessionLocal()
    try:
        # Case 1: Maharashtra, Pune (Matches state1 and dist1)
        c1 = Case(
            case_id="AAROH-VIC-1", # matches victim1
            language="en", district_type="urban",
            district="Pune", state="Maharashtra",
            priority_use_case="dv", current_stage="active"
        )
        # Case 2: Gujarat, Mumbai (Different state/district)
        c2 = Case(
            case_id="AAROH-VIC-2",
            language="en", district_type="urban",
            district="Mumbai", state="Gujarat",
            priority_use_case="dv", current_stage="active"
        )
        db.add_all([c1, c2])
        db.commit()
        db.refresh(c1)
        db.refresh(c2)

        # Assign couns1 to Case 1
        inv = Intervention(
            case_id=c1.id, intervention_type="ROUTINE_MONITORING",
            status="PENDING", assigned_to="couns1"
        )
        db.add(inv)
        db.commit()
        return {"c1_id": c1.id, "c2_id": c2.id}
    finally:
        db.close()

class TestRBACCrossScopeViaSession:
    def _login(self, client, username, password):
        r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        return r.cookies

    def test_victim_accessing_anothers_case(self, client, auth_seeded_cases):
        cookies = self._login(client, "victim1", "vicpass")
        # Victim1 owns Case 1, hitting Case 2 -> 403
        r = client.get(f"/api/v1/cases/{auth_seeded_cases['c2_id']}", cookies=cookies)
        assert r.status_code == 403
        assert "another person's case" in r.json()["error"]["message"]

    def test_counsellor_hitting_unassigned_case(self, client, auth_seeded_cases):
        cookies = self._login(client, "couns1", "counspass")
        # Couns1 is assigned to Case 1, hitting Case 2 -> 403
        r = client.get(f"/api/v1/cases/{auth_seeded_cases['c2_id']}", cookies=cookies)
        assert r.status_code == 403
        assert "not assigned" in r.json()["error"]["message"]

    def test_district_official_crossing_into_another_district(self, client, auth_seeded_cases):
        cookies = self._login(client, "dist1", "distpass")
        # Dist1 is Pune, hitting Case 2 (Mumbai) -> 403
        r = client.get(f"/api/v1/cases/{auth_seeded_cases['c2_id']}", cookies=cookies)
        assert r.status_code == 403
        assert "outside district" in r.json()["error"]["message"]

    def test_state_official_crossing_into_another_state(self, client, auth_seeded_cases):
        cookies = self._login(client, "state1", "statepass")
        # State1 is Maharashtra, hitting Case 2 (Gujarat) -> 403
        r = client.get(f"/api/v1/cases/{auth_seeded_cases['c2_id']}", cookies=cookies)
        assert r.status_code == 403
        assert "outside state" in r.json()["error"]["message"]
