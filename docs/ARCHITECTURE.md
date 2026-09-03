\# AAROH — System Architecture



\*\*Project:\*\* AI-Powered Dynamic Mental Health Monitoring and Distress Prediction System for Victims of Atrocities



\*\*Version:\*\* 1.0  

\*\*Status:\*\* Architecture Freeze — Development Baseline  

\*\*Date:\*\* September 2026



\---



\## 1. Purpose



AAROH is a dynamic mental-health monitoring and distress-prediction system designed for victims/complainants registered through approved channels such as NHAA (14566), the Integrated Portal, chatbot, mobile application, IVRS, SMS, web, or other authorized interfaces.



The system continuously monitors changes in psychological distress over time and identifies potential escalation so that designated human officials or counsellors can respond earlier.



AAROH is an assistive decision-support system.



It is \*\*not a clinical diagnostic system\*\* and AI predictions must not autonomously determine medical treatment, legal decisions, witness protection, relocation, compensation, or rehabilitation decisions.



\---



\## 2. Core System Flow



```text

Victim / Complainant

&#x20;       |

&#x20;       v

Periodic Interaction

(Chat / Web / Mobile / IVRS / Voice / SMS)

&#x20;       |

&#x20;       v

+-----------------------------+

| Data Collection             |

| Text / Voice / Behavioural  |

| Engagement / Safety Data    |

+-----------------------------+

&#x20;       |

&#x20;       v

Feature Extraction

&#x20;       |

&#x20;       +--------------------+

&#x20;       |                    |

&#x20;       v                    v

&#x20;  Text Features        Voice Features

&#x20;       |                    |

&#x20;       +---------+----------+

&#x20;                 |

&#x20;                 v

&#x20;         Feature Fusion

&#x20;                 |

&#x20;                 v

&#x20;      Dynamic Distress Score

&#x20;                 |

&#x20;                 v

&#x20;     Longitudinal Trend /

&#x20;     Baseline Deviation

&#x20;                 |

&#x20;                 v

&#x20;      Escalation Prediction

&#x20;                 |

&#x20;                 v

&#x20;            Risk Level

&#x20;                 |

&#x20;                 v

&#x20;       Intervention Engine

&#x20;                 |

&#x20;                 v

&#x20;      Human Official /

&#x20;         Counsellor

&#x20;                 |

&#x20;                 v

&#x20;           Outcome

&#x20;                 |

&#x20;                 v

&#x20;      Continued Monitoring

&#x20;                 |

&#x20;                 +-----------> New Interaction

````



The important architectural principle is that AAROH is \*\*longitudinal\*\*.



A single interaction should not be treated as the complete state of a victim. Historical observations, current distress, changes from baseline, engagement changes, and previous interventions must contribute to the overall picture.



\---



\## 3. High-Level Architecture



```text

+----------------------------------------------------------+

|                    CLIENT / CHANNELS                     |

|----------------------------------------------------------|

| Victim Web | Mobile | Chatbot | IVRS | SMS | Helpline   |

| Official Dashboard | Counsellor Dashboard                |

+---------------------------+------------------------------+

&#x20;                           |

&#x20;                           v

+----------------------------------------------------------+

|                     FASTAPI APPLICATION                  |

|----------------------------------------------------------|

| Authentication                                             |

| Authorization / RBAC                                      |

| Request Validation                                        |

| Case APIs                                                 |

| Interaction APIs                                          |

| Consent APIs                                              |

| Event APIs                                                |

| Prediction APIs                                           |

| Intervention APIs                                         |

| Outcome APIs                                              |

| Analytics APIs                                            |

| Health / Readiness                                        |

+---------------------------+------------------------------+

&#x20;                           |

&#x20;                           v

+----------------------------------------------------------+

|                     SERVICE LAYER                        |

|----------------------------------------------------------|

| Case Service                                              |

| Interaction Service                                       |

| Consent Service                                           |

| Event Service                                             |

| Prediction Service                                        |

| Intervention Service                                      |

| Outcome Service                                           |

| Analytics Service                                         |

| Audit Service                                             |

| NHAA Adapter                                              |

+-------------+--------------------------+-----------------+

&#x20;             |                          |

&#x20;             v                          v

+--------------------------+    +---------------------------+

|     PostgreSQL           |    |       AI / ML Layer       |

|--------------------------|    |---------------------------|

| Cases                    |    | Text NLP                 |

| Interactions             |    | Voice-derived Features   |

| Events                   |    | Behavioural Features     |

