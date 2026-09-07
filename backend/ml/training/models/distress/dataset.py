"""Dynamic Distress Dataset and Input Containers (Slice 3.6).

Defines:
- DistressInputRecord: Dataclass encapsulating Slice 3.5 outputs (fused_embedding, modality_weights,
  reconstructed_tabular) alongside Slice 3.1 behavioural and engagement feature slices.
- DistressDataset: Dataloader and batch generator supporting missing feature masking and deterministic splits.
- Synthetic demonstration label generation and case-level splitting with zero data leakage.

Strict Invariants:
- Preserves None != 0 invariant via explicit missingness indicator masks.
- Strictly references SYNTHETIC DEMONSTRATION LABELS ONLY (NOT CLINICAL GROUND TRUTH).
- Clinical boundary: Does NOT consume future interactions, longitudinal trajectories, or previous distress states.
"""

from __future__ import annotations

import json
import math
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from backend.ml.features.registry import (
    FEATURE_NAME_TO_INDEX,
    FEATURE_REGISTRY,
    TOTAL_FEATURES_COUNT,
)
from backend.ml.training.models.fusion.dataset import (
    MultimodalInputRecord,
    build_synthetic_multimodal_records,
)

# Canonical notice for all training and evaluation labels in Slice 3.6
LABEL_DISCLAIMER = "SYNTHETIC DEMONSTRATION LABELS - NOT CLINICAL GROUND TRUTH"

# Feature index ranges from Slice 3.1 registry
# Behavioural: indices 18 to 25 (8 features)
BEHAVIOURAL_START_IDX = 18
BEHAVIOURAL_END_IDX = 26
BEHAVIOURAL_COUNT = 8

# Engagement: indices 26 to 38 (13 features)
ENGAGEMENT_START_IDX = 26
ENGAGEMENT_END_IDX = 39
ENGAGEMENT_COUNT = 13

FUSED_EMBEDDING_DIM = 256
MODALITY_WEIGHTS_DIM = 3
# 256 (fused_emb) + 16 (8 values + 8 masks) + 26 (13 values + 13 masks) + 3 (modality weights) = 301
DISTRESS_INPUT_DIM = (
    FUSED_EMBEDDING_DIM
    + (BEHAVIOURAL_COUNT * 2)
    + (ENGAGEMENT_COUNT * 2)
    + MODALITY_WEIGHTS_DIM
)


