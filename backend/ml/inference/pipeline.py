"""End-to-End ML Inference Pipeline Orchestrator (Slice 3.9).

Wires Slices 3.1–3.8 into a single deterministic inference pipeline producing
the official MlInferenceResult contract.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import random
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from backend.ml.contract import (
    DistressOutput,
    ExplanationOutput,
    MlInferenceResult,
    ModelOutput,
    PredictionOutput,
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
    abstained_result,
    failed_result,
    insufficient_data_result,
)
from backend.ml.features.assembly import MLInput
from backend.ml.inference.cache import InferenceCache
from backend.ml.inference.config import (
    EXECUTION_MODE_FALLBACK,
    NEURAL_EXECUTION_MODES,
    VALID_EXECUTION_MODES,
    PipelineConfig,
    _UNSET,
    is_execution_mode_compatible,
)
from backend.ml.inference.exceptions import (
    ArtifactNotFoundError,
    ExecutionModeError,
    InferencePipelineError,
    InvalidInputError,
    ModelLoadError,
    NeuralExecutionError,
    PipelineExecutionError,
    VersionMismatchError,
)
from backend.ml.inference.registry import (
    DEFAULT_MODEL_VERSIONS,
    MODEL_DIRECTORIES,
    ModelRegistry,
)
from backend.ml.inference.runner import (
    PipelineLogger,
    StageTimer,
    validate_audio_stage,
    validate_distress_stage,
    validate_escalation_stage,
    validate_fusion_stage,
    validate_text_stage,
    validate_trajectory_stage,
)
from backend.ml.training.models.audio_emotion.model import AudioEmotionModel
from backend.ml.training.models.distress.dataset import (
    BEHAVIOURAL_COUNT,
    ENGAGEMENT_COUNT,
    DistressInputRecord,
)
from backend.ml.training.models.distress.model import DynamicDistressModel
from backend.ml.training.models.escalation.dataset import EscalationInputRecord
from backend.ml.training.models.escalation.model import EscalationAssessmentModel
from backend.ml.training.models.fusion.dataset import MultimodalInputRecord
from backend.ml.training.models.fusion.model import MultimodalFusionModel
from backend.ml.training.models.text_emotion.model import TextEmotionModel
from backend.ml.training.models.trajectory.dataset import TrajectoryInputRecord
from backend.ml.training.models.trajectory.model import LongitudinalTrajectoryModel

logger = logging.getLogger("aaroh.ml.inference")

PIPELINE_EXECUTION_ORDER = [
    "MLInput / Case History",
    "Behavioural & Engagement Feature Extraction",
    "Text Representation (TextEmotionModel)",
    "Audio Representation (AudioEmotionModel)",
    "Multimodal Feature Fusion (MultimodalFusionModel)",
    "Dynamic Distress Model (DynamicDistressModel)",
    "Longitudinal Trajectory Model (LongitudinalTrajectoryModel)",
    "Escalation Assessment Model (EscalationAssessmentModel)",
    "Grounded Explanation Forwarding",
    "MlInferenceResult Contract Assembly",
]


class MLInferencePipeline:
    """Production orchestration layer wiring Slices 3.1–3.8 into a single deterministic inference pipeline."""

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        registry: Optional[ModelRegistry] = None,
        cache: Optional[InferenceCache] = None,
        base_dir: Optional[Union[str, Path]] = None,
        execution_mode: Any = _UNSET,
    ) -> None:
        if execution_mode != _UNSET:
            if not execution_mode or execution_mode not in VALID_EXECUTION_MODES:
                raise ExecutionModeError(
                    f"Invalid execution mode '{execution_mode}'. Must be one of {sorted(VALID_EXECUTION_MODES)}"
                )
            if config is not None:
                config.default_execution_mode = execution_mode
            else:
                config = PipelineConfig(execution_mode=execution_mode)

        self.config = config or PipelineConfig()
        self.registry = registry or ModelRegistry(base_dir=base_dir)
        self.cache = cache or InferenceCache()
        self.execution_mode = self.config.default_execution_mode
        self._models_loaded: bool = False
        self._loaded_versions: Dict[str, str] = {}
        self._last_manifest: Optional[Dict[str, Any]] = None

        # Models
        self.text_model: Optional[TextEmotionModel] = None
        self.audio_model: Optional[AudioEmotionModel] = None
        self.fusion_model: Optional[MultimodalFusionModel] = None
        self.distress_model: Optional[DynamicDistressModel] = None
        self.trajectory_model: Optional[LongitudinalTrajectoryModel] = None
        self.escalation_model: Optional[EscalationAssessmentModel] = None

    @property
    def manifest(self) -> Optional[Dict[str, Any]]:
        """Returns the loaded pipeline manifest dictionary."""
        return self._last_manifest

    @classmethod
    def from_saved_models(
        cls,
        base_dir: Optional[Union[str, Path]] = None,
        config: Optional[PipelineConfig] = None,
    ) -> MLInferencePipeline:
        """Convenience factory: instantiates pipeline, points to base_dir, and loads all models."""
        pipeline = cls(config=config, base_dir=base_dir)
        pipeline.load_models()
        return pipeline

    def _set_seed(self, seed: Optional[int] = None) -> None:
        """Enforces deterministic execution across all stages."""
        s = seed if seed is not None else self.config.seed
        random.seed(s)
        try:
            import numpy as np
            np.random.seed(s)
        except ImportError:
            pass
        try:
            import torch
            torch.manual_seed(s)
        except ImportError:
            pass

    def load_models(self, base_dir: Optional[Union[str, Path]] = None) -> None:
        """Loads all exported model checkpoints from disk, verifying artifacts and versions."""
        if base_dir is not None:
            self.registry = ModelRegistry(base_dir=base_dir)

        self._set_seed()

        # Enforce valid execution mode
        if self.execution_mode not in VALID_EXECUTION_MODES:
            raise ExecutionModeError(
                f"Invalid pipeline execution mode '{self.execution_mode}'. "
                f"Must be one of {sorted(VALID_EXECUTION_MODES)}"
            )

        # Check manifest compatibility if manifest exists on disk
        manifest_file = self.registry.base_dir / "pipeline_manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                raise ModelLoadError(
                    f"Failed to read or parse pipeline manifest at '{manifest_file}': {exc}"
                ) from exc

            manifest_mode = manifest_data.get("execution_mode")
            if manifest_mode:
                if manifest_mode not in VALID_EXECUTION_MODES:
                    raise ExecutionModeError(
                        f"Pipeline manifest '{manifest_file}' has invalid execution_mode '{manifest_mode}'."
                    )
                if not is_execution_mode_compatible(self.execution_mode, manifest_mode):
                    raise ExecutionModeError(
                        f"Pipeline manifest execution_mode mismatch: runtime is configured for "
                        f"'{self.execution_mode}', but manifest specifies '{manifest_mode}'. "
                        f"Incompatible execution modes cannot proceed."
                    )

        try:
            # 1. Verify artifacts for all models first
            for key in MODEL_DIRECTORIES:
                self.registry.verify_artifacts(key)

            # 2. Text Emotion Model (Slice 3.3)
            text_dir = self.registry.get_model_path("text")
            with open(text_dir / "metadata.json", "r", encoding="utf-8") as f:
                text_meta = json.load(f)
            self.registry.validate_metadata("text", text_meta, self.execution_mode)
            self._loaded_versions["text"] = text_meta.get("model_version", "1.0.0")

            text_m = TextEmotionModel(execution_mode=self.execution_mode)
            weights_file = text_dir / "pytorch_model.bin"
            if self.execution_mode in NEURAL_EXECUTION_MODES:
                import torch
                state_dict = torch.load(weights_file, map_location="cpu", weights_only=True)
            else:
                with open(weights_file, "r", encoding="utf-8") as f:
                    state_dict = json.load(f)
            text_m.load_state_dict(state_dict)
            self.text_model = text_m
            self.cache.put("model_text", text_m)
            self.cache.put("meta_text", text_meta)

            # 3. Audio Emotion Model (Slice 3.4)
            audio_dir = self.registry.get_model_path("audio")
            with open(audio_dir / "metadata.json", "r", encoding="utf-8") as f:
                audio_meta = json.load(f)
            self.registry.validate_metadata("audio", audio_meta, self.execution_mode)
            self._loaded_versions["audio"] = audio_meta.get("model_version", "1.0.0")

            audio_m = AudioEmotionModel(execution_mode=self.execution_mode)
            audio_weights_file = audio_dir / "pytorch_model.bin"
            if self.execution_mode in NEURAL_EXECUTION_MODES:
                import torch
                audio_state_dict = torch.load(audio_weights_file, map_location="cpu", weights_only=True)
            else:
                with open(audio_weights_file, "r", encoding="utf-8") as f:
                    audio_state_dict = json.load(f)
            audio_m.load_state_dict(audio_state_dict)
            self.audio_model = audio_m
            self.cache.put("model_audio", audio_m)
            self.cache.put("meta_audio", audio_meta)

            # 4. Multimodal Fusion Model (Slice 3.5)
            fusion_dir = self.registry.get_model_path("fusion")
            with open(fusion_dir / "metadata.json", "r", encoding="utf-8") as f:
                fusion_meta = json.load(f)
            self.registry.validate_metadata("fusion", fusion_meta, self.execution_mode)
            self._loaded_versions["fusion"] = fusion_meta.get("model_version", "1.0.0")

            fusion_m = MultimodalFusionModel(seed=self.config.seed, force_mode=self.execution_mode)
            fusion_m.load_checkpoint(fusion_dir / "weights")
            self.fusion_model = fusion_m
            self.cache.put("model_fusion", fusion_m)
            self.cache.put("meta_fusion", fusion_meta)

            # 5. Dynamic Distress Model (Slice 3.6)
            distress_dir = self.registry.get_model_path("distress")
            with open(distress_dir / "metadata.json", "r", encoding="utf-8") as f:
                distress_meta = json.load(f)
            self.registry.validate_metadata("distress", distress_meta, self.execution_mode)
            self._loaded_versions["distress"] = distress_meta.get("model_version", "aaroh-distress-v1")

            distress_m = DynamicDistressModel(seed=self.config.seed, force_mode=self.execution_mode)
            distress_m.load_checkpoint(distress_dir / "weights")
            self.distress_model = distress_m
            self.cache.put("model_distress", distress_m)
            self.cache.put("meta_distress", distress_meta)

            # 6. Longitudinal Trajectory Model (Slice 3.7)
            traj_dir = self.registry.get_model_path("trajectory")
            with open(traj_dir / "metadata.json", "r", encoding="utf-8") as f:
                traj_meta = json.load(f)
            self.registry.validate_metadata("trajectory", traj_meta, self.execution_mode)
            self._loaded_versions["trajectory"] = traj_meta.get("model_version", "aaroh-trajectory-v1")

            traj_m = LongitudinalTrajectoryModel(seed=self.config.seed, force_mode=self.execution_mode)
            traj_m.load_checkpoint(traj_dir / "weights")
            self.trajectory_model = traj_m
            self.cache.put("model_trajectory", traj_m)
            self.cache.put("meta_trajectory", traj_meta)

            # 7. Escalation Assessment Model (Slice 3.8)
            esc_dir = self.registry.get_model_path("escalation")
            with open(esc_dir / "metadata.json", "r", encoding="utf-8") as f:
                esc_meta = json.load(f)
            self.registry.validate_metadata("escalation", esc_meta, self.execution_mode)
            self._loaded_versions["escalation"] = esc_meta.get("model_version", "aaroh-escalation-v1")

            esc_m = EscalationAssessmentModel(seed=self.config.seed)
            esc_m.load_checkpoint(esc_dir / "weights")
            self.escalation_model = esc_m
            self.cache.put("model_escalation", esc_m)
            self.cache.put("meta_escalation", esc_meta)

            self._models_loaded = True

            # Generate manifest
            if self.config.export_manifest:
                self.export_manifest()

            # Warmup if configured
            if self.config.warmup_on_load:
                self.warmup()

        except (ArtifactNotFoundError, VersionMismatchError, ExecutionModeError, NeuralExecutionError):
            self._models_loaded = False
            raise
        except Exception as exc:
            self._models_loaded = False
            raise ModelLoadError(f"Failed to load models: {exc}") from exc

    def export_manifest(
        self,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Generates and writes pipeline_manifest.json detailing versions, order, and artifact checksums."""
        manifest_dest = Path(output_path or self.config.manifest_path)
        manifest_dest.parent.mkdir(parents=True, exist_ok=True)

        artifact_checksums = self.registry.get_all_artifact_checksums()

        manifest: Dict[str, Any] = {
            "pipeline_version": self.config.pipeline_version,
            "pipeline_build": self.config.pipeline_build,
            "creation_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "execution_order": PIPELINE_EXECUTION_ORDER,
            "loaded_model_versions": dict(self._loaded_versions),
            "feature_schema_version": self.config.feature_schema_version,
            "contract_version": self.config.contract_version,
            "execution_mode": self.execution_mode,
            "pipeline_config": self.config.to_dict(),
            "artifact_checksums": artifact_checksums,
            "compatibility_information": {
                "python_runtime": ">=3.9",
                "framework_independent": True,
                "fallback_mode_supported": True,
                "upstream_slices_compatible": ["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8"],
            },
        }

        with open(manifest_dest, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        self._last_manifest = manifest
        return manifest

    def warmup(self) -> bool:
        """Pre-warms pipeline models with synthetic input to verify end-to-end execution path."""
        if not self._models_loaded:
            self.load_models()

        self._set_seed()
        try:
            # Execute dummy run
            dummy_input = {
                "case_id": "WARMUP-CASE",
                "interaction_date": datetime.date.today().isoformat(),
                "feature_values": [0.5] * 60,
                "raw_text": "I am feeling okay today",
                "raw_audio": [0.0] * 16000,
            }
            result = self._execute_pipeline(
                [self._normalize_input(dummy_input)],
                run_id="warmup_run",
                validate_stages=self.config.strict_stage_validation,
            )
            return result.status in (ProcessingStatus.SUCCESS, ProcessingStatus.LOW_CONFIDENCE)
        except Exception as exc:
            logger.warning(f"Warmup encountered an issue: {exc}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Provides structured health and readiness status."""
        text_ok = self.text_model is not None
        audio_ok = self.audio_model is not None
        fusion_ok = self.fusion_model is not None
        distress_ok = self.distress_model is not None
        trajectory_ok = self.trajectory_model is not None
        escalation_ok = self.escalation_model is not None

        all_models_ok = text_ok and audio_ok and fusion_ok and distress_ok and trajectory_ok and escalation_ok

        artifacts_ok = False
        try:
            for k in MODEL_DIRECTORIES:
                self.registry.verify_artifacts(k)
            artifacts_ok = True
        except Exception:
            artifacts_ok = False

        overall_status = "HEALTHY" if (all_models_ok and artifacts_ok) else "DEGRADED"
        if not self._models_loaded:
            overall_status = "UNINITIALIZED"

        return {
            "ready": all_models_ok and artifacts_ok,
            "overall_status": overall_status,
            "pipeline_version": self.config.pipeline_version,
            "execution_mode": self.execution_mode,
            "text_loaded": text_ok,
            "audio_loaded": audio_ok,
            "fusion_loaded": fusion_ok,
            "distress_loaded": distress_ok,
            "trajectory_loaded": trajectory_ok,
            "escalation_loaded": escalation_ok,
            "artifacts_valid": artifacts_ok,
            "versions_valid": bool(self._loaded_versions),
            "loaded_versions": dict(self._loaded_versions),
            "model_versions": dict(self._loaded_versions),
            "cache_stats": self.cache.stats,
        }

    def run(self, input_record: Union[MLInput, Mapping[str, Any]]) -> MlInferenceResult:
        """Runs inference on a single interaction record.

        Never crashes: returns structured FAILED, INSUFFICIENT_DATA, or ABSTAINED on error.
        """
        return self.run_case([input_record])

    def run_case(
        self,
        case_history: Sequence[Union[MLInput, Mapping[str, Any]]],
    ) -> MlInferenceResult:
        """Runs longitudinal inference across beneficiary's interaction history."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        logger_tracer = PipelineLogger(run_id)
        logger_tracer.log_stage("Input received")

        # Basic validation of history sequence
        if not case_history:
            return failed_result(
                case_id="UNKNOWN",
                prediction_date=datetime.date.today().isoformat(),
                message="Case history sequence is empty.",
                metadata={"pipeline_run_id": run_id},
            )

        # Parse inputs into MLInput objects
        parsed_history: List[MLInput] = []
        for idx, item in enumerate(case_history):
            try:
                parsed = self._normalize_input(item)
                parsed_history.append(parsed)
            except Exception as exc:
                return failed_result(
                    case_id="UNKNOWN",
                    prediction_date=datetime.date.today().isoformat(),
                    message=f"Invalid input record at index {idx}: {exc}",
                    metadata={"pipeline_run_id": run_id},
                )

        # Ensure chronological ordering across history
        parsed_history.sort(key=lambda x: str(x.interaction_date or ""))

        # Truncate to history window
        active_history = parsed_history[-self.config.max_history_window :]
        current_input = active_history[-1]
        case_id = current_input.case_id
        pred_date = current_input.interaction_date or datetime.date.today().isoformat()

        # Check model loading
        if not self._models_loaded:
            try:
                self.load_models()
            except (ArtifactNotFoundError, VersionMismatchError, ModelLoadError) as exc:
                return failed_result(
                    case_id=case_id,
                    prediction_date=pred_date,
                    message=f"Model loading failure: {exc}",
                    metadata={
                        "pipeline_run_id": run_id,
                        "pipeline_version": self.config.pipeline_version,
                        "execution_mode": self.execution_mode,
                    },
                )

        # Execute pipeline
        try:
            return self._execute_pipeline(
                active_history,
                run_id=run_id,
                logger_tracer=logger_tracer,
                validate_stages=self.config.strict_stage_validation,
            )
        except PipelineExecutionError as exc:
            return failed_result(
                case_id=case_id,
                prediction_date=pred_date,
                message=f"Pipeline execution failure: {exc}",
                metadata={
                    "pipeline_run_id": run_id,
                    "pipeline_version": self.config.pipeline_version,
                    "execution_mode": self.execution_mode,
                },
            )
        except Exception as exc:
            logger.exception(f"Unhandled exception during inference: {exc}")
            return failed_result(
                case_id=case_id,
                prediction_date=pred_date,
                message=f"Inference execution error: {exc}",
                metadata={
                    "pipeline_run_id": run_id,
                    "pipeline_version": self.config.pipeline_version,
                    "execution_mode": self.execution_mode,
                },
            )

    def _execute_pipeline(
        self,
        history: List[InferenceInput],
        run_id: str,
        logger_tracer: Optional[PipelineLogger] = None,
        validate_stages: bool = True,
    ) -> MlInferenceResult:
        """Internal execution method flowing through all stages."""
        self._set_seed()
        timer = StageTimer()
        timer.start_pipeline()

        current_input = history[-1]
        case_id = current_input.case_id
        pred_date = current_input.interaction_date or datetime.date.today().isoformat()

        # Evidence checks
        tabular_vals = current_input.feature_values
        valid_feature_count = sum(1 for v in tabular_vals if v is not None)
        has_text = bool(current_input.raw_text and current_input.raw_text.strip())
        has_audio = bool(
            (current_input.raw_audio and len(current_input.raw_audio) > 0)
            or bool(current_input.metadata.get("voice_available"))
        )

        # Insufficient data check: if no features and no text/audio, fail closed
        if valid_feature_count == 0 and not has_text and not has_audio:
            timer.stop_pipeline()
            return insufficient_data_result(
                case_id=case_id,
                prediction_date=pred_date,
                message="No valid features or modality inputs present in record.",
                metadata={
                    "pipeline_run_id": run_id,
                    "timing": timer.to_dict(),
                    "pipeline_version": self.config.pipeline_version,
                },
            )

        # Step 1: Text Representation (Slice 3.3)
        with timer.measure("text"):
            if has_text and self.text_model is not None:
                text_out = self.text_model.encode_and_predict([current_input.raw_text])
            else:
                # Deterministic zero embedding and uniform emotion probabilities when text absent
                text_out = {
                    "emotion_embeddings": [[0.0] * 768],
                    "emotion_probabilities": [{k: 0.0 for k in self.text_model.get_config()["taxonomy"]}] if self.text_model else [{}],
                }
        if validate_stages:
            validate_text_stage(text_out)
        if logger_tracer:
            logger_tracer.log_stage("Text complete")

        # Step 2: Audio Representation (Slice 3.4)
        with timer.measure("audio"):
            if has_audio and self.audio_model is not None:
                # Format audio waveform
                waveform = list(current_input.raw_audio) if isinstance(current_input.raw_audio, (list, tuple)) else [0.0] * 16000
                audio_out = self.audio_model.encode_and_predict([waveform])
            else:
                # Deterministic zero embedding and uniform emotion probabilities when audio absent
                audio_out = {
                    "audio_embeddings": [[0.0] * 768],
                    "audio_emotion_probabilities": [{k: 0.125 for k in ("neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprised")}],
                }
        if validate_stages:
            validate_audio_stage(audio_out)
        if logger_tracer:
            logger_tracer.log_stage("Audio complete")

        # Step 3: Multimodal Feature Fusion (Slice 3.5)
        with timer.measure("fusion"):
            mm_record = MultimodalInputRecord(
                case_id=case_id,
                interaction_date=pred_date,
                tabular_features=list(tabular_vals),
                text_response=current_input.raw_text,
                text_emotion_probabilities=text_out["emotion_probabilities"][0],
                text_emotion_embedding=text_out["emotion_embeddings"][0],
                audio_emotion_probabilities=audio_out["audio_emotion_probabilities"][0],
                audio_embedding=audio_out["audio_embeddings"][0],
            )
            assert self.fusion_model is not None
            fusion_out = self.fusion_model.fuse(mm_record)
        if validate_stages:
            validate_fusion_stage(fusion_out)
        if logger_tracer:
            logger_tracer.log_stage("Fusion complete")

        # Extract behavioral and engagement features from MLInput (indices 18-25 and 26-38)
        b_features = list(tabular_vals[18:26]) if len(tabular_vals) >= 26 else [None] * BEHAVIOURAL_COUNT
        e_features = list(tabular_vals[26:39]) if len(tabular_vals) >= 39 else [None] * ENGAGEMENT_COUNT

        # Step 4: Dynamic Distress Model (Slice 3.6)
        with timer.measure("distress"):
            distress_rec = DistressInputRecord(
                case_id=case_id,
                interaction_date=pred_date,
                fused_embedding=fusion_out["fused_embedding"],
                modality_weights=fusion_out["modality_weights"],
                behavioural_features=b_features,
                engagement_features=e_features,
            )
            assert self.distress_model is not None
            distress_out = self.distress_model.predict_distress(distress_rec)
        if validate_stages:
            validate_distress_stage(distress_out)
        if logger_tracer:
            logger_tracer.log_stage("Distress complete")

        # Step 5: Longitudinal Trajectory Model (Slice 3.7)
        with timer.measure("trajectory"):
            # Construct trajectory sequence across history window
            traj_history: List[TrajectoryInputRecord] = []
            for step_idx, step_input in enumerate(history):
                # For previous steps in history, compute lightweight distress state if needed
                step_date = step_input.interaction_date or pred_date
                step_tab = step_input.feature_values
                step_b = list(step_tab[18:26]) if len(step_tab) >= 26 else [None] * BEHAVIOURAL_COUNT
                step_e = list(step_tab[26:39]) if len(step_tab) >= 39 else [None] * ENGAGEMENT_COUNT

                # Format as numerical values + missingness masks (None != 0 preserved)
                traj_b_vals = [0.0 if v is None else float(v) for v in step_b]
                traj_b_masks = [1.0 if v is None else 0.0 for v in step_b]
                traj_b = traj_b_vals + traj_b_masks

                traj_e_vals = [0.0 if v is None else float(v) for v in step_e]
                traj_e_masks = [1.0 if v is None else 0.0 for v in step_e]
                traj_e = traj_e_vals + traj_e_masks

                # If this is current step, reuse computed outputs; otherwise reuse current representations
                fused_emb = fusion_out["fused_embedding"]
                d_emb = distress_out["distress_embedding"]
                d_score = distress_out["distress_score"]
                d_lvl = distress_out["distress_level"]

                traj_history.append(
                    TrajectoryInputRecord(
                        case_id=case_id,
                        interaction_id=f"{case_id}-{step_idx}",
                        timestamp=step_date,
                        fused_embedding=fused_emb,
                        distress_embedding=d_emb,
                        distress_score=d_score,
                        distress_level=d_lvl,
                        behavioural_features=traj_b,
                        engagement_features=traj_e,
                    )
                )

            assert self.trajectory_model is not None
            traj_out = self.trajectory_model.predict_trajectory(traj_history)
        if validate_stages:
            validate_trajectory_stage(traj_out)
        if logger_tracer:
            logger_tracer.log_stage("Trajectory complete")

        # Step 6: Escalation Assessment Model (Slice 3.8)
        with timer.measure("escalation"):
            b_dict = {
                "safety_distress": b_features[0] if len(b_features) > 0 else None,
                "sleep_disturbance": b_features[1] if len(b_features) > 1 else None,
                "fear_intensity": b_features[2] if len(b_features) > 2 else None,
                "low_social_support": b_features[3] if len(b_features) > 3 else None,
                "help_requested": b_features[4] if len(b_features) > 4 else None,
                "composite_distress": b_features[5] if len(b_features) > 5 else None,
            }
            e_dict = {
                "checkin_consistency": e_features[0] if len(e_features) > 0 else None,
                "missed_checkin_streak": e_features[1] if len(e_features) > 1 else None,
                "response_delay": e_features[2] if len(e_features) > 2 else None,
                "engagement_score": e_features[3] if len(e_features) > 3 else None,
                "engagement_drop": e_features[4] if len(e_features) > 4 else None,
            }

            esc_rec = EscalationInputRecord.from_upstream(
                case_id=case_id,
                interaction_id=f"{case_id}-current",
                timestamp=pred_date,
                distress_output=distress_out,
                trajectory_output=traj_out,
                fusion_output=fusion_out,
                behavioural_features=b_dict,
                engagement_features=e_dict,
                text_available=has_text,
                audio_available=has_audio,
                history_length=len(history),
            )
            assert self.escalation_model is not None
            esc_out = self.escalation_model.predict_escalation(esc_rec)
        if validate_stages:
            validate_escalation_stage(esc_out)
        if logger_tracer:
            logger_tracer.log_stage("Escalation complete")

        timer.stop_pipeline()

        # Step 7: Grounded Explanation Forwarding & Contract Assembly
        if logger_tracer:
            logger_tracer.log_stage("Contract generated")

        explanation_raw = esc_out["explanation"]
        explanation = ExplanationOutput(
            factors=tuple(explanation_raw.get("factors", ())),
            trend=Trajectory(explanation_raw.get("trend", traj_out["trajectory_label"])),
            baseline_deviation=explanation_raw.get("baseline_deviation"),
        )

        distress_output = DistressOutput(
            score=float(distress_out["distress_score"]),
            trajectory=Trajectory(traj_out["trajectory_label"]),
            confidence=float(esc_out["confidence"]),
            baseline_deviation=explanation_raw.get("baseline_deviation"),
        )

        model_output = ModelOutput(
            model_name="aaroh-end-to-end-pipeline",
            model_version=self.config.pipeline_version,
        )

        # Status & Source
        status = ProcessingStatus(esc_out.get("status", "SUCCESS"))
        source = ResultSource(esc_out.get("source", "ml"))

        # Pipeline Metadata packaging
        pipeline_metadata: Dict[str, Any] = {
            "pipeline_version": self.config.pipeline_version,
            "pipeline_build": self.config.pipeline_build,
            "pipeline_run_id": run_id,
            "creation_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "execution_mode": self.execution_mode,
            "feature_schema_version": self.config.feature_schema_version,
            "contract_version": self.config.contract_version,
            "loaded_models": dict(self._loaded_versions),
            "model_versions": dict(self._loaded_versions),
            "timing": timer.to_dict(),
            "pipeline_config": self.config.to_dict(),
        }

        # ---------------------------------------------------------------------
        # Downstream Deterministic Safety Override (POST-ML INFERENCE)
        # ---------------------------------------------------------------------
        # ARCHITECTURAL INVARIANT: The ML Escalation Model (Slice 3.8) strictly
        # outputs LOW, MODERATE, or HIGH. RiskLevel.EMERGENCY is NEVER an ML
        # prediction class; it is exclusively a downstream deterministic safety
        # override triggered by explicit crisis keywords to prevent patient harm.
        crisis_terms = (
            "suicide", "kill myself", "end my life", "emergency", "dying", 
            "ambulance", "call police", "jaan ka khatra", "आपातकाल", "जान का खतरा"
        )
        is_crisis = False
        if has_text and current_input.raw_text:
            text_lower = current_input.raw_text.lower()
            if any(term in text_lower for term in crisis_terms):
                is_crisis = True

        if is_crisis:
            factors_list = list(explanation.factors)
            crisis_factor = "Immediate crisis indicator detected requiring urgent escalation"
            if crisis_factor not in factors_list:
                factors_list.insert(0, crisis_factor)
            explanation = ExplanationOutput(
                factors=tuple(factors_list),
                trend=explanation.trend,
                baseline_deviation=explanation.baseline_deviation,
            )
            # CRITICAL ARCHITECTURAL REQUIREMENT:
            # Preserve the ML model's true probabilistic output and confidence.
            # Do NOT fabricate 0.99 probability or 0.99 confidence.
            # EMERGENCY is an operational safety state applied downstream.
            prob = float(esc_out.get("escalation_probability") or 0.0)
            conf = float(esc_out.get("confidence") or 0.0)
            prediction_output = PredictionOutput(
                escalation_probability=prob,
                target_horizon_days=int(esc_out.get("target_horizon_days", self.config.target_horizon_days)),
                confidence=conf,
                risk_level=RiskLevel.EMERGENCY,
            )
            pipeline_metadata["safety_override"] = True
            pipeline_metadata["safety_override_reason"] = "CRISIS_KEYWORD"
            result = MlInferenceResult(
                case_id=case_id,
                prediction_date=pred_date,
                status=ProcessingStatus.SUCCESS,
                source=ResultSource.ML,
                distress=distress_output,
                prediction=prediction_output,
                explanation=explanation,
                model=model_output,
                message="Emergency crisis safety override triggered (deterministic safety rule).",
                metadata=pipeline_metadata,
            )
        elif status == ProcessingStatus.INSUFFICIENT_DATA:
            result = insufficient_data_result(
                case_id=case_id,
                prediction_date=pred_date,
                message=esc_out.get("message", "Insufficient evidence for escalation assessment."),
                model=model_output,
                metadata=pipeline_metadata,
            )
        elif status == ProcessingStatus.ABSTAINED:
            result = abstained_result(
                case_id=case_id,
                prediction_date=pred_date,
                message=esc_out.get("message", "Evidence insufficient or confidence below minimum threshold."),
                source=source,
                distress=distress_output,
                explanation=explanation,
                model=model_output,
                metadata=pipeline_metadata,
            )
        else:
            prediction_output = PredictionOutput(
                escalation_probability=float(esc_out["escalation_probability"]),
                target_horizon_days=int(esc_out["target_horizon_days"]),
                confidence=float(esc_out["confidence"]),
                risk_level=RiskLevel(esc_out["risk_level"]),
            )
            result = MlInferenceResult(
                case_id=case_id,
                prediction_date=pred_date,
                status=status,
                source=source,
                distress=distress_output,
                prediction=prediction_output,
                explanation=explanation,
                model=model_output,
                message=esc_out.get("message"),
                metadata=pipeline_metadata,
            )

        if logger_tracer:
            logger_tracer.log_stage("Pipeline finished")

        return result

    def _normalize_input(self, item: Union[MLInput, Mapping[str, Any], InferenceInput]) -> InferenceInput:
        """Coerces MLInput, Mapping, or InferenceInput into a validated InferenceInput container."""
        if isinstance(item, InferenceInput):
            return item

        if isinstance(item, MLInput):
            raw_text = None
            if item.metadata:
                raw_text = item.metadata.get("raw_text") or item.metadata.get("text_response")
            raw_audio = None
            if item.metadata:
                raw_audio = item.metadata.get("raw_audio") or item.metadata.get("audio_waveform")

            return InferenceInput(
                case_id=item.case_id,
                interaction_date=item.interaction_date or datetime.date.today().isoformat(),
                feature_values=tuple(item.feature_values),
                raw_text=str(raw_text) if raw_text is not None else None,
                raw_audio=tuple(raw_audio) if raw_audio is not None else None,
                metadata=dict(item.metadata) if item.metadata else {},
            )

        if not isinstance(item, Mapping):
            raise InvalidInputError(f"Expected MLInput, InferenceInput, or Mapping, got {type(item).__name__}")

        case_id = str(item.get("case_id", ""))
        if not case_id:
            raise InvalidInputError("Record missing required 'case_id'")

        interaction_date = str(item.get("interaction_date") or item.get("prediction_date") or datetime.date.today().isoformat())
        feature_vals = item.get("feature_values")
        if feature_vals is None:
            feature_vals = item.get("tabular_features")
        if feature_vals is None:
            feature_vals = [None] * 60
        else:
            feature_vals = list(feature_vals)
            if len(feature_vals) < 60:
                feature_vals.extend([None] * (60 - len(feature_vals)))

        def _to_float(v: Any) -> Optional[float]:
            if v is None:
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        # 1. Voice features ingestion (Diya's locked contract, indices 52-59)
        voice_dict = item.get("voice") or item.get("voice_features")
        if isinstance(voice_dict, Mapping):
            if voice_dict.get("voice_available", True):
                if "speech_rate" in voice_dict and feature_vals[52] is None:
                    feature_vals[52] = _to_float(voice_dict.get("speech_rate"))
                if "pause_ratio" in voice_dict and feature_vals[53] is None:
                    feature_vals[53] = _to_float(voice_dict.get("pause_ratio"))
                if "response_latency" in voice_dict and feature_vals[54] is None:
                    feature_vals[54] = _to_float(voice_dict.get("response_latency"))
                if "pitch_variability" in voice_dict and feature_vals[55] is None:
                    feature_vals[55] = _to_float(voice_dict.get("pitch_variability"))
                if "energy_variation" in voice_dict and feature_vals[56] is None:
                    feature_vals[56] = _to_float(voice_dict.get("energy_variation"))
                if "audio_quality" in voice_dict and feature_vals[57] is None:
                    feature_vals[57] = _to_float(voice_dict.get("audio_quality"))
                if "asr_confidence" in voice_dict and feature_vals[58] is None:
                    feature_vals[58] = _to_float(voice_dict.get("asr_confidence"))
                if "baseline_deviation" in voice_dict and feature_vals[59] is None:
                    feature_vals[59] = _to_float(voice_dict.get("baseline_deviation"))

        # 2. Behavioural features ingestion (indices 18-25)
        behav_dict = item.get("behavioural") or item.get("behavioural_features")
        if isinstance(behav_dict, Mapping):
            if "safety_distress" in behav_dict and feature_vals[18] is None:
                feature_vals[18] = _to_float(behav_dict.get("safety_distress"))
            if "sleep_disturbance" in behav_dict and feature_vals[19] is None:
                feature_vals[19] = _to_float(behav_dict.get("sleep_disturbance"))
            if "fear_intensity" in behav_dict and feature_vals[20] is None:
                feature_vals[20] = _to_float(behav_dict.get("fear_intensity"))
            if "low_social_support" in behav_dict and feature_vals[21] is None:
                feature_vals[21] = _to_float(behav_dict.get("low_social_support"))
            if "help_requested" in behav_dict and feature_vals[22] is None:
                feature_vals[22] = _to_float(behav_dict.get("help_requested"))
            if "composite_distress" in behav_dict and feature_vals[23] is None:
                feature_vals[23] = _to_float(behav_dict.get("composite_distress"))
            if "change_from_previous" in behav_dict and feature_vals[24] is None:
                feature_vals[24] = _to_float(behav_dict.get("change_from_previous"))
            if "change_from_baseline" in behav_dict and feature_vals[25] is None:
                feature_vals[25] = _to_float(behav_dict.get("change_from_baseline"))

        # 3. Engagement features ingestion (indices 26-38)
        eng_dict = item.get("engagement") or item.get("engagement_features")
        if isinstance(eng_dict, Mapping):
            if "completed_checkin" in eng_dict and feature_vals[26] is None:
                feature_vals[26] = _to_float(eng_dict.get("completed_checkin"))
            if "missed_checkin" in eng_dict and feature_vals[27] is None:
                feature_vals[27] = _to_float(eng_dict.get("missed_checkin"))
            if "missed_checkin_streak" in eng_dict and feature_vals[28] is None:
                feature_vals[28] = _to_float(eng_dict.get("missed_checkin_streak"))
            if "checkin_consistency" in eng_dict and feature_vals[29] is None:
                feature_vals[29] = _to_float(eng_dict.get("checkin_consistency"))
            if "response_delay" in eng_dict and feature_vals[30] is None:
                feature_vals[30] = _to_float(eng_dict.get("response_delay"))
            if "average_response_delay" in eng_dict and feature_vals[31] is None:
                feature_vals[31] = _to_float(eng_dict.get("average_response_delay"))
            if "response_frequency" in eng_dict and feature_vals[32] is None:
                feature_vals[32] = _to_float(eng_dict.get("response_frequency"))
            if "engagement_drop" in eng_dict and feature_vals[33] is None:
                feature_vals[33] = _to_float(eng_dict.get("engagement_drop"))
            if "recent_activity_count" in eng_dict and feature_vals[34] is None:
                feature_vals[34] = _to_float(eng_dict.get("recent_activity_count"))
            if "inactivity_duration" in eng_dict and feature_vals[35] is None:
                feature_vals[35] = _to_float(eng_dict.get("inactivity_duration"))
            if ("score" in eng_dict or "engagement_score" in eng_dict) and feature_vals[36] is None:
                feature_vals[36] = _to_float(eng_dict.get("score", eng_dict.get("engagement_score")))
            if "change_from_previous" in eng_dict and feature_vals[37] is None:
                feature_vals[37] = _to_float(eng_dict.get("change_from_previous"))
            if "change_from_baseline" in eng_dict and feature_vals[38] is None:
                feature_vals[38] = _to_float(eng_dict.get("change_from_baseline"))

        # 4. Longitudinal features ingestion (indices 39-51)
        long_dict = item.get("longitudinal") or item.get("longitudinal_features")
        if isinstance(long_dict, Mapping):
            if "observation_count" in long_dict and feature_vals[39] is None:
                feature_vals[39] = _to_float(long_dict.get("observation_count"))
            if "history_span_days" in long_dict and feature_vals[40] is None:
                feature_vals[40] = _to_float(long_dict.get("history_span_days"))
            if "current_distress" in long_dict and feature_vals[41] is None:
                feature_vals[41] = _to_float(long_dict.get("current_distress"))
            if "baseline_distress" in long_dict and feature_vals[42] is None:
                feature_vals[42] = _to_float(long_dict.get("baseline_distress"))
            if "previous_distress" in long_dict and feature_vals[43] is None:
                feature_vals[43] = _to_float(long_dict.get("previous_distress"))
            if "delta_from_baseline" in long_dict and feature_vals[44] is None:
                feature_vals[44] = _to_float(long_dict.get("delta_from_baseline"))
            if "delta_from_previous" in long_dict and feature_vals[45] is None:
                feature_vals[45] = _to_float(long_dict.get("delta_from_previous"))
            if "distress_velocity" in long_dict and feature_vals[46] is None:
                feature_vals[46] = _to_float(long_dict.get("distress_velocity"))
            if "distress_acceleration" in long_dict and feature_vals[47] is None:
                feature_vals[47] = _to_float(long_dict.get("distress_acceleration"))
            if "distress_volatility" in long_dict and feature_vals[48] is None:
                feature_vals[48] = _to_float(long_dict.get("distress_volatility"))
            if "peak_distress" in long_dict and feature_vals[49] is None:
                feature_vals[49] = _to_float(long_dict.get("peak_distress"))
            if "trough_distress" in long_dict and feature_vals[50] is None:
                feature_vals[50] = _to_float(long_dict.get("trough_distress"))
            if "sustained_distress_count" in long_dict and feature_vals[51] is None:
                feature_vals[51] = _to_float(long_dict.get("sustained_distress_count"))

        raw_text = item.get("raw_text") or item.get("text_response") or item.get("transcription")
        raw_audio = item.get("raw_audio") or item.get("audio_waveform")

        meta = dict(item.get("metadata", {}))
        if isinstance(voice_dict, Mapping) and voice_dict.get("voice_available", True):
            meta["voice_available"] = True
        for extra_key in ("interaction_id", "language", "asr_confidence", "audio_quality"):
            if extra_key in item and extra_key not in meta:
                meta[extra_key] = item[extra_key]

        return InferenceInput(
            case_id=case_id,
            interaction_date=interaction_date,
            feature_values=tuple(feature_vals),
            raw_text=str(raw_text) if raw_text is not None else None,
            raw_audio=tuple(raw_audio) if raw_audio is not None else None,
            metadata=meta,
        )


@dataclass(frozen=True)
class InferenceInput:
    """Normalized internal input representation for pipeline stages."""

    case_id: str
    interaction_date: str
    feature_values: tuple[Optional[float], ...]
    raw_text: Optional[str] = None
    raw_audio: Optional[tuple[float, ...]] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

