# AAROH ML subsystem (Slice 1)

This package owns machine-learning **contracts and inference interfaces**.
It does not own FastAPI, interventions, voice/ASR, or PostgreSQL persistence.

## Responsibilities

| Module | Responsibility |
| --- | --- |
| `contract` | Nested ML API result (`distress`, `prediction`, `explanation`, `model`) plus `status` and `source` |
| `config` | Configurable prediction horizon and confidence/abstention thresholds |
| `policies` | Confidence / abstention **interfaces** and a default threshold policy |
| `inference` | `infer(...)` → Python `dict`. **No database writes.** |
| `preprocessing` | Future feature assembly (existing extractors stay in `backend/features/`) |
| `models` | Future learned-model adapters (rule-based code stays in `backend/risk/`) |
| `training` | Future reproducible training scripts (offline; not required for inference) |
| `evaluation` | Future metrics; synthetic scores are not clinical evidence |
| `explainability` | Future feature-grounded factors |
| `versioning` | Model name/version identity attached to outputs |

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

## Slice 1 limits

- No trained artifacts
- No PostgreSQL access
- Existing `features/` and `risk/` behaviour is unchanged
- If no estimates/estimator are supplied, `infer` returns `status: FAILED`

## How the application should call inference

```python
from backend.ml import infer, InferenceConfig

result = infer({"case_id": "AAROH-001"}, config=InferenceConfig())
# persist result via FastAPI / application services — not from this package
```
