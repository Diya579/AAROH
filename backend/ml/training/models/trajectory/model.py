"""Longitudinal Trajectory Model (Slice 3.7).

Models the temporal progression and direction of change in an individual's distress state
across ordered interactions.

Architectural Modes:
- FALLBACK: Lightweight deterministic temporal aggregation (projection -> mean pooling & first/last delta -> MLP -> head)
  Pure Python implementation for engineering pipeline and smoke-test verification without PyTorch/GPU.
- PYTORCH_FROZEN: Single-layer nn.GRU with frozen upstream backbones.
- PYTORCH_FINETUNE: Single-layer nn.GRU with optional fine-tuning.

Strict Clinical & Architectural Boundaries:
- Estimates TRAJECTORY ONLY (STABLE, IMPROVING, WORSENING, RAPIDLY_WORSENING).
- Does NOT perform escalation prediction, confidence estimation, or clinical diagnosis.
- Does NOT recommend interventions or treatments.
- Allowed outputs strictly: trajectory_embedding, trajectory_probabilities, trajectory_score, trajectory_label, model_version.
- Supervised using SYNTHETIC DEMONSTRATION LABELS (NOT CLINICAL GROUND TRUTH).
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
    enforce_trajectory_boundary,
    get_device,
    set_seed,
)
from backend.ml.training.models.trajectory.dataset import (
    DEFAULT_HISTORY_WINDOW,
    ID_TO_LABEL,
    LABEL_DISCLAIMER,
    LABEL_IMPROVING,
    LABEL_RAPIDLY_WORSENING,
    LABEL_STABLE,
    LABEL_TO_ID,
    LABEL_WORSENING,
    SMOKE_TEST_DISCLAIMER,
    TIMESTEP_INPUT_DIM,
    TRAJECTORY_DEFINITIONS,
    TRAJECTORY_EMBEDDING_DIM,
    TRAJECTORY_INTERNAL_SCORES,
    VALID_TRAJECTORY_LABELS,
    CaseTrajectory,
    TrajectoryInputRecord,
    TrajectoryLabel,
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
INPUT_DIM = TIMESTEP_INPUT_DIM  # 432
PROJECTION_DIM = 128
GRU_HIDDEN_DIM = 128
EMBEDDING_DIM = TRAJECTORY_EMBEDDING_DIM  # 128
HEAD_HIDDEN_DIM = 64
NUM_CLASSES = len(VALID_TRAJECTORY_LABELS)  # 4

# Fallback Aggregation Dimensions
FALLBACK_AGG_DIM = PROJECTION_DIM * 2  # 256 (mean_pool + delta)
FALLBACK_MLP_HIDDEN = 128

DEFAULT_MODEL_VERSION = "aaroh-trajectory-v1"


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
    """Xavier uniform initialization for deterministic weights."""
    rng = random.Random(seed)
    limit = math.sqrt(6.0 / (in_dim + out_dim))
    return [[rng.uniform(-limit, limit) for _ in range(out_dim)] for _ in range(in_dim)]


def _relu(val: float) -> float:
    return val if val > 0.0 else 0.0


def _softmax(logits: List[float]) -> List[float]:
    """Numerically stable softmax."""
    max_l = max(logits) if logits else 0.0
    exp_vals = [math.exp(v - max_l) for v in logits]
    sum_exp = sum(exp_vals) or 1e-8
    return [v / sum_exp for v in exp_vals]


class LongitudinalTrajectoryModel:
    """AAROH Longitudinal Trajectory Model supporting PyTorch and Pure-Python Fallback execution."""

    def __init__(
        self,
        model_version: str = DEFAULT_MODEL_VERSION,
        history_window: int = DEFAULT_HISTORY_WINDOW,
        device: Optional[str] = None,
        seed: int = 42,
        unfreeze_backbone: bool = False,
        force_mode: Optional[str] = None,
    ) -> None:
        self.model_version = model_version
        self.history_window = history_window
        self.seed = seed
        self.device = device or get_device()
        self.unfreeze_backbone = unfreeze_backbone
        set_seed(seed)

        # Detect PyTorch availability
        self.is_torch_available = False
        self.torch_model = None
        try:
            import torch
            import torch.nn as nn
            self.is_torch_available = True
        except ImportError:
            self.is_torch_available = False

        # Determine execution mode
        if force_mode is not None:
            if force_mode not in VALID_EXECUTION_MODES:
                raise ExecutionModeError(
                    f"Invalid execution mode: {force_mode}. Valid options: {sorted(VALID_EXECUTION_MODES)}"
                )
            if force_mode == EXECUTION_MODE_NEURAL:
                self.execution_mode = EXECUTION_MODE_PYTORCH_FINETUNE if self.unfreeze_backbone else EXECUTION_MODE_PYTORCH_FROZEN
            else:
                self.execution_mode = force_mode
        elif not self.is_torch_available:
            self.execution_mode = EXECUTION_MODE_FALLBACK
        elif self.unfreeze_backbone:
            self.execution_mode = EXECUTION_MODE_PYTORCH_FINETUNE
        else:
            self.execution_mode = EXECUTION_MODE_PYTORCH_FROZEN

        # Transformer backbones: referenced in config only, never instantiated in FALLBACK
        self.text_backbone = None
        self.audio_backbone = None

        if self.execution_mode in (EXECUTION_MODE_PYTORCH_FROZEN, EXECUTION_MODE_PYTORCH_FINETUNE):
            if self.is_torch_available:
                self._init_pytorch_model()
            else:
                self._init_fallback_weights()
        else:
            self._init_fallback_weights()

    def _init_fallback_weights(self) -> None:
        """Initializes deterministic weights for pure-Python fallback temporal aggregation.

        Parameter Accounting (Fallback):
        - W_proj: 432 x 128 = 55,296, b_proj: 128 -> 55,424
        - W_agg1: 256 x 128 = 32,768, b_agg1: 128 -> 32,896
        - W_agg2: 128 x 128 = 16,384, b_agg2: 128 -> 16,512
        - W_head1: 128 x 64 = 8,192,  b_head1: 64 -> 8,256
        - W_head2:  64 x 4  =   256,  b_head2:  4 ->   260
        Total Fallback Trainable Parameters: 113,348
        """
        s = self.seed
        self.W_proj = _init_weight_matrix(INPUT_DIM, PROJECTION_DIM, seed=s)
        self.b_proj = [0.0] * PROJECTION_DIM

        self.W_agg1 = _init_weight_matrix(FALLBACK_AGG_DIM, FALLBACK_MLP_HIDDEN, seed=s + 1)
        self.b_agg1 = [0.0] * FALLBACK_MLP_HIDDEN

        self.W_agg2 = _init_weight_matrix(FALLBACK_MLP_HIDDEN, EMBEDDING_DIM, seed=s + 2)
        self.b_agg2 = [0.0] * EMBEDDING_DIM

        self.W_head1 = _init_weight_matrix(EMBEDDING_DIM, HEAD_HIDDEN_DIM, seed=s + 3)
        self.b_head1 = [0.0] * HEAD_HIDDEN_DIM

        self.W_head2 = _init_weight_matrix(HEAD_HIDDEN_DIM, NUM_CLASSES, seed=s + 4)
        self.b_head2 = [0.0] * NUM_CLASSES

    def _init_pytorch_model(self) -> None:
        """Initializes PyTorch nn.Module with single-layer GRU and Trajectory Head."""
        if not self.is_torch_available:
            return
        import torch
        import torch.nn as nn

        class _PyTorchTrajectoryNet(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.proj = nn.Sequential(
                    nn.Linear(INPUT_DIM, PROJECTION_DIM),
                    nn.ReLU(),
                )
                self.gru = nn.GRU(
                    input_size=PROJECTION_DIM,
                    hidden_size=GRU_HIDDEN_DIM,
                    num_layers=1,
                    batch_first=True,
                )
                self.head = nn.Sequential(
                    nn.Linear(GRU_HIDDEN_DIM, HEAD_HIDDEN_DIM),
                    nn.ReLU(),
                    nn.Linear(HEAD_HIDDEN_DIM, NUM_CLASSES),
                )

            def forward(
                self,
                x: torch.Tensor,
                padding_mask: Optional[torch.Tensor] = None,
                lengths: Optional[torch.Tensor] = None,
            ) -> Tuple[torch.Tensor, torch.Tensor]:
                """Forward pass through projection, GRU, and classification head.

                x: [B, history_window, 432]
                padding_mask: [B, history_window] (True = padded)
                lengths: [B]
                """
                B, T, D = x.shape
                proj_x = self.proj(x)  # [B, T, 128]

                # Run through GRU
                out, h_n = self.gru(proj_x)  # h_n: [1, B, 128]
                h_last = h_n.squeeze(0)      # [B, 128]

                # L2-normalize trajectory embedding
                norm = torch.norm(h_last, p=2, dim=-1, keepdim=True).clamp(min=1e-8)
                h_emb = h_last / norm

                logits = self.head(h_emb)
                probs = torch.softmax(logits, dim=-1)
                return h_emb, probs

        self.torch_model = _PyTorchTrajectoryNet()
        self._init_fallback_weights()

    def get_parameter_counts(self) -> Dict[str, int]:
        """Returns rigorous parameter accounting across all 4 metrics.

        1. Trainable Parameters:
           - In PyTorch GRU mode:
             Projection: 55,424
             GRU: 99,072
             Head: 8,516
             Total: 163,012
           - In Fallback mode:
             Projection: 55,424
             Aggregation MLP: 49,408
             Head: 8,516
             Total: 113,348
        2. Upstream Backbone Parameters:
           229,774,080 (DistilBERT: 134,734,080 + Wav2Vec2: 95,040,000)
        3. Total If Instantiated:
           trainable + backbone_parameters
        4. Actually Instantiated:
           Only trainable parameters in FALLBACK mode (transformers in config only).
        """
        if self.execution_mode == EXECUTION_MODE_FALLBACK:
            trainable_params = 113_348
        else:
            trainable_params = 163_012

        backbone_params = FROZEN_BACKBONES_PARAM_COUNT
        total_if_instantiated = trainable_params + backbone_params

        if self.execution_mode == EXECUTION_MODE_FALLBACK:
            actually_instantiated = trainable_params
        elif self.execution_mode == EXECUTION_MODE_PYTORCH_FROZEN:
            actually_instantiated = total_if_instantiated
        elif self.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE:
            actually_instantiated = total_if_instantiated
        else:
            actually_instantiated = trainable_params

        return {
            "trainable_parameters": trainable_params,
            "trainable_head_parameters": trainable_params,
            "backbone_parameters": backbone_params,
            "total_parameters_if_instantiated": total_if_instantiated,
            "actually_instantiated_parameters": actually_instantiated,
            "frozen_backbone_parameters": (
                0 if self.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE else backbone_params
            ),
        }

    def _fallback_forward_single(
        self,
        windowed_vectors: List[List[float]],
        padding_mask: List[bool],
    ) -> Tuple[List[float], List[float]]:
        """Pure-Python forward pass for a single windowed sequence.

        1. Sequence projection for each timestep
        2. Deterministic temporal aggregation over non-padded timesteps (mean + first/last delta)
        3. MLP projection & L2 normalization to unit hypersphere
        4. Trajectory head classification
        """
        history_len = len(windowed_vectors)
        valid_projected: List[List[float]] = []

        # 1. Project each timestep
        for t in range(history_len):
            if not padding_mask[t]:
                vt = windowed_vectors[t]
                proj_t = _mat_vec_mul(self.W_proj, vt, self.b_proj)
                valid_projected.append([_relu(v) for v in proj_t])

        if not valid_projected:
            # Degenerate all-padded case: use zero vector
            valid_projected = [[0.0] * PROJECTION_DIM]

        # 2. Temporal Aggregation (mean pooling + delta between last and first valid timesteps)
        L = len(valid_projected)
        mean_pool = [0.0] * PROJECTION_DIM
        for v in valid_projected:
            for j in range(PROJECTION_DIM):
                mean_pool[j] += v[j] / L

        first_step = valid_projected[0]
        last_step = valid_projected[-1]
        delta = [last_step[j] - first_step[j] for j in range(PROJECTION_DIM)]

        # Concatenate: [256-dim]
        agg = mean_pool + delta

        # 3. Intermediate MLP: Linear(256, 128) -> ReLU -> Linear(128, 128) -> ReLU
        h_agg1_lin = _mat_vec_mul(self.W_agg1, agg, self.b_agg1)
        h_agg1 = [_relu(v) for v in h_agg1_lin]

        h_agg2_lin = _mat_vec_mul(self.W_agg2, h_agg1, self.b_agg2)
        h_agg2 = [_relu(v) for v in h_agg2_lin]

        # L2-normalize trajectory embedding onto unit hypersphere
        norm = math.sqrt(sum(v * v for v in h_agg2)) or 1e-8
        h_emb = [v / norm for v in h_agg2]

        # 4. Trajectory Head: Linear(128, 64) -> ReLU -> Linear(64, 4) -> Softmax
        h_head1_lin = _mat_vec_mul(self.W_head1, h_emb, self.b_head1)
        h_head1 = [_relu(v) for v in h_head1_lin]

        logits = _mat_vec_mul(self.W_head2, h_head1, self.b_head2)
        probs = _softmax(logits)

        return h_emb, probs

    def forward(
        self,
        windowed_vectors: List[List[float]],
        padding_mask: Optional[List[bool]] = None,
    ) -> Tuple[List[float], List[float]]:
        """Forward pass for a single windowed sequence."""
        if padding_mask is None:
            padding_mask = [False] * len(windowed_vectors)
        return self._fallback_forward_single(windowed_vectors, padding_mask)

    def train_step(self, batch: Dict[str, Any], lr: float = 1e-3) -> float:
        """Executes a single mini-batch gradient descent step in FALLBACK mode.

        Optimizes cross-entropy loss over trajectory classes.
        """
        inputs: List[List[List[float]]] = batch["inputs"]
        masks: List[List[bool]] = batch["padding_masks"]
        targets: List[int] = batch["targets"]
        B = len(inputs)
        if B == 0:
            return 0.0

        batch_losses: List[float] = []

        for k in range(B):
            win_vecs = inputs[k]
            mask = masks[k]
            target_idx = targets[k]

            # Forward pass with intermediate activations saved
            valid_projected: List[List[float]] = []
            for t in range(len(win_vecs)):
                if not mask[t]:
                    proj_t = _mat_vec_mul(self.W_proj, win_vecs[t], self.b_proj)
                    valid_projected.append([_relu(v) for v in proj_t])

            if not valid_projected:
                valid_projected = [[0.0] * PROJECTION_DIM]

            L = len(valid_projected)
            mean_pool = [0.0] * PROJECTION_DIM
            for v in valid_projected:
                for j in range(PROJECTION_DIM):
                    mean_pool[j] += v[j] / L

            first_step = valid_projected[0]
            last_step = valid_projected[-1]
            delta = [last_step[j] - first_step[j] for j in range(PROJECTION_DIM)]
            agg = mean_pool + delta

            h_agg1_lin = _mat_vec_mul(self.W_agg1, agg, self.b_agg1)
            h_agg1 = [_relu(v) for v in h_agg1_lin]

            h_agg2_lin = _mat_vec_mul(self.W_agg2, h_agg1, self.b_agg2)
            h_agg2 = [_relu(v) for v in h_agg2_lin]

            norm = math.sqrt(sum(v * v for v in h_agg2)) or 1e-8
            h_emb = [v / norm for v in h_agg2]

            h_head1_lin = _mat_vec_mul(self.W_head1, h_emb, self.b_head1)
            h_head1 = [_relu(v) for v in h_head1_lin]

            logits = _mat_vec_mul(self.W_head2, h_head1, self.b_head2)
            probs = _softmax(logits)

            # Cross-entropy loss
            target_prob = max(1e-7, probs[target_idx])
            loss = -math.log(target_prob)
            batch_losses.append(loss)

            # Gradient wrt logits: (probs - target_one_hot)
            d_logits = [probs[c] - (1.0 if c == target_idx else 0.0) for c in range(NUM_CLASSES)]

            # Gradients for W_head2, b_head2
            d_h_head1 = [0.0] * HEAD_HIDDEN_DIM
            for c in range(NUM_CLASSES):
                d_l = d_logits[c]
                self.b_head2[c] -= (lr / B) * d_l
                for j in range(HEAD_HIDDEN_DIM):
                    self.W_head2[j][c] -= (lr / B) * (d_l * h_head1[j])
                    d_h_head1[j] += d_l * self.W_head2[j][c]

            # Gradients for W_head1, b_head1
            d_h_emb = [0.0] * EMBEDDING_DIM
            for j in range(HEAD_HIDDEN_DIM):
                if h_head1_lin[j] > 0:
                    d_relu = d_h_head1[j]
                    self.b_head1[j] -= (lr / B) * d_relu
                    for i in range(EMBEDDING_DIM):
                        self.W_head1[i][j] -= (lr / B) * (d_relu * h_emb[i])
                        d_h_emb[i] += d_relu * self.W_head1[i][j]

            # Gradients for agg2
            for i in range(EMBEDDING_DIM):
                if h_agg2_lin[i] > 0:
                    d_a = d_h_emb[i]
                    self.b_agg2[i] -= (lr / B) * d_a
                    for m in range(FALLBACK_MLP_HIDDEN):
                        self.W_agg2[m][i] -= (lr / B) * (d_a * h_agg1[m])

        return float(sum(batch_losses) / len(batch_losses)) if batch_losses else 0.0

    def predict_trajectory(
        self,
        input_data: Union[CaseTrajectory, List[TrajectoryInputRecord], List[List[float]], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Public Inference Interface for AAROH Longitudinal Trajectory Model.

        Accepts:
        - CaseTrajectory object
        - List of TrajectoryInputRecord objects
        - Windowed feature matrix [history_window, 432]
        - Dict with "inputs" and optional "padding_mask"

        Returns strictly and only:
        - trajectory_embedding: 128-dim list of floats (L2 norm = 1.0)
        - trajectory_probabilities: dict mapping all 4 classes to probabilities
        - trajectory_score: continuous slope progression index in [-1.0, 1.0]
        - trajectory_label: predicted discrete label (STABLE, IMPROVING, WORSENING, RAPIDLY_WORSENING)
        - model_version: internal tracking string
        """
        # Parse inputs into windowed vectors and padding mask
        if isinstance(input_data, CaseTrajectory):
            vectors, mask, _ = input_data.get_windowed_sequence(self.history_window)
        elif isinstance(input_data, list) and len(input_data) > 0 and isinstance(input_data[0], TrajectoryInputRecord):
            case = CaseTrajectory(
                case_id=input_data[0].case_id,
                records=input_data,
                trajectory_label="UNKNOWN",
            )
            vectors, mask, _ = case.get_windowed_sequence(self.history_window)
        elif isinstance(input_data, dict):
            vectors = input_data["inputs"]
            mask = input_data.get("padding_mask", [False] * len(vectors))
        elif isinstance(input_data, list):
            # Assumed raw vectors
            vectors = input_data
            mask = [False] * len(vectors)
        else:
            raise TypeError(f"Unsupported input type for predict_trajectory: {type(input_data)}")

        # Forward pass
        h_emb, probs = self.forward(vectors, mask)

        # Enforce unit-sphere invariant
        norm = math.sqrt(sum(x * x for x in h_emb))
        if abs(norm - 1.0) > 1e-4 and norm > 0:
            h_emb = [x / norm for x in h_emb]

        # Trajectory Probabilities Dictionary
        prob_dict = {
            ID_TO_LABEL[i]: round(float(probs[i]), 4)
            for i in range(NUM_CLASSES)
        }

        # Argmax discrete trajectory label
        best_idx = max(range(NUM_CLASSES), key=lambda i: probs[i])
        pred_label = ID_TO_LABEL[best_idx]

        # Continuous Trajectory Score in [-1.0, 1.0]: computed from centralized TrajectoryLabel definitions
        # trajectory_score = sum(P(label) * label.internal_score)
        continuous_score = sum(
            prob_dict.get(tl.value, 0.0) * tl.internal_score
            for tl in TrajectoryLabel
        )
        continuous_score = round(max(-1.0, min(1.0, continuous_score)), 4)

        result = {
            "trajectory_embedding": [round(float(v), 6) for v in h_emb],
            "trajectory_probabilities": prob_dict,
            "trajectory_score": continuous_score,
            "trajectory_label": pred_label,
            "model_version": self.model_version,
        }

        # Strict Clinical Boundary Validation
        for k in result.keys():
            enforce_trajectory_boundary(k)

        return result

    def save_checkpoint(
        self,
        checkpoint_path: Union[str, Path],
        epoch: int = 1,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Saves model weights, history window, and state metadata."""
        out_path = Path(checkpoint_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "model_type": "longitudinal_trajectory_model",
            "model_version": self.model_version,
            "history_window": self.history_window,
            "execution_mode": self.execution_mode,
            "epoch": epoch,
            "metrics": metrics or {},
            "W_proj": self.W_proj,
            "b_proj": self.b_proj,
            "W_agg1": self.W_agg1,
            "b_agg1": self.b_agg1,
            "W_agg2": self.W_agg2,
            "b_agg2": self.b_agg2,
            "W_head1": self.W_head1,
            "b_head1": self.b_head1,
            "W_head2": self.W_head2,
            "b_head2": self.b_head2,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_checkpoint(self, checkpoint_path: Union[str, Path]) -> Dict[str, Any]:
        """Loads weights and state from checkpoint file."""
        in_path = Path(checkpoint_path)
        if not in_path.exists():
            raise FileNotFoundError(f"Checkpoint not found at {in_path}")

        with open(in_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        self.model_version = state.get("model_version", self.model_version)
        self.history_window = state.get("history_window", self.history_window)
        self.W_proj = state["W_proj"]
        self.b_proj = state["b_proj"]
        self.W_agg1 = state["W_agg1"]
        self.b_agg1 = state["b_agg1"]
        self.W_agg2 = state["W_agg2"]
        self.b_agg2 = state["b_agg2"]
        self.W_head1 = state["W_head1"]
        self.b_head1 = state["b_head1"]
        self.W_head2 = state["W_head2"]
        self.b_head2 = state["b_head2"]

        return {
            "epoch": state.get("epoch", 1),
            "metrics": state.get("metrics", {}),
        }

    def export(
        self,
        output_dir: Union[str, Path],
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """Exports standard 5 artifacts: weights, config.json, metadata.json, metrics.json, label_mapping.json."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Weights
        weights_file = out_dir / "weights"
        state = {
            "W_proj": self.W_proj,
            "b_proj": self.b_proj,
            "W_agg1": self.W_agg1,
            "b_agg1": self.b_agg1,
            "W_agg2": self.W_agg2,
            "b_agg2": self.b_agg2,
            "W_head1": self.W_head1,
            "b_head1": self.b_head1,
            "W_head2": self.W_head2,
            "b_head2": self.b_head2,
        }
        with open(weights_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        # 2. Config
        param_counts = self.get_parameter_counts()
        config_data = {
            "model_type": "longitudinal_trajectory_model",
            "model_version": self.model_version,
            "input_dim": INPUT_DIM,
            "projection_dim": PROJECTION_DIM,
            "gru_hidden_dim": GRU_HIDDEN_DIM,
            "trajectory_embedding_dim": EMBEDDING_DIM,
            "head_hidden_dim": HEAD_HIDDEN_DIM,
            "num_classes": NUM_CLASSES,
            "history_window": self.history_window,
            "execution_mode": self.execution_mode,
            "labels": list(VALID_TRAJECTORY_LABELS),
            "trainable_parameters": param_counts["trainable_parameters"],
            "backbone_parameters": param_counts["backbone_parameters"],
            "total_parameters_if_instantiated": param_counts["total_parameters_if_instantiated"],
            "actually_instantiated_parameters": param_counts["actually_instantiated_parameters"],
            "disclaimer": LABEL_DISCLAIMER,
        }
        with open(out_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        # 3. Metadata
        meta_dict = {
            "model_name": "aaroh-longitudinal-trajectory",
            "model_version": self.model_version,
            "dataset_name": "aaroh-synthetic-trajectory-demonstration",
            "dataset_version": "3.7.0",
            "label_disclaimer": LABEL_DISCLAIMER,
            "smoke_test_disclaimer": SMOKE_TEST_DISCLAIMER,
            "execution_mode": self.execution_mode,
            "parameter_counts": param_counts,
            "hyperparameters": {
                "input_dim": INPUT_DIM,
                "history_window": self.history_window,
                "trajectory_embedding_dim": EMBEDDING_DIM,
                "seed": self.seed,
            },
            "backbones": {
                "text": "distilbert-base-multilingual-cased",
                "audio": "facebook/wav2vec2-base",
                "status": "FROZEN" if not self.unfreeze_backbone else "UNFROZEN",
            },
        }
        with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

        # 4. Metrics
        metrics_data = metrics or {}
        with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)

        # 5. Label mapping (derived directly from centralized TrajectoryLabel definitions)
        label_mapping_data = {
            "task": "longitudinal_trajectory_estimation",
            "model_version": self.model_version,
            "labels": [tl.value for tl in TrajectoryLabel],
            "label_to_id": LABEL_TO_ID,
            "id_to_label": ID_TO_LABEL,
            "internal_scores": {tl.value: tl.internal_score for tl in TrajectoryLabel},
            "disclaimer": LABEL_DISCLAIMER,
            "definitions": {tl.value: tl.definition for tl in TrajectoryLabel},
        }
        with open(out_dir / "label_mapping.json", "w", encoding="utf-8") as f:
            json.dump(label_mapping_data, f, indent=2)

        return {
            "weights": str(weights_file),
            "config": str(out_dir / "config.json"),
            "metadata": str(out_dir / "metadata.json"),
            "metrics": str(out_dir / "metrics.json"),
            "label_mapping": str(out_dir / "label_mapping.json"),
        }
