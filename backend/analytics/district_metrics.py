"""
AAROH — District-Level Analytics Engine
Author: Preet

Aggregates operational metrics across all monitored cases in a given district.
Enforces privacy boundaries by exposing only aggregate distributions and counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    avg_response_time_hours: Optional[float]
    sla_compliance_rate: float
    outcome_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "district": self.district,
            "total_monitored_cases": self.total_monitored_cases,
            "risk_distribution": {
                "HIGH": self.high_risk_cases,
                "MODERATE": self.moderate_risk_cases,
                "LOW": self.low_risk_cases,
            },
            "trajectory_alerts": {
                "RAPIDLY_WORSENING": self.rapidly_worsening_cases,
                "WORSENING": self.worsening_cases,
            },
            "intervention_workload": {
                "pending": self.pending_interventions,
                "overdue": self.overdue_interventions,
                "completed": self.completed_interventions,
            },
            "performance": {
                "avg_response_time_hours": self.avg_response_time_hours,
                "sla_compliance_rate": round(self.sla_compliance_rate, 2),
            },
            "outcome_distribution": self.outcome_distribution,
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

        # Response times and SLA
        response_times = [
            float(i["response_time_hours"])
            for i in intervention_records
            if i.get("response_time_hours") is not None
        ]
        avg_rt = round(sum(response_times) / len(response_times), 2) if response_times else None

        total_evaluated_sla = sum(
            1 for i in intervention_records if i.get("status") in ("COMPLETED", "MET", "BREACHED")
        )
        met_sla = sum(
            1 for i in intervention_records if i.get("is_overdue") is False and i.get("status") == "COMPLETED"
        )
        sla_rate = (met_sla / total_evaluated_sla * 100.0) if total_evaluated_sla > 0 else 100.0

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
            avg_response_time_hours=avg_rt,
            sla_compliance_rate=sla_rate,
            outcome_distribution=outcomes_dist,
        )
