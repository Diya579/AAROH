"""
AAROH — Case API Tests
"""

import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# Sample valid payload
VALID_CASE_PAYLOAD = {
    "case_id": "EXT-1234",
    "language": "en",
    "district_type": "urban",
    "district": "North District",
    "priority_use_case": "Standard",
    "current_stage": "Initial",
    "voice_opted_in": True,
    "monitoring_consent": True
}

# Sample valid response
VALID_CASE_RESPONSE = {
    "id": 1,
    "created_at": "2026-09-05T10:00:00",
    "state": None,  # state is Optional — None when not populated
    **VALID_CASE_PAYLOAD
}


class TestCaseEndpoints:

    @patch("backend.api.v1.cases.case_service.create_case")
    def test_create_case_success(self, mock_create):
        """POST /api/v1/cases should return 201 on success."""
        mock_create.return_value = VALID_CASE_RESPONSE

        response = client.post("/api/v1/cases", json=VALID_CASE_PAYLOAD)

        assert response.status_code == 201
        data = response.json()
        assert data["case_id"] == "EXT-1234"
        assert data["id"] == 1

    @patch("backend.api.v1.cases.case_service.create_case")
    def test_create_case_duplicate(self, mock_create):
        """POST /api/v1/cases should return 409 on duplicate case_id."""
        mock_create.side_effect = ValueError("Case with case_id 'EXT-1234' already exists.")

        response = client.post("/api/v1/cases", json=VALID_CASE_PAYLOAD)

        assert response.status_code == 409
        assert "already exists" in response.json()["error"]["message"]

    def test_create_case_invalid_payload(self):
        """POST /api/v1/cases should return 422 for validation errors."""
        invalid_payload = {"case_id": "EXT-1234"} # Missing required fields

        response = client.post("/api/v1/cases", json=invalid_payload)

        assert response.status_code == 422

    @patch("backend.api.v1.cases.case_service.list_cases")
    def test_list_cases_success(self, mock_list):
        """GET /api/v1/cases should return 200 and a list of cases."""
        mock_list.return_value = [VALID_CASE_RESPONSE]

        response = client.get("/api/v1/cases")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["case_id"] == "EXT-1234"

    @patch("backend.api.v1.cases.case_service.get_case")
    def test_get_case_success(self, mock_get):
        """GET /api/v1/cases/{id} should return 200 on success."""
        mock_get.return_value = VALID_CASE_RESPONSE

        response = client.get("/api/v1/cases/1")

        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == "EXT-1234"

    @patch("backend.api.v1.cases.case_service.get_case")
    def test_get_case_not_found(self, mock_get):
        """GET /api/v1/cases/{id} should return 404 if not found."""
        mock_get.return_value = None

        response = client.get("/api/v1/cases/999")

        assert response.status_code == 404
        assert "not found" in response.json()["error"]["message"]

    @patch("backend.api.v1.cases.case_service.update_case")
    def test_update_case_success(self, mock_update):
        """PUT /api/v1/cases/{id} should return 200 on success."""
        updated_response = VALID_CASE_RESPONSE.copy()
        updated_response["language"] = "fr"
        mock_update.return_value = updated_response

        response = client.put("/api/v1/cases/1", json={"language": "fr"})

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "fr"

    @patch("backend.api.v1.cases.case_service.update_case")
    def test_update_case_not_found(self, mock_update):
        """PUT /api/v1/cases/{id} should return 404 if not found."""
        mock_update.return_value = None

        response = client.put("/api/v1/cases/999", json={"language": "fr"})

        assert response.status_code == 404

    @patch("backend.api.v1.cases.case_service.delete_case")
    def test_delete_case_success(self, mock_delete):
        """DELETE /api/v1/cases/{id} should return 204 on success."""
        mock_delete.return_value = True

        response = client.delete("/api/v1/cases/1")

        assert response.status_code == 204

    @patch("backend.api.v1.cases.case_service.delete_case")
    def test_delete_case_not_found(self, mock_delete):
        """DELETE /api/v1/cases/{id} should return 404 if not found."""
        mock_delete.return_value = False

        response = client.delete("/api/v1/cases/999")

        assert response.status_code == 404
