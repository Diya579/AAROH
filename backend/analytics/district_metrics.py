"""
AAROH — District-Level Analytics Engine
Author: Preet

Aggregates operational metrics across all monitored cases in a given district.
Enforces privacy boundaries by exposing only aggregate distributions and counts.
Implements small-cell suppression (<3) for sensitive granular metrics to prevent
victim re-identification, while preserving exact numerators and denominators for
mathematically sound state/national rollups.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def mask_small_cell(val: int) -> Any:
    """
    Rule 10: Granular cells with 1 or 2 occurrences are suppressed as '<3'
    to prevent re-identification in low-volume districts.
    Zero remains 0.
    """
    if 0 < val < 3:
        return "<3"
    return val


@dataclass
class DistrictSummaryMetrics:
    district: str
    total_monitored_cases: int
    high_risk_cases: int
    moderate_risk_cases: int
    low_risk_cases: int
    rapidly_worsening_cases: int
    worsening_cases: int
    pending_interventions: int
    overdue_interventions: int
    completed_interventions: int
    met_sla_interventions: int
    evaluated_sla_interventions: int
    total_response_time_sum_hours: float
    total_responded_interventions: int
    avg_response_time_hours: Optional[float]
    sla_compliance_rate: Optional[float]
    outcome_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self, suppress_small_cells: bool = True) -> Dict[str, Any]:
        """
        Exports dictionary representation.
        If suppress_small_cells is True, applies k-anonymity guard (<3) to sensitive granular fields.
        """
        suppressed_fields: List[str] = []

        def _apply_mask(val: int, field_name: str) -> Any:
            masked = mask_small_cell(val) if suppress_small_cells else val
            if masked == "<3":
                suppressed_fields.append(field_name)
            return masked

        masked_risk = {
            "HIGH": _apply_mask(self.high_risk_cases, "risk_distribution.HIGH"),
            "MODERATE": _apply_mask(self.moderate_risk_cases, "risk_distribution.MODERATE"),
            "LOW": _apply_mask(self.low_risk_cases, "risk_distribution.LOW"),
        }

        masked_trajectories = {
            "RAPIDLY_WORSENING": _apply_mask(self.rapidly_worsening_cases, "trajectory_alerts.RAPIDLY_WORSENING"),
            "WORSENING": _apply_mask(self.worsening_cases, "trajectory_alerts.WORSENING"),
        }

        masked_outcomes = {
            k: _apply_mask(v, f"outcome_distribution.{k}")
            for k, v in self.outcome_distribution.items()
        }

        return {
            "district": self.district,
            "total_monitored_cases": self.total_monitored_cases,
            "risk_distribution": masked_risk,
            "trajectory_alerts": masked_trajectories,
            "intervention_workload": {
                "pending": self.pending_interventions,
                "overdue": self.overdue_interventions,
                "completed": self.completed_interventions,
            },
            "performance": {
                "avg_response_time_hours": self.avg_response_time_hours,
                "sla_compliance_rate": self.sla_compliance_rate,
            },
            "outcome_distribution": masked_outcomes,
            "small_cell_suppression_applied": len(suppressed_fields) > 0,
            "suppressed_fields": suppressed_fields,
        }


class DistrictMetricsCalculator:
    """
    Computes aggregate metrics for an administrative district.
    """

    @staticmethod
    def calculate(
        district: str,
        case_records: List[Dict[str, Any]],
        intervention_records: List[Dict[str, Any]],
        outcome_records: List[Dict[str, Any]],
    ) -> DistrictSummaryMetrics:
        total_cases = len(case_records)

        # Risk distribution
        high_risk = sum(1 for c in case_records if str(c.get("risk_level", "")).upper() == "HIGH")
        mod_risk = sum(1 for c in case_records if str(c.get("risk_level", "")).upper() == "MODERATE")
        low_risk = sum(1 for c in case_records if str(c.get("risk_level", "")).upper() == "LOW")

        # Trajectories
        rapid_worsening = sum(
            1 for c in case_records if str(c.get("trajectory", "")).upper() == "RAPIDLY_WORSENING"
        )
        worsening = sum(
            1 for c in case_records if str(c.get("trajectory", "")).upper() == "WORSENING"
        )

        # Interventions
        pending = sum(
            1 for i in intervention_records
            if i.get("status") in ("PENDING", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS")
        )
        overdue = sum(1 for i in intervention_records if i.get("is_overdue", False))
        completed = sum(1 for i in intervention_records if i.get("status") == "COMPLETED")

        # Response times: aggregate exact sum and count
        response_times = [
            float(i["response_time_hours"])
            for i in intervention_records
            if i.get("response_time_hours") is not None
        ]
        rt_sum = sum(response_times)
        rt_count = len(response_times)
        avg_rt = round(rt_sum / rt_count, 2) if rt_count > 0 else None

        # SLA compliance: aggregate exact numerators and denominators
        # An intervention is evaluated for SLA if it is completed or breached/met
        total_evaluated_sla = sum(
            1 for i in intervention_records if i.get("status") in ("COMPLETED", "MET", "BREACHED")
        )
        met_sla = sum(
            1 for i in intervention_records
            if i.get("status") in ("COMPLETED", "MET") and not i.get("is_overdue", False)
        )
        sla_rate = (
            round((met_sla / total_evaluated_sla) * 100.0, 2)
            if total_evaluated_sla > 0
            else None
        )

        # Outcome distribution
        outcomes_dist: Dict[str, int] = {}
        for out in outcome_records:
            ot = str(out.get("outcome_type", "OTHER"))
            outcomes_dist[ot] = outcomes_dist.get(ot, 0) + 1

        return DistrictSummaryMetrics(
            district=district,
            total_monitored_cases=total_cases,
            high_risk_cases=high_risk,
            moderate_risk_cases=mod_risk,
            low_risk_cases=low_risk,
            rapidly_worsening_cases=rapid_worsening,
            worsening_cases=worsening,
            pending_interventions=pending,
            overdue_interventions=overdue,
            completed_interventions=completed,
            met_sla_interventions=met_sla,
            evaluated_sla_interventions=total_evaluated_sla,
            total_response_time_sum_hours=rt_sum,
            total_responded_interventions=rt_count,
            avg_response_time_hours=avg_rt,
            sla_compliance_rate=sla_rate,
            outcome_distribution=outcomes_dist,
        )
