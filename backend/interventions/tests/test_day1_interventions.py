"""
AAROH Day 1 Comprehensive Test Suite
Author: Preet

Verifies:
- Risk-to-intervention decision mapping
- Consent verification & blocking
- Low-confidence & abstention handling
- Priority ranking & queue ordering
- Role-based and district routing
- SLA computation, due-soon, and overdue detection
- Valid status transitions and terminal invalid transition rejection
- Outcome recording & closed-loop feedback
- Multi-tier analytics (Case, District, State, National)
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

from backend.interventions.engine import (
    InterventionEngine,
    InterventionType,
    InterventionStatus,
    PriorityLevel,
    InterventionCategory,
)
from backend.interventions.prioritization import (
    calculate_priority,
    compute_case_urgency_score,
    rank_cases_by_priority,
)
from backend.interventions.routing import (
    AssignmentRouter,
    AssigneeRole,
    SyntheticOfficer,
)
from backend.interventions.sla import (
    SLAManager,
    SLAStatus,
    SLARecord,
)
from backend.interventions.outcomes import (
    OutcomeManager,
    OutcomeType,
    ClosedLoopObservation,
)
from backend.analytics.case_metrics import CaseMetricsCalculator
from backend.analytics.district_metrics import DistrictMetricsCalculator
from backend.analytics.state_metrics import StateMetricsCalculator
from backend.analytics.national_metrics import NationalMetricsCalculator


class TestInterventionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = InterventionEngine()

    def test_high_risk_triggers_urgent_priority_human_review(self):
        decision = self.engine.evaluate(
            case_id="AAROH-001",
            risk_level="HIGH",
            escalation_probability=0.85,
            trajectory="RAPIDLY_WORSENING",
            confidence=0.90,
            factors=["Severe intimidation reported", "High fear signals"],
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.PRIORITY_HUMAN_REVIEW)
        self.assertEqual(decision.priority, PriorityLevel.URGENT)
        self.assertIn(InterventionCategory.WITNESS_PROTECTION_SUPPORT, decision.suggested_categories)
        self.assertFalse(decision.is_duplicate)

    def test_moderate_risk_triggers_human_follow_up(self):
        decision = self.engine.evaluate(
            case_id="AAROH-002",
            risk_level="MODERATE",
            escalation_probability=0.55,
            trajectory="WORSENING",
            confidence=0.85,
            factors=["Sleep disruption"],
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.HUMAN_FOLLOW_UP)
        self.assertEqual(decision.priority, PriorityLevel.HIGH)

    def test_improving_trajectory_triggers_continue_monitoring(self):
        decision = self.engine.evaluate(
            case_id="AAROH-003",
            risk_level="LOW",
            escalation_probability=0.20,
            trajectory="IMPROVING",
            confidence=0.88,
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.CONTINUE_MONITORING)
        self.assertEqual(decision.priority, PriorityLevel.LOW)

    def test_stable_low_concern_triggers_routine_monitoring(self):
        decision = self.engine.evaluate(
            case_id="AAROH-004",
            risk_level="LOW",
            escalation_probability=0.15,
            trajectory="STABLE",
            confidence=0.92,
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.ROUTINE_MONITORING)
        self.assertEqual(decision.priority, PriorityLevel.ROUTINE)

    def test_missing_consent_blocks_automated_interventions(self):
        decision = self.engine.evaluate(
            case_id="AAROH-005",
            risk_level="HIGH",
            escalation_probability=0.95,
            trajectory="RAPIDLY_WORSENING",
            confidence=0.99,
            monitoring_consent=False,
        )
        self.assertEqual(decision.intervention_type, InterventionType.NO_AUTOMATED_INTERVENTION)
        self.assertEqual(decision.priority, PriorityLevel.NONE)
        self.assertIn("Monitoring consent is absent", decision.reason.abstention_reason)

    def test_low_confidence_abstention_triggers_human_review(self):
        decision = self.engine.evaluate(
            case_id="AAROH-006",
            risk_level="LOW",
            escalation_probability=0.10,
            trajectory="STABLE",
            confidence=0.30,  # Below threshold
            ml_status="LOW_CONFIDENCE",
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.PRIORITY_HUMAN_REVIEW)
        self.assertEqual(decision.priority, PriorityLevel.HIGH)
        self.assertIsNotNone(decision.reason.abstention_reason)

    def test_duplicate_pending_intervention_is_prevented(self):
        active = [
            {"id": 42, "status": "PENDING", "intervention_type": "PRIORITY_HUMAN_REVIEW"}
        ]
        decision = self.engine.evaluate(
            case_id="AAROH-001",
            risk_level="HIGH",
            escalation_probability=0.88,
            trajectory="RAPIDLY_WORSENING",
            monitoring_consent=True,
            active_interventions=active,
        )
        self.assertTrue(decision.is_duplicate)
        self.assertEqual(decision.existing_intervention_id, 42)


class TestPrioritization(unittest.TestCase):
    def test_priority_ranking_order(self):
        case_critical = {
            "case_id": "CRITICAL",
            "risk_level": "HIGH",
            "escalation_probability": 0.89,
            "trajectory": "RAPIDLY_WORSENING",
            "is_overdue": True,
        }
        case_routine = {
            "case_id": "ROUTINE",
            "risk_level": "LOW",
            "escalation_probability": 0.12,
            "trajectory": "STABLE",
            "is_overdue": False,
        }
        ranked = rank_cases_by_priority([case_routine, case_critical])
        self.assertEqual(ranked[0]["case_id"], "CRITICAL")
        self.assertEqual(ranked[1]["case_id"], "ROUTINE")


class TestRouting(unittest.TestCase):
    def test_routing_allocates_designated_officer_for_urgent(self):
        router = AssignmentRouter()
        result = router.route(
            case_id="CASE-01",
            district="Patna",
            intervention_type=InterventionType.PRIORITY_HUMAN_REVIEW,
            priority=PriorityLevel.URGENT,
        )
        self.assertEqual(result.assigned_role, AssigneeRole.DESIGNATED_OFFICER)
        self.assertIn("SYNTH-DSGNT", result.primary_assignee)

    def test_routing_allocates_counsellor_for_moderate(self):
        router = AssignmentRouter()
        result = router.route(
            case_id="CASE-02",
            district="Ahmedabad",
            intervention_type=InterventionType.HUMAN_FOLLOW_UP,
            priority=PriorityLevel.HIGH,
        )
        self.assertEqual(result.assigned_role, AssigneeRole.COUNSELLOR)
        self.assertEqual(result.primary_assignee, "SYNTH-COUNS-03")


class TestSLA(unittest.TestCase):
    def setUp(self):
        self.manager = SLAManager()

    def test_sla_due_time_calculation(self):
        base_time = datetime(2026, 9, 5, 10, 0, 0)
        due_urgent = self.manager.compute_due_time(PriorityLevel.URGENT, base_time)
        self.assertEqual(due_urgent, base_time + timedelta(hours=4))

        due_high = self.manager.compute_due_time(PriorityLevel.HIGH, base_time)
        self.assertEqual(due_high, base_time + timedelta(hours=24))

    def test_overdue_detection(self):
        created = datetime(2026, 9, 5, 10, 0, 0)
        due = created + timedelta(hours=4)
        record = SLARecord(1, PriorityLevel.URGENT, created, due)

        # Before deadline
        self.assertEqual(record.evaluate_status(created + timedelta(hours=1)), SLAStatus.PENDING)
        # Due soon (85% elapsed)
        self.assertEqual(record.evaluate_status(created + timedelta(hours=3, minutes=30)), SLAStatus.DUE_SOON)
        # Overdue (past 4h)
        self.assertEqual(record.evaluate_status(created + timedelta(hours=5)), SLAStatus.OVERDUE)


class TestOutcomesAndTransitions(unittest.TestCase):
    def test_valid_transitions(self):
        status = InterventionStatus.PENDING
        status = OutcomeManager.transition_status(status, InterventionStatus.ASSIGNED)
        self.assertEqual(status, InterventionStatus.ASSIGNED)

        status = OutcomeManager.transition_status(status, InterventionStatus.ACKNOWLEDGED)
        self.assertEqual(status, InterventionStatus.ACKNOWLEDGED)

        status = OutcomeManager.transition_status(status, InterventionStatus.IN_PROGRESS)
        self.assertEqual(status, InterventionStatus.IN_PROGRESS)

        status = OutcomeManager.transition_status(status, InterventionStatus.COMPLETED)
        self.assertEqual(status, InterventionStatus.COMPLETED)

    def test_invalid_completed_to_pending_raises_error(self):
        with self.assertRaises(ValueError):
            OutcomeManager.transition_status(InterventionStatus.COMPLETED, InterventionStatus.PENDING)

    def test_closed_loop_observation(self):
        obs = ClosedLoopObservation(
            case_id="AAROH-001",
            intervention_id=10,
            outcome_type=OutcomeType.COUNSELLING_PROVIDED,
            pre_distress_score=0.75,
            pre_trajectory="WORSENING",
        )
        shift = obs.evaluate_shift(post_score=0.45, post_trajectory="IMPROVING")
        self.assertEqual(shift, "SUBSEQUENT_IMPROVEMENT")
        self.assertEqual(obs.observed_shift, "SUBSEQUENT_IMPROVEMENT")


class TestAnalytics(unittest.TestCase):
    def test_district_aggregation(self):
        cases = [
            {"case_id": "C1", "risk_level": "HIGH", "trajectory": "RAPIDLY_WORSENING"},
            {"case_id": "C2", "risk_level": "MODERATE", "trajectory": "WORSENING"},
            {"case_id": "C3", "risk_level": "LOW", "trajectory": "STABLE"},
        ]
        interventions = [
            {"id": 1, "status": "PENDING", "is_overdue": False, "response_time_hours": 1.5},
            {"id": 2, "status": "COMPLETED", "is_overdue": False, "response_time_hours": 2.0},
        ]
        outcomes = [
            {"outcome_type": "COUNSELLING_PROVIDED"},
        ]

        district_metrics = DistrictMetricsCalculator.calculate(
            district="Patna",
            case_records=cases,
            intervention_records=interventions,
            outcome_records=outcomes,
        )

        self.assertEqual(district_metrics.total_monitored_cases, 3)
        self.assertEqual(district_metrics.high_risk_cases, 1)
        self.assertEqual(district_metrics.pending_interventions, 1)
        self.assertEqual(district_metrics.completed_interventions, 1)
        self.assertEqual(district_metrics.avg_response_time_hours, 1.75)

    def test_state_and_national_rollup(self):
        d1 = DistrictMetricsCalculator.calculate("Patna", [{"risk_level": "HIGH"}], [], [])
        d2 = DistrictMetricsCalculator.calculate("Gaya", [{"risk_level": "LOW"}], [], [])

        state_metrics = StateMetricsCalculator.calculate("Bihar", [d1, d2])
        self.assertEqual(state_metrics.total_districts, 2)
        self.assertEqual(state_metrics.total_monitored_cases, 2)
        self.assertEqual(state_metrics.total_high_risk, 1)

        nat_metrics = NationalMetricsCalculator.calculate([state_metrics])
        self.assertEqual(nat_metrics.total_states, 1)
        self.assertEqual(nat_metrics.total_monitored_cases, 2)


if __name__ == "__main__":
    unittest.main()
