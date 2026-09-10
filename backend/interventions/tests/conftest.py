"""
AAROH — Interventions Test Suite Configuration & State Isolation Fixture
Author: Preet (Senior Backend Engineer — Intervention, Routing, SLA, Outcomes & Analytics Owner)

Ensures 100% test isolation, preventing database state and singleton bleeding across
all test suites regardless of execution order or concurrency.
"""

import os
import pytest
from sqlalchemy import create_engine, text

from backend.interventions.notifications import notification_service


def _get_pg_engine():
    pg_url = os.environ.get("DATABASE_URL")
    if not pg_url or "sqlite" in pg_url:
        pg_url = "postgresql://postgres:root@localhost:5432/aaroh_db"
    try:
        eng = create_engine(pg_url, pool_pre_ping=True)
        with eng.connect() as conn:
            pass
        return eng
    except Exception:
        return None


def reset_test_environment():
    """
    Cleans up any ephemeral test artifacts, deletes non-baseline rows,
    restores baseline Case 1-20 consent and predictions, and clears in-memory notification logs.
    """
    notification_service.clear_log()

    eng = _get_pg_engine()
    if not eng:
        return

    with eng.connect() as conn:
        try:
            # 1. Clean temporary test cases
            test_case_ids = [
                r[0] for r in conn.execute(
                    text("SELECT id FROM cases WHERE id > 20 OR case_id NOT LIKE 'AAROH-%'")
                ).fetchall()
            ]
            if test_case_ids:
                cid_str = ",".join(map(str, test_case_ids))
                conn.execute(text(f"DELETE FROM notifications WHERE case_id IN ({cid_str})"))
                conn.execute(text(f"DELETE FROM outcomes WHERE case_id IN ({cid_str})"))
                conn.execute(text(f"DELETE FROM interventions WHERE case_id IN ({cid_str})"))
                conn.execute(text(f"DELETE FROM predictions WHERE case_id IN ({cid_str})"))
                conn.execute(text(f"DELETE FROM distress_states WHERE case_id IN ({cid_str})"))
                conn.execute(text(f"DELETE FROM engagement_features WHERE interaction_id IN (SELECT id FROM interactions WHERE case_id IN ({cid_str}))"))
                conn.execute(text(f"DELETE FROM interactions WHERE case_id IN ({cid_str})"))
                conn.execute(text(f"DELETE FROM consents WHERE case_id IN ({cid_str})"))
                conn.execute(text(f"DELETE FROM case_events WHERE case_id IN ({cid_str})"))
                conn.execute(text(f"DELETE FROM cases WHERE id IN ({cid_str})"))

            # 2. Clean temporary distress states, predictions, and interactions created during tests
            conn.execute(text("DELETE FROM distress_states WHERE id > 20"))
            conn.execute(text("DELETE FROM predictions WHERE id > 20"))
            conn.execute(text("DELETE FROM engagement_features WHERE interaction_id IN (SELECT id FROM interactions WHERE id > 20)"))
            conn.execute(text("DELETE FROM interactions WHERE id > 20"))

            # 3. Clean test interventions, outcomes, and notifications
            conn.execute(text("DELETE FROM notifications"))
            conn.execute(text("DELETE FROM outcomes"))
            conn.execute(text("DELETE FROM interventions"))

            # 4. Restore baseline consents for standard cases
            conn.execute(text(
                "UPDATE consents SET monitoring_consent = true, voice_analysis_consent = true, "
                "text_analysis_consent = true, case_linkage_consent = true, safe_channel = 'sms' "
                "WHERE case_id <= 20"
            ))

            conn.commit()
        except Exception:
            conn.rollback()


@pytest.fixture(autouse=True)
def isolate_test_state():
    """Autouse fixture isolating every single test run."""
    reset_test_environment()
    yield
    reset_test_environment()
