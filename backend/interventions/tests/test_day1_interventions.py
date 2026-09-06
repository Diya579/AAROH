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
from datetime import datetime, timedelta, timezone

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
    RoutingStatus,
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

    def test_abstained_status_triggers_priority_human_review(self):
        decision = self.engine.evaluate(
            case_id="AAROH-ABSTAIN",
            risk_level="LOW",
            escalation_probability=0.0,
            trajectory="STABLE",
            confidence=0.0,
            ml_status="ABSTAINED",
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.PRIORITY_HUMAN_REVIEW)
        self.assertEqual(decision.priority, PriorityLevel.HIGH)
        self.assertIn("insufficient (ABSTAINED)", decision.reason.abstention_reason)

    def test_insufficient_data_status_triggers_priority_human_review(self):
        decision = self.engine.evaluate(
            case_id="AAROH-NODATA",
            risk_level="LOW",
            escalation_probability=0.0,
            trajectory="STABLE",
            confidence=0.0,
            ml_status="INSUFFICIENT_DATA",
            monitoring_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.PRIORITY_HUMAN_REVIEW)
        self.assertEqual(decision.priority, PriorityLevel.HIGH)
        self.assertIn("insufficient (INSUFFICIENT_DATA)", decision.reason.abstention_reason)

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
        self.assertEqual(result.status, RoutingStatus.ASSIGNED)

    def test_routing_refuses_cross_district_fallback(self):
        # District with no registered officers
        router = AssignmentRouter()
        result = router.route(
            case_id="CASE-03",
            district="Varanasi",
            intervention_type=InterventionType.PRIORITY_HUMAN_REVIEW,
            priority=PriorityLevel.URGENT,
        )
        self.assertEqual(result.status, RoutingStatus.ROUTING_UNAVAILABLE)
        self.assertIsNone(result.primary_assignee)
        self.assertIsNone(result.backup_assignee)
        self.assertIn("ROUTING_UNAVAILABLE", result.notes)

    def test_routing_rejects_missing_or_empty_district(self):
        router = AssignmentRouter()
        result = router.route(
            case_id="CASE-04",
            district="",
            intervention_type=InterventionType.HUMAN_FOLLOW_UP,
            priority=PriorityLevel.HIGH,
        )
        self.assertEqual(result.status, RoutingStatus.INVALID_JURISDICTION)
        self.assertIsNone(result.primary_assignee)
        self.assertIsNone(result.assigned_at)

    def test_routing_deterministic_tie_breaking(self):
        # Two officers with exact same caseload in same district
        officers = [
            SyntheticOfficer("SYNTH-B", "Officer B", AssigneeRole.COUNSELLOR, "Patna", active_caseload=2),
            SyntheticOfficer("SYNTH-A", "Officer A", AssigneeRole.COUNSELLOR, "Patna", active_caseload=2),
        ]
        router = AssignmentRouter(officers=officers)
        result = router.route(
            case_id="CASE-05",
            district="Patna",
            intervention_type=InterventionType.HUMAN_FOLLOW_UP,
            priority=PriorityLevel.HIGH,
        )
        # SYNTH-A must win alphabetically when caseloads tie
        self.assertEqual(result.primary_assignee, "SYNTH-A")
        self.assertEqual(result.backup_assignee, "SYNTH-B")

    def test_routing_respects_capacity_and_availability(self):
        officers = [
            SyntheticOfficer("SYNTH-FULL", "Full Officer", AssigneeRole.COUNSELLOR, "Patna", active_caseload=10, max_capacity=10),
            SyntheticOfficer("SYNTH-UNAVAIL", "Unavail Officer", AssigneeRole.COUNSELLOR, "Patna", active_caseload=0, is_available=False),
            SyntheticOfficer("SYNTH-OK", "Available Officer", AssigneeRole.COUNSELLOR, "Patna", active_caseload=4, max_capacity=10),
        ]
        router = AssignmentRouter(officers=officers)
        result = router.route(
            case_id="CASE-06",
            district="Patna",
            intervention_type=InterventionType.HUMAN_FOLLOW_UP,
            priority=PriorityLevel.HIGH,
        )
        self.assertEqual(result.primary_assignee, "SYNTH-OK")
        self.assertIsNone(result.backup_assignee)  # No other eligible in district


