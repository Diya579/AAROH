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
- **Slice 3.5**: Multimodal feature fusion network (`backend/ml/training/models/fusion/`).
- **Slice 3.6**: Dynamic distress model (`backend/ml/training/models/distress/`).
- **Slice 3.7**: Longitudinal trajectory model (`backend/ml/training/models/trajectory/`).
- **Slice 3.8**: Escalation assessment model (`backend/ml/training/models/escalation/`).

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

## 6. Slice 3.5: Multimodal Feature Fusion Network

Slice 3.5 integrates structured tabular features, multilingual text representations, and acoustic audio representations into a unified multimodal latent embedding via dynamic cross-modal gating.

```
backend/ml/training/models/fusion/
├── __init__.py               # Exports MultimodalFusionModel, MultimodalInputRecord, dataset utilities
├── dataset.py                # MultimodalInputRecord container, MultimodalFusionDataset, case splitting
└── model.py                  # Gated Multimodal Fusion network with self-supervised reconstruction head
```

### Architecture & Gating Mechanism
- **Tabular Branch**: Projects 120-dim input (60 continuous/discrete features + 60 binary missingness indicators preserving `None != 0`) $\to$ 128-dim representation.
- **Text Branch**: Projects 797-dim input (768-dim text embedding + 28 GoEmotions probabilities + 1 Dreaddit stress probability) $\to$ 128-dim representation.
- **Audio Branch**: Projects 776-dim input (768-dim Wav2Vec 2.0 embedding + 8 RAVDESS emotion probabilities) $\to$ 128-dim representation.
- **Dynamic Modality Gating**:
  $$\text{Gate Logits} = W_{\text{gate}} \cdot [h_{\text{tab}}, h_{\text{text}}, h_{\text{audio}}] + b_{\text{gate}} \in \mathbb{R}^3$$
  Masked Softmax over available modalities ensures absent modalities (e.g. missing audio or absent text) automatically receive strictly `0.0` weight, with active modalities summing to `1.0`.
- **Fused Latent Space**:
  $$h_{\text{fused}} = \text{Normalize}_{L_2}\left(W_{\text{fusion}} \cdot [g_{\text{tab}} h_{\text{tab}}, g_{\text{text}} h_{\text{text}}, g_{\text{audio}} h_{\text{audio}}] + b_{\text{fusion}}\right) \in \mathbb{R}^{256}$$
- **Self-Supervised Reconstruction Head**:
  Maps $h_{\text{fused}} \to \hat{x}_{\text{tab}} \in \mathbb{R}^{60}$, optimizing masked Mean Squared Error (MSE) over observed tabular signals during representation training.

### Explicit Execution Modes
1. **`FALLBACK` Mode**:
   - Executes lightweight pure-Python mathematical forward/backward propagation without requiring PyTorch or HuggingFace transformers.
   - Pretrained transformer backbones are **referenced in configuration only** and are **NOT instantiated in memory**.
   - Parameters actually instantiated: **332,223** (trainable projection and fusion heads only).
2. **`PYTORCH_FROZEN` Mode**:
   - Instantiates configured HuggingFace backbones (`distilbert-base-multilingual-cased` and `facebook/wav2vec2-base`).
   - Freezes all backbone parameters (`requires_grad=False`, 229,774,080 parameters).
   - Trains only the 332,223 fusion head parameters.
3. **`PYTORCH_FINETUNE` Mode**:
   - Instantiates backbones and unfreezes them (`requires_grad=True` when `--unfreeze-backbone` is passed).
   - Trains all 230,106,303 parameters end-to-end on GPU.

### Exact Parameter Accounting
- **1. Trainable Head Parameters**: **332,223**
- **2. Backbone Parameters**: **229,774,080**
- **3. Total Parameters If Instantiated**: **230,106,303**
- **4. Parameters Actually Instantiated**: **332,223** (in `FALLBACK` mode) / **230,106,303** (in `PYTORCH_*` modes)

### Reusable Public Inference Interface
```python
from backend.ml.training.models.fusion import MultimodalFusionModel, MultimodalInputRecord

model = MultimodalFusionModel()
result = model.fuse(record)
# Returns:
# {
#     "fused_embedding": [0.042, -0.015, ..., 0.089],  # 256-dim unit sphere vector
#     "modality_weights": {"tabular": 0.397, "text": 0.387, "audio": 0.216},
#     "reconstructed_tabular": [...],
#     "active_modalities": ["tabular", "text", "audio"],
#     "fused_dimension": 256
# }
```

