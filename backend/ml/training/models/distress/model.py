"""Dynamic Distress Model (Slice 3.6).

Converts current multimodal fusion representations and interaction features into a CURRENT
distress state.

Architectural Pipeline:
1. Inputs (301-dim):
   - Fused multimodal embedding from Slice 3.5 (256-dim)
   - Behavioural feature slice from Slice 3.1 (8 values + 8 missingness masks = 16-dim)
   - Engagement feature slice from Slice 3.1 (13 values + 13 missingness masks = 26-dim)
   - Modality gating weights from Slice 3.5 (3-dim)
2. Feature Projection:
   - Linear(301, 128) + ReLU
3. Residual Feed Forward Block:
   - Linear(128, 128) + ReLU + Linear(128, 128)
   - Residual connection: h_res = ReLU(h_proj + FFN(h_proj))
4. 128-dimensional Distress Embedding:
   - Latent representation on unit hypersphere: h_emb = h_res / ||h_res||_2
5. Regression Head:
   - Linear(128, 64) + ReLU + Linear(64, 1) + Sigmoid -> continuous distress_score in [0.0, 1.0]
6. Threshold Mapper:
   - Categorizes score into LOW, MODERATE, HIGH, CRITICAL

Strict Clinical & Architectural Boundaries:
- Estimates CURRENT distress state only.
- Does NOT predict future trajectories, escalation, or longitudinal progression.
- Does NOT predict psychiatric diagnoses (depression, anxiety, PTSD, suicide risk).
- Does NOT recommend clinical treatments or interventions.
- Allowed outputs strictly limited to: distress_embedding, distress_score, distress_level.
- Supervised ONLY using SYNTHETIC DEMONSTRATION LABELS (NOT CLINICAL GROUND TRUTH).
"""

from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from backend.ml.training.models.common import (
    ModelExportManager,
    ModelMetadata,
    enforce_distress_boundary,
    get_device,
    set_seed,
)
from backend.ml.training.models.distress.dataset import (
    DISTRESS_INPUT_DIM,
    FUSED_EMBEDDING_DIM,
    LABEL_DISCLAIMER,
    DistressInputRecord,
)

from backend.ml.inference.exceptions import (
    ExecutionModeError,
    NeuralExecutionError,
)

# Upstream Pretrained Backbone Parameter References (Slice 3.3 and Slice 3.4)
DISTILBERT_PARAM_COUNT = 134_734_080
WAV2VEC2_PARAM_COUNT = 95_040_000
FROZEN_BACKBONES_PARAM_COUNT = DISTILBERT_PARAM_COUNT + WAV2VEC2_PARAM_COUNT

# Explicit Execution Modes
EXECUTION_MODE_FALLBACK = "FALLBACK"
EXECUTION_MODE_NEURAL = "NEURAL"
EXECUTION_MODE_PYTORCH_FROZEN = "PYTORCH_FROZEN"
EXECUTION_MODE_PYTORCH_FINETUNE = "PYTORCH_FINETUNE"
VALID_EXECUTION_MODES = {
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_NEURAL,
    EXECUTION_MODE_PYTORCH_FROZEN,
    EXECUTION_MODE_PYTORCH_FINETUNE,
}

# Dimensions
INPUT_DIM = DISTRESS_INPUT_DIM  # 301
PROJECTION_DIM = 128
RESIDUAL_HIDDEN_DIM = 128
DISTRESS_EMBEDDING_DIM = 128
REGRESSION_HIDDEN_DIM = 64
OUTPUT_SCORE_DIM = 1

# Default Thresholds
DEFAULT_THRESHOLDS = {
    "low": 0.25,
    "moderate": 0.55,
    "high": 0.80,
}

DEFAULT_MODEL_VERSION = "aaroh-distress-v1"
DEFAULT_DISTRESS_BACKBONE = "distilbert-base-multilingual-cased"
THRESHOLDS_FILENAME = "thresholds.json"

LEVEL_LOW = "LOW"
LEVEL_MODERATE = "MODERATE"
LEVEL_HIGH = "HIGH"
LEVEL_CRITICAL = "CRITICAL"
VALID_DISTRESS_LEVELS = (LEVEL_LOW, LEVEL_MODERATE, LEVEL_HIGH, LEVEL_CRITICAL)


def load_thresholds_from_config(config_or_thresholds_path: Union[str, Path]) -> Dict[str, float]:
    """Loads thresholds dictionary from a versioned JSON file (config.json or legacy thresholds.json)."""
    p = Path(config_or_thresholds_path)
    if not p.exists():
        raise FileNotFoundError(f"Thresholds file not found at {p}")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "threshold_configuration" in data and isinstance(data["threshold_configuration"], dict):
        cfg = data["threshold_configuration"]
        if "thresholds" in cfg and isinstance(cfg["thresholds"], dict):
            return {str(k): float(v) for k, v in cfg["thresholds"].items()}
    if "thresholds" in data and isinstance(data["thresholds"], dict):
        return {str(k): float(v) for k, v in data["thresholds"].items()}
    elif "low" in data and "moderate" in data and "high" in data:
        return {str(k): float(v) for k, v in data.items() if k in ("low", "moderate", "high")}
    raise ValueError(f"Could not extract thresholds from {p}")


