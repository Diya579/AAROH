"""
AAROH Day 2 Integration & Service Layer Test Suite
Author: Preet

Verifies:
1. ML -> Intervention: Consumes ML outputs as-is, never recalculates, routes LOW_CONFIDENCE/ABSTAINED/INSUFFICIENT_DATA to human review (never LOW_RISK).
2. Routing & Jurisdiction: Strict district isolation, primary & backup in same district, unassigned + capacity flag when no officer exists, MISSING_JURISDICTION on empty/invalid district.
3. Priority + SLA: Priority separate from risk, UTC-aware, exact windows (URGENT 4h, HIGH 24h, ROUTINE 72h, LOW 120h), workflow status distinct from SLA status.
4. Outcomes & Transitions: State machine enforcement, rejection of invalid/terminal transitions, latest outcome strictly MAX(recorded_at).
5. Closed Loop: Distress trajectory tracking with non-causal association.
6. Multi-Tier Analytics: K<3 privacy suppression, state rollup via raw numerators/denominators (never percentage averages), national rollup.
7. Service Integration: Clean service methods produce business-ready dictionaries for FastAPI and Frontend.
"""

from datetime import datetime, timedelta, timezone
import unittest

try:
    from backend.interventions.service import (
        OperationalInterventionService,
        intervention_service,
    )
    from backend.interventions.routing import (
        AssigneeRole,
        AssignmentRouter,
        RoutingStatus,
        SyntheticOfficer,
    )
    from backend.interventions.sla import SLAStatus, ensure_utc
    from backend.interventions.outcomes import OutcomeType
    from backend.interventions.engine import InterventionStatus, PriorityLevel, InterventionType
    from backend.analytics.district_metrics import DistrictSummaryMetrics
except ImportError:
    from interventions.service import (
        OperationalInterventionService,
        intervention_service,
    )
    from interventions.routing import (
        AssigneeRole,
        AssignmentRouter,
        RoutingStatus,
        SyntheticOfficer,
    )
    from interventions.sla import SLAStatus, ensure_utc
    from interventions.outcomes import OutcomeType
    from interventions.engine import InterventionStatus, PriorityLevel, InterventionType
    from analytics.district_metrics import DistrictSummaryMetrics


