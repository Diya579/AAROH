"""Unit tests for Audio Emotion Representation Model (Slice 3.4).

Verifies:
- RAVDESS dataset loading and lazy WAV indexing
- Audio preprocessing (16 kHz resampling, amplitude normalization, 5s pad/truncate)
- Deterministic actor-level splitting with zero leakage validation
- AudioEmotionModel forward pass and shape verification
- Backward propagation and loss computation
- Frozen vs. unfrozen backbone configuration
- Public predict_audio_embedding() interface
- Checkpoint save and reload into fresh model instance
- Model artifact export and file existence verification
- Strict clinical boundary assertions (Audio Emotion != Clinical Distress)
- Confusion matrix and per-class accuracy computation
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

from backend.ml.training.models.audio_emotion import (
    DEFAULT_AUDIO_BACKBONE,
    DEFAULT_TARGET_SAMPLES,
    EMOTION_TO_ID,
    ID_TO_EMOTION,
    RAVDESS_EMOTIONS,
    AudioEmotionModel,
    RavdessDataset,
    load_and_preprocess_wav,
    split_ravdess_records_by_actor,
)
from backend.ml.training.models.audio_emotion.dataset import validate_no_actor_leakage
from backend.ml.training.models.common import (
    CheckpointManager,
    ModelExportManager,
    ModelMetadata,
    compute_confusion_matrix,
    compute_per_class_accuracy,
    enforce_audio_emotion_boundary,
)
from backend.ml.training.train_audio_emotion import parse_args


class TestAudioRepresentationModel(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # =================================================================
    # 1. Dataset Loading & Actor-Level Splitting
    # =================================================================

    def test_actor_level_split_programmatic_and_no_leakage(self) -> None:
        """Verifies deterministic programmatic actor split and zero leakage."""
        mock_records = [
            {"actor": "01", "audio_path": "path/1.wav", "emotion": "neutral"},
            {"actor": "01", "audio_path": "path/2.wav", "emotion": "calm"},
            {"actor": "02", "audio_path": "path/3.wav", "emotion": "happy"},
            {"actor": "03", "audio_path": "path/4.wav", "emotion": "sad"},
            {"actor": "04", "audio_path": "path/5.wav", "emotion": "angry"},
            {"actor": "05", "audio_path": "path/6.wav", "emotion": "fearful"},
        ]
        train_recs, test_recs = split_ravdess_records_by_actor(
            mock_records,
            test_ratio=0.33,
            seed=42,
        )
        train_actors = set(r["actor"] for r in train_recs)
        test_actors = set(r["actor"] for r in test_recs)

        # Zero leakage
        self.assertEqual(len(train_actors.intersection(test_actors)), 0)
        self.assertEqual(len(train_actors) + len(test_actors), 5)

    def test_actor_leakage_detection_raises_error(self) -> None:
        """Verifies that intentional actor leakage raises ValueError."""
        # 1. Direct leakage validator
        train_leak = [{"actor": "01"}, {"actor": "02"}]
        test_leak = [{"actor": "02"}, {"actor": "03"}]
        with self.assertRaises(ValueError) as ctx:
            validate_no_actor_leakage(train_leak, test_leak)
        self.assertIn("ACTOR LEAKAGE DETECTED", str(ctx.exception))

        # 2. Partition covering all actors in test
        mock_records = [
            {"actor": "01", "audio_path": "p1.wav", "emotion": "neutral"},
            {"actor": "02", "audio_path": "p2.wav", "emotion": "calm"},
        ]
        with self.assertRaises(ValueError):
            split_ravdess_records_by_actor(mock_records, test_actors=["01", "02"])

    def test_lazy_wav_loading_and_preprocessing(self) -> None:
        """Verifies lazy loading of a real WAV file and padding to 80,000 samples."""
        real_wav = Path("datasets/ravdess/Actor_01/03-01-01-01-01-01-01.wav")
        if real_wav.exists():
            waveform, sr = load_and_preprocess_wav(real_wav)
            self.assertEqual(sr, 16000)
            self.assertEqual(len(waveform), DEFAULT_TARGET_SAMPLES)
            self.assertLessEqual(max(waveform), 1.0)
            self.assertGreaterEqual(min(waveform), -1.0)

    # =================================================================
    # 2. Model Architecture, Forward Pass & Boundaries
    # =================================================================

    def test_audio_emotion_model_forward_pass(self) -> None:
        """Verifies forward pass producing probabilities and 768-dim embeddings."""
        model = AudioEmotionModel(embedding_dim=768)
        dummy_waveforms = [
            [0.1 * ((i % 100) / 50.0 - 1.0) for i in range(DEFAULT_TARGET_SAMPLES)],
            [0.2 * ((i % 50) / 25.0 - 1.0) for i in range(DEFAULT_TARGET_SAMPLES)],
        ]
        res = model.encode_and_predict(dummy_waveforms)

        self.assertIn("audio_emotion_probabilities", res)
        self.assertIn("audio_embeddings", res)
        self.assertEqual(len(res["audio_emotion_probabilities"]), 2)
        self.assertEqual(len(res["audio_embeddings"]), 2)
        self.assertEqual(len(res["audio_embeddings"][0]), 768)

        # Check probability keys match 8 RAVDESS emotions
        for emo in RAVDESS_EMOTIONS:
            self.assertIn(emo, res["audio_emotion_probabilities"][0])

    def test_public_predict_audio_embedding_interface(self) -> None:
        """Verifies public predict_audio_embedding() interface consumed by Slice 3.5."""
        model = AudioEmotionModel(embedding_dim=768)
        dummy_waveform = [0.05 * math.sin(i * 0.1) for i in range(DEFAULT_TARGET_SAMPLES)]

        res = model.predict_audio_embedding(dummy_waveform)
        self.assertIn("audio_embedding", res)
        self.assertIn("audio_emotion_probabilities", res)
        self.assertEqual(len(res["audio_embedding"]), 768)
        self.assertEqual(len(res["audio_emotion_probabilities"]), 8)

    def test_frozen_vs_unfrozen_backbone(self) -> None:
        """Verifies parameter count differences between frozen and unfrozen backbone."""
        frozen_model = AudioEmotionModel(frozen_backbone=True)
        unfrozen_model = AudioEmotionModel(frozen_backbone=False)

        self.assertEqual(frozen_model.trainable_parameters_count, 768 * 8 + 8)
        self.assertGreater(unfrozen_model.trainable_parameters_count, frozen_model.trainable_parameters_count)

    def test_clinical_boundary_enforcement(self) -> None:
        """Verifies that audio emotion representations forbid distress or diagnostic outputs."""
        with self.assertRaises(ValueError):
            enforce_audio_emotion_boundary("distress_score")
        with self.assertRaises(ValueError):
            enforce_audio_emotion_boundary("escalation_probability")
        with self.assertRaises(ValueError):
            enforce_audio_emotion_boundary("depression")
        with self.assertRaises(ValueError):
            enforce_audio_emotion_boundary("clinical_diagnosis")

        # Valid outputs should pass
        enforce_audio_emotion_boundary("audio_emotion_probabilities")
        enforce_audio_emotion_boundary("audio_embedding")

    # =================================================================
    # 3. Training Step & Loss Calculation
    # =================================================================

    def test_train_step_loss_decrease(self) -> None:
        """Verifies that train_step computes finite loss and updates parameters."""
        model = AudioEmotionModel(embedding_dim=768)
        dummy_batch = [
            [0.1 * math.sin(i * 0.05) for i in range(DEFAULT_TARGET_SAMPLES)],
            [0.2 * math.cos(i * 0.05) for i in range(DEFAULT_TARGET_SAMPLES)],
        ]
        targets = [2, 5]  # happy, fearful

        loss1 = model.train_step(dummy_batch, targets, lr=0.01)
        loss2 = model.train_step(dummy_batch, targets, lr=0.01)

        self.assertTrue(math.isfinite(loss1))
        self.assertTrue(math.isfinite(loss2))
        self.assertLess(loss2, loss1)

    # =================================================================
    # 4. Checkpoint Save, Reload & Export
    # =================================================================

    def test_checkpoint_save_and_reload(self) -> None:
        """Verifies saving checkpoint and reloading into fresh model instance."""
        ckpt_dir = self.test_dir / "ckpts"
        mgr = CheckpointManager(ckpt_dir)

        model = AudioEmotionModel()
        ckpt_path = mgr.save_checkpoint(epoch=1, model_state=model.state_dict())

        fresh_model = AudioEmotionModel()
        loaded = mgr.load_checkpoint(ckpt_path)
        state_dict = loaded.get("model_state_dict", loaded)
        fresh_model.load_state_dict(state_dict)

        # Inference should succeed
        dummy = [[0.0] * DEFAULT_TARGET_SAMPLES]
        preds = fresh_model.encode_and_predict(dummy)
        self.assertEqual(len(preds["audio_embeddings"][0]), 768)

    def test_model_export_and_files_exist(self) -> None:
        """Verifies model export produces all 6 expected files under models/audio_emotion."""
        export_dir = self.test_dir / "models" / "audio_emotion"
        model = AudioEmotionModel()

        saved_path = model.save(
            output_dir=export_dir,
            metrics={"accuracy": 0.75, "macro_f1": 0.72},
        )
        self.assertTrue((export_dir / "pytorch_model.bin").exists())
        self.assertTrue((export_dir / "config.json").exists())
        self.assertTrue((export_dir / "metadata.json").exists())
        self.assertTrue((export_dir / "metrics.json").exists())
        self.assertTrue((export_dir / "label_mapping.json").exists())
        self.assertTrue((export_dir / "preprocessor_config.json").exists())

    # =================================================================
    # 5. Metrics & Confusion Matrix
    # =================================================================

    def test_confusion_matrix_and_per_class_accuracy(self) -> None:
        """Verifies confusion matrix and per-class accuracy calculation."""
        y_true = ["neutral", "calm", "happy", "happy", "angry"]
        y_pred = ["neutral", "happy", "happy", "sad", "angry"]

        cm = compute_confusion_matrix(y_true, y_pred, classes=RAVDESS_EMOTIONS)
        self.assertEqual(len(cm), 8)
        self.assertEqual(len(cm[0]), 8)

        per_class = compute_per_class_accuracy(y_true, y_pred, classes=RAVDESS_EMOTIONS)
        self.assertEqual(per_class["neutral"], 1.0)
        self.assertEqual(per_class["happy"], 0.5)
        self.assertEqual(per_class["calm"], 0.0)
        self.assertEqual(per_class["angry"], 1.0)


if __name__ == "__main__":
    unittest.main()
