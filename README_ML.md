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
- **Slice 3.4**: Audio emotion representation model (`backend/ml/training/models/audio_emotion/`).

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

## 5. Slice 3.4: Audio Emotion Representation Model

Slice 3.4 provides an audio representation encoder trained on the speech-only RAVDESS dataset (`Actor_01` to `Actor_24`, speech statements 01-02, excluding songs) to output reusable audio emotion representations and embeddings.

```
backend/ml/training/models/audio_emotion/
├── __init__.py               # Exports dataset, model, and constant definitions
├── dataset.py                # RavdessDataset with lazy loading, 16kHz resampling, and actor splitting
└── model.py                  # AudioEmotionModel (wav2vec 2.0 backbone, frozen/unfrozen, projection head)
```

### Architecture & Capabilities
- **Backbone**: `facebook/wav2vec2-base` (768-dim latent space).
- **Backbone Status**: **Frozen by default** (trains linear classification and projection heads only, ~6,152 parameters). Full fine-tuning can be enabled via `--unfreeze-backbone`.
- **Audio Preprocessing**:
  - Resampling to 16,000 Hz mono (via `torchaudio`/`librosa` with deterministic interpolation fallback).
  - Amplitude normalization to $[-1.0, 1.0]$.
  - Fixed-length padding or center truncation to 80,000 samples (5.0 seconds).
  - **Lazy Loading**: Audio waveforms are read from disk during iteration to preserve RAM.
- **Actor-Level Splitting**:
  - Programmatic, deterministic actor-level split with `seed=42`.
  - Strict validation ensures $\text{Actors}_{\text{train}} \cap \text{Actors}_{\text{val}} = \emptyset$ (zero actor leakage).
- **Model Outputs**:
  - `audio_emotion_probabilities`: 8-class probability distribution (`neutral`, `calm`, `happy`, `sad`, `angry`, `fearful`, `disgust`, `surprised`).
  - `audio_embedding`: 768-dim latent audio representation vector.
- **Reusable Public Inference Interface**:
  ```python
  from backend.ml.training.models.audio_emotion import AudioEmotionModel

  model = AudioEmotionModel()
  result = model.predict_audio_embedding(waveform)
  # Returns: {"audio_embedding": [...], "audio_emotion_probabilities": {...}}
  ```
  *(To be consumed directly in future Slice 3.5 feature fusion).*

### Strict Architectural & Clinical Boundaries
- **Clinical Invariant**: `Audio Emotion != Clinical Distress`.
  - The model outputs exclusively acoustic emotional affect representations.
  - It NEVER outputs `distress_score`, `escalation_probability`, `depression_prediction`, `anxiety_prediction`, `risk_level`, or `clinical_diagnosis`.
- **Voice Service Invariant**:
  - Low-level acoustic and conversational dynamics (ASR transcription, Voice Activity Detection / VAD, speech rate, pause ratio, pitch variability, energy variation, response latency, audio quality metrics, baseline acoustic deviation) belong strictly to **Diya's Voice Service** and are NOT duplicated or handled by this model.

---

## 6. Training & Evaluation Workflows (Google Colab Ready)

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

# 4. Train Audio Emotion Representation Model (RAVDESS)
python3 train_audio_emotion.py \
    --data-dir datasets/processed \
    --output-dir models/audio_emotion \
    --backbone facebook/wav2vec2-base \
    --batch-size 16 \
    --lr 1e-4 \
    --epochs 10 \
    --seed 42 \
    --fp16 \
    --drive-checkpoint-dir /content/drive/MyDrive/aaroh_checkpoints/audio_emotion

# Fast Smoke-Test Execution (Single Epoch / Small Batch)
python3 train_audio_emotion.py --smoke-test
```

### Comprehensive Evaluation Suite
```bash
# Evaluate Text Representation Models:
python3 evaluate_text_models.py --model-type all --models-dir models/ --data-dir datasets/processed/

# Evaluate Audio Emotion Representation Model:
python3 evaluate_audio_model.py --model-dir models/audio_emotion/ --data-dir datasets/processed/
```
Metrics produced:
- **Text Emotion**: Accuracy, Precision, Recall, Macro F1, Weighted F1.
- **Stress**: Accuracy, Precision, Recall, F1, ROC-AUC.
- **Mental Health Representation**: Mean embedding norm, Cosine separation, Domain alignment.
- **Audio Emotion**: Overall Accuracy, Precision, Recall, Macro F1, Weighted F1, Confusion Matrix, Per-Class Accuracy for all 8 RAVDESS emotions.

---

## 7. Model Export Structure

Models exported under `models/<model_name>/` save the following standard artifacts:
- `pytorch_model.bin` / `weights` (model weights)
- `tokenizer_config.json` / `tokenizer` (tokenizer parameters & configuration)
- `preprocessor_config.json` (audio sampling rate, duration, normalization params)
- `config.json` (architecture hyper-parameters & dimensions)
- `label_mapping.json` (class index mappings)
- `metrics.json` (validation and test performance metrics)
- `metadata.json` (containing `model_version`, `dataset_version`, `training_date`, `hyperparameters`, and clinical boundary assertions)

---

## 8. Clinical & Regulatory Boundary Invariant

> [!IMPORTANT]
> AAROH ML models and features operate exclusively as **clinical decision support**.
> - Datasets and models do NOT provide psychiatric diagnoses.
> - `emotion != distress`
> - `stress != distress`
> - `audio_emotion != distress`
> - `PHQ != AAROH distress`
> - ML features never override human clinician judgments.
> - Missing data must remain `None` and must never be fabricated as zero.

