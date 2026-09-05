# AAROH ML subsystem (Slice 1, Slice 2.1 & Slice 2.2)

This package owns machine-learning **contracts, inference interfaces, preprocessing pipelines, and feature extractors**.
It does not own FastAPI, interventions, voice/ASR, or PostgreSQL persistence.

## Responsibilities

| Module | Responsibility |
| --- | --- |
| `contract` | Nested ML API result (`distress`, `prediction`, `explanation`, `model`) plus `status` and `source` |
| `config` | Configurable prediction horizon and confidence/abstention thresholds |
| `policies` | Confidence / abstention **interfaces** and a default threshold policy |
| `inference` | `infer(...)` → Python `dict`. **No database writes.** |
| `preprocessing` | Input validation, Unicode text normalization, safe missingness handling, and record standardization (Slice 2.1) |
| `features` | Deterministic multilingual text feature extraction and explainability evidence (Slice 2.2) |
| `models` | Future learned-model adapters (rule-based code stays in `backend/risk/`) |
| `training` | Future reproducible training scripts (offline; not required for inference) |
| `evaluation` | Future metrics; synthetic scores are not clinical evidence |
| `explainability` | Future feature-grounded factors |
| `versioning` | Model name/version identity attached to outputs |

## Preprocessing Pipeline (Slice 2.1)

The preprocessing layer (`backend.ml.preprocessing`) provides deterministic, modular preparation of raw interaction data before feature extraction:

1. **Input Validation (`validation.py`)**:
   - Validates `case_id`, `interaction_date`, 1–5 Likert ratings, booleans, and continuous metrics.
   - Preserves unknown languages with a warning rather than failing preprocessing.
2. **Text Normalization & Unicode Preservation (`text.py`)**:
   - Canonical Unicode normalization (`NFKC`).
   - Strict preservation of Indic scripts (Devanagari, Bengali, Gujarati, Tamil, Telugu, Kannada, Malayalam, etc.) and code-mixed text (Hinglish).
   - Preserves Zero-Width Joiner (ZWJ) and Zero-Width Non-Joiner (ZWNJ) essential for Indic conjunct ligatures.
   - Cleans invisible formatting noise (BOM, zero-width space, bidi controls) and normalizes whitespace.
   - Evaluates text quality and flags empty or very short inputs.
3. **Safe Missingness Handling (`missingness.py`)**:
   - Explicit invariant: `None` is **never** silently coerced to `0` or `0.0`.
   - Generates `MissingnessReport` tracking exact available and missing fields.
4. **Forward Compatibility (`pipeline.py`)**:
   - Any unrecognized input fields are captured inside `PreprocessedInteraction.metadata` to guarantee forward compatibility for future features.

### How to use Preprocessing

```python
from backend.ml import preprocess_interaction

raw_payload = {
    "case_id": "AAROH-001",
    "interaction_date": "2026-09-03",
    "language": "Hindi",
    "text_response": "मुझे बहुत डर लग रहा है।",
    "safety_response": 2,
    "fear_level": 4,
}

record = preprocess_interaction(raw_payload)
# record is a PreprocessedInteraction dataclass ready for feature extraction
```

## Text Feature Extraction (Slice 2.2)

The text feature extraction layer (`backend.ml.features`) consumes `PreprocessedInteraction` objects to generate structured, deterministic text features:

1. **Basic Lexical Metrics (`lexical.py`)**:
   - `word_count`, `character_count`, `sentence_count` (including Indic dandas `।`, `॥`), `average_word_length`, `uppercase_ratio`, and `punctuation_ratio`.
2. **Distress Indicators (`distress.py`)**:
   - Observable indicators: `fear`, `hopelessness`, `isolation`, `helplessness`, `intimidation`, `sadness`, `anxiety` in `[0.0, 1.0]`.
3. **Help-Seeking Indicators (`help_seeking.py`)**:
   - `asking_for_help`, `requesting_support`, `emergency_language` in `[0.0, 1.0]`.
4. **Safety Indicators (`safety.py`)**:
   - `urgency`, `danger_related_wording` in `[0.0, 1.0]`.
5. **Centralized Multilingual Lexicons (`lexicons.py`)**:
   - Single source of truth supporting English, Hindi (Devanagari), and Hinglish (Romanized Hindi).
6. **Explainability Evidence (`evidence`)**:
   - Matched keywords/phrases are captured inside `ExplanationEvidence` without altering scores, enabling downstream inference layers to cite grounded terms in predictions.
7. **Safe Missingness Invariant (`None != 0`)**:
   - If text is absent or empty, `text_available` is `False`, and feature indicator blocks are `None` (never fabricated as `0.0`).

### How to extract Text Features

```python
from backend.ml import extract_text_features, preprocess_interaction

raw_payload = {
    "case_id": "AAROH-001",
    "interaction_date": "2026-09-03",
    "language": "Hindi",
    "text_response": "मुझे बहुत डर लग रहा है, कृपया मदद चाहिए।",
}

interaction = preprocess_interaction(raw_payload)
features = extract_text_features(interaction)
# features is a strongly typed, immutable TextFeatures dataclass
```

## Application-facing result

`infer` returns a dict shaped like `docs/ML_API_CONTRACT.md`:

```text
case_id
prediction_date
status          SUCCESS | FAILED | INSUFFICIENT_DATA | LOW_CONFIDENCE | ABSTAINED
source          ml | baseline | fallback | insufficient_evidence
distress        { score, trajectory, confidence, baseline_deviation } | null
prediction      { escalation_probability, target_horizon_days, confidence, risk_level } | null
explanation     { factors, trend, baseline_deviation } | null
model           { model_name, model_version } | null
```

`FAILED`, `INSUFFICIENT_DATA`, and `ABSTAINED` must not fabricate
`escalation_probability: 0.0` with `risk_level: LOW`.

Never label a rule-based number as `source: ml`.

## Horizon

Default `target_horizon_days` is **7**, set on `InferenceConfig`. It is not
hard-coded inside training or scoring logic in this package.

## Scope & Limits

- No trained artifacts
- No PostgreSQL access
- Existing `features/` and `risk/` behaviour is unchanged
- If no estimates/estimator are supplied, `infer` returns `status: FAILED`
- Text feature extraction prepares observable features; model training and inference scoring belong to subsequent slices

## How the application should call inference

```python
from backend.ml import infer, InferenceConfig

result = infer({"case_id": "AAROH-001"}, config=InferenceConfig())
# persist result via FastAPI / application services — not from this package
```

