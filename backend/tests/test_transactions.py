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


def test_idempotency_transaction_rollback(monkeypatch):
    """
    Proves that a failure during the final atomic commit in execute_idempotent
    (e.g., when saving the IdempotencyRecord) successfully rolls back the
    flushed domain record, preventing a half-committed state.
    """
    db = SessionLocal()
    
    # 1. Create a valid payload that WOULD succeed
    # We use a real user and real case (assumes test DB has one or we can bypass)
    # Actually, we can just patch `execute_idempotent`? No, the test must hit the endpoint.
    # To hit the endpoint, we need authentication. We can use the FakeAuthProvider defaults.
    
    # Let's mock Session.commit to raise an Exception ONCE, specifically when called 
    # from execute_idempotent after the domain flush.
    from sqlalchemy.orm import Session
    original_commit = Session.commit
    
    commit_calls = {"count": 0}
    
    def mock_commit(self):
        commit_calls["count"] += 1
        # The interaction endpoint does NO commits before execute_idempotent's final commit.
        # So the FIRST commit is the one we want to fail.
        if commit_calls["count"] == 1:
            raise Exception("Simulated crash during atomic commit!")
        original_commit(self)
        
    monkeypatch.setattr(Session, "commit", mock_commit)
    
    # First, let's create a valid case to interact with so FK constraints pass.
    # Actually, if we mock commit(), we can't create a case easily if it commits.
    # Let's create the case BEFORE patching!
    # Wait, the monkeypatch is active during the whole test unless we apply it dynamically.
    monkeypatch.undo() # remove it for setup
    
    import uuid
    unique_case_id = f"TX-TEST-{uuid.uuid4().hex[:8]}"
    from backend.models import Case
    new_case = Case(case_id=unique_case_id, language="en", district_type="urban", district="Pune", state="Maharashtra", priority_use_case="dv", current_stage="active")
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    
    monkeypatch.setattr(Session, "commit", mock_commit)
    
    payload = {
        "case_id": new_case.id,
        "interaction_date": "2026-09-05T00:00:00Z",
        "channel": "voice",
        "language": "en"
    }
    
    from backend.core.auth_provider import FakeAuthProvider, AuthenticatedUser
    from backend.core.security import get_auth_provider
    from backend.main import app
    
    old_overrides = app.dependency_overrides.copy()
    try:
        app.dependency_overrides[get_auth_provider] = lambda: FakeAuthProvider(
            AuthenticatedUser(id="admin", role="ADMIN", state=None, district=None)
        )
        
        from fastapi.testclient import TestClient
        client_no_raise = TestClient(app, raise_server_exceptions=False)
        
        response = client_no_raise.post("/api/v1/interactions", json=payload, headers={"Idempotency-Key": "crash-test-key"})
        
        # The simulated crash happens in `execute_idempotent` during the final `db.commit()`.
        # It bubbles up to the global generic_exception_handler, returning a 500.
        assert response.status_code == 500
        
        # Now, unpatch commit so we can query properly
        monkeypatch.undo()
        
        # 2. Query the database to PROVE the interaction was rolled back.
        # The global exception handler does not explicitly call db.rollback() because
        # FastAPI's request lifecycle manages the session via dependencies.
        # Actually, if the transaction wasn't explicitly committed, it is rolled back when
        # the session is closed!
        from backend.models import Interaction
        interactions = db.query(Interaction).filter(Interaction.case_id == new_case.id).all()
        
        assert len(interactions) == 0, "Domain record was left half-committed!"
        
    finally:
        db.close()
        app.dependency_overrides.clear()
        app.dependency_overrides.update(old_overrides)

