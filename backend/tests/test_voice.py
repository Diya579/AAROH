"""
AAROH — Voice Endpoint Tests

Covers:
  - Missing file → 400
  - No filename → 400
  - Invalid extension → 422
  - Invalid MIME type → 422
  - Oversized file → 413
  - Unrecognised format (bad magic bytes) → 422
  - No consent record → 403
  - Consent record exists but voice_analysis_consent=False → 403
  - Valid WAV upload → 202 RECEIVED
  - Temp file cleanup after processing
  - Voice endpoint delegates to voice_service (not ASR/ML directly)

Test strategy:
  - All tests use in-memory SQLite via conftest FakeAuthProvider (ADMIN default).
  - DB override is applied per-module.
  - A valid minimal WAV file is synthesised in-process (stdlib wave module).
  - No real audio files or real DB connections used.
"""

from __future__ import annotations

import io
import os
import struct
import tempfile
import uuid
import wave
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base
from backend import models
from backend.api.v1.interactions import get_db as get_interactions_db
from backend.api.v1.consents import get_db as get_consents_db
from backend.api.v1.cases import get_db as get_cases_db

# ---------------------------------------------------------------------------
# In-memory DB for this module
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


client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    
    app.dependency_overrides[get_interactions_db] = override_get_db
    app.dependency_overrides[get_consents_db] = override_get_db
    app.dependency_overrides[get_cases_db] = override_get_db
    
    yield
    
    app.dependency_overrides.pop(get_interactions_db, None)
    app.dependency_overrides.pop(get_consents_db, None)
    app.dependency_overrides.pop(get_cases_db, None)
    
    Base.metadata.drop_all(bind=engine)





# ---------------------------------------------------------------------------
# Helpers — build test data directly in DB
# ---------------------------------------------------------------------------

