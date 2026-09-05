"""
AAROH — Shared test configuration

Installs a FakeAuthProvider override so all existing tests continue to work
after the X-Mock-Role stub was removed from production code.

The default fake identity is ADMIN so that any endpoint that the existing
unit tests hit (without caring about auth) will pass RBAC. Individual test
files or fixtures can override `get_auth_provider` again with a more
specific identity where required.

This conftest applies to every test under backend/tests/ automatically.
"""

import sys
import os

# Ensure the project root is on sys.path so that `backend.*` imports resolve.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from backend.main import app
from backend.core.security import get_auth_provider
from backend.core.auth_provider import AuthenticatedUser, FakeAuthProvider

# ---------------------------------------------------------------------------
# Default fake identity used by all tests unless overridden.
# ADMIN lets existing unit tests pass without RBAC friction.
# Auth-specific tests (test_auth.py) override this on a per-test basis.
# ---------------------------------------------------------------------------

DEFAULT_TEST_USER = AuthenticatedUser(id="test-admin", role="ADMIN")


@pytest.fixture(autouse=True, scope="session")
def install_fake_auth():
    """
    Replace DevAuthProvider with FakeAuthProvider for the entire test session.
    Tests that need a different role use a nested override inside the test.
    """
    app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(DEFAULT_TEST_USER)
    yield
    # Clean up after session
    app.dependency_overrides.pop(get_auth_provider, None)