@dataclass
class DistressInputRecord:
    """Encapsulates current multimodal fusion representations and interaction features for distress estimation."""

    case_id: str
    interaction_date: str

    # 1. Slice 3.5 Fusion representations (current interaction only)
    fused_embedding: Sequence[float]  # 256-dim unit vector
    modality_weights: Dict[str, float] = field(
        default_factory=lambda: {"tabular": 0.3333, "text": 0.3333, "audio": 0.3334}
    )
    reconstructed_tabular: Optional[Sequence[Optional[float]]] = None

    # 2. Modality slices from current interaction (None != 0 preserved)
    behavioural_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None
    engagement_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None

    # 3. Synthetic demonstration supervision (training/validation only; NOT CLINICAL GROUND TRUTH)
    synthetic_distress_score: Optional[float] = None
    label_disclaimer: str = LABEL_DISCLAIMER

    # 4. Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.fused_embedding) != FUSED_EMBEDDING_DIM:
            raise ValueError(
                f"fused_embedding dimension must be {FUSED_EMBEDDING_DIM}, got {len(self.fused_embedding)}"
            )
        if self.synthetic_distress_score is not None:
            if not (0.0 <= self.synthetic_distress_score <= 1.0):
                raise ValueError(
                    f"synthetic_distress_score must be in [0.0, 1.0], got {self.synthetic_distress_score}"
                )

    def to_feature_vector(self) -> List[float]:
        """Flattens the record into a 301-dimensional numerical vector.

        Components:
        1. Fused embedding: 256 dims
        2. Behavioural features: 8 values + 8 missingness indicator masks = 16 dims
        3. Engagement features: 13 values + 13 missingness indicator masks = 26 dims
        4. Modality weights: 3 dims (tabular, text, audio)
        """
        vec: List[float] = []

        # 1. Fused embedding (256)
        vec.extend(float(x) for x in self.fused_embedding)

        # 2. Behavioural features (8 values + 8 masks)
        b_vals, b_masks = self._extract_feature_slice(
            self.behavioural_features, BEHAVIOURAL_COUNT, BEHAVIOURAL_START_IDX
        )
        vec.extend(b_vals)
        vec.extend(b_masks)

        # 3. Engagement features (13 values + 13 masks)
        e_vals, e_masks = self._extract_feature_slice(
            self.engagement_features, ENGAGEMENT_COUNT, ENGAGEMENT_START_IDX
        )
        vec.extend(e_vals)
        vec.extend(e_masks)

        # 4. Modality weights (3)
        w_tab = float(self.modality_weights.get("tabular", 0.3333))
        w_text = float(self.modality_weights.get("text", 0.3333))
        w_audio = float(self.modality_weights.get("audio", 0.3334))
        vec.extend([w_tab, w_text, w_audio])

        if len(vec) != DISTRESS_INPUT_DIM:
            raise ValueError(
                f"Assembled feature vector dimension mismatch: expected {DISTRESS_INPUT_DIM}, got {len(vec)}"
            )
        return vec

    @staticmethod
    def _extract_feature_slice(
        features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]],
        expected_count: int,
        registry_start_idx: int,
    ) -> Tuple[List[float], List[float]]:
        """Extracts numerical values and missingness masks, rigorously enforcing None != 0."""
        values: List[float] = [0.0] * expected_count
        masks: List[float] = [0.0] * expected_count

        if features is None:
            return values, masks

        if isinstance(features, dict):
            # Extract by feature name from registry slice
            for offset in range(expected_count):
                reg_def = FEATURE_REGISTRY[registry_start_idx + offset]
                val = features.get(reg_def.name)
                if val is not None:
                    values[offset] = float(val)
                    masks[offset] = 1.0
        else:
            # Extract by sequential position
            for offset in range(min(len(features), expected_count)):
                val = features[offset]
                if val is not None:
                    values[offset] = float(val)
                    masks[offset] = 1.0

        return values, masks

    @classmethod
    def from_multimodal_record(
        cls,
        record: MultimodalInputRecord,
        fusion_model: Optional[Any] = None,
        synthetic_score: Optional[float] = None,
    ) -> DistressInputRecord:
        """Factory constructor converting a MultimodalInputRecord into a DistressInputRecord."""
        # 1. Obtain fused representation from Slice 3.5 model or metadata
        if fusion_model is not None:
            fuse_res = fusion_model.fuse(record)
            fused_emb = fuse_res["fused_embedding"]
            mod_weights = fuse_res["modality_weights"]
            recon_tab = fuse_res.get("reconstructed_tabular")
        elif "fused_embedding" in record.metadata:
            fused_emb = record.metadata["fused_embedding"]
            mod_weights = record.metadata.get(
                "modality_weights", {"tabular": 0.3333, "text": 0.3333, "audio": 0.3334}
            )
            recon_tab = record.metadata.get("reconstructed_tabular")
        else:
            # Fallback deterministic pseudo-embedding if fusion model not yet run
            rng = random.Random(hash(record.case_id + record.interaction_date) & 0xFFFFFFFF)
            raw = [rng.gauss(0.0, 1.0) for _ in range(FUSED_EMBEDDING_DIM)]
            norm = math.sqrt(sum(x * x for x in raw)) or 1.0
            fused_emb = [x / norm for x in raw]
            mod_weights = {"tabular": 0.4, "text": 0.4, "audio": 0.2}
            recon_tab = None

        # 2. Extract behavioural and engagement feature slices from tabular features
        behavioural: Optional[List[Optional[float]]] = None
        engagement: Optional[List[Optional[float]]] = None
        if record.tabular_features is not None:
            if len(record.tabular_features) >= BEHAVIOURAL_END_IDX:
                behavioural = list(record.tabular_features[BEHAVIOURAL_START_IDX:BEHAVIOURAL_END_IDX])
            if len(record.tabular_features) >= ENGAGEMENT_END_IDX:
                engagement = list(record.tabular_features[ENGAGEMENT_START_IDX:ENGAGEMENT_END_IDX])

        # 3. Assign or compute synthetic demonstration label
        if synthetic_score is None:
            synthetic_score = compute_synthetic_distress_score(record)

        return cls(
            case_id=record.case_id,
            interaction_date=record.interaction_date,
            fused_embedding=fused_emb,
            modality_weights=mod_weights,
            reconstructed_tabular=recon_tab,
            behavioural_features=behavioural,
            engagement_features=engagement,
            synthetic_distress_score=synthetic_score,
            metadata=dict(record.metadata),
        )


