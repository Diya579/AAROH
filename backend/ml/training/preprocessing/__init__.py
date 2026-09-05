"""AAROH Dataset Ingestion and Preprocessing package (Slice 3.2).

Provides preprocessing pipelines for auxiliary training datasets:
- GoEmotions Hindi Adaptation (translated fine-grained emotion classification)
- GoEmotions (English fine-grained multilabel emotion classification)
- Dreaddit (social media stress and psychological indicators)
- RAVDESS (multimodal speech emotion audio)
- Real EmoInHindi (official conversational dataset placeholder)
"""

from backend.ml.training.preprocessing.common import (
    compute_dataset_stats,
    deterministic_sort,
    load_csv_records,
    load_tsv_records,
    normalize_text,
    read_jsonl,
    save_json,
    validate_required_columns,
    write_jsonl,
)
from backend.ml.training.preprocessing.preprocess_dreaddit import (
    detect_dreaddit_files,
    preprocess_dreaddit_file,
    process_dreaddit,
)
from backend.ml.training.preprocessing.preprocess_emoinhindi import (
    EMOINHINDI_EMOTIONS,
    detect_emoinhindi_files,
    preprocess_emoinhindi_split,
    process_emoinhindi,
)
from backend.ml.training.preprocessing.preprocess_goemotions import (
    DEFAULT_GOEMOTIONS_TAXONOMY,
    detect_goemotions_files,
    preprocess_goemotions_split,
    process_goemotions,
)
from backend.ml.training.preprocessing.preprocess_goemotions_hindi_adaptation import (
    GOEMOTIONS_HINDI_EMOTIONS,
    detect_goemotions_hindi_adaptation_files,
    preprocess_goemotions_hindi_adaptation_split,
    process_goemotions_hindi_adaptation,
)
from backend.ml.training.preprocessing.preprocess_ravdess import (
    RAVDESS_EMOTIONS,
    RAVDESS_INTENSITIES,
    RAVDESS_STATEMENTS,
    discover_ravdess_files,
    parse_ravdess_filename,
    preprocess_ravdess_directory,
    process_ravdess,
)
from backend.ml.training.preprocessing.preprocess_real_emoinhindi import (
    REAL_EMOINHINDI_EMOTIONS,
    preprocess_real_emoinhindi_split,
    process_real_emoinhindi,
)
from backend.ml.training.preprocessing.run_all import run_all_preprocessing

__all__ = [
    # Common utilities
    "normalize_text",
    "load_csv_records",
    "load_tsv_records",
    "write_jsonl",
    "read_jsonl",
    "validate_required_columns",
    "deterministic_sort",
    "compute_dataset_stats",
    "save_json",
    # GoEmotions Hindi Adaptation
    "GOEMOTIONS_HINDI_EMOTIONS",
    "process_goemotions_hindi_adaptation",
    "preprocess_goemotions_hindi_adaptation_split",
    "detect_goemotions_hindi_adaptation_files",
    # EmoInHindi (backward compatibility aliases)
    "process_emoinhindi",
    "preprocess_emoinhindi_split",
    "detect_emoinhindi_files",
    "EMOINHINDI_EMOTIONS",
    # Real EmoInHindi (Official Conversational Placeholder)
    "REAL_EMOINHINDI_EMOTIONS",
    "process_real_emoinhindi",
    "preprocess_real_emoinhindi_split",
    # GoEmotions (English)
    "process_goemotions",
    "preprocess_goemotions_split",
    "detect_goemotions_files",
    "DEFAULT_GOEMOTIONS_TAXONOMY",
    # Dreaddit
    "process_dreaddit",
    "preprocess_dreaddit_file",
    "detect_dreaddit_files",
    # RAVDESS
    "process_ravdess",
    "preprocess_ravdess_directory",
    "discover_ravdess_files",
    "parse_ravdess_filename",
    "RAVDESS_EMOTIONS",
    "RAVDESS_INTENSITIES",
    "RAVDESS_STATEMENTS",
    # Orchestrator
    "run_all_preprocessing",
]
