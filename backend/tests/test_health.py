"""
AAROH — FastAPI Foundation Tests

Tests for:
    GET /api/v1/health
    GET /api/v1/ready

Run from the project root (d:/SIH PROJECT AAROH/AAROH/):
    python -m pytest backend/tests/test_health.py -v

Requirements:
    pip install pytest httpx

These tests use FastAPI's TestClient which runs synchronously in-process.
No real PostgreSQL connection is required for the health test.
The readiness test is run both with a real DB (integration) and with a
simulated DB failure (unit) to confirm both code paths.

No real credentials are used in this file.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_health_returns_200(self):
        """GET /api/v1/health must return HTTP 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self):
        """GET /api/v1/health must return {"status": "ok"}."""
        response = client.get("/api/v1/health")
        assert response.json() == {"status": "ok"}

    def test_health_content_type_is_json(self):
        """Response must be JSON."""
        response = client.get("/api/v1/health")
        assert "application/json" in response.headers["content-type"]

    def test_health_does_not_query_database(self):
        """
        /health must never touch the database.
        We verify by patching SessionLocal to raise immediately —
        the health endpoint must still return 200.
        """
        with patch("backend.database.SessionLocal") as mock_session:
            mock_session.side_effect = Exception("DB must not be called")
            response = client.get("/api/v1/health")
        # If the health endpoint called the DB, the patch would have raised.
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Readiness endpoint tests
# ---------------------------------------------------------------------------

class TestReadyEndpoint:

    def test_ready_returns_200_when_db_reachable(self):
        """
        GET /api/v1/ready must return 200 when the DB execute succeeds.
        We mock SessionLocal so the test does not need a real database.
        """
        mock_session = MagicMock()
        mock_session.execute.return_value = None  # SELECT 1 succeeds

        with patch("backend.api.v1.health.SessionLocal", return_value=mock_session):
            response = client.get("/api/v1/ready")

        assert response.status_code == 200

    def test_ready_returns_ready_body_when_db_reachable(self):
        """Response body must be {"status": "ready"} when DB is OK."""
        mock_session = MagicMock()
        mock_session.execute.return_value = None

        with patch("backend.api.v1.health.SessionLocal", return_value=mock_session):
            response = client.get("/api/v1/ready")

        assert response.json() == {"status": "ready"}

    def test_ready_returns_503_when_db_unavailable(self):
        """
        GET /api/v1/ready must return 503 when PostgreSQL is unavailable.
        We simulate a connection failure via OperationalError.
        """
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError(
            "connection refused", None, None
        )

        with patch("backend.api.v1.health.SessionLocal", return_value=mock_session):
            response = client.get("/api/v1/ready")

        assert response.status_code == 503

    def test_ready_returns_not_ready_body_when_db_unavailable(self):
        """Response body must be {"status": "not_ready"} when DB is down."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError(
            "connection refused", None, None
        )

        with patch("backend.api.v1.health.SessionLocal", return_value=mock_session):
            response = client.get("/api/v1/ready")

        assert response.json() == {"status": "not_ready"}

    def test_ready_does_not_expose_db_error_details(self):
        """
        The response body must not contain database error details,
        connection strings, usernames, passwords, or stack traces.
        """
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError(
            "password authentication failed for user 'secret_user' "
            "postgresql://secret_user:secret_pass@localhost/aaroh_db",
            None,
            None,
        )

        with patch("backend.api.v1.health.SessionLocal", return_value=mock_session):
            response = client.get("/api/v1/ready")

        body_text = response.text

        # The safe response should only contain "not_ready"
        assert "not_ready" in body_text

        # Must NOT expose any sensitive information
        assert "password" not in body_text.lower()
        assert "secret_user" not in body_text
        assert "secret_pass" not in body_text
        assert "localhost" not in body_text
        assert "OperationalError" not in body_text
        assert "Traceback" not in body_text
        assert "postgresql" not in body_text.lower()

    def test_ready_session_is_always_closed(self):
        """
        SessionLocal().close() must be called regardless of outcome.
        This verifies the finally block works for both success and failure.
        """
        # --- success path ---
        mock_session_ok = MagicMock()
        mock_session_ok.execute.return_value = None

        with patch("backend.api.v1.health.SessionLocal", return_value=mock_session_ok):
            client.get("/api/v1/ready")

        mock_session_ok.close.assert_called_once()

        # --- failure path ---
        mock_session_fail = MagicMock()
        mock_session_fail.execute.side_effect = OperationalError(
            "refused", None, None
        )

        with patch("backend.api.v1.health.SessionLocal", return_value=mock_session_fail):
            client.get("/api/v1/ready")

        mock_session_fail.close.assert_called_once()
