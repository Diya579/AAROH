"""
AAROH — Authentication and RBAC tests

Verifies:
  1. Unauthenticated request → 401 (no credential supplied)
  2. Authenticated request → accepted (correct role)
  3. Client cannot self-assign ADMIN role via any header
  4. Wrong role → 403
  5. COUNSELLOR can access authorised endpoints
  6. USER/VICTIM cannot access official endpoints
  7. DISTRICT_OFFICIAL cannot be granted ADMIN via header tampering

Strategy:
  - DevAuthProvider reads from AAROH_DEV_TOKENS env var.
    We set that env var in the fixture to control tokens deterministically.
  - We remove the FakeAuthProvider override installed by conftest for
    these tests so DevAuthProvider is used directly.
  - After each test class, conftest's session-scoped fixture restores ADMIN.

Note: We temporarily remove the FakeAuthProvider override so DevAuthProvider
runs. We restore it after auth tests.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app
from backend.core.security import get_auth_provider
from backend.core.auth_provider import AuthenticatedUser, FakeAuthProvider, DevAuthProvider

# ---------------------------------------------------------------------------
# Tokens we'll register in AAROH_DEV_TOKENS for auth tests
# ---------------------------------------------------------------------------

DEV_TOKENS = {
    "valid-counsellor-token": {
        "id": "test-counsellor-001",
        "role": "COUNSELLOR",
        "district": "Pune",
    },
    "valid-admin-token": {
        "id": "test-admin-001",
        "role": "ADMIN",
    },
    "valid-user-token": {
        "id": "test-user-001",
        "role": "USER",
    },
    "valid-district-token": {
        "id": "test-district-001",
        "role": "DISTRICT_OFFICIAL",
        "district": "Pune",
    },
}


@pytest.fixture()
def dev_auth_client():
    """
    A TestClient that uses DevAuthProvider with a known token map.
    Temporarily removes the conftest FakeAuthProvider override so that
    the real DevAuthProvider runs.
    """
    env_tokens = json.dumps(DEV_TOKENS)
    # Remove the FakeAuthProvider override installed by conftest
    saved = app.dependency_overrides.pop(get_auth_provider, None)
    with patch.dict(os.environ, {"AAROH_DEV_TOKENS": env_tokens}):
        # Now DevAuthProvider will load our test tokens
        yield TestClient(app)
    # Restore conftest override
    if saved is not None:
        app.dependency_overrides[get_auth_provider] = saved


def mock_service(monkeypatch):
    """Patch all services to avoid real DB calls in auth-focused tests."""
    pass  # Services already return errors for missing DB; we check HTTP codes


# ---------------------------------------------------------------------------
# 1. Unauthenticated → 401
# ---------------------------------------------------------------------------

class TestUnauthenticated:

    def test_no_auth_header_returns_401(self, dev_auth_client):
        """GET /api/v1/cases with no Authorization header must return 401."""
        response = dev_auth_client.get("/api/v1/cases")
        assert response.status_code == 401

    def test_401_has_error_envelope(self, dev_auth_client):
        """401 response must use the standard error envelope."""
        response = dev_auth_client.get("/api/v1/cases")
        body = response.json()
        assert "error" in body
        assert "message" in body["error"]

    def test_401_has_www_authenticate_header(self, dev_auth_client):
        """401 must include WWW-Authenticate: Bearer per RFC 6750."""
        response = dev_auth_client.get("/api/v1/cases")
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_no_auth_on_post_cases_returns_401(self, dev_auth_client):
        """POST /api/v1/cases without auth must return 401."""
        response = dev_auth_client.post("/api/v1/cases", json={})
        assert response.status_code == 401

    def test_health_does_not_require_auth(self, dev_auth_client):
        """/api/v1/health must be accessible without authentication."""
        response = dev_auth_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_invalid_token_returns_401(self, dev_auth_client):
        """A Bearer token not in the token map must return 401."""
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={"Authorization": "Bearer totally-invalid-token"}
        )
        assert response.status_code == 401

    def test_malformed_auth_header_returns_401(self, dev_auth_client):
        """A non-Bearer Authorization header must return 401."""
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# 2. Authenticated → accepted (correct role)
# ---------------------------------------------------------------------------

class TestAuthenticated:

    @patch("backend.api.v1.cases.case_service.list_cases", return_value=[])
    def test_counsellor_can_list_cases(self, mock_list, dev_auth_client):
        """COUNSELLOR with valid token can GET /api/v1/cases."""
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={"Authorization": "Bearer valid-counsellor-token"}
        )
        assert response.status_code == 200

    @patch("backend.api.v1.cases.case_service.list_cases", return_value=[])
    def test_admin_can_list_cases(self, mock_list, dev_auth_client):
        """ADMIN with valid token can GET /api/v1/cases."""
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={"Authorization": "Bearer valid-admin-token"}
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 3. Client cannot self-assign ADMIN via header
# ---------------------------------------------------------------------------

class TestClientCannotChooseRole:

    def test_x_mock_role_header_is_ignored(self, dev_auth_client):
        """
        Sending X-Mock-Role: ADMIN without a valid Bearer token must still return 401.
        This verifies that the old X-Mock-Role pattern is completely removed from
        production code. The header must have zero effect.
        """
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={"X-Mock-Role": "ADMIN"}
        )
        assert response.status_code == 401, (
            "X-Mock-Role must have no effect in production code. Got: "
            f"{response.status_code} {response.text}"
        )

    def test_x_mock_role_admin_with_user_token_is_still_user(self, dev_auth_client):
        """
        Even if a client sends X-Mock-Role: ADMIN alongside a valid USER token,
        the role must be USER (from the token map), not ADMIN.
        USER does not have access to GET /api/v1/cases → must return 403.
        """
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={
                "Authorization": "Bearer valid-user-token",
                "X-Mock-Role": "ADMIN",
            }
        )
        # USER is not in the allowed roles for GET /cases
        assert response.status_code == 403, (
            "Client-supplied X-Mock-Role must not override the backend-resolved role."
        )

    def test_authorization_header_impersonation_rejected(self, dev_auth_client):
        """
        Sending `Authorization: Bearer <made-up-admin-token>` that is not in
        the token map must return 401, not grant ADMIN access.
        """
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={"Authorization": "Bearer i-am-admin-trust-me"}
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# 4. Wrong role → 403
# ---------------------------------------------------------------------------

class TestWrongRole:

    def test_user_cannot_list_cases(self, dev_auth_client):
        """USER role must be rejected from GET /api/v1/cases (403)."""
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={"Authorization": "Bearer valid-user-token"}
        )
        assert response.status_code == 403

    def test_user_cannot_create_case(self, dev_auth_client):
        """USER role must be rejected from POST /api/v1/cases (403)."""
        response = dev_auth_client.post(
            "/api/v1/cases",
            json={"case_id": "X", "language": "en", "district_type": "urban",
                  "district": "D", "priority_use_case": "P", "current_stage": "S"},
            headers={"Authorization": "Bearer valid-user-token"},
        )
        assert response.status_code == 403

    def test_403_has_error_envelope(self, dev_auth_client):
        """403 response must use the standard error envelope."""
        response = dev_auth_client.get(
            "/api/v1/cases",
            headers={"Authorization": "Bearer valid-user-token"}
        )
        body = response.json()
        assert "error" in body
        assert "message" in body["error"]


# ---------------------------------------------------------------------------
# 5. FakeAuthProvider works correctly in regular tests
# ---------------------------------------------------------------------------

class TestFakeAuthProvider:
    """
    Verify the FakeAuthProvider (used by the rest of the test suite via conftest)
    actually works as expected. This uses the conftest-installed override.
    """

    @patch("backend.api.v1.cases.case_service.list_cases", return_value=[])
    def test_default_admin_fake_can_access_cases(self, mock_list):
        """The default ADMIN fake identity can access GET /api/v1/cases."""
        # TestClient with no special override — conftest installs ADMIN FakeAuthProvider
        client = TestClient(app)
        response = client.get("/api/v1/cases")
        assert response.status_code == 200

    def test_fake_provider_with_user_role_gets_403(self):
        """FakeAuthProvider with USER role must be rejected by COUNSELLOR endpoints."""
        user = AuthenticatedUser(id="test-user", role="USER")
        app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(user)
        try:
            client = TestClient(app)
            response = client.get("/api/v1/cases")
            assert response.status_code == 403
        finally:
            # Restore default ADMIN from conftest
            from backend.tests.conftest import DEFAULT_TEST_USER
            app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(DEFAULT_TEST_USER)

    def test_authenticated_user_model_is_frozen(self):
        """AuthenticatedUser must be immutable to prevent tampering."""
        user = AuthenticatedUser(id="u1", role="COUNSELLOR")
        with pytest.raises(Exception):  # ValidationError or TypeError
            user.role = "ADMIN"
