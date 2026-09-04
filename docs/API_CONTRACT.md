# AAROH — FastAPI API Contract

## 1. Purpose

This document defines the application-layer API contract for AAROH.

FastAPI is the controlled application boundary between:

* frontend clients
* authenticated users
* voice processing
* ML inference
* intervention services
* PostgreSQL
* future authorised external integrations

The API must provide secure, validated and role-aware access to AAROH functionality.

---

# 2. Base URL

All application APIs use:

```text
/api/v1
```

Example:

```text
/api/v1/cases
```

Versioning allows future API evolution without unexpectedly breaking existing clients.

---

# 3. Architecture Boundary

The required architecture is:

```text
Frontend
    ↓
FastAPI
    ↓
Authentication
    ↓
Authorization
    ↓
Pydantic Validation
    ↓
Service Layer
    ↓
Repository / SQLAlchemy
    ↓
PostgreSQL
```

For AI/voice processing:

```text
FastAPI
   ↓
Service Layer
   ├── Voice Service
   ├── ML Service
   └── Intervention Service
```

The frontend must never directly access PostgreSQL.

The frontend must never directly access internal ML or voice infrastructure.

---

# 4. Authentication

Authentication identifies the caller.

Initial application roles:

```text
USER / VICTIM
COUNSELLOR
DISTRICT_OFFICIAL
STATE_OFFICIAL
NATIONAL_OFFICIAL
ADMIN
SYSTEM_SERVICE
```

There is no public registration endpoint.

A user's role must be obtained from the authenticated backend identity.

The client must never be trusted to select its own role.

---

# 5. Authorization

Authorization determines whether an authenticated identity may perform an action.

Authorization must consider:

```text
Identity
+
Role
+
Geographic scope
+
Assignment scope
+
Permission
+
Resource
+
Consent
+
Field-level access
```

Examples:

```text
Victim → own authorised information
Counsellor → assigned/authorised cases
District Official → authorised district scope
State Official → authorised state scope
National Official → authorised national scope
Admin → authorised administrative functions
System Service → machine-to-machine permissions
```

Frontend route guards are only a UX mechanism.

Backend authorization is the actual security boundary.

---

# 6. Authentication Endpoints

Conceptual endpoints:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

### Login

Authenticates an authorised user.

The client does not submit a role selection.

### Me

Returns the authenticated user's permitted identity and role information.

### Logout

Invalidates the authenticated session.

Authentication implementation must follow the separate security contract.

---

# 7. Health

```text
GET /api/v1/health
```

Purpose:

> Confirm that the FastAPI application process is running.

Expected:

```json
{
  "status": "ok"
}
```

This endpoint does not need to query PostgreSQL.

---

# 8. Readiness

```text
GET /api/v1/ready
```

Purpose:

> Confirm that required application dependencies are available.

For the initial deployment, PostgreSQL is a required dependency.

A successful response:

```json
{
  "status": "ready"
}
```

If a required dependency is unavailable:

```text
503 Service Unavailable
```

Do not expose database errors.

---

# 9. Case APIs

Conceptual endpoints:

```text
GET   /api/v1/cases
GET   /api/v1/cases/{case_id}
POST  /api/v1/cases
PATCH /api/v1/cases/{case_id}
GET   /api/v1/cases/{case_id}/timeline
```

The API must enforce role and scope restrictions.

Supported filtering may include:

* case ID
* district
* state
* risk level
* priority
* case stage
* intervention status
* assigned official
* SLA status
* date range

Only authorised filters may be used.

---

# 10. Case Response Rules

Do not automatically expose the entire database `Case` object.

Responses must use explicit API schemas.

This prevents accidental exposure of:

* internal fields
* sensitive metadata
* fields belonging to another role
* future database columns

The API response should contain only fields appropriate to the endpoint and caller.

---

# 11. Interaction APIs

Conceptual endpoints:

```text
POST /api/v1/cases/{case_id}/interactions
GET  /api/v1/cases/{case_id}/interactions
```

Interactions may contain:

* channel
* language
* text response
* completion status
* safety response
* authorised behavioural information
* data-quality information

Sensitive text must only be returned to roles with permission to access it.

---

# 12. Voice Endpoint

For the initial live-capture architecture:

```text
POST /api/v1/interactions/{interaction_id}/voice
```

The frontend records audio and submits the captured recording after the user stops recording.

This is:

```text
Record → Stop → Submit → Process
```

not continuous streaming.

The API is responsible for:

* authentication
* authorization
* consent verification
* request validation
* size/type validation
* safe ingestion
* processing orchestration
* status response

The API is **not responsible for ASR**.

ASR belongs to the voice service.

