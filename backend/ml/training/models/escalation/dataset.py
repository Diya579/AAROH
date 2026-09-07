"""Escalation Assessment Dataset and Input Representation (Slice 3.8 Revision).

Defines:
- EscalationConfig: Configurable target horizon and risk level thresholds.
- EscalationInputRecord: Consumes outputs from previous slices (Slices 3.1, 3.5, 3.6, 3.7)
  without recomputing them, while strictly preserving None != 0.
- Evidence Quality tracking: text_available, audio_available, history_length, valid observations.
- Temporal Leakage Protection: Filtering cutoff timestamps.
- Zero-leakage case-level splitters.
- Supervised synthetic demonstration generator.

Disclaimers:
- Synthetic demonstration labels are used solely for engineering verification and architecture validation.
  They are NOT clinical ground truth.
- This model produces an operational assessment signal only, NOT a clinical diagnosis.
"""

from __future__ import annotations

import datetime
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from backend.ml.contract import (
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
)

LABEL_DISCLAIMER = (
    "SYNTHETIC DEMONSTRATION LABELS - NOT CLINICAL GROUND TRUTH. "
    "Supervised solely for engineering verification and architecture validation."
)
SMOKE_TEST_DISCLAIMER = (
    "Smoke-test metrics are intended only to verify that the training, "
    "checkpointing, inference, and evaluation pipelines function correctly. "
    "They are NOT indicators of real-world model performance."
)

DEFAULT_TARGET_HORIZON_DAYS = 7
DEFAULT_THRESHOLD_LOW_MODERATE = 0.40
DEFAULT_THRESHOLD_MODERATE_HIGH = 0.75
DEFAULT_MIN_CONFIDENCE_THRESHOLD = 0.25


@dataclass
class ConfidencePolicyConfig:
    """Versioned policy configuration for computing epistemic confidence."""

    version: str = "1.0"
    observation_weight: float = 0.35
    text_weight: float = 0.20
    audio_weight: float = 0.15
    missingness_weight: float = 0.15
    uncertainty_weight: float = 0.15
    minimum_history: int = 2
    minimum_modalities: int = 1
    minimum_confidence: float = 0.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "observation_weight": self.observation_weight,
            "text_weight": self.text_weight,
            "audio_weight": self.audio_weight,
            "missingness_weight": self.missingness_weight,
            "uncertainty_weight": self.uncertainty_weight,
            "minimum_history": self.minimum_history,
            "minimum_modalities": self.minimum_modalities,
            "minimum_confidence": self.minimum_confidence,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> ConfidencePolicyConfig:
        if not data:
            return cls()
        return cls(
            version=data.get("version", "1.0"),
            observation_weight=float(data.get("observation_weight", 0.35)),
            text_weight=float(data.get("text_weight", 0.20)),
            audio_weight=float(data.get("audio_weight", 0.15)),
            missingness_weight=float(data.get("missingness_weight", 0.15)),
            uncertainty_weight=float(data.get("uncertainty_weight", 0.15)),
            minimum_history=int(data.get("minimum_history", 2)),
            minimum_modalities=int(data.get("minimum_modalities", 1)),
            minimum_confidence=float(data.get("minimum_confidence", 0.25)),
        )