class TestDay2IntegrationAndOperationalCorrectness(unittest.TestCase):
    def setUp(self) -> None:
        self.service = OperationalInterventionService()

    # -------------------------------------------------------------------------
    # 1. ML -> Intervention
    # -------------------------------------------------------------------------
    def test_01_ml_output_consumed_as_is_without_recalculation(self) -> None:
        """Verifies ML outputs are consumed as-is without altering probabilities or risk."""
        res = self.service.evaluate_intervention(
            case_id="CASE-DAY2-01",
            risk_level="HIGH",
            escalation_probability=0.88,
            trajectory="RAPIDLY_WORSENING",
            confidence=0.92,
            factors=["acute fear", "severe intimidation"],
            monitoring_consent=True,
        )
        self.assertEqual(res["case_id"], "CASE-DAY2-01")
        self.assertEqual(res["intervention_type"], "PRIORITY_HUMAN_REVIEW")
        self.assertEqual(res["priority"], "URGENT")
        self.assertEqual(res["reason"]["risk_level"], "HIGH")
        self.assertEqual(res["reason"]["escalation_probability"], 0.88)
        self.assertIn("WITNESS_PROTECTION_SUPPORT", res["suggested_categories"])

    def test_02_uncertainty_and_abstention_never_produce_low_risk(self) -> None:
        """
        Verifies LOW_CONFIDENCE, ABSTAINED, and INSUFFICIENT_DATA route to
        PRIORITY_HUMAN_REVIEW with HIGH priority, never LOW_RISK.
        """
        for status in ("LOW_CONFIDENCE", "ABSTAINED", "INSUFFICIENT_DATA"):
            res = self.service.evaluate_intervention(
                case_id=f"CASE-UNCERTAIN-{status}",
                risk_level="LOW",  # Even if nominal upstream risk is LOW
                escalation_probability=0.10,
                trajectory="STABLE",
                confidence=0.35,  # Low confidence
                ml_status=status,
                monitoring_consent=True,
            )
            self.assertEqual(
                res["intervention_type"],
                "PRIORITY_HUMAN_REVIEW",
                f"Status {status} must trigger PRIORITY_HUMAN_REVIEW",
            )
            self.assertEqual(
                res["priority"],
                "HIGH",
                f"Status {status} must trigger HIGH priority human review",
            )
            self.assertIn(
                status,
                res["reason"]["abstention_reason"],
            )

    def test_03_consent_absence_blocks_automated_interventions(self) -> None:
        """Absence of monitoring consent halts automated interventions."""
        res = self.service.evaluate_intervention(
            case_id="CASE-NO-CONSENT",
            risk_level="HIGH",
            escalation_probability=0.95,
            trajectory="RAPIDLY_WORSENING",
            monitoring_consent=False,
        )
        self.assertEqual(res["intervention_type"], "NO_AUTOMATED_INTERVENTION")
        self.assertEqual(res["priority"], "NONE")
        self.assertIn("consent is absent", res["reason"]["abstention_reason"])

    # -------------------------------------------------------------------------
    # 2. Routing & Jurisdiction
    # -------------------------------------------------------------------------
    def test_04_missing_jurisdiction_returns_missing_jurisdiction(self) -> None:
        """Missing or empty district returns MISSING_JURISDICTION."""
        for invalid_district in (None, "", "   "):
            res = self.service.assign_intervention(
                case_id="CASE-NO-DISTRICT",
                district=invalid_district,
                intervention_type="PRIORITY_HUMAN_REVIEW",
                priority="URGENT",
            )
            self.assertEqual(res["status"], "MISSING_JURISDICTION")
            self.assertIsNone(res["primary_assignee"])
            self.assertIsNone(res["backup_assignee"])
            self.assertFalse(res["capacity_flag"])

    def test_05_strict_district_isolation_and_backup_in_same_district(self) -> None:
        """Primary and backup must both belong to the exact target district."""
        custom_officers = [
            SyntheticOfficer("OFF-PATNA-1", "Patna Officer 1", AssigneeRole.COUNSELLOR, "Patna", active_caseload=2),
            SyntheticOfficer("OFF-PATNA-2", "Patna Officer 2", AssigneeRole.COUNSELLOR, "Patna", active_caseload=4),
            SyntheticOfficer("OFF-DELHI-1", "Delhi Officer 1", AssigneeRole.COUNSELLOR, "Delhi", active_caseload=0),
        ]
        res = self.service.assign_intervention(
            case_id="CASE-PATNA-ISO",
            district="Patna",
            intervention_type="HUMAN_FOLLOW_UP",
            priority="HIGH",
            officers=custom_officers,
        )
        self.assertEqual(res["status"], "ASSIGNED")
        self.assertEqual(res["primary_assignee"], "OFF-PATNA-1")
        self.assertEqual(res["backup_assignee"], "OFF-PATNA-2")
        self.assertNotEqual(res["primary_assignee"], "OFF-DELHI-1")
        self.assertNotEqual(res["backup_assignee"], "OFF-DELHI-1")
        self.assertFalse(res["capacity_flag"])

    def test_06_unassigned_and_capacity_flag_when_no_officer_available(self) -> None:
        """
        When all officers in target district are at capacity (or none exist),
        case is left unassigned and capacity is flagged.
        """
        full_officers = [
            SyntheticOfficer("OFF-FULL-1", "Busy Officer", AssigneeRole.COUNSELLOR, "Ranchi", active_caseload=10, max_capacity=10),
            SyntheticOfficer("OFF-OTHER-1", "Delhi Officer", AssigneeRole.COUNSELLOR, "Delhi", active_caseload=0, max_capacity=10),
        ]
        res = self.service.assign_intervention(
            case_id="CASE-RANCHI-FULL",
            district="Ranchi",
            intervention_type="HUMAN_FOLLOW_UP",
            priority="HIGH",
            officers=full_officers,
        )
        self.assertEqual(res["status"], "ROUTING_UNAVAILABLE")
        self.assertIsNone(res["primary_assignee"])
        self.assertIsNone(res["backup_assignee"])
        self.assertTrue(res["capacity_flag"])

    # -------------------------------------------------------------------------
    # 3. Priority + SLA
    # -------------------------------------------------------------------------
    def test_07_sla_exact_windows_and_utc_awareness(self) -> None:
        """Verifies SLA windows: URGENT 4h, HIGH 24h, ROUTINE 72h, LOW 120h in UTC."""
        now = datetime.now(timezone.utc)
        windows = {
            "URGENT": 4.0,
            "HIGH": 24.0,
            "ROUTINE": 72.0,
            "LOW": 120.0,
        }
        for prio, hours in windows.items():
            res = self.service.calculate_sla(
                intervention_id=101,
                priority=prio,
                created_at=now,
                current_time=now,
            )
            created_dt = datetime.fromisoformat(res["created_at"])
            due_dt = datetime.fromisoformat(res["due_at"])
            diff_hours = (due_dt - created_dt).total_seconds() / 3600.0
            self.assertAlmostEqual(diff_hours, hours, places=1)
            self.assertIsNotNone(created_dt.tzinfo)
            self.assertIsNotNone(due_dt.tzinfo)

    def test_08_separate_workflow_status_from_sla_status(self) -> None:
        """Completed interventions are never actively overdue; recorded as MET or BREACHED."""
        created = datetime.now(timezone.utc) - timedelta(hours=10)
        # 1. Completed within window (e.g. HIGH 24h window, completed in 5h)
        met_res = self.service.calculate_sla(
            intervention_id=201,
            priority="HIGH",
            created_at=created,
            completed_at=created + timedelta(hours=5),
            current_time=datetime.now(timezone.utc),
        )
        self.assertFalse(met_res["is_overdue"])
        self.assertEqual(met_res["sla_status"], "MET")
        self.assertEqual(met_res["response_time_hours"], 5.0)

        # 2. Completed after window (URGENT 4h window, completed in 8h)
        breached_res = self.service.calculate_sla(
            intervention_id=202,
            priority="URGENT",
            created_at=created,
            completed_at=created + timedelta(hours=8),
            current_time=datetime.now(timezone.utc),
        )
        self.assertFalse(breached_res["is_overdue"])
        self.assertEqual(breached_res["sla_status"], "BREACHED")
        self.assertEqual(breached_res["response_time_hours"], 8.0)

        # 3. Uncompleted after window -> actively OVERDUE
        overdue_res = self.service.calculate_sla(
            intervention_id=203,
            priority="URGENT",
            created_at=created,
            completed_at=None,
            current_time=datetime.now(timezone.utc),
        )
        self.assertTrue(overdue_res["is_overdue"])
        self.assertEqual(overdue_res["sla_status"], "OVERDUE")

    # -------------------------------------------------------------------------
    # 4. Outcomes & Lifecycle
    # -------------------------------------------------------------------------
    def test_09_state_machine_valid_and_invalid_transitions(self) -> None:
        """Valid transitions succeed; terminal and illegal skips raise ValueError."""
        # Valid progression: PENDING -> ASSIGNED
        step1 = self.service.record_outcome(
            case_id="CASE-SM-01",
            intervention_id=301,
            outcome_type="CONTACTED",
            current_status="PENDING",
            new_status="ASSIGNED",
        )
        self.assertTrue(step1["status_transition"]["transition_valid"])

        # Invalid terminal transition: COMPLETED -> PENDING
        with self.assertRaises(ValueError):
            self.service.record_outcome(
                case_id="CASE-SM-01",
                intervention_id=301,
                outcome_type="OTHER",
                current_status="COMPLETED",
                new_status="PENDING",
            )

        # Invalid jump: PENDING -> COMPLETED
        with self.assertRaises(ValueError):
            self.service.record_outcome(
                case_id="CASE-SM-01",
                intervention_id=301,
                outcome_type="RESOLVED",
                current_status="PENDING",
                new_status="COMPLETED",
            )

    def test_10_latest_outcome_selected_by_max_recorded_at(self) -> None:
        """Latest outcome is strictly resolved by MAX(recorded_at), regardless of order."""
        t1 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)
        t3 = datetime(2026, 9, 3, 15, 0, tzinfo=timezone.utc)

        # Shuffled list
        outcomes = [
            {"outcome_type": "CONTACTED", "recorded_at": t1.isoformat()},
            {"outcome_type": "RESOLVED", "recorded_at": t3.isoformat()},  # LATEST
            {"outcome_type": "COUNSELLING_PROVIDED", "recorded_at": t2.isoformat()},
        ]

        metrics = self.service.get_case_analytics(
            case_id="CASE-OUT-01",
            distress_score=0.45,
            trajectory="IMPROVING",
            escalation_prob=0.20,
            risk_level="LOW",
            confidence=0.90,
            outcomes=outcomes,
        )
        self.assertEqual(metrics["latest_outcome"], "RESOLVED")

    # -------------------------------------------------------------------------
    # 5. Closed Loop
    # -------------------------------------------------------------------------
    def test_11_closed_loop_tracking_reports_temporal_association(self) -> None:
        """Closed loop evaluates distress difference non-causally."""
        # Subsequent improvement: 0.80 -> 0.60 (diff -0.20 <= -0.10)
        res_imp = self.service.record_outcome(
            case_id="CASE-CL-01",
            intervention_id=401,
            outcome_type="COUNSELLING_PROVIDED",
            current_status="IN_PROGRESS",
            new_status="COMPLETED",
            pre_distress_score=0.80,
            pre_trajectory="WORSENING",
            post_distress_score=0.60,
            post_trajectory="IMPROVING",
        )
        self.assertEqual(
            res_imp["closed_loop_observation"]["observed_shift"],
            "SUBSEQUENT_IMPROVEMENT",
        )

        # Subsequent deterioration: 0.40 -> 0.65 (diff +0.25 >= 0.10)
        res_det = self.service.record_outcome(
            case_id="CASE-CL-02",
            intervention_id=402,
            outcome_type="CONTACTED",
            current_status="IN_PROGRESS",
            new_status="COMPLETED",
            pre_distress_score=0.40,
            pre_trajectory="STABLE",
            post_distress_score=0.65,
            post_trajectory="WORSENING",
        )
        self.assertEqual(
            res_det["closed_loop_observation"]["observed_shift"],
            "SUBSEQUENT_DETERIORATION",
        )

    # -------------------------------------------------------------------------
    # 6. Analytics: Privacy & Sound Aggregation
    # -------------------------------------------------------------------------
    def test_12_privacy_suppression_k_less_than_three(self) -> None:
        """Sensitive breakdown counts of 1 or 2 are masked as '<3'."""
        cases = [
            {"risk_level": "HIGH", "trajectory": "RAPIDLY_WORSENING"},
            {"risk_level": "LOW", "trajectory": "STABLE"},
            {"risk_level": "LOW", "trajectory": "STABLE"},
            {"risk_level": "LOW", "trajectory": "STABLE"},
        ]
        res = self.service.get_district_analytics(
            district="Bhopal",
            case_records=cases,
            intervention_records=[],
            outcome_records=[],
            suppress_small_cells=True,
        )
        self.assertEqual(res["total_monitored_cases"], 4)  # Total unmasked
        self.assertEqual(res["risk_distribution"]["HIGH"], "<3")  # Count 1 masked
        self.assertEqual(res["risk_distribution"]["LOW"], 3)     # Count 3 unmasked
        self.assertEqual(res["trajectory_alerts"]["RAPIDLY_WORSENING"], "<3")
        self.assertTrue(res["small_cell_suppression_applied"])

    def test_13_state_and_national_sound_aggregation_numerators_first(self) -> None:
        """
        Rollup aggregates raw numerators and denominators first.
        Avoids distorted averaging of percentages across different sized districts.
        """
        # District A: 1 case, met SLA -> 100%
        # District B: 9 cases, 0 met SLA -> 0%
        # Simple average of percentages = 50% (INCORRECT)
        # Correct numerator/denominator rollup: 1 / 10 = 10.0%
        d1 = DistrictSummaryMetrics(
            district="Dist-A",
            total_monitored_cases=1,
            high_risk_cases=1,
            moderate_risk_cases=0,
            low_risk_cases=0,
            rapidly_worsening_cases=0,
            worsening_cases=0,
            pending_interventions=0,
            overdue_interventions=0,
            completed_interventions=1,
            met_sla_interventions=1,
            evaluated_sla_interventions=1,
            total_response_time_sum_hours=2.0,
            total_responded_interventions=1,
            avg_response_time_hours=2.0,
            sla_compliance_rate=100.0,
            outcome_distribution={},
        )
        d2 = DistrictSummaryMetrics(
            district="Dist-B",
            total_monitored_cases=9,
            high_risk_cases=9,
            moderate_risk_cases=0,
            low_risk_cases=0,
            rapidly_worsening_cases=0,
            worsening_cases=0,
            pending_interventions=0,
            overdue_interventions=0,
            completed_interventions=9,
            met_sla_interventions=0,
            evaluated_sla_interventions=9,
            total_response_time_sum_hours=90.0,
            total_responded_interventions=9,
            avg_response_time_hours=10.0,
            sla_compliance_rate=0.0,
            outcome_distribution={},
        )

        state_res = self.service.get_state_analytics("Bihar", [d1, d2])
        self.assertEqual(state_res["total_monitored_cases"], 10)
        self.assertEqual(state_res["performance"]["overall_sla_compliance_rate"], 10.0)
        # Total response hours = 92.0 / 10 = 9.2h
        self.assertEqual(state_res["performance"]["avg_response_time_hours"], 9.2)

        # National rollup
        nat_res = self.service.get_national_analytics([state_res])
        self.assertEqual(nat_res["total_monitored_cases"], 10)
        self.assertEqual(nat_res["performance"]["overall_sla_compliance_rate"], 10.0)
        self.assertEqual(nat_res["performance"]["avg_response_time_hours"], 9.2)


if __name__ == "__main__":
    unittest.main()
