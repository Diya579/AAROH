
# AAROH — Database Contract

## 1. Purpose

This document defines the shared database contract for AAROH.

The database is the persistent source of truth for:

- cases
- case lifecycle events
- victim interactions
- extracted features
- longitudinal distress states
- escalation predictions
- consent
- interventions
- intervention outcomes
- model versions

All team members must treat this contract as shared infrastructure.

No developer should silently change a shared table, field meaning, relationship, enum, or data contract.

---

## 2. Database

### Development

- Database: PostgreSQL
- Host: localhost
- Port: 5432
- Database: aaroh
- ORM: SQLAlchemy

### Production

Production PostgreSQL configuration must be supplied through environment variables or a managed secret.

Credentials must never be committed to Git.

---

## 3. Core Data Flow

```text
Case
 ↓
Case Events
 ↓
Interactions
 ↓
Feature Extraction
 ├── Text Features
 ├── Voice Features
 └── Engagement Features
 ↓
Dynamic Distress State
 ↓
Escalation Prediction
 ↓
Intervention
 ↓
Outcome
 ↓
New Interaction
 ↓
Updated Distress State
````

Historical predictions and distress states must not be overwritten.

---

## 4. Tables

### 4.1 cases

Represents a registered victim/complainant case.

| Field              | Type               | Purpose                                |
| ------------------ | ------------------ | -------------------------------------- |
| id                 | Integer PK         | Internal identifier                    |
| case_id            | String(50), unique | Public/business case identifier        |
| language           | String(20)         | Primary case language                  |
| district_type      | String(20)         | District classification                |
| district           | String(100)        | District                               |
| priority_use_case  | String(100)        | Priority atrocity/use-case category    |
| current_stage      | String(50)         | Current case stage                     |
| voice_opted_in     | Boolean            | Whether voice interaction is permitted |
| monitoring_consent | Boolean            | Whether monitoring is permitted        |
| created_at         | DateTime           | Case creation time                     |

`case_id` must remain unique.

---

### 4.2 case_events

Represents important events in the case lifecycle.

Examples:

* complaint registration
* investigation
* court appearance
* threat/intimidation event
* rehabilitation event
* compensation event
* case-stage change

Each event belongs to exactly one case.

---

### 4.3 interactions

Represents a monitoring interaction with the victim.

Possible channels include:

* chatbot
* IVRS
* SMS
* mobile application
* web
* helpline
* approved future channels

Interaction data may contain:

* text response
* voice availability
* safety response
* sleep disruption
* fear level
* social support
* help request
* completion state
* data quality

Sensitive narrative content must not be unnecessarily exposed through logs or aggregate dashboards.

---

### 4.4 text_features

Stores features extracted from interaction text.

Current baseline features:

* distress_intensity
* fear
* intimidation
* hopelessness
* isolation
* help_seeking
* language_confidence

Future multilingual NLP may add richer model-generated features, but existing field meanings must remain stable unless the contract is deliberately revised.

---

### 4.5 voice_features

Stores features derived from voice/audio.

Current baseline:

* speech_rate
* pause_ratio
* response_latency
* pitch_variability
* energy_variation
* audio_quality
* baseline_deviation

The complete audio pipeline is owned by Diya.

```text
Audio
 ↓
Validation
 ↓
Preprocessing
 ↓
ASR
 ↓
Transcription + Language
 ↓
Voice Features
 ↓