### Strict Clinical Boundaries
- `enforce_fusion_boundary()` programmatically blocks outputs with forbidden names (`distress_score`, `escalation_probability`, `risk_level`, `clinical_diagnosis`, `depression`, `anxiety`).
- Multimodal feature fusion outputs representations and modality weights exclusively; it NEVER predicts clinical distress or escalation.

---

## 7. Dynamic Distress Model (Slice 3.6)

The **Dynamic Distress Model** is the first AAROH-specific model. It converts the current fused multimodal representation alongside behavioral and engagement interaction feature slices into a **CURRENT** distress state representation.

### Architectural Pipeline
1. **Inputs (301 Dimensions)**:
   - Fused Multimodal Embedding from Slice 3.5: **256 dimensions** (unit sphere vector).
   - Behavioural Features Slice (from Slice 3.1): **8 values + 8 missingness indicator masks = 16 dimensions**.
   - Engagement Features Slice (from Slice 3.1): **13 values + 13 missingness indicator masks = 26 dimensions**.
   - Modality Gating Weights (from Slice 3.5): **3 dimensions** (`tabular`, `text`, `audio`).
   - *Strict Invariant*: Preserves `None != 0` via explicit missingness indicator masks.
   - *Boundary Constraint*: Consumes **current** interaction only. Does **NOT** consume future interactions, trajectories, longitudinal history, or previous distress states.
2. **Feature Projection**:
   - `Linear(301, 128)` + `ReLU`.
3. **Residual Feed Forward Block**:
   - `Linear(128, 128)` + `ReLU` + `Linear(128, 128)`.
   - Residual addition: $h_{\text{res}} = \text{ReLU}(h_{\text{proj}} + \text{FFN}(h_{\text{proj}}))$.
4. **128-Dimensional Distress Embedding**:
   - Learned latent vector normalized on the unit hypersphere: $h_{\text{distress}} = h_{\text{res}} / \|h_{\text{res}}\|_2$.
5. **Regression Head**:
   - `Linear(128, 64)` + `ReLU` + `Linear(64, 1)` + `Sigmoid` $\to$ continuous `distress_score` $\in [0.0, 1.0]$.
6. **Configurable Threshold Mapper**:
   - Categorizes continuous score into discrete distress levels:
     - `LOW`: $[0.0, 0.25)$
     - `MODERATE`: $[0.25, 0.55)$
     - `HIGH`: $[0.55, 0.80)$
     - `CRITICAL`: $[0.80, 1.0]$

### Training Supervision & Smoke-Test Disclaimers
> [!WARNING]
> - **Smoke-test metrics are intended only to verify that the training, checkpointing, inference, and evaluation pipelines function correctly. They are NOT indicators of real-world model performance.**
> - **Synthetic demonstration labels are used solely for engineering verification and architecture validation. They are NOT clinical ground truth.**
>
> Public machine learning corpora do not contain clinical AAROH distress labels. The Dynamic Distress Model is trained and verified exclusively using deterministic synthetic demonstration supervision. These labels demonstrate pipeline mechanics, gradient descent convergence, and zero-leakage case-level splits, and **MUST NEVER** be interpreted as clinically validated ground truth.

### Versioned Threshold Configuration
Thresholds are versioned and stored directly within the model configuration:
- Primary location: embedded in `models/distress/config.json` under `threshold_configuration`
- Legacy fallback location: `models/distress/thresholds.json`

Schema (`config.json` snippet):
```json
{
  "model_type": "dynamic_distress_model",
  "model_version": "aaroh-distress-v1",
  "threshold_configuration": {
    "version": "1.0",
    "model_version": "aaroh-distress-v1",
    "thresholds": {
      "low": 0.25,
      "moderate": 0.55,
      "high": 0.80
    },
    "disclaimer": "Synthetic demonstration labels are used solely for engineering verification and architecture validation. They are NOT clinical ground truth."
  },
  "thresholds": {
    "low": 0.25,
    "moderate": 0.55,
    "high": 0.80
  }
}
```
During model loading (`load_checkpoint` or `DynamicDistressModel(config_path=...)`), thresholds are dynamically loaded by checking the primary `config.json` first, falling back to legacy `thresholds.json` if present, or defaulting to `DEFAULT_THRESHOLDS` (0.25, 0.55, 0.80). This eliminates unneeded standalone files while guaranteeing backwards compatibility and versioned governance.

