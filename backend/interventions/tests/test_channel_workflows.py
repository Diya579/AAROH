"""
AAROH — Multi-Channel (IVR, SMS, Chatbot) Workflows Test Suite
Author: Preet (Senior Backend Engineer — Intervention, Routing, SLA, Outcomes & Analytics Owner)

Tests all channel intake workflows and event edge cases:
- IVR check-in with consent gating and intervention trigger.
- SMS check-in with text analysis consent.
- Chatbot session with authorized case verification.
- Edge case: Missed check-in triggers caseworker review.
- Edge case: Incomplete interaction triggers INSUFFICIENT_DATA human review.
- Edge case: Duplicate interaction idempotency within window.
- Edge case: Late response detection and logging.
- Edge case: Unsafe channel detection / panic triggers emergency protocol.
- Edge case: Consent revocation blocks automated intervention.
"""

import os
import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import SessionLocal
from backend.models import (
    Case,
    Consent,
    Interaction,
    CaseEvent,
    DistressState,
    Prediction,
    Intervention,
    Outcome,
)
from backend.interventions.engine import (
    InterventionType,
    PriorityLevel,
    InterventionStatus,
)
from backend.interventions.routing import (
    AssignmentRouter,
    AssigneeRole,
    SyntheticOfficer,
)
from backend.interventions.channels import (
    ChannelType,
    ChannelEventType,
    channel_service,
)


