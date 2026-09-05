"""
AAROH — Case-Level Analytics Engine
Author: Preet

Calculates individual case longitudinal profiles, active intervention states,
and response performance metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CaseSummaryMetrics:
    case_id: str
    current_distress_score: float
    current_trajectory: str
    escalation_probability: float
    risk_level: str
    confidence: float
    active_interventions_count: int
    overdue_interventions_count: int
    completed_interventions_count: int
    avg_response_time_hours: Optional[float] = None
    latest_outcome: Optional[str] = None
    last_interaction_date: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "current_distress_score": round(self.current_distress_score, 4),
            "current_trajectory": self.current_trajectory,
            "escalation_probability": round(self.escalation_probability, 4),
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 4),
            "active_interventions_count": self.active_interventions_count,
            "overdue_interventions_count": self.overdue_interventions_count,
            "completed_interventions_count": self.completed_interventions_count,
            "avg_response_time_hours": self.avg_response_time_hours,
            "latest_outcome": self.latest_outcome,
            "last_interaction_date": (
                self.last_interaction_date.isoformat()
                if self.last_interaction_date
                else None
            ),
        }


class CaseMetricsCalculator:
    """
    Computes analytical summaries for single cases.
    """

    @staticmethod
    def calculate(
        case_id: str,
        distress_score: float,
        trajectory: str,
        escalation_prob: float,
        risk_level: str,
        confidence: float,
        interventions: Optional[List[Dict[str, Any]]] = None,
        outcomes: Optional[List[Dict[str, Any]]] = None,
        last_interaction_date: Optional[datetime] = None,
    ) -> CaseSummaryMetrics:
        int_list = interventions or []
        out_list = outcomes or []

        active_count = sum(
            1 for i in int_list
            if i.get("status") in ("PENDING", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS", "ESCALATED")
        )
        completed_count = sum(
            1 for i in int_list if i.get("status") == "COMPLETED"
        )
        overdue_count = sum(
            1 for i in int_list if i.get("is_overdue", False)
        )

        # Average response time from interventions with recorded response times
        response_times = [
            float(i["response_time_hours"])
            for i in int_list
            if i.get("response_time_hours") is not None
        ]
        avg_rt = round(sum(response_times) / len(response_times), 2) if response_times else None

        latest_outcome = out_list[0].get("outcome_type") if out_list else None

        return CaseSummaryMetrics(
            case_id=case_id,
            current_distress_score=distress_score,
            current_trajectory=trajectory,
            escalation_probability=escalation_prob,
            risk_level=risk_level,
            confidence=confidence,
            active_interventions_count=active_count,
            overdue_interventions_count=overdue_count,
            completed_interventions_count=completed_count,
            avg_response_time_hours=avg_rt,
            latest_outcome=latest_outcome,
            last_interaction_date=last_interaction_date,
        )
