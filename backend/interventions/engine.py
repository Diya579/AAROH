"""
AAROH — Operational Intervention Decision Engine
Author: Preet

This module implements the core business logic for mapping ML predictions,
distress trajectories, confidence, and consent status into actionable,
human-centred intervention recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional, Sequence


class InterventionType(str, Enum):
    NO_AUTOMATED_INTERVENTION = "NO_AUTOMATED_INTERVENTION"
    PRIORITY_HUMAN_REVIEW = "PRIORITY_HUMAN_REVIEW"
    HUMAN_FOLLOW_UP = "HUMAN_FOLLOW_UP"
    CONTINUE_MONITORING = "CONTINUE_MONITORING"
    ROUTINE_MONITORING = "ROUTINE_MONITORING"


class PriorityLevel(str, Enum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    ROUTINE = "ROUTINE"
    LOW = "LOW"
    NONE = "NONE"


class InterventionStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ESCALATED = "ESCALATED"
    CANCELLED = "CANCELLED"


class InterventionCategory(str, Enum):
    COUNSELLING_PSYCHOLOGICAL_SUPPORT = "COUNSELLING_PSYCHOLOGICAL_SUPPORT"
    MEDICAL_TREATMENT_REFERRAL = "MEDICAL_TREATMENT_REFERRAL"
    WITNESS_PROTECTION_SUPPORT = "WITNESS_PROTECTION_SUPPORT"
    RELOCATION_SAFETY_SUPPORT = "RELOCATION_SAFETY_SUPPORT"
    FINANCIAL_COMPENSATION_ASSISTANCE = "FINANCIAL_COMPENSATION_ASSISTANCE"
    LEGAL_AID = "LEGAL_AID"
    REHABILITATION_SUPPORT = "REHABILITATION_SUPPORT"
    CONTINUED_MONITORING = "CONTINUED_MONITORING"


@dataclass(frozen=True)
class InterventionReason:
    risk_level: str
    trajectory: str
    escalation_probability: float
    confidence: float
    factors: tuple[str, ...] = field(default_factory=tuple)
    abstention_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "risk_level": self.risk_level,
            "trajectory": self.trajectory,
            "escalation_probability": round(self.escalation_probability, 4),
            "confidence": round(self.confidence, 4),
            "factors": list(self.factors),
        }
        if self.abstention_reason:
            data["abstention_reason"] = self.abstention_reason
        return data


@dataclass
class InterventionDecision:
    case_id: str
    intervention_type: InterventionType
    priority: PriorityLevel
    reason: InterventionReason
    suggested_categories: List[InterventionCategory]
    is_duplicate: bool = False
    existing_intervention_id: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "intervention_type": self.intervention_type.value,
            "priority": self.priority.value,
            "reason": self.reason.to_dict(),
            "suggested_categories": [cat.value for cat in self.suggested_categories],
            "is_duplicate": self.is_duplicate,
            "existing_intervention_id": self.existing_intervention_id,
            "created_at": self.created_at.isoformat(),
        }


class InterventionEngine:
    """
    Evaluates predictions and contextual signals to generate operational recommendations.
    Enforces ethical boundaries: recommendations assist authorized officials,
    never autonomously executing critical actions (e.g. forced medical treatment or witness relocation).
    """

    def __init__(
        self,
        high_risk_prob_threshold: float = 0.75,
        moderate_risk_prob_threshold: float = 0.40,
        min_confidence_threshold: float = 0.50,
    ) -> None:
        self.high_risk_prob_threshold = high_risk_prob_threshold
        self.moderate_risk_prob_threshold = moderate_risk_prob_threshold
        self.min_confidence_threshold = min_confidence_threshold

    def evaluate(
        self,
        case_id: str,
        risk_level: str,
        escalation_probability: float,
        trajectory: str,
        confidence: float = 1.0,
        factors: Optional[Sequence[str]] = None,
        monitoring_consent: bool = True,
        ml_status: str = "SUCCESS",
        active_interventions: Optional[Sequence[dict[str, Any]]] = None,
    ) -> InterventionDecision:
        """
        Main decision method evaluating ML outputs and operational constraints.
        """
        factor_tuple = tuple(factors) if factors else ()

        # 1. CONSENT CHECK
        # Monitoring consent is absolute. If missing, block automated intervention.
        if not monitoring_consent:
            reason = InterventionReason(
                risk_level=risk_level,
                trajectory=trajectory,
                escalation_probability=escalation_probability,
                confidence=confidence,
                factors=factor_tuple,
                abstention_reason="Monitoring consent is absent or revoked.",
            )
            return InterventionDecision(
                case_id=case_id,
                intervention_type=InterventionType.NO_AUTOMATED_INTERVENTION,
                priority=PriorityLevel.NONE,
                reason=reason,
                suggested_categories=[],
            )

        # 2. ABSTENTION & LOW-CONFIDENCE CHECK
        # Never convert uncertainty into low risk. Require human review.
        if (
            ml_status in ("LOW_CONFIDENCE", "ABSTAINED", "INSUFFICIENT_DATA")
            or confidence < self.min_confidence_threshold
        ):
            reason = InterventionReason(
                risk_level=risk_level,
                trajectory=trajectory,
                escalation_probability=escalation_probability,
                confidence=confidence,
                factors=factor_tuple,
                abstention_reason=f"Model confidence is insufficient ({ml_status}). Human review required.",
            )
            decision = InterventionDecision(
                case_id=case_id,
                intervention_type=InterventionType.PRIORITY_HUMAN_REVIEW,
                priority=PriorityLevel.HIGH,
                reason=reason,
                suggested_categories=[InterventionCategory.CONTINUED_MONITORING],
            )
            return self._check_duplicates(decision, active_interventions)

        # 3. HIGH ESCALATION SCENARIOS
        if (
            risk_level.upper() == "HIGH"
            or escalation_probability >= self.high_risk_prob_threshold
            or trajectory.upper() == "RAPIDLY_WORSENING"
        ):
            suggested = [
                InterventionCategory.COUNSELLING_PSYCHOLOGICAL_SUPPORT,
                InterventionCategory.RELOCATION_SAFETY_SUPPORT,
            ]
            if any("fear" in f.lower() or "threat" in f.lower() or "intimidation" in f.lower() for f in factor_tuple):
                suggested.append(InterventionCategory.WITNESS_PROTECTION_SUPPORT)

            reason = InterventionReason(
                risk_level=risk_level,
                trajectory=trajectory,
                escalation_probability=escalation_probability,
                confidence=confidence,
                factors=factor_tuple,
            )
            decision = InterventionDecision(
                case_id=case_id,
                intervention_type=InterventionType.PRIORITY_HUMAN_REVIEW,
                priority=PriorityLevel.URGENT,
                reason=reason,
                suggested_categories=suggested,
            )
            return self._check_duplicates(decision, active_interventions)

        # 4. MODERATE / WORSENING SCENARIOS
        if (
            risk_level.upper() == "MODERATE"
            or escalation_probability >= self.moderate_risk_prob_threshold
            or trajectory.upper() == "WORSENING"
        ):
            suggested = [
                InterventionCategory.COUNSELLING_PSYCHOLOGICAL_SUPPORT,
                InterventionCategory.REHABILITATION_SUPPORT,
            ]
            reason = InterventionReason(
                risk_level=risk_level,
                trajectory=trajectory,
                escalation_probability=escalation_probability,
                confidence=confidence,
                factors=factor_tuple,
            )
            decision = InterventionDecision(
                case_id=case_id,
                intervention_type=InterventionType.HUMAN_FOLLOW_UP,
                priority=PriorityLevel.HIGH,
                reason=reason,
                suggested_categories=suggested,
            )
            return self._check_duplicates(decision, active_interventions)

        # 5. IMPROVING TRAJECTORY
        if trajectory.upper() in ("IMPROVING", "RAPIDLY_IMPROVING"):
            reason = InterventionReason(
                risk_level=risk_level,
                trajectory=trajectory,
                escalation_probability=escalation_probability,
                confidence=confidence,
                factors=factor_tuple,
            )
            decision = InterventionDecision(
                case_id=case_id,
                intervention_type=InterventionType.CONTINUE_MONITORING,
                priority=PriorityLevel.LOW,
                reason=reason,
                suggested_categories=[InterventionCategory.CONTINUED_MONITORING],
            )
            return self._check_duplicates(decision, active_interventions)

        # 6. STABLE / LOW RISK
        reason = InterventionReason(
            risk_level=risk_level,
            trajectory=trajectory,
            escalation_probability=escalation_probability,
            confidence=confidence,
            factors=factor_tuple,
        )
        decision = InterventionDecision(
            case_id=case_id,
            intervention_type=InterventionType.ROUTINE_MONITORING,
            priority=PriorityLevel.ROUTINE,
            reason=reason,
            suggested_categories=[InterventionCategory.CONTINUED_MONITORING],
        )
        return self._check_duplicates(decision, active_interventions)

    def _check_duplicates(
        self,
        decision: InterventionDecision,
        active_interventions: Optional[Sequence[dict[str, Any]]],
    ) -> InterventionDecision:
        """
        Prevents creating multiple identical unresolved/pending interventions for a case.
        """
        if not active_interventions:
            return decision

        for intervention in active_interventions:
            status = intervention.get("status")
            int_type = intervention.get("intervention_type")

            # Active statuses that block duplicate creation
            if status in ("PENDING", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS"):
                if int_type == decision.intervention_type.value:
                    decision.is_duplicate = True
                    decision.existing_intervention_id = intervention.get("id")
                    break

        return decision
