"""
AAROH — State-Level Analytics Engine
Author: Preet

Aggregates district summaries across an entire state to support regional
resource allocation and high-level atrocity monitoring.
Enforces Rule 11: Aggregates numerators and denominators first,
never averaging district percentages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .district_metrics import DistrictSummaryMetrics


@dataclass
class StateSummaryMetrics:
    state: str
    total_districts: int
    total_monitored_cases: int
    total_high_risk: int
    total_moderate_risk: int
    total_low_risk: int
    total_pending_interventions: int
    total_overdue_interventions: int
    total_completed_interventions: int
    total_met_sla_interventions: int
    total_evaluated_sla_interventions: int
    total_response_time_sum_hours: float
    total_responded_interventions: int
    overall_sla_compliance_rate: Optional[float]
    avg_response_time_hours: Optional[float]
    district_summaries: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "total_districts": self.total_districts,
            "total_monitored_cases": self.total_monitored_cases,
            "risk_totals": {
                "HIGH": self.total_high_risk,
                "MODERATE": self.total_moderate_risk,
                "LOW": self.total_low_risk,
            },
            "intervention_totals": {
                "pending": self.total_pending_interventions,
                "overdue": self.total_overdue_interventions,
                "completed": self.total_completed_interventions,
            },
            "performance": {
                "overall_sla_compliance_rate": self.overall_sla_compliance_rate,
                "avg_response_time_hours": self.avg_response_time_hours,
            },
            "total_met_sla_interventions": self.total_met_sla_interventions,
            "total_evaluated_sla_interventions": self.total_evaluated_sla_interventions,
            "total_response_time_sum_hours": self.total_response_time_sum_hours,
            "total_responded_interventions": self.total_responded_interventions,
            "district_comparison": self.district_summaries,
        }


class StateMetricsCalculator:
    """
    Rolls up district summaries into state-level metrics.
    Aggregates numerators and denominators across districts before computing percentages.
    """

    @staticmethod
    def calculate(
        state: str,
        districts: List[DistrictSummaryMetrics],
    ) -> StateSummaryMetrics:
        if not districts:
            return StateSummaryMetrics(
                state=state,
                total_districts=0,
                total_monitored_cases=0,
                total_high_risk=0,
                total_moderate_risk=0,
                total_low_risk=0,
                total_pending_interventions=0,
                total_overdue_interventions=0,
                total_completed_interventions=0,
                total_met_sla_interventions=0,
                total_evaluated_sla_interventions=0,
                total_response_time_sum_hours=0.0,
                total_responded_interventions=0,
                overall_sla_compliance_rate=None,
                avg_response_time_hours=None,
                district_summaries=[],
            )

        total_cases = sum(d.total_monitored_cases for d in districts)
        high = sum(d.high_risk_cases for d in districts)
        mod = sum(d.moderate_risk_cases for d in districts)
        low = sum(d.low_risk_cases for d in districts)

        pending = sum(d.pending_interventions for d in districts)
        overdue = sum(d.overdue_interventions for d in districts)
        completed = sum(d.completed_interventions for d in districts)

        # Rule 11: Aggregate numerators and denominators first
        met_sla = sum(d.met_sla_interventions for d in districts)
        eval_sla = sum(d.evaluated_sla_interventions for d in districts)
        overall_sla = round((met_sla / eval_sla) * 100.0, 2) if eval_sla > 0 else None

        rt_sum = sum(d.total_response_time_sum_hours for d in districts)
        rt_count = sum(d.total_responded_interventions for d in districts)
        avg_rt = round(rt_sum / rt_count, 2) if rt_count > 0 else None

        summaries = [d.to_dict(suppress_small_cells=True) for d in districts]

        return StateSummaryMetrics(
            state=state,
            total_districts=len(districts),
            total_monitored_cases=total_cases,
            total_high_risk=high,
            total_moderate_risk=mod,
            total_low_risk=low,
            total_pending_interventions=pending,
            total_overdue_interventions=overdue,
            total_completed_interventions=completed,
            total_met_sla_interventions=met_sla,
            total_evaluated_sla_interventions=eval_sla,
            total_response_time_sum_hours=rt_sum,
            total_responded_interventions=rt_count,
            overall_sla_compliance_rate=overall_sla,
            avg_response_time_hours=avg_rt,
            district_summaries=summaries,
        )
