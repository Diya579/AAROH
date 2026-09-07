"""
AAROH — Password Hashing (Argon2id)

Uses argon2-cffi with the Argon2id variant (the default).
Never stores or logs plaintext passwords.

Do NOT invent a custom hashing scheme.
"""

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

_ph = PasswordHasher()  # Argon2id by default


def hash_password(plain: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Returns True if the password matches, False otherwise.
    Never raises on mismatch — always returns a boolean.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