### Explicit Execution Modes
1. **`FALLBACK` Mode**:
   - Lightweight pure-Python neural forward and backward propagation.
   - Pretrained transformer backbones are **referenced in configuration and metadata only** and are **NOT instantiated in memory**.
   - Parameters actually instantiated: **80,001** (trainable projection, residual, and regression heads only).
2. **`PYTORCH_FROZEN` Mode**:
   - Instantiates configured PyTorch neural module and references HuggingFace backbones with `requires_grad=False`.
   - Trains only the 80,001 distress model parameters.
3. **`PYTORCH_FINETUNE` Mode**:
   - Instantiates backbones and unfreezes them (`requires_grad=True` when `--unfreeze-backbone` is passed) for end-to-end gradient updates.

### Exact Parameter Accounting
- **1. Trainable Parameters**: **80,001**
  - Feature Projection: $301 \times 128 + 128 = 38,656$
  - Residual Layer 1: $128 \times 128 + 128 = 16,512$
  - Residual Layer 2: $128 \times 128 + 128 = 16,512$
  - Regression Hidden: $128 \times 64 + 64 = 8,256$
  - Regression Output: $64 \times 1 + 1 = 65$
  - Total Trainable Parameters: $38,656 + 16,512 + 16,512 + 8,256 + 65 = 80,001$
- **2. Upstream Backbone Parameters**: **229,774,080** (DistilBERT: 134,734,080 + Wav2Vec2: 95,040,000)
- **3. Total Parameters If Instantiated**: **229,854,081** ($80,001 + 229,774,080$)
- **4. Parameters Actually Instantiated**: **80,001** (in `FALLBACK` mode) / **229,854,081** (in `PYTORCH_*` modes)

### Reusable Public Inference Interface & Model Version Tracking
```python
from backend.ml.training.models.distress import DynamicDistressModel, DistressInputRecord

model = DynamicDistressModel()
result = model.predict_distress(record)
# Returns:
# {
#     "distress_embedding": [0.038, -0.012, ..., 0.091],  # 128-dim unit vector
#     "distress_score": 0.4834,                           # continuous [0.0, 1.0]
#     "distress_level": "MODERATE",                       # LOW / MODERATE / HIGH / CRITICAL
#     "model_version": "aaroh-distress-v1"                # internal model version tracking
# }
```

### Strict Clinical & Architectural Boundaries
- `enforce_distress_boundary()` programmatically blocks outputs with forbidden names (`diagnosis`, `clinical_diagnosis`, `escalation`, `escalation_probability`, `future_risk`, `future_prediction`, `depression`, `anxiety`, `ptsd`, `suicide_risk`, `treatment_recommendation`, `intervention_recommendation`).
- Dynamic Distress Model outputs ONLY current distress state representations (`distress_embedding`, `distress_score`, `distress_level`, `model_version`).
- NEVER predicts psychiatric diagnoses, escalation, future trajectory, or treatment recommendations.

---

## 8. Longitudinal Trajectory Model (Slice 3.7)

The **Longitudinal Trajectory Model** models how an individual's distress state evolves across ordered interactions over time.

### Model Purpose: Temporal Progression (NOT Current Distress)
- Estimates **how an individual is changing over time** (direction and velocity of progression).
- It is **NOT** "How distressed are they?" (which is modeled exclusively by Slice 3.6).
- Does **NOT** perform escalation prediction, confidence estimation, intervention planning, or clinical diagnosis.

### Trajectory Categories
- `STABLE`: Distress state remains consistent across the recent interaction window.
- `IMPROVING`: Distress state exhibits a significant downward trajectory over recent interactions.
- `WORSENING`: Distress state exhibits a gradual upward progression over recent interactions.
- `RAPIDLY_WORSENING`: Distress state exhibits sharp escalation across consecutive interactions.

### Fixed History Window & Sequence Handling
- Configurable history window (default: `history_window = 10`).
- **If interactions < history_window**: Left-padded with zero vectors while preserving chronological order. Padded timesteps are marked with `padding_mask = True` and ignored during recurrent/pooling processing.
- **If interactions == history_window**: Consumed directly (`padding_mask = all False`).
- **If interactions > history_window**: Truncates to retain **ONLY the most recent `history_window` interactions**; older interactions outside the window are discarded. Chronological ordering within the window is strictly preserved.

