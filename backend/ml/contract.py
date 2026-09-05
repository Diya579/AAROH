"""Nested ML inference result contract.

Matches ``docs/ML_API_CONTRACT.md`` (distress, prediction, explanation, model)
plus processing ``status`` and result ``source`` so callers can tell ML, baseline,
fallback, and insufficient-evidence outputs apart.

This module never connects to PostgreSQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Mapping, Optional


class Trajectory(str, Enum):
    STABLE = "STABLE"
    IMPROVING = "IMPROVING"
    WORSENING = "WORSENING"
    RAPIDLY_IMPROVING = "RAPIDLY_IMPROVING"
    RAPIDLY_WORSENING = "RAPIDLY_WORSENING"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class ProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    ABSTAINED = "ABSTAINED"


class ResultSource(str, Enum):
    """How the numeric result was produced.

    Never present a rule-based number as ``ML``.
    """

    ML = "ml"
    BASELINE = "baseline"
    FALLBACK = "fallback"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


STATUSES_WITHOUT_PREDICTION = frozenset(
    {
        ProcessingStatus.FAILED,
        ProcessingStatus.INSUFFICIENT_DATA,
        ProcessingStatus.ABSTAINED,
    }
)


def _require_unit_interval(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0.0, 1.0], got {value!r}")


def _format_prediction_date(value: date | datetime | str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    parsed = date.fromisoformat(str(value)[:10])
    return parsed.isoformat()


@dataclass(frozen=True)
class DistressOutput:
    score: float
    trajectory: Trajectory
    confidence: float
    baseline_deviation: Optional[float]

    def __post_init__(self) -> None:
        _require_unit_interval("distress.score", self.score)
        _require_unit_interval("distress.confidence", self.confidence)
        if self.baseline_deviation is not None and self.baseline_deviation < 0:
            raise ValueError("distress.baseline_deviation must be >= 0 or null")

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "trajectory": self.trajectory.value,
            "confidence": self.confidence,
            "baseline_deviation": self.baseline_deviation,
        }


@dataclass(frozen=True)
class PredictionOutput:
    escalation_probability: float
    target_horizon_days: int
    confidence: float
    risk_level: RiskLevel

    def __post_init__(self) -> None:
        _require_unit_interval(
            "prediction.escalation_probability",
            self.escalation_probability,
        )
        _require_unit_interval("prediction.confidence", self.confidence)
        if self.target_horizon_days <= 0:
            raise ValueError("prediction.target_horizon_days must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "escalation_probability": self.escalation_probability,
            "target_horizon_days": self.target_horizon_days,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
        }


@dataclass(frozen=True)
class ExplanationOutput:
    factors: tuple[str, ...]
    trend: Trajectory
    baseline_deviation: Optional[float]

    def __post_init__(self) -> None:
        if self.baseline_deviation is not None and self.baseline_deviation < 0:
            raise ValueError("explanation.baseline_deviation must be >= 0 or null")

    def to_dict(self) -> dict[str, Any]:
        return {
            "factors": list(self.factors),
            "trend": self.trend.value,
            "baseline_deviation": self.baseline_deviation,
        }


@dataclass(frozen=True)
class ModelOutput:
    model_name: str
    model_version: str

    def __post_init__(self) -> None:
        if not self.model_name or not self.model_version:
            raise ValueError("model_name and model_version are required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
        }


@dataclass(frozen=True)
class MlInferenceResult:
    """Nested inference result returned to the application layer."""

    case_id: str
    prediction_date: str
    status: ProcessingStatus
    source: ResultSource
    distress: Optional[DistressOutput] = None
    prediction: Optional[PredictionOutput] = None
    explanation: Optional[ExplanationOutput] = None
    model: Optional[ModelOutput] = None
    message: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("case_id is required")

        _format_prediction_date(self.prediction_date)

        if self.status in STATUSES_WITHOUT_PREDICTION:
            if self.prediction is not None:
                raise ValueError(
                    f"status {self.status.value} must not include a prediction payload"
                )
        else:
            if self.distress is None or self.prediction is None:
                raise ValueError(
                    f"status {self.status.value} requires distress and prediction"
                )
            if self.model is None:
                raise ValueError(
                    f"status {self.status.value} requires model identity"
                )

        if (
            self.status == ProcessingStatus.INSUFFICIENT_DATA
            and self.source != ResultSource.INSUFFICIENT_EVIDENCE
        ):
            raise ValueError(
                "INSUFFICIENT_DATA must use source insufficient_evidence"
            )

        if (
            self.source == ResultSource.INSUFFICIENT_EVIDENCE
            and self.status not in (
                ProcessingStatus.INSUFFICIENT_DATA,
                ProcessingStatus.ABSTAINED,
            )
        ):
            raise ValueError(
                "source insufficient_evidence requires INSUFFICIENT_DATA or ABSTAINED"
            )

    def to_dict(self) -> dict[str, Any]:
        """Application-facing nested dict. Does not write to a database."""

        payload: dict[str, Any] = {
            "case_id": self.case_id,
            "prediction_date": _format_prediction_date(self.prediction_date),
            "status": self.status.value,
            "source": self.source.value,
            "distress": None if self.distress is None else self.distress.to_dict(),
            "prediction": (
                None if self.prediction is None else self.prediction.to_dict()
            ),
            "explanation": (
                None if self.explanation is None else self.explanation.to_dict()
            ),
            "model": None if self.model is None else self.model.to_dict(),
        }
        if self.message is not None:
            payload["message"] = self.message
        return payload


def failed_result(
    case_id: str,
    prediction_date: date | datetime | str,
    *,
    message: str,
    source: ResultSource = ResultSource.ML,
    model: Optional[ModelOutput] = None,
) -> MlInferenceResult:
    """Technical failure: no fabricated LOW / 0.0 prediction."""

    return MlInferenceResult(
        case_id=case_id,
        prediction_date=_format_prediction_date(prediction_date),
        status=ProcessingStatus.FAILED,
        source=source,
        distress=None,
        prediction=None,
        explanation=None,
        model=model,
        message=message,
    )


def insufficient_data_result(
    case_id: str,
    prediction_date: date | datetime | str,
    *,
    message: str,
    model: Optional[ModelOutput] = None,
) -> MlInferenceResult:
    return MlInferenceResult(
        case_id=case_id,
        prediction_date=_format_prediction_date(prediction_date),
        status=ProcessingStatus.INSUFFICIENT_DATA,
        source=ResultSource.INSUFFICIENT_EVIDENCE,
        distress=None,
        prediction=None,
        explanation=None,
        model=model,
        message=message,
    )


def abstained_result(
    case_id: str,
    prediction_date: date | datetime | str,
    *,
    message: str,
    source: ResultSource = ResultSource.ML,
    distress: Optional[DistressOutput] = None,
    explanation: Optional[ExplanationOutput] = None,
    model: Optional[ModelOutput] = None,
) -> MlInferenceResult:
    return MlInferenceResult(
        case_id=case_id,
        prediction_date=_format_prediction_date(prediction_date),
        status=ProcessingStatus.ABSTAINED,
        source=source,
        distress=distress,
        prediction=None,
        explanation=explanation,
        model=model,
        message=message,
    )


def result_from_mapping(data: Mapping[str, Any]) -> MlInferenceResult:
    """Build a validated result from nested mappings (tests and adapters)."""

    distress_raw = data.get("distress")
    prediction_raw = data.get("prediction")
    explanation_raw = data.get("explanation")
    model_raw = data.get("model")

    distress = None
    if distress_raw is not None:
        distress = DistressOutput(
            score=float(distress_raw["score"]),
            trajectory=Trajectory(distress_raw["trajectory"]),
            confidence=float(distress_raw["confidence"]),
            baseline_deviation=_optional_float(distress_raw.get("baseline_deviation")),
        )

    prediction = None
    if prediction_raw is not None:
        prediction = PredictionOutput(
            escalation_probability=float(prediction_raw["escalation_probability"]),
            target_horizon_days=int(prediction_raw["target_horizon_days"]),
            confidence=float(prediction_raw["confidence"]),
            risk_level=RiskLevel(prediction_raw["risk_level"]),
        )

    explanation = None
    if explanation_raw is not None:
        factors = explanation_raw.get("factors") or []
        explanation = ExplanationOutput(
            factors=tuple(str(item) for item in factors),
            trend=Trajectory(explanation_raw["trend"]),
            baseline_deviation=_optional_float(explanation_raw.get("baseline_deviation")),
        )

    model = None
    if model_raw is not None:
        model = ModelOutput(
            model_name=str(model_raw["model_name"]),
            model_version=str(model_raw["model_version"]),
        )

    return MlInferenceResult(
        case_id=str(data["case_id"]),
        prediction_date=_format_prediction_date(data["prediction_date"]),
        status=ProcessingStatus(data["status"]),
        source=ResultSource(data["source"]),
        distress=distress,
        prediction=prediction,
        explanation=explanation,
        model=model,
        message=data.get("message"),
    )


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)
