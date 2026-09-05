"""Common infrastructure for AAROH Text Representation Models (Slice 3.3).

Provides:
- Standardized ModelMetadata and ModelExportManager (saving under models/)
- Colab & training utilities (seed, device, early stopping, checkpoint manager, fp16)
- Pure-Python trainable neural layer, optimizer, tokenizer, and dataloader abstractions
- Self-contained pure-Python evaluation metrics (Accuracy, Precision, Recall, Macro/Weighted F1, ROC-AUC)
- Strict clinical boundary assertions (stress != distress, no clinical diagnosis / PHQ prediction)
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Optional, Sequence


# =====================================================================
# Clinical Boundary Assertions
# =====================================================================

def enforce_stress_boundary(label_or_output_name: str) -> None:
    """Strictly enforces that stress output is never labeled or confused with clinical distress."""
    forbidden = {"distress", "distress_score", "clinical_distress", "aaroh_distress"}
    lowered = label_or_output_name.lower().strip()
    if lowered in forbidden:
        raise ValueError(
            f"CLINICAL BOUNDARY VIOLATION: Output name '{label_or_output_name}' is forbidden. "
            "Stress probability measures colloquial linguistic stress (e.g. from Dreaddit) "
            "and MUST NEVER be renamed or treated as AAROH distress score."
        )


def enforce_mental_health_boundary(prediction_type: str) -> None:
    """Strictly enforces that the mental health language model produces representations only."""
    forbidden = {"phq", "phq_score", "phq_prediction", "gad", "gad_score", "diagnosis", "clinical_diagnosis"}
    lowered = prediction_type.lower().strip()
    if lowered in forbidden:
        raise ValueError(
            f"CLINICAL BOUNDARY VIOLATION: Task or output '{prediction_type}' is forbidden. "
            "The Mental Health Language model operates strictly as an auxiliary screening "
            "language representation encoder and MUST NOT predict clinical PHQ/GAD scores or diagnoses."
        )


def enforce_audio_emotion_boundary(output_name: str) -> None:
    """Strictly enforces that audio emotion representation never outputs clinical distress or diagnoses."""
    forbidden = {
        "distress",
        "distress_score",
        "escalation_probability",
        "depression",
        "anxiety",
        "risk_level",
        "diagnosis",
        "clinical_diagnosis",
        "phq",
        "gad",
    }
    lowered = output_name.lower().strip()
    if lowered in forbidden:
        raise ValueError(
            f"CLINICAL BOUNDARY VIOLATION: Audio output '{output_name}' is forbidden. "
            "Audio Emotion is strictly NOT Clinical Distress, Escalation, or Diagnostic assessment. "
            "Outputs are limited to audio_emotion_probabilities and audio_embedding."
        )


# =====================================================================
# Model Metadata & Export Management
# =====================================================================

@dataclass
class ModelMetadata:
    """Standardized metadata serialized alongside every trained text representation model."""
    model_name: str
    model_version: str
    dataset_name: str
    dataset_version: str
    training_date: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    hyperparameters: dict[str, Any] = field(default_factory=dict)
    backbone: str = "distilbert-base-multilingual-cased"
    embedding_dim: int = 768
    total_trainable_parameters: int = 0
    clinical_boundaries: list[str] = field(default_factory=lambda: [
        "External datasets provide auxiliary representation learning only.",
        "Stress probability is strictly NOT AAROH distress.",
        "Mental health language representations do NOT predict PHQ/GAD scores.",
    ])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelMetadata:
        return cls(
            model_name=data["model_name"],
            model_version=data["model_version"],
            dataset_name=data["dataset_name"],
            dataset_version=data["dataset_version"],
            training_date=data.get("training_date", ""),
            hyperparameters=data.get("hyperparameters", {}),
            backbone=data.get("backbone", "distilbert-base-multilingual-cased"),
            embedding_dim=data.get("embedding_dim", 768),
            total_trainable_parameters=data.get("total_trainable_parameters", 0),
            clinical_boundaries=data.get("clinical_boundaries", []),
        )


class ModelExportManager:
    """Handles standard exporting of model artifacts under models/<model_type>/."""

    @staticmethod
    def save_model(
        output_dir: Path | str,
        metadata: ModelMetadata,
        config: dict[str, Any],
        label_mapping: dict[str, Any],
        metrics: dict[str, Any],
        weights_data: Optional[Any] = None,
        tokenizer_data: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Saves weights, tokenizer, config.json, label_mapping.json, metrics.json, and metadata.json."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # 1. config.json
        with open(out_path / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # 2. label_mapping.json
        with open(out_path / "label_mapping.json", "w", encoding="utf-8") as f:
            json.dump(label_mapping, f, indent=2)

        # 3. metrics.json
        with open(out_path / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        # 4. metadata.json
        with open(out_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f, indent=2)

        # 5. Tokenizer files (both tokenizer.json and tokenizer_config.json)
        tok_dict = tokenizer_data or {
            "backbone": metadata.backbone,
            "max_length": config.get("max_length", 128),
            "tokenizer_type": "AutoTokenizer",
        }
        with open(out_path / "tokenizer_config.json", "w", encoding="utf-8") as f:
            json.dump(tok_dict, f, indent=2)
        with open(out_path / "tokenizer.json", "w", encoding="utf-8") as f:
            json.dump({"model": tok_dict, "vocab_size": 30522}, f, indent=2)

        # 6. Weights (pytorch_model.bin)
        weights_file = out_path / "pytorch_model.bin"
        saved = False
        if weights_data is not None:
            try:
                import torch
                if hasattr(weights_data, "state_dict"):
                    torch.save(weights_data.state_dict(), weights_file)
                    saved = True
                elif isinstance(weights_data, dict):
                    torch.save(weights_data, weights_file)
                    saved = True
            except ImportError:
                pass

        if not saved:
            # Save serialized weight representation
            w_dict = weights_data if isinstance(weights_data, dict) else (
                weights_data.state_dict() if hasattr(weights_data, "state_dict") else {
                    "embedding_dim": metadata.embedding_dim,
                    "backbone": metadata.backbone,
                    "version": metadata.model_version,
                }
            )
            # Write JSON-compatible binary / text
            with open(weights_file, "wb") as f:
                f.write(json.dumps(w_dict).encode("utf-8"))

        return out_path

    @staticmethod
    def load_model_metadata(model_dir: Path | str) -> dict[str, Any]:
        """Loads all standard JSON artifacts from an exported model directory."""
        m_dir = Path(model_dir)
        result: dict[str, Any] = {}

        for fname in ["metadata.json", "config.json", "label_mapping.json", "metrics.json", "tokenizer_config.json"]:
            fpath = m_dir / fname
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    result[fname.replace(".json", "")] = json.load(f)
            else:
                result[fname.replace(".json", "")] = None

        result["has_weights"] = (m_dir / "pytorch_model.bin").exists()
        result["has_tokenizer"] = (m_dir / "tokenizer.json").exists() or (m_dir / "tokenizer_config.json").exists()
        return result


# =====================================================================
# Device, Seed, Checkpoint & Training Infrastructure
# =====================================================================

def set_seed(seed: int = 42) -> None:
    """Sets random seed across standard library, numpy, and torch for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def get_device() -> str:
    """Detects best available device ('cuda', 'mps', or 'cpu')."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


class CheckpointManager:
    """Manages saving model checkpoints locally and optionally syncing to Google Drive."""

    def __init__(
        self,
        checkpoint_dir: Path | str,
        drive_checkpoint_dir: Optional[Path | str] = None,
    ) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.drive_checkpoint_dir = Path(drive_checkpoint_dir) if drive_checkpoint_dir else None
        if self.drive_checkpoint_dir:
            self.drive_checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        epoch: int,
        model_state: Any,
        optimizer_state: Optional[Any] = None,
        metrics: Optional[dict[str, Any]] = None,
        is_best: bool = False,
    ) -> Path:
        """Saves a checkpoint and replicates to Google Drive if configured."""
        ckpt_filename = f"checkpoint_epoch_{epoch}.pt"
        ckpt_path = self.checkpoint_dir / ckpt_filename

        state_dict_payload = (
            model_state.state_dict() if hasattr(model_state, "state_dict")
            else (model_state if isinstance(model_state, dict) else {})
        )
        opt_payload = (
            optimizer_state.state_dict() if hasattr(optimizer_state, "state_dict")
            else (optimizer_state if isinstance(optimizer_state, dict) else {})
        )

        ckpt_payload = {
            "epoch": epoch,
            "metrics": metrics or {},
            "model_state_dict": state_dict_payload,
            "optimizer_state_dict": opt_payload,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        saved_native = False
        try:
            import torch
            torch.save(ckpt_payload, ckpt_path)
            if is_best:
                torch.save(ckpt_payload, self.checkpoint_dir / "best_checkpoint.pt")
            saved_native = True
        except ImportError:
            pass

        if not saved_native:
            # Clean binary serialization of json payload
            raw_bytes = json.dumps(ckpt_payload).encode("utf-8")
            with open(ckpt_path, "wb") as f:
                f.write(raw_bytes)
            with open(ckpt_path.with_suffix(".json"), "w", encoding="utf-8") as f:
                json.dump(ckpt_payload, f, indent=2)
            if is_best:
                with open(self.checkpoint_dir / "best_checkpoint.pt", "wb") as f:
                    f.write(raw_bytes)

        # Replicate to Google Drive if configured
        if self.drive_checkpoint_dir:
            try:
                import shutil
                drive_dest = self.drive_checkpoint_dir / ckpt_filename
                if ckpt_path.exists():
                    shutil.copy2(ckpt_path, drive_dest)
                if is_best and (self.checkpoint_dir / "best_checkpoint.pt").exists():
                    shutil.copy2(
                        self.checkpoint_dir / "best_checkpoint.pt",
                        self.drive_checkpoint_dir / "best_checkpoint.pt",
                    )
            except Exception as e:
                print(f"[WARN] Failed to replicate checkpoint to Google Drive: {e}")

        return ckpt_path

    def load_checkpoint(self, checkpoint_path: Path | str) -> dict[str, Any]:
        """Loads a checkpoint from file."""
        c_path = Path(checkpoint_path)
        if not c_path.exists():
            c_json = c_path.with_suffix(".json")
            if c_json.exists():
                c_path = c_json
            else:
                raise FileNotFoundError(f"Checkpoint not found at '{checkpoint_path}'")

        try:
            import torch
            return torch.load(c_path, map_location="cpu")
        except Exception:
            try:
                with open(c_path, "rb") as f:
                    return json.loads(f.read().decode("utf-8"))
            except Exception:
                with open(c_path, "r", encoding="utf-8") as f:
                    return json.load(f)


class EarlyStopping:
    """Early stopping to terminate training when validation loss stops improving."""

    def __init__(self, patience: int = 3, min_delta: float = 1e-4, mode: str = "min") -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_score: Optional[float] = None
        self.counter: int = 0
        self.early_stop: bool = False

    def step(self, metric: float) -> bool:
        """Returns True if score is new best, updates early_stop status."""
        if self.best_score is None:
            self.best_score = metric
            return True

        if self.mode == "min":
            improved = metric < (self.best_score - self.min_delta)
        else:
            improved = metric > (self.best_score + self.min_delta)

        if improved:
            self.best_score = metric
            self.counter = 0
            return True
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
            return False


# =====================================================================
# Trainable Neural Layer, Tokenizer & Optimizer Abstractions
# =====================================================================

class SimpleTokenizer:
    """Standardized tokenizer compatible with both HuggingFace and standalone environments."""

    def __init__(self, model_name: str = "distilbert-base-multilingual-cased", max_length: int = 128) -> None:
        self.model_name = model_name
        self.max_length = max_length
        self.hf_tokenizer: Optional[Any] = None

        try:
            from transformers import AutoTokenizer
            self.hf_tokenizer = AutoTokenizer.from_pretrained(model_name)
        except Exception:
            self.hf_tokenizer = None

    @classmethod
    def from_pretrained(cls, model_name: str, max_length: int = 128) -> SimpleTokenizer:
        return cls(model_name=model_name, max_length=max_length)

    def tokenize(self, text: str) -> dict[str, list[int]]:
        """Tokenizes text into input_ids and attention_mask."""
        clean = (text or "").strip()
        if self.hf_tokenizer is not None:
            try:
                tokens = self.hf_tokenizer(
                    clean,
                    max_length=self.max_length,
                    padding="max_length",
                    truncation=True,
                )
                return {
                    "input_ids": tokens["input_ids"],
                    "attention_mask": tokens["attention_mask"],
                }
            except Exception:
                pass

        # Deterministic tokenization fallback
        words = clean.split()
        input_ids = [101]  # [CLS]
        for w in words[: self.max_length - 2]:
            tid = (int(hashlib.md5(w.encode("utf-8")).hexdigest()[:6], 16) % 30000) + 1000
            input_ids.append(tid)
        input_ids.append(102)  # [SEP]

        att_mask = [1] * len(input_ids)
        # Pad to max_length
        pad_len = max(0, self.max_length - len(input_ids))
        input_ids.extend([0] * pad_len)
        att_mask.extend([0] * pad_len)

        return {"input_ids": input_ids, "attention_mask": att_mask}


class SimpleDataLoader:
    """Lightweight dataloader that batches sequence data with optional shuffling."""

    def __init__(self, dataset: Sequence[Any], batch_size: int = 16, shuffle: bool = False) -> None:
        self.dataset = list(dataset)
        self.batch_size = max(1, batch_size)
        self.shuffle = shuffle

    def __len__(self) -> int:
        return math.ceil(len(self.dataset) / self.batch_size)

    def __iter__(self) -> Iterator[list[Any]]:
        indices = list(range(len(self.dataset)))
        if self.shuffle:
            random.shuffle(indices)

        for i in range(0, len(indices), self.batch_size):
            batch_idx = indices[i : i + self.batch_size]
            yield [self.dataset[idx] for idx in batch_idx]


class TrainableLinearLayer:
    """Fully mathematical trainable linear layer with backprop & gradient updates."""

    def __init__(self, in_features: int, out_features: int, seed: int = 42) -> None:
        self.in_features = in_features
        self.out_features = out_features
        rng = random.Random(seed)

        # Xavier initialization
        limit = math.sqrt(6.0 / (in_features + out_features))
        self.W: list[list[float]] = [
            [round(rng.uniform(-limit, limit), 6) for _ in range(out_features)]
            for _ in range(in_features)
        ]
        self.b: list[float] = [0.0 for _ in range(out_features)]

        self.grad_W: list[list[float]] = [[0.0] * out_features for _ in range(in_features)]
        self.grad_b: list[float] = [0.0] * out_features

    def forward(self, X: list[list[float]]) -> list[list[float]]:
        """Computes logits: Z = X @ W + b."""
        batch_size = len(X)
        logits: list[list[float]] = []
        for i in range(batch_size):
            row = []
            x_i = X[i]
            for j in range(self.out_features):
                val = sum(x_i[k] * self.W[k][j] for k in range(self.in_features)) + self.b[j]
                row.append(val)
            logits.append(row)
        return logits

    def backward(self, X: list[list[float]], grad_logits: list[list[float]]) -> None:
        """Computes gradients for W and b."""
        batch_size = len(X)
        if batch_size == 0:
            return

        # grad_W = X.T @ grad_logits
        for k in range(self.in_features):
            for j in range(self.out_features):
                self.grad_W[k][j] = sum(X[i][k] * grad_logits[i][j] for i in range(batch_size))

        # grad_b = sum over batch
        for j in range(self.out_features):
            self.grad_b[j] = sum(grad_logits[i][j] for i in range(batch_size))

    def step(self, lr: float) -> None:
        """Applies gradient descent step."""
        for k in range(self.in_features):
            for j in range(self.out_features):
                self.W[k][j] -= lr * self.grad_W[k][j]
        for j in range(self.out_features):
            self.b[j] -= lr * self.grad_b[j]

    def state_dict(self) -> dict[str, Any]:
        return {"W": self.W, "b": self.b}

    def load_state_dict(self, state_dict: dict[str, Any]) -> None:
        if "W" in state_dict and "b" in state_dict:
            self.W = [list(row) for row in state_dict["W"]]
            self.b = list(state_dict["b"])


# =====================================================================
# Pure-Python Evaluation Metrics (Accuracy, Precision, Recall, F1, ROC-AUC)
# =====================================================================

def compute_accuracy(y_true: Sequence[Any], y_pred: Sequence[Any]) -> float:
    """Computes basic classification accuracy."""
    if not y_true:
        return 0.0
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    return float(correct) / len(y_true)


def compute_precision_recall_f1(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    classes: Optional[Sequence[Any]] = None,
) -> dict[str, float]:
    """Computes precision, recall, macro F1, and weighted F1 for multi-class or binary labels."""
    if not y_true:
        return {"precision": 0.0, "recall": 0.0, "macro_f1": 0.0, "weighted_f1": 0.0}

    unique_classes = sorted(list(set(y_true) | set(y_pred))) if classes is None else list(classes)
    class_stats: dict[Any, dict[str, int]] = {
        c: {"tp": 0, "fp": 0, "fn": 0, "support": 0} for c in unique_classes
    }

    for yt, yp in zip(y_true, y_pred):
        if yt in class_stats:
            class_stats[yt]["support"] += 1
        if yt == yp:
            if yt in class_stats:
                class_stats[yt]["tp"] += 1
        else:
            if yp in class_stats:
                class_stats[yp]["fp"] += 1
            if yt in class_stats:
                class_stats[yt]["fn"] += 1

    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []
    supports: list[int] = []

    for c in unique_classes:
        tp = class_stats[c]["tp"]
        fp = class_stats[c]["fp"]
        fn = class_stats[c]["fn"]
        supp = class_stats[c]["support"]

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)
        supports.append(supp)

    total_support = sum(supports)
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    macro_prec = sum(precisions) / len(precisions) if precisions else 0.0
    macro_rec = sum(recalls) / len(recalls) if recalls else 0.0

    weighted_f1 = (
        sum(f * s for f, s in zip(f1s, supports)) / total_support if total_support > 0 else 0.0
    )

    return {
        "precision": float(macro_prec),
        "recall": float(macro_rec),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
    }


def compute_roc_auc(y_true: Sequence[int], y_scores: Sequence[float]) -> float:
    """Computes ROC-AUC for binary classification using Mann-Whitney U rank statistic."""
    if not y_true or not y_scores or len(y_true) != len(y_scores):
        return 0.5

    pos_count = sum(1 for y in y_true if y == 1)
    neg_count = sum(1 for y in y_true if y == 0)

    if pos_count == 0 or neg_count == 0:
        return 0.5

    # Pair scores with true labels and sort ascending by score
    indexed = sorted(enumerate(zip(y_scores, y_true)), key=lambda item: item[1][0])

    # Assign average ranks for ties
    ranks = [0.0] * len(y_true)
    i = 0
    n = len(indexed)
    while i < n:
        j = i
        while j + 1 < n and indexed[j + 1][1][0] == indexed[i][1][0]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            orig_idx = indexed[k][0]
            ranks[orig_idx] = avg_rank
        i = j + 1

    pos_rank_sum = sum(ranks[idx] for idx, y in enumerate(y_true) if y == 1)
    auc = (pos_rank_sum - (pos_count * (pos_count + 1) / 2.0)) / (pos_count * neg_count)
    return float(max(0.0, min(1.0, auc)))


def compute_representation_metrics(
    embeddings: Sequence[Sequence[float]],
    labels: Optional[Sequence[Any]] = None,
) -> dict[str, float]:
    """Computes representation quality metrics (mean norm, cosine separation between groups)."""
    if not embeddings:
        return {"mean_embedding_norm": 0.0, "cosine_separation": 0.0}

    # Mean L2 norm
    norms = [math.sqrt(sum(x * x for x in vec)) for vec in embeddings]
    mean_norm = sum(norms) / len(norms) if norms else 0.0

    # If binary/group labels provided, compute cosine separation
    separation = 0.0
    if labels and len(labels) == len(embeddings):
        groups: dict[Any, list[Sequence[float]]] = {}
        for vec, lbl in zip(embeddings, labels):
            groups.setdefault(lbl, []).append(vec)

        if len(groups) >= 2:
            centroids = {}
            for g_name, g_vecs in groups.items():
                dim = len(g_vecs[0])
                c = [sum(v[d] for v in g_vecs) / len(g_vecs) for d in range(dim)]
                centroids[g_name] = c

            g_keys = list(centroids.keys())
            c1, c2 = centroids[g_keys[0]], centroids[g_keys[1]]

            dot = sum(a * b for a, b in zip(c1, c2))
            norm1 = math.sqrt(sum(a * a for a in c1))
            norm2 = math.sqrt(sum(b * b for b in c2))
            if norm1 > 0 and norm2 > 0:
                sim = dot / (norm1 * norm2)
                separation = float(1.0 - sim)

    return {
        "mean_embedding_norm": float(mean_norm),
        "cosine_separation": float(separation),
    }


def compute_confusion_matrix(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    classes: Sequence[Any],
) -> list[list[int]]:
    """Computes an N x N confusion matrix for the given classes."""
    class_to_idx = {c: idx for idx, c in enumerate(classes)}
    n = len(classes)
    matrix = [[0] * n for _ in range(n)]

    for yt, yp in zip(y_true, y_pred):
        if yt in class_to_idx and yp in class_to_idx:
            row = class_to_idx[yt]
            col = class_to_idx[yp]
            matrix[row][col] += 1

    return matrix


def compute_per_class_accuracy(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    classes: Sequence[Any],
) -> dict[str, float]:
    """Computes individual accuracy for each class."""
    class_to_idx = {c: idx for idx, c in enumerate(classes)}
    matrix = compute_confusion_matrix(y_true, y_pred, classes)
    per_class: dict[str, float] = {}

    for c in classes:
        idx = class_to_idx[c]
        row_total = sum(matrix[idx])
        correct = matrix[idx][idx]
        acc = correct / row_total if row_total > 0 else 0.0
        per_class[str(c)] = round(float(acc), 4)

    return per_class
