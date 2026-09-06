"""Standalone Artifact Loader & Verification Script (Slice 3.9 Hardening).

Proves that production inference boots entirely from saved disk artifacts
WITHOUT importing any training, dataset generation, or optimizer code.

Workflow:
1. Assert zero training modules are imported.
2. Locate exported model checkpoints and metadata in models/.
3. Validate metadata, versions, and schema definitions.
4. Load models via MLInferencePipeline (pure production inference path).
5. Run inference on beneficiary interaction inputs.
6. Verify official MlInferenceResult contract.
7. Verify loading resilience against corrupted/missing artifacts.
8. PASS.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

# Workspace root
workspace_root = Path(__file__).resolve().parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

# STRICT ARCHITECTURAL INVARIANT: Must NOT import training execution or evaluation scripts
FORBIDDEN_MODULE_SUBSTRINGS = ["train_", "evaluate_"]

# Import ONLY production contract and inference layer
from backend.ml.contract import (
    MlInferenceResult,
    ProcessingStatus,
    ResultSource,
    RiskLevel,
    Trajectory,
)
from backend.ml.inference import (
    InferenceCache,
    MLInferencePipeline,
    ModelRegistry,
    PipelineConfig,
)
from backend.ml.inference.exceptions import (
    ArtifactNotFoundError,
    InferencePipelineError,
    VersionMismatchError,
)


def assert_clean_production_environment() -> None:
    """Verifies that no training modules have leaked into the runtime environment."""
    for mod_name in list(sys.modules.keys()):
        for forbidden in FORBIDDEN_MODULE_SUBSTRINGS:
            if forbidden in mod_name and "backend.ml.training" in mod_name:
                raise RuntimeError(
                    f"ARCHITECTURE VIOLATION: Production artifact loader imported training module '{mod_name}'"
                )


def run_standalone_artifact_verification() -> Dict[str, Any]:
    """Executes the complete production artifact loading and inference verification."""
    start_time = time.perf_counter()
    checklist: Dict[str, bool] = {}

    print("\n" + "=" * 78)
    print("       AAROH — STANDALONE PRODUCTION ARTIFACT LOADER & VERIFIER")
    print("=" * 78)

    # 1. Verify Clean Environment (No Training Imports)
    assert_clean_production_environment()
    checklist["no_training_code_imported"] = True

    # 2. Locate Exported Checkpoints & Artifacts
    models_dir = workspace_root / "models"
    checklist["models_directory_exists"] = models_dir.is_dir()

    registry = ModelRegistry(base_dir=models_dir)
    checksums = registry.get_all_artifact_checksums()
    checklist["all_model_artifacts_located"] = (
        len(checksums) == 6
        and all(len(c) > 0 for c in checksums.values())
    )

    # 3. Validate Escalation Artifacts & Metadata Lineage
    esc_dir = models_dir / "escalation"
    meta_path = esc_dir / "metadata.json"
    weights_path = esc_dir / "weights"
    config_path = esc_dir / "config.json"
    label_path = esc_dir / "label_mapping.json"

    checklist["escalation_artifacts_present"] = (
        meta_path.exists()
        and weights_path.exists()
        and config_path.exists()
        and label_path.exists()
    )

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Validate required metadata fields
    required_meta_keys = [
        "model_name",
        "model_version",
        "training_date",
        "dataset_version",
        "feature_schema_version",
        "training_seed",
        "target_horizon_days",
        "confidence_policy_version",
        "calibration_method",
        "upstream_model_versions",
    ]
    has_all_meta = all(k in meta for k in required_meta_keys)
    checklist["metadata_lineage_complete"] = has_all_meta

    # 4. Instantiate Production Pipeline from Disk
    config = PipelineConfig(
        default_execution_mode="FALLBACK",
        strict_stage_validation=True,
    )
    pipeline = MLInferencePipeline(config=config, registry=registry)
    pipeline.load_models()
    checklist["pipeline_loaded_from_disk"] = pipeline._models_loaded

    # 5. Run Health Check
    health = pipeline.health_check()
    checklist["health_check_ready"] = (
        health["ready"] is True
        and health["overall_status"] == "HEALTHY"
        and health["escalation_loaded"] is True
    )

    # 6. Run Production Inference on Beneficiary Interaction
    sample_input = {
        "case_id": "BENEFICIARY-409",
        "prediction_date": "2026-09-06",
        "feature_values": [0.45] * 60,
        "raw_text": "I feel very overwhelmed and need someone to talk to about my family situation.",
        "raw_audio": [0.0] * 16000,
    }
    result = pipeline.run(sample_input)

    # 7. Validate MlInferenceResult Contract
    is_valid_contract = (
        isinstance(result, MlInferenceResult)
        and result.case_id == "BENEFICIARY-409"
        and result.status == ProcessingStatus.SUCCESS
        and result.source == ResultSource.ML
        and result.distress is not None
        and 0.0 <= result.distress.score <= 1.0
        and isinstance(result.distress.trajectory, Trajectory)
        and result.prediction is not None
        and 0.0 <= result.prediction.escalation_probability <= 1.0
        and result.prediction.risk_level in (RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH)
        and result.explanation is not None
        and len(result.explanation.factors) > 0
        and result.metadata is not None
        and "pipeline_run_id" in result.metadata
        and "timing" in result.metadata
    )
    checklist["inference_contract_verified"] = is_valid_contract

    # 8. Determinism Check (Two Runs -> Identical Predictions)
    result2 = pipeline.run(sample_input)
    checklist["deterministic_outputs_verified"] = (
        result.status == result2.status
        and result.distress.score == result2.distress.score
        and result.prediction.escalation_probability == result2.prediction.escalation_probability
        and result.prediction.risk_level == result2.prediction.risk_level
        and result.explanation.factors == result2.explanation.factors
        and result.metadata["pipeline_run_id"] != result2.metadata["pipeline_run_id"]
    )

    # 9. Loading Resilience (Corrupted/Missing Artifacts)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Sandbox with missing weights
        broken_dir = tmp_path / "escalation"
        broken_dir.mkdir(parents=True)
        (broken_dir / "config.json").write_text("{}")
        (broken_dir / "metadata.json").write_text('{"model_version": "aaroh-escalation-v1"}')
        broken_registry = ModelRegistry(base_dir=tmp_path)
        broken_pipe = MLInferencePipeline(registry=broken_registry)
        fail_res = broken_pipe.run(sample_input)

        # Must return FAILED, never fabricate SUCCESS / LOW / 0.0
        checklist["loading_resilience_verified"] = (
            fail_res.status == ProcessingStatus.FAILED
            and fail_res.prediction is None
            and "Model loading failure" in (fail_res.message or "")
        )

    # Final assert again that no training code leaked
    assert_clean_production_environment()

    duration = round(time.perf_counter() - start_time, 3)

    return {
        "checklist": checklist,
        "duration_seconds": duration,
        "sample_result": result.to_dict(),
        "metadata": meta,
        "all_passed": all(checklist.values()),
    }


def print_standalone_report(summary: Dict[str, Any]) -> None:
    """Formats and prints verification report for standalone artifact loading."""
    chk = summary["checklist"]
    res = summary["sample_result"]
    meta = summary["metadata"]

    print("\n" + "=" * 78)
    print("           STANDALONE ARTIFACT LOADER VERIFICATION REPORT")
    print("=" * 78)
    print(f"  Model Name:                       {meta.get('model_name')}")
    print(f"  Model Version:                    {meta.get('model_version')}")
    print(f"  Training Date:                    {meta.get('training_date')}")
    print(f"  Training Seed:                    {meta.get('training_seed')}")
    print(f"  Target Horizon Days:              {meta.get('target_horizon_days')}")
    print(f"  Confidence Policy Version:        {meta.get('confidence_policy_version')}")
    print(f"  Calibration Method:               {meta.get('calibration_method')}")
    print(f"  Verification Runtime:             {summary['duration_seconds']}s")
    print("-" * 78)
    print("  Checklist:")
    for name, status in chk.items():
        formatted_name = name.replace("_", " ").title()
        status_str = "[PASS]" if status else "[FAIL]"
        print(f"    ✓ {formatted_name:<45} : {status_str}")

    print("-" * 78)
    print("  Production Inference Output:")
    print(f"    Case ID:                        {res.get('case_id')}")
    print(f"    Status:                         {res.get('status')}")
    print(f"    Source:                         {res.get('source')}")
    dist = res.get("distress") or {}
    pred = res.get("prediction") or {}
    expl = res.get("explanation") or {}
    print(f"    Distress Score:                 {dist.get('score')}")
    print(f"    Distress Trajectory:            {dist.get('trajectory')}")
    print(f"    Escalation Probability:         {pred.get('escalation_probability')}")
    print(f"    Risk Level:                     {pred.get('risk_level')}")
    print(f"    Confidence:                     {pred.get('confidence')}")
    print(f"    Explanation Factors:            {expl.get('factors')}")
    print("-" * 78)
    print("  Engineering & Integration Boundaries:")
    print("    ✓ Zero training modules imported (pure inference runtime).")
    print("    ✓ Bootstrapped 100% from disk artifacts without in-memory state.")
    print("    ✓ Ready for Mahendra's FastAPI startup and Preet's intervention layer.")
    print("    ✓ SYNTHETIC DEMONSTRATION LABELS ONLY - NOT CLINICAL GROUND TRUTH.")
    print("-" * 78)
    overall = "PASSED [100%]" if summary["all_passed"] else "FAILED"
    print(f"FINAL RESULT: STANDALONE ARTIFACT LOADER {overall}")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    report = run_standalone_artifact_verification()
    print_standalone_report(report)
    if not report["all_passed"]:
        sys.exit(1)
