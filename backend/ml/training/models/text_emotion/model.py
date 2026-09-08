"""Text Emotion Model architecture (Slice 3.3).

Lightweight multilingual HuggingFace model trained on GoEmotions + EmoHinD.
Produces:
- emotion_probabilities: 28-class normalized emotion probability vector
- emotion_embedding: Latent representation vector (e.g. 768-dim)

Strict Boundary:
- Outputs emotion representations only.
- Does NOT predict AAROH clinical distress or risk level.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from backend.ml.inference.config import (
    EXECUTION_MODE_FALLBACK,
    EXECUTION_MODE_PYTORCH_FROZEN,
    EXECUTION_MODE_PYTORCH_FINETUNE,
    NEURAL_EXECUTION_MODES,
    VALID_EXECUTION_MODES,
)
from backend.ml.inference.exceptions import (
    ExecutionModeError,
    NeuralExecutionError,
)
from backend.ml.training.models.common import (
    ModelExportManager,
    ModelMetadata,
    TrainableLinearLayer,
    compute_accuracy,
    compute_precision_recall_f1,
)
from backend.ml.training.models.text_emotion.dataset import (
    GOEMOTIONS_TAXONOMY,
    ID_TO_LABEL,
    LABEL_TO_ID,
)

DEFAULT_TEXT_EMOTION_BACKBONE = "distilbert-base-multilingual-cased"


class TextEmotionModel:
    """Lightweight text emotion encoder & multi-label classifier."""

    def __init__(
        self,
        backbone: str = DEFAULT_TEXT_EMOTION_BACKBONE,
        num_classes: int = len(GOEMOTIONS_TAXONOMY),
        embedding_dim: int = 768,
        max_length: int = 128,
        dropout_rate: float = 0.2,
        execution_mode: str = "FALLBACK",
        unfreeze_layers: int = 2,
        local_artifact_dir: Optional[Path | str] = None,
    ) -> None:
        if execution_mode not in VALID_EXECUTION_MODES:
            raise ExecutionModeError(
                f"Invalid execution mode '{execution_mode}'. Must be one of {sorted(VALID_EXECUTION_MODES)}"
            )
        self.execution_mode = execution_mode
        self.backbone = backbone
        self.num_classes = num_classes
        self.embedding_dim = embedding_dim
        self.max_length = max_length
        self.dropout_rate = dropout_rate
        self.unfreeze_layers = unfreeze_layers
        self.local_artifact_dir = Path(local_artifact_dir) if local_artifact_dir else None

        self.torch_model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.linear_head = TrainableLinearLayer(embedding_dim, num_classes)

        # Only attempt to initialize PyTorch transformer if neural execution is explicitly requested
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            self._init_torch_layers(self.local_artifact_dir)

    def _init_torch_layers(self, local_artifact_dir: Optional[Path] = None) -> None:
        """Initializes PyTorch layers and tokenizer if available."""
        try:
            import torch
            import torch.nn as nn
            from transformers import AutoConfig, AutoModel, AutoTokenizer

            class _TorchEmotionHead(nn.Module):
                def __init__(
                    self,
                    encoder_name_or_path: str,
                    n_classes: int,
                    emb_dim: int,
                    drop: float,
                    is_local: bool = False,
                ):
                    super().__init__()
                    if is_local:
                        cfg_file = Path(encoder_name_or_path) / "transformer_config.json"
                        if cfg_file.exists():
                            cfg = AutoConfig.from_pretrained(str(cfg_file), local_files_only=True)
                            self.encoder = AutoModel.from_config(cfg)
                        else:
                            self.encoder = AutoModel.from_pretrained(
                                encoder_name_or_path, local_files_only=True, attn_implementation="eager"
                            )
                    else:
                        self.encoder = AutoModel.from_pretrained(encoder_name_or_path, attn_implementation="eager")
                    self.dropout = nn.Dropout(drop)
                    self.classifier = nn.Linear(emb_dim, n_classes)

                def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor):
                    outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                    last_hidden_state = outputs.last_hidden_state
                    mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
                    sum_embeddings = torch.sum(last_hidden_state * mask_expanded, 1)
                    sum_mask = mask_expanded.sum(1).clamp(min=1e-9)
                    pooled = sum_embeddings / sum_mask

                    dropped = self.dropout(pooled)
                    logits = self.classifier(dropped)
                    probabilities = torch.sigmoid(logits)
                    return {
                        "logits": logits,
                        "emotion_probabilities": probabilities,
                        "emotion_embedding": pooled,
                    }

            self._torch_class = _TorchEmotionHead
            is_local = local_artifact_dir is not None and local_artifact_dir.exists()
            encoder_source = str(local_artifact_dir) if is_local else self.backbone

            self.torch_model = self._torch_class(
                encoder_name_or_path=encoder_source,
                n_classes=self.num_classes,
                emb_dim=self.embedding_dim,
                drop=self.dropout_rate,
                is_local=is_local,
            )
            if is_local:
                self.tokenizer = AutoTokenizer.from_pretrained(str(local_artifact_dir), local_files_only=True)
            else:
                self.tokenizer = AutoTokenizer.from_pretrained(self.backbone)

            if self.execution_mode == EXECUTION_MODE_PYTORCH_FROZEN:
                for p in self.torch_model.encoder.parameters():
                    p.requires_grad = False
            elif self.execution_mode == EXECUTION_MODE_PYTORCH_FINETUNE:
                # Freeze lower transformer layers and unfreeze upper layers
                for p in self.torch_model.encoder.parameters():
                    p.requires_grad = False
                if hasattr(self.torch_model.encoder, "transformer") and hasattr(
                    self.torch_model.encoder.transformer, "layer"
                ):
                    layers = self.torch_model.encoder.transformer.layer
                    n_unfreeze = max(0, min(len(layers), self.unfreeze_layers))
                    for layer in layers[-n_unfreeze:]:
                        for p in layer.parameters():
                            p.requires_grad = True
        except Exception as exc:
            self._torch_class = None
            self.torch_model = None
            self.tokenizer = None
            if self.execution_mode in NEURAL_EXECUTION_MODES:
                raise NeuralExecutionError(
                    f"Failed to initialize PyTorch transformer backbone '{self.backbone}' "
                    f"under mode '{self.execution_mode}': {exc}"
                ) from exc

    @property
    def trainable_parameters_count(self) -> int:
        """Returns total trainable parameter count."""
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            if self.torch_model is not None:
                return sum(p.numel() for p in self.torch_model.parameters() if p.requires_grad)
        return self.embedding_dim * self.num_classes + self.num_classes

    @property
    def frozen_parameters_count(self) -> int:
        """Returns total frozen parameter count."""
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            if self.torch_model is not None:
                return sum(p.numel() for p in self.torch_model.parameters() if not p.requires_grad)
        return 0

    def get_unfrozen_layer_names(self) -> list[str]:
        """Returns list of layer parameter names that are trainable."""
        if self.execution_mode in NEURAL_EXECUTION_MODES and self.torch_model is not None:
            return [name for name, p in self.torch_model.named_parameters() if p.requires_grad]
        return ["linear_head.W", "linear_head.b"]

    def _extract_latent_embeddings(self, texts: Sequence[str]) -> list[list[float]]:
        """Computes deterministic latent representation embeddings for texts."""
        embeddings_list: list[list[float]] = []
        for text in texts:
            clean_text = (text or "").strip().lower()
            emb: list[float] = []
            for dim in range(self.embedding_dim):
                h = hashlib.md5(f"emo_{clean_text}_{dim}".encode("utf-8")).hexdigest()
                val = (int(h[:6], 16) / 0xFFFFFF) * 2.0 - 1.0
                emb.append(round(val, 5))

            norm = math.sqrt(sum(x * x for x in emb)) or 1.0
            embeddings_list.append([round(x / norm, 5) for x in emb])
        return embeddings_list

    def encode_and_predict(
        self,
        texts: Sequence[str],
        device: str = "cpu",
        batch_size: int = 16,
    ) -> dict[str, Any]:
        """Encodes texts and returns emotion probabilities and emotion embeddings using memory-safe batched inference."""
        # CASE 1: FALLBACK mode - intentionally use deterministic representation
        if self.execution_mode == EXECUTION_MODE_FALLBACK:
            probabilities_list: list[dict[str, float]] = []
            embs = self._extract_latent_embeddings(texts)
            if embs:
                logits = self.linear_head.forward(embs)
                for row in logits:
                    prob_dict: dict[str, float] = {}
                    for i, logit_val in enumerate(row):
                        p = 1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, logit_val))))
                        prob_dict[GOEMOTIONS_TAXONOMY[i]] = round(p, 4)
                    probabilities_list.append(prob_dict)

            return {
                "emotion_probabilities": probabilities_list,
                "emotion_embeddings": embs,
            }

        # CASE 2: NEURAL mode - must execute neural inference; fail closed if unavailable or errors
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            try:
                import torch
                from transformers import AutoModel, AutoTokenizer
            except ImportError as err:
                raise NeuralExecutionError(
                    f"Neural execution mode '{self.execution_mode}' requested for TextEmotionModel, "
                    f"but required neural dependencies ('torch', 'transformers') are not installed: {err}"
                ) from err

            if self.torch_model is None or self.tokenizer is None:
                raise NeuralExecutionError(
                    f"Neural execution mode '{self.execution_mode}' requested for TextEmotionModel, "
                    f"but neural torch_model or tokenizer is not initialized or weights are missing."
                )

            probabilities_list = []
            embeddings_list = []
            safe_bs = max(1, int(batch_size))
            text_list = list(texts)

            try:
                self.torch_model.eval()
                with torch.no_grad():
                    for start_idx in range(0, len(text_list), safe_bs):
                        batch_slice = text_list[start_idx : start_idx + safe_bs]
                        if not batch_slice:
                            continue

                        inputs = self.tokenizer(
                            batch_slice,
                            padding=True,
                            truncation=True,
                            max_length=self.max_length,
                            return_tensors="pt",
                        ).to(device)

                        outputs = self.torch_model(
                            input_ids=inputs["input_ids"],
                            attention_mask=inputs["attention_mask"],
                        )
                        probs_tensor = outputs["emotion_probabilities"].detach().cpu().tolist()
                        embs_tensor = outputs["emotion_embedding"].detach().cpu().tolist()

                        for probs_vec in probs_tensor:
                            probs_dict = {
                                GOEMOTIONS_TAXONOMY[i]: float(probs_vec[i])
                                for i in range(len(GOEMOTIONS_TAXONOMY))
                            }
                            probabilities_list.append(probs_dict)
                        embeddings_list.extend(embs_tensor)

                    return {
                        "emotion_probabilities": probabilities_list,
                        "emotion_embeddings": embeddings_list,
                    }
            except Exception as exc:
                raise NeuralExecutionError(
                    f"Neural inference failed for TextEmotionModel under mode '{self.execution_mode}': {exc}"
                ) from exc

        raise ExecutionModeError(f"Unsupported execution mode '{self.execution_mode}'")

    def train_step(
        self,
        batch_texts: Sequence[str],
        batch_label_vecs: Sequence[Sequence[float]],
        lr: float = 1e-3,
    ) -> float:
        """Executes a single forward, loss, backward, and optimizer step."""
        batch_size = len(batch_texts)
        if batch_size == 0:
            return 0.0

        embs = self._extract_latent_embeddings(batch_texts)
        logits = self.linear_head.forward(embs)

        # Multi-label Binary Cross Entropy Loss
        total_loss = 0.0
        grad_logits: list[list[float]] = []

        for i in range(batch_size):
            grad_row: list[float] = []
            for j in range(self.num_classes):
                # Sigmoid
                p = 1.0 / (1.0 + math.exp(-max(-15.0, min(15.0, logits[i][j]))))
                p = max(1e-7, min(1.0 - 1e-7, p))
                y = batch_label_vecs[i][j]
                bce = -(y * math.log(p) + (1.0 - y) * math.log(1.0 - p))
                total_loss += bce

                # Gradient of BCE w.r.t logit: p - y
                grad_row.append((p - y) / (batch_size * self.num_classes))
            grad_logits.append(grad_row)

        mean_loss = total_loss / (batch_size * self.num_classes)

        # Backward pass & optimizer step
        self.linear_head.backward(embs, grad_logits)
        self.linear_head.step(lr)

        return float(mean_loss)

    def state_dict(self) -> dict[str, Any]:
        """Returns model weights state dict."""
        if self.execution_mode in NEURAL_EXECUTION_MODES and self.torch_model is not None:
            return self.torch_model.state_dict()
        return self.linear_head.state_dict()

    def load_state_dict(self, state_dict: dict[str, Any]) -> None:
        """Loads weights from state dict."""
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            if self.torch_model is None:
                raise NeuralExecutionError(
                    "Cannot load neural weights: torch_model is not initialized."
                )
            self.torch_model.load_state_dict(state_dict)
            return

        # FALLBACK mode
        if "W" in state_dict and "b" in state_dict:
            self.linear_head.load_state_dict(state_dict)
        else:
            raise ExecutionModeError(
                "Provided state_dict does not contain linear head weights ('W', 'b') for FALLBACK mode."
            )

    def get_config(self) -> dict[str, Any]:
        """Returns serializable architecture configuration."""
        return {
            "model_type": "text_emotion",
            "backbone": self.backbone,
            "num_classes": self.num_classes,
            "embedding_dim": self.embedding_dim,
            "max_length": self.max_length,
            "dropout_rate": self.dropout_rate,
            "unfreeze_layers": getattr(self, "unfreeze_layers", 2),
            "taxonomy": list(GOEMOTIONS_TAXONOMY),
        }

    def save(
        self,
        output_dir: Path | str,
        metrics: Optional[dict[str, Any]] = None,
        hyperparameters: Optional[dict[str, Any]] = None,
        model_version: str = "1.0.0",
        dataset_version: str = "3.2.0",
    ) -> Path:
        """Exports model weights, config, label mappings, metrics, and metadata."""
        metadata = ModelMetadata(
            model_name="aaroh-text-emotion",
            model_version=model_version,
            dataset_name="goemotions_and_emohind",
            dataset_version=dataset_version,
            execution_mode=self.execution_mode,
            hyperparameters=hyperparameters or {},
            backbone=self.backbone,
            embedding_dim=self.embedding_dim,
            total_trainable_parameters=self.trainable_parameters_count,
            total_frozen_parameters=self.frozen_parameters_count,
            unfrozen_layers=self.get_unfrozen_layer_names(),
            clinical_boundaries=[
                "Outputs emotion probabilities and embeddings only.",
                "Does NOT predict AAROH clinical distress score.",
            ],
        )

        label_mapping = {
            "label_to_id": LABEL_TO_ID,
            "id_to_label": ID_TO_LABEL,
            "num_classes": self.num_classes,
        }

        weights_payload = self.torch_model if self.torch_model is not None else self.state_dict()
        out_p = ModelExportManager.save_model(
            output_dir=output_dir,
            metadata=metadata,
            config=self.get_config(),
            label_mapping=label_mapping,
            metrics=metrics or {},
            weights_data=weights_payload,
        )
        if self.tokenizer is not None and hasattr(self.tokenizer, "save_pretrained"):
            try:
                self.tokenizer.save_pretrained(out_p)
            except Exception:
                pass
        if self.torch_model is not None and hasattr(self.torch_model, "encoder") and hasattr(self.torch_model.encoder, "config"):
            try:
                self.torch_model.encoder.config.to_json_file(out_p / "transformer_config.json")
            except Exception:
                pass
        return out_p

    @classmethod
    def load_from_artifact(cls, artifact_dir: Path | str) -> "TextEmotionModel":
        """Loads a model directly from a self-contained artifact directory offline."""
        art_path = Path(artifact_dir)
        if not art_path.exists():
            raise FileNotFoundError(f"Artifact directory not found: {art_path}")

        req_files = ["config.json", "metadata.json", "pytorch_model.bin", "label_mapping.json"]
        missing = [f for f in req_files if not (art_path / f).exists()]
        if missing:
            raise FileNotFoundError(f"Missing required artifact files in {art_path}: {missing}")

        with open(art_path / "config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        with open(art_path / "metadata.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        execution_mode = meta.get("execution_mode", EXECUTION_MODE_FALLBACK)
        model = cls(
            execution_mode=execution_mode,
            backbone=cfg.get("backbone", DEFAULT_TEXT_EMOTION_BACKBONE),
            num_classes=cfg.get("num_classes", len(GOEMOTIONS_TAXONOMY)),
            embedding_dim=cfg.get("embedding_dim", 768),
            max_length=cfg.get("max_length", 128),
            dropout_rate=cfg.get("dropout_rate", 0.2),
            unfreeze_layers=cfg.get("unfreeze_layers", 2),
            local_artifact_dir=art_path,
        )

        weights_path = art_path / "pytorch_model.bin"
        import torch
        weights = torch.load(weights_path, map_location="cpu")
        model.load_state_dict(weights)
        if model.torch_model is not None:
            model.torch_model.eval()
        return model

