from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    code: str = Field(..., description="A constant string code representing the error type (e.g. 'VALIDATION_ERROR', 'CASE_NOT_FOUND').")
    message: str = Field(..., description="A human-readable error message.")
    request_id: str = Field(..., description="The unique correlation ID for this request, matching the X-Request-ID header.")

class ErrorEnvelope(BaseModel):
    error: ErrorDetail = Field(..., description="The error details envelope.")

# Shared OpenAPI responses dictionary to be injected into all routers
common_responses = {
    400: {"description": "Bad Request", "model": ErrorEnvelope},
    401: {"description": "Unauthorized - Missing or invalid credentials", "model": ErrorEnvelope},
    403: {"description": "Forbidden - Insufficient permissions or out of scope", "model": ErrorEnvelope},
    404: {"description": "Not Found - Resource does not exist", "model": ErrorEnvelope},
    409: {"description": "Conflict - Resource already exists or state conflict", "model": ErrorEnvelope},
    422: {"description": "Unprocessable Entity - Validation failed", "model": ErrorEnvelope},
    500: {"description": "Internal Server Error", "model": ErrorEnvelope},
}