ML Feature Handoff
```

Voice-derived features are handed to the ML layer for fusion.

---

### 4.6 engagement_features

Stores behavioural/engagement signals.

Current fields:

* response_delay
* missed_checkin
* engagement_change

These features support longitudinal monitoring and should not be interpreted independently as clinical diagnoses.

---

### 4.7 distress_states

Represents the dynamic psychological distress state at a point in time.

Fields:

* case_id
* observation_date
* distress_score
* trajectory
* confidence

Trajectory values currently used by the baseline:

```text
RAPIDLY_WORSENING
WORSENING
STABLE
IMPROVING
RAPIDLY_IMPROVING
```

Distress states are historical observations and must not be overwritten.

---

### 4.8 predictions

Represents an escalation-risk prediction.

Required conceptual fields:

* case_id
* prediction_date
* escalation_probability
* target_horizon_days
* confidence

The prediction layer must eventually additionally provide:

* risk_level
* explanation
* model_version
* uncertainty/abstention state

Example conceptual response:

```json
{
  "case_id": "CASE-001",
  "prediction_date": "2026-09-03",
  "escalation_probability": 0.78,
  "target_horizon_days": 7,
  "confidence": 0.86,
  "risk_level": "HIGH",
  "explanation": {
    "factors": [],
    "trend": "WORSENING",
    "baseline_deviation": 0.31,
    "model_version": "aaroh-escalation-v1"
  }
}
```

Predictions are historical records.

A new prediction creates a new record.

---

### 4.9 consents

Stores consent and safe-contact preferences.

Current consent dimensions:

* monitoring_consent
* text_analysis_consent
* voice_analysis_consent
* case_linkage_consent

Safe-contact fields:

* safe_channel
* safe_time

Consent must be checked before the corresponding automated processing occurs.

Withdrawal of consent must restrict subsequent processing according to the applicable consent type.

---

### 4.10 interventions

Represents an intervention recommendation/workflow.

Current fields:

* case_id
* intervention_type
* status
* assigned_to

Intervention decisions remain human-controlled.

AI may recommend prioritisation or follow-up, but must not autonomously decide:

* medical treatment
* legal action
* witness protection
* relocation
* financial assistance
* rehabilitation decisions

---

### 4.11 outcomes

Represents the result of an intervention.

Fields:

* case_id
* intervention_id
* outcome_type
* completed
* recorded_at

Outcomes form the feedback loop:

```text
Prediction
 ↓
Intervention
 ↓
Outcome
 ↓
New Interaction
 ↓
New Prediction
```

Historical outcomes must be preserved.

---

### 4.12 model_versions

Tracks deployed/trained model versions.

Conceptual fields:

* model_name
* version
* created_at

Predictions should eventually reference the exact model version that generated them.

Model versioning must allow historical predictions to remain interpretable after a newer model is deployed.

---

## 5. Relationships

Primary relationships:

```text
Case
 ├── CaseEvent
 ├── Interaction
 │    ├── TextFeature
 │    ├── VoiceFeature
 │    └── EngagementFeature
 ├── DistressState
 ├── Prediction
 ├── Consent
 ├── Intervention
 │    └── Outcome
 └── Outcome
```

Every child record must reference a valid parent.

The current baseline has been verified to contain zero orphan records.

---

## 6. Integrity Rules

The following rules are mandatory:

1. Every case must have a unique `case_id`.
2. Every event must belong to an existing case.
3. Every interaction must belong to an existing case.
4. Every feature record must belong to an existing interaction.
5. Every distress state must belong to an existing case.
6. Every prediction must belong to an existing case.
7. Every consent record must belong to an existing case.
8. Every intervention must belong to an existing case.
9. Every outcome must belong to an existing case.
10. An outcome referencing an intervention must reference an existing intervention.
11. Historical distress states must not be overwritten.
12. Historical predictions must not be overwritten.
13. Sensitive information must not be placed in application logs.
14. Credentials and secrets must never be stored in the database schema as hardcoded values.

---

## 7. Consent Rules

Consent is a first-class system constraint.

Before processing:

* monitoring data → monitoring consent
* text analysis → text analysis consent
* voice analysis → voice analysis consent
* external/case linkage → case linkage consent

The system must not silently bypass consent because an interaction contains available data.

Safe channel and safe time must be respected by intervention/contact workflows.

---

## 8. Prediction Contract

The prediction system must provide:

```text
case_id
prediction_date
escalation_probability
target_horizon_days
confidence
risk_level
explanation
model_version
```

Expected numeric ranges:

```text
escalation_probability ∈ [0, 1]
confidence ∈ [0, 1]
target_horizon_days > 0
```

Low-confidence predictions must not be presented as certain.

Where the model cannot produce a reliable prediction, the system should support an explicit uncertainty/abstention state rather than fabricating a value.

The existing rule-based risk system remains the fallback until the real ML inference pipeline is production-ready.

---

## 9. Intervention Contract

Conceptual flow:

```text
Prediction
 ↓
