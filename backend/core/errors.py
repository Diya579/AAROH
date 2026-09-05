"""
AAROH — Structured error helpers

Provides AaROHError (carries a named error `code`) and shorthand
raise helpers. The global exception handler in main.py reads the
`code` attribute via getattr, so plain HTTPException still works
alongside AaROHError.

Usage:
    raise_not_found("Case", case_id)
    raise_forbidden("VOICE_CONSENT_DENIED", "Voice analysis consent not granted.")
    raise_conflict("CASE_DUPLICATE", "A case with this ID already exists.")
"""

from fastapi import HTTPException, status


class AaROHError(HTTPException):
    """
    HTTPException subclass that carries a named error code.

    The global handler in main.py reads `exc.code` via getattr, so any
    AaROHError will produce a structured { "error": { "code": ..., "message": ... } }
    envelope instead of the generic "HTTP_EXCEPTION" code.
    """

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code


# ---------------------------------------------------------------------------
# Shorthand helpers
# ---------------------------------------------------------------------------

def raise_not_found(entity: str, id) -> None:
    """Raise 404 with a structured NOT_FOUND code."""
    raise AaROHError(
        status_code=status.HTTP_404_NOT_FOUND,
        code=f"{entity.upper()}_NOT_FOUND",
        message=f"{entity} with id {id} not found.",
    )


def raise_forbidden(code: str, message: str) -> None:
    """Raise 403 with a named code."""
    raise AaROHError(
        status_code=status.HTTP_403_FORBIDDEN,
        code=code,
        message=message,
    )


def raise_conflict(code: str, message: str) -> None:
    """Raise 409 with a named code."""
    raise AaROHError(
        status_code=status.HTTP_409_CONFLICT,
        code=code,
        message=message,
    )


def raise_unprocessable(code: str, message: str) -> None:
    """Raise 422 with a named code."""
    raise AaROHError(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code=code,
        message=message,
    )
