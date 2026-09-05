"""Longitudinal Trajectory Dataset and Input Representation (Slice 3.7).

Models the temporal evolution of an individual's distress state across ordered interactions.
Preserves strict chronological order within each case and implements fixed-window padding/truncation.

Strict Boundaries:
- Estimates trajectory representations and dynamics over time ONLY.
- Does NOT perform clinical diagnosis, escalation prediction, or treatment planning.
- Supervised using SYNTHETIC DEMONSTRATION LABELS (NOT CLINICAL GROUND TRUTH).
"""

from __future__ import annotations

import copy
import datetime
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

# Feature Dimensions
FUSED_EMBEDDING_DIM = 256
DISTRESS_EMBEDDING_DIM = 128
TRAJECTORY_EMBEDDING_DIM = 128
DISTRESS_SCORE_DIM = 1
DISTRESS_LEVEL_DIM = 4  # LOW, MODERATE, HIGH, CRITICAL one-hot
BEHAVIOURAL_FEATURE_DIM = 16  # 8 values + 8 masks
ENGAGEMENT_FEATURE_DIM = 26   # 13 values + 13 masks
TIME_DELTA_DIM = 1

TIMESTEP_INPUT_DIM = (
    FUSED_EMBEDDING_DIM
    + DISTRESS_EMBEDDING_DIM
    + DISTRESS_SCORE_DIM
    + DISTRESS_LEVEL_DIM
    + BEHAVIOURAL_FEATURE_DIM
    + ENGAGEMENT_FEATURE_DIM
    + TIME_DELTA_DIM
)  # Exactly 432 dimensions

DEFAULT_HISTORY_WINDOW = 10

from enum import Enum


class TrajectoryLabel(str, Enum):
    """Canonical enumeration of longitudinal trajectory categories with associated internal scores."""

    STABLE = "STABLE"
    IMPROVING = "IMPROVING"
    WORSENING = "WORSENING"
    RAPIDLY_WORSENING = "RAPIDLY_WORSENING"

    @property
    def internal_score(self) -> float:
        """Canonical numeric slope score for expected trajectory calculation."""
        return TRAJECTORY_INTERNAL_SCORES[self]

    @property
    def definition(self) -> str:
        return TRAJECTORY_DEFINITIONS[self]


# Canonical internal score mapping
TRAJECTORY_INTERNAL_SCORES: Dict[TrajectoryLabel, float] = {
    TrajectoryLabel.IMPROVING: -1.0,
    TrajectoryLabel.STABLE: 0.0,
    TrajectoryLabel.WORSENING: 0.5,
    TrajectoryLabel.RAPIDLY_WORSENING: 1.0,
}

# Canonical definitions
TRAJECTORY_DEFINITIONS: Dict[TrajectoryLabel, str] = {
    TrajectoryLabel.STABLE: "Distress state remains consistent across recent interaction window.",
    TrajectoryLabel.IMPROVING: "Distress state exhibits significant downward trajectory over recent interactions.",
    TrajectoryLabel.WORSENING: "Distress state exhibits gradual upward progression over recent interactions.",
    TrajectoryLabel.RAPIDLY_WORSENING: "Distress state exhibits sharp escalation across consecutive interactions.",
}

# Trajectory String Constants derived from canonical enum
LABEL_STABLE = TrajectoryLabel.STABLE.value
LABEL_IMPROVING = TrajectoryLabel.IMPROVING.value
LABEL_WORSENING = TrajectoryLabel.WORSENING.value
LABEL_RAPIDLY_WORSENING = TrajectoryLabel.RAPIDLY_WORSENING.value
VALID_TRAJECTORY_LABELS: Tuple[str, ...] = tuple(
    tl.value
    for tl in (
        TrajectoryLabel.STABLE,
        TrajectoryLabel.IMPROVING,
        TrajectoryLabel.WORSENING,
        TrajectoryLabel.RAPIDLY_WORSENING,
    )
)
LABEL_TO_ID: Dict[str, int] = {lbl: i for i, lbl in enumerate(VALID_TRAJECTORY_LABELS)}
ID_TO_LABEL: Dict[int, str] = {i: lbl for i, lbl in enumerate(VALID_TRAJECTORY_LABELS)}

