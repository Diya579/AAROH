# Dynamic Distress Model Architecture & Specification (Slice 3.6)

## 1. Executive Summary & Operational Definition

The **Dynamic Distress Model** is a core multimodal subsystem within the AAROH AI/ML architecture. It estimates a client's **current, acute psychological distress state** at the moment of a given interaction.

### What Distress IS:
- A continuous, dynamic estimation of subjective psychological strain, anxiety, sorrow, fear, or affective upheaval at an exact point in time.
- A normalized real scalar value:
  $$\text{distress\_score} \in [0.00, 1.00]$$
- An operational four-tier discrete triage categorization (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
- A 128-dimensional continuous latent state representation ($\|\mathbf{z}\|_2 = 1.0$) capturing nuanced distress geometry for downstream models.
- Fully transparent and explainable via machine-readable evidence grounded in observable input signals (emotion drivers, behavioral markers, bilingual lexicons).

### What Distress IS NOT (Strict Clinical Boundaries):
- **NOT a psychiatric diagnosis**: The model does not predict major depressive disorder (MDD), generalized anxiety disorder (GAD), PTSD, or any DSM-5 / ICD-11 condition.
- **NOT a clinical psychometric test score**: It does not predict or replace PHQ-9, GAD-7, or Columbia Suicide Severity Rating Scale (C-SSRS) scores.
- **NOT a suicide or self-harm risk predictor**: Suicide risk detection is handled exclusively by dedicated crisis protocols with human-in-the-loop escalation.
- **NOT a longitudinal trajectory**: It captures the *instantaneous* state at interaction $t$. Modeling trend over time $t-k \dots t$ is the explicit responsibility of the Longitudinal Trajectory Model (Slice 3.7).
- **NOT an escalation action**: Determining counselor dispatch, supervisor alert, or crisis handoff is the responsibility of the Escalation Policy Engine (Slice 3.8).
- **NOT a treatment recommendation**: The model never prescribes medication, suggests clinical interventions, or recommends specific therapeutic modalities.

---

## 2. Mathematical Formulation & Architecture

### 2.1 Input Representation ($\mathbb{R}^{301}$)

The distress model consumes a 301-dimensional composite representation combining multimodal embeddings, structured behavioral indicators, and explicit missingness masks:

$$\mathbf{x} = [\mathbf{e}_{\text{fused}} \;\|\; \mathbf{b}_{\text{values}} \;\|\; \mathbf{b}_{\text{mask}} \;\|\; \mathbf{g}_{\text{values}} \;\|\; \mathbf{g}_{\text{mask}} \;\|\; \mathbf{w}_{\text{modalities}}] \in \mathbb{R}^{301}$$

| Component | Dimensions | Source / Description | Missingness Policy |
| :--- | :--- | :--- | :--- |
| $\mathbf{e}_{\text{fused}}$ | 256 | Fused representation from Slice 3.5 (or projected text emotion embedding from frozen Slice 3.3) | Default to neutral vector if missing |
| $\mathbf{b}_{\text{values}}$ | 8 | Behavioural feature values (sleep disruption, withdrawal, appetite, etc.) | Standardized floats; zeroed if missing |
| $\mathbf{b}_{\text{mask}}$ | 8 | Behavioural missingness indicator ($1.0 = \text{present}$, $0.0 = \text{missing}$) | Preserves `None != 0.0` semantic integrity |
| $\mathbf{g}_{\text{values}}$ | 13 | Engagement feature values (response latency, session frequency, drop-off rate, etc.) | Standardized floats; zeroed if missing |
| $\mathbf{g}_{\text{mask}}$ | 13 | Engagement missingness indicator ($1.0 = \text{present}$, $0.0 = \text{missing}$) | Preserves `None != 0.0` semantic integrity |
| $\mathbf{w}_{\text{modalities}}$ | 3 | Modality gating weights: `[tabular, text, audio]` summing to $\le 1.0$ | Dynamic weights reflecting input presence |

### 2.2 Network Architecture & Projections

The core network maps the 301-dimensional input into both a 128-dimensional latent space and a bounded scalar score:

```
Input x ∈ ℝ³⁰¹
   │
   ▼
Linear(301 → 256) ──► LayerNorm ──► GELU ──► Dropout(p=0.1)
   │
   ▼
Linear(256 → 128) ──► LayerNorm ──► GELU ──► Dropout(p=0.1)
   ├──► Linear(128 → 128) ──► L2 Normalize ──► z_distress ∈ ℝ¹²⁸ (Latent Embedding, ||z||₂ = 1)
   │
   └──► Linear(128 → 64) ──► GELU ──► Linear(64 → 1) ──► Sigmoid ──► distress_score ∈ [0.00, 1.00]
```

1. **Latent Distress Embedding ($\mathbf{z} \in \mathbb{R}^{128}$)**:
   $$\mathbf{z} = \frac{\mathbf{h}_{\text{latent}}}{\|\mathbf{h}_{\text{latent}}\|_2 + \epsilon}$$
   Constrained to the unit hypersphere $\mathcal{S}^{127}$, guaranteeing uniform scale and angle-preserving cosine similarity for the longitudinal trajectory model (Slice 3.7).

2. **Continuous Distress Score ($s \in [0.00, 1.00]$)**:
   $$s = \sigma(\mathbf{W}_2 \cdot \text{GELU}(\mathbf{W}_1 \mathbf{h}_{\text{shared}} + \mathbf{b}_1) + b_2)$$

### 2.3 Threshold Mapping to Discrete Triage Levels

The continuous score $s$ is mapped deterministically to discrete levels using configurable, versioned clinical thresholds:

$$\text{Level}(s) = \begin{cases} 
\text{LOW} & 0.00 \le s < 0.25 \\
\text{MODERATE} & 0.25 \le s < 0.55 \\
\text{HIGH} & 0.55 \le s < 0.80 \\
\text{CRITICAL} & 0.80 \le s \le 1.00 
\end{cases}$$

- **LOW ($[0.00, 0.25)$)**: Minimal distress. Typical baseline state or positive/neutral sentiment. Routine interaction flow.
- **MODERATE ($[0.25, 0.55)$)**: Mild to moderate distress. Noticeable affective strain, sorrow, or stress signals without immediate crisis indicators. Supportive counseling recommended.
- **HIGH ($[0.55, 0.80)$)**: Significant acute distress. Strong markers of fear, grief, hopelessness, or behavioural withdrawal. Priority queuing for human counselor review.
- **CRITICAL ($[0.80, 1.00]$)**: Severe acute distress. Compounding multi-factor distress language or severe disengagement. Triggers immediate escalation evaluation.

---

## 3. Explainability & Evidence Architecture

To maintain clinical trust and auditability, every prediction is accompanied by structured, machine-readable evidence grounded strictly in observable model inputs.

### 3.1 Confidence Scoring
Model confidence is computed heuristically in $[0.50, 0.99]$ as a function of the score's distance to decision boundaries:

$$\Delta_{\text{boundary}} = \min(|s - 0.25|, |s - 0.55|, |s - 0.80|)$$
$$\text{confidence} = \text{clamp}(0.70 + 1.5 \cdot \Delta_{\text{boundary}}, 0.50, 0.99)$$

Predictions near classification boundaries naturally exhibit lower confidence, highlighting uncertainty for downstream decision systems.

### 3.2 Evidence Payload (`DistressEvidence`)
```json
{
  "distress_score": 0.682,
  "distress_level": "HIGH",
  "confidence": 0.88,
  "main_contributors": [
    "High fear (probability=0.65)",
    "High sadness (probability=0.40)",
    "Distress language detected (fear, hopelessness: 'terrified', 'hopeless')"
  ],
  "top_emotion_drivers": [
    {"emotion": "fear", "probability": 0.65, "impact": 0.163},
    {"emotion": "sadness", "probability": 0.40, "impact": 0.080}
  ],
  "protective_factors": [
    {"emotion": "gratitude", "probability": 0.22, "mitigation": 0.033}
  ],
  "lexicon_matches": {
    "fear": ["terrified", "panic"],
    "hopelessness": ["hopeless"]
  },
  "modality_weights": {
    "tabular": 0.10,
    "text": 0.90,
    "audio": 0.00
  },
  "model_version": "aaroh-distress-v1.0.0",
  "label_disclaimer": "SYNTHETIC DEMONSTRATION LABELS - NOT CLINICAL GROUND TRUTH"
}
```

### 3.3 Multilingual Grounding
The explainability engine uses verified bilingual lexicons covering:
- **English**: High distress markers (*terrified, panic, hopeless, overwhelmed, devastated*).
- **Hindi (Devanagari)**: (*डर, भय, खौफ, घबराहट, निराश, नाउम्मीद, सब खत्म, अकेला*).
- **Hinglish**: (*darr, ghabrahat, koi umeed nahi, sab khatam, akela*).

---

## 4. End-to-End Inference Pipeline (`DistressInferencePipeline`)

The distress model connects directly to the frozen multilingual Text Emotion model (`TextEmotionModel`, Slice 3.3):

```
Text Input ("I feel overwhelmed and scared")
   │
   ▼
TextEmotionModel (Slice 3.3 - Multilingual DistilBERT)
   ├─► Emotion Probabilities (28 GoEmotions + EmoHinD)
   └─► Emotion Embedding (768-dim)
   │
   ▼
Projection & Indicator Extraction
   ├─► Stride Pooling + Emotion Modulation ──► 256-dim Fused Embedding
   ├─► Bilingual Lexicon Matching (English / Hindi / Hinglish)
   └─► Tabular Feature Integration (Behavioural & Engagement with None masks)
   │
   ▼
DistressInputRecord (301-dim)
   │
   ▼
DynamicDistressModel (Slice 3.6)
   │
   ▼
Inference Result
   ├─ distress_score: 0.68
   ├─ distress_level: HIGH
   ├─ distress_embedding: [128-dim unit vector]
   ├─ confidence: 0.88
   ├─ main_contributors: ["High fear (0.65)", "Distress language detected ('scared')"]
   └─ regulatory_disclaimer: "..."
```

---

## 5. Execution Modes & Safety Guards

The model supports three distinct runtime execution modes:

1. **`FALLBACK` (Default in standard runtime)**:
   - Pure PyTorch feedforward network operating on pre-extracted embeddings and tabular vectors.
   - Zero heavyweight external backbone dependencies.
   - Extremely fast (<2ms latency), deterministic, lightweight.

2. **`PYTORCH_FROZEN`**:
   - Loads pretrained multilingual transformer (`distilbert-base-multilingual-cased`) and audio (`facebook/wav2vec2-base`) backbones.
   - Backbone parameters are frozen (`requires_grad = False`).
   - Fail-closed: Raises `RuntimeError` immediately if checkpoint weights or architectures fail to load.

3. **`PYTORCH_FINETUNE`**:
   - Enables gradient updates through backbones during specialized fine-tuning runs.
   - Strictly requires explicit environment and configuration opt-ins to prevent unintended parameter corruption.

---

## 6. Offline Model Artifact Contract

The model exports self-contained, versioned artifact packages that can be loaded in fresh Python environments with zero global state:

```
models/distress/
├── config.json          # Architecture dimensions, thresholds, model version
├── metadata.json        # Execution mode, parameter count, date, hardware
├── metrics.json         # MAE, RMSE, Pearson r, Macro F1, Per-level breakdown
├── label_mapping.json   # Mapping of level indices to string labels
└── weights              # Serialized PyTorch state dictionary (fp32)
```

Loading code:
```python
from backend.ml.training.models.distress import DynamicDistressModel

model = DynamicDistressModel.load_from_artifact("models/distress")
pred = model.predict_distress(record)
```

---

## 7. Verification & Test Suite

The subsystem is validated by a dedicated test suite with 100% pass rates:
- `backend/ml/tests/test_dynamic_distress_model.py`: 15 architectural tests.
- `backend/ml/tests/test_execution_mode_guards.py`: 12 security and fail-closed guard tests.
- `backend/ml/tests/test_distress_subsystem.py`: 13 integration, explainability, multilingual, and boundary compliance tests.