---

# 13. Voice Processing Status

Initial statuses:

```text
RECEIVED
PROCESSING
COMPLETED
FAILED
RETRY_REQUIRED
```

Example processing flow:

```text
RECEIVED
   ↓
PROCESSING
   ↓
COMPLETED
```

Failure:

```text
PROCESSING
   ↓
FAILED / RETRY_REQUIRED
```

The API must never report successful processing if the voice service failed.

---

# 14. Consent APIs

Conceptual endpoints:

```text
GET   /api/v1/cases/{case_id}/consent
PATCH /api/v1/cases/{case_id}/consent
```

Supported consent information:

```text
monitoring_consent
text_analysis_consent
voice_analysis_consent
case_linkage_consent
safe_channel
safe_time
```

Consent changes must be audited.

Withdrawal must affect future processing according to the security/privacy contract.

---

# 15. Prediction APIs

Conceptual endpoints:

```text
GET /api/v1/cases/{case_id}/prediction
GET /api/v1/cases/{case_id}/predictions
```

Prediction responses may contain:

* distress score
* trajectory
* distress confidence
* baseline deviation
* escalation probability
* prediction horizon
* prediction confidence
* risk level
* explanation
* model name
* model version

The API validates ML output.

The API does not calculate ML output.

---

# 16. Intervention APIs

Conceptual endpoints:

```text
GET   /api/v1/cases/{case_id}/interventions
POST  /api/v1/cases/{case_id}/interventions
GET   /api/v1/interventions/{intervention_id}
PATCH /api/v1/interventions/{intervention_id}
POST  /api/v1/interventions/{intervention_id}/assign
```

Intervention creation and status transitions must follow the intervention contract.

The API must not invent intervention recommendations.

AI recommendations and human actions must remain distinguishable.

---

# 17. Outcome APIs

Conceptual endpoint:

```text
POST /api/v1/interventions/{intervention_id}/outcome
```

Outcome information may include:

* outcome type
* completion status
* recorded time
* authorised notes
* follow-up requirement

Outcome records must be associated with the appropriate intervention/case.

---

# 18. Analytics APIs

Conceptual endpoints:

```text
GET /api/v1/analytics/cases/{case_id}
GET /api/v1/analytics/districts/{district}
GET /api/v1/analytics/states/{state}
GET /api/v1/analytics/national
```

Analytics must return aggregated information appropriate to the user's scope.

Examples:

* case volume
* risk distribution
* distress trends
* escalation trends
* intervention performance
* response times
* outcome statistics
* monitoring coverage

Aggregate endpoints must not unnecessarily expose raw victim narratives.

---

# 19. Notifications

Conceptual endpoint:

```text
GET /api/v1/notifications
```

Notifications must be role- and permission-aware.

Examples:

```text
High-priority case
Escalation alert
Intervention assigned
Intervention overdue
Follow-up required
Outcome update
System notification
```

A user must not receive internal notifications outside their authorized scope.

---

# 20. Pagination

Large list endpoints must support pagination.

Example conceptual parameters:

```text
?page=1&page_size=20
```

The API must enforce sensible limits on page size.

Do not allow unlimited database queries through public endpoints.

---

# 21. Standard Error Envelope

API errors should follow a consistent structure:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Requested resource was not found.",
    "request_id": "req_123"
  }
}
```

Error responses must not expose:

* stack traces
* SQL statements
* database connection strings
* passwords
* API keys
* internal file paths
* raw victim information

---

# 22. HTTP Status Expectations

Use standard HTTP semantics.

Examples:

```text
200 OK
201 Created
202 Accepted
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Validation Error
429 Too Many Requests
500 Internal Server Error
503 Service Unavailable
```

Asynchronous voice/ML processing may return:

```text
202 Accepted
```

when processing has been accepted but is not yet complete.

---

# 23. Request IDs / Correlation IDs

Requests should have a traceable request/correlation ID.

This allows:

```text
Frontend request
      ↓
FastAPI
      ↓
Voice / ML / Intervention
      ↓
Database
```

to be correlated during debugging and monitoring.

Do not put sensitive victim content into correlation IDs.

---

# 24. Idempotency

Operations that may be retried must be designed to avoid accidental duplication.

This particularly applies to:

* voice processing
* prediction generation
* intervention creation
* intervention assignment
* outcome creation

For example, retrying a network request must not accidentally create duplicate interventions.

---

# 25. Consent Enforcement

Consent is a backend processing gate.

The frontend cannot override consent.

Examples:

```text
voice_analysis_consent = false
        ↓
voice processing denied
```

```text
text_analysis_consent = false
        ↓
