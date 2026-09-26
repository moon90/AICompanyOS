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


class ApiRateLimiter:
    """General sliding-window rate limiter for API requests and agent calls."""

    def __init__(self, default_limit: int = 120, window_seconds: int = 60) -> None:
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _cleanup_old_requests(self, key: str, now: float) -> list[float]:
        threshold = now - self.window_seconds
        reqs = [ts for ts in self._requests.get(key, []) if ts > threshold]
        if reqs:
            self._requests[key] = reqs
        else:
            self._requests.pop(key, None)
        return reqs

    def check_and_record(self, key: str, limit: int | None = None) -> tuple[bool, int]:
        """Check if request is allowed, and record it if allowed.

        Returns:
            tuple[bool, int]: (is_allowed, remaining_requests)
        """
        max_limit = limit or self.default_limit
        now = datetime.now(UTC).timestamp()
        with self._lock:
            reqs = self._cleanup_old_requests(key, now)
            if len(reqs) >= max_limit:
                return False, 0
            reqs.append(now)
            self._requests[key] = reqs
            remaining = max(0, max_limit - len(reqs))
            return True, remaining

    def reset(self, key: str | None = None) -> None:
        """Reset rate limiter counts."""
        with self._lock:
            if key is not None:
                self._requests.pop(key, None)
            else:
                self._requests.clear()


api_rate_limiter = ApiRateLimiter()
