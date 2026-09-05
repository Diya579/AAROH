"""
AAROH — National-Level Analytics Engine
Author: Preet

Provides nationwide macro visibility into atrocity monitoring, system workloads,
and response effectiveness with strict privacy enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from .state_metrics import StateSummaryMetrics


@dataclass
class NationalSummaryMetrics:
    total_states: int
    total_monitored_cases: int
    national_high_risk_cases: int
    national_moderate_risk_cases: int
    national_low_risk_cases: int
    national_pending_interventions: int
    national_overdue_interventions: int
    national_completed_interventions: int
    overall_sla_compliance_rate: float
    state_breakdown: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_states": self.total_states,
            "total_monitored_cases": self.total_monitored_cases,
            "national_risk_distribution": {
                "HIGH": self.national_high_risk_cases,
                "MODERATE": self.national_moderate_risk_cases,
                "LOW": self.national_low_risk_cases,
            },
            "national_intervention_workload": {
                "pending": self.national_pending_interventions,
                "overdue": self.national_overdue_interventions,
                "completed": self.national_completed_interventions,
            },
            "overall_sla_compliance_rate": round(self.overall_sla_compliance_rate, 2),
            "state_breakdown": self.state_breakdown,
        }


class NationalMetricsCalculator:
    """
    Rolls up state summaries into national aggregates.
    Enforces privacy rules: eliminates individual narratives and applies small-cell suppression.
    """

    @staticmethod
    def calculate(states: List[StateSummaryMetrics]) -> NationalSummaryMetrics:
        if not states:
            return NationalSummaryMetrics(
                total_states=0,
                total_monitored_cases=0,
                national_high_risk_cases=0,
                national_moderate_risk_cases=0,
                national_low_risk_cases=0,
                national_pending_interventions=0,
                national_overdue_interventions=0,
                national_completed_interventions=0,
                overall_sla_compliance_rate=100.0,
                state_breakdown=[],
            )

        total_cases = sum(s.total_monitored_cases for s in states)
        high = sum(s.total_high_risk for s in states)
        mod = sum(s.total_moderate_risk for s in states)
        low = sum(s.total_low_risk for s in states)

        pending = sum(s.total_pending_interventions for s in states)
        overdue = sum(s.total_overdue_interventions for s in states)
        completed = sum(s.total_completed_interventions for s in states)

        avg_sla = sum(s.overall_sla_compliance_rate for s in states) / len(states)

        breakdown = [s.to_dict() for s in states]

        return NationalSummaryMetrics(
            total_states=len(states),
            total_monitored_cases=total_cases,
            national_high_risk_cases=high,
            national_moderate_risk_cases=mod,
            national_low_risk_cases=low,
            national_pending_interventions=pending,
            national_overdue_interventions=overdue,
            national_completed_interventions=completed,
            overall_sla_compliance_rate=avg_sla,
            state_breakdown=breakdown,
        )