text analysis denied
```

The exact processing behaviour must follow the consent contract.

---

# 26. Field-Level Data Protection

The API must return role-appropriate schemas.

Do not use:

```text
Return entire database object
       ↓
Hide fields in React
```

Instead:

```text
Database
   ↓
Service
   ↓
Role-aware API schema
   ↓
Authorised response
```

This reduces accidental data exposure.

---

# 27. Service Layer

Endpoints should remain thin.

Preferred architecture:

```text
Router
   ↓
Schema validation
   ↓
Service
   ↓
Repository / SQLAlchemy
```

Business logic should not be duplicated across endpoints.

---

# 28. Database Boundary

FastAPI may use SQLAlchemy to access PostgreSQL.

No client may:

* submit raw SQL
* access PostgreSQL directly
* access database credentials
* bypass API authorization

PostgreSQL remains an internal service.

---

# 29. ML Boundary

The API communicates with ML through a defined service/interface.

```text
FastAPI
   ↓
ML service/interface
   ↓
ML inference
   ↓
Validated ML response
   ↓
FastAPI
   ↓
PostgreSQL
```

FastAPI must validate ML output before persistence.

ML must not directly modify application database records.

---

# 30. Voice Boundary

The API communicates with the voice pipeline through a defined service/interface.

```text
Frontend
   ↓
FastAPI
   ↓
Voice service
   ↓
Audio validation
   ↓
Preprocessing
   ↓
ASR
   ↓
Voice features + transcription
   ↓
ML
```

FastAPI does not perform ASR itself.

---

# 31. NHAA Integration Boundary

NHAA integration must remain replaceable.

Use an adapter concept:

```text
AAROH
   ↓
NHAA Adapter
   ↓
Demo implementation / future authorized integration
```

The API must not:

* claim access to undocumented NHAA APIs
* reverse engineer private interfaces
* hard-code government credentials
* expose fake government data as real

Any future NHAA integration must use an authorized interface.

---

# 32. Security Requirements

The API must implement:

* authentication
* authorization
* role/scope checks
* consent checks
* request validation
* response filtering
* rate limiting where appropriate
* secure CORS
* secure sessions
* CSRF protection where cookie authentication requires it
* safe error handling
* request tracing
* secure audio handling
* upload limits
* dependency/security scanning

Secrets must never be committed.

---

# 33. Audit Events

Sensitive operations should produce audit events where authorised.

Initial event types:

```text
LOGIN
LOGIN_FAILURE
CASE_VIEW
CASE_UPDATE
CONSENT_CHANGE
VOICE_PROCESS
PREDICTION_GENERATE
INTERVENTION_CREATE
INTERVENTION_ASSIGN
OUTCOME_CREATE
ADMIN_ACTION
```

Audit records should contain:

* actor
* action
* timestamp
* resource
* relevant request/correlation ID

Audit records must not contain unnecessary sensitive narratives, raw audio or credentials.

---

# 34. Privacy Rules

The API must minimise exposure of sensitive information.

Never log:

* passwords
* session tokens
* API keys
* database credentials
* raw audio
* raw victim narratives
* unnecessary transcripts

Sensitive information must not be unnecessarily placed in:

* URLs
* query parameters
* browser logs
* application logs
* analytics aggregates

---

# 35. API Documentation

FastAPI OpenAPI documentation should remain available during development.

Expected:

```text
/docs
```

The OpenAPI specification must reflect the actual API contract.

Documentation must not claim endpoints that do not exist in the implementation.

---

# 36. API Contract Change Rule

Shared API changes follow:

```text
Proposal
   ↓
Impact assessment
   ↓
Team agreement
   ↓
Update API contract
   ↓
Update backend implementation
   ↓
Update dependent services/frontend
   ↓
Integration tests
```

No developer should silently rename/remove/change shared fields or endpoints.

---

# 37. Non-Goals

FastAPI must NOT:

* train ML models
* perform ASR
* independently calculate distress
* independently calculate escalation probability
* autonomously make medical decisions
* autonomously make legal decisions
* autonomously decide witness protection
* directly expose PostgreSQL
* bypass RBAC
* bypass consent
* fabricate AI results
* claim undocumented NHAA integration

---

# 38. Core AAROH Flow

The API must ultimately support:

```text
User
 ↓
Authentication
 ↓
Authorization
 ↓
Case
 ↓
Interaction
 ↓
Voice/Text Processing
 ↓
Feature Extraction
 ↓
ML Inference
 ↓
Distress + Risk
 ↓
Intervention
 ↓
Human Action
 ↓
Outcome
 ↓
Re-monitoring
```

FastAPI is the controlled orchestration boundary connecting these components.
