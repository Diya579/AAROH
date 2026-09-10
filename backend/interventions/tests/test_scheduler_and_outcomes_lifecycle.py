"""
AAROH — Scheduler, Centralized Outcomes & Closed-Loop Observation Lifecycle Tests
Author: Preet (Senior Backend Engineer — Intervention, Routing, SLA, Outcomes & Analytics Owner)

Verifies:
1. PeriodicOverdueScanner thread lifecycle and scan_once operations.
2. Centralized get_outcomes() with case, intervention, and RBAC district scoping.
3. ClosedLoopObservation wiring in record_outcome() and record_re_monitoring().
4. FOLLOW_UP_SCHEDULED event creation on follow_up_required=True.
5. High-level backend.services.intervention_service integration.
"""

import os
import unittest
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import SessionLocal
from backend.models import (
    Case,
    Intervention,
    Outcome,
    CaseEvent,
    DistressState,
)
from backend.interventions.db_service import db_operational_service
from backend.interventions.scheduler import PeriodicOverdueScanner, overdue_scanner
from backend.services import intervention_service


class TestSchedulerAndOutcomesLifecycle(unittest.TestCase):
    engine = None
    Session = None

    @classmethod
    def setUpClass(cls):
        pg_url = os.environ.get("DATABASE_URL")
        if not pg_url or "sqlite" in pg_url:
            pg_url = "postgresql://postgres:root@localhost:5432/aaroh_db"
        try:
            cls.engine = create_engine(pg_url, pool_pre_ping=True)
            with cls.engine.connect() as conn:
                pass
            cls.Session = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False)
        except Exception:
            cls.Session = None

    def setUp(self):
        if not self.Session:
            self.skipTest("PostgreSQL aaroh_db unavailable for lifecycle test")
        self.db = self.Session()

    def tearDown(self):
        if self.db:
            self.db.rollback()
            self.db.close()

    def test_01_periodic_overdue_scanner_lifecycle(self):
        """Verifies PeriodicOverdueScanner scan_once, start, status, and graceful stop."""
        scanner = PeriodicOverdueScanner(default_interval_seconds=1)
        self.assertFalse(scanner.is_running())

        # Test scan_once
        res = scanner.scan_once(db=self.db)
        self.assertIsInstance(res, list)
        self.assertIsNotNone(scanner.status["last_scan_time"])

        # Test start and stop
        scanner.start(interval_seconds=1)
        self.assertTrue(scanner.is_running())
        scanner.stop(timeout=2.0)
        self.assertFalse(scanner.is_running())

    def test_02_record_outcome_wires_closed_loop_and_follow_up_event(self):
        """Verifies outcome recording instantiates ClosedLoopObservation and logs FOLLOW_UP_SCHEDULED."""
        res_interv = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=1,
            auto_commit=True,
        )
        interv_id = res_interv["intervention_id"]

        # Transition to IN_PROGRESS
        interv = self.db.query(Intervention).filter(Intervention.id == interv_id).first()
        interv.status = "IN_PROGRESS"
        self.db.commit()

        # Record outcome with follow_up_required=True
        outcome_res = db_operational_service.record_outcome(
            db=self.db,
            intervention_id=interv_id,
            outcome_type="REFERRED",
            actor_id="OFF-URBAN-1",
            actor_role="CASE_OFFICER",
            actor_district="Synthetic Urban District",
            follow_up_required=True,
            notes="Requires specialized follow-up medical consultation.",
            auto_commit=True,
        )

        self.assertTrue(outcome_res["follow_up_required"])
        self.assertIn("closed_loop_observation", outcome_res)
        cl_data = outcome_res["closed_loop_observation"]
        self.assertIsNotNone(cl_data)
        self.assertEqual(cl_data["case_id"], "AAROH-001")
        self.assertEqual(cl_data["intervention_id"], interv_id)
        self.assertEqual(cl_data["outcome_type"], "REFERRED")
        self.assertIsNotNone(cl_data["pre_distress_score"])

        # Verify FOLLOW_UP_SCHEDULED event in CaseEvent table
        event = (
            self.db.query(CaseEvent)
            .filter(CaseEvent.case_id == 1, CaseEvent.event_type == "FOLLOW_UP_SCHEDULED")
            .first()
        )
        self.assertIsNotNone(event)
        self.assertIn("Follow-up monitoring scheduled", event.description)

    def test_03_record_re_monitoring_evaluates_shift_via_closed_loop(self):
        """Verifies record_re_monitoring links to ClosedLoopObservation and evaluates shift."""
        remon_res = db_operational_service.record_re_monitoring(
            db=self.db,
            case_id=1,
            new_distress_score=0.35,
            new_trajectory="IMPROVING",
            confidence=0.90,
            auto_commit=True,
        )

        self.assertIn("closed_loop_observation", remon_res)
        cl_data = remon_res["closed_loop_observation"]
        self.assertIsNotNone(cl_data)
        self.assertEqual(cl_data["case_id"], "AAROH-001")
        self.assertIn("observed_shift", remon_res)
        self.assertIn(remon_res["observed_shift"], ("SUBSEQUENT_IMPROVEMENT", "SUBSEQUENT_DETERIORATION", "SUBSEQUENT_STABLE"))

    def test_04_centralized_get_outcomes_and_rbac_scoping(self):
        """Verifies get_outcomes() with case filter and RBAC district isolation."""
        # Create an intervention and outcome
        res_interv = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=1,
            auto_commit=True,
        )
        interv = self.db.query(Intervention).filter(Intervention.id == res_interv["intervention_id"]).first()
        interv.status = "IN_PROGRESS"
        self.db.commit()

        db_operational_service.record_outcome(
            db=self.db,
            intervention_id=interv.id,
            outcome_type="COUNSELLING_PROVIDED",
            actor_id="OFF-URBAN-1",
            actor_role="CASE_OFFICER",
            actor_district="Synthetic Urban District",
            follow_up_required=False,
            auto_commit=True,
        )

        # 1. Fetch outcomes via DatabaseOperationalService
        outcomes_all = db_operational_service.get_outcomes(db=self.db, case_id=1)
        self.assertTrue(len(outcomes_all) >= 1)
        self.assertEqual(outcomes_all[0]["case_id"], 1)
        self.assertIn("outcome_type", outcomes_all[0])
        self.assertIn("recorded_at", outcomes_all[0])

        # 2. RBAC Matching District -> should return records
        outcomes_urban = db_operational_service.get_outcomes(
            db=self.db,
            user_role="CASE_OFFICER",
            user_district="Synthetic Urban District",
        )
        self.assertTrue(len(outcomes_urban) >= 1)

        # 3. RBAC Non-Matching District -> should return 0 records for Case 1
        outcomes_rural = db_operational_service.get_outcomes(
            db=self.db,
            case_id=1,
            user_role="CASE_OFFICER",
            user_district="Synthetic Rural District",
        )
        self.assertEqual(len(outcomes_rural), 0)

    def test_05_services_intervention_service_facade(self):
        """Verifies backend.services.intervention_service exports and query helpers."""
        intervs = intervention_service.get_interventions(db=self.db, limit=10)
        self.assertIsInstance(intervs, list)

        outcomes = intervention_service.get_outcomes(db=self.db, limit=10)
        self.assertIsInstance(outcomes, list)

        overdue_scan = intervention_service.check_overdue(db=self.db)
        self.assertIsInstance(overdue_scan, list)


if __name__ == "__main__":
    unittest.main()
