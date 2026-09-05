"""Unit tests for dataset ingestion and preprocessing pipelines (Slice 3.2).

Verifies:
- CSV and TSV loading (including headerless TSVs)
- Unicode text normalization and invisible control character cleanup
- Schema validation and descriptive errors on missing required columns
- Safe missing value preservation (no fabrication)
- Deterministic sorting and JSONL serialization
- Dataset statistics generation
- EmoInHindi label parsing and split processing
- GoEmotions multilabel parsing and taxonomy mapping
- Dreaddit dynamic schema detection and privacy filtering
- RAVDESS filename parsing and actor discovery
"""

import json
from pathlib import Path
import tempfile
import unittest

from backend.ml.training.preprocessing.common import (
    check_missing_fields,
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
    map_labels_to_names,
    parse_label_ids,
    preprocess_emoinhindi_split,
    process_emoinhindi,
)
from backend.ml.training.preprocessing.preprocess_goemotions import (
    parse_multilabel_ids,
    preprocess_goemotions_split,
    process_goemotions,
)
from backend.ml.training.preprocessing.preprocess_ravdess import (
    parse_ravdess_filename,
    preprocess_ravdess_directory,
    process_ravdess,
)


class TestDatasetPreprocessing(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # --- Common Utility Tests ---

    def test_unicode_normalization_and_invisible_chars(self) -> None:
        """Verifies NFKC normalization, whitespace collapse, and invisible character cleanup."""
        raw = "Hello\ufeff world\u200b with \u200eextra   spaces   and Devanagari: डर"
        normalized = normalize_text(raw)
        self.assertEqual(normalized, "Hello world with extra spaces and Devanagari: डर")

        # Test empty and None handling
        self.assertEqual(normalize_text(None), "")
        self.assertEqual(normalize_text("   "), "")

    def test_csv_and_tsv_loading(self) -> None:
        """Verifies CSV and TSV loaders."""
        csv_file = self.test_dir / "sample.csv"
        csv_file.write_text("id,text,label\n1,Sample text,0\n2,Another sample,1\n", encoding="utf-8")
        headers, rows = load_csv_records(csv_file)
        self.assertEqual(headers, ["id", "text", "label"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], "1")

        # TSV with default columns (headerless)
        tsv_file = self.test_dir / "sample.tsv"
        tsv_file.write_text("Hello\t27\tid_1\nWorld\t2\tid_2\n", encoding="utf-8")
        has_header, t_headers, t_rows = load_tsv_records(
            tsv_file, default_columns=["text", "labels", "id"]
        )
        self.assertFalse(has_header)
        self.assertEqual(t_headers, ["text", "labels", "id"])
        self.assertEqual(len(t_rows), 2)
        self.assertEqual(t_rows[0]["text"], "Hello")
        self.assertEqual(t_rows[0]["labels"], "27")

    def test_schema_validation_missing_columns(self) -> None:
        """Verifies schema validation fails with descriptive error when required columns are missing."""
        available = ["id", "comment"]
        required = ["text", "label"]
        with self.assertRaises(ValueError) as ctx:
            validate_required_columns(available, required, dataset_name="TestDataset")
        self.assertIn("TestDataset", str(ctx.exception))
        self.assertIn("missing required column(s)", str(ctx.exception))

    def test_deterministic_sorting_and_jsonl_roundtrip(self) -> None:
        """Verifies deterministic sorting and JSONL write/read roundtrip."""
        data = [
            {"id": "b", "val": 2},
            {"id": "a", "val": 1},
            {"id": "c", "val": 3},
        ]
        sorted_data = deterministic_sort(data, key_fields=["id"])
        self.assertEqual([d["id"] for d in sorted_data], ["a", "b", "c"])

        jsonl_path = self.test_dir / "test.jsonl"
        written_count = write_jsonl(sorted_data, jsonl_path)
        self.assertEqual(written_count, 3)

        read_records = read_jsonl(jsonl_path)
        self.assertEqual(read_records, sorted_data)

    def test_dataset_statistics_computation(self) -> None:
        """Verifies computation of sample counts, label distributions, and missing values."""
        records = [
            {"dataset": "test", "text": "hello", "label": "pos"},
            {"dataset": "test", "text": "world", "label": "neg"},
            {"dataset": "test", "text": "", "label": "pos"},
        ]
        stats = compute_dataset_stats("test", records, label_field="label", language="en")
        self.assertEqual(stats["sample_count"], 3)
        self.assertEqual(stats["label_counts"], {"neg": 1, "pos": 2})
        self.assertEqual(stats["missing_values"]["text"], 1)
        self.assertEqual(stats["missing_values"]["label"], 0)

    # --- EmoInHindi Tests ---

    def test_emoinhindi_label_parsing(self) -> None:
        """Verifies parsing of numpy-bracketed strings like '[27]', '[ 8 20]'."""
        self.assertEqual(parse_label_ids("[27]"), [27])
        self.assertEqual(parse_label_ids("[ 8 20]"), [8, 20])
        self.assertEqual(parse_label_ids("[2, 14]"), [2, 14])
        self.assertEqual(parse_label_ids(14), [14])

        names = map_labels_to_names([14, 27])
        self.assertEqual(names, ["fear", "neutral"])

    def test_emoinhindi_split_preprocessing(self) -> None:
        """Verifies EmoInHindi split ingestion without inventing missing values."""
        sample_csv = self.test_dir / "emoHi-train.csv"
        sample_csv.write_text(
            ",id,labels,text\n"
            "0,eebbqej,[27],मेरा पसंदीदा खाना\n"
            "1,ed7ypvh,[14],उसे खतरा महसूस कराने के लिए\n",
            encoding="utf-8",
        )
        records = preprocess_emoinhindi_split(sample_csv, split_name="train")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["language"], "hi")
        self.assertEqual(records[0]["dataset"], "emoinhindi")
        self.assertIsNone(records[0]["dialogue_id"])
        self.assertIsNone(records[0]["emotion_intensity"])
        self.assertEqual(records[0]["previous_turns"], [])

        # Record with fear label 14
        fear_rec = next(r for r in records if r["utterance_id"] == "ed7ypvh")
        self.assertEqual(fear_rec["emotion"], "fear")
        self.assertEqual(fear_rec["label_ids"], [14])

    # --- GoEmotions Tests ---

    def test_goemotions_multilabel_parsing(self) -> None:
        """Verifies parsing of GoEmotions comma-separated labels."""
        self.assertEqual(parse_multilabel_ids("27"), [27])
        self.assertEqual(parse_multilabel_ids("4,27"), [4, 27])
        self.assertEqual(parse_multilabel_ids([0, 1]), [0, 1])

    def test_goemotions_split_preprocessing(self) -> None:
        """Verifies GoEmotions TSV preprocessing."""
        sample_tsv = self.test_dir / "train.tsv"
        sample_tsv.write_text(
            "My favourite food is good.\t27\teebbqej\n"
            "I feel so afraid right now!\t14,25\ted7ypvh\n",
            encoding="utf-8",
        )
        taxonomy = ["admiration", "amusement", "anger", "annoyance", "approval", "caring",
                    "confusion", "curiosity", "desire", "disappointment", "disapproval",
                    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
                    "joy", "love", "nervousness", "optimism", "pride", "realization",
                    "relief", "remorse", "sadness", "surprise", "neutral"]

        records = preprocess_goemotions_split(sample_tsv, split_name="train", taxonomy=taxonomy)
        self.assertEqual(len(records), 2)
        fear_rec = next(r for r in records if r["id"] == "ed7ypvh")
        self.assertEqual(fear_rec["label_ids"], [14, 25])
        self.assertEqual(fear_rec["emotion_labels"], ["fear", "sadness"])

    # --- Dreaddit Tests ---

    def test_dreaddit_preprocessing_and_privacy(self) -> None:
        """Verifies Dreaddit preprocessing ignores user identities and extracts stress labels."""
        sample_csv = self.test_dir / "dreaddit.csv"
        sample_csv.write_text(
            "id,subreddit,author,text,label,confidence\n"
            "1,anxiety,secret_user,I am constantly overwhelmed by panic,1,0.85\n"
            "2,casualconversation,user2,Just enjoyed a quiet walk today,0,0.90\n",
            encoding="utf-8",
        )
        records = preprocess_dreaddit_file(sample_csv)
        self.assertEqual(len(records), 2)
        # Verify privacy: author is not present in the output
        for r in records:
            self.assertNotIn("author", r)
            self.assertIn("stress_label", r)
            self.assertIn("source_subreddit", r)

        r1 = next(r for r in records if r["source_subreddit"] == "anxiety")
        self.assertEqual(r1["stress_label"], 1)

    # --- RAVDESS Tests ---

    def test_ravdess_filename_parsing(self) -> None:
        """Verifies parsing of standard 7-part RAVDESS audio filenames."""
        fname = "03-01-06-02-01-01-12.wav"
        parsed = parse_ravdess_filename(fname)
        self.assertEqual(parsed["modality"], "speech")
        self.assertEqual(parsed["emotion"], "fearful")
        self.assertEqual(parsed["intensity"], "strong")
        self.assertEqual(parsed["statement"], "Kids are talking by the door")
        self.assertEqual(parsed["repetition"], "1st repetition")
        self.assertEqual(parsed["actor"], "12")

        # Invalid format raises ValueError
        with self.assertRaises(ValueError):
            parse_ravdess_filename("invalid-audio-name.wav")


if __name__ == "__main__":
    unittest.main()
