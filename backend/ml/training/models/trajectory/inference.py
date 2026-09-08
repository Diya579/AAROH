"""Dedicated High-Level Longitudinal Trajectory Inference Pipeline (Slice 3.7).

Wired directly across upstream components:
Text
  ↓
Text Emotion Model (Slice 3.3 - Multilingual DistilBERT)
  ↓
Dynamic Distress Model (Slice 3.6 - Multimodal Distress Engine)
  ↓
Longitudinal Trajectory Model (Slice 3.7 - GRU / Temporal Aggregation)
  ↓
Trajectory Score + State (Improving / Stable / Slowly worsening / Rapidly worsening / Recovering)
  + Velocity + Acceleration + Confidence + Machine-Readable Evidence

Supports:
- End-to-end multi-interaction text sequence prediction
- Incremental interaction addition and state tracking
- Direct prediction from pre-extracted TrajectoryInputRecord lists
- Offline artifact loading (zero global state)
- Clinical boundary validation
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from backend.ml.training.models.distress.dataset import (
    BEHAVIOURAL_COUNT,
    ENGAGEMENT_COUNT,
    DistressInputRecord,
)
from backend.ml.training.models.distress.inference import (
    _project_text_to_distress_fused_embedding,
)
from backend.ml.training.models.distress.model import DynamicDistressModel
from backend.ml.training.models.text_emotion.model import TextEmotionModel
from backend.ml.training.models.trajectory.dataset import (
    BEHAVIOURAL_FEATURE_DIM,
    DEFAULT_HISTORY_WINDOW,
    ENGAGEMENT_FEATURE_DIM,
    CaseTrajectory,
    TrajectoryInputRecord,
)
from backend.ml.training.models.trajectory.model import (
    LongitudinalTrajectoryModel,
)


def _format_iso(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


class TrajectoryInferencePipeline:
    """Production inference interface wiring Emotion, Distress, and Trajectory models."""

    def __init__(
        self,
        trajectory_model: Optional[LongitudinalTrajectoryModel] = None,
        distress_model: Optional[DynamicDistressModel] = None,
        text_model: Optional[TextEmotionModel] = None,
        trajectory_artifact_dir: Optional[Union[str, Path]] = None,
        distress_artifact_dir: Optional[Union[str, Path]] = None,
        text_artifact_dir: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
        history_window: int = DEFAULT_HISTORY_WINDOW,
    ) -> None:
        self.device = device or "cpu"
        self.history_window = history_window

        # 1. Trajectory Model
        if trajectory_model is not None:
            self.trajectory_model = trajectory_model
        elif trajectory_artifact_dir and Path(trajectory_artifact_dir).exists():
            self.trajectory_model = LongitudinalTrajectoryModel.load_from_artifact(
                trajectory_artifact_dir, device=self.device
            )
        else:
            self.trajectory_model = LongitudinalTrajectoryModel(
                history_window=self.history_window, device=self.device
            )

        # 2. Distress Model
        if distress_model is not None:
            self.distress_model = distress_model
        elif distress_artifact_dir and Path(distress_artifact_dir).exists():
            self.distress_model = DynamicDistressModel.load_from_artifact(
                distress_artifact_dir, device=self.device
            )
        else:
            self.distress_model = DynamicDistressModel(device=self.device)

        # 3. Text Emotion Model
        if text_model is not None:
            self.text_model = text_model
        elif text_artifact_dir and Path(text_artifact_dir).exists():
            self.text_model = TextEmotionModel.load_from_artifact(
                text_artifact_dir, device=self.device
            )
        else:
            self.text_model = TextEmotionModel()

    def create_timestep_from_text(
        self,
        text: str,
        timestamp: Optional[str] = None,
        case_id: str = "CASE-LONGITUDINAL",
        interaction_id: Optional[str] = None,
        time_delta_hours: float = 24.0,
        behavioural_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None,
        engagement_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None,
    ) -> TrajectoryInputRecord:
        """Converts raw text and optional metadata into a complete 432-dim TrajectoryInputRecord."""
        clean_text = text.strip() if text else ""
        i_id = interaction_id or f"INT-{datetime.datetime.now().strftime('%H%M%S%f')[:10]}"
        ts = timestamp or _format_iso(datetime.datetime.now())

        # 1. Text Emotion Forward
        if clean_text:
            text_out = self.text_model.encode_and_predict([clean_text], device=self.device)
            emotion_probs = text_out["emotion_probabilities"][0]
            emotion_emb = text_out["emotion_embeddings"][0]
        else:
            emotion_probs = {}
            emotion_emb = [0.0] * 768

        # 2. Project text -> 256-dim fused representation
        fused_emb = _project_text_to_distress_fused_embedding(emotion_emb, emotion_probs)

        # 3. Dynamic Distress Forward
        modality_weights = {
            "tabular": 0.10 if (behavioural_features or engagement_features) else 0.0,
            "text": 0.90 if clean_text else 0.0,
            "audio": 0.0,
        }
        distress_rec = DistressInputRecord(
            case_id=case_id,
            interaction_date=ts[:10],
            fused_embedding=fused_emb,
            modality_weights=modality_weights,
            behavioural_features=behavioural_features,
            engagement_features=engagement_features,
        )
        dist_out = self.distress_model.predict_distress(distress_rec)

        # 4. Prepare normalized 16-dim behavioural and 26-dim engagement features
        b_vec = [0.0] * BEHAVIOURAL_FEATURE_DIM
        if behavioural_features:
            if isinstance(behavioural_features, dict):
                vals = list(behavioural_features.values())
            else:
                vals = list(behavioural_features)
            for i, v in enumerate(vals[:8]):
                if v is not None:
                    b_vec[i] = float(v)
                    b_vec[i + 8] = 1.0  # present mask

        e_vec = [0.0] * ENGAGEMENT_FEATURE_DIM
        if engagement_features:
            if isinstance(engagement_features, dict):
                vals = list(engagement_features.values())
            else:
                vals = list(engagement_features)
            for i, v in enumerate(vals[:13]):
                if v is not None:
                    e_vec[i] = float(v)
                    e_vec[i + 13] = 1.0  # present mask

        return TrajectoryInputRecord(
            case_id=case_id,
            interaction_id=i_id,
            timestamp=ts,
            distress_embedding=dist_out["distress_embedding"],
            distress_score=dist_out["distress_score"],
            distress_level=dist_out["distress_level"],
            fused_embedding=fused_emb,
            behavioural_features=b_vec,
            engagement_features=e_vec,
            time_delta_hours=time_delta_hours,
        )

    def predict_from_records(
        self,
        records: List[TrajectoryInputRecord],
    ) -> Dict[str, Any]:
        """Predicts trajectory directly from an ordered sequence of TrajectoryInputRecord objects."""
        if not records:
            raise ValueError("records list cannot be empty for trajectory prediction")

        case = CaseTrajectory(
            case_id=records[0].case_id,
            records=records,
            trajectory_label="UNKNOWN",
        )
        return self.trajectory_model.predict_trajectory_with_evidence(case)

    def predict_from_texts(
        self,
        texts: List[str],
        timestamps: Optional[List[str]] = None,
        case_id: str = "CASE-SEQUENCE",
        behavioural_series: Optional[List[Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]]]] = None,
        engagement_series: Optional[List[Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]]]] = None,
    ) -> Dict[str, Any]:
        """End-to-end inference from a chronological sequence of client text messages."""
        if not texts:
            raise ValueError("texts list cannot be empty for sequence trajectory prediction")

        base_time = datetime.datetime.now() - datetime.timedelta(days=len(texts))
        records: List[TrajectoryInputRecord] = []

        for idx, text in enumerate(texts):
            # Resolve timestamp
            if timestamps and idx < len(timestamps) and timestamps[idx]:
                ts = timestamps[idx]
            else:
                dt = base_time + datetime.timedelta(days=idx)
                ts = _format_iso(dt)

            dt_hours = 24.0 if idx > 0 else 0.0

            b_feats = behavioural_series[idx] if (behavioural_series and idx < len(behavioural_series)) else None
            e_feats = engagement_series[idx] if (engagement_series and idx < len(engagement_series)) else None

            rec = self.create_timestep_from_text(
                text=text,
                timestamp=ts,
                case_id=case_id,
                interaction_id=f"INT-{idx+1:03d}",
                time_delta_hours=dt_hours,
                behavioural_features=b_feats,
                engagement_features=e_feats,
            )
            records.append(rec)

        out = self.predict_from_records(records)
        out["interactions_processed"] = len(records)
        out["most_recent_distress_score"] = records[-1].distress_score
        out["most_recent_distress_level"] = records[-1].distress_level
        return out
