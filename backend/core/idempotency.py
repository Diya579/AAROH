import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, TypeVar, cast
from fastapi import HTTPException, status, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from backend.models import IdempotencyRecord

logger = logging.getLogger(__name__)

T = TypeVar("T")

def generate_request_hash(payload: Any) -> str:
    """Generate a SHA-256 hash of the request payload to detect mismatches."""
    if payload is None:
        return hashlib.sha256(b"").hexdigest()
    
    if isinstance(payload, bytes):
        return hashlib.sha256(payload).hexdigest()
    
    # If it's a Pydantic model, dump to dict
    if isinstance(payload, BaseModel):
        data = payload.model_dump(mode="json")
    elif isinstance(payload, dict):
        data = payload
    else:
        # Fallback for primitive types or lists
        data = payload
        
    serialized = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def execute_idempotent(
    db: Session,
    actor_user_id: str,
    operation: str,
    idempotency_key: Optional[str],
    payload: Any,
    executor: Callable[[], T],
    response_status: int = status.HTTP_200_OK,
    response_obj: Optional[Response] = None,
    ttl_hours: int = 24
) -> T:
    """
    Executes a function idempotently if an idempotency_key is provided.
    
    If the key matches an existing record:
    - If request_hash matches, returns the cached response_body.
    - If request_hash differs, raises 409 Conflict.
    
    If no key is provided, simply executes the function.
    """
    if not idempotency_key:
        return executor()

    req_hash = generate_request_hash(payload)

    # 1. Check for existing record
    existing = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.actor_user_id == actor_user_id,
            IdempotencyRecord.operation == operation,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .first()
    )

    if existing:
        if existing.request_hash != req_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Idempotency key '{idempotency_key}' was previously used with a different payload."
            )
        # Explicitly set the response status from the cached record
        if response_obj is not None:
            response_obj.status_code = existing.response_status
        return cast(T, existing.response_body)

    # 2. Execute the operation
    try:
        result = executor()
    except HTTPException as e:
        # We do not cache client errors or validation errors usually, but for strict 
        # idempotency, some systems do. Diya's spec didn't specify caching errors.
        # We'll let exceptions bubble up without caching.
        raise
    except Exception as e:
        # Unexpected errors bubble up
        raise

    # 3. Cache the result
    resp_body = jsonable_encoder(result)

    expires = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        operation=operation,
        actor_user_id=actor_user_id,
        request_hash=req_hash,
        response_status=response_status,
        response_body=resp_body,
        expires_at=expires
    )
    
    try:
        db.add(record)
        db.commit()
    except IntegrityError:
        # Another request with the same key might have completed simultaneously
        db.rollback()
        # Fetch the one that just got committed
        simultaneous_record = (
            db.query(IdempotencyRecord)
            .filter(
                IdempotencyRecord.actor_user_id == actor_user_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.idempotency_key == idempotency_key,
            )
            .first()
        )
        if simultaneous_record:
            if simultaneous_record.request_hash != req_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Idempotency key '{idempotency_key}' was previously used with a different payload."
                )
            if response_obj is not None:
                response_obj.status_code = simultaneous_record.response_status
            return cast(T, simultaneous_record.response_body)
        else:
            # Should not happen, but safe fallback
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Idempotency record conflict could not be resolved."
            )

    # Since result could be a raw dict now (or the original model), 
    # we return the original model so it passes Pydantic validations gracefully.
    return result