| Consent                  |    | Engagement Features     |

| Features                 |    | Longitudinal Features    |

| Distress States          |    | Distress Model           |

| Predictions              |    | Escalation Model         |

| Interventions            |    | Confidence / Abstention  |

| Outcomes                 |    | Explainability           |

| Model Versions           |    | Model Artifacts          |

| Audit Records            |    +---------------------------+

+--------------------------+

&#x20;             ^

&#x20;             |

&#x20;             |

+-------------+--------------------------------------------+

|                 DIYA VOICE PIPELINE                      |

|----------------------------------------------------------|

| Audio Input                                               |

|      ↓                                                    |

| Validation                                                |

|      ↓                                                    |

| Preprocessing                                             |

|      ↓                                                    |

| ASR                                                       |

|      ↓                                                    |

| Transcription + Language                                  |

|      ↓                                                    |

| Voice Feature Extraction                                  |

|      ↓                                                    |

| Text + Voice Features → ML Layer                         |

+----------------------------------------------------------+

```



\---



\## 4. Component Responsibilities



\### 4.1 FastAPI Application



The FastAPI layer is the controlled entry point into AAROH.



It is responsible for:



\* API routing

\* request validation

\* authentication

\* authorization

\* service invocation

\* response formatting

\* error handling

\* API documentation

\* health/readiness endpoints



The API must not contain large amounts of business logic or direct raw database manipulation.



\---



\### 4.2 Service Layer



The service layer contains application/business workflows.



Expected services include:



```text

CaseService

InteractionService

ConsentService

EventService

PredictionService

InterventionService

OutcomeService

AnalyticsService

AuditService

```



Services communicate with repositories/database models and ML components through defined interfaces.



\---



\### 4.3 PostgreSQL



PostgreSQL is the persistent data foundation of AAROH.



It stores:



\* case information

\* case events

\* interactions

\* consent

\* extracted features

\* distress states

\* predictions

\* interventions

\* outcomes

\* model versions

\* audit information



Historical predictions and distress states must be preserved.



New predictions must not overwrite previous predictions.



\---



\## 5. Database Architecture



The current database baseline contains the following primary entities:



```text

Case

&#x20;|

&#x20;+---- CaseEvent

&#x20;|

&#x20;+---- Interaction

&#x20;         |

&#x20;         +---- TextFeature

&#x20;         +---- VoiceFeature

&#x20;         +---- EngagementFeature

&#x20;|

&#x20;+---- DistressState

&#x20;|

&#x20;+---- Prediction

&#x20;|

&#x20;+---- Consent

&#x20;|

&#x20;+---- Intervention

&#x20;         |

&#x20;         +---- Outcome

&#x20;|

&#x20;+---- ModelVersion

```



The existing schema is the development baseline.



Schema changes must follow this process:



```text

Propose change

&#x20;     ↓

Review impact

&#x20;     ↓

Update shared contract

&#x20;     ↓

Migration

&#x20;     ↓

Update dependent code

&#x20;     ↓

Run validation

```



No team member should silently change shared database structures while another component depends on them.



\---



\## 6. Voice / Audio Architecture



AAROH's voice pipeline is owned by \*\*Diya\*\*.



The pipeline is deliberately separated from the downstream ML models.



```text

Audio

&#x20; |

&#x20; v

Audio Validation

&#x20; |

&#x20; v

Preprocessing

&#x20; |

&#x20; v

ASR

&#x20; |

&#x20; v

Transcription + Language Detection

&#x20; |

&#x20; +----------------------+

&#x20; |                      |

&#x20; v                      v

Text                    Voice

&#x20; |                    Features

&#x20; |                      |

&#x20; +----------+-----------+

&#x20;            |

&#x20;            v

&#x20;      ML Feature Fusion

```



\### 6.1 Audio Validation



The system must validate:



\* supported file format

\* file size

\* duration

\* sample rate

\* channel configuration

\* corrupted files

\* empty audio

\* unusable audio



Invalid audio must produce a controlled error and must not crash the API.



\---



\### 6.2 Preprocessing



Preprocessing may include:



\* resampling

\* channel normalization

\* silence handling

\* noise reduction where appropriate

\* amplitude normalization

\* conversion into the ASR-supported format



The original audio should not be modified destructively.



\---



\### 6.3 ASR



The ASR component converts speech into text.



The selected ASR implementation must support the languages chosen for the AAROH demo.



The ASR layer must return at minimum:



```json