@dataclass
class EscalationConfig:
    """Configurable operational parameters for Escalation Assessment Model."""

    target_horizon_days: int = DEFAULT_TARGET_HORIZON_DAYS
    threshold_low_moderate: float = DEFAULT_THRESHOLD_LOW_MODERATE
    threshold_moderate_high: float = DEFAULT_THRESHOLD_MODERATE_HIGH
    min_confidence_threshold: float = DEFAULT_MIN_CONFIDENCE_THRESHOLD
    confidence_policy: ConfidencePolicyConfig = field(default_factory=ConfidencePolicyConfig)
    config_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if isinstance(self.confidence_policy, dict):
            self.confidence_policy = ConfidencePolicyConfig.from_dict(self.confidence_policy)
        if self.target_horizon_days <= 0:
            raise ValueError(f"target_horizon_days must be > 0, got {self.target_horizon_days}")
        if not (0.0 < self.threshold_low_moderate < self.threshold_moderate_high < 1.0):
            raise ValueError(
                f"Invalid thresholds: 0.0 < {self.threshold_low_moderate} < {self.threshold_moderate_high} < 1.0 required"
            )

    def get_risk_level(self, probability: float) -> RiskLevel:
        """Maps continuous escalation probability to RiskLevel enum.

        Mapping:
        - LOW: probability < threshold_low_moderate (0.40)
        - MODERATE: threshold_low_moderate <= probability < threshold_moderate_high (0.75)
        - HIGH: probability >= threshold_moderate_high (0.75)
        No CRITICAL level is permitted.
        """
        if probability < self.threshold_low_moderate:
            return RiskLevel.LOW
        if probability < self.threshold_moderate_high:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_horizon_days": self.target_horizon_days,
            "threshold_low_moderate": self.threshold_low_moderate,
            "threshold_moderate_high": self.threshold_moderate_high,
            "min_confidence_threshold": self.min_confidence_threshold,
            "confidence_policy": self.confidence_policy.to_dict(),
            "config_version": self.config_version,
        }


# Canonical feature names used for interpretable Logistic Regression
ESCALATION_FEATURE_NAMES = [
    "distress_score",
    "distress_is_high_or_critical",
    "distress_is_moderate",
    "baseline_deviation",
    "baseline_deviation_missing",
    "trajectory_score",
    "trajectory_is_worsening",
    "trajectory_is_rapidly_worsening",
    "trajectory_prob_worsening_combined",
    "safety_distress",
    "safety_distress_missing",
    "sleep_disturbance",
    "sleep_disturbance_missing",
    "fear_intensity",
    "fear_intensity_missing",
    "help_requested",
    "help_requested_missing",
    "checkin_consistency",
    "checkin_consistency_missing",
    "engagement_drop",
    "engagement_drop_missing",
    "text_available",
    "audio_available",
    "history_length_norm",
    "valid_observation_count_norm",
    "distress_emb_norm",
    "trajectory_emb_norm",
    "fused_emb_norm",
]


