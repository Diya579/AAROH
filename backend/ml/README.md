# AAROH ML subsystem (Slice 1, Slice 2.1-2.5 & Slice 3.1)

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
| `features` | Deterministic text (2.2), behavioural (2.3), engagement (2.4), longitudinal (2.5), and ML input assembly (3.1) with feature registry and explainability |
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

## Behavioural Feature Extraction (Slice 2.3)

The behavioural feature extraction layer (`backend.ml.features.behavioural`) consumes `PreprocessedInteraction` records and optional historical interactions to produce structured behavioural distress features:

1. **Centralized Metric Definitions (`definitions.py`)**:
   - Single source of truth for Likert 1–5 scale boundaries and normalization.
   - Consistent directionality: scales are mapped such that `1.0` uniformly represents maximal distress.
   - `safety_response` and `social_support` are inverted (`1 - norm`), while `fear_level` and `sleep_disruption` are direct.
2. **Normalized Observable Indicators**:
   - `safety_distress`, `sleep_disturbance`, `fear_intensity`, `low_social_support`, `help_requested`, and `composite_distress` in `[0.0, 1.0]`.
3. **Longitudinal History Support**:
   - `change_from_previous` (delta from immediately preceding interaction)
   - `change_from_baseline` (delta from first recorded interaction in history)
4. **Explainability Evidence Metadata (`evidence`)**:
   - Retains `observation_count`, raw 1–5 scores, previous/baseline scores, per-metric deltas, observation timestamps, and human-readable `notable_shifts` (e.g. sharp distress spikes).
   - This metadata does not affect numeric scores and directly supports downstream prediction justifications.
5. **Strict `None != 0` Invariant**:
   - Absent history or missing ratings remain `None`. Never converts missing behavioural data into zero.

### How to extract Behavioural Features

```python
from backend.ml import extract_behavioural_features, preprocess_interaction

raw_payload = {
    "case_id": "AAROH-001",
    "interaction_date": "2026-09-03",
    "safety_response": 2,
    "sleep_disruption": 4,
    "fear_level": 5,
    "social_support": 1,
    "help_requested": True,
}

interaction = preprocess_interaction(raw_payload)
behavioural = extract_behavioural_features(interaction)
# behavioural is a strongly typed, immutable BehaviouralFeatures dataclass
```

## Engagement Feature Extraction (Slice 2.4)

The engagement feature extraction layer (`backend.ml.features.engagement`) consumes `PreprocessedInteraction` records and previous interaction history to produce structured interaction engagement patterns:

1. **Configurable Thresholds (`EngagementConfig`)**:
   - Thresholds (`expected_interval_days`, `delayed_response_threshold_hours`, `disengagement_inactivity_days`, `trend_change_threshold`, etc.) are exposed as a configurable dataclass rather than hard-coded constants, enabling model calibration without extractor changes.
2. **Explicit Semantic Boundary**:
   - `engagement_score` measures interaction adherence/regularity (`[0.0, 1.0]`).
   - It is strictly an engineered behavioural feature and is **never** used as an implicit distress or clinical escalation score (distress estimation remains the responsibility of baseline models in Slice 2.5+).
3. **Core Observable Metrics**:
   - `frequency_days`: Mean interval in days between recorded interactions.
   - `response_delay_hours`: Latency in hours between prompt delivery and beneficiary response.
   - `completion_rate`: Proportion of requested questions or check-ins answered.
   - `streak_count`: Consecutive expected check-ins completed without missed days.
   - `days_since_last_interaction`: Inactivity duration relative to the current interaction date.
   - `engagement_trend`: Trajectory enum (`IMPROVING`, `STABLE`, `DECLINING`, `UNKNOWN`).
4. **Strict `None != 0` Invariant**:
   - Missing response delays, intervals, or absence of historical interactions evaluate to `None`.
   - Never converts absent data into 0.0 hours or 0.0 frequency.
5. **Explainability Evidence Metadata (`evidence`)**:
   - Retains grounded explanation signals: `total_interactions`, `valid_delays_count`, `previous_score`, `baseline_score`, `score_change`, `disengagement_risk_flag`, `delayed_response_flag`, and human-readable `engagement_alerts`.

### How to extract Engagement Features

```python
from backend.ml import (
    EngagementConfig,
    extract_engagement_features,
    preprocess_interaction,
)

current_payload = {
    "case_id": "AAROH-001",
    "interaction_date": "2026-09-03",
    "response_delay_hours": 1.5,
    "completed": True,
}

history_payloads = [
    {"case_id": "AAROH-001", "interaction_date": "2026-08-20", "response_delay_hours": 2.0, "completed": True},
    {"case_id": "AAROH-001", "interaction_date": "2026-08-27", "response_delay_hours": 1.0, "completed": True},
]

current = preprocess_interaction(current_payload)
history = [preprocess_interaction(h) for h in history_payloads]

engagement = extract_engagement_features(current, history=history, config=EngagementConfig())
# engagement is a strongly typed, immutable EngagementFeatures dataclass
```

## Longitudinal Feature Extraction (Slice 2.5)

The longitudinal feature extraction layer (`backend.ml.features.longitudinal`) tracks multi-interaction timelines to extract distress rate-of-change, acceleration, volatility, baseline deltas, and trajectory patterns:

1. **Centralized Definitions & Trend Classification (`longitudinal_definitions.py`)**:
   - Single source of truth for trajectory trend enums: `LongitudinalTrend` (`UNKNOWN`, `STABLE`, `IMPROVING`, `WORSENING`, `RAPIDLY_IMPROVING`, `RAPIDLY_WORSENING`).
   - Configurable policy object `LongitudinalConfig` holding operational cutoffs (`rapid_shift_threshold`, `notable_shift_threshold`, `high_distress_threshold`, `rapid_velocity_threshold`, `volatility_alert_threshold`).
   - `classify_longitudinal_trend()` centralized classification used across features, future models, and explainability.
