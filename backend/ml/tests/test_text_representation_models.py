"""Comprehensive unit tests for Text Representation Models (Slice 3.3).

Verifies:
- Model metadata handling & serialization
- Pure-Python evaluation metrics (Accuracy, Precision, Recall, Macro/Weighted F1, ROC-AUC)
- Representation quality metrics (norm, cosine separation)
- Checkpoint manager & early stopping
- Text Emotion dataset loading and model encoding (GoEmotions + EmoHinD)
- Stress dataset loading and model encoding (Dreaddit)
- Mental Health Language dataset loading and representation encoding (MindBridge)
- Model export & load round-trip (weights, config, label_mapping, metrics, metadata)
- CLI argument parsing across all training and evaluation scripts
- Seed reproducibility
- Strict clinical boundary assertions (stress != distress, no PHQ/GAD predictions)
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from backend.ml.inference.exceptions import NeuralExecutionError

from backend.ml.training.evaluate_text_models import (
    evaluate_all,
    evaluate_mental_health,
    evaluate_stress,
    evaluate_text_emotion,
    parse_args as parse_eval_args,
)
from backend.ml.training.models.common import (
    CheckpointManager,
    EarlyStopping,
    ModelExportManager,
    ModelMetadata,
    compute_accuracy,
    compute_precision_recall_f1,
    compute_representation_metrics,
    compute_roc_auc,
    enforce_mental_health_boundary,
    enforce_stress_boundary,
    get_device,
    set_seed,
)
from backend.ml.training.models.mental_health_language import (
    MentalHealthLanguageModel,
    MindBridgeDataset,
    load_mindbridge_records,
)
from backend.ml.training.models.stress import (
    DreadditStressDataset,
    StressModel,
    load_dreaddit_records,
)
from backend.ml.training.models.text_emotion import (
    GOEMOTIONS_TAXONOMY,
    TextEmotionDataset,
    TextEmotionModel,
    load_combined_emotion_records,
)
from backend.ml.training.train_mental_health import parse_args as parse_mh_args
from backend.ml.training.train_stress import parse_args as parse_stress_args
from backend.ml.training.train_text_emotion import parse_args as parse_emotion_args


class TestTextRepresentationModels(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # =================================================================
    # 1. Common Infrastructure & Metrics Tests
    # =================================================================

    def test_model_metadata_serialization(self) -> None:
        """Verifies ModelMetadata serialization to and from dictionary."""
        meta = ModelMetadata(
            model_name="test-model",
            model_version="1.0.0",
            dataset_name="test-data",
            dataset_version="3.3.0",
            hyperparameters={"lr": 1e-4, "batch_size": 16},
            backbone="distilbert-base-uncased",
            embedding_dim=768,
        )
        d = meta.to_dict()
        self.assertEqual(d["model_name"], "test-model")
        self.assertEqual(d["embedding_dim"], 768)
        self.assertEqual(d["hyperparameters"]["batch_size"], 16)

        reconstructed = ModelMetadata.from_dict(d)
        self.assertEqual(reconstructed.model_name, meta.model_name)
        self.assertEqual(reconstructed.hyperparameters, meta.hyperparameters)

    def test_compute_accuracy(self) -> None:
        """Verifies accuracy calculation."""
        self.assertEqual(compute_accuracy([1, 0, 1, 1], [1, 0, 0, 1]), 0.75)
        self.assertEqual(compute_accuracy([], []), 0.0)

    def test_compute_precision_recall_f1(self) -> None:
        """Verifies multi-class precision, recall, macro F1, and weighted F1."""
        y_true = ["joy", "sadness", "joy", "fear"]
        y_pred = ["joy", "joy", "joy", "fear"]
        metrics = compute_precision_recall_f1(y_true, y_pred, classes=["joy", "sadness", "fear"])

        self.assertIn("precision", metrics)
        self.assertIn("recall", metrics)
        self.assertIn("macro_f1", metrics)
        self.assertIn("weighted_f1", metrics)
        self.assertGreater(metrics["macro_f1"], 0.0)
        self.assertLessEqual(metrics["macro_f1"], 1.0)

    def test_compute_roc_auc(self) -> None:
        """Verifies ROC-AUC calculation."""
        # Perfect separation
        y_true = [0, 0, 1, 1]
        y_scores = [0.1, 0.2, 0.8, 0.9]
        self.assertAlmostEqual(compute_roc_auc(y_true, y_scores), 1.0)

        # Inverted separation
        y_scores_inv = [0.9, 0.8, 0.2, 0.1]
        self.assertAlmostEqual(compute_roc_auc(y_true, y_scores_inv), 0.0)

        # Ties
        y_scores_ties = [0.5, 0.5, 0.5, 0.5]
        self.assertAlmostEqual(compute_roc_auc(y_true, y_scores_ties), 0.5)

    def test_compute_representation_metrics(self) -> None:
        """Verifies embedding representation norm and cosine separation."""
        embs = [
            [1.0, 0.0],
            [0.9, 0.1],
            [0.0, 1.0],
            [0.1, 0.9],
        ]
        labels = ["A", "A", "B", "B"]
        rep_metrics = compute_representation_metrics(embs, labels=labels)

        self.assertIn("mean_embedding_norm", rep_metrics)
        self.assertIn("cosine_separation", rep_metrics)
        self.assertGreater(rep_metrics["mean_embedding_norm"], 0.0)
        self.assertGreater(rep_metrics["cosine_separation"], 0.5)

    def test_checkpoint_manager_and_early_stopping(self) -> None:
        """Verifies checkpoint manager saving and early stopping step logic."""
        ckpt_dir = self.test_dir / "ckpts"
        drive_dir = self.test_dir / "drive_ckpts"
        mgr = CheckpointManager(ckpt_dir, drive_dir)

        p = mgr.save_checkpoint(epoch=1, model_state={"layer": [1, 2]}, is_best=True)
        self.assertTrue(p.exists() or p.with_suffix(".json").exists())

        stopper = EarlyStopping(patience=2, min_delta=0.01, mode="min")
        self.assertTrue(stopper.step(1.0))
        self.assertFalse(stopper.early_stop)
        self.assertTrue(stopper.step(0.8))  # improvement
        self.assertFalse(stopper.early_stop)
        self.assertFalse(stopper.step(0.81))  # no improvement (1)
        self.assertFalse(stopper.early_stop)
        self.assertFalse(stopper.step(0.82))  # no improvement (2 -> patience reached)
        self.assertTrue(stopper.early_stop)

    def test_seed_and_device(self) -> None:
        """Verifies set_seed runs cleanly and get_device returns valid string."""
        set_seed(42)
        dev = get_device()
        self.assertIn(dev, ["cuda", "mps", "cpu"])

    # =================================================================
    # 2. Strict Clinical Boundaries Tests
    # =================================================================

    def test_enforce_stress_boundary(self) -> None:
        """Verifies that stress probability cannot be renamed or treated as distress."""
        with self.assertRaises(ValueError):
            enforce_stress_boundary("distress")
        with self.assertRaises(ValueError):
            enforce_stress_boundary("distress_score")
        with self.assertRaises(ValueError):
            enforce_stress_boundary("clinical_distress")

        # Valid names should pass without error
        enforce_stress_boundary("stress_probability")
        enforce_stress_boundary("stress_score")

    def test_enforce_mental_health_boundary(self) -> None:
        """Verifies that mental health model cannot predict PHQ scores or clinical diagnoses."""
        with self.assertRaises(ValueError):
            enforce_mental_health_boundary("phq")
        with self.assertRaises(ValueError):
            enforce_mental_health_boundary("phq_score")
        with self.assertRaises(ValueError):
            enforce_mental_health_boundary("clinical_diagnosis")

        # Valid tasks should pass
        enforce_mental_health_boundary("representation_encoder")
        enforce_mental_health_boundary("screening_embedding")

    # =================================================================
    # 3. Text Emotion Model & Dataset Tests (GoEmotions + EmoHinD)
    # =================================================================

    def test_text_emotion_dataset_and_model(self) -> None:
        """Verifies TextEmotionDataset loading and TextEmotionModel encoding."""
        mock_records = [
            {"text": "I am so grateful for this support", "emotion": "gratitude", "label_ids": [15]},
            {"text": "यह बहुत डरावना और दुखद था", "emotion": "fear", "label_ids": [14]},
        ]
        ds = TextEmotionDataset(mock_records)
        self.assertEqual(len(ds), 2)
        sample = ds[0]
        self.assertEqual(sample["text"], "I am so grateful for this support")
        self.assertEqual(len(sample["label_vec"]), 28)
        self.assertEqual(sample["label_vec"][15], 1.0)

        # Model instantiation and prediction
        model = TextEmotionModel(embedding_dim=768)
        preds = model.encode_and_predict(["I am feeling grateful", "यह परीक्षण है"])

        self.assertIn("emotion_probabilities", preds)
        self.assertIn("emotion_embeddings", preds)
        self.assertEqual(len(preds["emotion_probabilities"]), 2)
        self.assertEqual(len(preds["emotion_embeddings"]), 2)
        self.assertEqual(len(preds["emotion_embeddings"][0]), 768)
        self.assertIn("gratitude", preds["emotion_probabilities"][0])

    def test_text_emotion_export(self) -> None:
        """Verifies export of Text Emotion model artifacts to models/text_emotion."""
        export_dir = self.test_dir / "models" / "text_emotion"
        model = TextEmotionModel(embedding_dim=768)

        saved_path = model.save(
            output_dir=export_dir,
            metrics={"accuracy": 0.85, "macro_f1": 0.81},
            hyperparameters={"epochs": 3, "batch_size": 32},
        )
        self.assertTrue((export_dir / "config.json").exists())
        self.assertTrue((export_dir / "label_mapping.json").exists())
        self.assertTrue((export_dir / "metrics.json").exists())
        self.assertTrue((export_dir / "metadata.json").exists())
        self.assertTrue((export_dir / "tokenizer_config.json").exists())

        loaded_meta = ModelExportManager.load_model_metadata(export_dir)
        self.assertEqual(loaded_meta["metadata"]["model_name"], "aaroh-text-emotion")
        self.assertEqual(loaded_meta["metrics"]["accuracy"], 0.85)

    # =================================================================
    # 4. Stress Model & Dataset Tests (Dreaddit)
    # =================================================================

    def test_stress_dataset_and_model(self) -> None:
        """Verifies Stress dataset and model with strict stress != distress invariance."""
        mock_records = [
            {"text": "I have been having terrible panic attacks and stress", "stress_label": 1},
            {"text": "Nice walk in the park today with no worries", "stress_label": 0},
        ]
        ds = DreadditStressDataset(mock_records)
        self.assertEqual(len(ds), 2)
        self.assertEqual(ds[0]["stress_label"], 1)

        model = StressModel(embedding_dim=768)
        preds = model.encode_and_predict(["Panic and stress overload", "Calm and peaceful"])

        self.assertIn("stress_probabilities", preds)
        self.assertIn("stress_embeddings", preds)
        self.assertNotIn("distress", preds)
        self.assertNotIn("distress_score", preds)
        self.assertEqual(len(preds["stress_probabilities"]), 2)
        self.assertEqual(len(preds["stress_embeddings"]), 2)
        self.assertEqual(len(preds["stress_embeddings"][0]), 768)
        self.assertGreaterEqual(preds["stress_probabilities"][0], 0.0)
        self.assertLessEqual(preds["stress_probabilities"][0], 1.0)

    def test_stress_model_export(self) -> None:
        """Verifies export of Stress model artifacts."""
        export_dir = self.test_dir / "models" / "stress"
        model = StressModel(embedding_dim=768)

        saved_path = model.save(
            output_dir=export_dir,
            metrics={"accuracy": 0.82, "roc_auc": 0.86},
        )
        self.assertTrue((export_dir / "config.json").exists())
        self.assertTrue((export_dir / "metadata.json").exists())

        loaded_meta = ModelExportManager.load_model_metadata(export_dir)
        self.assertEqual(loaded_meta["metadata"]["dataset_name"], "dreaddit")
        self.assertEqual(loaded_meta["config"]["clinical_boundary"], "stress_probability != distress_score")

    # =================================================================
    # 5. Mental Health Language Model & Dataset Tests (MindBridge)
    # =================================================================

    def test_mental_health_language_dataset_and_model(self) -> None:
        """Verifies MindBridge dataset loading and MentalHealthLanguageModel representation encoding."""
        records = load_mindbridge_records(self.test_dir, allow_synthetic_fallback=True)
        self.assertGreater(len(records), 0)

        ds = MindBridgeDataset(records)
        sample = ds[0]
        self.assertIn("text", sample)
        self.assertIn("category", sample)

        model = MentalHealthLanguageModel(embedding_dim=768)
        enc_res = model.encode([records[0]["text"], records[1]["text"]])

        self.assertIn("mental_health_embeddings", enc_res)
        self.assertNotIn("phq", enc_res)
        self.assertNotIn("phq_score", enc_res)
        self.assertEqual(len(enc_res["mental_health_embeddings"]), 2)
        self.assertEqual(len(enc_res["mental_health_embeddings"][0]), 768)

    def test_mental_health_language_export(self) -> None:
        """Verifies export of Mental Health Language model artifacts."""
        export_dir = self.test_dir / "models" / "mental_health_language"
        model = MentalHealthLanguageModel(embedding_dim=768)

        saved_path = model.save(
            output_dir=export_dir,
            metrics={"mean_embedding_norm": 1.0, "cosine_separation": 0.42},
        )
        self.assertTrue((export_dir / "metadata.json").exists())
        self.assertTrue((export_dir / "config.json").exists())

        loaded_meta = ModelExportManager.load_model_metadata(export_dir)
        self.assertEqual(loaded_meta["metadata"]["model_name"], "aaroh-mental-health-language")
        self.assertIn("Does NOT predict PHQ", str(loaded_meta["config"]["clinical_boundaries"]))

    # =================================================================
    # 6. CLI Argument Parsing Tests
    # =================================================================

    def test_cli_parsing(self) -> None:
        """Verifies CLI argument parsing across all training and evaluation scripts."""
        # Emotion CLI
        args_emo = parse_emotion_args(["--batch-size", "64", "--epochs", "10", "--fp16", "--seed", "123"])
        self.assertEqual(args_emo.batch_size, 64)
        self.assertEqual(args_emo.epochs, 10)
        self.assertTrue(args_emo.fp16)
        self.assertEqual(args_emo.seed, 123)

        # Stress CLI
        args_stress = parse_stress_args(["--lr", "1e-4", "--gradient-accumulation-steps", "4"])
        self.assertEqual(args_stress.lr, 1e-4)
        self.assertEqual(args_stress.gradient_accumulation_steps, 4)

        # Mental Health CLI
        args_mh = parse_mh_args(["--output-dir", "custom/mh"])
        self.assertEqual(args_mh.output_dir, "custom/mh")

        # Evaluation CLI
        args_eval = parse_eval_args(["--model-type", "stress", "--models-dir", "models/"])
        self.assertEqual(args_eval.model_type, "stress")

    # =================================================================
    # 7. Comprehensive Evaluation Suite Tests
    # =================================================================

    def test_evaluate_all_pipeline(self) -> None:
        """Verifies that evaluate_all executes across all models and generates evaluation_metrics.json."""
        out_json = self.test_dir / "eval_out.json"
        results = evaluate_all(
            data_dir="datasets/processed",
            models_dir=self.test_dir / "models",
            model_type="all",
            output_file=out_json,
        )
        self.assertIn("evaluations", results)
        self.assertIn("text_emotion", results["evaluations"])
        self.assertIn("stress", results["evaluations"])
        self.assertIn("mental_health_language", results["evaluations"])
        self.assertTrue(out_json.exists())

    def test_distilbert_backbone_clean_loading_and_mlm_handling(self) -> None:
        """Verifies that the DistilBERT backbone loads with zero missing keys,
        explicitly decoupling MLM prediction head weights and preserving legitimate encoder weights."""
        model = TextEmotionModel(
            backbone="distilbert-base-multilingual-cased",
            execution_mode="PYTORCH_FINETUNE",
            unfreeze_layers=2,
        )
        self.assertIsNotNone(model.torch_model)
        self.assertIsNotNone(model.torch_model.encoder)

        # Check total parameter counts
        total_encoder_params = sum(p.numel() for p in model.torch_model.encoder.parameters())
        self.assertEqual(total_encoder_params, 134_734_080)
        self.assertEqual(model.trainable_parameters_count, 14_197_276)
        self.assertEqual(model.frozen_parameters_count, 120_558_336)

        # Verify legitimate encoder layers are present
        param_names = [name for name, _ in model.torch_model.named_parameters()]
        self.assertTrue(any("encoder.embeddings.word_embeddings.weight" in n for n in param_names))
        self.assertTrue(any("encoder.transformer.layer.0" in n for n in param_names))
        self.assertTrue(any("encoder.transformer.layer.5" in n for n in param_names))
        self.assertTrue(any("classifier.weight" in n for n in param_names))

        # Explicitly verify NO MLM-head keys exist in model parameters
        mlm_head_keys = [
            "vocab_transform.weight",
            "vocab_transform.bias",
            "vocab_layer_norm.weight",
            "vocab_layer_norm.bias",
            "vocab_projector.weight",
            "vocab_projector.bias",
        ]
        for k in mlm_head_keys:
            self.assertFalse(any(k in n for n in param_names), f"MLM-head key '{k}' unexpectedly found in model parameters!")

        # Verify batched forward pass executes with valid 768-D representations
        test_texts = ["Testing clean DistilBERT loading without MLM head warning.", "यह परीक्षण है।"]
        res = model.encode_and_predict(test_texts, device="cpu", batch_size=2)
        self.assertEqual(len(res["emotion_probabilities"]), 2)
        self.assertEqual(len(res["emotion_embeddings"]), 2)
        self.assertEqual(len(res["emotion_embeddings"][0]), 768)
        self.assertIn("neutral", res["emotion_probabilities"][0])

    def test_distilbert_backbone_missing_keys_fails_closed_no_fallback(self) -> None:
        """Verifies that missing encoder keys detected by AutoModelForMaskedLM fail closed immediately,
        raising NeuralExecutionError and NOT silently falling back to AutoModel."""
        with patch("transformers.AutoModelForMaskedLM.from_pretrained") as mock_mlm, \
             patch("transformers.AutoModel.from_pretrained") as mock_base:
            mock_mlm.return_value = (
                MagicMock(),
                {"missing_keys": ["distilbert.embeddings.word_embeddings.weight"], "unexpected_keys": []},
            )

            with self.assertRaises(NeuralExecutionError) as ctx:
                TextEmotionModel(
                    backbone="distilbert-base-multilingual-cased",
                    execution_mode="PYTORCH_FINETUNE",
                )

            self.assertIn("Missing encoder keys", str(ctx.exception))
            self.assertIn("distilbert.embeddings.word_embeddings.weight", str(ctx.exception))
            # Critical requirement: AutoModel fallback must NOT have been called!
            mock_base.assert_not_called()

    def test_distilbert_backbone_fallback_to_automodel_on_incompatible_arch(self) -> None:
        """Verifies that AutoModel fallback is ONLY used when AutoModelForMaskedLM is genuinely incompatible
        (e.g., ValueError), and if AutoModel also detects missing keys, it fails closed loudly."""
        with patch("transformers.AutoModelForMaskedLM.from_pretrained", side_effect=ValueError("Unrecognized configuration")):
            with patch("transformers.AutoModel.from_pretrained") as mock_base:
                mock_base.return_value = (
                    MagicMock(),
                    {"missing_keys": ["transformer.wte.weight"], "unexpected_keys": []},
                )

                with self.assertRaises(NeuralExecutionError) as ctx:
                    TextEmotionModel(
                        backbone="gpt2-or-custom",
                        execution_mode="PYTORCH_FINETUNE",
                    )

                self.assertIn("Missing encoder keys", str(ctx.exception))
                self.assertIn("transformer.wte.weight", str(ctx.exception))
                mock_base.assert_called_once()

    def test_encode_and_predict_automatic_device_synchronization(self) -> None:
        """Verifies that encode_and_predict dynamically synchronizes model parameter placement
        with the requested target device (e.g. CPU or MPS), preventing device mismatch failures."""
        import torch
        model = TextEmotionModel(
            backbone="distilbert-base-multilingual-cased",
            execution_mode="PYTORCH_FINETUNE",
        )
        self.assertIsNotNone(model.torch_model)

        # 1. Start on CPU
        res_cpu = model.encode_and_predict(["Test on CPU"], device="cpu", batch_size=1)
        self.assertEqual(len(res_cpu["emotion_probabilities"]), 1)
        first_param = next(model.torch_model.parameters())
        self.assertEqual(first_param.device.type, "cpu")

        # 2. Transition to MPS if available, otherwise mock target device
        if torch.backends.mps.is_available():
            res_mps = model.encode_and_predict(["Test on MPS"], device="mps", batch_size=1)
            self.assertEqual(len(res_mps["emotion_probabilities"]), 1)
            first_param = next(model.torch_model.parameters())
            self.assertEqual(first_param.device.type, "mps")

            # Transition back to CPU cleanly
            res_back_cpu = model.encode_and_predict(["Test back on CPU"], device="cpu", batch_size=1)
            self.assertEqual(len(res_back_cpu["emotion_probabilities"]), 1)
            first_param = next(model.torch_model.parameters())
            self.assertEqual(first_param.device.type, "cpu")

    def test_tokenization_edge_cases_and_numerical_stability(self) -> None:
        """Verifies that empty string, whitespace, unicode, emoji, Hindi, and long texts
        produce valid 768-D embeddings and probabilities without NaNs or infinities."""
        import math
        model = TextEmotionModel(
            backbone="distilbert-base-multilingual-cased",
            execution_mode="PYTORCH_FINETUNE",
        )

        edge_cases = [
            "",
            "   ",
            "\n\t\r",
            "😊🎉🔥🚨💔",
            "नमस्ते आप कैसे हैं? मुझे बहुत चिंता हो रही है।",
            "Hello world I feel very anxious today.",
            "Mujhe lagta hai ki everything is going wrong yaar.",
            "English with emoji 😢 and Hindi शब्द mixed! 12345! @#$%",
            "a",
            "long " * 500,
        ]

        res = model.encode_and_predict(edge_cases, device="cpu", batch_size=4)
        self.assertEqual(len(res["emotion_probabilities"]), len(edge_cases))
        self.assertEqual(len(res["emotion_embeddings"]), len(edge_cases))

        for p_dict, emb in zip(res["emotion_probabilities"], res["emotion_embeddings"]):
            self.assertEqual(len(p_dict), len(GOEMOTIONS_TAXONOMY))
            self.assertEqual(len(emb), 768)
            for prob in p_dict.values():
                self.assertFalse(math.isnan(prob))
                self.assertFalse(math.isinf(prob))
                self.assertGreaterEqual(prob, 0.0)
                self.assertLessEqual(prob, 1.0)
            for val in emb:
                self.assertFalse(math.isnan(val))
                self.assertFalse(math.isinf(val))

    def test_batch_size_inference_invariance(self) -> None:
        """Verifies numerical consistency across varying batch sizes (1, 3, 7, 16)."""
        import numpy as np
        model = TextEmotionModel(
            backbone="distilbert-base-multilingual-cased",
            execution_mode="PYTORCH_FINETUNE",
        )
        texts = [
            "I feel ecstatic!",
            "I feel anxious and worried.",
            "Just another day.",
            "यह एक परीक्षण है।",
            "I cannot handle this stress anymore.",
        ]

        res_1 = model.encode_and_predict(texts, batch_size=1)
        res_3 = model.encode_and_predict(texts, batch_size=3)
        res_7 = model.encode_and_predict(texts, batch_size=7)

        for i in range(len(texts)):
            p1 = [res_1["emotion_probabilities"][i][k] for k in GOEMOTIONS_TAXONOMY]
            p3 = [res_3["emotion_probabilities"][i][k] for k in GOEMOTIONS_TAXONOMY]
            p7 = [res_7["emotion_probabilities"][i][k] for k in GOEMOTIONS_TAXONOMY]
            np.testing.assert_allclose(p1, p3, atol=1e-4)
            np.testing.assert_allclose(p1, p7, atol=1e-4)

    def test_load_from_artifact_validation_and_weights_only(self) -> None:
        """Verifies that load_from_artifact enforces missing neural file validation and safe weights loading."""
        import tempfile
        import torch
        with tempfile.TemporaryDirectory() as tmpdir:
            art_p = Path(tmpdir)
            with open(art_p / "config.json", "w") as f:
                json.dump({"backbone": "distilbert-base-multilingual-cased"}, f)
            with open(art_p / "metadata.json", "w") as f:
                json.dump({"execution_mode": "PYTORCH_FINETUNE", "model_version": "1.0.0"}, f)
            with open(art_p / "label_mapping.json", "w") as f:
                json.dump({"num_classes": 28}, f)
            torch.save({"dummy": torch.zeros(1)}, art_p / "pytorch_model.bin")

            # Missing neural tokenizer files must raise FileNotFoundError
            with self.assertRaises(FileNotFoundError) as ctx:
                TextEmotionModel.load_from_artifact(art_p)
            self.assertIn("Missing required neural tokenizer files", str(ctx.exception))

    def test_export_import_round_trip_parity(self) -> None:
        """Verifies Phase 13 export/import round trip across PYTORCH_FINETUNE and FALLBACK modes,
        ensuring 100% numerical equivalence on embeddings, probabilities, and execution mode."""
        import numpy as np
        import tempfile
        test_texts = [
            "I feel happy and hopeful today!",
            "This is completely terrifying and overwhelming.",
            "नमस्ते, यह परीक्षण है।",
        ]

        for mode in ["PYTORCH_FINETUNE", "FALLBACK"]:
            model = TextEmotionModel(
                backbone="distilbert-base-multilingual-cased",
                execution_mode=mode,
            )
            pred_orig = model.encode_and_predict(test_texts, device="cpu", batch_size=2)

            with tempfile.TemporaryDirectory() as tmpdir:
                out_dir = Path(tmpdir) / "exported_model"
                model.save(output_dir=out_dir)

                loaded_model = TextEmotionModel.load_from_artifact(out_dir, device="cpu")
                pred_loaded = loaded_model.encode_and_predict(test_texts, device="cpu", batch_size=2)

                self.assertEqual(loaded_model.execution_mode, mode)
                np.testing.assert_allclose(
                    pred_orig["emotion_embeddings"],
                    pred_loaded["emotion_embeddings"],
                    atol=1e-5,
                    err_msg=f"Embedding mismatch in mode {mode}",
                )

                for i in range(len(test_texts)):
                    p_orig = list(pred_orig["emotion_probabilities"][i].values())
                    p_loaded = list(pred_loaded["emotion_probabilities"][i].values())
                    np.testing.assert_allclose(
                        p_orig,
                        p_loaded,
                        atol=1e-5,
                        err_msg=f"Probability mismatch in mode {mode}",
                    )

    def test_checkpoint_manager_load_checkpoint_weights_only(self) -> None:
        """Verifies that CheckpointManager.load_checkpoint enforces weights_only=True and rejects exploit payloads."""
        import tempfile
        import torch

        class Exploit:
            def __reduce__(self):
                return (eval, ("__import__('os').system('echo EXPLOIT')",))

        mgr = CheckpointManager(checkpoint_dir=self.test_dir / "ckpts")
        mgr.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        exploit_path = mgr.checkpoint_dir / "exploit.pt"
        torch.save(Exploit(), exploit_path)

        with self.assertRaises(Exception) as ctx:
            mgr.load_checkpoint(exploit_path)
        # Should raise unpickling/security error, not execute payload
        self.assertTrue("UnpicklingError" in type(ctx.exception).__name__ or "weights_only" in str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
