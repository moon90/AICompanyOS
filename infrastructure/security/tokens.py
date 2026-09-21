"""Cryptographically secure token generation and hashing utilities."""

import hashlib
import secrets


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 hash of a raw token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_session_token() -> tuple[str, str]:
    """Generate a high-entropy session token and its SHA-256 hash.

    Returns:
        tuple[str, str]: (raw_token, token_hash)
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash
