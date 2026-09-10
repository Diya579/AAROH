"""
AAROH — Notification Persistence and Trigger Verification Tests
Author: Preet

Verifies end-to-end:
1. Real PostgreSQL persistence into notifications table.
2. HIGH_RISK_CASE trigger on HIGH/URGENT interventions.
3. INTERVENTION_ASSIGNED and SUPPORT_UPDATE (victim) persistence.
4. FOLLOW_UP_REQUIRED trigger on outcome recording with follow_up_required=True.
5. INTERVENTION_OVERDUE trigger via check_and_notify_overdue_interventions.
6. list_notifications() API retrieval for assigned officer and victim.
7. Victim privacy sanitization in persisted notification records.
"""

import os
import unittest
from datetime import datetime, timezone, timedelta

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
    Notification,
)
from backend.interventions import (
    db_operational_service,
    notification_service,
    NotificationType,
    NotificationRecipientRole,
    PriorityLevel,
    InterventionStatus,
)
from backend.services.notification_service import list_notifications


class TestNotificationPersistenceAndTriggers(unittest.TestCase):
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
            Notification.__table__.create(bind=cls.engine, checkfirst=True)
        except Exception:
            cls.Session = None

    def setUp(self):
        if not self.Session:
            self.skipTest("PostgreSQL aaroh_db unavailable for live persistence test")
        self.db = self.Session()

    def tearDown(self):
        if self.db:
            self.db.rollback()
            self.db.close()

    def test_01_high_risk_intervention_persists_notifications_for_officer_and_victim(self):
        """
        Triggering a HIGH-risk intervention must:
        - Persist INTERVENTION_ASSIGNED for officer.
        - Persist HIGH_RISK_CASE for supervisor/officer.
        - Persist SUPPORT_UPDATE for victim using case_id without leaks.
        """
        case = self.db.query(Case).filter(Case.case_id == "AAROH-002").first()
        if not case:
            self.skipTest("Case AAROH-002 not found in PostgreSQL")

        # Clear existing notifications, outcomes, and interventions for AAROH-002 to test fresh creation
        self.db.query(Notification).filter(Notification.case_id == case.id).delete()
        self.db.query(Outcome).filter(Outcome.case_id == case.id).delete()
        self.db.query(Intervention).filter(Intervention.case_id == case.id).delete()
        self.db.commit()

        # Case AAROH-002 is HIGH/URGENT escalation (0.78 probability)
        res = db_operational_service.process_case_intervention(
            db=self.db,
            case_id="AAROH-002",
            auto_commit=True,
        )
        self.assertIn(res["priority"], ("HIGH", "URGENT"))
        assigned_to = res["assigned_to"]
        self.assertIsNotNone(assigned_to)

        # 1. Verify officer received notifications in PostgreSQL
        officer_notifs = list_notifications(self.db, recipient_user_id=assigned_to)
        self.assertTrue(len(officer_notifs) > 0)
        types = [n.notification_type for n in officer_notifs]
        self.assertIn(NotificationType.INTERVENTION_ASSIGNED.value, types)

        # 2. Verify HIGH_RISK_CASE notification was persisted
        high_risk_notifs = (
            self.db.query(Notification)
            .filter(
                Notification.notification_type == NotificationType.HIGH_RISK_CASE.value,
                Notification.intervention_id == res["id"],
            )
            .all()
        )
        self.assertTrue(len(high_risk_notifs) > 0)

        # 3. Verify victim received citizen-safe notification in PostgreSQL
        victim_notifs = list_notifications(self.db, recipient_user_id="AAROH-002")
        self.assertTrue(len(victim_notifs) > 0)
        v_types = [n.notification_type for n in victim_notifs]
        self.assertIn(NotificationType.SUPPORT_UPDATE.value, v_types)

        # Check victim message privacy: no internal diagnostic leak
        latest_victim_notif = victim_notifs[0]
        self.assertNotIn("probability", latest_victim_notif.message.lower())
        self.assertNotIn("distress score", latest_victim_notif.message.lower())
        self.assertNotIn("sla breach", latest_victim_notif.message.lower())

    def test_02_follow_up_required_persists_notification(self):
        """
        Recording an outcome with follow_up_required=True must persist
        a FOLLOW_UP_REQUIRED notification to the assigned officer.
        """
        interv = (
            self.db.query(Intervention)
            .filter(Intervention.status.in_(["ASSIGNED", "IN_PROGRESS", "PENDING"]))
            .first()
        )
        if not interv:
            res = db_operational_service.process_case_intervention(
                db=self.db,
                case_id=1,
                auto_commit=True,
            )
            interv = self.db.query(Intervention).filter(Intervention.id == res["intervention_id"]).first()

        interv.status = "IN_PROGRESS"
        self.db.commit()

        officer = interv.assigned_to
        outcome_res = db_operational_service.record_outcome(
            db=self.db,
            intervention_id=interv.id,
            outcome_type="REFERRED",
            actor_id="OFF-TEST-1",
            actor_role="CASE_OFFICER",
            actor_district="Synthetic Urban District",
            follow_up_required=True,
            notes="Follow-up counseling session needed next week.",
            auto_commit=True,
        )

        # Verify FOLLOW_UP_REQUIRED in DB
        follow_up_notifs = (
            self.db.query(Notification)
            .filter(
                Notification.notification_type == NotificationType.FOLLOW_UP_REQUIRED.value,
                Notification.intervention_id == interv.id,
            )
            .all()
        )
        self.assertTrue(len(follow_up_notifs) > 0)
        self.assertEqual(follow_up_notifs[0].outcome_id, outcome_res["id"])

    def test_03_check_and_notify_overdue_interventions(self):
        """
        check_and_notify_overdue_interventions must detect expired due_at,
        log SLA_BREACHED event, and persist INTERVENTION_OVERDUE notifications.
        """
        # Create a mock overdue intervention in DB
        case = self.db.query(Case).first()
        past_due = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=5)
        overdue_interv = Intervention(
            case_id=case.id,
            intervention_type="ROUTINE_MONITORING",
            status="ASSIGNED",
            assigned_to="OVERDUE-OFFICER-99",
            priority="HIGH",
            due_at=past_due,
        )
        self.db.add(overdue_interv)
        self.db.commit()
        self.db.refresh(overdue_interv)

        overdue_results = db_operational_service.check_and_notify_overdue_interventions(
            db=self.db,
            auto_commit=True,
        )
        self.assertTrue(any(o["intervention_id"] == overdue_interv.id for o in overdue_results))

        # Verify INTERVENTION_OVERDUE notification exists in PostgreSQL
        overdue_notifs = (
            self.db.query(Notification)
            .filter(
                Notification.notification_type == NotificationType.INTERVENTION_OVERDUE.value,
                Notification.intervention_id == overdue_interv.id,
            )
            .all()
        )
        self.assertTrue(len(overdue_notifs) > 0)


if __name__ == "__main__":
    unittest.main()
