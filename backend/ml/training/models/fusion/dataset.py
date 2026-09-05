"""Multimodal Feature Fusion Dataset and Data Containers (Slice 3.5).

Defines:
- MultimodalInputRecord: Dataclass encapsulating tabular features (MLInput), text representations, and audio representations.
- MultimodalFusionDataset: Lazy and in-memory multimodal dataset builder supporting missing modality masking and deterministic splits.
- Utilities to generate paired multimodal training/evaluation sets from processed corpora.

Strict Invariants:
- Preserves the None != 0 invariant via explicit tabular masks and modality availability indicators.
- NEVER fabricates missing modalities or coerces missing features to zero without an explicit mask.
- Clinical boundary: Does NOT generate or predict distress scores, escalation probabilities, or clinical diagnoses.
"""

from __future__ import annotations

import json
import math
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from backend.ml.features.assembly import MLInput
from backend.ml.features.registry import FEATURE_NAMES, TOTAL_FEATURES_COUNT


@dataclass
class MultimodalInputRecord:
    """Encapsulates all multimodal signals for a single beneficiary interaction."""

    case_id: str
    interaction_date: str

    # 1. Tabular features (60 features from MLInput; None != 0 preserved)
    tabular_features: Optional[Sequence[Optional[float]]] = None

    # 2. Text modality (raw text and/or representations from Slice 3.3)
    text_response: Optional[str] = None
    text_emotion_probabilities: Optional[Dict[str, float]] = None  # 28 GoEmotions classes
    text_emotion_embedding: Optional[List[float]] = None  # 768-dim
    stress_probability: Optional[float] = None  # 1-dim in [0.0, 1.0]
    stress_embedding: Optional[List[float]] = None  # 768-dim
    mental_health_embedding: Optional[List[float]] = None  # 768-dim

    # 3. Audio modality (raw waveform and/or representations from Slice 3.4)
    audio_path: Optional[str] = None
    audio_waveform: Optional[List[float]] = None
    audio_emotion_probabilities: Optional[Dict[str, float]] = None  # 8 RAVDESS classes
    audio_embedding: Optional[List[float]] = None  # 768-dim

    # Modality availability flags
    modality_availability: Dict[str, bool] = field(
        default_factory=lambda: {"tabular": False, "text": False, "audio": False}
    )

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Determines modality availability flags based on provided signals."""
        has_tab = bool(
            self.tabular_features is not None
            and any(f is not None for f in self.tabular_features)
        )
        has_text = bool(
            (self.text_response and self.text_response.strip())
            or (self.text_emotion_embedding and len(self.text_emotion_embedding) > 0)
            or (self.stress_embedding and len(self.stress_embedding) > 0)
            or (self.mental_health_embedding and len(self.mental_health_embedding) > 0)
        )
        has_audio = bool(
            self.audio_path
            or (self.audio_waveform and len(self.audio_waveform) > 0)
            or (self.audio_embedding and len(self.audio_embedding) > 0)
        )
        self.modality_availability = {
            "tabular": has_tab,
            "text": has_text,
            "audio": has_audio,
        }

    @classmethod
    def from_ml_input(
        cls,
        ml_input: MLInput,
        text_response: Optional[str] = None,
        text_emotion_probs: Optional[Dict[str, float]] = None,
        text_emotion_emb: Optional[List[float]] = None,
        stress_prob: Optional[float] = None,
        stress_emb: Optional[List[float]] = None,
        mental_health_emb: Optional[List[float]] = None,
        audio_path: Optional[str] = None,
        audio_emotion_probs: Optional[Dict[str, float]] = None,
        audio_emb: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MultimodalInputRecord:
        """Factory constructor building a record directly from an assembled MLInput."""
        return cls(
            case_id=ml_input.case_id,
            interaction_date=ml_input.interaction_date,
            tabular_features=list(ml_input.feature_values),
            text_response=text_response,
            text_emotion_probabilities=text_emotion_probs,
            text_emotion_embedding=text_emotion_emb,
            stress_probability=stress_prob,
            stress_embedding=stress_emb,
            mental_health_embedding=mental_health_emb,
            audio_path=audio_path,
            audio_emotion_probabilities=audio_emotion_probs,
            audio_embedding=audio_emb,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes record to dictionary suitable for JSONL."""
        return {
            "case_id": self.case_id,
            "interaction_date": self.interaction_date,
            "tabular_features": list(self.tabular_features) if self.tabular_features is not None else None,
            "text_response": self.text_response,
            "text_emotion_probabilities": self.text_emotion_probabilities,
            "text_emotion_embedding": self.text_emotion_embedding,
            "stress_probability": self.stress_probability,
            "stress_embedding": self.stress_embedding,
            "mental_health_embedding": self.mental_health_embedding,
            "audio_path": self.audio_path,
            "audio_emotion_probabilities": self.audio_emotion_probabilities,
            "audio_embedding": self.audio_embedding,
            "modality_availability": self.modality_availability,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MultimodalInputRecord:
        """Deserializes record from dictionary."""
        return cls(
            case_id=data.get("case_id", "UNKNOWN"),
            interaction_date=data.get("interaction_date", "2026-09-01"),
            tabular_features=data.get("tabular_features"),
            text_response=data.get("text_response"),
            text_emotion_probabilities=data.get("text_emotion_probabilities"),
            text_emotion_embedding=data.get("text_emotion_embedding"),
            stress_probability=data.get("stress_probability"),
            stress_embedding=data.get("stress_embedding"),
            mental_health_embedding=data.get("mental_health_embedding"),
            audio_path=data.get("audio_path"),
            audio_waveform=data.get("audio_waveform"),
            audio_emotion_probabilities=data.get("audio_emotion_probabilities"),
            audio_embedding=data.get("audio_embedding"),
            metadata=data.get("metadata", {}),
        )


class MultimodalFusionDataset:
    """Dataset class providing batched multimodal tensors / vectors for feature fusion."""

    def __init__(
        self,
        records: Sequence[MultimodalInputRecord],
        tabular_dim: int = TOTAL_FEATURES_COUNT,
        text_emb_dim: int = 768,
        audio_emb_dim: int = 768,
    ) -> None:
        self.records = list(records)
        self.tabular_dim = tabular_dim
        self.text_emb_dim = text_emb_dim
        self.audio_emb_dim = audio_emb_dim

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> MultimodalInputRecord:
        return self.records[index]

    def get_batch(self, indices: Sequence[int]) -> Dict[str, Any]:
        """Constructs a normalized, masked multimodal batch for the given indices."""
        batch_records = [self.records[i] for i in indices]
        batch_size = len(batch_records)

        # 1. Tabular features & missingness mask (preserves None != 0)
        batch_tab_values: List[List[float]] = []
        batch_tab_mask: List[List[float]] = []
        batch_tab_avail: List[float] = []

        for rec in batch_records:
            vals = [0.0] * self.tabular_dim
            masks = [0.0] * self.tabular_dim
            if rec.tabular_features is not None:
                for j in range(min(len(rec.tabular_features), self.tabular_dim)):
                    f_val = rec.tabular_features[j]
                    if f_val is not None:
                        vals[j] = float(f_val)
                        masks[j] = 1.0
            batch_tab_values.append(vals)
            batch_tab_mask.append(masks)
            batch_tab_avail.append(1.0 if rec.modality_availability.get("tabular", False) else 0.0)

        # 2. Text features (768 text emb + 28 emotion probs + 1 stress prob = 797 dim)
        batch_text_emb: List[List[float]] = []
        batch_text_avail: List[float] = []

        for rec in batch_records:
            has_text = rec.modality_availability.get("text", False)
            batch_text_avail.append(1.0 if has_text else 0.0)

            # Combined text representation vector
            text_vec = [0.0] * (self.text_emb_dim + 28 + 1)
            if has_text:
                # Fill embedding (prefer mental_health or text_emotion or stress)
                emb = rec.text_emotion_embedding or rec.mental_health_embedding or rec.stress_embedding
                if emb:
                    for k in range(min(len(emb), self.text_emb_dim)):
                        text_vec[k] = float(emb[k])
                # Fill 28 emotion probs
                if rec.text_emotion_probabilities:
                    for idx_p, p_val in enumerate(rec.text_emotion_probabilities.values()):
                        if idx_p < 28:
                            text_vec[self.text_emb_dim + idx_p] = float(p_val)
                # Fill stress prob
                if rec.stress_probability is not None:
                    text_vec[self.text_emb_dim + 28] = float(rec.stress_probability)

            batch_text_emb.append(text_vec)

        # 3. Audio features (768 audio emb + 8 emotion probs = 776 dim)
        batch_audio_emb: List[List[float]] = []
        batch_audio_avail: List[float] = []

        for rec in batch_records:
            has_audio = rec.modality_availability.get("audio", False)
            batch_audio_avail.append(1.0 if has_audio else 0.0)

            audio_vec = [0.0] * (self.audio_emb_dim + 8)
            if has_audio:
                if rec.audio_embedding:
                    for k in range(min(len(rec.audio_embedding), self.audio_emb_dim)):
                        audio_vec[k] = float(rec.audio_embedding[k])
                if rec.audio_emotion_probabilities:
                    for idx_p, p_val in enumerate(rec.audio_emotion_probabilities.values()):
                        if idx_p < 8:
                            audio_vec[self.audio_emb_dim + idx_p] = float(p_val)

            batch_audio_emb.append(audio_vec)

        return {
            "case_ids": [r.case_id for r in batch_records],
            "interaction_dates": [r.interaction_date for r in batch_records],
            "tabular_values": batch_tab_values,
            "tabular_mask": batch_tab_mask,
            "tabular_available": batch_tab_avail,
            "text_vector": batch_text_emb,
            "text_available": batch_text_avail,
            "audio_vector": batch_audio_emb,
            "audio_available": batch_audio_avail,
            "batch_size": batch_size,
        }

    def iterate_batches(self, batch_size: int, shuffle: bool = True, seed: int = 42) -> Iterator[Dict[str, Any]]:
        """Yields batches sequentially."""
        n = len(self.records)
        indices = list(range(n))
        if shuffle:
            rng = random.Random(seed)
            rng.shuffle(indices)

        for start_idx in range(0, n, batch_size):
            batch_idx = indices[start_idx : start_idx + batch_size]
            yield self.get_batch(batch_idx)


def split_multimodal_records_by_case(
    records: Sequence[MultimodalInputRecord],
    val_ratio: float = 0.2,
    seed: int = 42,
) -> Tuple[List[MultimodalInputRecord], List[MultimodalInputRecord]]:
    """Splits records deterministically at the case_id level to prevent leakage."""
    cases = sorted(list(set(r.case_id for r in records)))
    if len(cases) < 2:
        raise ValueError(f"Cannot perform case-level split with fewer than 2 distinct cases (got {len(cases)}).")

    rng = random.Random(seed)
    shuffled = list(cases)
    rng.shuffle(shuffled)

    val_count = max(1, int(len(cases) * val_ratio))
    val_cases = set(shuffled[:val_count])
    train_cases = set(shuffled[val_count:])

    # Strict leakage validation
    overlap = train_cases.intersection(val_cases)
    if overlap:
        raise ValueError(f"CASE LEAKAGE DETECTED: Cases appear in both splits: {overlap}")

    train_records = [r for r in records if r.case_id in train_cases]
    val_records = [r for r in records if r.case_id in val_cases]

    return train_records, val_records


def build_synthetic_multimodal_records(
    count: int = 100,
    seed: int = 42,
) -> List[MultimodalInputRecord]:
    """Generates realistic multimodal records for pipeline verification and smoke tests.

    Accurately models missingness patterns:
    - 20% interactions missing audio (no voice consent / telephony fallback)
    - 10% interactions missing text (voice check-in only)
    - Tabular features have natural None entries (preserving None != 0).
    """
    rng = random.Random(seed)
    records: List[MultimodalInputRecord] = []

    case_ids = [f"CASE-{i:03d}" for i in range(1, 21)]

    for idx in range(count):
        case_id = rng.choice(case_ids)
        day = (idx % 28) + 1
        date_str = f"2026-09-{day:02d}"

        # 1. Tabular features (60 features)
        tab_feats: List[Optional[float]] = []
        for feat_idx in range(TOTAL_FEATURES_COUNT):
            # 15% random feature missingness
            if rng.random() < 0.15:
                tab_feats.append(None)
            else:
                tab_feats.append(round(rng.uniform(0.0, 1.0), 3))

        # Modality presence
        has_text = rng.random() > 0.10
        has_audio = rng.random() > 0.20

        # Text signals
        text_resp = None
        text_probs = None
        text_emb = None
        stress_p = None
        if has_text:
            text_resp = "मुझे बहुत डर लग रहा है, कृपया मदद चाहिए।" if idx % 2 == 0 else "Feeling overwhelmed and stressed today."
            # Normalized 28 emotion distribution
            raw_p = [rng.expovariate(1.0) for _ in range(28)]
            sum_p = sum(raw_p)
            text_probs = {f"emotion_{e}": round(p / sum_p, 4) for e, p in enumerate(raw_p)}
            text_emb = [round(rng.gauss(0.0, 0.1), 4) for _ in range(768)]
            stress_p = round(rng.uniform(0.1, 0.9), 3)

        # Audio signals
        audio_path = None
        audio_probs = None
        audio_emb = None
        if has_audio:
            audio_path = f"datasets/ravdess/Actor_{(idx % 24) + 1:02d}/03-01-01-01-01-01-{(idx % 24) + 1:02d}.wav"
            raw_a = [rng.expovariate(1.0) for _ in range(8)]
            sum_a = sum(raw_a)
            audio_probs = {f"audio_emotion_{e}": round(p / sum_a, 4) for e, p in enumerate(raw_a)}
            audio_emb = [round(rng.gauss(0.0, 0.1), 4) for _ in range(768)]

        rec = MultimodalInputRecord(
            case_id=case_id,
            interaction_date=date_str,
            tabular_features=tab_feats,
            text_response=text_resp,
            text_emotion_probabilities=text_probs,
            text_emotion_embedding=text_emb,
            stress_probability=stress_p,
            stress_embedding=text_emb,
            mental_health_embedding=text_emb,
            audio_path=audio_path,
            audio_emotion_probabilities=audio_probs,
            audio_embedding=audio_emb,
            metadata={"sample_index": idx, "synthetic": True},
        )
        records.append(rec)

    return records
