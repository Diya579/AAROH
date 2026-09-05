# AAROH Machine Learning Subsystem

This document outlines the architecture, dataset pipelines, and feature engineering layers of the AAROH mental health decision-support platform.

---

## 1. Emotion & Mental Health Datasets Comparison

AAROH leverages diverse auxiliary datasets for multilingual emotion recognition, conversational context, and psychological distress indicators. To prevent data contamination and modeling errors, the following table clarifies the distinctions between the emotion datasets:

| Feature / Attribute | **GoEmotions (Original)** | **GoEmotions Hindi Adaptation** | **EmoInHindi (Official Benchmark)** |
| :--- | :--- | :--- | :--- |
| **Language** | English (`en`) | Hindi (`hi`, Devanagari script) | Hindi (`hi`, Devanagari script) |
| **Data Format** | Single-turn Reddit comments | Single-turn comment translations | Multi-turn conversational dialogues |
| **Sample Count** | 54,263 comments (train: 43,410 / dev: 5,426 / test: 5,427) | 54,263 comments (train: 43,410 / dev: 5,426 / test: 5,427) | ~44,247 utterances across ~1,814 dialogues |
| **Dialogue Context** | None (independent comments) | None (independent comments) | Preserves conversational turns & speaker history |
| **Emotion Taxonomy** | 28 fine-grained emotions (Ekman + expansions + neutral) | 28 fine-grained emotions (identical to GoEmotions) | 16 conversational emotion classes |
| **Intensity Scoring** | No (binary multi-hot annotations) | No (binary multi-hot annotations) | Yes (explicit numerical emotion intensity) |
| **Repository Path** | `datasets/goemotions/` | `datasets/goemotions_hindi_adaptation/` | `datasets/emoinhindi/` or `datasets/real_emoinhindi/` |
| **Preprocess Module** | `preprocess_goemotions.py` | `preprocess_goemotions_hindi_adaptation.py` | `preprocess_real_emoinhindi.py` (placeholder) |
| **Verification Tool** | Automated schema detection | Automated schema detection | `verify_real_emoinhindi.py` |
| **Current Status** | Ingested & Preprocessed | Ingested & Preprocessed | Awaiting dataset files |

### Dataset Summaries

#### 1. GoEmotions (English)
- **Source**: Google Research GoEmotions corpus.
- **Role**: Provides fine-grained multi-label emotion supervision for English text interactions across 28 distinct emotional states.

#### 2. GoEmotions Hindi Adaptation
- **Source**: Direct Hindi adaptation/translation of GoEmotions (`emoHi-train.csv`, `emoHi-valid.csv`, `emoHi-test.csv`).
- **Role**: Provides auxiliary supervisory signals for understanding 28 fine-grained emotions in translated Hindi text, enabling multilingual alignment without fabricating conversational turns.

#### 3. EmoInHindi (Official Conversational Benchmark)
- **Source**: Academic benchmark for emotion recognition in multi-turn Hindi conversations (~1,814 dialogues, ~44,247 utterances, 16 classes).
- **Role**: Will supply native conversational emotion context, speaker turn transitions, and intensity labels once placed in the repository.
- **Verification**: Run `python3 verify_real_emoinhindi.py` to check presence and validate structure.

---

## 2. Dataset Preprocessing Pipeline (Slice 3.2)

Standardized preprocessors convert diverse raw corpora into deterministic, normalized `.jsonl` files in `datasets/processed/`:

```bash
# Run all preprocessing pipelines
python3 -m backend.ml.training.preprocessing.run_all
```

Outputs produced:
- `datasets/processed/goemotions_hindi_adaptation_{train,valid,test}.jsonl`
- `datasets/processed/goemotions_{train,dev,test}.jsonl`
- `datasets/processed/dreaddit_{train,test}.jsonl`
- `datasets/processed/ravdess_all.jsonl`
- `datasets/processed/dataset_statistics.json`

---

## 3. Machine Learning Architectural Slices

- **Slice 1**: Core ML contracts, interfaces, and confidence policy (`backend/ml/contracts/`).
- **Slice 2.1**: Preprocessing pipeline and text normalization (`backend/ml/preprocessing/`).
- **Slice 2.2**: Deterministic text feature extraction (`backend/ml/features/text/`).
- **Slice 2.3**: Behavioural feature extraction (`backend/ml/features/behaviour/`).
- **Slice 2.4**: Engagement feature extraction (`backend/ml/features/engagement/`).
- **Slice 2.5**: Longitudinal feature extraction (`backend/ml/features/longitudinal/`).
- **Slice 3.1**: ML input assembly & schema registry (`backend/ml/assembly/`).
- **Slice 3.2**: Auxiliary dataset ingestion & preprocessing (`backend/ml/training/preprocessing/`).

---

## 4. Clinical & Regulatory Boundary Invariant

> [!IMPORTANT]
> AAROH ML models and features operate exclusively as **clinical decision support**.
> - Datasets and models do NOT provide psychiatric diagnoses.
> - ML features never override human clinician judgments.
> - Missing data must remain `None` and must never be fabricated as zero.
