"""Password hashing and verification utilities using bcrypt."""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False