@dataclass
class EscalationInputRecord:
    """Unified input container consuming upstream multimodal and longitudinal representations.

    Preserves None != 0 invariant across all clinical and behavioural features.
    """

    case_id: str
    interaction_id: str
    timestamp: str  # ISO-8601 UTC

    # 1. Current Distress (Slice 3.6)
    distress_score: float
    distress_level: str
    distress_embedding: List[float] = field(default_factory=list)
    baseline_deviation: Optional[float] = None

    # 2. Longitudinal Trajectory (Slice 3.7)
    trajectory_score: float = 0.0
    trajectory_label: str = "STABLE"
    trajectory_probabilities: Dict[str, float] = field(
        default_factory=lambda: {"STABLE": 1.0, "IMPROVING": 0.0, "WORSENING": 0.0, "RAPIDLY_WORSENING": 0.0}
    )
    trajectory_embedding: List[float] = field(default_factory=list)

    # 3. Multimodal Fusion (Slice 3.5)
    fused_embedding: List[float] = field(default_factory=list)
    modality_weights: Dict[str, float] = field(
        default_factory=lambda: {"tabular": 0.34, "text": 0.33, "audio": 0.33}
    )

    # 4. Behavioural Features (Slice 3.1) — None != 0 preserved
    safety_distress: Optional[float] = None
    sleep_disturbance: Optional[float] = None
    fear_intensity: Optional[float] = None
    low_social_support: Optional[float] = None
    help_requested: Optional[float] = None
    composite_distress: Optional[float] = None

    # 5. Engagement Features (Slice 3.1) — None != 0 preserved
    checkin_consistency: Optional[float] = None
    missed_checkin_streak: Optional[float] = None
    response_delay: Optional[float] = None
    engagement_score: Optional[float] = None
    engagement_drop: Optional[float] = None

    # 6. Evidence Quality
    text_available: bool = True
    audio_available: bool = True
    history_length: int = 1
    valid_observation_count: int = 5

    # 7. Supervised Target Label for Verification/Training
    synthetic_escalation_target: Optional[int] = None

    @classmethod
    def from_upstream(
        cls,
        case_id: str,
        interaction_id: str,
        timestamp: str,
        distress_output: Dict[str, Any],
        trajectory_output: Dict[str, Any],
        fusion_output: Optional[Dict[str, Any]] = None,
        behavioural_features: Optional[Dict[str, Any]] = None,
        engagement_features: Optional[Dict[str, Any]] = None,
        text_available: bool = True,
        audio_available: bool = True,
        history_length: int = 1,
        synthetic_escalation_target: Optional[int] = None,
    ) -> EscalationInputRecord:
        """Factory constructor integrating upstream Slice 3.1, 3.5, 3.6, and 3.7 outputs."""
        fusion_dict = fusion_output or {}
        behav = behavioural_features or {}
        eng = engagement_features or {}

        d_score = float(distress_output.get("distress_score", 0.0))
        d_lvl = str(distress_output.get("distress_level", "LOW"))
        d_emb = distress_output.get("distress_embedding", [0.0] * 128)
        base_dev = distress_output.get("baseline_deviation")

        t_score = float(trajectory_output.get("trajectory_score", 0.0))
        t_lvl = str(trajectory_output.get("trajectory_label", "STABLE"))
        t_probs = trajectory_output.get(
            "trajectory_probabilities",
            {"STABLE": 1.0, "IMPROVING": 0.0, "WORSENING": 0.0, "RAPIDLY_WORSENING": 0.0},
        )
        t_emb = trajectory_output.get("trajectory_embedding", [0.0] * 128)

        f_emb = fusion_dict.get("fused_embedding", [0.0] * 256)
        mod_weights = fusion_dict.get("modality_weights", {"tabular": 0.34, "text": 0.33, "audio": 0.33})

        # Count non-None valid observations
        all_obs = [
            base_dev,
            behav.get("safety_distress"),
            behav.get("sleep_disturbance"),
            behav.get("fear_intensity"),
            behav.get("help_requested"),
            eng.get("checkin_consistency"),
            eng.get("engagement_drop"),
        ]
        valid_count = sum(1 for o in all_obs if o is not None)
        if text_available:
            valid_count += 1
        if audio_available:
            valid_count += 1

        return cls(
            case_id=case_id,
            interaction_id=interaction_id,
            timestamp=timestamp,
            distress_score=d_score,
            distress_level=d_lvl,
            distress_embedding=d_emb,
            baseline_deviation=base_dev,
            trajectory_score=t_score,
            trajectory_label=t_lvl,
            trajectory_probabilities=t_probs,
            trajectory_embedding=t_emb,
            fused_embedding=f_emb,
            modality_weights=mod_weights,
            safety_distress=behav.get("safety_distress"),
            sleep_disturbance=behav.get("sleep_disturbance"),
            fear_intensity=behav.get("fear_intensity"),
            low_social_support=behav.get("low_social_support"),
            help_requested=behav.get("help_requested"),
            composite_distress=behav.get("composite_distress"),
            checkin_consistency=eng.get("checkin_consistency"),
            missed_checkin_streak=eng.get("missed_checkin_streak"),
            response_delay=eng.get("response_delay"),
            engagement_score=eng.get("engagement_score"),
            engagement_drop=eng.get("engagement_drop"),
            text_available=text_available,
            audio_available=audio_available,
            history_length=history_length,
            valid_observation_count=valid_count,
            synthetic_escalation_target=synthetic_escalation_target,
        )

    def to_feature_dict(self) -> Dict[str, float]:
        """Extracts interpretable numerical features strictly preserving None != 0."""
        d_lvl = self.distress_level.upper()
        t_lbl = self.trajectory_label.upper()

        prob_worsening = float(self.trajectory_probabilities.get("WORSENING", 0.0))
        prob_rapidly = float(self.trajectory_probabilities.get("RAPIDLY_WORSENING", 0.0))

        # Vector norms
        d_norm = math.sqrt(sum(v * v for v in self.distress_embedding)) if self.distress_embedding else 1.0
        t_norm = math.sqrt(sum(v * v for v in self.trajectory_embedding)) if self.trajectory_embedding else 1.0
        f_norm = math.sqrt(sum(v * v for v in self.fused_embedding)) if self.fused_embedding else 1.0

        features: Dict[str, float] = {
            # Distress
            "distress_score": float(self.distress_score),
            "distress_is_high_or_critical": 1.0 if d_lvl in ("HIGH", "CRITICAL") else 0.0,
            "distress_is_moderate": 1.0 if d_lvl == "MODERATE" else 0.0,
            "baseline_deviation": float(self.baseline_deviation) if self.baseline_deviation is not None else 0.0,
            "baseline_deviation_missing": 1.0 if self.baseline_deviation is None else 0.0,
            # Trajectory
            "trajectory_score": float(self.trajectory_score),
            "trajectory_is_worsening": 1.0 if t_lbl in ("WORSENING", "RAPIDLY_WORSENING") else 0.0,
            "trajectory_is_rapidly_worsening": 1.0 if t_lbl == "RAPIDLY_WORSENING" else 0.0,
            "trajectory_prob_worsening_combined": min(1.0, prob_worsening + prob_rapidly),
            # Behaviour (None != 0 preserved via missing indicator)
            "safety_distress": float(self.safety_distress) if self.safety_distress is not None else 0.0,
            "safety_distress_missing": 1.0 if self.safety_distress is None else 0.0,
            "sleep_disturbance": float(self.sleep_disturbance) if self.sleep_disturbance is not None else 0.0,
            "sleep_disturbance_missing": 1.0 if self.sleep_disturbance is None else 0.0,
            "fear_intensity": float(self.fear_intensity) if self.fear_intensity is not None else 0.0,
            "fear_intensity_missing": 1.0 if self.fear_intensity is None else 0.0,
            "help_requested": float(self.help_requested) if self.help_requested is not None else 0.0,
            "help_requested_missing": 1.0 if self.help_requested is None else 0.0,
            # Engagement (None != 0 preserved via missing indicator)
            "checkin_consistency": float(self.checkin_consistency) if self.checkin_consistency is not None else 0.0,
            "checkin_consistency_missing": 1.0 if self.checkin_consistency is None else 0.0,
            "engagement_drop": float(self.engagement_drop) if self.engagement_drop is not None else 0.0,
            "engagement_drop_missing": 1.0 if self.engagement_drop is None else 0.0,
            # Evidence Quality
            "text_available": 1.0 if self.text_available else 0.0,
            "audio_available": 1.0 if self.audio_available else 0.0,
            "history_length_norm": min(1.0, self.history_length / 10.0),
            "valid_observation_count_norm": min(1.0, self.valid_observation_count / 10.0),
            # Representation Norms
            "distress_emb_norm": d_norm,
            "trajectory_emb_norm": t_norm,
            "fused_emb_norm": f_norm,
        }
        return features

    def to_feature_vector(self, feature_names: Sequence[str] = ESCALATION_FEATURE_NAMES) -> List[float]:
        """Returns ordered feature vector matching feature_names."""
        f_dict = self.to_feature_dict()
        return [f_dict.get(name, 0.0) for name in feature_names]