Risk Level
 ↓
Intervention Engine
 ↓
Priority
 ↓
Assignment/Routing
 ↓
Human Official/Counsellor
 ↓
Outcome
```

The intervention layer must:

* respect consent
* prevent duplicate pending interventions where applicable
* preserve status
* support assignment
* support priority/SLA information
* link outcomes to interventions
* distinguish AI recommendation from human decision

---

## 10. Model Versioning

Every production prediction must be traceable to a model version.

Example:

```text
aaroh-distress-v1
aaroh-escalation-v1
```

A model update must not invalidate or overwrite historical predictions.

Model artifacts must be loadable independently of training environments such as Google Colab.

Training and production inference are separate concerns.

---

## 11. Migration Rules

Database changes must follow:

```text
Propose
 ↓
Review
 ↓
Update Contract
 ↓
Migration
 ↓
Update Dependents
 ↓
Test
 ↓
Merge
```

No developer may silently modify shared database structures.

Schema changes must not break existing data.

Migrations must be reproducible on:

* an empty database
* the existing development database
* the deployment database

Where practical, rollback procedures should be documented.

---

## 12. Indexing Strategy

Indexes should be introduced deliberately based on actual query patterns.

Expected high-value access patterns include:

* case lookup by `case_id`
* interactions by `case_id` + date
* case events by `case_id` + date
* distress states by `case_id` + observation date
* predictions by `case_id` + prediction date
* interventions by `case_id` + status
* outcomes by `case_id` + recorded date

Indexes must be reviewed before production deployment.

---

## 13. Security

The database must support:

* least-privilege database users
* encrypted connections in production
* secret management through environment/configuration
* restricted access
* backups
* restore testing
* auditability
* sensitive-data minimization

Raw victim narratives must never be exposed through national/state/district aggregate analytics.

---

## 14. Current Baseline Status

Verified baseline:

```text
Cases: 20
Events: 200
Interactions: 200
Text features: 200
Voice features: 200
Engagement features: 200
Distress states: 200
Predictions: 20
Consents: 20
Interventions: 20
Outcomes: 0
Model versions: 0
```

Referential-integrity verification:

```text
All orphan checks: 0
```

Pipeline validation:

```text
AAROH PIPELINE VALIDATION: PASSED
```

The current baseline must remain reproducible before schema migrations begin.

---

## 15. Ownership

### Diya

* database architecture
* migrations
* cloud database
* database security
* complete voice/audio pipeline
* system integration
* final validation

### Adwait

* NLP
* behavioural/engagement/longitudinal ML
* distress model
* escalation model
* confidence/uncertainty
* explainability
* model versioning
* ML inference

Adwait consumes voice-derived features/transcriptions but does not own the voice pipeline implementation.

### Mahendra

* FastAPI
* Pydantic/API contracts
* services
* database integration
* case/interaction/event/consent APIs
* authentication/authorization implementation

### Preet

* intervention engine
* risk-to-action mapping
* assignment/routing
* SLA workflow
* outcomes
* intervention analytics

---

## 16. Non-Negotiable Rules

AAROH must not:

* fake NHAA APIs
* claim synthetic data proves clinical validity
* present itself as a diagnostic system
* allow AI to autonomously make medical/legal/witness-protection decisions
* overwrite historical predictions
* fabricate missing data
* expose sensitive narratives in aggregate dashboards
* hard-code credentials
* commit secrets or real victim data
* allow uncontrolled shared-schema modifications
* merge untested database changes into `main`
* depend on Google Colab for production inference