# Distress Level mapping
DISTRESS_LEVELS = ("LOW", "MODERATE", "HIGH", "CRITICAL")
DISTRESS_LEVEL_TO_ID = {lvl: i for i, lvl in enumerate(DISTRESS_LEVELS)}

LABEL_DISCLAIMER = (
    "SYNTHETIC DEMONSTRATION LABELS - NOT CLINICAL GROUND TRUTH. "
    "Supervised solely for engineering verification and architectural integrity."
)
SMOKE_TEST_DISCLAIMER = (
    "Smoke-test metrics are intended only to verify that the training, "
    "checkpointing, inference, and evaluation pipelines function correctly. "
    "They are NOT indicators of real-world model performance."
)


@dataclass
class TrajectoryInputRecord:
    """Single interaction timestep in an individual's longitudinal history.

    Features:
    - Fused embedding from Slice 3.5 (256-dim)
    - Distress embedding from Slice 3.6 (128-dim)
    - Distress continuous score from Slice 3.6 (1-dim)
    - Distress discrete level from Slice 3.6 (4-dim one-hot)
    - Behavioural interaction features from Slice 3.1 (16-dim: 8 values + 8 missingness masks)
    - Engagement interaction features from Slice 3.1 (26-dim: 13 values + 13 missingness masks)
    - Time delta in hours since previous interaction (1-dim, normalized)
    Total timestep feature vector: 432-dim.
    """

    case_id: str
    interaction_id: str
    timestamp: str
    distress_embedding: List[float]
    distress_score: float
    distress_level: str
    fused_embedding: List[float]
    behavioural_features: List[float]
    engagement_features: List[float]
    time_delta_hours: float = 0.0
    synthetic_trajectory_label: Optional[str] = None
    history_length: int = 1

    def to_timestep_vector(self) -> List[float]:
        """Concatenates all multimodal and interaction features into a 432-dim vector."""
        vec: List[float] = []

        # 1. Fused multimodal embedding (256)
        if len(self.fused_embedding) >= FUSED_EMBEDDING_DIM:
            vec.extend(self.fused_embedding[:FUSED_EMBEDDING_DIM])
        else:
            vec.extend(self.fused_embedding)
            vec.extend([0.0] * (FUSED_EMBEDDING_DIM - len(self.fused_embedding)))

        # 2. Distress embedding (128)
        if len(self.distress_embedding) >= DISTRESS_EMBEDDING_DIM:
            vec.extend(self.distress_embedding[:DISTRESS_EMBEDDING_DIM])
        else:
            vec.extend(self.distress_embedding)
            vec.extend([0.0] * (DISTRESS_EMBEDDING_DIM - len(self.distress_embedding)))

        # 3. Distress continuous score (1)
        score = max(0.0, min(1.0, float(self.distress_score)))
        vec.append(score)

        # 4. Distress discrete level one-hot (4)
        lvl_one_hot = [0.0] * len(DISTRESS_LEVELS)
        lvl_idx = DISTRESS_LEVEL_TO_ID.get(self.distress_level.upper(), 1)
        lvl_one_hot[lvl_idx] = 1.0
        vec.extend(lvl_one_hot)

        # 5. Behavioural features (16)
        if len(self.behavioural_features) >= BEHAVIOURAL_FEATURE_DIM:
            vec.extend(self.behavioural_features[:BEHAVIOURAL_FEATURE_DIM])
        else:
            vec.extend(self.behavioural_features)
            vec.extend([0.0] * (BEHAVIOURAL_FEATURE_DIM - len(self.behavioural_features)))

        # 6. Engagement features (26)
        if len(self.engagement_features) >= ENGAGEMENT_FEATURE_DIM:
            vec.extend(self.engagement_features[:ENGAGEMENT_FEATURE_DIM])
        else:
            vec.extend(self.engagement_features)
            vec.extend([0.0] * (ENGAGEMENT_FEATURE_DIM - len(self.engagement_features)))

        # 7. Normalized time delta (1) - capped at 7 days (168h) -> [0.0, 1.0]
        norm_dt = max(0.0, min(1.0, float(self.time_delta_hours) / 168.0))
        vec.append(norm_dt)

        assert len(vec) == TIMESTEP_INPUT_DIM, f"Expected {TIMESTEP_INPUT_DIM}, got {len(vec)}"
        return vec