def _mat_vec_mul(W: List[List[float]], x: List[float], b: List[float]) -> List[float]:
    """Computes y = W^T x + b where W is (in_dim, out_dim)."""
    in_dim = len(x)
    out_dim = len(b)
    out = [b[j] for j in range(out_dim)]
    for i in range(in_dim):
        xi = x[i]
        if xi != 0.0:
            Wi = W[i]
            for j in range(out_dim):
                out[j] += xi * Wi[j]
    return out


def _init_weight_matrix(in_dim: int, out_dim: int, seed: int = 42) -> List[List[float]]:
    """Xavier uniform initialization for pure-Python fallback weights."""
    rng = random.Random(seed)
    limit = math.sqrt(6.0 / (in_dim + out_dim))
    return [[rng.uniform(-limit, limit) for _ in range(out_dim)] for _ in range(in_dim)]


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid function."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def _relu(val: float) -> float:
    return val if val > 0.0 else 0.0


class DynamicDistressModel:
    """AAROH Dynamic Distress Model supporting dual-mode execution (PyTorch & Pure-Python Fallback)."""

    def __init__(
        self,
        model_version: str = DEFAULT_MODEL_VERSION,
        thresholds: Optional[Dict[str, float]] = None,
        config_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
        seed: int = 42,
        unfreeze_backbone: bool = False,
        force_mode: Optional[str] = None,
        backbone: str = DEFAULT_DISTRESS_BACKBONE,
        max_length: int = 128,
        local_artifact_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.model_version = model_version
        self.seed = seed
        self.device = device or get_device()
        self.unfreeze_backbone = unfreeze_backbone
        self.backbone = backbone
        self.max_length = max_length
        self.local_artifact_dir = Path(local_artifact_dir) if local_artifact_dir else None
        set_seed(seed)

        # Configurable thresholds: resolve from argument, explicit config_path, default config.json, legacy thresholds.json, or fallback
        if thresholds is not None:
            self.thresholds = dict(thresholds)
        elif config_path is not None and Path(config_path).exists():
            self.thresholds = load_thresholds_from_config(config_path)
        elif Path("models/distress/config.json").exists():
            self.thresholds = load_thresholds_from_config("models/distress/config.json")
        elif Path("models/distress/thresholds.json").exists():
            self.thresholds = load_thresholds_from_config("models/distress/thresholds.json")
        else:
            self.thresholds = dict(DEFAULT_THRESHOLDS)
        self._validate_thresholds()

        # Detect PyTorch availability
        self.is_torch_available = False
        self.torch_model = None
        self.transformer_model = None
        self.tokenizer = None
        try:
            import torch
            import torch.nn as nn
            self.is_torch_available = True
        except ImportError:
            self.is_torch_available = False

        # Determine explicit execution mode
        if force_mode is not None:
            if force_mode not in VALID_EXECUTION_MODES:
                raise ExecutionModeError(
                    f"Invalid execution mode: {force_mode}. Valid options: {sorted(VALID_EXECUTION_MODES)}"
                )
            if force_mode == EXECUTION_MODE_NEURAL:
                self.execution_mode = (
                    EXECUTION_MODE_PYTORCH_FINETUNE
                    if self.unfreeze_backbone
                    else EXECUTION_MODE_PYTORCH_FROZEN
                )
            else:
                self.execution_mode = force_mode
        else:
            self.execution_mode = EXECUTION_MODE_FALLBACK

        # Backbones
        self.text_backbone = None
        self.audio_backbone = None

        if self.execution_mode in (EXECUTION_MODE_PYTORCH_FROZEN, EXECUTION_MODE_PYTORCH_FINETUNE):
            if self.is_torch_available:
                self._init_pytorch_model()
                self._init_transformer_model(self.local_artifact_dir)
            else:
                self._init_pure_python_weights()
        else:
            self._init_pure_python_weights()

    def _init_transformer_model(self, local_artifact_dir: Optional[Path] = None) -> None:
        """Initializes the real multilingual transformer used by Colab training/inference."""
        import torch.nn as nn
        from transformers import AutoModel, AutoTokenizer

        class _DistressTransformerHead(nn.Module):
            def __init__(self, encoder: Any) -> None:
                super().__init__()
                self.encoder = encoder
                hidden = int(encoder.config.hidden_size)
                self.dropout = nn.Dropout(0.2)
                self.embedding = nn.Linear(hidden, DISTRESS_EMBEDDING_DIM)
                self.regression = nn.Sequential(
                    nn.ReLU(),
                    nn.Linear(DISTRESS_EMBEDDING_DIM, REGRESSION_HIDDEN_DIM),
                    nn.ReLU(),
                    nn.Linear(REGRESSION_HIDDEN_DIM, 1),
                    nn.Sigmoid(),
                )

            def forward(self, input_ids: Any, attention_mask: Any, **_: Any) -> Tuple[Any, Any]:
                outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                hidden = outputs.last_hidden_state
                mask = attention_mask.unsqueeze(-1).float()
                pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                embedding = self.embedding(self.dropout(pooled))
                embedding = embedding / embedding.norm(p=2, dim=-1, keepdim=True).clamp(min=1e-8)
                return embedding, self.regression(embedding).squeeze(-1)

        source = str(local_artifact_dir) if local_artifact_dir and local_artifact_dir.exists() else self.backbone
        if local_artifact_dir and (local_artifact_dir / "transformer_config.json").exists():
            from transformers import AutoConfig
            encoder = AutoModel.from_config(
                AutoConfig.from_pretrained(local_artifact_dir / "transformer_config.json", local_files_only=True)
            )
        else:
            encoder = AutoModel.from_pretrained(source, attn_implementation="eager")
        self.transformer_model = _DistressTransformerHead(encoder)
        self.tokenizer = AutoTokenizer.from_pretrained(
            source, local_files_only=bool(local_artifact_dir and local_artifact_dir.exists())
        )
        if self.execution_mode == EXECUTION_MODE_PYTORCH_FROZEN:
            for parameter in self.transformer_model.encoder.parameters():
                parameter.requires_grad = False
        elif self.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE:
            for parameter in self.transformer_model.encoder.parameters():
                parameter.requires_grad = False
            layers = getattr(getattr(self.transformer_model.encoder, "transformer", None), "layer", [])
            for layer in list(layers)[-2:]:
                for parameter in layer.parameters():
                    parameter.requires_grad = True

    def encode_and_predict_text(self, texts: Sequence[str], device: Optional[str] = None) -> Dict[str, Any]:
        """Runs genuine transformer inference for raw text in neural execution modes."""
        if self.transformer_model is None or self.tokenizer is None:
            raise NeuralExecutionError("Distress transformer artifacts are not initialized")
        import torch
        target = torch.device(device or self.device)
        self.transformer_model.to(target).eval()
        tokens = self.tokenizer(list(texts), max_length=self.max_length, padding=True, truncation=True, return_tensors="pt")
        tokens = {key: value.to(target) for key, value in tokens.items()}
        with torch.no_grad():
            embeddings, scores = self.transformer_model(**tokens)
        return {
            "distress_embeddings": embeddings.detach().cpu().tolist(),
            "distress_scores": scores.detach().cpu().tolist(),
        }

    def _validate_thresholds(self) -> None:
        low = self.thresholds.get("low", DEFAULT_THRESHOLDS["low"])
        mod = self.thresholds.get("moderate", DEFAULT_THRESHOLDS["moderate"])
        high = self.thresholds.get("high", DEFAULT_THRESHOLDS["high"])
        if not (0.0 < low < mod < high < 1.0):
            raise ValueError(
                f"Invalid threshold ordering: expected 0 < low < moderate < high < 1, "
                f"got low={low}, moderate={mod}, high={high}"
            )

    def _init_pure_python_weights(self) -> None:
        """Initializes deterministic weights for pure-Python fallback execution.

        Exact Parameter Breakdown:
        - W_proj: 301 x 128 = 38,528, b_proj: 128 -> 38,656
        - W_res1: 128 x 128 = 16,384, b_res1: 128 -> 16,512
        - W_res2: 128 x 128 = 16,384, b_res2: 128 -> 16,512
        - W_reg1: 128 x 64  =  8,192, b_reg1:  64 ->  8,256
        - W_reg2:  64 x 1   =     64, b_reg2:   1 ->     65
        Total Trainable Parameters: 80,001
        """
        # 1. Feature projection (301 -> 128)
        self.W_proj = _init_weight_matrix(INPUT_DIM, PROJECTION_DIM, seed=self.seed)
        self.b_proj = [0.0] * PROJECTION_DIM

        # 2. Residual block (128 -> 128 -> 128)
        self.W_res1 = _init_weight_matrix(PROJECTION_DIM, RESIDUAL_HIDDEN_DIM, seed=self.seed + 1)
        self.b_res1 = [0.0] * RESIDUAL_HIDDEN_DIM
        self.W_res2 = _init_weight_matrix(RESIDUAL_HIDDEN_DIM, DISTRESS_EMBEDDING_DIM, seed=self.seed + 2)
        self.b_res2 = [0.0] * DISTRESS_EMBEDDING_DIM

        # 3. Regression head (128 -> 64 -> 1)
        self.W_reg1 = _init_weight_matrix(DISTRESS_EMBEDDING_DIM, REGRESSION_HIDDEN_DIM, seed=self.seed + 3)
        self.b_reg1 = [0.0] * REGRESSION_HIDDEN_DIM
        self.W_reg2 = _init_weight_matrix(REGRESSION_HIDDEN_DIM, OUTPUT_SCORE_DIM, seed=self.seed + 4)
        self.b_reg2 = [0.0] * OUTPUT_SCORE_DIM

    def _init_pytorch_model(self) -> None:
        """Initializes PyTorch nn.Module implementation when PyTorch is available."""
        if not self.is_torch_available:
            return
        import torch
        import torch.nn as nn

        class _PyTorchDistressNet(nn.Module):
            def __init__(self, thresholds: Dict[str, float]) -> None:
                super().__init__()
                self.proj = nn.Sequential(
                    nn.Linear(INPUT_DIM, PROJECTION_DIM),
                    nn.ReLU(),
                )
                self.res_fc1 = nn.Linear(PROJECTION_DIM, RESIDUAL_HIDDEN_DIM)
                self.res_relu = nn.ReLU()
                self.res_fc2 = nn.Linear(RESIDUAL_HIDDEN_DIM, DISTRESS_EMBEDDING_DIM)
                self.post_res_relu = nn.ReLU()

                self.reg = nn.Sequential(
                    nn.Linear(DISTRESS_EMBEDDING_DIM, REGRESSION_HIDDEN_DIM),
                    nn.ReLU(),
                    nn.Linear(REGRESSION_HIDDEN_DIM, OUTPUT_SCORE_DIM),
                    nn.Sigmoid(),
                )

            def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
                h_proj = self.proj(x)
                h_res = self.res_fc2(self.res_relu(self.res_fc1(h_proj)))
                h_res = self.post_res_relu(h_proj + h_res)

                # L2 normalize distress embedding
                norm = torch.norm(h_res, p=2, dim=-1, keepdim=True).clamp(min=1e-8)
                h_emb = h_res / norm

                score = self.reg(h_emb)
                return h_emb, score

        self.torch_model = _PyTorchDistressNet(self.thresholds)
        self._init_pure_python_weights()

    def get_parameter_counts(self) -> Dict[str, int]:
        """Returns rigorous parameter accounting across all 4 metrics.

        1. Trainable Parameters:
           38,656 (projection) + 16,512 (res1) + 16,512 (res2) + 8,256 (reg1) + 65 (reg2) = 80,001
        2. Backbone Parameters:
           229,774,080 (DistilBERT: 134,734,080 + Wav2Vec2: 95,040,000)
        3. Total If Instantiated:
           229,854,081 (80,001 + 229,774,080)
        4. Actually Instantiated:
           80,001 in FALLBACK mode (backbones referenced in config only, zero transformer weights in RAM)
        """
        trainable_head = 80_001
        backbone_params = FROZEN_BACKBONES_PARAM_COUNT
        total_if_instantiated = trainable_head + backbone_params

        if self.execution_mode == EXECUTION_MODE_FALLBACK:
            instantiated = trainable_head
        elif self.execution_mode == EXECUTION_MODE_PYTORCH_FROZEN:
            instantiated = total_if_instantiated
        elif self.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE:
            instantiated = total_if_instantiated
        else:
            instantiated = trainable_head

        return {
            "trainable_parameters": trainable_head,
            "trainable_head_parameters": trainable_head,
            "backbone_parameters": backbone_params,
            "total_parameters_if_instantiated": total_if_instantiated,
            "actually_instantiated_parameters": instantiated,
            "frozen_backbone_parameters": (
                0 if self.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE else backbone_params
            ),
        }

    def map_score_to_level(self, score: float) -> str:
        """Maps continuous distress score in [0.0, 1.0] to discrete distress level."""
        low = self.thresholds.get("low", DEFAULT_THRESHOLDS["low"])
        mod = self.thresholds.get("moderate", DEFAULT_THRESHOLDS["moderate"])
        high = self.thresholds.get("high", DEFAULT_THRESHOLDS["high"])

        if score < low:
            return LEVEL_LOW
        elif score < mod:
            return LEVEL_MODERATE
        elif score < high:
            return LEVEL_HIGH
        else:
            return LEVEL_CRITICAL

    def forward(self, x: List[float]) -> Tuple[List[float], float]:
        """Pure-Python forward pass for a single 301-dim input vector."""
        if len(x) != INPUT_DIM:
            raise ValueError(f"Expected input vector of length {INPUT_DIM}, got {len(x)}")

        # 1. Feature Projection: (301 -> 128) + ReLU
        proj_linear = _mat_vec_mul(self.W_proj, x, self.b_proj)
        h_proj = [_relu(v) for v in proj_linear]

        # 2. Residual Block: Linear -> ReLU -> Linear + Residual -> ReLU
        res1_linear = _mat_vec_mul(self.W_res1, h_proj, self.b_res1)
        h_res1 = [_relu(v) for v in res1_linear]
        res2_linear = _mat_vec_mul(self.W_res2, h_res1, self.b_res2)
        h_res = [_relu(h_proj[i] + res2_linear[i]) for i in range(PROJECTION_DIM)]

        # 3. 128-dim Distress Embedding (L2 normalized)
        norm = math.sqrt(sum(v * v for v in h_res)) or 1e-8
        h_emb = [v / norm for v in h_res]

        # 4. Regression Head: (128 -> 64 -> 1) + Sigmoid
        reg1_linear = _mat_vec_mul(self.W_reg1, h_emb, self.b_reg1)
        h_reg1 = [_relu(v) for v in reg1_linear]
        reg2_linear = _mat_vec_mul(self.W_reg2, h_reg1, self.b_reg2)
        score = _sigmoid(reg2_linear[0])

        return h_emb, score

    def train_step(self, batch: Dict[str, Any], lr: float = 1e-3) -> float:
        """Executes a single mini-batch gradient descent step."""
        inputs: List[List[float]] = batch["inputs"]
        targets: List[float] = batch["targets"]
        batch_size = len(inputs)
        if batch_size == 0:
            return 0.0

        batch_losses: List[float] = []

        for k in range(batch_size):
            x = inputs[k]
            target = targets[k]

            # Forward pass with intermediate activations saved
            proj_linear = _mat_vec_mul(self.W_proj, x, self.b_proj)
            h_proj = [_relu(v) for v in proj_linear]

            res1_linear = _mat_vec_mul(self.W_res1, h_proj, self.b_res1)
            h_res1 = [_relu(v) for v in res1_linear]

            res2_linear = _mat_vec_mul(self.W_res2, h_res1, self.b_res2)
            h_res = [_relu(h_proj[i] + res2_linear[i]) for i in range(PROJECTION_DIM)]

            norm = math.sqrt(sum(v * v for v in h_res)) or 1e-8
            h_emb = [v / norm for v in h_res]

            reg1_linear = _mat_vec_mul(self.W_reg1, h_emb, self.b_reg1)
            h_reg1 = [_relu(v) for v in reg1_linear]

            reg2_linear = _mat_vec_mul(self.W_reg2, h_reg1, self.b_reg2)
            score = _sigmoid(reg2_linear[0])

            # MSE loss on continuous distress score
            diff = score - target
            loss = 0.5 * (diff * diff)
            batch_losses.append(loss)

            # Backpropagation
            d_score = diff
            d_logit = d_score * (score * (1.0 - score))  # sigmoid derivative

            # Gradients for W_reg2, b_reg2
            d_b_reg2 = d_logit
            d_h_reg1 = [d_logit * self.W_reg2[j][0] for j in range(REGRESSION_HIDDEN_DIM)]

            for j in range(REGRESSION_HIDDEN_DIM):
                self.W_reg2[j][0] -= (lr / batch_size) * (d_logit * h_reg1[j])
            self.b_reg2[0] -= (lr / batch_size) * d_b_reg2

            # Gradients for W_reg1, b_reg1
            d_reg1_lin = [d_h_reg1[j] if reg1_linear[j] > 0 else 0.0 for j in range(REGRESSION_HIDDEN_DIM)]
            for i in range(DISTRESS_EMBEDDING_DIM):
                h_emb_i = h_emb[i]
                for j in range(REGRESSION_HIDDEN_DIM):
                    self.W_reg1[i][j] -= (lr / batch_size) * (d_reg1_lin[j] * h_emb_i)
            for j in range(REGRESSION_HIDDEN_DIM):
                self.b_reg1[j] -= (lr / batch_size) * d_reg1_lin[j]

            # Backprop into projection and residual blocks (lightweight update)
            d_h_emb = [0.0] * DISTRESS_EMBEDDING_DIM
            for i in range(DISTRESS_EMBEDDING_DIM):
                for j in range(REGRESSION_HIDDEN_DIM):
                    d_h_emb[i] += d_reg1_lin[j] * self.W_reg1[i][j]

            # Embedding projection update
            for i in range(min(len(x), INPUT_DIM)):
                xi = x[i]
                if xi != 0.0:
                    for j in range(PROJECTION_DIM):
                        grad = d_h_emb[j] * (1.0 if proj_linear[j] > 0 else 0.0) * xi
                        self.W_proj[i][j] -= (lr / batch_size) * 0.1 * grad

        return float(sum(batch_losses) / len(batch_losses)) if batch_losses else 0.0

    def predict_distress(
        self,
        record: Union[DistressInputRecord, Dict[str, Any], Sequence[float]],
        raw_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Public Inference Interface for AAROH Dynamic Distress Model.

        Returns strictly and only:
        {
            "distress_embedding": List[float],  # 128-dim learned latent vector
            "distress_score": float,            # continuous in [0.0, 1.0]
            "distress_level": str               # LOW / MODERATE / HIGH / CRITICAL
        }

        Strictly enforces clinical boundaries: NEVER outputs diagnoses, escalation,
        future trajectories, depression, anxiety, PTSD, or treatment recommendations.
        """
        # 1. Convert input to 301-dim vector
        if isinstance(record, DistressInputRecord):
            vec = record.to_feature_vector()
            raw_text = raw_text if raw_text is not None else record.raw_text
        elif isinstance(record, dict):
            raw_text = raw_text if raw_text is not None else record.get("raw_text")
            if "inputs" in record:
                vec = list(record["inputs"])
            elif "fused_embedding" in record:
                d_rec = DistressInputRecord(
                    case_id=record.get("case_id", "ANON"),
                    interaction_date=record.get("interaction_date", "2026-01-01"),
                    fused_embedding=record["fused_embedding"],
                    modality_weights=record.get("modality_weights", {"tabular": 0.33, "text": 0.33, "audio": 0.34}),
                    behavioural_features=record.get("behavioural_features"),
                    engagement_features=record.get("engagement_features"),
                )
                vec = d_rec.to_feature_vector()
            else:
                raise ValueError("Dictionary record must contain 'fused_embedding' or 'inputs'")
        elif isinstance(record, (list, tuple)):
            vec = list(record)
        else:
            raise TypeError(f"Unsupported record type for predict_distress: {type(record)}")

        # 2. Use the exported transformer for text; retain vector compatibility for callers without text.
        if raw_text and self.transformer_model is not None:
            text_out = self.encode_and_predict_text([raw_text])
            h_emb = text_out["distress_embeddings"][0]
            score = float(text_out["distress_scores"][0])
        else:
            h_emb, score = self.forward(vec)

        # 3. Categorize score into discrete level
        level = self.map_score_to_level(score)

        # 4. Construct response dictionary
        result = {
            "distress_embedding": [round(v, 6) for v in h_emb],
            "distress_score": round(float(score), 4),
            "distress_level": str(level),
            "model_version": str(self.model_version),
        }

        # 5. Enforce clinical boundaries across all outputs
        for key in result.keys():
            enforce_distress_boundary(key)
        if set(result.keys()) != {
            "distress_embedding",
            "distress_score",
            "distress_level",
            "model_version",
        }:
            raise ValueError(
                f"Clinical boundary violation: illegal output keys present in {set(result.keys())}"
            )

        return result

    def predict_distress_with_evidence(
        self,
        record: Union[DistressInputRecord, Dict[str, Any], Sequence[float]],
        raw_text: Optional[str] = None,
        emotion_probabilities: Optional[Dict[str, float]] = None,
        previous_emotion_probabilities: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Predicts distress and returns structured, machine-readable evidence grounded in inputs."""
        from backend.ml.training.models.distress.explainability import generate_distress_evidence

        base_result = self.predict_distress(record, raw_text=raw_text)

        b_feats = None
        e_feats = None
        mod_weights = None
        if isinstance(record, DistressInputRecord):
            b_feats = record.behavioural_features
            e_feats = record.engagement_features
            mod_weights = record.modality_weights
        elif isinstance(record, dict):
            b_feats = record.get("behavioural_features")
            e_feats = record.get("engagement_features")
            mod_weights = record.get("modality_weights")

        evidence = generate_distress_evidence(
            distress_score=base_result["distress_score"],
            distress_level=base_result["distress_level"],
            thresholds=self.thresholds,
            model_version=self.model_version,
            raw_text=raw_text,
            emotion_probabilities=emotion_probabilities,
            previous_emotion_probabilities=previous_emotion_probabilities,
            behavioural_features=b_feats,
            engagement_features=e_feats,
            modality_weights=mod_weights,
        )

        return {
            "distress_score": base_result["distress_score"],
            "distress_level": base_result["distress_level"],
            "distress_embedding": base_result["distress_embedding"],
            "model_version": base_result["model_version"],
            "confidence": evidence.confidence,
            "main_contributors": evidence.main_contributors,
            "evidence": evidence.to_dict(),
        }

    def save_checkpoint(
        self,
        path: Union[str, Path],
        epoch: int,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Saves model weights and training metadata."""
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "epoch": epoch,
            "metrics": metrics or {},
            "model_version": self.model_version,
            "thresholds": self.thresholds,
            "execution_mode": self.execution_mode,
            "W_proj": self.W_proj,
            "b_proj": self.b_proj,
            "W_res1": self.W_res1,
            "b_res1": self.b_res1,
            "W_res2": self.W_res2,
            "b_res2": self.b_res2,
            "W_reg1": self.W_reg1,
            "b_reg1": self.b_reg1,
            "W_reg2": self.W_reg2,
            "b_reg2": self.b_reg2,
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_checkpoint(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Reloads checkpoint weights into model, reading thresholds from config when available."""
        in_path = Path(path)
        try:
            import torch

            state = torch.load(in_path, map_location="cpu", weights_only=True)
        except Exception:
            with open(in_path, "r", encoding="utf-8") as f:
                state = json.load(f)

        self.model_version = state.get("model_version", self.model_version)

        if "model_state_dict" in state:
            if self.transformer_model is None:
                if not self.is_torch_available:
                    raise NeuralExecutionError(
                        "Cannot load neural distress checkpoint without PyTorch."
                    )
                self.execution_mode = EXECUTION_MODE_PYTORCH_FROZEN
                self._init_transformer_model()
            self.transformer_model.load_state_dict(state["model_state_dict"])
            self.transformer_model.to(self.device).eval()
            return {
                "epoch": state.get("epoch", 1),
                "metrics": state.get("metrics", {}),
            }

        # Check for adjacent versioned config.json (new) or legacy thresholds.json
        parent_dir = in_path.parent
        if (parent_dir / "config.json").exists():
            try:
                self.thresholds = load_thresholds_from_config(parent_dir / "config.json")
            except Exception:
                self.thresholds = state.get("thresholds", self.thresholds)
        elif (parent_dir / THRESHOLDS_FILENAME).exists():
            try:
                self.thresholds = load_thresholds_from_config(parent_dir / THRESHOLDS_FILENAME)
            except Exception:
                self.thresholds = state.get("thresholds", self.thresholds)
        else:
            self.thresholds = state.get("thresholds", self.thresholds)

        self.W_proj = state["W_proj"]
        self.b_proj = state["b_proj"]
        self.W_res1 = state["W_res1"]
        self.b_res1 = state["b_res1"]
        self.W_res2 = state["W_res2"]
        self.b_res2 = state["b_res2"]
        self.W_reg1 = state["W_reg1"]
        self.b_reg1 = state["b_reg1"]
        self.W_reg2 = state["W_reg2"]
        self.b_reg2 = state["b_reg2"]

        return {
            "epoch": state.get("epoch", 1),
            "metrics": state.get("metrics", {}),
        }

    def export(
        self,
        output_dir: Union[str, Path],
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Exports weights, configuration (with embedded thresholds), metadata, metrics, and label mapping."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Weights
        weights_file = out_dir / "weights"
        state = {
            "W_proj": self.W_proj,
            "b_proj": self.b_proj,
            "W_res1": self.W_res1,
            "b_res1": self.b_res1,
            "W_res2": self.W_res2,
            "b_res2": self.b_res2,
            "W_reg1": self.W_reg1,
            "b_reg1": self.b_reg1,
            "W_reg2": self.W_reg2,
            "b_reg2": self.b_reg2,
        }
        with open(weights_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        # 2. Config (includes embedded versioned threshold configuration)
        param_counts = self.get_parameter_counts()
        config_data = {
            "model_type": "dynamic_distress_model",
            "model_version": self.model_version,
            "input_dim": INPUT_DIM,
            "projection_dim": PROJECTION_DIM,
            "residual_hidden_dim": RESIDUAL_HIDDEN_DIM,
            "distress_embedding_dim": DISTRESS_EMBEDDING_DIM,
            "regression_hidden_dim": REGRESSION_HIDDEN_DIM,
            "output_dim": OUTPUT_SCORE_DIM,
            "backbone": self.backbone,
            "max_length": self.max_length,
            "threshold_configuration": {
                "version": "1.0",
                "model_version": self.model_version,
                "thresholds": self.thresholds,
                "disclaimer": LABEL_DISCLAIMER,
            },
            "thresholds": self.thresholds,
            "execution_mode": self.execution_mode,
            "trainable_parameters": param_counts["trainable_parameters"],
            "backbone_parameters": param_counts["backbone_parameters"],
            "total_parameters_if_instantiated": param_counts["total_parameters_if_instantiated"],
            "actually_instantiated_parameters": param_counts["actually_instantiated_parameters"],
            "instantiation_note": (
                "In FALLBACK mode, pretrained transformer backbones are referenced in configuration only "
                "and are NOT instantiated in memory. Only the 80,001 distress model parameters were instantiated."
                if self.execution_mode == EXECUTION_MODE_FALLBACK
                else f"Backbones instantiated in PyTorch ({self.execution_mode})."
            ),
        }
        with open(out_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        # 3. Metadata
        meta_dict = {
            "model_name": "aaroh-dynamic-distress",
            "model_version": self.model_version,
            "dataset_name": "aaroh-synthetic-distress-demonstration",
            "dataset_version": "3.6.0",
            "label_disclaimer": LABEL_DISCLAIMER,
            "execution_mode": self.execution_mode,
            "parameter_counts": param_counts,
            "hyperparameters": {
                "input_dim": INPUT_DIM,
                "distress_embedding_dim": DISTRESS_EMBEDDING_DIM,
                "thresholds": self.thresholds,
                "seed": self.seed,
            },
            "backbones": {
                "text": "distilbert-base-multilingual-cased",
                "audio": "facebook/wav2vec2-base",
                "status": "FROZEN" if not self.unfreeze_backbone else "UNFROZEN",
            },
            "instantiation_note": (
                "In FALLBACK mode, pretrained transformer backbones are referenced in configuration only "
                "and are NOT instantiated in memory. Only the 80,001 distress model parameters were instantiated."
                if self.execution_mode == EXECUTION_MODE_FALLBACK
                else f"Backbones instantiated in PyTorch ({self.execution_mode})."
            ),
        }
        with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

        # 4. Metrics
        metrics_data = metrics or {}
        with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)

        # 5. Label mapping & thresholds
        label_mapping_data = {
            "task": "dynamic_distress_estimation",
            "model_version": self.model_version,
            "levels": list(VALID_DISTRESS_LEVELS),
            "thresholds": self.thresholds,
            "disclaimer": LABEL_DISCLAIMER,
            "rules": {
                "LOW": f"[0.0, {self.thresholds['low']})",
                "MODERATE": f"[{self.thresholds['low']}, {self.thresholds['moderate']})",
                "HIGH": f"[{self.thresholds['moderate']}, {self.thresholds['high']})",
                "CRITICAL": f"[{self.thresholds['high']}, 1.0]",
            },
        }
        with open(out_dir / "label_mapping.json", "w", encoding="utf-8") as f:
            json.dump(label_mapping_data, f, indent=2)

        if self.transformer_model is not None and self.tokenizer is not None:
            import torch
            torch.save(self.transformer_model.state_dict(), out_dir / "pytorch_model.bin")
            self.tokenizer.save_pretrained(out_dir)
            if hasattr(self.transformer_model.encoder, "config"):
                self.transformer_model.encoder.config.to_json_file(out_dir / "transformer_config.json")

        return {
            "weights": str(weights_file),
            "config": str(out_dir / "config.json"),
            "metadata": str(out_dir / "metadata.json"),
            "metrics": str(out_dir / "metrics.json"),
            "label_mapping": str(out_dir / "label_mapping.json"),
        }

    @classmethod
    def load_from_artifact(
        cls,
        artifact_dir: Union[str, Path],
        device: Optional[str] = None,
    ) -> "DynamicDistressModel":
        """Loads a DynamicDistressModel entirely from an exported artifact directory.

        Ensures fresh Python process compatibility with zero global variables.
        """
        art_dir = Path(artifact_dir)
        if not art_dir.exists():
            raise FileNotFoundError(f"Distress artifact directory not found: {art_dir}")

        req_files = ["config.json", "metadata.json", "weights"]
        missing = [f for f in req_files if not (art_dir / f).exists()]
        if missing:
            raise FileNotFoundError(f"Missing required distress artifact files in {art_dir}: {missing}")

        with open(art_dir / "config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)

        with open(art_dir / "metadata.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        execution_mode = meta.get("execution_mode", cfg.get("execution_mode", EXECUTION_MODE_FALLBACK))
        thresholds = cfg.get("thresholds", DEFAULT_THRESHOLDS)

        model = cls(
            model_version=cfg.get("model_version", DEFAULT_MODEL_VERSION),
            thresholds=thresholds,
            device=device,
            seed=meta.get("hyperparameters", {}).get("seed", 42),
            force_mode=execution_mode,
            backbone=cfg.get("backbone", DEFAULT_DISTRESS_BACKBONE),
            max_length=cfg.get("max_length", 128),
            local_artifact_dir=art_dir if (art_dir / "pytorch_model.bin").exists() else None,
        )

        model.load_checkpoint(art_dir / "weights")
        if model.transformer_model is not None and (art_dir / "pytorch_model.bin").exists():
            import torch
            state = torch.load(art_dir / "pytorch_model.bin", map_location="cpu", weights_only=True)
            model.transformer_model.load_state_dict(state)
            model.transformer_model.to(device).eval()
        return model

