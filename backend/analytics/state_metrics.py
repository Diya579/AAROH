"""
AAROH — State-Level Analytics Engine
Author: Preet

Aggregates district summaries across an entire state to support regional
resource allocation and high-level atrocity monitoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
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
    overall_sla_compliance_rate: float
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
            "overall_sla_compliance_rate": round(self.overall_sla_compliance_rate, 2),
            "district_comparison": self.district_summaries,
        }


class StateMetricsCalculator:
    """
    Rolls up district summaries into state-level metrics.
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
                overall_sla_compliance_rate=100.0,
                district_summaries=[],
            )

        total_cases = sum(d.total_monitored_cases for d in districts)
        high = sum(d.high_risk_cases for d in districts)
        mod = sum(d.moderate_risk_cases for d in districts)
        low = sum(d.low_risk_cases for d in districts)

        pending = sum(d.pending_interventions for d in districts)
        overdue = sum(d.overdue_interventions for d in districts)
        completed = sum(d.completed_interventions for d in districts)

        avg_sla = sum(d.sla_compliance_rate for d in districts) / len(districts)

        summaries = [d.to_dict() for d in districts]

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
            overall_sla_compliance_rate=avg_sla,
            district_summaries=summaries,
        )
