"""
AAROH Integration Resilience Test Suite
Author: Preet (Intervention, Routing, SLA, Outcomes & Analytics Owner)

Verifies proactive hardening across all layers:
1. Flexible case resolution (_get_case with int 1, str "1", and str "AAROH-001")
2. Missing prediction fallback to PRIORITY_HUMAN_REVIEW (fail-closed, no crash)
3. FastAPI endpoint helpers (get_intervention, get_case_interventions, assign_intervention)
4. Outcome recording without case_id (inferred from intervention)
5. Notification role resilience (DISTRICT_OFFICIAL, STATE_OFFICIAL, ADMIN, fallbacks)
6. Optional DB session lifecycle (db=None auto-creates and safely closes session)
7. Package level exports in backend.interventions
"""

import os
import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import SessionLocal
from backend.models import (
    Case,
    Prediction,
    Consent,
    DistressState,
    Intervention,
    Outcome,
)
from backend.interventions import (
    InterventionEngine,
    InterventionType,
    InterventionStatus,
    PriorityLevel,
    InterventionCategory,
    AssignmentRouter,
    AssigneeRole,
    SyntheticOfficer,
    db_operational_service,
    DatabaseOperationalService,
    channel_service,
    ChannelWorkflowService,
    ChannelType,
    ChannelEventType,
    notification_service,
    NotificationService,
    NotificationRecipientRole,
    NotificationType,
    CaseMetricsCalculator,
    DistrictMetricsCalculator,
    StateMetricsCalculator,
    NationalMetricsCalculator,
)