### Timestep Feature Vector (432 Dimensions)
Each interaction in the longitudinal sequence is encoded into a 432-dimensional vector:
1. **Fused Multimodal Embedding (Slice 3.5)**: 256 dimensions.
2. **Distress Embedding (Slice 3.6)**: 128 dimensions.
3. **Distress Continuous Score (Slice 3.6)**: 1 dimension $\in [0.0, 1.0]$.
4. **Distress Discrete Level One-Hot (Slice 3.6)**: 4 dimensions (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
5. **Behavioural Features Slice (Slice 3.1)**: 16 dimensions (8 values + 8 missingness masks).
6. **Engagement Features Slice (Slice 3.1)**: 26 dimensions (13 values + 13 missingness masks).
7. **Normalized Time Delta**: 1 dimension (hours since previous interaction normalized).

### Dual-Mode Architecture
1. **`FALLBACK` Mode**:
   - Sequence Projection: `Linear(432, 128)` + `ReLU`.
   - Deterministic Temporal Aggregation: Computes valid-timestep mean pooling (`128-dim`) + first-to-last valid timestep delta (`128-dim`) $\to$ concatenated `256-dim` representation.
   - Aggregation MLP: `Linear(256, 128)` + `ReLU` + `Linear(128, 128)`.
   - Unit Sphere Normalization: $L_2$ normalized to `128-dim` `trajectory_embedding`.
   - Trajectory Head: `Linear(128, 64)` + `ReLU` + `Linear(64, 4)` + `Softmax`.
   - Parameter Count: **113,348** trainable parameters. Pure Python. Zero transformer backbones in memory.
2. **`PYTORCH_FROZEN` Mode**:
   - Sequence Projection: `Linear(432, 128)` + `ReLU`.
   - Recurrent Core: Single-layer `nn.GRU(input_size=128, hidden_size=128, batch_first=True)`.
   - Trajectory Head: `Linear(128, 64)` + `ReLU` + `Linear(64, 4)` + `Softmax`.
   - Parameter Count: **163,012** trainable parameters. Backbones frozen.
3. **`PYTORCH_FINETUNE` Mode**:
   - Same GRU architecture with backbones unfrozen when `--unfreeze-backbone` is supplied.

### Exact Parameter Accounting
- **1. Trainable Parameters**:
  - `FALLBACK` Mode: **113,348**
  - `PYTORCH_*` Modes: **163,012**
- **2. Upstream Backbone Parameters**: **229,774,080** (DistilBERT: 134,734,080 + Wav2Vec2: 95,040,000)
- **3. Total Parameters If Instantiated**: **229,887,428** (Fallback) / **229,937,092** (PyTorch)
- **4. Parameters Actually Instantiated**: **113,348** in Fallback mode (transformers referenced in config only) / **229,937,092** in PyTorch mode

### Training Supervision & Smoke-Test Disclaimers
> [!WARNING]
> - **Smoke-test metrics are intended only to verify that the training, checkpointing, inference, and evaluation pipelines function correctly. They are NOT indicators of real-world model performance.**
> - **Synthetic demonstration labels are used solely for engineering verification and architecture validation. They are NOT clinical ground truth.**

### Reusable Public Inference Interface
```python
from backend.ml.training.models.trajectory import LongitudinalTrajectoryModel, CaseTrajectory

model = LongitudinalTrajectoryModel()
result = model.predict_trajectory(case_trajectory)
# Returns strictly:
# {
#     "trajectory_embedding": [0.042, -0.018, ..., 0.088],  # 128-dim unit vector
#     "trajectory_probabilities": {
#         "STABLE": 0.05,
#         "IMPROVING": 0.02,
#         "WORSENING": 0.21,
#         "RAPIDLY_WORSENING": 0.72
#     },
#     "trajectory_score": 0.825,                            # continuous direction index [-1.0, 1.0]
#     "trajectory_label": "RAPIDLY_WORSENING",              # categorical argmax
#     "model_version": "aaroh-trajectory-v1"                # traceability
# }
```

### Strict Clinical & Architectural Boundaries
- `enforce_trajectory_boundary()` strictly blocks: `diagnosis`, `escalation`, `future_risk`, `confidence`, `explanation`, `intervention`, `recommendation`, `depression`, `anxiety`, `ptsd`, `suicide_risk`, `phq`, `gad`.
- Model outputs strictly limited to: `trajectory_embedding`, `trajectory_probabilities`, `trajectory_score`, `trajectory_label`, and `model_version`.

---

## 9. Slice 3.8: Escalation Assessment Model (v1)

Slice 3.8 provides the **Escalation Assessment Model** (`EscalationAssessmentModel`), the final predictive decision layer in the AAROH ML pipeline.

### Architectural Overview & Decision Pipeline
Rather than an uninterpretable deep neural network, Slice 3.8 implements a transparent, calibrated **Logistic Regression baseline** exposing continuous probabilities via the logistic sigmoid $\sigma(z) = \frac{1}{1 + e^{-z}}$.

The strict hierarchical pipeline flows as follows:
```
MLInput (Slice 3.1)
  │
  ├── Representation Models (Slice 3.3 / 3.4)
  │     ├── Text: DistilBERT (Emotion 7-dim, Stress 2-dim, Mental Health 768-dim)
  │     └── Audio: Wav2Vec2 (8-dim probabilities, 768-dim embedding)
  │
  └── Multimodal Feature Fusion (Slice 3.5)
        ├── Dynamic modality gating (tabular, text, audio)
        └── Fused multimodal representation (256-dim)
              │
              ├── Dynamic Distress Model (Slice 3.6)
              │     └── Current distress state (128-dim embedding, score, level)
              │           │
              │           └── Longitudinal Trajectory Model (Slice 3.7)
              │                 └── Distress change over time (128-dim embedding, score, label)
              │                       │
              └───────────────────────┴──► Escalation Assessment Model (Slice 3.8)
                                            └── Calibrated operational assessment signal
```

```
backend/ml/training/models/escalation/
├── __init__.py
├── dataset.py                # EscalationConfig, EscalationInputRecord, 28 interpretable features, zero-leakage case splitter
└── model.py                  # EscalationAssessmentModel (Interpretable Logistic Regression, confidence, explainability, abstention)
```

### Strict Pipeline Responsibility Separation
The AAROH ML subsystem enforces a strict division of clinical and operational responsibilities across pipeline layers:

1. **Representation Models (Slices 3.3 / 3.4 / 3.5)**:
   - Produce latent embeddings and intermediate multimodal representations only (`text_embedding`, `audio_embedding`, `fused_embedding`, `modality_weights`).
   - Do NOT estimate distress, trajectory, escalation, diagnosis, or triage actions.

2. **Current Distress Model (Slice 3.6)**:
   - Estimates **current state only** (`distress_score`, `distress_level`, `distress_embedding`).
   - Does NOT perform longitudinal reasoning, predict future states, or output escalation signals.

3. **Longitudinal Trajectory Model (Slice 3.7)**:
   - Estimates **temporal direction only** (`trajectory_score`, `trajectory_label`, `trajectory_probabilities`, `trajectory_embedding`).
   - Models distress rate of change over time; does NOT predict operational escalation, triage decisions, or diagnoses.

4. **Escalation Assessment Model (Slice 3.8 — This Slice)**:
   - The **ONLY** layer in the ML pipeline authorized to produce:
     - `escalation_probability`
     - `confidence`
     - `target_horizon_days`
     - `risk_level`
     - `grounded explanation` (and `factors`)
     - `model_version`
   - **Important Clinical Boundary on Explanations**: In the AAROH subsystem, `explanation` refers strictly to **feature-level mathematical evidence** (traceable positive feature contributions $w_i \cdot x_i$) supporting the model's operational assessment signal. It does **NOT** represent a clinical opinion, medical judgment, psychiatric evaluation, or diagnosis.

### Centralized Escalation Risk Taxonomy (`RiskLevel`)
Risk levels are determined strictly via configurable probability thresholds defined in `EscalationConfig`:
- `LOW` ($P < 0.40$): Low probability of acute distress escalation within horizon; standard workflow continues.
- `MODERATE` ($0.40 \le P < 0.75$): Intermediate escalation probability; scheduled follow-up and monitoring indicated.
- `HIGH` ($P \ge 0.75$): Elevated escalation probability; prompt case manager review and assessment signal triggered.
- **Strict Clinical Invariant**: `CRITICAL` is strictly forbidden in Slice 3.8. Emergency triage is handled exclusively by deterministic safety guardrails in downstream layers.

### Configurable Target Horizon
The prediction horizon is configurable via `EscalationConfig(target_horizon_days=7)` and is never hardcoded. All inference outputs explicitly state `target_horizon_days`.

### Interpretable 28-Dimensional Feature Representation
Each escalation record derives 28 structured, interpretable features from upstream slices without recomputation:
1. **Distress State (Slice 3.6)**: `distress_score`, `distress_is_high`, `distress_is_critical`.
2. **Longitudinal Trajectory (Slice 3.7)**: `trajectory_score`, `trajectory_is_worsening`, `trajectory_is_rapidly_worsening`.
3. **Multimodal Alignment (Slice 3.5)**: `modality_weight_tabular`, `modality_weight_text`, `modality_weight_audio`, `modality_entropy`.
4. **Behavioural Metrics (Slice 3.1)**: `sleep_disturbance_level`, `social_withdrawal_score`, `appetite_change_score`, `mood_variability`.
5. **Engagement Metrics (Slice 3.1)**: `checkin_frequency_drop`, `response_delay_hours`, `session_duration_zscore`, `missed_checkins_count`.
6. **Observation Completeness & Missing Indicators**: `valid_observation_count`, `has_text_modality`, `has_audio_modality`, plus explicit missing indicators preserving `None != 0` (`sleep_missing`, `social_missing`, `appetite_missing`, `mood_missing`, `checkin_drop_missing`, `delay_missing`).

### Evidence-Based Confidence Policy (`ConfidencePolicyConfig`)
Confidence is strictly decoupled from probability ($C \ne P$ and $C \ne |P - 0.5| \times 2$). It reflects epistemic completeness governed by a versioned `ConfidencePolicyConfig`:
- `observation_weight = 0.35`: Depth of observation history ($\le 5$ points).
- `text_weight = 0.20`: Availability of text modality observations.
- `audio_weight = 0.15`: Availability of acoustic modality observations.
- `missingness_weight = 0.15`: Proportion of non-missing clinical/behavioural indicators.
- `uncertainty_weight = 0.15`: Margin of certainty away from ambiguity ($2 \times |P - 0.5|$).
- `minimum_history = 2`: Minimum required observation count to attempt assessment.
- `minimum_modalities = 1`: Minimum active modalities required.
- `minimum_confidence = 0.25`: Threshold below which status transitions to `LOW_CONFIDENCE`.

$$C = w_{\text{obs}} \times \min\left(1.0, \frac{\text{obs\_count}}{5}\right) + w_{\text{text}} \times M_{\text{text}} + w_{\text{audio}} \times M_{\text{audio}} + w_{\text{miss}} \times (1 - M_{\text{missing\_ratio}}) + w_{\text{unc}} \times 2|P - 0.5|$$

### Explicit Abstention Policy
When data is insufficient to form an evidence-based assessment, the model explicitly abstains rather than fabricating `LOW` risk or $0.0$ probability:
- Returns `status = "INSUFFICIENT_DATA"`, `escalation_probability = None`, and `risk_level = None` when:
  - Observation count is below minimum threshold (`valid_observation_count < 2`).
  - Required upstream distress state is missing (`distress_score is None`).
  - Neither text nor audio modality is present.
- When confidence drops below threshold ($C < 0.25$), outputs `status = "LOW_CONFIDENCE"`.
- Supported lifecycle statuses: `SUCCESS`, `FAILED`, `LOW_CONFIDENCE`, `INSUFFICIENT_DATA`, `ABSTAINED`.

### Grounded Explainability & Raw Contribution Tracking
Explanations are computed directly from feature contributions ($c_i = w_i \cdot x_i$):
- **Raw Contribution Table**: Preserved internally on `model.get_last_feature_contributions()` for auditing, debugging, and explainability verification.
- **Traceable Clinical Factors**: Top positive drivers ($c_i > 0.05$) are mapped to standardized clinical factor names (e.g. `recent_distress_elevation`, `worsening_trajectory`, `sleep_disruption`, `social_withdrawal`, `engagement_drop`, `elevated_response_delay`).
- **Modality Availability Invariant**: Explanations never reference unavailable modalities.
- **Clinical Safety Guarantee**: Prohibits generating psychiatric diagnoses, disorder labels (e.g. depression, anxiety, PTSD), suicide predictions, or medical/treatment recommendations.
- **Explanation vs. Diagnosis Clarification**: Explanation refers to **feature-level mathematical evidence** and does NOT represent a clinical opinion or diagnosis.

### Model Parameters & Exported Assets
- **Trainable Parameters**: **29** (28 feature weights + 1 bias term).
- **Export Directory**: `models/escalation/`
  - `weights`: Model parameters `[w_1, ..., w_28, b]`.
  - `config.json`: Feature count, thresholds (`low_threshold=0.40`, `high_threshold=0.75`), `target_horizon_days=7`, `min_confidence_threshold=0.25`, versioned `confidence_policy`, versioned `calibration`.
  - `metadata.json`: Model version (`aaroh-escalation-v1`), training timestamp, parameter counts, versioned `calibration` (`{"method": "logistic_sigmoid", "version": "1.0"}`), versioned `confidence_policy` (`{"version": "1.0", ...}`), feature schema version (`"1.0"`), dataset version (`"3.8.0"`), and upstream model lineage (`aaroh-fusion-v1`, `aaroh-distress-v1`, `aaroh-trajectory-v1`).
  - `metrics.json`: Calibration metrics (Brier score, ECE, calibration curve) and discrimination metrics (ROC-AUC, PR-AUC, Accuracy, Precision, Recall, F1).
  - `label_mapping.json`: Risk levels and smoke-test disclaimer.

### Calibration & Evaluation Suite
- **Calibration Evaluation**: Brier Score, Expected Calibration Error (ECE), and 5-bin calibration curve mapping mean predicted probability to empirical frequency.
- **Discrimination Evaluation**: ROC-AUC, PR-AUC, Precision, Recall, Macro F1.

### Public Inference Interface & Contract Conformance
Outputs strictly conform to the AAROH `MlInferenceResult` specification:
```python
from backend.ml.training.models.escalation import EscalationAssessmentModel, EscalationInputRecord

model = EscalationAssessmentModel.load("models/escalation")
result = model.predict_escalation(record)

# Returns dictionary conforming to MlInferenceResult:
# {
#     "case_id": "case_101",
#     "prediction_date": "2026-09-06T02:00:00.000000+00:00",
#     "escalation_probability": 0.8124,
#     "target_horizon_days": 7,
#     "confidence": 0.8250,
#     "risk_level": "HIGH",
#     "factors": ["recent_distress_elevation", "worsening_trajectory", "sleep_disruption"],
#     "explanation": "Elevated escalation risk driven by recent distress elevation, worsening trajectory, sleep disruption over the next 7 days.",
#     "trend": "WORSENING",
#     "baseline_deviation": 0.4215,
#     "model_version": "aaroh-escalation-v1",
#     "status": "SUCCESS",
#     "source": "model",
#     "message": None
# }
```

### Strict Clinical & Architectural Boundaries
- `enforce_escalation_boundary()` guarantees no psychiatric diagnoses, disorder labels, medical advice, therapy/medication recommendations, or `CRITICAL` risk levels are emitted.
- Invariance to future data: temporal filtering ensures predictions at cutoff $T$ remain identical even if interactions after $T$ exist in history.

---

## 10. Training & Evaluation Workflows (Google Colab Ready)

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

# 5. Train Multimodal Feature Fusion Model (Slice 3.5)
python3 train_multimodal_fusion.py \
    --data-dir datasets/processed \
    --output-dir models/multimodal_fusion \
    --batch-size 16 \
    --lr 1e-3 \
    --epochs 10 \
    --seed 42 \
    --fp16 \
    --drive-checkpoint-dir /content/drive/MyDrive/aaroh_checkpoints/fusion

# Fast Smoke-Test Execution (Single Epoch / Small Batch)
python3 train_multimodal_fusion.py --smoke-test

# 6. Train Dynamic Distress Model (Slice 3.6)
python3 train_distress.py \
    --data-dir datasets/processed \
    --output-dir models/distress \
    --batch-size 16 \
    --lr 1e-3 \
    --epochs 10 \
    --seed 42 \
    --fp16 \
    --drive-checkpoint-dir /content/drive/MyDrive/aaroh_checkpoints/distress

# Fast Smoke-Test Execution (Single Epoch / Small Batch)
python3 train_distress.py --smoke-test

# 7. Train Longitudinal Trajectory Model (Slice 3.7)
python3 train_trajectory.py \
    --output-dir models/trajectory \
    --checkpoint-dir checkpoints/trajectory \
    --history-window 10 \
    --batch-size 8 \
    --lr 1e-3 \
    --epochs 5 \
    --seed 42 \
    --drive-checkpoint-dir /content/drive/MyDrive/aaroh_checkpoints/trajectory

# Fast Smoke-Test Execution
python3 train_trajectory.py --smoke-test

# 8. Train Escalation Assessment Model (Slice 3.8)
python3 train_escalation.py \
    --output-dir models/escalation \
    --checkpoint-dir checkpoints/escalation \
    --batch-size 8 \
    --lr 1e-3 \
    --epochs 5 \
    --seed 42 \
    --drive-checkpoint-dir /content/drive/MyDrive/aaroh_checkpoints/escalation

# Fast Smoke-Test Execution
python3 train_escalation.py --smoke-test
```

### Comprehensive Evaluation Suite
```bash
# Evaluate Text Representation Models:
python3 evaluate_text_models.py --model-type all --models-dir models/ --data-dir datasets/processed/

# Evaluate Audio Emotion Representation Model:
python3 evaluate_audio_model.py --model-dir models/audio_emotion/ --data-dir datasets/processed/

# Evaluate Multimodal Feature Fusion Model:
python3 evaluate_fusion_model.py --model-dir models/multimodal_fusion/ --data-dir datasets/processed/

# Evaluate Dynamic Distress Model:
python3 evaluate_distress_model.py --model-dir models/distress/

# Evaluate Longitudinal Trajectory Model:
python3 evaluate_trajectory_model.py --model-dir models/trajectory/

# Evaluate Escalation Assessment Model:
python3 evaluate_escalation_model.py --model-dir models/escalation/
```
Metrics produced:
- **Text Emotion**: Accuracy, Precision, Recall, Macro F1, Weighted F1.
- **Stress**: Accuracy, Precision, Recall, F1, ROC-AUC.
- **Mental Health Representation**: Mean embedding norm, Cosine separation, Domain alignment.
- **Audio Emotion**: Overall Accuracy, Precision, Recall, Macro F1, Weighted F1, Confusion Matrix, Per-Class Accuracy for all 8 RAVDESS emotions.
- **Multimodal Fusion**: Tabular Reconstruction Loss (MSE), Dynamic Modality Gating Weights (`tabular`, `text`, `audio`), Missing Modality Zero-Weight Verification, Mean Fused Embedding Norm, Cross-Case Cosine Diversity.
- **Dynamic Distress**: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Pearson Correlation ($r$), Threshold Accuracy, Distress Level Distribution (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), Distress Embedding Norm.
- **Longitudinal Trajectory**: Overall Accuracy, Macro Precision, Macro Recall, Macro F1, Weighted F1, 4x4 Confusion Matrix, Per-Class Accuracy, Trajectory Label Distribution (`STABLE`, `IMPROVING`, `WORSENING`, `RAPIDLY_WORSENING`), Mean Trajectory Embedding Norm.
- **Escalation Assessment**: Brier Score, Expected Calibration Error (ECE), Calibration Curve (5 bins), ROC-AUC, PR-AUC, Accuracy, Precision, Recall, Macro F1, Risk Level Distribution (`LOW`, `MODERATE`, `HIGH`), Mean Escalation Probability, Mean Confidence, Abstention Rate.

---

## 11. Model Export Structure

Models exported under `models/<model_name>/` save the following standard artifacts:
- `pytorch_model.bin` / `weights` (model weights)
- `tokenizer_config.json` / `tokenizer` (tokenizer parameters & configuration)
- `preprocessor_config.json` (audio sampling rate, duration, normalization params)
- `config.json` (architecture hyper-parameters & dimensions)
- `label_mapping.json` (class index / threshold mappings & disclaimers)
- `metrics.json` (validation and test performance metrics)
- `metadata.json` (containing `model_version`, `dataset_version`, `training_date`, `execution_mode`, `parameter_counts`, `hyperparameters`, `upstream_models`, and clinical boundary assertions)
- `modality_schema.json` (multimodal input dimensions, masking schema, fusion dimensions)

---

## 12. Clinical & Regulatory Boundary Invariant

> [!IMPORTANT]
> AAROH ML models and features operate exclusively as **clinical decision support**.
> - Datasets and models do NOT provide psychiatric diagnoses.
> - `emotion != distress`
> - `stress != distress`
> - `audio_emotion != distress`
> - `fusion != distress`
> - `PHQ != AAROH distress`
> - Dynamic Distress Model estimates **current** distress representations only and NEVER predicts future trajectories, escalation, suicide risk, or treatment recommendations.
> - Longitudinal Trajectory Model estimates **change over time** only.
> - Escalation Assessment Model provides an **escalation assessment signal** only and is NOT a clinical decision maker, diagnostic tool, or treatment planner.
> - ML features never override human clinician judgments.
> - Missing data must remain `None` and must never be fabricated as zero.



