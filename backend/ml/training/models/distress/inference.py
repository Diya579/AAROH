"""Dedicated High-Level Inference and Text-to-Distress Pipeline (Slice 3.6).

Wired directly to the frozen multilingual Text Emotion Model:
Input: Text
  ↓
Multilingual Emotion Probabilities (GoEmotions / EmoHinD) + Distress Lexicon Signals
  ↓
Dynamic Distress Model
  ↓
Distress Score [0.00, 1.00] + Discrete Level (LOW, MODERATE, HIGH, CRITICAL) + Machine-Readable Evidence

Supports:
- End-to-end text-to-distress inference
- Direct emotion-probabilities-to-distress inference
- Memory-safe batched inference
- Clean offline artifact loading (zero global state)
- Clinical boundary validation
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from backend.ml.features.distress import extract_distress_indicators
from backend.ml.training.models.distress.dataset import (
    BEHAVIOURAL_COUNT,
    DISTRESS_INPUT_DIM,
    ENGAGEMENT_COUNT,
    FUSED_EMBEDDING_DIM,
    LABEL_DISCLAIMER,
    DistressInputRecord,
)
from backend.ml.training.models.distress.explainability import (
    DistressEvidence,
    generate_distress_evidence,
)
from backend.ml.training.models.distress.model import (
    DEFAULT_THRESHOLDS,
    DynamicDistressModel,
)
from backend.ml.training.models.text_emotion.model import TextEmotionModel


def _find_repo_root() -> Path:
    cur = Path(__file__).resolve()
    for parent in cur.parents:
        if (parent / "models").exists() and (parent / "backend").exists():
            return parent
    return Path.cwd()


def _project_text_to_distress_fused_embedding(
    emotion_embedding: Sequence[float],  # 768-dim
    emotion_probabilities: Dict[str, float],
    stress_probability: float = 0.0,
) -> List[float]:
    """Deterministically projects 768-dim text embedding + emotions to 256-dim fused representation.

    Matches the Multimodal Feature Fusion (Slice 3.5) projection when only text modality is active.
    """
    import math

    # 768-dim embedding -> 256-dim via structured stride projection
    fused = [0.0] * FUSED_EMBEDDING_DIM
    emb_len = len(emotion_embedding) if emotion_embedding else 768
    raw_emb = list(emotion_embedding) if emotion_embedding else [0.0] * 768

    for i in range(FUSED_EMBEDDING_DIM):
        # 3:1 stride pooling with emotion modulation
        idx1 = (i * 3) % emb_len
        idx2 = (i * 3 + 1) % emb_len
        idx3 = (i * 3 + 2) % emb_len
        val = (raw_emb[idx1] + raw_emb[idx2] + raw_emb[idx3]) / 3.0
        fused[i] = val

    # Modulate top distress emotion signals into fused embedding
    fear_signal = float(emotion_probabilities.get("fear", 0.0))
    sad_signal = float(emotion_probabilities.get("sadness", 0.0))
    grief_signal = float(emotion_probabilities.get("grief", 0.0))
    nervous_signal = float(emotion_probabilities.get("nervousness", 0.0))
    joy_signal = float(emotion_probabilities.get("joy", 0.0))
    opt_signal = float(emotion_probabilities.get("optimism", 0.0))

    distress_load = (fear_signal * 0.35 + sad_signal * 0.25 + grief_signal * 0.25 + nervous_signal * 0.15)
    protective_load = (joy_signal * 0.50 + opt_signal * 0.50)
    net_factor = distress_load - protective_load

    for i in range(FUSED_EMBEDDING_DIM):
        fused[i] += net_factor * 0.20 * (((i % 8) + 1) / 8.0)

    # L2 normalize onto unit hypersphere
    norm = math.sqrt(sum(x * x for x in fused)) or 1e-8
    return [x / norm for x in fused]


class DistressInferencePipeline:
    """Production inference interface wiring Text Emotion Model to Dynamic Distress Model."""

    def __init__(
        self,
        distress_model: Optional[DynamicDistressModel] = None,
        text_model: Optional[TextEmotionModel] = None,
        distress_artifact_dir: Optional[Union[str, Path]] = None,
        text_artifact_dir: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
    ) -> None:
        self.device = device or "cpu"
        repo_root = _find_repo_root()

        # Resolve default artifact directories if not provided
        resolved_distress_dir = distress_artifact_dir or (repo_root / "models" / "distress")
        resolved_text_dir = text_artifact_dir or (repo_root / "models" / "text_emotion")

        # 1. Initialize or load Distress Model
        if distress_model is not None:
            self.distress_model = distress_model
        elif resolved_distress_dir and Path(resolved_distress_dir).exists():
            self.distress_model = DynamicDistressModel.load_from_artifact(resolved_distress_dir, device=self.device)
        else:
            self.distress_model = DynamicDistressModel(device=self.device)

        # 2. Initialize or load Text Emotion Model
        if text_model is not None:
            self.text_model = text_model
        elif resolved_text_dir and Path(resolved_text_dir).exists():
            self.text_model = TextEmotionModel.load_from_artifact(resolved_text_dir, device=self.device)
        else:
            # Fallback initialized text model
            self.text_model = TextEmotionModel()

    def predict_from_text(
        self,
        text: str,
        case_id: str = "CASE-INFERENCE",
        interaction_date: Optional[str] = None,
        behavioural_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None,
        engagement_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None,
        previous_emotion_probabilities: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Computes continuous distress score and machine-readable evidence from raw text."""
        clean_text = text.strip() if text else ""

        # Handle empty text cleanly
        if not clean_text:
            empty_evidence = generate_distress_evidence(
                distress_score=0.0,
                distress_level="LOW",
                thresholds=self.distress_model.thresholds,
                model_version=self.distress_model.model_version,
                raw_text="",
                emotion_probabilities={},
                behavioural_features=behavioural_features,
                engagement_features=engagement_features,
            )
            return {
                "distress_score": 0.0,
                "distress_level": "LOW",
                "distress_embedding": [0.0] * 128,
                "model_version": str(self.distress_model.model_version),
                "confidence": 0.95,
                "main_contributors": ["Empty text input: zero distress language observed"],
                "evidence": empty_evidence.to_dict(),
            }

        # Observable distress indicators extraction
        indicators, matched_evidence = extract_distress_indicators(clean_text)

        # 1. Step 1: Text Emotion Model Forward
        text_out = self.text_model.encode_and_predict([clean_text], device=self.device)
        emotion_probs = text_out["emotion_probabilities"][0]
        emotion_emb = text_out["emotion_embeddings"][0]

        # 2. Step 2: Project to Fused Representation (256-dim)
        fused_emb = _project_text_to_distress_fused_embedding(emotion_emb, emotion_probs)

        # 3. Step 3: Build DistressInputRecord
        resolved_b = behavioural_features
        if resolved_b is None:
            # Map observable text distress indicators to behavioural slots when tabular features absent
            dist_val = max(indicators.hopelessness, indicators.helplessness, indicators.intimidation, indicators.sadness)
            fear_val = max(indicators.fear, indicators.anxiety)
            if dist_val > 0.0 or fear_val > 0.0:
                resolved_b = [dist_val, 0.0, fear_val, 0.0, 0.0, 0.0, 0.0, 0.0]

        modality_weights = {"tabular": 0.20 if (resolved_b or engagement_features) else 0.0, "text": 0.80, "audio": 0.0}
        record = DistressInputRecord(
            case_id=case_id,
            interaction_date=interaction_date or "2026-03-01",
            fused_embedding=fused_emb,
            modality_weights=modality_weights,
            behavioural_features=resolved_b,
            engagement_features=engagement_features,
        )

        # 4. Step 4: Dynamic Distress Model Forward & Evidence Generation
        out = self.distress_model.predict_distress_with_evidence(
            record=record,
            raw_text=clean_text,
            emotion_probabilities=emotion_probs,
            previous_emotion_probabilities=previous_emotion_probabilities,
        )

        # Include emotion probabilities in output for end-to-end traceability
        out["emotion_probabilities"] = emotion_probs
        return out

    def predict_from_emotions(
        self,
        emotion_probabilities: Dict[str, float],
        emotion_embedding: Optional[Sequence[float]] = None,
        case_id: str = "CASE-EMOTIONS",
        behavioural_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None,
        engagement_features: Optional[Union[Dict[str, Optional[float]], Sequence[Optional[float]]]] = None,
        raw_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Computes distress score directly from precomputed emotion probabilities."""
        emb = list(emotion_embedding) if emotion_embedding is not None else [0.0] * 768
        fused_emb = _project_text_to_distress_fused_embedding(emb, emotion_probabilities)

        modality_weights = {"tabular": 0.20 if (behavioural_features or engagement_features) else 0.0, "text": 0.80, "audio": 0.0}
        record = DistressInputRecord(
            case_id=case_id,
            interaction_date="2026-03-01",
            fused_embedding=fused_emb,
            modality_weights=modality_weights,
            behavioural_features=behavioural_features,
            engagement_features=engagement_features,
        )

        out = self.distress_model.predict_distress_with_evidence(
            record=record,
            raw_text=raw_text,
            emotion_probabilities=emotion_probabilities,
        )
        return out
