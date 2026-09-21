"""Unit tests for password hashing, token generation, and rate limiting."""

import pytest

from infrastructure.security.password import hash_password, verify_password
from infrastructure.security.rate_limiter import LoginRateLimiter
from infrastructure.security.tokens import generate_session_token, hash_token


def test_password_hashing_and_verification() -> None:
    """Verify bcrypt hashes plaintext and verifies correctly."""
    plaintext = "super-secret-password-123"
    hashed = hash_password(plaintext)

    assert hashed != plaintext
    assert hashed.startswith("$2b$")
    assert verify_password(plaintext, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_empty_password_fails() -> None:
    """Verify empty password is not accepted for hashing."""
    with pytest.raises(ValueError, match="Password cannot be empty"):
        hash_password("")


def test_token_generation_and_hashing() -> None:
    """Verify session tokens are random and SHA-256 hashed deterministically."""
    token1, hash1 = generate_session_token()
    token2, hash2 = generate_session_token()

    assert token1 != token2
    assert hash1 != hash2
    assert len(hash1) == 64
    assert hash_token(token1) == hash1


def test_rate_limiter_behavior() -> None:
    """Verify sliding-window rate limiter trips after max attempts and can be reset."""
    limiter = LoginRateLimiter(max_attempts=3, window_seconds=60)
    key = "user@example.com"

    # Initially not limited
    is_limited, _ = limiter.is_rate_limited(key)
    assert is_limited is False

    # Record 2 failures
    limiter.record_failure(key)
    limiter.record_failure(key)
    is_limited, _ = limiter.is_rate_limited(key)
    assert is_limited is False

    # 3rd failure reaches threshold
    limiter.record_failure(key)
    is_limited, retry_after = limiter.is_rate_limited(key)
    assert is_limited is True
    assert retry_after > 0

    # Reset upon success
    limiter.reset(key)
    is_limited, _ = limiter.is_rate_limited(key)
    assert is_limited is False
