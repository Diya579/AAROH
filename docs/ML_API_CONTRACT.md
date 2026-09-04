# AAROH — ML API Contract

## 1. Purpose

This document defines the contract between the AAROH Machine Learning layer and the FastAPI application layer.

The contract ensures that ML outputs are:

* structured
* validated
* traceable
* versioned
* confidence-aware
* safe to consume
* independent of the frontend

The ML layer is responsible for generating mental-health monitoring and escalation-prediction outputs.

FastAPI is responsible for validating, authorising, storing and safely exposing those outputs.

---

# 2. Ownership

### Adwait — ML Ownership

Responsible for:

* text NLP
* behavioural features
* engagement features
* longitudinal features
* multimodal fusion
* distress estimation
* distress trajectory
* escalation prediction
* ML confidence
* explainability
* model versioning
* inference interface
* model loading
* missing-feature handling
* low-confidence/abstention behaviour

### Diya — Voice Ownership

Responsible for:

* live audio capture architecture
* audio validation
* preprocessing
* ASR
* transcription
* ASR confidence
* acoustic voice features
* audio quality assessment
* voice → ML handoff

The ML layer consumes the voice-derived information but does not implement the ASR pipeline.

### Mahendra — FastAPI Ownership

Responsible for:

* request/response schemas
* authentication
* authorization
* validation
* service orchestration
* persistence
* safe API exposure
* error handling

FastAPI does not independently calculate distress or escalation.

---

# 3. ML Input

The ML layer may receive:

### Case context

```json
{
  "case_id": "CASE-001",
  "interaction_id": 101,
  "language": "hi"
}
```

### Text information

Where consent and availability permit:

```json
{
  "transcription": "Mujhe ab ghar se bahar nikalne mein darr lagta hai."
}
```

### ASR metadata

```json
{
  "asr_confidence": 0.91
}
```

ASR confidence represents transcription reliability.

It is NOT mental-health confidence.

### Voice features

```json
{
  "speech_rate": 2.8,
  "pause_ratio": 0.31,
  "response_latency": 2.4,
  "pitch_variability": 0.14,
  "energy_variation": 0.22,
  "audio_quality": 0.86,
  "baseline_deviation": 0.37
}
```

### Other ML features

Depending on availability:

* behavioural features
* engagement features
* longitudinal features
* previous distress states
* previous prediction context

Missing features must remain explicitly missing.

**NULL/missing must never automatically become zero.**

The ML layer decides how missing features are handled.

---

# 4. ML Output Contract

A successful ML inference result must conceptually follow:

```json
{
  "case_id": "CASE-001",
  "prediction_date": "2026-09-03",

  "distress": {
    "score": 0.69,
    "trajectory": "WORSENING",
    "confidence": 0.86,
    "baseline_deviation": 0.31
  },

  "prediction": {
    "escalation_probability": 0.78,
    "target_horizon_days": 7,
    "confidence": 0.86,
    "risk_level": "HIGH"
  },

  "explanation": {
    "factors": [
      "Increasing fear indicators",
      "Distress increased compared with baseline"
    ],
    "trend": "WORSENING",
    "baseline_deviation": 0.31
  },

  "model": {
    "model_name": "aaroh-escalation",
    "model_version": "aaroh-escalation-v1"
  }
}
```

---

# 5. Distress Score

`distress.score`

Type:

```text
float
```

Valid range:

```text
0.0 – 1.0
```

Interpretation:

* higher value = greater estimated distress
* lower value = lower estimated distress

The score is a monitoring/model output.

It is **not a clinical diagnosis**.

FastAPI must validate the range.

FastAPI must not recalculate the score.

---

# 6. Distress Trajectory

Allowed values:

```text
STABLE
IMPROVING
WORSENING
RAPIDLY_IMPROVING
RAPIDLY_WORSENING
```

The ML layer owns trajectory determination.

The frontend displays the returned value.

The API validates the enum.

---

# 7. Distress Confidence

`distress.confidence`

Type:

```text
float
```

Valid range:

```text
0.0 – 1.0
```

This represents confidence in the distress estimation.

It must not be confused with:

* ASR confidence
* escalation probability
* audio quality

---

# 8. Baseline Deviation

`distress.baseline_deviation`

Type:

```text
float | null
```

Valid range:

```text
>= 0
```

It represents deviation from the individual's historical baseline.

It is not a universal distress threshold.

If insufficient historical data exists:

```text
null
```

must be returned rather than a fabricated value.

---

# 9. Escalation Probability

`prediction.escalation_probability`

Type:

```text
float
```

Valid range:

```text
0.0 – 1.0
```

This represents the model's estimated probability of escalation within the specified prediction horizon.

The ML layer owns this calculation.

FastAPI validates and stores it.

The frontend must not independently calculate it.

---

# 10. Prediction Horizon

`prediction.target_horizon_days`

Type:

```text
integer
```

Must be:

```text
> 0
```

The value identifies the prediction horizon associated with the escalation probability.

For the initial AAROH implementation, a 7-day horizon may be used where supported by the model.

The frontend must display the value returned by the backend rather than assuming a horizon.

---

# 11. Risk Level

Initial supported values:

```text
LOW
MODERATE
HIGH
```

Risk level is an ML/application output based on the agreed AAROH risk contract.