def filter_interactions_by_cutoff(
    records: List[EscalationInputRecord],
    cutoff_timestamp: str,
) -> List[EscalationInputRecord]:
    """Strict temporal leakage protection: filters out interactions occurring after cutoff.

    Ensures that interactions occurring at T + delta do not leak into evaluation at time T.
    """
    valid_records = [r for r in records if r.timestamp <= cutoff_timestamp]
    return sorted(valid_records, key=lambda r: r.timestamp)


def determine_synthetic_escalation_target(
    distress_score: float,
    distress_level: str,
    trajectory_score: float,
    trajectory_label: str,
    baseline_deviation: Optional[float] = None,
    help_requested: Optional[float] = None,
    engagement_drop: Optional[float] = None,
) -> int:
    """Supervised synthetic label assignment for engineering verification.

    1: Escalation within target horizon.
    0: No escalation within target horizon.
    """
    risk_score = 0.0

    # Distress contributions
    if distress_score >= 0.70 or distress_level.upper() in ("HIGH", "CRITICAL"):
        risk_score += 0.45
    elif distress_score >= 0.40 or distress_level.upper() == "MODERATE":
        risk_score += 0.20

    if baseline_deviation is not None and baseline_deviation >= 0.25:
        risk_score += 0.20

    # Trajectory contributions
    t_lbl = trajectory_label.upper()
    if t_lbl == "RAPIDLY_WORSENING" or trajectory_score >= 0.60:
        risk_score += 0.40
    elif t_lbl == "WORSENING" or trajectory_score >= 0.25:
        risk_score += 0.25
    elif t_lbl == "IMPROVING" or trajectory_score <= -0.25:
        risk_score -= 0.25

    # Behavioural & engagement
    if help_requested and help_requested > 0.5:
        risk_score += 0.30
    if engagement_drop and engagement_drop >= 0.25:
        risk_score += 0.15

    return 1 if risk_score >= 0.50 else 0