def compute_synthetic_distress_score(
    record: Union[MultimodalInputRecord, DistressInputRecord],
    seed: int = 42,
) -> float:
    """Computes a deterministic demonstration distress score for research and testing purposes ONLY.

    CRITICAL NOTICE:
    SYNTHETIC DEMONSTRATION LABELS - NOT CLINICAL GROUND TRUTH.
    Public corpora do not contain AAROH distress labels; this synthetic score provides
    demonstration supervision for testing pipeline mechanics and zero-leakage training loops.

    Formula combines:
    - Safety distress & fear intensity (from behavioural slice)
    - Stress probability (from text slice)
    - Audio emotion signal (from audio slice)
    - Engagement drop / missed checkin (from engagement slice)
    """
    score = 0.20  # baseline prior

    # 1. Behavioural contribution
    if isinstance(record, MultimodalInputRecord) and record.tabular_features is not None:
        tf = record.tabular_features
        # 18: behavioural_safety_distress
        if len(tf) > 18 and tf[18] is not None:
            score += 0.25 * float(tf[18])
        # 20: behavioural_fear_intensity
        if len(tf) > 20 and tf[20] is not None:
            score += 0.20 * float(tf[20])
        # 19: behavioural_sleep_disturbance
        if len(tf) > 19 and tf[19] is not None:
            score += 0.10 * float(tf[19])
        # 33: engagement_engagement_drop
        if len(tf) > 33 and tf[33] is not None:
            score += 0.15 * float(tf[33])
    elif isinstance(record, DistressInputRecord) and record.behavioural_features is not None:
        bf = record.behavioural_features
        if isinstance(bf, sequence_type := (list, tuple)):
            if len(bf) > 0 and bf[0] is not None:
                score += 0.25 * float(bf[0])
            if len(bf) > 2 and bf[2] is not None:
                score += 0.20 * float(bf[2])
            if len(bf) > 1 and bf[1] is not None:
                score += 0.10 * float(bf[1])

    # 2. Text stress contribution
    if isinstance(record, MultimodalInputRecord) and record.stress_probability is not None:
        score += 0.15 * float(record.stress_probability)

    # 3. Audio emotion contribution
    if isinstance(record, MultimodalInputRecord) and record.audio_emotion_probabilities is not None:
        a_probs = record.audio_emotion_probabilities
        fear = a_probs.get("fearful", 0.0)
        sad = a_probs.get("sad", 0.0)
        angry = a_probs.get("angry", 0.0)
        score += 0.10 * (fear + sad + angry)

    # Deterministic minor perturbation based on case_id to ensure continuous spread
    case_hash = hash(record.case_id + record.interaction_date) & 0xFFFF
    perturbation = ((case_hash % 100) / 100.0 - 0.5) * 0.08
    score += perturbation

    # Clamp strictly to [0.0, 1.0]
    return max(0.0, min(1.0, round(score, 4)))


