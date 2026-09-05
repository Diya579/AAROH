"""
AAROH — Consent API Tests
"""

import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# Sample valid payload
VALID_CONSENT_PAYLOAD = {
    "monitoring_consent": True,
    "text_analysis_consent": True,
    "voice_analysis_consent": False,
    "case_linkage_consent": True,
    "safe_channel": "sms",
    "safe_time": "evening"
}

# Sample valid response
VALID_CONSENT_RESPONSE = {
    "id": 1,
    "case_id": 1,
    **VALID_CONSENT_PAYLOAD
}


class TestConsentEndpoints:

    @patch("backend.api.v1.consents.consent_service.upsert_consent")
    def test_upsert_consent_success(self, mock_upsert):
        """PUT /api/v1/consents/{case_id} should return 200 on success."""
        mock_upsert.return_value = VALID_CONSENT_RESPONSE

        response = client.put("/api/v1/consents/1", json=VALID_CONSENT_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        assert data["safe_channel"] == "sms"
        assert data["case_id"] == 1

    @patch("backend.api.v1.consents.consent_service.upsert_consent")
    def test_upsert_consent_db_error(self, mock_upsert):
        """PUT /api/v1/consents/{case_id} should return 422 on DB error."""
        mock_upsert.side_effect = Exception("DB error")

        response = client.put("/api/v1/consents/1", json=VALID_CONSENT_PAYLOAD)

        assert response.status_code == 422
        assert "Ensure case_id is valid" in response.json()["detail"]

    @patch("backend.api.v1.consents.consent_service.get_consent")
    def test_get_consent_success(self, mock_get):
        """GET /api/v1/consents/{case_id} should return 200 on success."""
        mock_get.return_value = VALID_CONSENT_RESPONSE

        response = client.get("/api/v1/consents/1")

        assert response.status_code == 200
        data = response.json()
        assert data["safe_channel"] == "sms"

    @patch("backend.api.v1.consents.consent_service.get_consent")
    def test_get_consent_not_found(self, mock_get):
        """GET /api/v1/consents/{case_id} should return 404 if not found."""
        mock_get.return_value = None

        response = client.get("/api/v1/consents/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
