"""
AAROH — Intervention Outcomes & Closed-Loop Feedback Engine
Author: Preet

Manages the valid status state machine, records structured outcomes using
a controlled vocabulary, and closes the feedback loop between interventions
and subsequent distress observations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from .engine import InterventionStatus


class OutcomeType(str, Enum):
    CONTACTED = "CONTACTED"
    COUNSELLING_PROVIDED = "COUNSELLING_PROVIDED"
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED"
    REFERRED = "REFERRED"
    UNABLE_TO_CONTACT = "UNABLE_TO_CONTACT"
    DECLINED = "DECLINED"
    RESOLVED = "RESOLVED"
    OTHER = "OTHER"


VALID_STATUS_TRANSITIONS: Dict[InterventionStatus, Set[InterventionStatus]] = {
    InterventionStatus.PENDING: {
        InterventionStatus.ASSIGNED,
        InterventionStatus.ESCALATED,
        InterventionStatus.CANCELLED,
    },
    InterventionStatus.ASSIGNED: {
        InterventionStatus.ACKNOWLEDGED,
        InterventionStatus.PENDING,
        InterventionStatus.ESCALATED,
        InterventionStatus.CANCELLED,
    },
    InterventionStatus.ACKNOWLEDGED: {
        InterventionStatus.IN_PROGRESS,
        InterventionStatus.ESCALATED,
    },
    InterventionStatus.IN_PROGRESS: {
        InterventionStatus.COMPLETED,
        InterventionStatus.ESCALATED,
    },
    InterventionStatus.ESCALATED: {
        InterventionStatus.ASSIGNED,
        InterventionStatus.ACKNOWLEDGED,
        InterventionStatus.IN_PROGRESS,
    },
    InterventionStatus.COMPLETED: set(),  # Terminal state
    InterventionStatus.CANCELLED: set(),  # Terminal state
}


@dataclass
class OutcomeRecord:
    case_id: str
    intervention_id: int
    outcome_type: OutcomeType
    completed: bool = True
    follow_up_required: bool = False
    notes: Optional[str] = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "intervention_id": self.intervention_id,
            "outcome_type": self.outcome_type.value,
            "completed": self.completed,
            "follow_up_required": self.follow_up_required,
            "notes": self.notes,
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass
class ClosedLoopObservation:
    case_id: str
    intervention_id: int
    outcome_type: OutcomeType
    pre_distress_score: float
    pre_trajectory: str
    post_distress_score: Optional[float] = None
    post_trajectory: Optional[str] = None
    observed_shift: Optional[str] = None

    def evaluate_shift(self, post_score: float, post_trajectory: str) -> str:
        self.post_distress_score = post_score
        self.post_trajectory = post_trajectory

        diff = round(post_score - self.pre_distress_score, 4)
        if diff <= -0.10:
            self.observed_shift = "SUBSEQUENT_IMPROVEMENT"
        elif diff >= 0.10:
            self.observed_shift = "SUBSEQUENT_DETERIORATION"
        else:
            self.observed_shift = "SUBSEQUENT_STABLE"

        return self.observed_shift

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "intervention_id": self.intervention_id,
            "outcome_type": self.outcome_type.value,
            "pre_distress_score": self.pre_distress_score,
            "pre_trajectory": self.pre_trajectory,
            "post_distress_score": self.post_distress_score,
            "post_trajectory": self.post_trajectory,
            "observed_shift": self.observed_shift,
        }


class OutcomeManager:
    """
    Validates status transitions, records outcomes, and tracks closed-loop observations.
    """

    @staticmethod
    def validate_transition(
        current_status: InterventionStatus,
        new_status: InterventionStatus,
    ) -> bool:
        allowed = VALID_STATUS_TRANSITIONS.get(current_status, set())
        return new_status in allowed

    @staticmethod
    def transition_status(
        current_status: InterventionStatus,
        new_status: InterventionStatus,
    ) -> InterventionStatus:
        if not OutcomeManager.validate_transition(current_status, new_status):
            raise ValueError(
                f"Invalid status transition from {current_status.value} to {new_status.value}."
            )
        return new_status

    @staticmethod
    def create_outcome(
        case_id: str,
        intervention_id: int,
        outcome_type: OutcomeType,
        completed: bool = True,
        follow_up_required: bool = False,
        notes: Optional[str] = None,
    ) -> OutcomeRecord:
        return OutcomeRecord(
            case_id=case_id,
            intervention_id=intervention_id,
            outcome_type=outcome_type,
            completed=completed,
            follow_up_required=follow_up_required,
            notes=notes,
        )
