"""Escalation Assessment Model (Slice 3.8 Revision).

Transparent, calibrated, supervised Logistic Regression baseline for operational escalation assessment.

Key Characteristics:
- Trainable, probabilistic, calibrated, interpretable, deterministic, lightweight.
- Exposes predict_proba() using true mathematical logistic sigmoid.
- Grounded explainability derived directly from model feature contributions (w_i * x_i).
- Rigorous confidence policy decoupling confidence from probability magnitude.
- Strict abstention handling (INSUFFICIENT_DATA, ABSTAINED, LOW_CONFIDENCE) without fabricating LOW risk or 0.0 probability.
- Strict clinical boundary enforcement: zero psychiatric claims, zero treatment/intervention advice.

Output Contract conforms to AAROH MlInferenceResult:
{
    "case_id": str,
    "prediction_date": str,
    "escalation_probability": float | None,
    "target_horizon_days": int,
    "confidence": float,
    "risk_level": str | None,
    "explanation": {
        "factors": List[str],
        "trend": str,
        "baseline_deviation": float | None,
        "model_version": str
    },
    "model_version": str
}
"""

from __future__ import annotations

import datetime
import json
import math
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from backend.ml.contract import (
    ExplanationOutput,
    MlInferenceResult,
    ModelOutput,
    PredictionOutput,
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
)
from backend.ml.training.models.common import (
    enforce_escalation_boundary,
    set_seed,
)
from backend.ml.training.models.escalation.dataset import (
    DEFAULT_TARGET_HORIZON_DAYS,
    ESCALATION_FEATURE_NAMES,
    LABEL_DISCLAIMER,
    SMOKE_TEST_DISCLAIMER,
    ConfidencePolicyConfig,
    EscalationConfig,
    EscalationInputRecord,
)

DEFAULT_MODEL_VERSION = "aaroh-escalation-v1"
DEFAULT_MODEL_NAME = "aaroh-escalation-assessment"


def _sigmoid(z: float) -> float:
    """Numerically stable logistic sigmoid function."""
    if z >= 35.0:
        return 1.0
    if z <= -35.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))


