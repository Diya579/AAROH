"""
AAROH — Audio API Tests
"""

import os
from io import BytesIO
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

class TestAudioEndpoints:

    def test_upload_audio_success(self, tmp_path, monkeypatch):
        """POST /api/v1/audio should return 201 and save the file."""
        # Patch the UPLOAD_DIR in the audio router to use a temp dir during tests
        monkeypatch.setattr("backend.api.v1.audio.UPLOAD_DIR", tmp_path)

        # Create a dummy file
        file_content = b"fake audio content"
        file_obj = BytesIO(file_content)
        file_obj.name = "test_audio.wav"

        response = client.post(
            "/api/v1/audio",
            files={"file": ("test_audio.wav", file_obj, "audio/wav")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Audio file uploaded successfully"
        assert data["filename"] == "test_audio.wav"
        
        # Verify file was actually saved
        saved_file = tmp_path / "test_audio.wav"
        assert saved_file.exists()
        assert saved_file.read_bytes() == file_content

    def test_upload_audio_missing_file(self):
        """POST /api/v1/audio should return 422 if no file provided."""
        response = client.post("/api/v1/audio")
        assert response.status_code == 422
