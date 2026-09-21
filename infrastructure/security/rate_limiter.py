"""In-memory rate limiter for login failure protection."""

import threading
from datetime import UTC, datetime


class LoginRateLimiter:
    """Sliding-window in-memory rate limiter to protect against brute-force attacks."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _cleanup_old_attempts(self, key: str, now: float) -> list[float]:
        threshold = now - self.window_seconds
        attempts = [ts for ts in self._attempts.get(key, []) if ts > threshold]
        if attempts:
            self._attempts[key] = attempts
        else:
            self._attempts.pop(key, None)
        return attempts

    def is_rate_limited(self, key: str) -> tuple[bool, int]:
        """Check if key has exceeded failed attempts.

        Returns:
            tuple[bool, int]: (is_limited, retry_after_seconds)
        """
        now = datetime.now(UTC).timestamp()
        with self._lock:
            attempts = self._cleanup_old_attempts(key, now)
            if len(attempts) >= self.max_attempts:
                oldest_in_window = attempts[0]
                retry_after = max(1, int(oldest_in_window + self.window_seconds - now))
                return True, retry_after
            return False, 0

    def record_failure(self, key: str) -> None:
        """Record a failed authentication attempt."""
        now = datetime.now(UTC).timestamp()
        with self._lock:
            attempts = self._cleanup_old_attempts(key, now)
            attempts.append(now)
            self._attempts[key] = attempts

    def reset(self, key: str) -> None:
        """Reset failed attempts for a key upon successful authentication."""
        with self._lock:
            self._attempts.pop(key, None)


login_rate_limiter = LoginRateLimiter()