The frontend must not invent risk categories.

A future `CRITICAL` level may only be introduced through a formal contract change.

---

# 12. Explainability

The ML layer may return structured explanation information.

Example:

```json
{
  "factors": [
    "Increasing fear indicators",
    "Reduced engagement",
    "Worsening recent trajectory"
  ],
  "trend": "WORSENING",
  "baseline_deviation": 0.31
}
```

Rules:

* factors must be supported by model/input evidence
* no invented explanations
* explanations must not claim clinical certainty
* frontend must not generate its own explanations
* explanations must respect role-based access
* sensitive raw narratives must not be exposed unnecessarily

---

# 13. Model Version

Every successful prediction must be traceable to a model version.

Example:

```json
{
  "model_name": "aaroh-escalation",
  "model_version": "aaroh-escalation-v1"
}
```

The model version must be stored with the prediction.

Historical predictions must remain associated with the version that produced them.

A model update must not silently rewrite historical predictions.

---

# 14. ML Processing Status

The application must distinguish between successful and unsuccessful ML processing.

Initial statuses:

```text
SUCCESS
FAILED
INSUFFICIENT_DATA
LOW_CONFIDENCE
ABSTAINED
```

### SUCCESS

A valid prediction was produced.

### FAILED

The ML process failed technically.

No fabricated prediction may be created.

### INSUFFICIENT_DATA

There is not enough valid information to produce a reliable result.

### LOW_CONFIDENCE

A result was produced but confidence is below the agreed operational threshold.

The result may be stored but must remain explicitly marked as low confidence.

### ABSTAINED

The model deliberately declines to provide a prediction because its reliability conditions were not satisfied.

The exact threshold/abstention policy is owned by the ML contract and implementation.

---

# 15. Failure Rules

If ML fails:

**Do not create a fake low-risk result.**

For example, this is invalid:

```json
{
  "escalation_probability": 0.0,
  "risk_level": "LOW"
}
```

when inference actually failed.

Instead:

```text
ML status = FAILED
```

and the API should return an appropriate processing/error state.

---

# 16. Confidence Distinctions

AAROH contains multiple independent quality/confidence concepts.

They must never be conflated.

| Field                    | Meaning                                 |
| ------------------------ | --------------------------------------- |
| `asr_confidence`         | Reliability of speech transcription     |
| `audio_quality`          | Suitability of recording for processing |
| `distress.confidence`    | Confidence in distress estimation       |
| `prediction.confidence`  | Confidence in escalation prediction     |
| `escalation_probability` | Estimated probability of escalation     |

None of these values alone represents a diagnosis.

---

# 17. Missing Features

The voice/feature pipeline may return:

```text
null
```

for unavailable features.

Examples:

```json
{
  "speech_rate": null,
  "pitch_variability": null
}
```

This does NOT mean:

```text
speech_rate = 0
pitch_variability = 0
```

The ML layer is responsible for deciding whether available features are sufficient.

---

# 18. Consent Boundary

ML processing must respect applicable consent.

In particular:

* voice-derived processing requires appropriate voice-analysis consent
* text analysis requires appropriate text-analysis consent
* monitoring processing requires monitoring consent

FastAPI must enforce consent before invoking protected processing.

ML must not bypass the application authorization/consent boundary.

---

# 19. Privacy

The ML layer must not unnecessarily persist:

* raw audio
* raw transcripts
* sensitive narratives

Raw sensitive information should only be retained according to the approved retention policy.

Logs must not contain:

* raw victim narratives
* raw audio
* passwords
* authentication tokens
* API keys
* database credentials

---

# 20. Production Independence

The production inference system must not depend on:

* Google Colab sessions
* manually running notebooks
* developer laptops
* temporary notebook state

Training may occur in an appropriate development/training environment.

Production inference must load a versioned model artifact through an independent inference service/process.

---

# 21. FastAPI Validation Boundary

The flow is:

```text
ML
 ↓
ML Output
 ↓
FastAPI
 ↓
Schema Validation
 ↓
Authorization / Scope Checks
 ↓
Persistence
 ↓
Frontend / Intervention
```

FastAPI must reject invalid outputs such as:

* probability < 0
* probability > 1
* confidence < 0
* confidence > 1
* invalid trajectory
* invalid risk level
* invalid horizon
* missing required identifiers

---

# 22. Historical Integrity

Predictions are historical records.

Once stored, a prediction must not be silently overwritten because a newer model produced a different result.

The system should preserve:

```text
Prediction 1 → Model v1
Prediction 2 → Model v1
Prediction 3 → Model v2
```

This allows longitudinal analysis and model traceability.

---

# 23. Contract Change Rule

Any change to this contract must follow:

```text
Propose
   ↓
Impact assessment
   ↓
Team agreement
   ↓
Update contract
   ↓
Update dependent implementation
   ↓
Integration test
```

No developer should silently change shared ML fields.

---

# 24. Non-Goals

The ML layer must NOT:

* diagnose mental illness
* autonomously prescribe treatment
* autonomously make legal decisions
* autonomously decide witness protection
* autonomously approve relocation
* autonomously approve financial assistance
* directly modify PostgreSQL
* bypass FastAPI authorization
* fabricate outputs when inference fails

AAROH provides decision support and monitoring information for authorised human workflows.