@dataclass
class CaseTrajectory:
    """Chronologically ordered sequence of interactions belonging to a single case."""

    case_id: str
    records: List[TrajectoryInputRecord]
    trajectory_label: str

    def __post_init__(self) -> None:
        # Sort chronologically by timestamp
        self.records.sort(key=lambda r: r.timestamp)
        # Verify chronological ordering
        for i in range(len(self.records) - 1):
            t_curr = self.records[i].timestamp
            t_next = self.records[i + 1].timestamp
            if t_curr > t_next:
                raise ValueError(
                    f"Chronological violation in case {self.case_id}: {t_curr} occurs after {t_next}"
                )

    @property
    def total_interactions(self) -> int:
        return len(self.records)

    def get_windowed_sequence(
        self,
        history_window: int = DEFAULT_HISTORY_WINDOW,
    ) -> Tuple[List[List[float]], List[bool], int]:
        """Applies fixed history window rules:

        - If interactions < history_window:
            left-pad with zero vectors, preserving chronological order.
            padding_mask: True for padded timesteps, False for valid interactions.
        - If interactions == history_window:
            use sequence directly, padding_mask: all False.
        - If interactions > history_window:
            retain ONLY the most recent history_window interactions.
            oldest interactions outside the window are discarded.
            Chronological ordering strictly preserved.
            padding_mask: all False.

        Returns:
            (windowed_vectors, padding_mask, sequence_length)
            windowed_vectors: [history_window, TIMESTEP_INPUT_DIM]
            padding_mask: [history_window] (bool, True indicates padded timestep to ignore)
            sequence_length: int (number of valid interactions in window)
        """
        if history_window <= 0:
            raise ValueError(f"history_window must be > 0, got {history_window}")

        num_interactions = len(self.records)

        if num_interactions == 0:
            zero_vec = [0.0] * TIMESTEP_INPUT_DIM
            return [zero_vec] * history_window, [True] * history_window, 0

        if num_interactions > history_window:
            # Retain only the most recent history_window interactions
            active_records = self.records[-history_window:]
            windowed_vectors = [r.to_timestep_vector() for r in active_records]
            padding_mask = [False] * history_window
            sequence_length = history_window
        elif num_interactions == history_window:
            windowed_vectors = [r.to_timestep_vector() for r in self.records]
            padding_mask = [False] * history_window
            sequence_length = history_window
        else:
            # Left-pad with zeros
            pad_count = history_window - num_interactions
            zero_vec = [0.0] * TIMESTEP_INPUT_DIM
            windowed_vectors = [zero_vec] * pad_count + [r.to_timestep_vector() for r in self.records]
            padding_mask = [True] * pad_count + [False] * num_interactions
            sequence_length = num_interactions

        return windowed_vectors, padding_mask, sequence_length