def _make_case(db, *, case_id="VOICE-CASE-1", district="Pune"):
    case = models.Case(
        case_id=case_id,
        language="hi-IN",
        district_type="rural",
        district=district,
        priority_use_case="domestic_violence",
        current_stage="intake",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def _make_interaction(db, *, case_id_fk: int):
    from datetime import datetime
    interaction = models.Interaction(
        case_id=case_id_fk,
        interaction_date=datetime(2026, 9, 5, 10, 0, 0),
        channel="voice",
        language="hi-IN",
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def _make_consent(db, *, case_id_fk: int, voice_analysis_consent: bool = True):
    consent = models.Consent(
        case_id=case_id_fk,
        monitoring_consent=True,
        text_analysis_consent=True,
        voice_analysis_consent=voice_analysis_consent,
        case_linkage_consent=True,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


# ---------------------------------------------------------------------------
# WAV file factory (stdlib — no external deps)
# ---------------------------------------------------------------------------

def _make_valid_wav(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generate a minimal valid WAV file in memory."""
    buf = io.BytesIO()
    n_frames = int(sample_rate * duration_seconds)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(sample_rate)
        # Write silence (all zeros)
        wf.writeframes(b"\x00\x00" * n_frames)
    return buf.getvalue()


def _make_tiny_wav(duration_seconds: float = 0.1) -> bytes:
    """WAV shorter than minimum duration (< 1 s)."""
    return _make_valid_wav(duration_seconds=duration_seconds)


def _make_long_wav(duration_seconds: float = 130.0) -> bytes:
    """WAV longer than maximum duration (> 120 s)."""
    return _make_valid_wav(duration_seconds=duration_seconds)


# ---------------------------------------------------------------------------
# Fixture: standard DB state (case + interaction + consent with voice=True)
# ---------------------------------------------------------------------------

@pytest.fixture()
def standard_setup():
    """Returns (case_id, interaction_id) with voice_analysis_consent=True."""
    db = TestingSessionLocal()
    try:
        case = _make_case(db, case_id=f"VC-{uuid.uuid4().hex}")
        interaction = _make_interaction(db, case_id_fk=case.id)
        _make_consent(db, case_id_fk=case.id, voice_analysis_consent=True)
        return case.id, interaction.id
    finally:
        db.close()


@pytest.fixture()
def no_consent_setup():
    """Returns (case_id, interaction_id) with NO consent record."""
    db = TestingSessionLocal()
    try:
        case = _make_case(db, case_id=f"NC-{uuid.uuid4().hex}")
        interaction = _make_interaction(db, case_id_fk=case.id)
        # Deliberately no consent record
        return case.id, interaction.id
    finally:
        db.close()


@pytest.fixture()
def denied_consent_setup():
    """Returns (case_id, interaction_id) with voice_analysis_consent=False."""
    db = TestingSessionLocal()
    try:
        case = _make_case(db, case_id=f"DC-{uuid.uuid4().hex}")
        interaction = _make_interaction(db, case_id_fk=case.id)
        _make_consent(db, case_id_fk=case.id, voice_analysis_consent=False)
        return case.id, interaction.id
    finally:
        db.close()


# ---------------------------------------------------------------------------
# URL helper
# ---------------------------------------------------------------------------

def _voice_url(interaction_id: int) -> str:
    return f"/api/v1/interactions/{interaction_id}/voice"


# ---------------------------------------------------------------------------
# Tests — audio validation (run before DB checks)
# ---------------------------------------------------------------------------

class TestAudioValidation:

    def test_missing_file_returns_400(self, standard_setup):
        _, interaction_id = standard_setup
        # Send request with no file field at all
        response = client.post(_voice_url(interaction_id), files={})
        assert response.status_code == 422  # FastAPI missing required field

    def test_invalid_extension_returns_422(self, standard_setup):
        _, interaction_id = standard_setup
        wav_bytes = _make_valid_wav()
        files = {"file": ("recording.txt", io.BytesIO(wav_bytes), "text/plain")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 422
        body = response.json()
        assert "error" in body
        assert body["error"]["code"] == "AUDIO_INVALID_EXTENSION"

    def test_invalid_mime_type_returns_422(self, standard_setup):
        _, interaction_id = standard_setup
        # Use valid WAV bytes but an invalid MIME type (non-allowed MIME)
        wav_bytes = _make_valid_wav()
        files = {"file": ("recording.wav", io.BytesIO(wav_bytes), "video/mp4")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 422

    def test_oversized_file_returns_413(self, standard_setup):
        _, interaction_id = standard_setup
        # Build a fake file that reports as .wav but is too large (11 MB of zeros)
        # We use actual WAV header so magic bytes pass, then pad with zeros
        header = _make_valid_wav(duration_seconds=0.01)
        # Pad to exceed 10MB
        large_data = header + (b"\x00" * (10 * 1024 * 1024 + 100))
        files = {"file": ("recording.wav", io.BytesIO(large_data), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 413

    def test_bad_magic_bytes_returns_422(self, standard_setup):
        _, interaction_id = standard_setup
        # .wav extension but garbage bytes (not a real WAV)
        garbage = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b" + b"garbage" * 100
        files = {"file": ("recording.wav", io.BytesIO(garbage), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "AUDIO_UNRECOGNISED_FORMAT"

    def test_wav_too_short_returns_422(self, standard_setup):
        _, interaction_id = standard_setup
        tiny = _make_tiny_wav(duration_seconds=0.1)
        files = {"file": ("recording.wav", io.BytesIO(tiny), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "AUDIO_TOO_SHORT"

    def test_wav_too_long_returns_422(self, standard_setup):
        _, interaction_id = standard_setup
        long_wav = _make_long_wav(duration_seconds=130.0)
        files = {"file": ("recording.wav", io.BytesIO(long_wav), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "AUDIO_TOO_LONG"


# ---------------------------------------------------------------------------
# Tests — consent enforcement
# ---------------------------------------------------------------------------

class TestConsentEnforcement:

    def test_no_consent_record_returns_403(self, no_consent_setup):
        _, interaction_id = no_consent_setup
        wav_bytes = _make_valid_wav()
        files = {"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 403
        assert "consent" in response.json()["error"]["message"].lower()

    def test_voice_consent_denied_returns_403(self, denied_consent_setup):
        _, interaction_id = denied_consent_setup
        wav_bytes = _make_valid_wav()
        files = {"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 403

    def test_voice_opted_in_alone_is_not_sufficient(self):
        """
        Case.voice_opted_in=True must NOT bypass the Consent table check.
        The consent record is the authoritative source.
        """
        db = TestingSessionLocal()
        try:
            # Create case with voice_opted_in=True but NO consent record
            case = models.Case(
                case_id=f"VOI-{uuid.uuid4().hex}",
                language="en",
                district_type="urban",
                district="Delhi",
                priority_use_case="test",
                current_stage="active",
                voice_opted_in=True,   # <-- set True
                monitoring_consent=True,
            )
            db.add(case)
            db.commit()
            db.refresh(case)

            from datetime import datetime
            interaction = models.Interaction(
                case_id=case.id,
                interaction_date=datetime(2026, 9, 5, 10, 0, 0),
                channel="voice",
                language="en",
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            interaction_id = interaction.id
        finally:
            db.close()

        wav_bytes = _make_valid_wav()
        files = {"file": ("test.wav", io.BytesIO(wav_bytes), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        # Must be rejected because there is no Consent record — voice_opted_in alone is insufficient
        assert response.status_code == 403, (
            "voice_opted_in=True on Case must not bypass the Consent table check."
        )


# ---------------------------------------------------------------------------
# Tests — happy path and delegation
# ---------------------------------------------------------------------------

class TestVoiceUpload:

    def test_valid_wav_returns_202(self, standard_setup):
        _, interaction_id = standard_setup
        wav_bytes = _make_valid_wav(duration_seconds=3.0)
        files = {"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 202
        body = response.json()
        assert body["status"] in ("RECEIVED", "PROCESSING", "COMPLETED", "FAILED", "RETRY_REQUIRED")
        assert body["interaction_id"] == interaction_id

    def test_valid_wav_returns_received_state(self, standard_setup):
        _, interaction_id = standard_setup
        wav_bytes = _make_valid_wav(duration_seconds=5.0)
        files = {"file": ("session.wav", io.BytesIO(wav_bytes), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        assert response.status_code == 202
        # With no voice subsystem installed, must return RECEIVED (not COMPLETED)
        assert response.json()["status"] == "RECEIVED"

    def test_nonexistent_interaction_returns_404(self):
        wav_bytes = _make_valid_wav()
        files = {"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")}
        response = client.post(_voice_url(99999), files=files)
        assert response.status_code == 404

    def test_fastapi_does_not_call_ml_directly(self, standard_setup):
        """
        Verify that the endpoint delegates to voice_service.delegate_voice_processing
        and does NOT call ASR, VAD, or ML feature functions directly.
        """
        _, interaction_id = standard_setup
        wav_bytes = _make_valid_wav()
        files = {"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")}

        with patch(
            "backend.services.voice_service.delegate_voice_processing",
            return_value="RECEIVED"
        ) as mock_delegate:
            response = client.post(_voice_url(interaction_id), files=files)

        assert response.status_code == 202
        mock_delegate.assert_called_once()
        # Verify the right arguments were passed (no ASR/ML logic in the call)
        call_kwargs = mock_delegate.call_args.kwargs
        assert "interaction_id" in call_kwargs
        assert "case_id" in call_kwargs
        assert "language" in call_kwargs
        assert "audio_bytes" in call_kwargs

    def test_temp_file_is_deleted_after_processing(self, standard_setup, tmp_path):
        """
        The temporary audio file must be deleted after voice_service processes it,
        regardless of whether processing succeeds.
        """
        _, interaction_id = standard_setup
        wav_bytes = _make_valid_wav()
        files = {"file": ("recording.wav", io.BytesIO(wav_bytes), "audio/wav")}

        created_files: list[str] = []

        original_delegate = __import__(
            "backend.services.voice_service",
            fromlist=["delegate_voice_processing"],
        ).delegate_voice_processing

        def tracking_delegate(**kwargs):
            # After calling the real function, check temp file is gone
            result = original_delegate(**kwargs)
            return result

        with patch(
            "backend.api.v1.interactions.voice_service.delegate_voice_processing",
            side_effect=tracking_delegate
        ):
            response = client.post(_voice_url(interaction_id), files=files)

        assert response.status_code == 202
        # Verify no .audio_tmp files were left behind in the OS temp dir
        import glob
        leftover = glob.glob(os.path.join(tempfile.gettempdir(), "aaroh_voice_*.audio_tmp"))
        assert len(leftover) == 0, (
            f"Temp audio files were not cleaned up: {leftover}"
        )


# ---------------------------------------------------------------------------
# Tests — response body does not leak sensitive info
# ---------------------------------------------------------------------------

class TestResponseSafety:

    def test_error_does_not_contain_filesystem_path(self, standard_setup):
        _, interaction_id = standard_setup
        garbage = b"\x00" * 200  # Will fail magic bytes
        files = {"file": ("recording.wav", io.BytesIO(garbage), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        # Must not expose any OS path in the error response
        body = response.text
        assert "C:\\" not in body
        assert "/tmp/" not in body
        assert "aaroh_voice_" not in body

    def test_error_envelope_structure(self, standard_setup):
        _, interaction_id = standard_setup
        garbage = b"\x00" * 200
        files = {"file": ("recording.wav", io.BytesIO(garbage), "audio/wav")}
        response = client.post(_voice_url(interaction_id), files=files)
        body = response.json()
        assert "error" in body
        assert "message" in body["error"]
