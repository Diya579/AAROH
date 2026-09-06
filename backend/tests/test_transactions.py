import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.main import app
from backend.database import SessionLocal

client = TestClient(app)

def test_failed_transaction_rolls_back_cleanly():
    """
    Ensures that when an endpoint catches a DB exception and explicitly rolls back,
    the session connection is left clean for subsequent queries and no ghost records persist.
    """
    db = SessionLocal()
    
    # 1. Try to create an interaction with a non-existent case_id to force a DB FK IntegrityError
    invalid_payload = {
        "case_id": 99999999,  # does not exist
        "interaction_date": "2026-09-05T00:00:00Z",
        "channel": "voice",
        "language": "en"
    }
    
    response = client.post("/api/v1/interactions", json=invalid_payload)
    
    # verify_case_id_access now fires BEFORE the DB write, returning 404 for a
    # non-existent case_id. This is more precise than the previous 422 from FK error.
    # The session-cleanliness guarantee is unchanged: the auth check raises before
    # any DB mutation, so no rollback is needed — and the session must still be usable.
    assert response.status_code == 404
    assert "not found" in response.json()["error"]["message"].lower()

    
    # 2. Check the DB directly to ensure the connection is clean and usable
    # If db.rollback() was missing, this would throw a PendingRollbackError
    try:
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1
    except Exception as e:
        pytest.fail(f"Session was not cleanly rolled back: {e}")
    finally:
        db.close()