class TrajectoryDataset:
    """In-memory dataset of case trajectories with fixed-window batching."""

    def __init__(
        self,
        trajectories: List[CaseTrajectory],
        history_window: int = DEFAULT_HISTORY_WINDOW,
    ) -> None:
        self.trajectories = list(trajectories)
        self.history_window = history_window

    def __len__(self) -> int:
        return len(self.trajectories)

    def __getitem__(self, idx: int) -> CaseTrajectory:
        return self.trajectories[idx]

    def iterate_batches(
        self,
        batch_size: int,
        shuffle: bool = True,
        seed: int = 42,
    ) -> Iterator[Dict[str, Any]]:
        """Yields mini-batches with fixed history window and padding masks."""
        indices = list(range(len(self.trajectories)))
        if shuffle:
            rng = random.Random(seed)
            rng.shuffle(indices)

        for i in range(0, len(indices), batch_size):
            batch_indices = indices[i : i + batch_size]
            batch_trajectories = [self.trajectories[idx] for idx in batch_indices]

            batch_inputs: List[List[List[float]]] = []
            batch_masks: List[List[bool]] = []
            batch_lengths: List[int] = []
            batch_targets: List[int] = []
            batch_case_ids: List[str] = []

            for traj in batch_trajectories:
                vectors, mask, length = traj.get_windowed_sequence(self.history_window)
                batch_inputs.append(vectors)
                batch_masks.append(mask)
                batch_lengths.append(length)
                target_idx = LABEL_TO_ID.get(traj.trajectory_label, 0)
                batch_targets.append(target_idx)
                batch_case_ids.append(traj.case_id)

            yield {
                "inputs": batch_inputs,          # [B, history_window, 432]
                "padding_masks": batch_masks,    # [B, history_window] (True = padded)
                "lengths": batch_lengths,        # [B]
                "targets": batch_targets,        # [B] (0..3)
                "case_ids": batch_case_ids,      # [B]
                "history_window": self.history_window,
            }


def determine_synthetic_trajectory_label(scores: List[float]) -> str:
    """Classifies a sequence of distress scores into one of 4 canonical trajectories.

    Criteria:
    - Delta = last_score - first_score
    - Rapid acceleration = any single consecutive jump >= 0.18 or delta >= 0.40
    - Improving: delta <= -0.20
    - Worsening: delta >= 0.14
    - Stable: otherwise
    """
    if len(scores) < 2:
        return LABEL_STABLE

    delta = scores[-1] - scores[0]

    # Check for rapid worsening
    max_jump = max((scores[i] - scores[i - 1]) for i in range(1, len(scores)))
    if delta >= 0.40 or (delta >= 0.25 and max_jump >= 0.18):
        return LABEL_RAPIDLY_WORSENING

    if delta <= -0.20:
        return LABEL_IMPROVING

    if delta >= 0.14:
        return LABEL_WORSENING

    return LABEL_STABLE


