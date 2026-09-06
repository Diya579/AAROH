# AaROH API Contract & Conventions

This document outlines the standard conventions, URL structures, and request patterns used across the AaROH backend API to ensure consistency and predictability.

## 1. Routing Conventions: Flat vs. Nested

AaROH uses **Flat Routing** for almost all domain entities. Instead of deeply nested resource URLs, relationships are specified within the JSON payload.

### Why Flat Routing?
Nested routes (e.g., `/api/v1/cases/{case_id}/events/{event_id}`) become difficult to manage, test, and secure when resources need to be queried independently of their parent. By keeping routes flat, we decouple the endpoint structure from the database hierarchy.

### 1.1 Standard Flat Routes
Resources that have their own distinct identity and primary key follow standard flat REST patterns:

- `POST /api/v1/events` (with `{"case_id": "...", ...}` in body)
- `GET /api/v1/events/{event_id}`
- `GET /api/v1/events?case_id={case_id}`
- `POST /api/v1/interactions` (with `{"case_id": "...", ...}` in body)
- `POST /api/v1/interventions` (with `{"case_id": "...", ...}` in body)

### 1.2 Case-Scoped (Nested) Routes
We only use nested or path-parameter scoped routes when the entity is strictly a 1:1 extension of the parent and has no meaningful independent lifecycle, or when performing a specific sub-action on a resource.

**Upserts (1:1 Relationships):**
- `PUT /api/v1/consents/{case_id}`
- `GET /api/v1/consents/{case_id}`
*(Consent is a 1:1 extension of a Case. You do not create a consent independently of a case, and it does not have an exposed auto-incrementing ID of its own).*

**Sub-actions:**
- `POST /api/v1/interactions/{interaction_id}/voice`
*(Uploading a voice file is an action performed against an existing interaction, not a new REST resource).*

## 2. Error Handling Standardization

All endpoints must return structured JSON errors using the `AaROHError` envelope to allow frontends to predictably parse failures.

### Standard Format
```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable description.",
    "request_id": "uuid-v4-string"
  }
}
```

### Raising Errors (Python)
Do not use raw `raise HTTPException(...)`. Instead, use the helpers from `backend.core.errors`:

- `raise_not_found(entity="Interaction", id=1)` -> `404 Not Found` with code `INTERACTION_NOT_FOUND`
- `raise_unprocessable(code="DB_ERROR", message="...")` -> `422 Unprocessable Entity`
- `raise_forbidden(code="VOICE_CONSENT_DENIED", message="...")` -> `403 Forbidden`
- `raise_conflict(code="CASE_DUPLICATE", message="...")` -> `409 Conflict`

## 3. Idempotency

Mutating endpoints (e.g., `POST /cases`, `POST /interactions`) must support idempotency to prevent duplicate records during network retries.

Clients may send an `Idempotency-Key` header (UUIDv4). If sent, the `execute_idempotent` wrapper ensures that the operation and the idempotency record are committed atomically in the same database transaction.

## 4. RBAC and Scope Isolation

Every endpoint is secured by two layers of authorization:

1. **Role-Based Access Control (RBAC):** Managed via `require_role(...)` in the router `Depends`. This ensures only valid roles (e.g., `ADMIN`, `COUNSELLOR`) can invoke the endpoint.
2. **Scope Isolation (Defense in Depth):** Managed via `verify_case_id_access(case_id, user, db)` inside the endpoint body. This ensures that even if a `COUNSELLOR` can create events, they can only create events for cases *assigned to them*. For officials, it ensures they only access cases within their *jurisdiction* (State/District).
