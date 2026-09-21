"""Domain exceptions for user management and authentication."""


class UserDomainError(Exception):
    """Base exception for user domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UserAlreadyExistsError(UserDomainError):
    """Raised when registering an email that is already registered."""

    def __init__(self, email: str) -> None:
        super().__init__(f"User with email '{email}' already exists.")
        self.email = email


class InvalidCredentialsError(UserDomainError):
    """Raised when authentication credentials do not match."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class UserInactiveError(UserDomainError):
    """Raised when user account is not active."""

    def __init__(self) -> None:
        super().__init__("User account is inactive.")


class SessionExpiredError(UserDomainError):
    """Raised when an authentication session has expired."""

    def __init__(self) -> None:
        super().__init__("Authentication session has expired.")


class SessionNotFoundError(UserDomainError):
    """Raised when an authentication session does not exist."""

    def __init__(self) -> None:
        super().__init__("Authentication session not found.")


class RateLimitExceededError(UserDomainError):
    """Raised when too many failed login attempts occur."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            f"Too many failed login attempts. Please try again in {retry_after_seconds} seconds."
        )
        self.retry_after_seconds = retry_after_seconds


class PasswordValidationError(UserDomainError):
    """Raised when a password does not meet requirements."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