def build_synthetic_trajectories(
    case_count: int = 40,
    min_interactions: int = 3,
    max_interactions: int = 14,
    seed: int = 42,
) -> List[CaseTrajectory]:
    """Generates synthetic multi-turn demonstration case trajectories.

    Simulates the 4 canonical trajectory dynamics across variable history lengths.
    Zero clinical validity: purely for pipeline and gradient descent verification.
    """
    rng = random.Random(seed)
    trajectories: List[CaseTrajectory] = []

    pattern_types = [LABEL_STABLE, LABEL_IMPROVING, LABEL_WORSENING, LABEL_RAPIDLY_WORSENING]

    base_time = datetime.datetime(2026, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

    for case_num in range(1, case_count + 1):
        case_id = f"CASE-{case_num:03d}"
        target_pattern = pattern_types[(case_num - 1) % len(pattern_types)]
        n_interactions = rng.randint(min_interactions, max_interactions)

        # Generate scores according to target pattern
        if target_pattern == LABEL_STABLE:
            base_score = rng.uniform(0.25, 0.60)
            scores = [
                max(0.05, min(0.95, base_score + rng.uniform(-0.04, 0.04)))
                for _ in range(n_interactions)
            ]
        elif target_pattern == LABEL_IMPROVING:
            start_score = rng.uniform(0.65, 0.90)
            end_score = rng.uniform(0.15, 0.35)
            step = (end_score - start_score) / (n_interactions - 1)
            scores = [
                max(0.05, min(0.95, start_score + i * step + rng.uniform(-0.03, 0.03)))
                for i in range(n_interactions)
            ]
        elif target_pattern == LABEL_WORSENING:
            start_score = rng.uniform(0.20, 0.45)
            end_score = rng.uniform(0.55, 0.72)
            step = (end_score - start_score) / (n_interactions - 1)
            scores = [
                max(0.05, min(0.95, start_score + i * step + rng.uniform(-0.03, 0.03)))
                for i in range(n_interactions)
            ]
        else:  # RAPIDLY_WORSENING
            start_score = rng.uniform(0.18, 0.35)
            scores = [start_score]
            curr = start_score
            for i in range(1, n_interactions):
                jump = rng.uniform(0.10, 0.22)
                curr = min(0.98, curr + jump)
                scores.append(curr)

        # Confirm actual label
        actual_label = determine_synthetic_trajectory_label(scores)

        # Generate interactions
        records: List[TrajectoryInputRecord] = []
        curr_time = base_time + datetime.timedelta(days=case_num)

        for step_idx in range(n_interactions):
            score = scores[step_idx]
            dt_hours = 0.0 if step_idx == 0 else rng.uniform(4.0, 48.0)
            curr_time += datetime.timedelta(hours=dt_hours)

            # Map score to level
            if score < 0.25:
                lvl = "LOW"
            elif score < 0.55:
                lvl = "MODERATE"
            elif score < 0.80:
                lvl = "HIGH"
            else:
                lvl = "CRITICAL"

            # Synthetic embeddings
            # Fused embedding (256-dim)
            fused_emb = [rng.gauss(0.0, 0.1) for _ in range(FUSED_EMBEDDING_DIM)]
            # Distress embedding (128-dim, unit-normalized)
            raw_distress = [rng.gauss(0.0, 0.1) for _ in range(DISTRESS_EMBEDDING_DIM)]
            norm = math.sqrt(sum(x * x for x in raw_distress)) or 1.0
            distress_emb = [x / norm for x in raw_distress]

            # Behavioural & engagement features
            beh_features = [rng.uniform(0.0, 1.0) for _ in range(8)] + [0.0] * 8
            eng_features = [rng.uniform(0.0, 1.0) for _ in range(13)] + [0.0] * 13

            record = TrajectoryInputRecord(
                case_id=case_id,
                interaction_id=f"{case_id}-INT-{step_idx + 1:02d}",
                timestamp=curr_time.isoformat(),
                distress_embedding=distress_emb,
                distress_score=score,
                distress_level=lvl,
                fused_embedding=fused_emb,
                behavioural_features=beh_features,
                engagement_features=eng_features,
                time_delta_hours=dt_hours,
                synthetic_trajectory_label=actual_label,
                history_length=step_idx + 1,
            )
            records.append(record)

        trajectories.append(
            CaseTrajectory(
                case_id=case_id,
                records=records,
                trajectory_label=actual_label,
            )
        )

    return trajectories


def split_trajectories_by_case(
    trajectories: List[CaseTrajectory],
    val_ratio: float = 0.25,
    seed: int = 42,
) -> Tuple[List[CaseTrajectory], List[CaseTrajectory]]:
    """Splits case trajectories into train and validation sets strictly by case_id.

    Zero case leakage: no case_id ever appears in both splits.
    """
    case_ids = sorted(list(set(t.case_id for t in trajectories)))
    rng = random.Random(seed)
    shuffled_cases = list(case_ids)
    rng.shuffle(shuffled_cases)

    val_count = max(1, int(len(shuffled_cases) * val_ratio))
    val_case_set = set(shuffled_cases[:val_count])
    train_case_set = set(shuffled_cases[val_count:])

    train_trajectories = [t for t in trajectories if t.case_id in train_case_set]
    val_trajectories = [t for t in trajectories if t.case_id in val_case_set]

    validate_no_case_leakage(train_trajectories, val_trajectories)
    return train_trajectories, val_trajectories


def validate_no_case_leakage(
    train_trajectories: List[CaseTrajectory],
    val_trajectories: List[CaseTrajectory],
) -> None:
    """Raises ValueError if any case_id appears in both splits."""
    train_cases = set(t.case_id for t in train_trajectories)
    val_cases = set(t.case_id for t in val_trajectories)
    overlap = train_cases.intersection(val_cases)
    if overlap:
        raise ValueError(f"CASE LEAKAGE DETECTED: Cases appear in both train and val: {sorted(list(overlap))}")