class TestSLA(unittest.TestCase):
    def setUp(self):
        self.manager = SLAManager()

    def test_sla_due_time_calculation(self):
        base_time = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)
        due_urgent = self.manager.compute_due_time(PriorityLevel.URGENT, base_time)
        self.assertEqual(due_urgent, base_time + timedelta(hours=4))

        due_high = self.manager.compute_due_time(PriorityLevel.HIGH, base_time)
        self.assertEqual(due_high, base_time + timedelta(hours=24))

    def test_overdue_detection(self):
        created = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)
        due = created + timedelta(hours=4)
        record = SLARecord(1, PriorityLevel.URGENT, created, due)

        # Before deadline
        self.assertEqual(record.evaluate_status(created + timedelta(hours=1)), SLAStatus.PENDING)
        self.assertFalse(record.is_overdue(created + timedelta(hours=1)))

        # Due soon (85% elapsed)
        self.assertEqual(record.evaluate_status(created + timedelta(hours=3, minutes=30)), SLAStatus.DUE_SOON)
        self.assertFalse(record.is_overdue(created + timedelta(hours=3, minutes=30)))

        # Overdue (past 4h)
        self.assertEqual(record.evaluate_status(created + timedelta(hours=5)), SLAStatus.OVERDUE)
        self.assertTrue(record.is_overdue(created + timedelta(hours=5)))

    def test_completed_intervention_is_never_overdue_status(self):
        created = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)
        due = created + timedelta(hours=4)
        # Completed late (at 6 hours)
        record = SLARecord(1, PriorityLevel.URGENT, created, due, completed_at=created + timedelta(hours=6))

        # is_overdue must be False because it is completed
        self.assertFalse(record.is_overdue(created + timedelta(hours=7)))
        # SLAStatus is BREACHED, not active OVERDUE
        self.assertEqual(record.evaluate_status(created + timedelta(hours=7)), SLAStatus.BREACHED)

    def test_completed_before_deadline_is_met(self):
        created = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)
        due = created + timedelta(hours=4)
        # Completed on time (at 2 hours)
        record = SLARecord(1, PriorityLevel.URGENT, created, due, completed_at=created + timedelta(hours=2))

        self.assertFalse(record.is_overdue(created + timedelta(hours=5)))
        self.assertEqual(record.evaluate_status(created + timedelta(hours=5)), SLAStatus.MET)

    def test_sla_safe_with_naive_and_aware_datetimes(self):
        created_naive = datetime(2026, 9, 5, 10, 0, 0)
        due_naive = created_naive + timedelta(hours=4)
        record = SLARecord(2, PriorityLevel.URGENT, created_naive, due_naive)

        # Querying with timezone-aware datetime should not throw TypeError
        now_aware = datetime(2026, 9, 5, 15, 0, 0, tzinfo=timezone.utc)
        self.assertTrue(record.is_overdue(now_aware))
        self.assertEqual(record.evaluate_status(now_aware), SLAStatus.OVERDUE)


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

    def test_latest_outcome_selected_by_recorded_at_not_list_order(self):
        # Outcomes list where the earlier outcome is placed first and latest outcome is placed second
        t_early = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
        t_late = datetime(2026, 9, 5, 14, 0, 0, tzinfo=timezone.utc)
        outcomes_reversed = [
            {"outcome_type": "CONTACTED", "recorded_at": t_early},
            {"outcome_type": "RESOLVED", "recorded_at": t_late},
        ]
        metrics = CaseMetricsCalculator.calculate(
            case_id="CASE-ORDER",
            distress_score=0.4,
            trajectory="STABLE",
            escalation_prob=0.3,
            risk_level="LOW",
            confidence=0.9,
            outcomes=outcomes_reversed,
        )
        # Even though CONTACTED is first in the list, RESOLVED has the newer timestamp
        self.assertEqual(metrics.latest_outcome, "RESOLVED")

    def test_separate_consent_fields_preservation(self):
        engine = InterventionEngine()
        # Voice consent denied, but monitoring consent granted
        decision = engine.evaluate(
            case_id="CASE-CONSENT",
            risk_level="HIGH",
            escalation_probability=0.80,
            trajectory="RAPIDLY_WORSENING",
            monitoring_consent=True,
            text_analysis_consent=True,
            voice_analysis_consent=False,
            case_linkage_consent=True,
        )
        self.assertEqual(decision.intervention_type, InterventionType.PRIORITY_HUMAN_REVIEW)
        self.assertIsNotNone(decision.reason.consent_status)
        self.assertFalse(decision.reason.consent_status["voice_analysis_consent"])
        self.assertTrue(decision.reason.consent_status["monitoring_consent"])


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

    def test_small_cell_suppression_masks_sensitive_counts(self):
        cases = [
            {"case_id": "C1", "risk_level": "HIGH", "trajectory": "RAPIDLY_WORSENING"},
            {"case_id": "C2", "risk_level": "HIGH", "trajectory": "STABLE"},
            {"case_id": "C3", "risk_level": "LOW", "trajectory": "STABLE"},
        ]
        outcomes = [{"outcome_type": "REFERRED"}]
        metrics = DistrictMetricsCalculator.calculate("Patna", cases, [], outcomes)

        # Masked output
        masked = metrics.to_dict(suppress_small_cells=True)
        # high_risk is 2, low_risk is 1 -> both are <3 and must be masked
        self.assertEqual(masked["risk_distribution"]["HIGH"], "<3")
        self.assertEqual(masked["risk_distribution"]["LOW"], "<3")
        self.assertEqual(masked["risk_distribution"]["MODERATE"], 0)  # 0 is not masked
        self.assertEqual(masked["outcome_distribution"]["REFERRED"], "<3")
        # Broad total is not masked
        self.assertEqual(masked["total_monitored_cases"], 3)
        self.assertTrue(masked["small_cell_suppression_applied"])
        self.assertIn("risk_distribution.HIGH", masked["suppressed_fields"])

        # Unmasked raw output
        unmasked = metrics.to_dict(suppress_small_cells=False)
        self.assertEqual(unmasked["risk_distribution"]["HIGH"], 2)
        self.assertEqual(unmasked["risk_distribution"]["LOW"], 1)
        self.assertFalse(unmasked["small_cell_suppression_applied"])

    def test_state_and_national_rollup_does_not_average_percentages(self):
        # District 1: 1 intervention, 1 met SLA -> 100% SLA rate
        d1 = DistrictMetricsCalculator.calculate(
            "District1",
            [{"case_id": "D1-C1"}],
            [{"status": "COMPLETED", "is_overdue": False, "response_time_hours": 1.0}],
            [],
        )
        self.assertEqual(d1.sla_compliance_rate, 100.0)

        # District 2: 9 interventions, 0 met SLA -> 0% SLA rate
        d2_interventions = [
            {"status": "COMPLETED", "is_overdue": True, "response_time_hours": 5.0}
            for _ in range(9)
        ]
        d2 = DistrictMetricsCalculator.calculate(
            "District2",
            [{"case_id": f"D2-C{i}"} for i in range(9)],
            d2_interventions,
            [],
        )
        self.assertEqual(d2.sla_compliance_rate, 0.0)

        # Averaging percentages would wrongly give: (100 + 0) / 2 = 50.0%
        # Correct aggregate: 1 met out of 10 evaluated = 10.0%
        state = StateMetricsCalculator.calculate("StateX", [d1, d2])
        self.assertEqual(state.overall_sla_compliance_rate, 10.0)

        national = NationalMetricsCalculator.calculate([state])
        self.assertEqual(national.overall_sla_compliance_rate, 10.0)

    def test_missing_data_distinguishable_from_zero(self):
        # When no interventions exist, SLA compliance and response time must be None, not 0.0
        metrics = DistrictMetricsCalculator.calculate("EmptyDistrict", [], [], [])
        self.assertIsNone(metrics.avg_response_time_hours)
        self.assertIsNone(metrics.sla_compliance_rate)

        state = StateMetricsCalculator.calculate("EmptyState", [metrics])
        self.assertIsNone(state.avg_response_time_hours)
        self.assertIsNone(state.overall_sla_compliance_rate)

    def test_privacy_leakage_prevented_in_all_summaries(self):
        # Ensure no raw text, notes, transcripts, or audio data leak into dictionary representations
        d = DistrictMetricsCalculator.calculate("Patna", [{"case_id": "C1"}], [], [])
        d_dict = d.to_dict()
        forbidden_keys = {"text_response", "narrative", "transcript", "notes", "audio_path", "audio"}
        for k in d_dict.keys():
            self.assertNotIn(k, forbidden_keys)

    def test_invalid_status_transitions_comprehensive(self):
        # Direct jump from PENDING to COMPLETED is invalid (must go through ASSIGNED/ACKNOWLEDGED/IN_PROGRESS)
        with self.assertRaises(ValueError):
            OutcomeManager.transition_status(InterventionStatus.PENDING, InterventionStatus.COMPLETED)

        # Cancelled is terminal
        with self.assertRaises(ValueError):
            OutcomeManager.transition_status(InterventionStatus.CANCELLED, InterventionStatus.IN_PROGRESS)


if __name__ == "__main__":
    unittest.main()