{

&#x20; "transcript": "...",

&#x20; "language": "en",

&#x20; "confidence": 0.91

}

```



Low-confidence transcription must remain identifiable.



A failed transcription must not be silently treated as valid text.



\---



\### 6.4 Voice Features



Where sufficient-quality audio exists, voice-derived features may include:



\* speech rate

\* pause ratio

\* response latency

\* pitch variability

\* energy variation

\* audio quality

\* deviation from baseline



These features are inputs to the downstream ML system.



Voice processing must gracefully handle:



```text

Missing audio

Poor-quality audio

Unsupported format

Failed transcription

Low-confidence transcription

```



No voice-derived feature should be fabricated when the underlying audio is unavailable.



\---



\## 7. AI / ML Boundary



The ML system consumes structured features rather than directly depending on the API implementation.



Conceptually:



```text

Interaction

&#x20;   |

&#x20;   v

Feature Extraction

&#x20;   |

&#x20;   +---- Text

&#x20;   +---- Voice

&#x20;   +---- Behavioural

&#x20;   +---- Engagement

&#x20;   +---- Longitudinal

&#x20;   |

&#x20;   v

Feature Fusion

&#x20;   |

&#x20;   v

Dynamic Distress Model

&#x20;   |

&#x20;   v

Distress State

&#x20;   |

&#x20;   v

Escalation Model

&#x20;   |

&#x20;   v

Prediction

```



The ML layer must eventually support:



\* multilingual NLP

\* behavioural signals

\* engagement signals

\* longitudinal signals

\* voice-derived signals where available

\* dynamic distress estimation

\* escalation prediction

\* confidence estimation

\* low-confidence handling / abstention

\* explainability

\* model versioning



The current rule-based system remains the fallback/development baseline until real ML models are integrated.



\---



\## 8. ML → Application Contract



The ML inference layer should expose a stable structured response.



Example:



```json

{

&#x20; "case\_id": "CASE-001",

&#x20; "prediction\_date": "2026-09-03",

&#x20; "escalation\_probability": 0.78,

&#x20; "target\_horizon\_days": 7,

&#x20; "confidence": 0.86,

&#x20; "risk\_level": "HIGH",

&#x20; "explanation": {

&#x20;   "factors": \[],

&#x20;   "trend": "WORSENING",

&#x20;   "baseline\_deviation": 0.31,

&#x20;   "model\_version": "aaroh-escalation-v1"

&#x20; }

}

```



Required principles:



\* probability must remain between 0 and 1

\* confidence must remain between 0 and 1

\* horizon must be explicit

\* risk level must use a defined enum

\* trend must use a defined enum

\* model version must be identifiable

\* missing values must be explicit

\* low-confidence predictions must not be presented as certainty

\* model failures must return controlled errors

\* historical predictions must remain stored



\---



\## 9. Risk and Intervention Boundary



AAROH separates AI prediction from human intervention.



```text

Prediction

&#x20;   |

&#x20;   v

Risk Level

&#x20;   |

&#x20;   v

Intervention Engine

&#x20;   |

&#x20;   v

Priority

&#x20;   |

&#x20;   v

Assignment / Routing

&#x20;   |

&#x20;   v

Human Official / Counsellor

&#x20;   |

&#x20;   v

Outcome

```



The AI recommends and prioritizes.



A human official remains responsible for decisions involving:



\* medical treatment

\* counselling decisions

\* legal aid

\* witness protection

\* relocation

\* financial assistance

\* rehabilitation

\* other official action



\---



\## 10. Consent and Privacy



Consent is a first-class architectural requirement.



Relevant consent categories include:



```text

Monitoring Consent

Text Analysis Consent

Voice Analysis Consent

Case Linkage Consent

Safe Channel

Safe Time

```



Automated processing must respect applicable consent.



If consent is withdrawn, processing must be restricted according to the defined system policy.



The system must follow data minimization principles.



Sensitive narratives must not be unnecessarily exposed through logs or aggregate dashboards.



Secrets must never be stored in source code.



\---



\## 11. Authentication and Authorization



AAROH must implement role-based access control.



Expected roles include:



```text

Victim / User

Counsellor

District Official

State Official

National / Admin

System Service

```



Authorization must be checked after authentication and before access to protected resources.



Examples:



```text

Victim

&#x20; → own permitted information



Counsellor

&#x20; → assigned / authorized cases



District Official

&#x20; → permitted district information



State Official

&#x20; → permitted state-level information



National Official

&#x20; → permitted national-level information