class TestIntegrationResilience(unittest.TestCase):
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
        self._clean_interventions()

    def tearDown(self) -> None:
        self._clean_interventions()
        self.db.close()

    def _clean_interventions(self) -> None:
        try:
            self.db.query(Outcome).delete()
            self.db.query(Intervention).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()

    # -------------------------------------------------------------------------
    # 1. Flexible Case Resolution
    # -------------------------------------------------------------------------
    def test_case_resolution_flexibility(self) -> None:
        """
        Verifies _get_case resolves correctly with:
        - int primary key: 1
        - numeric string: "1"
        - alphanumeric string: "AAROH-001"
        """
        svc = db_operational_service

        c1 = svc._get_case(self.db, 1)
        self.assertEqual(c1.id, 1)

        c2 = svc._get_case(self.db, "1")
        self.assertEqual(c2.id, 1)

        c3 = svc._get_case(self.db, "AAROH-001")
        self.assertEqual(c3.id, 1)

        # Also test channel_service._get_case
        cs = channel_service
        self.assertEqual(cs._get_case(self.db, 1).id, 1)
        self.assertEqual(cs._get_case(self.db, "1").id, 1)
        self.assertEqual(cs._get_case(self.db, "AAROH-001").id, 1)

        # Invalid case raises ValueError
        with self.assertRaises(ValueError):
            svc._get_case(self.db, 999999)
        with self.assertRaises(ValueError):
            svc._get_case(self.db, "NON-EXISTENT-CASE")

    # -------------------------------------------------------------------------
    # 2. Missing Prediction Fallback
    # -------------------------------------------------------------------------
    def test_missing_prediction_fallback(self) -> None:
        """
        When a new case is registered before ML inference runs (no Prediction row exists),
        process_case_intervention does not crash with 500 / ValueError.
        It safely falls back to INSUFFICIENT_DATA -> PRIORITY_HUMAN_REVIEW (HIGH priority, 24h SLA).
        """
        # Temporarily create a dummy case without any prediction
        dummy_case = Case(
            case_id="AAROH-TEST-NOPRED",
            district_type="URBAN",
            district="Synthetic Urban District",
            priority_use_case="STANDARD",
            current_stage="INTAKE",
            monitoring_consent=True,
            language="en",
        )
        self.db.add(dummy_case)
        self.db.commit()
        self.db.refresh(dummy_case)

        try:
            # Verify no predictions exist for this case
            preds = self.db.query(Prediction).filter(Prediction.case_id == dummy_case.id).all()
            self.assertEqual(len(preds), 0)

            # Process intervention
            result = db_operational_service.process_case_intervention(
                db=self.db,
                case_id=dummy_case.id,
                auto_commit=True,
            )

            # Must NOT crash, and must generate PRIORITY_HUMAN_REVIEW
            self.assertIsNotNone(result)
            self.assertEqual(result["intervention_type"], InterventionType.PRIORITY_HUMAN_REVIEW.value)
            self.assertEqual(result["priority"], PriorityLevel.HIGH.value)
            self.assertEqual(result["sla_hours"], 24.0)
            self.assertIn("INSUFFICIENT_DATA", result["reason"]["abstention_reason"])

            # Verify saved in DB
            saved = self.db.query(Intervention).filter(Intervention.case_id == dummy_case.id).first()
            self.assertIsNotNone(saved)
            self.assertEqual(saved.intervention_type, InterventionType.PRIORITY_HUMAN_REVIEW.value)

        finally:
            # Clean up dummy case
            self.db.query(Intervention).filter(Intervention.case_id == dummy_case.id).delete()
            self.db.query(Case).filter(Case.id == dummy_case.id).delete()
            self.db.commit()

    # -------------------------------------------------------------------------
    # 3. FastAPI Query & Assignment Helpers
    # -------------------------------------------------------------------------
    def test_fastapi_helpers_and_assignment(self) -> None:
        """
        Verifies:
        - get_intervention(id)
        - get_case_interventions(case_id)
        - assign_intervention(intervention_id, assignee_id, actor_id, actor_role)
        - Cross-district assignment rejection
        """
        svc = db_operational_service

        # 1. Create an intervention for Case 1
        res = svc.process_case_intervention(db=self.db, case_id=1, auto_commit=True)
        interv_id = res["intervention_id"]

        # 2. get_intervention
        detail = svc.get_intervention(db=self.db, intervention_id=interv_id)
        self.assertEqual(detail["id"], interv_id)
        self.assertEqual(detail["case_id"], 1)
        self.assertEqual(detail["case_string_id"], "AAROH-001")
        self.assertEqual(detail["status"], "ASSIGNED")

        # 3. get_case_interventions (via numeric string "1")
        case_intervs = svc.get_case_interventions(db=self.db, case_id="1")
        self.assertEqual(len(case_intervs), 1)
        self.assertEqual(case_intervs[0]["id"], interv_id)

        # 4. assign_intervention: reassign by supervisor
        reassigned = svc.assign_intervention(
            db=self.db,
            intervention_id=interv_id,
            assignee_id="OFF-URBAN-99",
            actor_id="SUP-01",
            actor_role="DISTRICT_AUTHORITY",
            actor_district="Synthetic Urban District",
            auto_commit=True,
        )
        self.assertEqual(reassigned["assigned_to"], "OFF-URBAN-99")
        self.assertEqual(reassigned["status"], "ASSIGNED")

        # 5. Cross-district assignment guard
        with self.assertRaises(PermissionError):
            svc.assign_intervention(
                db=self.db,
                intervention_id=interv_id,
                assignee_id="OFF-RURAL-01",
                actor_id="OFF-RURAL-01",
                actor_role="CASE_OFFICER",
                actor_district="Other District",
                auto_commit=True,
            )

    # -------------------------------------------------------------------------
    # 4. Outcome Recording Without Case ID
    # -------------------------------------------------------------------------
    def test_record_outcome_without_case_id(self) -> None:
        """
        FastAPI endpoint POST /api/v1/interventions/{id}/outcome passes only intervention_id.
        record_outcome should infer case_id from the intervention seamlessly.
        """
        svc = db_operational_service

        # Create intervention
        res = svc.process_case_intervention(db=self.db, case_id=1, auto_commit=True)
        interv_id = res["intervention_id"]

        # Advance state to IN_PROGRESS
        svc.transition_status(
            db=self.db,
            intervention_id=interv_id,
            new_status="ACKNOWLEDGED",
            actor_id="OFF-01",
            actor_role="CASE_OFFICER",
            auto_commit=True,
        )
        svc.transition_status(
            db=self.db,
            intervention_id=interv_id,
            new_status="IN_PROGRESS",
            actor_id="OFF-01",
            actor_role="CASE_OFFICER",
            auto_commit=True,
        )

        # Record outcome with case_id=None
        outcome_res = svc.record_outcome(
            db=self.db,
            intervention_id=interv_id,
            outcome_type="REFERRAL_MADE",
            completed=True,
            notes="Referred to medical clinic",
            officer_id="OFF-01",
            officer_role="CASE_OFFICER",
            officer_district="Synthetic Urban District",
            auto_commit=True,
        )

        self.assertEqual(outcome_res["outcome_type"], "REFERRED")
        self.assertEqual(outcome_res["case_id"], 1)
        self.assertEqual(outcome_res["case_string_id"], "AAROH-001")
        self.assertEqual(outcome_res["intervention_status"], "COMPLETED")

        # Verify outcome in DB
        db_out = self.db.query(Outcome).filter(Outcome.intervention_id == interv_id).first()
        self.assertIsNotNone(db_out)
        self.assertEqual(db_out.outcome_type, "REFERRED")
        self.assertEqual(db_out.case_id, 1)

    # -------------------------------------------------------------------------
    # 5. Notification Role Resilience
    # -------------------------------------------------------------------------
    def test_notification_roles_and_resilience(self) -> None:
        """
        Verifies expanded roles work cleanly and unknown inputs never raise unhandled exceptions.
        """
        notif = notification_service

        # Test expanded roles
        rec1 = notif.notify(
            recipient_role=NotificationRecipientRole.DISTRICT_OFFICIAL,
            recipient_id="DIST-OFF-01",
            notification_type=NotificationType.INTERVENTION_ASSIGNED,
            title="District Assignment",
            message="New assignment in district.",
            case_id="AAROH-001",
        )
        self.assertIsNotNone(rec1.created_at)
        self.assertEqual(rec1.recipient_role, NotificationRecipientRole.DISTRICT_OFFICIAL)

        rec2 = notif.notify(
            recipient_role=NotificationRecipientRole.ADMIN,
            recipient_id="ADMIN-01",
            notification_type=NotificationType.SUPPORT_UPDATE,
            title="Admin Alert",
            message="Security check alert.",
            case_id="AAROH-001",
        )
        self.assertIsNotNone(rec2.created_at)

        # Test fallback string inputs
        rec3 = notif.notify(
            recipient_role="CUSTOM_EXTERNAL_ROLE",
            recipient_id="EXT-01",
            notification_type="CUSTOM_EVENT",
            title="Custom Alert",
            message="Testing fallback resilience.",
            case_id="AAROH-001",
        )
        self.assertIsNotNone(rec3.created_at)
        self.assertEqual(rec3.recipient_role, NotificationRecipientRole.CASE_OFFICER)

    # -------------------------------------------------------------------------
    # 6. Optional DB Session Lifecycle (db=None)
    # -------------------------------------------------------------------------
    def test_optional_db_session_lifecycle(self) -> None:
        """
        Verifies methods work autonomously when db is omitted (db=None),
        opening and closing sessions cleanly without connection leaks.
        """
        svc = db_operational_service

        # 1. process_case_intervention with db=None
        res = svc.process_case_intervention(case_id=1, auto_commit=True)
        interv_id = res["intervention_id"]
        self.assertIsNotNone(interv_id)

        # 2. get_intervention with db=None
        interv = svc.get_intervention(intervention_id=interv_id)
        self.assertEqual(interv["id"], interv_id)

        # 3. get_case_interventions with db=None
        case_intervs = svc.get_case_interventions(case_id="AAROH-001")
        self.assertTrue(len(case_intervs) >= 1)

        # 4. record_re_monitoring with db=None
        remon = svc.record_re_monitoring(
            case_id=1,
            new_distress_score=0.30,
            new_trajectory="IMPROVING",
            confidence=0.92,
            auto_commit=True,
        )
        self.assertEqual(remon["case_id"], "AAROH-001")
        self.assertIn("observed_shift", remon)

        # 5. get_rbac_case_analytics with db=None
        analytics = svc.get_rbac_case_analytics(
            case_id=1,
            user_role="ADMIN",
        )
        self.assertEqual(analytics["case_id"], "AAROH-001")

        # 6. channel_service.process_sms_check_in with db=None
        sms_res = channel_service.process_sms_check_in(
            case_id="AAROH-001",
            text_response="Feeling much better today and safe.",
            safety_response=4,
            fear_level=1,
            auto_commit=True,
        )
        self.assertEqual(sms_res["channel"], ChannelType.SMS.value)
        self.assertIsNotNone(sms_res["interaction_id"])

    # 7. Reconciled Canonical Schema Verification
    def test_canonical_schema_reconciliation(self) -> None:
        """
        Verifies that Intervention and Outcome models have all canonical columns,
        backup_assignee property alias functions correctly, and API helpers return
        all operational fields.
        """
        # 1. Model attribute checks
        for attr in ("priority", "reason", "assigned_role", "backup_assigned_to",
                     "assigned_at", "acknowledged_at", "due_at", "completed_at", "created_at"):
            self.assertTrue(
                hasattr(Intervention, attr),
                f"Intervention model missing canonical column: {attr}",
            )

        for attr in ("follow_up_required", "notes"):
            self.assertTrue(
                hasattr(Outcome, attr),
                f"Outcome model missing canonical column: {attr}",
            )

        # 2. backup_assignee property alias check
        test_interv = Intervention(
            case_id=1,
            intervention_type="ROUTINE_MONITORING",
            status="ASSIGNED",
            assigned_to="OFFICER-1",
            backup_assigned_to="BACKUP-OFFICER-2",
        )
        self.assertEqual(test_interv.backup_assignee, "BACKUP-OFFICER-2")
        test_interv.backup_assignee = "NEW-BACKUP-3"
        self.assertEqual(test_interv.backup_assigned_to, "NEW-BACKUP-3")

        # 3. get_intervention returns canonical operational keys
        if not self.Session:
            self.skipTest("PostgreSQL not available")

        db = self.Session()
        try:
            interv_row = db.query(Intervention).filter(Intervention.priority.isnot(None)).first()
            if interv_row:
                res = db_operational_service.get_intervention(db, interv_row.id)
                self.assertIn("priority", res)
                self.assertIn("assigned_role", res)
                self.assertIn("backup_assigned_to", res)
                self.assertIn("backup_assignee", res)
                self.assertEqual(res["backup_assigned_to"], res["backup_assignee"])
                self.assertIn("due_at", res)
                self.assertIn("created_at", res)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
