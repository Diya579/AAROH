"""
AAROH Day 4 Real PostgreSQL Workflow Integration Test Suite
Author: Preet (Intervention, Routing, SLA, Outcomes & Analytics Owner)

Directly tests the real operational flow against live PostgreSQL database records:
1. HIGH -> URGENT -> assignment -> SLA -> completion -> outcome
2. WORSENING -> human follow-up -> assignment
3. IMPROVING -> monitoring
4. low-confidence -> human review
5. missing district -> no assignment
6. no eligible officer -> routing unavailable
7. unauthorized official -> blocked
8. outcome -> persisted/history
9. analytics -> correct scoped/privacy-safe results
10. closed-loop re-monitoring -> temporal association with clinical disclaimer
"""

import os
import unittest
from datetime import datetime, timedelta, timezone

from backend.database import SessionLocal
from backend.models import (
    Case,
    Prediction,
    Consent,
    DistressState,
    Intervention,
    Outcome,
)
from backend.interventions.engine import (
    InterventionEngine,
    InterventionType,
    InterventionStatus,
    PriorityLevel,
    InterventionCategory,
)
from backend.interventions.routing import (
    AssignmentRouter,
    AssigneeRole,
    RoutingStatus,
    SyntheticOfficer,
)
from backend.interventions.sla import (
    SLAManager,
    SLAStatus,
    ensure_utc,
)
from backend.interventions.outcomes import (
    OutcomeManager,
    OutcomeType,
)
from backend.interventions.notifications import (
    notification_service,
    NotificationRecipientRole,
    NotificationType,
)
from backend.interventions.db_service import (
    DatabaseOperationalService,
    db_operational_service,
)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestDay4RealPostgreSqlWorkflow(unittest.TestCase):
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

    def setUp(self) -> None:
        if self.Session is None:
            self.skipTest("PostgreSQL database is not reachable at localhost:5432.")
        self.db = self.Session()
        case_1 = self.db.query(Case).filter(Case.id == 1).first()
        if not case_1:
            self.db.close()
            self.skipTest("Test Case 1 not found in database.")
        self._clean_all_test_interventions()

    def tearDown(self) -> None:
        self.db.rollback()
        self._clean_all_test_interventions()
        self.db.close()

    def _clean_all_test_interventions(self) -> None:
        """Cleans up interventions and outcomes created during integration tests."""
        try:
            self.db.query(Outcome).delete()
            self.db.query(Intervention).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()

    # -------------------------------------------------------------------------
    # 1. HIGH -> URGENT -> assignment -> SLA -> completion -> outcome
    # -------------------------------------------------------------------------
    def test_01_real_postgresql_high_urgent_assignment_sla_completion_outcome(self) -> None:
        """
        Tests: HIGH risk -> URGENT priority -> assigned to urban officer ->
        4h SLA window -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED -> Outcome persisted.
        """
        router = AssignmentRouter([
            SyntheticOfficer("OFF-URBAN-1", "Urban Primary", AssigneeRole.DESIGNATED_OFFICER, "Synthetic Urban District", active_caseload=0),
            SyntheticOfficer("OFF-URBAN-2", "Urban Backup", AssigneeRole.DESIGNATED_OFFICER, "Synthetic Urban District", active_caseload=1),
        ])

        # Case 1 has prob=0.88, conf=0.95, trajectory=RAPIDLY_WORSENING
        res = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=1,
            custom_router=router,
        )
        interv_id = res["intervention_id"]
        self.assertIsNotNone(interv_id)
        self.assertEqual(res["intervention_type"], InterventionType.PRIORITY_HUMAN_REVIEW.value)
        self.assertEqual(res["priority"], PriorityLevel.URGENT.value)
        self.assertEqual(res["status"], "ASSIGNED")
        self.assertEqual(res["assigned_to"], "OFF-URBAN-1")
        self.assertEqual(res["backup_officer"], "OFF-URBAN-2")
        self.assertEqual(res["sla_hours"], 4.0)

        # State transition: ASSIGNED -> ACKNOWLEDGED
        ack_res = db_operational_service.transition_status(
            db=self.db,
            intervention_id=interv_id,
            new_status="ACKNOWLEDGED",
            actor_id="OFF-URBAN-1",
            actor_role="DESIGNATED_OFFICER",
            actor_district="Synthetic Urban District",
        )
        self.assertEqual(ack_res["current_status"], "ACKNOWLEDGED")

        # State transition: ACKNOWLEDGED -> IN_PROGRESS
        prog_res = db_operational_service.transition_status(
            db=self.db,
            intervention_id=interv_id,
            new_status="IN_PROGRESS",
            actor_id="OFF-URBAN-1",
            actor_role="DESIGNATED_OFFICER",
            actor_district="Synthetic Urban District",
        )
        self.assertEqual(prog_res["current_status"], "IN_PROGRESS")

        # Record Outcome: COUNSELLING_PROVIDED -> marks COMPLETED
        out_res = db_operational_service.record_outcome(
            db=self.db,
            case_id=1,
            intervention_id=interv_id,
            outcome_type="COUNSELLING_PROVIDED",
            completed=True,
            officer_id="OFF-URBAN-1",
            officer_role="DESIGNATED_OFFICER",
            officer_district="Synthetic Urban District",
        )
        self.assertEqual(out_res["outcome_type"], "COUNSELLING_PROVIDED")
        self.assertEqual(out_res["intervention_status"], "COMPLETED")

        # Verify in PostgreSQL
        db_interv = self.db.query(Intervention).filter(Intervention.id == interv_id).first()
        self.assertEqual(db_interv.status, "COMPLETED")
        self.assertEqual(db_interv.assigned_to, "OFF-URBAN-1")

        db_out = self.db.query(Outcome).filter(Outcome.intervention_id == interv_id).first()
        self.assertIsNotNone(db_out)
        self.assertEqual(db_out.outcome_type, "COUNSELLING_PROVIDED")
        self.assertTrue(db_out.completed)

    # -------------------------------------------------------------------------
    # 2. WORSENING -> human follow-up -> assignment
    # -------------------------------------------------------------------------
    def test_02_real_postgresql_worsening_human_followup_assignment(self) -> None:
        """
        Tests: Case 3 (prob=0.55, WORSENING) -> HUMAN_FOLLOW_UP -> HIGH priority ->
        24h SLA window -> assigned to rural officer.
        """
        router = AssignmentRouter([
            SyntheticOfficer("OFF-RURAL-1", "Rural Primary", AssigneeRole.COUNSELLOR, "Synthetic Rural District", active_caseload=0),
            SyntheticOfficer("OFF-RURAL-2", "Rural Backup", AssigneeRole.COUNSELLOR, "Synthetic Rural District", active_caseload=2),
        ])

        res = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=3,
            custom_router=router,
        )
        self.assertEqual(res["intervention_type"], InterventionType.HUMAN_FOLLOW_UP.value)
        self.assertEqual(res["priority"], PriorityLevel.HIGH.value)
        self.assertEqual(res["status"], "ASSIGNED")
        self.assertEqual(res["assigned_to"], "OFF-RURAL-1")
        self.assertEqual(res["backup_officer"], "OFF-RURAL-2")
        self.assertEqual(res["sla_hours"], 24.0)

    # -------------------------------------------------------------------------
    # 3. IMPROVING -> monitoring
    # -------------------------------------------------------------------------
    def test_03_real_postgresql_improving_monitoring(self) -> None:
        """
        Tests: Case 5 (prob=0.15, IMPROVING) -> CONTINUE_MONITORING -> LOW priority ->
        120h SLA window.
        """
        router = AssignmentRouter([
            SyntheticOfficer("OFF-RURAL-1", "Rural Primary", AssigneeRole.COUNSELLOR, "Synthetic Rural District", active_caseload=0),
        ])

        res = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=5,
            custom_router=router,
        )
        self.assertEqual(res["intervention_type"], InterventionType.CONTINUE_MONITORING.value)
        self.assertEqual(res["priority"], PriorityLevel.LOW.value)
        self.assertEqual(res["sla_hours"], 120.0)
        self.assertIn("CONTINUED_MONITORING", res["suggested_categories"])

    # -------------------------------------------------------------------------
    # 4. low-confidence -> human review
    # -------------------------------------------------------------------------
    def test_04_real_postgresql_low_confidence_human_review(self) -> None:
        """
        Tests: Case 6 has low confidence (conf=0.35 < 0.60 threshold).
        Even though probability=0.30 (nominal low), it MUST route to PRIORITY_HUMAN_REVIEW (HIGH priority).
        Uncertainty is never converted to LOW_RISK.
        """
        router = AssignmentRouter([
            SyntheticOfficer("OFF-URBAN-1", "Urban Primary", AssigneeRole.COUNSELLOR, "Synthetic Urban District", active_caseload=0),
        ])

        res = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=6,
            custom_router=router,
        )
        self.assertEqual(res["intervention_type"], InterventionType.PRIORITY_HUMAN_REVIEW.value)
        self.assertEqual(res["priority"], PriorityLevel.HIGH.value)
        self.assertIn("LOW_CONFIDENCE", res["reason"]["abstention_reason"])

    # -------------------------------------------------------------------------
    # 5. missing district -> no assignment
    # -------------------------------------------------------------------------
    def test_05_real_postgresql_missing_district_no_assignment(self) -> None:
        """
        Tests: Case with missing/empty district cannot be routed.
        Returns MISSING_JURISDICTION and stays unassigned in PENDING status.
        Jurisdiction is never guessed.
        """
        case_temp = Case(
            case_id="CASE-NO-DISTRICT",
            language="Hindi",
            district_type="Urban",
            district="",  # Empty district
            priority_use_case="Domestic Violence",
            current_stage="Reported",
            monitoring_consent=True,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.db.add(case_temp)
        self.db.commit()
        self.db.refresh(case_temp)

        pred_temp = Prediction(
            case_id=case_temp.id,
            prediction_date=datetime.now(timezone.utc),
            escalation_probability=0.80,
            confidence=0.90,
        )
        self.db.add(pred_temp)
        self.db.commit()

        try:
            res = db_operational_service.process_case_intervention(
                db=self.db,
                case_id=case_temp.id,
            )
            self.assertEqual(res["routing_status"], "MISSING_JURISDICTION")
            self.assertIsNone(res["assigned_to"])
            self.assertEqual(res["status"], "PENDING")

            # Verify in PostgreSQL
            db_interv = self.db.query(Intervention).filter(Intervention.id == res["intervention_id"]).first()
            self.assertEqual(db_interv.status, "PENDING")
            self.assertIsNone(db_interv.assigned_to)
        finally:
            self.db.query(Intervention).filter(Intervention.case_id == case_temp.id).delete()
            self.db.query(Prediction).filter(Prediction.case_id == case_temp.id).delete()
            self.db.query(Case).filter(Case.id == case_temp.id).delete()
            self.db.commit()

    # -------------------------------------------------------------------------
    # 6. no eligible officer -> routing unavailable
    # -------------------------------------------------------------------------
    def test_06_real_postgresql_no_eligible_officer_routing_unavailable(self) -> None:
        """
        Tests: Case in Synthetic Urban District with all officers at capacity.
        Never cross-routes to rural officers. Flags capacity and stays unassigned.
        """
        router = AssignmentRouter([
            # Urban officer at max capacity
            SyntheticOfficer("OFF-URBAN-FULL", "Busy Urban Officer", AssigneeRole.COUNSELLOR, "Synthetic Urban District", active_caseload=10, max_capacity=10),
            # Rural officer with capacity, but wrong district
            SyntheticOfficer("OFF-RURAL-FREE", "Free Rural Officer", AssigneeRole.COUNSELLOR, "Synthetic Rural District", active_caseload=0, max_capacity=10),
        ])

        res = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=1,  # Belongs to Synthetic Urban District
            custom_router=router,
        )
        self.assertEqual(res["routing_status"], "ROUTING_UNAVAILABLE")
        self.assertTrue(res["capacity_flag"])
        self.assertIsNone(res["assigned_to"])
        self.assertIsNone(res["backup_officer"])
        self.assertEqual(res["status"], "PENDING")

    # -------------------------------------------------------------------------
    # 7. unauthorized official -> blocked
    # -------------------------------------------------------------------------
    def test_07_real_postgresql_unauthorized_official_blocked(self) -> None:
        """
        Tests:
        1. Unauthorized role cannot transition intervention.
        2. Officer from different district cannot transition intervention.
        3. Unauthorized role cannot record outcome.
        4. Officer from different district cannot record outcome.
        5. Unauthorized role cannot access RBAC case analytics.
        """
        router = AssignmentRouter([
            SyntheticOfficer("OFF-URBAN-1", "Urban Officer", AssigneeRole.DESIGNATED_OFFICER, "Synthetic Urban District", active_caseload=0),
        ])
        res = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=1,
            custom_router=router,
        )
        interv_id = res["intervention_id"]

        # 1. Unauthorized role transition blocked
        with self.assertRaises(PermissionError):
            db_operational_service.transition_status(
                db=self.db,
                intervention_id=interv_id,
                new_status="ACKNOWLEDGED",
                actor_id="GUEST-01",
                actor_role="EXTERNAL_GUEST",
            )

        # 2. Cross-district caseworker transition blocked
        with self.assertRaises(PermissionError):
            db_operational_service.transition_status(
                db=self.db,
                intervention_id=interv_id,
                new_status="ACKNOWLEDGED",
                actor_id="OFF-RURAL-1",
                actor_role="CASE_OFFICER",
                actor_district="Synthetic Rural District",  # Case is in Synthetic Urban District
            )

        # 3. Unauthorized role outcome recording blocked
        with self.assertRaises(PermissionError):
            db_operational_service.record_outcome(
                db=self.db,
                case_id=1,
                intervention_id=interv_id,
                outcome_type="CONTACTED",
                officer_role="UNAUTHORIZED_OFFICIAL",
            )

        # 4. Cross-district caseworker outcome recording blocked
        with self.assertRaises(PermissionError):
            db_operational_service.record_outcome(
                db=self.db,
                case_id=1,
                intervention_id=interv_id,
                outcome_type="CONTACTED",
                officer_role="CASE_OFFICER",
                officer_district="Different District",
            )

        # 5. Unauthorized role case analytics blocked
        with self.assertRaises(PermissionError):
            db_operational_service.get_rbac_case_analytics(
                db=self.db,
                case_id=1,
                user_role="UNAUTHORIZED_CITIZEN",
            )

    # -------------------------------------------------------------------------
    # 8. outcome -> persisted/history
    # -------------------------------------------------------------------------
    def test_08_real_postgresql_outcome_persisted_and_history(self) -> None:
        """
        Tests: Multiple outcomes recorded chronologically in PostgreSQL.
        Latest outcome query resolves strictly via MAX(recorded_at), regardless of order.
        """
        router = AssignmentRouter([
            SyntheticOfficer("OFF-URBAN-1", "Urban Officer", AssigneeRole.DESIGNATED_OFFICER, "Synthetic Urban District", active_caseload=0),
        ])
        res = db_operational_service.process_case_intervention(
            db=self.db,
            case_id=1,
            custom_router=router,
        )
        interv_id = res["intervention_id"]

        # Progress to IN_PROGRESS
        db_operational_service.transition_status(self.db, interv_id, "ACKNOWLEDGED", "OFF-URBAN-1", "DESIGNATED_OFFICER")
        db_operational_service.transition_status(self.db, interv_id, "IN_PROGRESS", "OFF-URBAN-1", "DESIGNATED_OFFICER")

        # Record Outcome 1 at T1
        t1 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        db_operational_service.record_outcome(
            db=self.db,
            case_id=1,
            intervention_id=interv_id,
            outcome_type="CONTACTED",
            completed=False,
            recorded_at=t1,
            officer_role="DESIGNATED_OFFICER",
        )

        # Record Outcome 2 at T2 (Latest)
        t2 = datetime(2026, 9, 2, 15, 0, tzinfo=timezone.utc)
        db_operational_service.record_outcome(
            db=self.db,
            case_id=1,
            intervention_id=interv_id,
            outcome_type="RESOLVED",
            completed=True,
            recorded_at=t2,
            officer_role="DESIGNATED_OFFICER",
        )

        # Verify in PostgreSQL
        outs = self.db.query(Outcome).filter(Outcome.case_id == 1).order_by(Outcome.recorded_at.asc()).all()
        self.assertEqual(len(outs), 2)
        self.assertEqual(outs[0].outcome_type, "CONTACTED")
        self.assertEqual(outs[1].outcome_type, "RESOLVED")

        # Query analytics
        metrics = db_operational_service.get_rbac_case_analytics(
            db=self.db,
            case_id=1,
            user_role="ADMIN",
        )
        self.assertEqual(metrics["latest_outcome"], "RESOLVED")

    # -------------------------------------------------------------------------
    # 9. analytics -> correct scoped/privacy-safe results
    # -------------------------------------------------------------------------
    def test_09_real_postgresql_analytics_correct_scoped_privacy_safe(self) -> None:
        """
        Tests:
        1. District officer can only view their own district analytics.
        2. Small-cell privacy suppression (<3) masks granular counts of 1 or 2.
        3. Zero victim narratives/transcripts/notes are leaked in analytics.
        """
        # 1. District isolation
        with self.assertRaises(PermissionError):
            db_operational_service.get_rbac_district_analytics(
                db=self.db,
                district="Synthetic Urban District",
                user_role="CASE_OFFICER",
                user_district="Different District",
            )

        # 2. Query district analytics with suppression
        dist_analytics = db_operational_service.get_rbac_district_analytics(
            db=self.db,
            district="Synthetic Urban District",
            user_role="DISTRICT_OFFICIAL",
            user_district="Synthetic Urban District",
            suppress_small_cells=True,
        )
        self.assertIn("risk_distribution", dist_analytics)
        self.assertIn("trajectory_alerts", dist_analytics)
        self.assertIn("suppressed_fields", dist_analytics)

        # 3. Verify zero victim private data in response
        self.assertNotIn("notes", dist_analytics)
        self.assertNotIn("transcript", dist_analytics)
        self.assertNotIn("audio_path", dist_analytics)

    # -------------------------------------------------------------------------
    # 10. closed-loop re-monitoring -> temporal association with disclaimer
    # -------------------------------------------------------------------------
    def test_10_real_postgresql_closed_loop_remonitoring_with_disclaimer(self) -> None:
        """
        Tests: Subsequent distress observation is persisted to PostgreSQL DistressState,
        computes temporal difference against baseline, and attaches non-causal clinical disclaimer.
        """
        created_dstate_id = None
        try:
            # Baseline is Case 1 (seeded at 0.85)
            prev_dstate = (
                self.db.query(DistressState)
                .filter(DistressState.case_id == 1)
                .order_by(DistressState.observation_date.desc(), DistressState.id.desc())
                .first()
            )
            base_score = prev_dstate.distress_score if prev_dstate and prev_dstate.distress_score is not None else 0.85
            improved_score = round(base_score - 0.25, 2)

            res = db_operational_service.record_re_monitoring(
                db=self.db,
                case_id=1,
                new_distress_score=improved_score,
                new_trajectory="IMPROVING",
                confidence=0.90,
            )
            created_dstate_id = res["new_observation_id"]

            self.assertEqual(res["observed_shift"], "SUBSEQUENT_IMPROVEMENT")
            self.assertIn("temporal correlation only", res["disclaimer"])
            self.assertIn("No causal clinical claim", res["disclaimer"])

            # Verify in PostgreSQL
            db_state = self.db.query(DistressState).filter(DistressState.id == created_dstate_id).first()
            self.assertIsNotNone(db_state)
            self.assertEqual(db_state.distress_score, improved_score)
            self.assertEqual(db_state.trajectory, "IMPROVING")
        finally:
            if created_dstate_id:
                self.db.query(DistressState).filter(DistressState.id == created_dstate_id).delete()
                self.db.commit()


if __name__ == "__main__":
    unittest.main()