```



The exact permission matrix must be defined before production deployment.



\---



\## 12. Audit Logging



Important security-sensitive actions should be auditable.



Examples:



```text

Login

Case access

Case modification

Consent change

Prediction generation

Intervention creation

Intervention assignment

Outcome update

Administrative action

```



Audit records should contain:



```text

Actor

Action

Timestamp

Resource

Relevant metadata

```



Raw sensitive narratives should not be unnecessarily copied into audit logs.



\---



\## 13. Outcome Feedback Loop



AAROH must close the loop between intervention and monitoring.



```text

Interaction

&#x20;   ↓

Prediction

&#x20;   ↓

Intervention

&#x20;   ↓

Human Action

&#x20;   ↓

Outcome

&#x20;   ↓

New Interaction

&#x20;   ↓

Updated Distress

&#x20;   ↓

New Prediction

```



This allows the system to represent whether a case is:



```text

Worsening

Stable

Improving

Rapidly Worsening

Rapidly Improving

```



Previous states remain part of the longitudinal history.



\---



\## 14. NHAA Integration Boundary



AAROH must not claim a direct government integration unless an authorized integration actually exists.



The architecture therefore uses an adapter boundary:



```text

AAROH

&#x20; |

&#x20; v

NHAA Adapter

&#x20; |

&#x20; +---- Demo / Mock Implementation

&#x20; |

&#x20; +---- Future Authorized NHAA Integration

```



The demo implementation must be clearly labelled as simulated/demo data.



A future authorized integration should replace the adapter implementation without requiring the rest of AAROH to be redesigned.



No fake NHAA endpoint or fabricated government API should be presented as real.



\---



\## 15. Dashboard Architecture



The backend must expose data required for:



\### Case-level view



```text

Case

Current distress

Distress trend

Escalation probability

Prediction confidence

Explanation

Timeline

Interventions

Outcomes

```



\### District-level view



```text

Total monitored cases

Risk distribution

High-priority cases

Intervention status

Outcome statistics

Trend summaries

```



\### State-level view



Aggregated statistics across authorized districts.



\### National-level view



Aggregated national indicators.



Aggregate dashboards must not expose raw sensitive victim narratives unnecessarily.



\---



\## 16. Failure and Safety Behaviour



AAROH must fail safely.



\### ML unavailable



```text

ML unavailable

&#x20;     ↓

Do not crash API

&#x20;     ↓

Mark prediction unavailable

&#x20;     ↓

Use approved fallback behaviour

&#x20;     ↓

Allow human review

```



\### Low confidence



```text

Low confidence

&#x20;     ↓

Mark prediction as uncertain

&#x20;     ↓

Do not present certainty

&#x20;     ↓

Allow human review

```



\### Missing data



```text

Missing data

&#x20;     ↓

Do not fabricate values

&#x20;     ↓

Record data-quality limitation

&#x20;     ↓

Continue where possible

```



\### Database failure



```text

Database failure

&#x20;     ↓

Controlled API error

&#x20;     ↓

No partial/corrupt state

```



\### Consent withdrawal



```text

Consent withdrawn

&#x20;     ↓

Restrict applicable automated processing

```



\---



\## 17. Development Ownership



\### Diya



Owns:



\* system architecture

\* database foundation

\* migrations

\* cloud database

\* integration

\* security

\* deployment

\* final validation

\* complete voice/audio pipeline



\### Adwait



Owns:



\* NLP

\* behavioural features

\* engagement features

\* longitudinal features

\* distress model

\* escalation model

\* training/evaluation

\* confidence/uncertainty

\* explainability

\* model versioning

\* ML inference



Receives voice-derived features/transcriptions from Diya.



\### Mahendra



Owns:



\* FastAPI

\* API routes

\* Pydantic schemas

\* authentication

\* authorization

\* application services

\* case APIs

\* interaction APIs

\* event APIs

\* consent APIs

\* prediction APIs

\* intervention APIs

\* outcome APIs

\* database integration

\* API tests/documentation



Audio ingestion/upload may be exposed by the API, but ASR and voice AI remain outside this responsibility.



\### Preet



Owns:



\* intervention logic

\* risk-to-action mapping

\* assignment/routing

\* priority

\* SLA handling

\* intervention status

\* outcome workflow

\* intervention analytics



\---



\## 18. Shared Contracts



The following interfaces must remain stable unless the team explicitly agrees to change them:



```text

Database schema

API request/response schemas

ML inference interface

Prediction object

Risk-level enum

Trend enum

Intervention object

