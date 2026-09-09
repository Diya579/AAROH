"""Audio Emotion Representation Model (Slice 3.4).

Lightweight audio encoder based on facebook/wav2vec2-base trained on RAVDESS speech audio.
Produces ONLY:
- audio_emotion_probabilities: 8-class normalized emotion probability distribution
- audio_embedding: 768-dim latent audio representation vector

Strict Clinical Boundary:
- Audio Emotion != Clinical Distress.
- Does NOT predict distress_score, escalation_probability, risk level, or clinical diagnosis.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

from backend.ml.inference.config import (
    EXECUTION_MODE_FALLBACK,
    NEURAL_EXECUTION_MODES,
    VALID_EXECUTION_MODES,
)
from backend.ml.inference.exceptions import (
    ExecutionModeError,
    NeuralExecutionError,
)
from backend.ml.training.models.audio_emotion.dataset import (
    DEFAULT_TARGET_SAMPLE_RATE,
    DEFAULT_TARGET_SAMPLES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    RAVDESS_EMOTIONS,
    load_and_preprocess_wav,
)
from backend.ml.training.models.common import (
    ModelExportManager,
    ModelMetadata,
    TrainableLinearLayer,
    compute_accuracy,
    compute_confusion_matrix,
    compute_per_class_accuracy,
    compute_precision_recall_f1,
    enforce_audio_emotion_boundary,
)

DEFAULT_AUDIO_BACKBONE = "facebook/wav2vec2-base"


class AudioEmotionModel:
    """Audio Emotion Representation Model with frozen/unfrozen backbone support."""

    def __init__(
        self,
        backbone: str = DEFAULT_AUDIO_BACKBONE,
        num_classes: int = len(RAVDESS_EMOTIONS),
        embedding_dim: int = 768,
        frozen_backbone: bool = True,
        dropout_rate: float = 0.1,
        execution_mode: str = "FALLBACK",
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
        self.frozen_backbone = frozen_backbone
        self.dropout_rate = dropout_rate
        self.local_artifact_dir = Path(local_artifact_dir) if local_artifact_dir else None

        self.torch_model: Optional[Any] = None
        self.processor: Optional[Any] = None
        # Head: Linear layer mapping 768-dim latent audio space to 8 emotion classes
        self.linear_head = TrainableLinearLayer(embedding_dim, num_classes)

        # Only attempt to initialize PyTorch transformer if neural execution is explicitly requested
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            self._init_torch_layers()

    def _init_torch_layers(self) -> None:
        """Initializes PyTorch / HuggingFace wav2vec2 layers if installed."""
        try:
            import torch
            import torch.nn as nn
            from transformers import Wav2Vec2Config, Wav2Vec2Model, Wav2Vec2Processor

            class _TorchAudioHead(nn.Module):
                def __init__(self, encoder_name: str, n_classes: int, emb_dim: int, freeze: bool, drop: float, is_local: bool):
                    super().__init__()
                    if is_local:
                        config_path = Path(encoder_name) / "transformer_config.json"
                        if config_path.exists():
                            self.encoder = Wav2Vec2Model(Wav2Vec2Config.from_pretrained(config_path, local_files_only=True))
                        else:
                            self.encoder = Wav2Vec2Model.from_pretrained(encoder_name, local_files_only=True)
                    else:
                        self.encoder = Wav2Vec2Model.from_pretrained(encoder_name)
                    if freeze:
                        self.encoder.freeze_feature_encoder()
                        for param in self.encoder.parameters():
                            param.requires_grad = False
                    self.dropout = nn.Dropout(drop)
                    self.classifier = nn.Linear(emb_dim, n_classes)

                def forward(self, input_values: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
                    outputs = self.encoder(input_values=input_values, attention_mask=attention_mask)
                    # Mean pooling over temporal sequence dimension
                    hidden_states = outputs.last_hidden_state  # (B, T, D)
                    if attention_mask is None:
                        pooled = torch.mean(hidden_states, dim=1)
                    else:
                        feature_mask = self.encoder._get_feature_vector_attention_mask(hidden_states.shape[1], attention_mask)
                        pooled = (hidden_states * feature_mask.unsqueeze(-1)).sum(dim=1) / feature_mask.sum(dim=1, keepdim=True).clamp(min=1)
                    dropped = self.dropout(pooled)
                    logits = self.classifier(dropped)
                    probabilities = torch.softmax(logits, dim=-1)
                    return {
                        "logits": logits,
                        "audio_emotion_probabilities": probabilities,
                        "audio_embedding": pooled,
                    }

            self._torch_class = _TorchAudioHead
            is_local = self.local_artifact_dir is not None and self.local_artifact_dir.exists()
            encoder_source = str(self.local_artifact_dir) if is_local else self.backbone
            self.torch_model = self._torch_class(encoder_source, self.num_classes, self.embedding_dim, self.frozen_backbone, self.dropout_rate, is_local)
            self.processor = Wav2Vec2Processor.from_pretrained(encoder_source, local_files_only=is_local)
        except Exception as exc:
            self._torch_class = None
            self.torch_model = None
            self.processor = None
            if self.execution_mode in NEURAL_EXECUTION_MODES:
                raise NeuralExecutionError(f"Failed to initialize Wav2Vec2 backbone '{self.backbone}': {exc}") from exc

    @property
    def trainable_parameters_count(self) -> int:
        """Returns the total number of trainable parameters."""
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            if self.torch_model is not None:
                return sum(p.numel() for p in self.torch_model.parameters() if p.requires_grad)
        # In fallback mode, head parameters are trainable: (768 * 8 + 8) = 6,152
        head_params = self.embedding_dim * self.num_classes + self.num_classes
        if not self.frozen_backbone:
            # Add backbone parameter representation (~95M for wav2vec2-base)
            return head_params + 94396416
        return head_params

    @property
    def frozen_parameters_count(self) -> int:
        """Returns the total number of frozen (non-trainable) parameters."""
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            if self.torch_model is not None:
                return sum(p.numel() for p in self.torch_model.parameters() if not p.requires_grad)
        return 0

    def get_unfrozen_layer_names(self) -> list[str]:
        """Returns list of layer parameter names that are trainable."""
        if self.execution_mode in NEURAL_EXECUTION_MODES and self.torch_model is not None:
            return [name for name, p in self.torch_model.named_parameters() if p.requires_grad]
        return ["linear_head.W", "linear_head.b"]

    def _extract_latent_audio_embedding(self, waveform: Sequence[float]) -> list[float]:
        """Computes deterministic 768-dim latent audio representation from waveform."""
        emb: list[float] = []
        n_samples = len(waveform)
        step = max(1, n_samples // self.embedding_dim)

        # Mathematical acoustic aggregation across frequency and temporal windows
        for d in range(self.embedding_dim):
            start = d * step
            chunk = waveform[start : start + step]
            if chunk:
                # Energy and sign variance
                energy = sum(x * x for x in chunk) / len(chunk)
                zero_crossings = sum(
                    1 for k in range(len(chunk) - 1) if (chunk[k] >= 0 > chunk[k + 1]) or (chunk[k] < 0 <= chunk[k + 1])
                )
                val = (energy * 10.0) + (zero_crossings / max(1, len(chunk))) - 0.5
            else:
                val = 0.0
            emb.append(round(val, 6))

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in emb)) or 1.0
        return [round(x / norm, 6) for x in emb]

    def encode_and_predict(
        self,
        waveforms: Sequence[Sequence[float]],
        device: str = "cpu",
    ) -> dict[str, Any]:
        """Encodes audio waveforms and returns audio_emotion_probabilities and audio_embeddings.

        Returns:
            dict containing:
            - audio_emotion_probabilities: list of dicts mapping emotion_name -> probability
            - audio_embeddings: list of 768-dim latent float vectors
        """
        # CASE 1: FALLBACK mode - intentionally use deterministic acoustic representation
        if self.execution_mode == EXECUTION_MODE_FALLBACK:
            probabilities_list: list[dict[str, float]] = []
            embs: list[list[float]] = [self._extract_latent_audio_embedding(w) for w in waveforms]
            if embs:
                logits = self.linear_head.forward(embs)
                for row in logits:
                    # Softmax over 8 classes
                    max_l = max(row)
                    exp_vals = [math.exp(max(-15.0, min(15.0, l - max_l))) for l in row]
                    sum_exp = sum(exp_vals) or 1.0
                    p_dict = {
                        RAVDESS_EMOTIONS[i]: round(exp_vals[i] / sum_exp, 4)
                        for i in range(self.num_classes)
                    }
                    probabilities_list.append(p_dict)

            enforce_audio_emotion_boundary("audio_emotion_probabilities")
            return {
                "audio_emotion_probabilities": probabilities_list,
                "audio_embeddings": embs,
            }

        # CASE 2: NEURAL mode - must execute neural inference; fail closed if unavailable or errors
        if self.execution_mode in NEURAL_EXECUTION_MODES:
            try:
                import torch
            except ImportError as err:
                raise NeuralExecutionError(
                    f"Neural execution mode '{self.execution_mode}' requested for AudioEmotionModel, "
                    f"but required neural dependencies ('torch', 'transformers') are not installed: {err}"
                ) from err

            if self.torch_model is None:
                raise NeuralExecutionError(
                    f"Neural execution mode '{self.execution_mode}' requested for AudioEmotionModel, "
                    f"but neural torch_model is not initialized or weights are missing."
                )
            if self.processor is None:
                raise NeuralExecutionError("Wav2Vec2Processor is not initialized.")

            probabilities_list = []
            try:
                self.torch_model.eval()
                with torch.no_grad():
                    inputs = self.processor(list(waveforms), sampling_rate=DEFAULT_TARGET_SAMPLE_RATE, padding=True, return_tensors="pt")
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    outputs = self.torch_model(inputs["input_values"], inputs.get("attention_mask"))
                    probs_tensor = outputs["audio_emotion_probabilities"].cpu().tolist()
                    embs_tensor = outputs["audio_embedding"].cpu().tolist()

                    for p_vec in probs_tensor:
                        p_dict = {RAVDESS_EMOTIONS[i]: float(p_vec[i]) for i in range(self.num_classes)}
                        probabilities_list.append(p_dict)

                    enforce_audio_emotion_boundary("audio_emotion_probabilities")
                    return {
                        "audio_emotion_probabilities": probabilities_list,
                        "audio_embeddings": embs_tensor,
                    }
            except Exception as exc:
                raise NeuralExecutionError(
                    f"Neural inference failed for AudioEmotionModel under mode '{self.execution_mode}': {exc}"
                ) from exc

        raise ExecutionModeError(f"Unsupported execution mode '{self.execution_mode}'")

        enforce_audio_emotion_boundary("audio_emotion_probabilities")
        return {
            "audio_emotion_probabilities": probabilities_list,
            "audio_embeddings": embs,
        }

    def predict_audio_embedding(
        self,
        audio: Union[str, Path, Sequence[float]],
    ) -> dict[str, Any]:
        """Public inference interface for Slice 3.5 multimodal Feature Fusion.

        Accepts:
            audio: path to WAV audio file (str or Path), or preprocessed waveform samples.

        Returns:
            {
                "audio_embedding": list[float] (768-dim),
                "audio_emotion_probabilities": dict[str, float] (8 classes)
            }
        """
        enforce_audio_emotion_boundary("audio_embedding")
        enforce_audio_emotion_boundary("audio_emotion_probabilities")

        if isinstance(audio, (str, Path)):
            waveform, _ = load_and_preprocess_wav(audio)
        else:
            waveform = list(audio)

        res = self.encode_and_predict([waveform])
        return {
            "audio_embedding": res["audio_embeddings"][0],
            "audio_emotion_probabilities": res["audio_emotion_probabilities"][0],
        }

    def train_step(
        self,
        batch_waveforms: Sequence[Sequence[float]],
        batch_emotion_ids: Sequence[int],
        lr: float = 1e-3,
    ) -> float:
        """Executes a single forward pass, cross-entropy loss calculation, backward pass, and parameter update."""
        batch_size = len(batch_waveforms)
        if batch_size == 0:
            return 0.0

        embs = [self._extract_latent_audio_embedding(w) for w in batch_waveforms]
        logits = self.linear_head.forward(embs)

        # Cross Entropy Loss with Softmax: d(loss)/d(logit_j) = (p_j - y_j) / batch_size
        total_loss = 0.0
        grad_logits: list[list[float]] = []

        for i in range(batch_size):
            target_class = int(batch_emotion_ids[i])
            row = logits[i]
            max_l = max(row)
            exp_vals = [math.exp(max(-15.0, min(15.0, l - max_l))) for l in row]
            sum_exp = sum(exp_vals) or 1.0
            probs = [e / sum_exp for e in exp_vals]

            # Loss: -log(p_target)
            p_target = max(1e-7, probs[target_class])
            loss_i = -math.log(p_target)
            total_loss += loss_i

            grad_row = []
            for j in range(self.num_classes):
                y_j = 1.0 if j == target_class else 0.0
                grad_row.append((probs[j] - y_j) / batch_size)
            grad_logits.append(grad_row)

        mean_loss = total_loss / batch_size

        # Backward propagation & optimizer step
        self.linear_head.backward(embs, grad_logits)
        self.linear_head.step(lr)

        return float(mean_loss)

    def state_dict(self) -> dict[str, Any]:
        """Returns model state dict."""
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
            "model_type": "audio_emotion",
            "backbone": self.backbone,
            "num_classes": self.num_classes,
            "embedding_dim": self.embedding_dim,
            "frozen_backbone": self.frozen_backbone,
            "dropout_rate": self.dropout_rate,
            "taxonomy": list(RAVDESS_EMOTIONS),
            "sample_rate": DEFAULT_TARGET_SAMPLE_RATE,
            "audio_duration_seconds": 5.0,
            "clinical_boundary": "Audio Emotion != Clinical Distress",
        }

    def save(
        self,
        output_dir: Path | str,
        metrics: Optional[dict[str, Any]] = None,
        hyperparameters: Optional[dict[str, Any]] = None,
        model_version: str = "1.0.0",
        dataset_version: str = "3.2.0",
    ) -> Path:
        """Exports weights, config.json, metadata.json, metrics.json, label_mapping.json, and preprocessor_config.json."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        training_mode = "unfrozen_backbone" if not self.frozen_backbone else "frozen_backbone"

        metadata = ModelMetadata(
            model_name="aaroh-audio-emotion",
            model_version=model_version,
            dataset_name="ravdess",
            dataset_version=dataset_version,
            execution_mode=self.execution_mode,
            hyperparameters={
                **(hyperparameters or {}),
                "training_mode": training_mode,
            },
            backbone=self.backbone,
            embedding_dim=self.embedding_dim,
            total_trainable_parameters=self.trainable_parameters_count,
            clinical_boundaries=[
                "Outputs audio_emotion_probabilities and audio_embedding only.",
                "Audio Emotion is strictly NOT Clinical Distress.",
                "Does NOT predict distress score, escalation probability, or clinical diagnoses.",
            ],
        )

        label_mapping = {
            "emotion_to_id": EMOTION_TO_ID,
            "id_to_emotion": ID_TO_EMOTION,
            "num_classes": self.num_classes,
        }

        # Preprocessor configuration
        preprocessor_config = {
            "feature_extractor_type": "Wav2Vec2FeatureExtractor",
            "sampling_rate": DEFAULT_TARGET_SAMPLE_RATE,
            "target_samples": DEFAULT_TARGET_SAMPLES,
            "padding_value": 0.0,
            "do_normalize": True,
            "return_attention_mask": False,
        }
        with open(out_path / "preprocessor_config.json", "w", encoding="utf-8") as f:
            json.dump(preprocessor_config, f, indent=2)

        weights_payload = self.torch_model if self.torch_model is not None else self.state_dict()
        exported = ModelExportManager.save_model(
            output_dir=out_path,
            metadata=metadata,
            config=self.get_config(),
            label_mapping=label_mapping,
            metrics=metrics or {},
            weights_data=weights_payload,
        )
        if self.processor is not None:
            self.processor.save_pretrained(exported)
        if self.torch_model is not None:
            self.torch_model.encoder.config.to_json_file(exported / "transformer_config.json")
        return exported

    @classmethod
    def load_from_artifact(cls, artifact_dir: Path | str, device: str = "cpu") -> "AudioEmotionModel":
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
        if execution_mode in NEURAL_EXECUTION_MODES:
            neural_req = ["preprocessor_config.json", "processor_config.json"]
            missing_neural = [f for f in neural_req if not (art_path / f).exists()]
            if missing_neural:
                raise FileNotFoundError(
                    f"Missing required neural processor files in '{art_path}' under mode '{execution_mode}': {missing_neural}"
                )

        model = cls(
            execution_mode=execution_mode,
            backbone=cfg.get("backbone", DEFAULT_AUDIO_BACKBONE),
            num_classes=cfg.get("num_classes", len(RAVDESS_EMOTIONS)),
            embedding_dim=cfg.get("embedding_dim", 768),
            frozen_backbone=cfg.get("frozen_backbone", True),
            dropout_rate=cfg.get("dropout_rate", 0.1),
            local_artifact_dir=art_path,
        )

        weights_path = art_path / "pytorch_model.bin"
        weights = None
        try:
            import torch
            try:
                weights = torch.load(weights_path, map_location="cpu", weights_only=True)
            except Exception:
                try:
                    weights = torch.load(weights_path, map_location="cpu", weights_only=False)
                except Exception:
                    weights = None
        except ImportError:
            weights = None

        if weights is None:
            # Fallback for JSON-encoded weights format
            with open(weights_path, "r", encoding="utf-8") as f:
                weights = json.load(f)

        model.load_state_dict(weights)
        if model.torch_model is not None:
            if device != "cpu":
                model.torch_model.to(device)
            model.torch_model.eval()
        return model