def build_synthetic_distress_records(
    count: int = 60,
    seed: int = 42,
    fusion_model: Optional[Any] = None,
) -> List[DistressInputRecord]:
    """Generates synthetic demonstration distress records across multiple beneficiary cases.

    CRITICAL NOTICE:
    SYNTHETIC DEMONSTRATION LABELS - NOT CLINICAL GROUND TRUTH.
    """
    multimodal_records = build_synthetic_multimodal_records(count=count, seed=seed)
    distress_records: List[DistressInputRecord] = []

    for rec in multimodal_records:
        d_rec = DistressInputRecord.from_multimodal_record(
            rec,
            fusion_model=fusion_model,
        )
        distress_records.append(d_rec)

    return distress_records


def validate_no_case_leakage(
    train_records: Sequence[DistressInputRecord],
    val_records: Sequence[DistressInputRecord],
) -> None:
    """Validates that no case ID appears in both train and validation splits.

    Raises ValueError if any case_id is found in both splits.
    """
    train_cases = set(r.case_id for r in train_records)
    val_cases = set(r.case_id for r in val_records)
    overlap = train_cases.intersection(val_cases)
    if overlap:
        raise ValueError(
            f"FATAL CASE LEAKAGE DETECTED: Cases {overlap} present in both train and val splits."
        )


def split_distress_records_by_case(
    records: Sequence[DistressInputRecord],
    val_ratio: float = 0.25,
    seed: int = 42,
) -> Tuple[List[DistressInputRecord], List[DistressInputRecord]]:
    """Splits distress records by case_id to strictly prevent longitudinal data leakage.

    Raises ValueError if any case_id is found in both train and validation splits.
    """
    case_map: Dict[str, List[DistressInputRecord]] = {}
    for r in records:
        case_map.setdefault(r.case_id, []).append(r)

    unique_cases = sorted(list(case_map.keys()))
    rng = random.Random(seed)
    shuffled_cases = list(unique_cases)
    rng.shuffle(shuffled_cases)

    val_count = max(1, int(round(len(shuffled_cases) * val_ratio)))
    val_cases = set(shuffled_cases[:val_count])
    train_cases = set(shuffled_cases[val_count:])

    train_records: List[DistressInputRecord] = []
    val_records: List[DistressInputRecord] = []

    for cid in train_cases:
        train_records.extend(case_map[cid])
    for cid in val_cases:
        val_records.extend(case_map[cid])

    validate_no_case_leakage(train_records, val_records)

    return train_records, val_records


class DistressDataset:
    """In-memory dataset container for Dynamic Distress model training and evaluation."""

    def __init__(self, records: Sequence[DistressInputRecord]) -> None:
        self.records = list(records)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> DistressInputRecord:
        return self.records[idx]

    def iterate_batches(
        self,
        batch_size: int = 16,
        shuffle: bool = True,
        seed: int = 42,
    ) -> Iterator[Dict[str, Any]]:
        """Yields mini-batches formatted for training and evaluation."""
        indices = list(range(len(self.records)))
        if shuffle:
            rng = random.Random(seed)
            rng.shuffle(indices)

        for start in range(0, len(indices), batch_size):
            batch_idx = indices[start : start + batch_size]
            batch_records = [self.records[i] for i in batch_idx]

            inputs: List[List[float]] = []
            targets: List[float] = []
            case_ids: List[str] = []

            for r in batch_records:
                inputs.append(r.to_feature_vector())
                targets.append(
                    r.synthetic_distress_score if r.synthetic_distress_score is not None else 0.5
                )
                case_ids.append(r.case_id)

            yield {
                "inputs": inputs,
                "targets": targets,
                "case_ids": case_ids,
                "batch_size": len(batch_records),
            }