def build_synthetic_escalation_records(
    case_count: int = 40,
    seed: int = 42,
) -> List[EscalationInputRecord]:
    """Generates synthetic demonstration records across low, moderate, and high escalation patterns."""
    rng = random.Random(seed)
    records: List[EscalationInputRecord] = []

    for case_num in range(1, case_count + 1):
        case_id = f"CASE-{case_num:03d}"
        pattern = case_num % 3  # 0: low, 1: moderate, 2: high

        base_date = datetime.datetime(2026, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        ts = (base_date + datetime.timedelta(days=case_num)).isoformat()

        if pattern == 0:  # Low risk
            d_score = rng.uniform(0.05, 0.32)
            d_lvl = "LOW"
            base_dev = rng.uniform(0.0, 0.10) if rng.random() > 0.2 else None
            t_lbl = rng.choice(["STABLE", "IMPROVING"])
            t_score = -0.40 if t_lbl == "IMPROVING" else 0.05
            help_req = 0.0
            eng_drop = 0.0
            checkin_cons = rng.uniform(0.80, 1.0)
            text_avail = True
            audio_avail = rng.random() > 0.3
            hist_len = rng.randint(3, 8)
        elif pattern == 1:  # Moderate risk
            d_score = rng.uniform(0.38, 0.62)
            d_lvl = "MODERATE"
            base_dev = rng.uniform(0.12, 0.28) if rng.random() > 0.2 else None
            t_lbl = rng.choice(["STABLE", "WORSENING"])
            t_score = 0.35 if t_lbl == "WORSENING" else 0.10
            help_req = 0.0 if rng.random() > 0.2 else 1.0
            eng_drop = rng.uniform(0.10, 0.30) if rng.random() > 0.3 else None
            checkin_cons = rng.uniform(0.50, 0.80)
            text_avail = True
            audio_avail = rng.random() > 0.4
            hist_len = rng.randint(2, 6)
        else:  # High risk
            d_score = rng.uniform(0.68, 0.94)
            d_lvl = "HIGH" if d_score < 0.82 else "CRITICAL"
            base_dev = rng.uniform(0.30, 0.60) if rng.random() > 0.15 else None
            t_lbl = rng.choice(["WORSENING", "RAPIDLY_WORSENING"])
            t_score = 0.80 if t_lbl == "RAPIDLY_WORSENING" else 0.45
            help_req = 1.0 if rng.random() > 0.3 else 0.0
            eng_drop = rng.uniform(0.35, 0.70) if rng.random() > 0.2 else None
            checkin_cons = rng.uniform(0.20, 0.50)
            text_avail = True
            audio_avail = rng.random() > 0.5
            hist_len = rng.randint(1, 10)

        t_probs = {lbl: 0.05 for lbl in ("STABLE", "IMPROVING", "WORSENING", "RAPIDLY_WORSENING")}
        t_probs[t_lbl] = 0.85

        target = determine_synthetic_escalation_target(
            distress_score=d_score,
            distress_level=d_lvl,
            trajectory_score=t_score,
            trajectory_label=t_lbl,
            baseline_deviation=base_dev,
            help_requested=help_req,
            engagement_drop=eng_drop,
        )

        rec = EscalationInputRecord(
            case_id=case_id,
            interaction_id=f"{case_id}-INT-01",
            timestamp=ts,
            distress_score=d_score,
            distress_level=d_lvl,
            distress_embedding=[rng.gauss(0.0, 0.1) for _ in range(128)],
            baseline_deviation=base_dev,
            trajectory_score=t_score,
            trajectory_label=t_lbl,
            trajectory_probabilities=t_probs,
            trajectory_embedding=[rng.gauss(0.0, 0.1) for _ in range(128)],
            fused_embedding=[rng.gauss(0.0, 0.1) for _ in range(256)],
            modality_weights={"tabular": 0.40, "text": 0.35, "audio": 0.25},
            safety_distress=rng.uniform(0.1, 0.8) if rng.random() > 0.25 else None,
            sleep_disturbance=rng.uniform(0.1, 0.9) if rng.random() > 0.25 else None,
            fear_intensity=rng.uniform(0.1, 0.85) if rng.random() > 0.25 else None,
            help_requested=help_req,
            checkin_consistency=checkin_cons,
            engagement_drop=eng_drop,
            text_available=text_avail,
            audio_available=audio_avail,
            history_length=hist_len,
            valid_observation_count=rng.randint(4, 9),
            synthetic_escalation_target=target,
        )
        records.append(rec)

    return records


def split_escalation_records_by_case(
    records: List[EscalationInputRecord],
    val_ratio: float = 0.25,
    seed: int = 42,
) -> Tuple[List[EscalationInputRecord], List[EscalationInputRecord]]:
    """Splits records into train and validation sets strictly by case_id (zero leakage)."""
    case_ids = sorted(list(set(r.case_id for r in records)))
    rng = random.Random(seed)
    shuffled_cases = list(case_ids)
    rng.shuffle(shuffled_cases)

    val_count = max(1, int(len(shuffled_cases) * val_ratio))
    val_cases = set(shuffled_cases[:val_count])
    train_cases = set(shuffled_cases[val_count:])

    train_recs = [r for r in records if r.case_id in train_cases]
    val_recs = [r for r in records if r.case_id in val_cases]

    validate_no_case_leakage(train_recs, val_recs)
    return train_recs, val_recs


def validate_no_case_leakage(
    train_records: List[EscalationInputRecord],
    val_records: List[EscalationInputRecord],
) -> None:
    """Raises ValueError if any case_id appears in both splits."""
    train_cases = set(r.case_id for r in train_records)
    val_cases = set(r.case_id for r in val_records)
    overlap = train_cases.intersection(val_cases)
    if overlap:
        raise ValueError(f"CASE LEAKAGE DETECTED: Cases in both train and val: {sorted(list(overlap))}")