class EscalationAssessmentModel:
    """Interpretable, calibrated Logistic Regression Escalation Assessment Model."""

    def __init__(
        self,
        config: Optional[EscalationConfig] = None,
        confidence_policy: Optional[ConfidencePolicyConfig] = None,
        model_version: str = DEFAULT_MODEL_VERSION,
        seed: int = 42,
    ) -> None:
        self.config = config or EscalationConfig()
        if confidence_policy is not None:
            self.config.confidence_policy = confidence_policy
        self.confidence_policy = self.config.confidence_policy
        self.model_version = model_version
        self.model_name = DEFAULT_MODEL_NAME
        self.seed = seed
        self.feature_names = list(ESCALATION_FEATURE_NAMES)
        self.num_features = len(self.feature_names)
        self.last_feature_contributions: List[Dict[str, Any]] = []

        # Logistic Regression Parameters: w in R^D, b in R
        self.weights: List[float] = [0.0] * self.num_features
        self.intercept: float = 0.0
        self.is_fitted: bool = False

        # Initialize default calibrated baseline weights
        self._init_baseline_weights()

    def _init_baseline_weights(self) -> None:
        """Sets calibrated baseline weights prioritizing high distress, worsening trajectory, and baseline deviation."""
        # Feature name to calibrated default weight mapping
        default_weights = {
            "distress_score": 1.40,
            "distress_is_high_or_critical": 1.20,
            "distress_is_moderate": 0.40,
            "baseline_deviation": 1.10,
            "baseline_deviation_missing": -0.10,
            "trajectory_score": 1.30,
            "trajectory_is_worsening": 0.90,
            "trajectory_is_rapidly_worsening": 1.50,
            "trajectory_prob_worsening_combined": 0.80,
            "safety_distress": 0.60,
            "safety_distress_missing": 0.0,
            "sleep_disturbance": 0.50,
            "sleep_disturbance_missing": 0.0,
            "fear_intensity": 0.50,
            "fear_intensity_missing": 0.0,
            "help_requested": 1.25,
            "help_requested_missing": 0.0,
            "checkin_consistency": -0.60,  # Protective: high consistency reduces risk
            "checkin_consistency_missing": 0.10,
            "engagement_drop": 0.75,
            "engagement_drop_missing": 0.0,
            "text_available": -0.10,
            "audio_available": -0.10,
            "history_length_norm": -0.20,
            "valid_observation_count_norm": -0.15,
            "distress_emb_norm": 0.0,
            "trajectory_emb_norm": 0.0,
            "fused_emb_norm": 0.0,
        }
        self.weights = [default_weights.get(name, 0.0) for name in self.feature_names]
        self.intercept = -1.80  # Base log-odds (corresponds to base probability ~0.14)
        self.is_fitted = True

    def fit(
        self,
        records: List[EscalationInputRecord],
        epochs: int = 150,
        lr: float = 0.08,
        l2_reg: float = 1e-3,
    ) -> Dict[str, float]:
        """Trains Logistic Regression weights using gradient descent on binary cross-entropy loss."""
        set_seed(self.seed)
        X = [r.to_feature_vector(self.feature_names) for r in records]
        y = [1.0 if r.synthetic_escalation_target == 1 else 0.0 for r in records]
        n = len(X)
        if n == 0:
            return {"initial_loss": 0.0, "final_loss": 0.0}

        dim = len(self.weights)

        # Compute initial loss
        def compute_loss() -> float:
            loss = 0.0
            for i in range(n):
                z = sum(self.weights[j] * X[i][j] for j in range(dim)) + self.intercept
                p = _sigmoid(z)
                p = max(1e-7, min(1.0 - 1e-7, p))
                yi = y[i]
                loss += -(yi * math.log(p) + (1.0 - yi) * math.log(1.0 - p))
            reg = 0.5 * l2_reg * sum(w * w for w in self.weights)
            return (loss / n) + reg

        initial_loss = compute_loss()

        # Gradient descent
        for epoch in range(epochs):
            grad_w = [0.0] * dim
            grad_b = 0.0

            for i in range(n):
                z = sum(self.weights[j] * X[i][j] for j in range(dim)) + self.intercept
                p = _sigmoid(z)
                err = p - y[i]
                grad_b += err
                for j in range(dim):
                    grad_w[j] += err * X[i][j]

            # Update parameters
            self.intercept -= lr * (grad_b / n)
            for j in range(dim):
                self.weights[j] -= lr * ((grad_w[j] / n) + l2_reg * self.weights[j])

        final_loss = compute_loss()
        self.is_fitted = True

        return {
            "initial_loss": round(initial_loss, 4),
            "final_loss": round(final_loss, 4),
        }

    def predict_proba(self, record_or_vector: Union[EscalationInputRecord, List[float]]) -> Tuple[float, float]:
        """Returns [P(Y=0), P(Y=1)] where P(Y=1) is the calibrated escalation probability."""
        if isinstance(record_or_vector, EscalationInputRecord):
            x = record_or_vector.to_feature_vector(self.feature_names)
        else:
            x = record_or_vector

        z = sum(self.weights[j] * x[j] for j in range(len(self.weights))) + self.intercept
        p1 = _sigmoid(z)
        p0 = 1.0 - p1
        return (round(p0, 4), round(p1, 4))

    def compute_confidence(self, record: EscalationInputRecord, probability: float) -> float:
        """Calculates evidence-based confidence score decoupled from probability value.

        Consumes versioned ConfidencePolicyConfig.
        Evaluates:
        - observation_weight (0.35): Depth of history and observation points.
        - text_weight (0.20): Availability of text modality.
        - audio_weight (0.15): Availability of audio modality.
        - missingness_weight (0.15): Completeness of clinical/behavioural indicators.
        - uncertainty_weight (0.15): Distance from maximum ambiguity boundary (|P - 0.5|).
        """
        policy = getattr(self, "confidence_policy", None) or getattr(self.config, "confidence_policy", None) or ConfidencePolicyConfig()

        # 1. Observation History & Depth [0.0, 1.0]
        obs_count = max(record.history_length, record.valid_observation_count)
        obs_term = min(1.0, max(0.0, obs_count / 5.0))

        # 2. Text Modality [0.0 or 1.0]
        text_term = 1.0 if record.text_available else 0.0

        # 3. Audio Modality [0.0 or 1.0]
        audio_term = 1.0 if record.audio_available else 0.0

        # 4. Completeness of non-missing clinical & behavioural indicators
        indicators = [
            record.distress_score is not None,
            record.trajectory_score is not None,
            record.baseline_deviation is not None,
            record.safety_distress is not None,
            record.sleep_disturbance is not None,
            record.fear_intensity is not None,
            record.help_requested is not None,
            record.checkin_consistency is not None,
            record.engagement_drop is not None,
        ]
        missingness_term = sum(1.0 for ind in indicators if ind) / len(indicators)

        # 5. Prediction Certainty [0.0, 1.0] (2 * |P - 0.5|)
        certainty_term = min(1.0, max(0.0, 2.0 * abs(probability - 0.50)))

        confidence = (
            policy.observation_weight * obs_term
            + policy.text_weight * text_term
            + policy.audio_weight * audio_term
            + policy.missingness_weight * missingness_term
            + policy.uncertainty_weight * certainty_term
        )
        return round(max(0.0, min(1.0, confidence)), 4)

    def compute_feature_contributions(
        self,
        record: EscalationInputRecord,
    ) -> List[Dict[str, Any]]:
        """Computes and stores raw feature contribution table for auditing and explainability.

        Each entry:
        {
            "feature": name,
            "value": float,
            "coefficient": float,
            "contribution": float  # w_i * x_i
        }
        """
        x = record.to_feature_vector(self.feature_names)
        contributions: List[Dict[str, Any]] = []

        for j, name in enumerate(self.feature_names):
            val = float(x[j])
            coef = float(self.weights[j])
            contrib = coef * val
            contributions.append({
                "feature": name,
                "value": round(val, 4),
                "coefficient": round(coef, 4),
                "contribution": round(contrib, 4),
            })

        self.last_feature_contributions = contributions
        return contributions

    def get_last_feature_contributions(self) -> List[Dict[str, Any]]:
        """Returns the most recent raw feature contribution table."""
        return list(self.last_feature_contributions)

    def generate_explanation(
        self,
        record: EscalationInputRecord,
        probability: float,
    ) -> Dict[str, Any]:
        """Generates grounded explanation factors directly from model feature contributions.

        Uses the computed feature contribution table.
        Zero psychiatric claims. Zero treatment advice.
        Does NOT reference unavailable modalities.
        """
        contributions = self.compute_feature_contributions(record)

        # Filter positive drivers with contribution > 0.05, excluding missingness indicators
        positive_drivers = sorted(
            [c for c in contributions if c["contribution"] > 0.05 and not c["feature"].endswith("_missing")],
            key=lambda c: c["contribution"],
            reverse=True,
        )

        factors: List[str] = []
        for c in positive_drivers[:4]:
            feat_name = c["feature"]
            if feat_name in ("trajectory_is_rapidly_worsening", "trajectory_is_worsening", "trajectory_score"):
                factors.append("Worsening distress trajectory across recent interactions")
            elif feat_name in ("distress_is_high_or_critical", "distress_score"):
                factors.append("Elevated acute distress state")
            elif feat_name == "baseline_deviation" and record.baseline_deviation is not None:
                factors.append("Elevated distress relative to personal baseline")
            elif feat_name == "help_requested" and record.help_requested:
                factors.append("Direct help-seeking indicator requested")
            elif feat_name == "engagement_drop" and record.engagement_drop:
                factors.append("Declining conversational engagement and check-in adherence")
            elif feat_name == "sleep_disturbance" and record.sleep_disturbance:
                factors.append("Reported sleep disturbance")
            elif feat_name == "fear_intensity" and record.fear_intensity:
                factors.append("Elevated fear intensity indicators")
            elif feat_name == "safety_distress" and record.safety_distress:
                factors.append("Elevated safety distress indicators")

        # Deduplicate while preserving order
        dedup_factors: List[str] = []
        for f in factors:
            if f not in dedup_factors:
                dedup_factors.append(f)

        if not dedup_factors:
            if probability < self.config.threshold_low_moderate:
                dedup_factors.append("Consistent check-in adherence and stable interaction pattern")
            else:
                dedup_factors.append("Multimodal interaction indicators within standard monitoring range")

        trend_str = record.trajectory_label.upper() if record.trajectory_label else "STABLE"
        if trend_str not in Trajectory.__members__:
            trend_str = "STABLE"

        return {
            "factors": dedup_factors,
            "trend": trend_str,
            "baseline_deviation": record.baseline_deviation,
            "model_version": self.model_version,
        }

    def predict_escalation(
        self,
        record: EscalationInputRecord,
        prediction_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Public Inference Interface conforming to AAROH MlInferenceResult contract.

        Supports abstention:
        - If evidence is insufficient (e.g. valid_observation_count < minimum_history or critical data absent),
          does NOT return LOW risk or probability = 0. Produces INSUFFICIENT_DATA or ABSTAINED.

        Returns contract dict:
        {
            "case_id": str,
            "prediction_date": str,
            "escalation_probability": float | None,
            "target_horizon_days": int,
            "confidence": float,
            "risk_level": str | None,
            "explanation": dict,
            "model_version": str,
            "status": str,
            "source": str
        }
        """
        policy = getattr(self, "confidence_policy", None) or getattr(self.config, "confidence_policy", None) or ConfidencePolicyConfig()

        # 1. Prediction date resolution (deterministic injection or current UTC)
        if prediction_date:
            date_str = str(prediction_date)
        else:
            date_str = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

        # 2. Check for Abstention / Insufficient Data
        modalities_present = int(record.text_available) + int(record.audio_available)
        if (
            max(record.history_length, record.valid_observation_count) < policy.minimum_history
            or record.valid_observation_count < policy.minimum_history
            or modalities_present < policy.minimum_modalities
            or (not record.text_available and not record.audio_available and record.distress_score == 0.0)
            or record.distress_score is None
        ):
            status = ProcessingStatus.INSUFFICIENT_DATA.value
            source = ResultSource.INSUFFICIENT_EVIDENCE.value
            explanation_payload = {
                "factors": ["Insufficient multimodal observations to reliably assess escalation risk"],
                "trend": record.trajectory_label.upper() if record.trajectory_label else "STABLE",
                "baseline_deviation": record.baseline_deviation,
                "model_version": self.model_version,
            }
            output = {
                "case_id": record.case_id,
                "prediction_date": date_str,
                "escalation_probability": None,  # NOT 0.0
                "target_horizon_days": self.config.target_horizon_days,
                "confidence": 0.0,
                "risk_level": None,  # NOT LOW
                "explanation": explanation_payload,
                "model_version": self.model_version,
                "status": status,
                "source": source,
                "message": "Abstained due to insufficient evidence.",
            }
            return output

        # 3. Probabilistic Inference
        _, prob = self.predict_proba(record)
        conf = self.compute_confidence(record, prob)
        risk_lvl = self.config.get_risk_level(prob).value

        # Check for low confidence status
        if conf < policy.minimum_confidence:
            status = ProcessingStatus.LOW_CONFIDENCE.value
        else:
            status = ProcessingStatus.SUCCESS.value
        source = ResultSource.ML.value

        # 4. Generate Grounded Explanation
        explanation_dict = self.generate_explanation(record, prob)

        output = {
            "case_id": record.case_id,
            "prediction_date": date_str,
            "escalation_probability": prob,
            "target_horizon_days": self.config.target_horizon_days,
            "confidence": conf,
            "risk_level": risk_lvl,
            "explanation": explanation_dict,
            "model_version": self.model_version,
            "status": status,
            "source": source,
        }

        # 5. Strict Clinical Boundary Validation
        for k in output.keys():
            enforce_escalation_boundary(k)
        if risk_lvl:
            enforce_escalation_boundary(risk_lvl)

        return output

    def save_checkpoint(
        self,
        checkpoint_path: Union[str, Path],
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persists trained weights, intercept, and configuration."""
        out_p = Path(checkpoint_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "model_type": "logistic_regression_escalation_model",
            "model_name": self.model_name,
            "model_version": self.model_version,
            "weights": self.weights,
            "intercept": self.intercept,
            "feature_names": self.feature_names,
            "config": self.config.to_dict(),
            "metrics": metrics or {},
        }
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_checkpoint(self, checkpoint_path: Union[str, Path]) -> Dict[str, Any]:
        """Restores model state from checkpoint."""
        in_p = Path(checkpoint_path)
        if not in_p.exists():
            raise FileNotFoundError(f"Checkpoint not found at {in_p}")

        with open(in_p, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.model_version = data.get("model_version", self.model_version)
        self.weights = data["weights"]
        self.intercept = data["intercept"]
        self.feature_names = data.get("feature_names", self.feature_names)
        self.num_features = len(self.weights)
        self.is_fitted = True

        cfg_dict = data.get("config", {})
        if cfg_dict:
            policy_dict = cfg_dict.get("confidence_policy")
            conf_policy = ConfidencePolicyConfig.from_dict(policy_dict) if policy_dict else ConfidencePolicyConfig()
            self.config = EscalationConfig(
                target_horizon_days=cfg_dict.get("target_horizon_days", DEFAULT_TARGET_HORIZON_DAYS),
                threshold_low_moderate=cfg_dict.get("threshold_low_moderate", 0.40),
                threshold_moderate_high=cfg_dict.get("threshold_moderate_high", 0.75),
                min_confidence_threshold=cfg_dict.get("min_confidence_threshold", 0.25),
                confidence_policy=conf_policy,
                config_version=cfg_dict.get("config_version", "1.0.0"),
            )
            self.confidence_policy = self.config.confidence_policy
        return data.get("metrics", {})

    def export(
        self,
        output_dir: Union[str, Path],
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Exports the 5 standard production artifacts."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Weights
        weights_file = out_dir / "weights"
        state = {
            "weights": self.weights,
            "intercept": self.intercept,
            "feature_names": self.feature_names,
            "num_features": len(self.weights),
        }
        with open(weights_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        # 2. Config
        config_file = out_dir / "config.json"
        config_data = {
            "model_type": "logistic_regression_escalation_model",
            "model_name": self.model_name,
            "model_version": self.model_version,
            "target_horizon_days": self.config.target_horizon_days,
            "threshold_low_moderate": self.config.threshold_low_moderate,
            "threshold_moderate_high": self.config.threshold_moderate_high,
            "min_confidence_threshold": self.config.min_confidence_threshold,
            "confidence_policy": self.confidence_policy.to_dict(),
            "calibration": {
                "method": "logistic_sigmoid",
                "version": "1.0",
            },
            "feature_names": self.feature_names,
            "disclaimer": LABEL_DISCLAIMER,
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        # 3. Metadata
        meta_file = out_dir / "metadata.json"
        meta_data = {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "dataset_version": "3.8.0",
            "feature_schema_version": "1.0",
            "training_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "target_horizon_days": self.config.target_horizon_days,
            "calibration": {
                "method": "logistic_sigmoid",
                "version": "1.0",
            },
            "calibration_method": "logistic_sigmoid",
            "confidence_policy": self.confidence_policy.to_dict(),
            "threshold_configuration": {
                "low": f"< {self.config.threshold_low_moderate}",
                "moderate": f"{self.config.threshold_low_moderate} - {self.config.threshold_moderate_high}",
                "high": f">= {self.config.threshold_moderate_high}",
            },
            "upstream_models": {
                "fusion": "aaroh-fusion-v1",
                "distress": "aaroh-distress-v1",
                "trajectory": "aaroh-trajectory-v1",
            },
            "label_disclaimer": LABEL_DISCLAIMER,
            "smoke_test_disclaimer": SMOKE_TEST_DISCLAIMER,
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta_data, f, indent=2)

        # 4. Metrics
        metrics_file = out_dir / "metrics.json"
        metrics_data = metrics or {}
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)

        # 5. Label Mapping
        label_file = out_dir / "label_mapping.json"
        label_data = {
            "task": "escalation_assessment",
            "risk_levels": ["LOW", "MODERATE", "HIGH"],
            "thresholds": {
                "LOW": [0.0, self.config.threshold_low_moderate],
                "MODERATE": [self.config.threshold_low_moderate, self.config.threshold_moderate_high],
                "HIGH": [self.config.threshold_moderate_high, 1.0],
            },
            "disclaimer": LABEL_DISCLAIMER,
        }
        with open(label_file, "w", encoding="utf-8") as f:
            json.dump(label_data, f, indent=2)

        return {
            "weights": str(weights_file),
            "config": str(config_file),
            "metadata": str(meta_file),
            "metrics": str(metrics_file),
            "label_mapping": str(label_file),
        }
