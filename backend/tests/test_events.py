"""
AAROH — Event API Tests
"""

import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# Sample valid payload
VALID_EVENT_PAYLOAD = {
    "case_id": 1,
    "event_date": "2026-09-05T10:00:00",
    "event_type": "Risk Assessment",
    "description": "Routine check",
    "case_stage": "Monitoring"
}

# Sample valid response
VALID_EVENT_RESPONSE = {
    "id": 1,
    **VALID_EVENT_PAYLOAD
}


class TestEventEndpoints:

    @patch("backend.api.v1.events.event_service.create_event")
    def test_create_event_success(self, mock_create):
        """POST /api/v1/events should return 201 on success."""
        mock_create.return_value = VALID_EVENT_RESPONSE

        response = client.post("/api/v1/events", json=VALID_EVENT_PAYLOAD)

        assert response.status_code == 201
        data = response.json()
        assert data["event_type"] == "Risk Assessment"
        assert data["id"] == 1

    @patch("backend.api.v1.events.event_service.create_event")
    def test_create_event_db_error(self, mock_create):
        """POST /api/v1/events should return 422 on DB error (e.g., bad case_id)."""
        mock_create.side_effect = Exception("DB error")

        response = client.post("/api/v1/events", json=VALID_EVENT_PAYLOAD)

        assert response.status_code == 422
        assert "Ensure case_id is valid" in response.json()["error"]["message"]

    def test_create_event_invalid_payload(self):
        """POST /api/v1/events should return 422 for validation errors."""
        invalid_payload = {"case_id": 1} # Missing required fields

        response = client.post("/api/v1/events", json=invalid_payload)

        assert response.status_code == 422

    @patch("backend.api.v1.events.event_service.list_events")
    def test_list_events_success(self, mock_list):
        """GET /api/v1/events should return 200 and a list of events."""
        mock_list.return_value = [VALID_EVENT_RESPONSE]

        response = client.get("/api/v1/events")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["event_type"] == "Risk Assessment"

    @patch("backend.api.v1.events.event_service.get_event")
    def test_get_event_success(self, mock_get):
        """GET /api/v1/events/{id} should return 200 on success."""
        mock_get.return_value = VALID_EVENT_RESPONSE

        response = client.get("/api/v1/events/1")

        assert response.status_code == 200
        data = response.json()
        assert data["event_type"] == "Risk Assessment"

    @patch("backend.api.v1.events.event_service.get_event")
    def test_get_event_not_found(self, mock_get):
        """GET /api/v1/events/{id} should return 404 if not found."""
        mock_get.return_value = None

        response = client.get("/api/v1/events/999")

        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"]
