"""
AAROH Day 3 Focused Integration & Regression Test Suite
Author: Preet

Verifies the complete operational flow against PostgreSQL and business logic:
1. Prediction -> Intervention Mapping (HIGH, WORSENING, IMPROVING, low-confidence, consent).
2. All 8 Authorized Intervention Categories.
3. District Routing (isolation, primary + backup, capacity flag, MISSING_JURISDICTION).
4. Assignment State Machine (transitions, invalid jumps, terminal rejection, ESCALATED).
5. SLA Deadlines (URGENT 4h, HIGH 24h, ROUTINE 72h, LOW 120h, UTC-aware, overdue).
6. Outcome Recording & MAX(recorded_at) resolution.
7. Closed-Loop Distress Re-monitoring (temporal association, no causal claim).
8. Role-Appropriate Notifications (victim privacy guard).
9. RBAC-Aware Multi-Tier Analytics (authorization, K<3 suppression, sound rollups).
10. Complete PostgreSQL Database Flow.
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
    SLARecord,
    SLAStatus,
    DEFAULT_SLA_RULES,
    ensure_utc,
)
from backend.interventions.outcomes import (
    OutcomeManager,
    OutcomeType,
    OutcomeRecord,
    ClosedLoopObservation,
)
from backend.interventions.notifications import (
    notification_service,
    NotificationRecipientRole,
    NotificationType,
)
from backend.interventions.service import (
    OperationalInterventionService,
    intervention_service,
)
from backend.interventions.db_service import (
    DatabaseOperationalService,
    db_operational_service,
)
from backend.analytics.district_metrics import DistrictSummaryMetrics


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestDay3OperationalFlow(unittest.TestCase):
    engine_pg = None
    Session = None

    @classmethod
    def setUpClass(cls):
        pg_url = os.environ.get("DATABASE_URL")
        if not pg_url or "sqlite" in pg_url:
            pg_url = "postgresql://postgres:root@localhost:5432/aaroh_db"
        try:
            cls.engine_pg = create_engine(pg_url, pool_pre_ping=True)
            with cls.engine_pg.connect() as conn:
                pass
            cls.Session = sessionmaker(bind=cls.engine_pg, autocommit=False, autoflush=False)
        except Exception:
            cls.Session = None

    def setUp(self) -> None:
        self.engine = InterventionEngine()
        self.sla_manager = SLAManager()
        self.service = OperationalInterventionService()
        if self.Session:
            self.db = self.Session()
        else:
            self.db = SessionLocal()

    def tearDown(self) -> None:
        self.db.close()

    # -------------------------------------------------------------------------
    # 1. Prediction -> Approved Intervention Mapping (HIGH, WORSENING, IMPROVING)
    # -------------------------------------------------------------------------
    def test_01_high_and_rapidly_worsening_mapping(self) -> None:
        """HIGH risk and RAPIDLY_WORSENING trajectory map to PRIORITY_HUMAN_REVIEW with URGENT priority."""
        decision = self.engine.evaluate(
            case_id="CASE-TEST-HIGH",
            risk_level="HIGH",
            escalation_probability=0.88,
            trajectory="RAPIDLY_WORSENING",
            confidence=0.95,
            factors=["acute fear", "severe intimidation"],
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.PRIORITY_HUMAN_REVIEW)
        self.assertEqual(decision.priority, PriorityLevel.URGENT)
        self.assertIn(InterventionCategory.COUNSELLING_PSYCHOLOGICAL_SUPPORT, decision.suggested_categories)
        self.assertIn(InterventionCategory.RELOCATION_SAFETY_SUPPORT, decision.suggested_categories)
        self.assertIn(InterventionCategory.WITNESS_PROTECTION_SUPPORT, decision.suggested_categories)

    def test_02_moderate_and_worsening_mapping(self) -> None:
        """MODERATE risk and WORSENING trajectory map to HUMAN_FOLLOW_UP with HIGH priority."""
        decision = self.engine.evaluate(
            case_id="CASE-TEST-MOD",
            risk_level="MODERATE",
            escalation_probability=0.55,
            trajectory="WORSENING",
            confidence=0.85,
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.HUMAN_FOLLOW_UP)
        self.assertEqual(decision.priority, PriorityLevel.HIGH)
        self.assertIn(InterventionCategory.COUNSELLING_PSYCHOLOGICAL_SUPPORT, decision.suggested_categories)
        self.assertIn(InterventionCategory.REHABILITATION_SUPPORT, decision.suggested_categories)

    def test_03_improving_trajectory_mapping(self) -> None:
        """IMPROVING trajectory maps to CONTINUE_MONITORING with LOW priority."""
        decision = self.engine.evaluate(
            case_id="CASE-TEST-IMP",
            risk_level="LOW",
            escalation_probability=0.15,
            trajectory="IMPROVING",
            confidence=0.90,
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.CONTINUE_MONITORING)
        self.assertEqual(decision.priority, PriorityLevel.LOW)

    def test_04_uncertainty_and_abstention_never_low_risk(self) -> None:
        """LOW_CONFIDENCE, ABSTAINED, and INSUFFICIENT_DATA route to human review, never LOW_RISK."""
        for ml_st in ("LOW_CONFIDENCE", "ABSTAINED", "INSUFFICIENT_DATA"):
            decision = self.engine.evaluate(
                case_id="CASE-TEST-UNC",
                risk_level="LOW",
                escalation_probability=0.10,
                trajectory="STABLE",
                confidence=0.30,
                ml_status=ml_st,
                monitoring_consent=True,
            )
            self.assertEqual(decision.intervention_type, InterventionType.PRIORITY_HUMAN_REVIEW)
            self.assertEqual(decision.priority, PriorityLevel.HIGH)
            self.assertIn(ml_st, decision.reason.abstention_reason)

    def test_05_consent_revocation_blocks_intervention(self) -> None:
        """Absence of monitoring consent strictly halts automated interventions."""
        decision = self.engine.evaluate(
            case_id="CASE-TEST-NOCONSENT",
            risk_level="HIGH",
            escalation_probability=0.95,
            trajectory="RAPIDLY_WORSENING",
            monitoring_consent=False,
        )
        self.assertEqual(decision.intervention_type, InterventionType.NO_AUTOMATED_INTERVENTION)
        self.assertEqual(decision.priority, PriorityLevel.NONE)

    # -------------------------------------------------------------------------
    # 2. All 8 Intervention Categories
    # -------------------------------------------------------------------------
    def test_06_all_eight_intervention_categories_available(self) -> None:
        """Verifies all 8 authorized intervention categories exist."""
        expected_categories = {
            "COUNSELLING_PSYCHOLOGICAL_SUPPORT",
            "MEDICAL_TREATMENT_REFERRAL",
            "WITNESS_PROTECTION_SUPPORT",
            "RELOCATION_SAFETY_SUPPORT",
            "FINANCIAL_COMPENSATION_ASSISTANCE",
            "LEGAL_AID",
            "REHABILITATION_SUPPORT",
            "CONTINUED_MONITORING",
        }
        actual_categories = {c.value for c in InterventionCategory}
        self.assertEqual(expected_categories, actual_categories)

    # -------------------------------------------------------------------------
    # 3. District-Aware Routing & Jurisdiction
    # -------------------------------------------------------------------------
    def test_07_strict_district_isolation_and_no_cross_routing(self) -> None:
        """Never cross-routes across districts; primary and backup must belong to target district."""
        officers = [
            SyntheticOfficer("OFF-PATNA-1", "Patna Primary", AssigneeRole.COUNSELLOR, "Patna", active_caseload=1),
            SyntheticOfficer("OFF-PATNA-2", "Patna Backup", AssigneeRole.COUNSELLOR, "Patna", active_caseload=3),
            SyntheticOfficer("OFF-RANCHI-1", "Ranchi Officer", AssigneeRole.COUNSELLOR, "Ranchi", active_caseload=0),
        ]
        router = AssignmentRouter(officers=officers)
        res = router.route(
            case_id="CASE-PATNA-01",
            district="Patna",
            intervention_type=InterventionType.HUMAN_FOLLOW_UP,
            priority=PriorityLevel.HIGH,
        )
        self.assertEqual(res.status, RoutingStatus.ASSIGNED)
        self.assertEqual(res.primary_assignee, "OFF-PATNA-1")
        self.assertEqual(res.backup_assignee, "OFF-PATNA-2")
        self.assertFalse(res.capacity_flag)

    def test_08_missing_jurisdiction_returns_missing_jurisdiction(self) -> None:
        """Missing or empty district returns status MISSING_JURISDICTION."""
        router = AssignmentRouter()
        for empty_val in (None, "", "   "):
            res = router.route(
                case_id="CASE-NO-JURISDICTION",
                district=empty_val,
                intervention_type=InterventionType.PRIORITY_HUMAN_REVIEW,
                priority=PriorityLevel.URGENT,
            )
            self.assertEqual(res.status, RoutingStatus.MISSING_JURISDICTION)
            self.assertIsNone(res.primary_assignee)
            self.assertIsNone(res.backup_assignee)

    def test_09_unassigned_and_capacity_flag_when_officers_at_capacity(self) -> None:
        """If all officers in district are at max capacity, case remains unassigned with capacity flag."""
        officers = [
            SyntheticOfficer("OFF-FULL-1", "Full Officer", AssigneeRole.COUNSELLOR, "Bhopal", active_caseload=10, max_capacity=10),
        ]
        router = AssignmentRouter(officers=officers)
        res = router.route(
            case_id="CASE-BHOPAL-FULL",
            district="Bhopal",
            intervention_type=InterventionType.HUMAN_FOLLOW_UP,
            priority=PriorityLevel.HIGH,
        )
        self.assertEqual(res.status, RoutingStatus.ROUTING_UNAVAILABLE)
        self.assertIsNone(res.primary_assignee)
        self.assertTrue(res.capacity_flag)

    # -------------------------------------------------------------------------
    # 4. Assignment State Machine
    # -------------------------------------------------------------------------
    def test_10_assignment_state_machine_valid_and_invalid_transitions(self) -> None:
        """Valid progression succeeds; invalid skips and terminal reversions raise ValueError."""
        # Valid progression: PENDING -> ASSIGNED -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED
        OutcomeManager.transition_status(InterventionStatus.PENDING, InterventionStatus.ASSIGNED)
        OutcomeManager.transition_status(InterventionStatus.ASSIGNED, InterventionStatus.ACKNOWLEDGED)
        OutcomeManager.transition_status(InterventionStatus.ACKNOWLEDGED, InterventionStatus.IN_PROGRESS)
        OutcomeManager.transition_status(InterventionStatus.IN_PROGRESS, InterventionStatus.COMPLETED)

        # Escalation path
        OutcomeManager.transition_status(InterventionStatus.IN_PROGRESS, InterventionStatus.ESCALATED)
        OutcomeManager.transition_status(InterventionStatus.ESCALATED, InterventionStatus.IN_PROGRESS)

        # Invalid terminal transition: COMPLETED -> PENDING
        with self.assertRaises(ValueError):
            OutcomeManager.transition_status(InterventionStatus.COMPLETED, InterventionStatus.PENDING)

        # Invalid shortcut: PENDING -> COMPLETED
        with self.assertRaises(ValueError):
            OutcomeManager.transition_status(InterventionStatus.PENDING, InterventionStatus.COMPLETED)

    # -------------------------------------------------------------------------
    # 5. SLA Deadlines & UTC Standardization
    # -------------------------------------------------------------------------
    def test_11_sla_deadlines_and_overdue_logic(self) -> None:
        """SLA windows (URGENT 4h, HIGH 24h, ROUTINE 72h, LOW 120h) and overdue evaluation."""
        now = datetime.now(timezone.utc)
        record = self.sla_manager.create_record(
            intervention_id=1,
            priority=PriorityLevel.URGENT,
            start_time=now,
        )
        self.assertAlmostEqual((record.due_at - record.created_at).total_seconds() / 3600.0, 4.0)

        # Not overdue within window
        self.assertFalse(record.is_overdue(now + timedelta(hours=2)))
        self.assertEqual(record.evaluate_status(now + timedelta(hours=2)), SLAStatus.PENDING)

        # Due soon at 85% elapsed
        self.assertEqual(record.evaluate_status(now + timedelta(hours=3.5)), SLAStatus.DUE_SOON)

        # Overdue past deadline when uncompleted
        self.assertTrue(record.is_overdue(now + timedelta(hours=5)))
        self.assertEqual(record.evaluate_status(now + timedelta(hours=5)), SLAStatus.OVERDUE)

        # Once completed within window -> MET (never actively overdue)
        record.completed_at = now + timedelta(hours=2)
        self.assertFalse(record.is_overdue(now + timedelta(hours=10)))
        self.assertEqual(record.evaluate_status(), SLAStatus.MET)

        # Once completed after window -> BREACHED (never actively overdue)
        record.completed_at = now + timedelta(hours=6)
        self.assertFalse(record.is_overdue(now + timedelta(hours=10)))
        self.assertEqual(record.evaluate_status(), SLAStatus.BREACHED)

    # -------------------------------------------------------------------------
    # 6. Outcome Recording & MAX(recorded_at)
    # -------------------------------------------------------------------------
    def test_12_latest_outcome_selected_by_max_recorded_at(self) -> None:
        """Latest outcome is resolved strictly by MAX(recorded_at) regardless of list order."""
        t1 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)
        t3 = datetime(2026, 9, 3, 14, 0, tzinfo=timezone.utc)

        outcomes = [
            {"outcome_type": "CONTACTED", "recorded_at": t1.isoformat()},
            {"outcome_type": "RESOLVED", "recorded_at": t3.isoformat()},  # LATEST
            {"outcome_type": "COUNSELLING_PROVIDED", "recorded_at": t2.isoformat()},
        ]
        metrics = self.service.get_case_analytics(
            case_id="CASE-MAX-OUT",
            distress_score=0.40,
            trajectory="STABLE",
            escalation_prob=0.30,
            risk_level="LOW",
            confidence=0.90,
            outcomes=outcomes,
        )
        self.assertEqual(metrics["latest_outcome"], "RESOLVED")

    # -------------------------------------------------------------------------
    # 7. Closed-Loop Distress Re-monitoring
    # -------------------------------------------------------------------------
    def test_13_closed_loop_tracking_reports_temporal_association(self) -> None:
        """Evaluates subsequent distress difference as temporal association without causal claim."""
        cl = ClosedLoopObservation(
            case_id="CASE-CL-01",
            intervention_id=1,
            outcome_type=OutcomeType.COUNSELLING_PROVIDED,
            pre_distress_score=0.85,
            pre_trajectory="RAPIDLY_WORSENING",
        )
        shift = cl.evaluate_shift(post_score=0.60, post_trajectory="IMPROVING")
        self.assertEqual(shift, "SUBSEQUENT_IMPROVEMENT")

    # -------------------------------------------------------------------------
    # 8. Role-Appropriate Notifications & Victim Privacy
    # -------------------------------------------------------------------------
    def test_14_role_appropriate_notifications_and_victim_privacy(self) -> None:
        """Internal police/caseworker alerts must never leak to victims."""
        # Official notification preserves metadata
        officer_notif = notification_service.notify(
            recipient_role=NotificationRecipientRole.CASE_OFFICER,
            recipient_id="OFF-01",
            notification_type=NotificationType.INTERVENTION_ASSIGNED,
            title="High Escalation Case Assigned",
            message="Escalation probability is 0.88. Urgent 4h response window.",
            case_id="CASE-PRIV-01",
            metadata={"risk_level": "HIGH", "escalation_probability": 0.88},
        )
        self.assertIn("0.88", officer_notif.message)
        self.assertEqual(officer_notif.metadata.get("risk_level"), "HIGH")

        # Victim notification sanitizes internal leaks
        victim_notif = notification_service.notify(
            recipient_role=NotificationRecipientRole.VICTIM,
            recipient_id="VICTIM-01",
            notification_type=NotificationType.SUPPORT_UPDATE,
            title="High Escalation Case Assigned",
            message="Internal Alert: Escalation probability is 0.88. Urgent 4h response.",
            case_id="CASE-PRIV-01",
            metadata={"risk_level": "HIGH", "escalation_probability": 0.88},
        )
        self.assertNotIn("0.88", victim_notif.message)
        self.assertNotIn("escalation", victim_notif.message.lower())
        self.assertEqual(victim_notif.metadata, {})
        self.assertEqual(victim_notif.title, "AAROH Support Services Update")

    # -------------------------------------------------------------------------
    # 9. RBAC-Aware Analytics & Small-Cell Privacy
    # -------------------------------------------------------------------------
    def test_15_rbac_authorization_and_privacy_suppression(self) -> None:
        """Caseworker cross-district access is blocked; K<3 privacy masks sparse counts."""
        if not self.db.query(Case).filter(Case.id == 1).first():
            self.skipTest("Test Case 1 not found in database.")
        # 1. RBAC cross-district block
        with self.assertRaises(PermissionError):
            db_operational_service.get_rbac_case_analytics(
                db=self.db,
                case_id=1,  # Belongs to Synthetic Urban District
                user_role="CASE_OFFICER",
                user_district="Different District",
            )

        # 2. Small-cell suppression
        cases = [
            {"risk_level": "HIGH", "trajectory": "RAPIDLY_WORSENING"},
            {"risk_level": "LOW", "trajectory": "STABLE"},
            {"risk_level": "LOW", "trajectory": "STABLE"},
            {"risk_level": "LOW", "trajectory": "STABLE"},
        ]
        dist_res = self.service.get_district_analytics(
            district="Bhopal",
            case_records=cases,
            intervention_records=[],
            outcome_records=[],
            suppress_small_cells=True,
        )
        self.assertEqual(dist_res["total_monitored_cases"], 4)
        self.assertEqual(dist_res["risk_distribution"]["HIGH"], "<3")  # Count 1 masked
        self.assertEqual(dist_res["risk_distribution"]["LOW"], 3)     # Count 3 unmasked

    # -------------------------------------------------------------------------
    # 10. End-to-End PostgreSQL Integration
    # -------------------------------------------------------------------------
    def test_16_end_to_end_postgresql_workflow(self) -> None:
        """
        Executes full workflow against PostgreSQL:
        Prediction -> Intervention -> Routing -> Status Transitions -> Outcome -> Re-monitoring
        """
        if not self.db.query(Case).filter(Case.id == 1).first():
            self.skipTest("Test Case 1 not found in database.")
        router = AssignmentRouter([
            SyntheticOfficer("OFF-URBAN-1", "Urban Officer", AssigneeRole.DESIGNATED_OFFICER, "Synthetic Urban District", active_caseload=0),
            SyntheticOfficer("OFF-URBAN-2", "Urban Counsellor", AssigneeRole.COUNSELLOR, "Synthetic Urban District", active_caseload=1),
        ])

        # Clean up any existing test interventions for case 1
        self.db.query(Outcome).filter(Outcome.case_id == 1).delete()
        self.db.query(Intervention).filter(Intervention.case_id == 1).delete()
        self.db.commit()

        created_dstate_id = None
        created_interv_id = None
        try:
            # 1. Create Intervention from Prediction
            res_interv = db_operational_service.process_case_intervention(
                db=self.db,
                case_id=1,
                custom_router=router,
            )
            interv_id = res_interv["intervention_id"]
            created_interv_id = interv_id
            self.assertIsNotNone(interv_id)

            # 2. Transition State Machine: ASSIGNED -> ACKNOWLEDGED -> IN_PROGRESS
            res_ack = db_operational_service.transition_status(
                db=self.db,
                intervention_id=interv_id,
                new_status="ACKNOWLEDGED",
                actor_id="OFF-URBAN-1",
                actor_role="DESIGNATED_OFFICER",
            )
            self.assertEqual(res_ack["current_status"], "ACKNOWLEDGED")

            res_prog = db_operational_service.transition_status(
                db=self.db,
                intervention_id=interv_id,
                new_status="IN_PROGRESS",
                actor_id="OFF-URBAN-1",
                actor_role="DESIGNATED_OFFICER",
            )
            self.assertEqual(res_prog["current_status"], "IN_PROGRESS")

            # 3. Record Outcome in PostgreSQL
            res_out = db_operational_service.record_outcome(
                db=self.db,
                case_id=1,
                intervention_id=interv_id,
                outcome_type="COUNSELLING_PROVIDED",
                completed=True,
                notes="Session completed successfully.",
            )
            self.assertEqual(res_out["outcome_type"], "COUNSELLING_PROVIDED")
            self.assertEqual(res_out["intervention_status"], "COMPLETED")

            # 4. Record Subsequent Re-monitoring Observation in PostgreSQL
            prev_state = (
                self.db.query(DistressState)
                .filter(DistressState.case_id == 1)
                .order_by(DistressState.observation_date.desc(), DistressState.id.desc())
                .first()
            )
            base_score = prev_state.distress_score if prev_state and prev_state.distress_score is not None else 0.85
            improved_score = round(base_score - 0.25, 2)

            res_remon = db_operational_service.record_re_monitoring(
                db=self.db,
                case_id=1,
                new_distress_score=improved_score,
                new_trajectory="IMPROVING",
            )
            created_dstate_id = res_remon["new_observation_id"]
            self.assertEqual(res_remon["observed_shift"], "SUBSEQUENT_IMPROVEMENT")
            self.assertIn("temporal correlation only", res_remon["disclaimer"])
        finally:
            if created_dstate_id:
                self.db.query(DistressState).filter(DistressState.id == created_dstate_id).delete()
            if created_interv_id:
                self.db.query(Outcome).filter(Outcome.case_id == 1).delete()
                self.db.query(Intervention).filter(Intervention.case_id == 1).delete()
            self.db.commit()


if __name__ == "__main__":
    unittest.main()
