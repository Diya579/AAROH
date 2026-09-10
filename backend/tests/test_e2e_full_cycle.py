"""
AAROH Phase 4 End-to-End Integration Test
Validates the full cycle from Interaction -> ML Inference -> Intervention -> Notification -> Outcome against a live PostgreSQL database.

# NOTE: This test validates against AssignmentRouter's DEMO_OFFICER_REGISTRY,
# not real PostgreSQL User records. Production wiring of live officer lookup
# into AssignmentRouter is a known open item (see Preet's integration notes).
"""

import os
import unittest
from datetime import datetime, timezone
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import (
    Case,
    Consent,
    Interaction,
    Prediction,
    DistressState,
    Intervention,
    Outcome,
    Notification
)
from backend.schemas.interaction import InteractionCreate
from backend.services.interaction_service import create_interaction
from backend.interventions.db_service import DatabaseOperationalService


class TestEndToEndFullCycle(unittest.TestCase):
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
        
        # Unique string ID to isolate this test's data
        self.unique_id = f"E2E-TEST-{uuid.uuid4().hex[:8].upper()}"

    def tearDown(self) -> None:
        if hasattr(self, 'db') and self.db:
            # Rollback any uncommitted transaction
            self.db.rollback()
            
            # Explicitly delete all created records to avoid DB pollution
            try:
                case = self.db.query(Case).filter(Case.case_id == self.unique_id).first()
                if case:
                    self.db.query(Notification).filter(Notification.case_id == case.case_id).delete()
                    self.db.query(Outcome).filter(Outcome.case_id == case.id).delete()
                    self.db.query(Intervention).filter(Intervention.case_id == case.id).delete()
                    self.db.query(Prediction).filter(Prediction.case_id == case.id).delete()
                    self.db.query(DistressState).filter(DistressState.case_id == case.id).delete()
                    self.db.query(Interaction).filter(Interaction.case_id == case.id).delete()
                    self.db.query(Consent).filter(Consent.case_id == case.id).delete()
                    self.db.delete(case)
                    self.db.commit()
            except Exception:
                self.db.rollback()
                
            self.db.close()

    def test_full_cycle_emergency_override(self):
        """
        Validates Case -> Consent -> Interaction (triggering Emergency) ->
        ML Prediction -> Intervention -> Notification -> Outcome (Closed Loop).
        """
        # 1. Create Case & Consent
        case = Case(
            case_id=self.unique_id,
            language="English",
            district_type="Urban",
            district="Synthetic Urban District", # Matches DEMO_OFFICER_REGISTRY
            priority_use_case="Domestic Violence",
            current_stage="MONITORING"
        )
        self.db.add(case)
        self.db.flush()
        
        consent = Consent(
            case_id=case.id,
            monitoring_consent=True,
            text_analysis_consent=True,
            voice_analysis_consent=True,
            case_linkage_consent=True
        )
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(case)
        
        # 2. Create Interaction (The Trigger)
        # Using crisis language triggers the EMERGENCY risk level via deterministic override
        payload = InteractionCreate(
            case_id=case.id,
            interaction_date=datetime.now(timezone.utc),
            channel="SMS",
            language="English",
            text_response="This is an emergency, please call police, he is trying to end my life.",
            sleep_disruption=None,
            fear_level=None,
            social_support=None,
            response_completed=True,
            voice_available=False,
            help_requested=True
        )
        
        # This orchestrates ML pipeline + DB Intervention Engine
        interaction_row = create_interaction(self.db, payload)
        
        self.assertIsNotNone(interaction_row.id)
        self.assertEqual(interaction_row.case_id, case.id)
        
        # 3. Assert ML Inference (Prediction & DistressState)
        prediction = self.db.query(Prediction).filter(Prediction.case_id == case.id).first()
        self.assertIsNotNone(prediction, "Prediction was not persisted.")
        self.assertEqual(prediction.risk_level, "EMERGENCY", "Safety override did not trigger EMERGENCY risk level.")
        self.assertIsNotNone(prediction.escalation_probability)
        
        distress = self.db.query(DistressState).filter(DistressState.case_id == case.id).first()
        self.assertIsNotNone(distress, "DistressState was not persisted.")
        
        # 4. Assert Intervention & Routing
        intervention = self.db.query(Intervention).filter(Intervention.case_id == case.id).first()
        self.assertIsNotNone(intervention, "Intervention was not persisted.")
        self.assertEqual(intervention.priority, "URGENT", "Intervention priority should be URGENT for EMERGENCY risk.")
        self.assertEqual(intervention.status, "ASSIGNED", "Intervention should be successfully routed and ASSIGNED.")
        self.assertEqual(intervention.assigned_to, "SYNTH-URBAN-DSGNT", "Assigned officer mismatch.")
        self.assertIsNotNone(intervention.due_at, "SLA deadline (due_at) not populated.")
        
        # 5. Assert Notification Dispatch
        # The routing engine sets assigned_to to 'SYNTH-URBAN-DSGNT'
        notification = self.db.query(Notification).filter(
            Notification.recipient_user_id == intervention.assigned_to,
            Notification.intervention_id == intervention.id
        ).first()
        self.assertIsNotNone(notification, "Notification to assigned officer was not dispatched.")
        self.assertFalse(notification.is_read, "Notification should be unread.")
        
        # 6. Acknowledge & Record Outcome
        db_ops = DatabaseOperationalService()
        
        # Transition to ACKNOWLEDGED
        db_ops.transition_status(
            db=self.db,
            intervention_id=intervention.id,
            new_status="ACKNOWLEDGED",
            actor_id="SYNTH-URBAN-DSGNT",
            actor_role="DESIGNATED_OFFICER",
            actor_district="Synthetic Urban District"
        )
        
        # Transition to IN_PROGRESS
        db_ops.transition_status(
            db=self.db,
            intervention_id=intervention.id,
            new_status="IN_PROGRESS",
            actor_id="SYNTH-URBAN-DSGNT",
            actor_role="DESIGNATED_OFFICER",
            actor_district="Synthetic Urban District"
        )
        
        # Record Outcome
        outcome_result = db_ops.record_outcome(
            db=self.db,
            intervention_id=intervention.id,
            outcome_type="REFERRED",
            completed=True,
            follow_up_required=True,
            notes="Escalated based on severe crisis language.",
            officer_id="SYNTH-URBAN-DSGNT",
            officer_role="DESIGNATED_OFFICER",
            officer_district="Synthetic Urban District"
        )
        
        # Assert Outcome response dict and ClosedLoopObservation
        self.assertTrue(outcome_result["follow_up_required"])
        self.assertIn("closed_loop_observation", outcome_result)
        
        cl_obs = outcome_result["closed_loop_observation"]
        self.assertEqual(cl_obs["case_id"], case.case_id)
        self.assertEqual(cl_obs["intervention_id"], intervention.id)
        self.assertEqual(cl_obs["outcome_type"], "REFERRED")
        
        # Verify Outcome DB row persistence
        outcome_row = self.db.query(Outcome).filter(Outcome.id == outcome_result["outcome_id"]).first()
        self.assertIsNotNone(outcome_row)
        self.assertTrue(outcome_row.follow_up_required)
        self.assertEqual(outcome_row.outcome_type, "REFERRED")
        
        # Assert record_outcome() internally transitioned the intervention to COMPLETED.
        # This is by design: record_outcome() calls OutcomeManager.transition_status()
        # unconditionally (lines 619-622 of db_service.py), making an explicit
        # transition_status("COMPLETED") call before record_outcome() unnecessary.
        self.db.refresh(intervention)
        self.assertEqual(
            intervention.status,
            "COMPLETED",
            "record_outcome() must internally transition the intervention to COMPLETED."
        )
        self.assertIsNotNone(
            intervention.completed_at,
            "record_outcome() must set completed_at on the intervention row."
        )

if __name__ == "__main__":
    unittest.main()
