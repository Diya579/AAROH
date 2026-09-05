# AAROH Machine Learning Subsystem

This document outlines the architecture, dataset pipelines, representation models, and feature engineering layers of the AAROH mental health decision-support platform.

---

## 1. Emotion & Mental Health Datasets Comparison

AAROH leverages diverse auxiliary datasets for multilingual emotion recognition, conversational context, and psychological distress indicators. To prevent data contamination and modeling errors, the following table clarifies the distinctions between the emotion datasets:

| Feature / Attribute | **GoEmotions (Original)** | **GoEmotions Hindi Adaptation (EmoHinD)** | **EmoInHindi (Official Benchmark)** |
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

#### 2. GoEmotions Hindi Adaptation (EmoHinD)
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
- **Slice 3.3**: Lightweight text representation models (`backend/ml/training/models/`).

---

## 4. Slice 3.3: Text Representation Models

Slice 3.3 provides lightweight text encoders trained on external datasets to output reusable representations and auxiliary predictions.

```
backend/ml/training/models/
├── common.py                 # Metadata, export manager, device selection, metrics, Colab utils
├── text_emotion/             # GoEmotions + EmoHinD multilingual emotion model
│   ├── model.py
│   └── dataset.py
├── stress/                   # Dreaddit stress model (stress != distress)
│   ├── model.py
│   └── dataset.py
└── mental_health_language/   # MindBridge screening language representation encoder
    ├── model.py
    └── dataset.py
```

### Models & Invariants

#### 1. Text Emotion Model
- **Datasets**: GoEmotions (English) + EmoHinD / GoEmotions Hindi Adaptation (Devanagari).
- **Backbone**: Default `distilbert-base-multilingual-cased` (or `xlm-roberta-base`).
- **Outputs**:
  - `emotion_probabilities`: 28-class normalized emotion distribution.
  - `emotion_embedding`: 768-dim latent text representation vector.
- **Strict Boundary**: Represents general emotional affect; does NOT predict AAROH clinical distress.

#### 2. Stress Model
- **Dataset**: Dreaddit social media stress corpus.
- **Backbone**: Default `distilbert-base-uncased`.
- **Outputs**:
  - `stress_probability`: Probability between 0.0 and 1.0 of linguistic stress.
  - `stress_embedding`: 768-dim latent text representation vector.
- **Strict Invariant**: `stress_probability != distress_score`. Stress probability measures colloquial linguistic expression and is NEVER renamed or treated as clinical distress.

#### 3. Mental Health Language Model
- **Dataset**: MindBridge screening language dataset.
- **Backbone**: Default `distilbert-base-uncased`.
- **Outputs**:
  - `mental_health_embedding`: 768-dim L2-normalized latent vector.
- **Strict Invariant**: Learns screening-oriented language representations only. Does NOT predict PHQ or GAD scores during inference. Does NOT perform clinical diagnoses.

---

## 5. Training & Evaluation Workflows (Google Colab Ready)

All training scripts feature Google Colab compatible settings (`fp16`, gradient accumulation, early stopping, Google Drive checkpointing, and `seed=42`).

### Training Commands
```bash
# 1. Train Text Emotion Model (GoEmotions + EmoHinD)
python3 train_text_emotion.py \
    --data-dir datasets/processed \
    --output-dir models/text_emotion \
    --model-name distilbert-base-multilingual-cased \
    --batch-size 32 \
    --lr 3e-5 \
    --epochs 5 \
    --gradient-accumulation-steps 2 \
    --fp16 \
    --seed 42 \
    --drive-checkpoint-dir /content/drive/MyDrive/aaroh_checkpoints/emotion

# 2. Train Stress Model (Dreaddit)
python3 train_stress.py \
    --data-dir datasets/processed \
    --output-dir models/stress \
    --model-name distilbert-base-uncased \
    --batch-size 16 \
    --lr 2e-5 \
    --epochs 5 \
    --fp16 \
    --seed 42 \
    --drive-checkpoint-dir /content/drive/MyDrive/aaroh_checkpoints/stress

# 3. Train Mental Health Language Model (MindBridge)
python3 train_mental_health.py \
    --data-dir datasets/processed \
    --output-dir models/mental_health_language \
    --model-name distilbert-base-uncased \
    --batch-size 16 \
    --lr 2e-5 \
    --epochs 5 \
    --fp16 \
    --seed 42 \
    --drive-checkpoint-dir /content/drive/MyDrive/aaroh_checkpoints/mental_health
```

### Comprehensive Evaluation Suite
Run evaluation across all models:
```bash
python3 evaluate_text_models.py --model-type all --models-dir models/ --data-dir datasets/processed/
```
Metrics produced:
- **Emotion**: Accuracy, Precision, Recall, Macro F1, Weighted F1.
- **Stress**: Accuracy, Precision, Recall, F1, ROC-AUC.
- **Mental Health Representation**: Mean embedding norm, Cosine separation, Domain alignment.

---

## 6. Model Export Structure

Models exported under `models/<model_name>/` save the following standard artifacts:
- `pytorch_model.bin` (model weights)
- `tokenizer_config.json` (tokenizer parameters & configuration)
- `config.json` (architecture hyper-parameters & dimensions)
- `label_mapping.json` (class index mappings)
- `metrics.json` (validation and test performance metrics)
- `metadata.json` (containing `model_version`, `dataset_version`, `training_date`, `hyperparameters`, and clinical boundary assertions)

---

## 7. Clinical & Regulatory Boundary Invariant

> [!IMPORTANT]
> AAROH ML models and features operate exclusively as **clinical decision support**.
> - Datasets and models do NOT provide psychiatric diagnoses.
> - `emotion != distress`
> - `stress != distress`
> - `PHQ != AAROH distress`
> - ML features never override human clinician judgments.
> - Missing data must remain `None` and must never be fabricated as zero.
