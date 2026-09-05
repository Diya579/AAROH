"""
AAROH — Middleware Tests

Tests for global middleware such as request/correlation ID threading.
"""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from backend.main import app

# We'll attach a temporary endpoint directly to the app for testing 500 errors
test_router = APIRouter()

@test_router.get("/api/v1/trigger_500")
def trigger_error():
    raise RuntimeError("Intentional test error")

app.include_router(test_router)

client = TestClient(app)

class TestRequestIDMiddleware:
    def test_successful_request_has_request_id_header(self):
        """A normal 200 OK response should include the X-Request-ID header."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 10

    def test_http_exception_includes_request_id_in_header_and_body(self):
        """A 404 response should include the request_id in both header and the error envelope."""
        response = client.get("/api/v1/cases/999999")  # Likely 404 or 401
        
        # Whether it hits 401 (no auth) or 404, it uses the StarletteHTTPException handler
        assert response.status_code in (401, 404)
        
        req_id_header = response.headers.get("X-Request-ID")
        assert req_id_header is not None
        
        body = response.json()
        assert "error" in body
        assert body["error"]["request_id"] == req_id_header

    def test_validation_error_includes_request_id_in_header_and_body(self):
        """A 422 ValidationError should include the request_id in both header and body."""
        # POST with missing required fields
        response = client.post("/api/v1/cases", json={"invalid": "payload"})
        
        assert response.status_code == 422
        
        req_id_header = response.headers.get("X-Request-ID")
        assert req_id_header is not None
        
        body = response.json()
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["request_id"] == req_id_header

    def test_generic_exception_includes_request_id_in_header_and_body(self):
        """An unhandled 500 exception should include the request_id in both header and body."""
        # Using raise_server_error will trigger the 500 handler, but our FastAPI test client
        # might raise it directly if we don't configure it to raise_server_exceptions=False
        client_no_raise = TestClient(app, raise_server_exceptions=False)
        response = client_no_raise.get("/api/v1/trigger_500")
        
        assert response.status_code == 500
        
        req_id_header = response.headers.get("X-Request-ID")
        assert req_id_header is not None
        
        body = response.json()
        assert "error" in body
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert body["error"]["request_id"] == req_id_header