class TestChannelWorkflows(unittest.TestCase):
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
        if self.Session:
            self.db = self.Session()
        else:
            self.db = SessionLocal()

        self.case = self.db.query(Case).filter(Case.id == 1).first()
        if not self.case:
            self.db.close()
            self.skipTest("Case 1 not found in database. Live DB required for channel integration tests.")

        self.router = AssignmentRouter([
            SyntheticOfficer("OFF-URBAN-1", "Urban Primary", AssigneeRole.DESIGNATED_OFFICER, self.case.district, active_caseload=0),
            SyntheticOfficer("OFF-URBAN-2", "Urban Backup", AssigneeRole.COUNSELLOR, self.case.district, active_caseload=1),
        ])
        self.consent = self.db.query(Consent).filter(Consent.case_id == 1).first()
        self.orig_safe_channel = self.consent.safe_channel if self.consent else "sms"
        self.orig_monitoring = self.consent.monitoring_consent if self.consent else True
        self.orig_voice = self.consent.voice_analysis_consent if self.consent else True
        self._clean_test_records()

    def tearDown(self) -> None:
        self._clean_test_records()
        consent = self.db.query(Consent).filter(Consent.case_id == 1).first()
        if consent:
            consent.safe_channel = self.orig_safe_channel
            consent.monitoring_consent = self.orig_monitoring
            consent.voice_analysis_consent = self.orig_voice
            self.db.commit()
        self.db.close()

    def _clean_test_records(self) -> None:
        try:
            self.db.query(Outcome).filter(Outcome.case_id == 1).delete()
            self.db.query(Intervention).filter(Intervention.case_id == 1).delete()
            self.db.query(CaseEvent).filter(CaseEvent.case_id == 1, CaseEvent.event_type.in_([
                ChannelEventType.CHECK_IN_RECEIVED.value,
                ChannelEventType.CHECK_IN_MISSED.value,
                ChannelEventType.INTERACTION_INCOMPLETE.value,
                ChannelEventType.DUPLICATE_EVENT.value,
                ChannelEventType.LATE_RESPONSE.value,
                ChannelEventType.UNSAFE_CHANNEL_DETECTED.value,
                "MONITORING_CONSENT_REVOKED",
                "VOICE_CONSENT_DENIED",
            ])).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()

    # -------------------------------------------------------------------------
    # 1. IVR CHANNEL WORKFLOW
    # -------------------------------------------------------------------------
    def test_01_ivr_check_in_flow(self) -> None:
        """IVR check-in logs Interaction, CaseEvent, derives Prediction, and creates Intervention."""
        consent = self.db.query(Consent).filter(Consent.case_id == 1).first()
        if consent:
            consent.safe_channel = "IVR"
            consent.monitoring_consent = True
            consent.voice_analysis_consent = True
            self.db.commit()

        res = channel_service.process_ivr_check_in(
            db=self.db,
            case_id=1,
            safety_response=4,
            fear_level=2,
            sleep_disruption=2,
            help_requested=False,
            audio_transcript="Everything is peaceful at home today.",
            voice_available=True,
            custom_router=self.router,
            auto_commit=True,
        )

        self.assertEqual(res["channel"], ChannelType.IVR.value)
        self.assertIsNotNone(res["interaction_id"])
        self.assertIsNotNone(res["intervention"])

        # Verify Interaction in DB
        interaction = self.db.query(Interaction).filter(Interaction.id == res["interaction_id"]).first()
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.channel, "IVR")
        self.assertTrue(interaction.voice_available)
        self.assertTrue(interaction.response_completed)

        # Verify CaseEvent in DB
        event = (
            self.db.query(CaseEvent)
            .filter(CaseEvent.case_id == 1, CaseEvent.event_type == ChannelEventType.CHECK_IN_RECEIVED.value)
            .first()
        )
        self.assertIsNotNone(event)

    # -------------------------------------------------------------------------
    # 2. IVR VOICE CONSENT GATING
    # -------------------------------------------------------------------------
    def test_02_ivr_voice_consent_denied_discards_audio(self) -> None:
        """When voice_analysis_consent is False, voice_available is set to False and event is logged."""
        consent = self.db.query(Consent).filter(Consent.case_id == 1).first()
        if not consent:
            consent = Consent(case_id=1, monitoring_consent=True, voice_analysis_consent=False, safe_channel="IVR")
            self.db.add(consent)
        else:
            consent.safe_channel = "IVR"
            consent.monitoring_consent = True
            consent.voice_analysis_consent = False
        self.db.commit()

        res = channel_service.process_ivr_check_in(
            db=self.db,
            case_id=1,
            safety_response=5,
            fear_level=1,
            audio_transcript="Checking in via keypad.",
            voice_available=True,
            custom_router=self.router,
            auto_commit=True,
        )

        interaction = self.db.query(Interaction).filter(Interaction.id == res["interaction_id"]).first()
        self.assertFalse(interaction.voice_available)

        # Reset consent
        consent.voice_analysis_consent = True
        self.db.commit()

    # -------------------------------------------------------------------------
    # 3. SMS CHANNEL WORKFLOW
    # -------------------------------------------------------------------------
    def test_03_sms_check_in_flow(self) -> None:
        """SMS response logs interaction, case event, and routes through intervention engine."""
        res = channel_service.process_sms_check_in(
            db=self.db,
            case_id=1,
            text_response="Feeling much better, attending work regularly.",
            safety_response=5,
            fear_level=1,
            help_requested=False,
            custom_router=self.router,
            auto_commit=True,
        )

        self.assertEqual(res["channel"], ChannelType.SMS.value)
        interaction = self.db.query(Interaction).filter(Interaction.id == res["interaction_id"]).first()
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.channel, "SMS")
        self.assertFalse(interaction.voice_available)
        self.assertIn("attending work", interaction.text_response)

    # -------------------------------------------------------------------------
    # 4. CHATBOT CHANNEL WORKFLOW
    # -------------------------------------------------------------------------
    def test_04_chatbot_interaction_flow(self) -> None:
        """Chatbot session verifies case authorization, logs interaction, and triggers intervention."""
        res = channel_service.process_chatbot_interaction(
            db=self.db,
            case_id=1,
            message_text="Can I schedule my counselling appointment for Thursday?",
            safety_response=4,
            fear_level=2,
            help_requested=False,
            custom_router=self.router,
            auto_commit=True,
        )

        self.assertEqual(res["channel"], ChannelType.CHATBOT.value)
        interaction = self.db.query(Interaction).filter(Interaction.id == res["interaction_id"]).first()
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.channel, "CHATBOT")
        self.assertIn("counselling appointment", interaction.text_response)

    # -------------------------------------------------------------------------
    # 5. MISSED CHECK-IN (Fails Closed -> Human Review)
    # -------------------------------------------------------------------------
    def test_05_missed_check_in_triggers_insufficient_data_human_review(self) -> None:
        """Missed check-in creates CHECK_IN_MISSED event and routes to PRIORITY_HUMAN_REVIEW (HIGH)."""
        res = channel_service.handle_missed_check_in(
            db=self.db,
            case_id=1,
            scheduled_time=datetime.now(timezone.utc) - timedelta(hours=3),
            custom_router=self.router,
            auto_commit=True,
        )

        self.assertEqual(res["event_type"], ChannelEventType.CHECK_IN_MISSED.value)
        interv = res["intervention"]
        self.assertEqual(interv["intervention_type"], InterventionType.PRIORITY_HUMAN_REVIEW.value)
        self.assertEqual(interv["priority"], PriorityLevel.HIGH.value)

        # Verify event logged
        event = (
            self.db.query(CaseEvent)
            .filter(CaseEvent.case_id == 1, CaseEvent.event_type == ChannelEventType.CHECK_IN_MISSED.value)
            .first()
        )
        self.assertIsNotNone(event)

    # -------------------------------------------------------------------------
    # 6. INCOMPLETE INTERACTION (Call dropped -> Human Review)
    # -------------------------------------------------------------------------
    def test_06_incomplete_interaction_triggers_human_review(self) -> None:
        """Dropped/aborted call logs INTERACTION_INCOMPLETE and safely routes to PRIORITY_HUMAN_REVIEW."""
        res = channel_service.handle_incomplete_interaction(
            db=self.db,
            case_id=1,
            channel="IVR",
            reason="Beneficiary hung up after 15 seconds",
            custom_router=self.router,
            auto_commit=True,
        )

        self.assertEqual(res["event_type"], ChannelEventType.INTERACTION_INCOMPLETE.value)
        interaction = self.db.query(Interaction).filter(Interaction.id == res["interaction_id"]).first()
        self.assertFalse(interaction.response_completed)
        self.assertEqual(interaction.data_quality, "incomplete")

        # Must route to PRIORITY_HUMAN_REVIEW due to INSUFFICIENT_DATA
        self.assertEqual(res["intervention"]["intervention_type"], InterventionType.PRIORITY_HUMAN_REVIEW.value)

    # -------------------------------------------------------------------------
    # 7. DUPLICATE EVENT SUPPRESSION
    # -------------------------------------------------------------------------
    def test_07_duplicate_event_suppression_within_window(self) -> None:
        """Second identical check-in within window is marked as duplicate and suppressed."""
        res1 = channel_service.process_sms_check_in(
            db=self.db,
            case_id=1,
            text_response="Routine status OK",
            custom_router=self.router,
            auto_commit=True,
        )
        self.assertFalse(res1.get("is_duplicate", False))

        # Repeated SMS check-in immediately
        res2 = channel_service.process_sms_check_in(
            db=self.db,
            case_id=1,
            text_response="Routine status OK",
            custom_router=self.router,
            auto_commit=True,
        )
        self.assertTrue(res2.get("is_duplicate", False))
        self.assertEqual(res2["status"], "DUPLICATE_IGNORED")

    # -------------------------------------------------------------------------
    # 8. LATE RESPONSE LOGGING
    # -------------------------------------------------------------------------
    def test_08_late_response_logs_event_and_evaluates(self) -> None:
        """Late response logs LATE_RESPONSE event with delay offset then completes evaluation."""
        res = channel_service.handle_late_response(
            db=self.db,
            case_id=1,
            channel="SMS",
            delay_hours=4.5,
            text_response="Apologies for late reply, I am safe.",
            custom_router=self.router,
            auto_commit=True,
        )

        event = (
            self.db.query(CaseEvent)
            .filter(CaseEvent.case_id == 1, CaseEvent.event_type == ChannelEventType.LATE_RESPONSE.value)
            .first()
        )
        self.assertIsNotNone(event)
        self.assertIn("4.5 hours", event.description)

    # -------------------------------------------------------------------------
    # 9. UNSAFE CHANNEL & PANIC DETECTION
    # -------------------------------------------------------------------------
    def test_09_unsafe_channel_panic_triggers_emergency_escalation(self) -> None:
        """Panic distress keyword immediately activates UNSAFE_CHANNEL_DETECTED and EMERGENCY_ESCALATION."""
        res = channel_service.process_sms_check_in(
            db=self.db,
            case_id=1,
            text_response="Please danger threat outside my house emergency",
            help_requested=True,
            custom_router=self.router,
            auto_commit=True,
        )

        self.assertEqual(res["event_type"], ChannelEventType.UNSAFE_CHANNEL_DETECTED.value)
        interv = res["intervention"]
        # Panic triggers EMERGENCY_ESCALATION with URGENT priority
        self.assertEqual(interv["priority"], PriorityLevel.URGENT.value)
        self.assertEqual(interv["sla_hours"], 4.0)

    # -------------------------------------------------------------------------
    # 10. MONITORING CONSENT REVOCATION
    # -------------------------------------------------------------------------
    def test_10_consent_revocation_blocks_automated_intervention(self) -> None:
        """When monitoring_consent is False, check-in produces NO_AUTOMATED_INTERVENTION."""
        consent = self.db.query(Consent).filter(Consent.case_id == 1).first()
        if not consent:
            consent = Consent(case_id=1, monitoring_consent=False)
            self.db.add(consent)
        else:
            consent.monitoring_consent = False
        self.db.commit()

        res = channel_service.process_chatbot_interaction(
            db=self.db,
            case_id=1,
            message_text="Hello, I want to withdraw consent.",
            custom_router=self.router,
            auto_commit=True,
        )

        interv = res
        self.assertEqual(interv["intervention_type"], InterventionType.NO_AUTOMATED_INTERVENTION.value)
        self.assertEqual(interv["priority"], PriorityLevel.NONE.value)

        # Restore consent
        consent.monitoring_consent = True
        self.db.commit()

    # -------------------------------------------------------------------------
    # 11. UNSAFE CHANNEL RESTRICTION MISMATCH
    # -------------------------------------------------------------------------
    def test_11_unsafe_channel_restriction_mismatch_triggers_emergency_escalation(self) -> None:
        """When beneficiary safe_channel is SMS and IVR is attempted, triggers UNSAFE_CHANNEL_DETECTED."""
        consent = self.db.query(Consent).filter(Consent.case_id == 1).first()
        if consent:
            consent.safe_channel = "SMS"
            consent.monitoring_consent = True
            self.db.commit()

        res = channel_service.process_ivr_check_in(
            db=self.db,
            case_id=1,
            safety_response=5,
            fear_level=1,
            audio_transcript="Checking in via IVR.",
            custom_router=self.router,
            auto_commit=True,
        )

        self.assertEqual(res["event_type"], ChannelEventType.UNSAFE_CHANNEL_DETECTED.value)
        self.assertEqual(res["attempted_channel"], "IVR")
        self.assertIn("restricted to 'SMS'", res["reason"])
        self.assertEqual(res["intervention"]["priority"], PriorityLevel.URGENT.value)


if __name__ == "__main__":
    unittest.main()