2. **Preserve `None != 0` Invariant & Explicit `UNKNOWN`**:
   - Missing historical interactions or single-point observations leave baseline distress, historical deltas, velocity, acceleration, and volatility as `None` (never fabricated as 0.0).
   - Insufficient history (< `min_observations_for_trend`) explicitly produces `longitudinal_trend = "UNKNOWN"` instead of guessing.
3. **Core Observable Metrics**:
   - `distress_velocity`: First derivative / slope of composite distress per day.
   - `distress_acceleration`: Second derivative / rate of change of velocity ($N \ge 3$).
   - `distress_volatility`: Sample standard deviation of observed distress scores across the timeline ($N \ge 2$).
   - `delta_from_baseline`: Shift relative to initial interaction.
   - `delta_from_previous`: Shift relative to immediately preceding interaction.
   - `peak_distress` & `trough_distress`: Extremes across observed timeline.
   - `sustained_distress_count`: Consecutive recent interactions exceeding high distress threshold ($\ge 0.65$).
4. **Structured Explainability Evidence (`LongitudinalEvidence`)**:
   - Retains observation count, sequence timestamps, distress scores, deltas, rates, trend, and human-readable `contributing_factors` (e.g., `"Distress substantially elevated above baseline (+0.35)"`, `"Rapidly worsening distress trajectory detected"`, `"Sustained high distress across 3 consecutive interactions"`).

### How to extract Longitudinal Features

```python
from backend.ml import (
    LongitudinalConfig,
    extract_longitudinal_features,
    preprocess_interaction,
)

current_payload = {
    "case_id": "AAROH-001",
    "interaction_date": "2026-09-01",
    "fear_level": 4,
    "safety_response": 2,
}

history_payloads = [
    {"case_id": "AAROH-001", "interaction_date": "2026-08-18", "fear_level": 1, "safety_response": 5},
    {"case_id": "AAROH-001", "interaction_date": "2026-08-25", "fear_level": 2, "safety_response": 4},
]

current = preprocess_interaction(current_payload)
history = [preprocess_interaction(h) for h in history_payloads]

longitudinal = extract_longitudinal_features(current, history=history, config=LongitudinalConfig())
# longitudinal is a strongly typed, immutable LongitudinalFeatures dataclass
```

## ML Input Assembly (Slice 3.1)

The input assembly layer (`backend.ml.features.assembly`) unifies multimodal features into a standardized, deterministic numeric representation (`MLInput`) ready for future baseline and escalation modeling:

1. **Centralized Feature Registry & Permanent Ordering (`registry.py`)**:
   - Single source of truth for all 60 numerical features spanning text (0–17), behavioural (18–25), engagement (26–38), longitudinal (39–51), and voice (52–59).
   - Indices are contiguous from 0 to $N-1$ and permanently frozen to prevent silent reordering across future model calibrations.
   - Schema versioning: `ML_INPUT_SCHEMA_VERSION = "3.1.0"`. Any breaking index or feature ordering changes require an explicit schema version increment.
2. **Deterministic Numeric Feature Vector (`feature_vector()`)**:
   - `ml_input.feature_vector()` returns an ordered tuple of floats matching `FEATURE_REGISTRY`.
   - **Strict `None != 0` Preservation**: Missing features (e.g., absent voice, missing text, or absent history) evaluate strictly to `None` in the vector, preventing false zero attribution.
   - Optional imputation `feature_vector(impute_missing=0.0)` is available when models require non-null dense arrays.
3. **Locked Voice→ML Contract (`voice.py`)**:
   - Consumes acoustic metrics (`speech_rate`, `pause_ratio`, `response_latency`, `pitch_variability`, `energy_variation`, `audio_quality`, `asr_confidence`, `baseline_deviation`) through `VoiceFeatures`.
   - Voice features are purely consumed; ASR and acoustic processing remain external to the ML package.
4. **Explainability Mapping**:
   - `ml_input.get_feature_metadata(name_or_index)` produces an explicit explainability record (`index → name → source + value + description + range`), enabling future inference layers to generate feature-grounded explanation factors.
5. **Schema and Range Validation**:
   - Enforces strict type checking on all sub-feature objects.
   - Validates feature values against declared `[min_value, max_value]` ranges, rejecting out-of-bounds values with descriptive errors.
   - Supports explicit feature masking (`mask_feature_names`) for ablation studies.

### How to assemble ML Input

```python
from backend.ml import (
    VoiceFeatures,
    assemble_ml_input,
    extract_behavioural_features,
    extract_engagement_features,
    extract_longitudinal_features,
    extract_text_features,
    preprocess_interaction,
)

current = preprocess_interaction({
    "case_id": "AAROH-001",
    "interaction_date": "2026-09-01",
    "text_response": "मुझे बहुत डर लग रहा है।",
    "safety_response": 2,
    "fear_level": 4,
})

text_feat = extract_text_features(current)
beh_feat = extract_behavioural_features(current)
eng_feat = extract_engagement_features(current)
long_feat = extract_longitudinal_features(current)
voice_feat = VoiceFeatures(voice_available=True, speech_rate=2.8, audio_quality=0.85)

ml_input = assemble_ml_input(
    text_features=text_feat,
    behavioural_features=beh_feat,
    engagement_features=eng_feat,
    longitudinal_features=long_feat,
    voice_features=voice_feat,
    case_id="AAROH-001",
    interaction_date="2026-09-01",
)

vector = ml_input.feature_vector()  # ordered tuple of 60 features (None != 0)
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