Outcome object

Consent behaviour

Authentication/RBAC rules

```



Any contract change must be communicated before dependent implementation continues.



\---



\## 19. Git Architecture



`main` is the stable integration branch.



Feature work should use branches such as:



```text

feature/adwait-ml

feature/mahendra-api

feature/preet-intervention-analytics

feature/diya-architecture

```



Expected workflow:



```text

Feature branch

&#x20;     ↓

Implementation

&#x20;     ↓

Tests

&#x20;     ↓

Commit

&#x20;     ↓

Pull Request

&#x20;     ↓

Architecture / Code Review

&#x20;     ↓

Validation

&#x20;     ↓

Merge into main

```



No untested feature should be merged into the stable branch.



\---



\## 20. Deployment Architecture



Target deployment:



```text

Internet

&#x20;  |

&#x20;  v

Frontend

&#x20;  |

&#x20;  v

FastAPI Backend

&#x20;  |

&#x20;  +-------------------+

&#x20;  |                   |

&#x20;  v                   v

PostgreSQL          ML Artifacts

&#x20;  |

&#x20;  v

Persistent AAROH Data

```



Production configuration must use environment-based secrets.



The deployed system must provide:



\* database connection

\* migrations

\* health endpoint

\* readiness endpoint

\* logging

\* error handling

\* backup strategy

\* restore strategy

\* secure configuration

\* model artifact loading



Training may occur in environments such as Colab, but production inference must not depend on an active Colab session.



\---



\## 21. Current Development Baseline



The current AAROH baseline includes:



```text

PostgreSQL

SQLAlchemy

20 cases

200 interactions

200 distress states

20 predictions

20 consents

20 interventions

Feature extraction

Rule-based risk scoring

Escalation prediction

Intervention engine

Pipeline validation

```



The baseline validation checkpoint is:



```text

AAROH PIPELINE VALIDATION: PASSED

```



This baseline should remain reproducible while new components are developed.



\---



\## 22. End-to-End Demonstration Scenario



A synthetic demonstration case should show the complete lifecycle.



\### Day 1



```text

Moderate distress

↓

Low escalation probability

↓

Routine monitoring

```



\### Day 4



```text

Increased fear

\+ sleep disruption

\+ engagement deterioration

↓

Distress increases

↓

Trend becomes WORSENING

↓

Escalation probability increases

↓

Higher intervention priority

```



\### Day 5



```text

Intervention created

↓

Official/counsellor assigned

↓

Human follow-up / counselling / referral

```



\### Day 8



```text

Follow-up interaction

↓

Outcome recorded

↓

Distress decreases

↓

Trend becomes IMPROVING

↓

Continue monitoring

```



This demonstrates the central value of AAROH:



> \*\*Detect change early, explain the change, connect the risk to a human response, and continue monitoring after the intervention.\*\*



\---



\## 23. Architectural Non-Goals



AAROH will not:



\* fabricate NHAA APIs

\* claim synthetic data proves clinical validity

\* present itself as a diagnostic system

\* allow AI to autonomously make medical/legal/witness-protection decisions

\* train a giant language model from scratch

\* depend on Colab for production inference

\* hard-code credentials

\* commit sensitive victim data

\* overwrite historical predictions

\* expose raw victim narratives through aggregate dashboards

\* treat low-confidence predictions as certainty

\* allow independent uncontrolled modification of shared database contracts



\---



\## 24. Architecture Freeze Principle



The architecture is considered frozen when:



```text

Database boundary      ✓

API boundary            ✓

ML boundary             ✓

Voice boundary          ✓

Intervention boundary   ✓

Consent boundary        ✓

Security boundary      ✓

NHAA adapter boundary   ✓

Ownership boundaries   ✓

```



After architecture freeze, implementation should proceed through these interfaces rather than repeatedly redesigning the overall system.



\---



\## 25. Definition of Architectural Success



AAROH's architecture is successful when all components can operate as one coherent lifecycle:



```text

DATA

&#x20; ↓

API

&#x20; ↓

FEATURES

&#x20; ↓

DISTRESS

&#x20; ↓

ESCALATION

&#x20; ↓

INTERVENTION

&#x20; ↓

HUMAN ACTION

&#x20; ↓

OUTCOME

&#x20; ↓

RE-MONITORING

```



The purpose of the architecture is not to maximize the number of technologies used.



The purpose is to produce a secure, explainable, longitudinal, human-supervised system that can detect deterioration earlier and connect that signal to an appropriate human response.



