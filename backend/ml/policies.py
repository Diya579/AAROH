"""Confidence and abstention policy interfaces.

Thresholds are configurable. This module does not train a model and does
not access PostgreSQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from backend.ml.config import InferenceConfig
from backend.ml.contract import ProcessingStatus


@dataclass(frozen=True)
class EvidenceContext:
    """Non-clinical evidence quality signals for the policy.

    Missing counts stay explicit. Callers must not coerce missing features to 0
    before filling this context.
    """

    observation_count: int
    missing_feature_count: int
    text_available: bool
    voice_available: bool
    data_quality_insufficient: bool


@dataclass(frozen=True)
class PolicyDecision:
    status: ProcessingStatus
    message: Optional[str] = None


@runtime_checkable
class ConfidenceAbstentionPolicy(Protocol):
    """Decides SUCCESS / LOW_CONFIDENCE / ABSTAINED / INSUFFICIENT_DATA."""

    def decide(
        self,
        *,
        distress_confidence: Optional[float],
        prediction_confidence: Optional[float],
        evidence: EvidenceContext,
        config: InferenceConfig,
    ) -> PolicyDecision:
        ...


class ThresholdConfidencePolicy:
    """Default threshold policy for Slice 1.

    Justification will be revisited when calibrated models exist. Until then
    these cutoffs are explicit configuration, not claimed accuracy.
    """

    def decide(
        self,
        *,
        distress_confidence: Optional[float],
        prediction_confidence: Optional[float],
        evidence: EvidenceContext,
        config: InferenceConfig,
    ) -> PolicyDecision:
        if evidence.observation_count < 1:
            return PolicyDecision(
                status=ProcessingStatus.INSUFFICIENT_DATA,
                message="No usable observations were provided.",
            )

        if (
            not evidence.text_available
            and not evidence.voice_available
            and evidence.missing_feature_count > 0
            and evidence.data_quality_insufficient
        ):
            return PolicyDecision(
                status=ProcessingStatus.INSUFFICIENT_DATA,
                message="Text, voice, and behavioural evidence are insufficient.",
            )

        if prediction_confidence is None or distress_confidence is None:
            return PolicyDecision(
                status=ProcessingStatus.INSUFFICIENT_DATA,
                message="Confidence could not be estimated from the available evidence.",
            )

        overall = min(distress_confidence, prediction_confidence)

        if overall < config.abstain_below_confidence:
            return PolicyDecision(
                status=ProcessingStatus.ABSTAINED,
                message="Confidence is below the abstention threshold.",
            )

        if (
            overall < config.min_success_confidence
            or distress_confidence < config.min_distress_confidence
        ):
            return PolicyDecision(
                status=ProcessingStatus.LOW_CONFIDENCE,
                message="A result was produced but confidence is below the operational threshold.",
            )

        return PolicyDecision(status=ProcessingStatus.SUCCESS)
