"""Public inference entry point.

Returns a nested dict. Never writes to PostgreSQL. Slice 1 does not load or
train models; without injected estimates the call fails closed (no fake LOW).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping, Optional

from backend.ml.config import InferenceConfig
from backend.ml.contract import (
    DistressOutput,
    ExplanationOutput,
    MlInferenceResult,
    ModelOutput,
    PredictionOutput,
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
    abstained_result,
    failed_result,
    insufficient_data_result,
)
from backend.ml.policies import (
    ConfidenceAbstentionPolicy,
    EvidenceContext,
    ThresholdConfidencePolicy,
)


def infer(
    ml_input: Mapping[str, Any],
    *,
    config: Optional[InferenceConfig] = None,
    estimates: Optional[Mapping[str, Any]] = None,
    evidence: Optional[EvidenceContext] = None,
    policy: Optional[ConfidenceAbstentionPolicy] = None,
) -> dict[str, Any]:
    """Run inference and return an ML API contract dict.

    Parameters
    ----------
    ml_input:
        Application payload. ``case_id`` is required. ``prediction_date`` is
        optional (defaults to UTC today).
    estimates:
        Optional numeric estimates from a future model or test double.
        Slice 1 has no trained estimator; omitting this yields FAILED.
    evidence:
        Optional missingness / data-quality context for abstention.
    policy:
        Confidence/abstention policy. Defaults to ``ThresholdConfidencePolicy``.
    """

    cfg = config or InferenceConfig()
    case_id = ml_input.get("case_id")
    if not case_id:
        return failed_result(
            case_id="UNKNOWN",
            prediction_date=_prediction_date(ml_input),
            message="case_id is required.",
        ).to_dict()

    prediction_date = _prediction_date(ml_input)

    if estimates is None:
        return failed_result(
            case_id=str(case_id),
            prediction_date=prediction_date,
            message=(
                "No estimator is loaded. Slice 1 exposes the inference "
                "interface only; models are not trained yet."
            ),
        ).to_dict()

    try:
        candidate = _candidate_from_estimates(
            case_id=str(case_id),
            prediction_date=prediction_date,
            estimates=estimates,
            horizon_days=cfg.target_horizon_days,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return failed_result(
            case_id=str(case_id),
            prediction_date=prediction_date,
            message=f"Invalid estimates: {exc}",
        ).to_dict()

    evidence_ctx = evidence or EvidenceContext(
        observation_count=int(ml_input.get("observation_count", 1)),
        missing_feature_count=int(ml_input.get("missing_feature_count", 0)),
        text_available=bool(ml_input.get("text_available", False)),
        voice_available=bool(ml_input.get("voice_available", False)),
        data_quality_insufficient=bool(
            ml_input.get("data_quality_insufficient", False)
        ),
    )

    decision = (policy or ThresholdConfidencePolicy()).decide(
        distress_confidence=candidate.distress.confidence if candidate.distress else None,
        prediction_confidence=(
            candidate.prediction.confidence if candidate.prediction else None
        ),
        evidence=evidence_ctx,
        config=cfg,
    )

    if decision.status == ProcessingStatus.INSUFFICIENT_DATA:
        return insufficient_data_result(
            case_id=str(case_id),
            prediction_date=prediction_date,
            message=decision.message or "Insufficient evidence.",
            model=candidate.model,
        ).to_dict()

    if decision.status == ProcessingStatus.ABSTAINED:
        return abstained_result(
            case_id=str(case_id),
            prediction_date=prediction_date,
            message=decision.message or "The model abstained.",
            source=candidate.source,
            distress=candidate.distress,
            explanation=candidate.explanation,
            model=candidate.model,
        ).to_dict()

    if decision.status == ProcessingStatus.LOW_CONFIDENCE:
        return MlInferenceResult(
            case_id=candidate.case_id,
            prediction_date=candidate.prediction_date,
            status=ProcessingStatus.LOW_CONFIDENCE,
            source=candidate.source,
            distress=candidate.distress,
            prediction=candidate.prediction,
            explanation=candidate.explanation,
            model=candidate.model,
            message=decision.message,
        ).to_dict()

    return candidate.to_dict()


def _prediction_date(ml_input: Mapping[str, Any]) -> str:
    raw = ml_input.get("prediction_date")
    if raw is None:
        return date.today().isoformat()
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    return date.fromisoformat(str(raw)[:10]).isoformat()


def _candidate_from_estimates(
    *,
    case_id: str,
    prediction_date: str,
    estimates: Mapping[str, Any],
    horizon_days: int,
) -> MlInferenceResult:
    distress_raw = estimates["distress"]
    prediction_raw = estimates["prediction"]
    model_raw = estimates["model"]
    explanation_raw = estimates.get("explanation")

    if "target_horizon_days" in prediction_raw:
        horizon = int(prediction_raw["target_horizon_days"])
    else:
        horizon = horizon_days

    distress = DistressOutput(
        score=float(distress_raw["score"]),
        trajectory=Trajectory(distress_raw["trajectory"]),
        confidence=float(distress_raw["confidence"]),
        baseline_deviation=(
            None
            if distress_raw.get("baseline_deviation") is None
            else float(distress_raw["baseline_deviation"])
        ),
    )

    prediction = PredictionOutput(
        escalation_probability=float(prediction_raw["escalation_probability"]),
        target_horizon_days=horizon,
        confidence=float(prediction_raw["confidence"]),
        risk_level=RiskLevel(prediction_raw["risk_level"]),
    )

    explanation = None
    if explanation_raw is not None:
        explanation = ExplanationOutput(
            factors=tuple(str(item) for item in (explanation_raw.get("factors") or [])),
            trend=Trajectory(explanation_raw.get("trend", distress.trajectory.value)),
            baseline_deviation=(
                None
                if explanation_raw.get("baseline_deviation") is None
                else float(explanation_raw["baseline_deviation"])
            ),
        )

    source_raw = estimates.get("source", ResultSource.ML.value)
    source = ResultSource(source_raw)

    return MlInferenceResult(
        case_id=case_id,
        prediction_date=prediction_date,
        status=ProcessingStatus.SUCCESS,
        source=source,
        distress=distress,
        prediction=prediction,
        explanation=explanation,
        model=ModelOutput(
            model_name=str(model_raw["model_name"]),
            model_version=str(model_raw["model_version"]),
        ),
    )
