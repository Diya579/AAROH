"""Unit tests for Multimodal Feature Fusion Model (Slice 3.5).

Tests:
1. MultimodalInputRecord creation, serialization, and from_ml_input factory.
2. Modality availability detection and missingness preservation.
3. Tabular None != 0 preservation through explicit masks.
4. Case-level splitting with zero data leakage.
5. Parameter counts breakdown (head, frozen backbones, total).
6. Forward pass producing 256-dim L2-normalized embedding.
7. Dynamic modality gating weights summing to 1.0.
8. Missing modality resilience (gate weight drops to strictly 0.0).
9. Self-supervised training step reducing reconstruction loss.
10. Checkpoint save and reload restoring inference.
11. Clinical and regulatory boundary enforcement.
12. Model export structure and artifact validation.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
import unittest
from pathlib import Path

from backend.ml.features.assembly import assemble_ml_input
from backend.ml.features.behavioural import extract_behavioural_features
from backend.ml.features.engagement import extract_engagement_features
from backend.ml.features.extractor import extract_text_features
from backend.ml.features.longitudinal import extract_longitudinal_features
from backend.ml.features.registry import TOTAL_FEATURES_COUNT
from backend.ml.features.voice import VoiceFeatures
from backend.ml.preprocessing import preprocess_interaction
from backend.ml.training.models.common import enforce_fusion_boundary
from backend.ml.training.models.fusion.dataset import (
    MultimodalFusionDataset,
    MultimodalInputRecord,
    build_synthetic_multimodal_records,
    split_multimodal_records_by_case,
)
from backend.ml.training.models.fusion.model import (
    DISTILBERT_PARAM_COUNT,
    FROZEN_BACKBONES_PARAM_COUNT,
    FUSION_EMBEDDING_DIM,
    MultimodalFusionModel,
    WAV2VEC2_PARAM_COUNT,
)


class TestMultimodalFusion(unittest.TestCase):
    """Test suite for Multimodal Feature Fusion (Slice 3.5)."""

    def setUp(self) -> None:
        self.seed = 42

    def test_record_creation_and_serialization(self) -> None:
        """Verifies MultimodalInputRecord fields, serialization, and deserialization."""
        rec = MultimodalInputRecord(
            case_id="CASE-101",
            interaction_date="2026-09-01",
            tabular_features=[0.5] * 60,
            text_response="Feeling anxious",
            text_emotion_probabilities={"anxiety": 0.8},
            text_emotion_embedding=[0.01] * 768,
            stress_probability=0.75,
            stress_embedding=[0.02] * 768,
            audio_path="datasets/ravdess/sample.wav",
            audio_emotion_probabilities={"fearful": 0.85},
            audio_embedding=[0.03] * 768,
        )

        self.assertTrue(rec.modality_availability["tabular"])
        self.assertTrue(rec.modality_availability["text"])
        self.assertTrue(rec.modality_availability["audio"])

        rec_dict = rec.to_dict()
        restored = MultimodalInputRecord.from_dict(rec_dict)

        self.assertEqual(restored.case_id, "CASE-101")
        self.assertEqual(restored.stress_probability, 0.75)
        self.assertEqual(restored.modality_availability, rec.modality_availability)

    def test_from_ml_input_factory(self) -> None:
        """Verifies record creation directly from an assembled MLInput object."""
        current = preprocess_interaction({
            "case_id": "CASE-202",
            "interaction_date": "2026-09-02",
            "text_response": "Need help urgently",
            "safety_response": 2,
            "fear_level": 4,
        })
        text_feat = extract_text_features(current)
        beh_feat = extract_behavioural_features(current)
        eng_feat = extract_engagement_features(current)
        long_feat = extract_longitudinal_features(current)
        voice_feat = VoiceFeatures(voice_available=True, speech_rate=3.0)

        ml_input = assemble_ml_input(
            text_features=text_feat,
            behavioural_features=beh_feat,
            engagement_features=eng_feat,
            longitudinal_features=long_feat,
            voice_features=voice_feat,
            case_id="CASE-202",
            interaction_date="2026-09-02",
        )

        rec = MultimodalInputRecord.from_ml_input(
            ml_input=ml_input,
            text_response=current.text.clean if current.text else None,
            stress_prob=0.6,
        )

        self.assertEqual(rec.case_id, "CASE-202")
        self.assertEqual(len(rec.tabular_features), TOTAL_FEATURES_COUNT)
        self.assertTrue(rec.modality_availability["tabular"])
        self.assertTrue(rec.modality_availability["text"])
        self.assertFalse(rec.modality_availability["audio"])

    def test_none_not_equal_zero_invariant_in_dataset(self) -> None:
        """Verifies that missing features in tabular input receive an explicit mask=0.0."""
        # 10 features provided, 50 features None
        partial_features = [0.5] * 10 + [None] * 50
        rec = MultimodalInputRecord(
            case_id="CASE-303",
            interaction_date="2026-09-03",
            tabular_features=partial_features,
        )
        ds = MultimodalFusionDataset([rec])
        batch = ds.get_batch([0])

        mask = batch["tabular_mask"][0]
        vals = batch["tabular_values"][0]

        self.assertEqual(sum(mask[:10]), 10.0)
        self.assertEqual(sum(mask[10:]), 0.0)
        # Missing values are zeroed in input tensor, but explicitly flagged by mask=0
        self.assertEqual(sum(vals[10:]), 0.0)

    def test_case_level_split_no_leakage(self) -> None:
        """Ensures that case-level split guarantees zero case overlap and detects leakage."""
        records = build_synthetic_multimodal_records(count=60, seed=self.seed)
        train_recs, val_recs = split_multimodal_records_by_case(records, val_ratio=0.25, seed=self.seed)

        train_cases = set(r.case_id for r in train_recs)
        val_cases = set(r.case_id for r in val_recs)

        self.assertTrue(len(train_cases) > 0)
        self.assertTrue(len(val_cases) > 0)
        self.assertEqual(len(train_cases.intersection(val_cases)), 0)

    def test_parameter_counts_breakdown(self) -> None:
        """Verifies calculation of trainable head parameters, frozen backbones, and total parameters."""
        model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)
        counts = model.get_parameter_counts()

        # Head parameters: 15,488 + 102,144 + 99,456 + 1,155 + 98,560 + 15,420 = 332,223
        self.assertEqual(counts["trainable_head_parameters"], 332_223)
        self.assertEqual(counts["backbone_parameters"], FROZEN_BACKBONES_PARAM_COUNT)
        self.assertEqual(counts["total_parameters_if_instantiated"], 230_106_303)
        self.assertEqual(counts["actually_instantiated_parameters"], 332_223)

    def test_forward_pass_and_l2_norm(self) -> None:
        """Verifies forward pass produces 256-dim embedding on unit sphere."""
        model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)
        rec = MultimodalInputRecord(
            case_id="CASE-404",
            interaction_date="2026-09-04",
            tabular_features=[0.4] * 60,
            text_response="Testing forward pass",
            text_emotion_embedding=[0.05] * 768,
            audio_embedding=[0.02] * 768,
        )
        res = model.fuse(rec)

        fused_emb = res["fused_embedding"]
        self.assertEqual(len(fused_emb), 256)

        norm = math.sqrt(sum(x * x for x in fused_emb))
        self.assertAlmostEqual(norm, 1.0, places=3)

    def test_modality_gating_weights(self) -> None:
        """Verifies dynamic modality weights sum to 1.0 and drop to 0.0 for absent modalities."""
        model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)

        # 1. All modalities present
        rec_all = MultimodalInputRecord(
            case_id="CASE-505",
            interaction_date="2026-09-05",
            tabular_features=[0.5] * 60,
            text_emotion_embedding=[0.01] * 768,
            audio_embedding=[0.01] * 768,
        )
        res_all = model.fuse(rec_all)
        weights_all = res_all["modality_weights"]
        self.assertAlmostEqual(sum(weights_all.values()), 1.0, places=3)
        self.assertTrue(weights_all["tabular"] > 0.0)
        self.assertTrue(weights_all["text"] > 0.0)
        self.assertTrue(weights_all["audio"] > 0.0)

        # 2. Audio missing
        rec_no_audio = MultimodalInputRecord(
            case_id="CASE-505",
            interaction_date="2026-09-05",
            tabular_features=[0.5] * 60,
            text_emotion_embedding=[0.01] * 768,
            audio_embedding=None,
        )
        res_no_audio = model.fuse(rec_no_audio)
        weights_no_audio = res_no_audio["modality_weights"]
        self.assertAlmostEqual(sum(weights_no_audio.values()), 1.0, places=3)
        self.assertEqual(weights_no_audio["audio"], 0.0)
        self.assertTrue(weights_no_audio["tabular"] > 0.0)
        self.assertTrue(weights_no_audio["text"] > 0.0)

        # 3. Text missing
        rec_no_text = MultimodalInputRecord(
            case_id="CASE-505",
            interaction_date="2026-09-05",
            tabular_features=[0.5] * 60,
            text_emotion_embedding=None,
            audio_embedding=[0.01] * 768,
        )
        res_no_text = model.fuse(rec_no_text)
        weights_no_text = res_no_text["modality_weights"]
        self.assertAlmostEqual(sum(weights_no_text.values()), 1.0, places=3)
        self.assertEqual(weights_no_text["text"], 0.0)
        self.assertTrue(weights_no_text["audio"] > 0.0)

    def test_train_step_decreases_loss(self) -> None:
        """Verifies forward, loss, backward, and optimizer update decreases reconstruction loss."""
        model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)
        records = build_synthetic_multimodal_records(count=16, seed=self.seed)
        ds = MultimodalFusionDataset(records)
        batch = ds.get_batch(list(range(16)))

        initial_loss = model.train_step(batch, lr=1e-2)
        losses = [initial_loss]
        for _ in range(5):
            l = model.train_step(batch, lr=1e-2)
            losses.append(l)

        final_loss = losses[-1]
        self.assertLess(final_loss, initial_loss)

    def test_checkpoint_save_and_reload(self) -> None:
        """Verifies checkpoint saving and reloading produces bit-exact inference."""
        model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)
        rec = build_synthetic_multimodal_records(count=1, seed=self.seed)[0]
        pred_before = model.fuse(rec)

        with tempfile.TemporaryDirectory() as tmp_dir:
            chk_path = Path(tmp_dir) / "checkpoint.pt"
            model.save_checkpoint(chk_path, epoch=1, metrics={"loss": 0.5})
            self.assertTrue(chk_path.exists())

            reloaded_model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)
            reloaded_model.load_checkpoint(chk_path)
            pred_after = reloaded_model.fuse(rec)

            self.assertEqual(pred_before["fused_embedding"], pred_after["fused_embedding"])
            self.assertEqual(pred_before["modality_weights"], pred_after["modality_weights"])

    def test_clinical_boundary_enforcement(self) -> None:
        """Strictly tests that enforce_fusion_boundary rejects clinical distress and diagnostic outputs."""
        # Allowed representation names
        enforce_fusion_boundary("fused_embedding")
        enforce_fusion_boundary("modality_weights")
        enforce_fusion_boundary("reconstructed_tabular")

        # Forbidden clinical output names
        forbidden = [
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
        ]
        for term in forbidden:
            with self.assertRaises(ValueError):
                enforce_fusion_boundary(term)

    def test_export_artifacts_structure(self) -> None:
        """Verifies that model export writes weights, config, metadata, metrics, and modality schema."""
        model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "exported_fusion"
            export_paths = model.export(out_dir, metrics={"validation_reconstruction_loss": 0.12})

            expected_files = ["weights", "config.json", "metadata.json", "metrics.json", "modality_schema.json"]
            for fname in expected_files:
                p = out_dir / fname
                self.assertTrue(p.exists(), f"Missing exported file: {fname}")

            # Validate metadata assertions and execution_mode
            with open(out_dir / "metadata.json", "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.assertEqual(meta["model_name"], "aaroh-multimodal-fusion")
            self.assertEqual(meta["feature_version"], "3.1.0")
            self.assertIn("execution_mode", meta)
            self.assertEqual(meta["execution_mode"], model.execution_mode)
            self.assertTrue(len(meta["clinical_boundary_assertions"]) > 0)

    def test_execution_mode_selection_and_no_backbone_in_fallback(self) -> None:
        """Verifies correct execution mode selection and that NO backbones are instantiated in FALLBACK mode."""
        # 1. Default without torch is FALLBACK
        fallback_model = MultimodalFusionModel(fusion_dim=256, seed=self.seed)
        self.assertEqual(fallback_model.execution_mode, "FALLBACK")
        self.assertIsNone(fallback_model.text_backbone)
        self.assertIsNone(fallback_model.audio_backbone)

        # 2. Invalid mode raises ValueError
        with self.assertRaises(ValueError):
            MultimodalFusionModel(fusion_dim=256, force_mode="INVALID_MODE")

        # 3. Forcing valid modes
        frozen_model = MultimodalFusionModel(fusion_dim=256, force_mode="PYTORCH_FROZEN")
        self.assertEqual(frozen_model.execution_mode, "PYTORCH_FROZEN")

        finetune_model = MultimodalFusionModel(fusion_dim=256, force_mode="PYTORCH_FINETUNE")
        self.assertEqual(finetune_model.execution_mode, "PYTORCH_FINETUNE")

    def test_parameter_accounting_across_all_three_modes(self) -> None:
        """Verifies exact parameter counts across FALLBACK, PYTORCH_FROZEN, and PYTORCH_FINETUNE."""
        # 1. FALLBACK mode
        fallback_model = MultimodalFusionModel(fusion_dim=256, force_mode="FALLBACK")
        counts_fb = fallback_model.get_parameter_counts()
        self.assertEqual(counts_fb["trainable_head_parameters"], 332_223)
        self.assertEqual(counts_fb["backbone_parameters"], 229_774_080)
        self.assertEqual(counts_fb["total_parameters_if_instantiated"], 230_106_303)
        self.assertEqual(counts_fb["actually_instantiated_parameters"], 332_223)
        self.assertEqual(counts_fb["total_trainable_parameters"], 332_223)

        # 2. PYTORCH_FROZEN mode
        frozen_model = MultimodalFusionModel(fusion_dim=256, force_mode="PYTORCH_FROZEN")
        counts_fz = frozen_model.get_parameter_counts()
        self.assertEqual(counts_fz["trainable_head_parameters"], 332_223)
        self.assertEqual(counts_fz["backbone_parameters"], 229_774_080)
        self.assertEqual(counts_fz["total_parameters_if_instantiated"], 230_106_303)
        self.assertEqual(counts_fz["actually_instantiated_parameters"], 230_106_303)
        self.assertEqual(counts_fz["frozen_backbone_parameters"], 229_774_080)
        self.assertEqual(counts_fz["total_trainable_parameters"], 332_223)

        # 3. PYTORCH_FINETUNE mode
        finetune_model = MultimodalFusionModel(fusion_dim=256, force_mode="PYTORCH_FINETUNE")
        counts_ft = finetune_model.get_parameter_counts()
        self.assertEqual(counts_ft["trainable_head_parameters"], 332_223)
        self.assertEqual(counts_ft["backbone_parameters"], 229_774_080)
        self.assertEqual(counts_ft["total_parameters_if_instantiated"], 230_106_303)
        self.assertEqual(counts_ft["actually_instantiated_parameters"], 230_106_303)
        self.assertEqual(counts_ft["frozen_backbone_parameters"], 0)
        self.assertEqual(counts_ft["total_trainable_parameters"], 230_106_303)

    def test_metadata_records_execution_mode(self) -> None:
        """Verifies that exported metadata.json contains the explicit execution_mode."""
        model = MultimodalFusionModel(fusion_dim=256, force_mode="FALLBACK")
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "export_meta"
            model.export(out_dir)
            with open(out_dir / "metadata.json", "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.assertEqual(meta["execution_mode"], "FALLBACK")
            self.assertIn("instantiation_note", meta)
            self.assertIn("In FALLBACK mode", meta["instantiation_note"])


if __name__ == "__main__":
    unittest.main()
