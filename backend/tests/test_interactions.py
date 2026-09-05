"""
AAROH — Interaction API Tests
"""

import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# Sample valid payload
VALID_INTERACTION_PAYLOAD = {
    "case_id": 1,
    "interaction_date": "2026-09-05T10:00:00",
    "channel": "sms",
    "language": "en",
    "text_response": "Hello",
    "voice_available": False,
    "response_completed": True,
    "help_requested": False,
    "data_quality": "good"
}

# Sample valid response
VALID_INTERACTION_RESPONSE = {
    "id": 1,
    **VALID_INTERACTION_PAYLOAD,
    "safety_response": None,
    "sleep_disruption": None,
    "fear_level": None,
    "social_support": None
}


class TestInteractionEndpoints:

    @patch("backend.api.v1.interactions.interaction_service.create_interaction")
    def test_create_interaction_success(self, mock_create):
        """POST /api/v1/interactions should return 201 on success."""
        mock_create.return_value = VALID_INTERACTION_RESPONSE

        response = client.post("/api/v1/interactions", json=VALID_INTERACTION_PAYLOAD)

        assert response.status_code == 201
        data = response.json()
        assert data["channel"] == "sms"
        assert data["id"] == 1

    @patch("backend.api.v1.interactions.interaction_service.create_interaction")
    def test_create_interaction_db_error(self, mock_create):
        """POST /api/v1/interactions should return 422 on DB error (e.g., bad case_id)."""
        mock_create.side_effect = Exception("DB error")

        response = client.post("/api/v1/interactions", json=VALID_INTERACTION_PAYLOAD)

        assert response.status_code == 422
        assert "Ensure case_id is valid" in response.json()["error"]["message"]

    def test_create_interaction_invalid_payload(self):
        """POST /api/v1/interactions should return 422 for validation errors."""
        invalid_payload = {"case_id": 1} # Missing required fields

        response = client.post("/api/v1/interactions", json=invalid_payload)

        assert response.status_code == 422

    @patch("backend.api.v1.interactions.interaction_service.list_interactions")
    def test_list_interactions_success(self, mock_list):
        """GET /api/v1/interactions should return 200 and a list of interactions."""
        mock_list.return_value = [VALID_INTERACTION_RESPONSE]

        response = client.get("/api/v1/interactions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["channel"] == "sms"

    @patch("backend.api.v1.interactions.interaction_service.get_interaction")
    def test_get_interaction_success(self, mock_get):
        """GET /api/v1/interactions/{id} should return 200 on success."""
        import types
        mock_get.return_value = types.SimpleNamespace(**VALID_INTERACTION_RESPONSE)
        
        response = client.get("/api/v1/interactions/1")

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "sms"

    @patch("backend.api.v1.interactions.interaction_service.get_interaction")
    def test_get_interaction_not_found(self, mock_get):
        """GET /api/v1/interactions/{id} should return 404 if not found."""
        mock_get.return_value = None

        response = client.get("/api/v1/interactions/999")

        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"]
