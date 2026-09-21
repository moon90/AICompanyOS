"""Application service for user authentication and session lifecycle management."""

import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.users.exceptions import (
    InvalidCredentialsError,
    PasswordValidationError,
    RateLimitExceededError,
    SessionExpiredError,
    SessionNotFoundError,
    UserAlreadyExistsError,
    UserInactiveError,
)
from infrastructure.config import Settings, get_settings
from infrastructure.database.models import User, UserSession
from infrastructure.security.password import hash_password, verify_password
from infrastructure.security.rate_limiter import LoginRateLimiter
from infrastructure.security.tokens import generate_session_token, hash_token

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthService:
    """Orchestrates registration, authentication, sessions, and credentials verification."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        rate_limiter: LoginRateLimiter | None = None,
    ) -> None:
        self.db = session
        self.settings = settings or get_settings()
        self.rate_limiter = rate_limiter or LoginRateLimiter(
            max_attempts=self.settings.login_rate_limit_attempts,
            window_seconds=self.settings.login_rate_limit_window_seconds,
        )

    async def register(
        self,
        name: str,
        email: str,
        password: str,
        confirm_password: str,
    ) -> User:
        """Register a new user account with validated credentials."""
        cleaned_name = name.strip()
        cleaned_email = email.strip().lower()

        if not cleaned_name:
            raise PasswordValidationError("Name cannot be blank.")

        if not EMAIL_REGEX.match(cleaned_email):
            raise PasswordValidationError("Invalid email address format.")

        if password != confirm_password:
            raise PasswordValidationError("Passwords do not match.")

        if len(password) < 8:
            raise PasswordValidationError("Password must be at least 8 characters long.")

        # Check existing user
        query = select(User).where(User.email == cleaned_email)
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        if existing:
            raise UserAlreadyExistsError(email=cleaned_email)

        password_hash = hash_password(password)
        new_user = User(
            name=cleaned_name,
            email=cleaned_email,
            password_hash=password_hash,
            status="active",
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[User, str]:
        """Authenticate user credentials, enforce rate limits, and issue session token."""
        cleaned_email = email.strip().lower()

        # Check rate limiter
        is_limited, retry_after = self.rate_limiter.is_rate_limited(cleaned_email)
        if is_limited:
            raise RateLimitExceededError(retry_after_seconds=retry_after)

        # Retrieve user
        query = select(User).where(User.email == cleaned_email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            self.rate_limiter.record_failure(cleaned_email)
            raise InvalidCredentialsError()

        if user.status != "active":
            raise UserInactiveError()

        # Reset rate limits upon successful credential verification
        self.rate_limiter.reset(cleaned_email)

        # Generate session
        raw_token, token_hash = generate_session_token()
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=self.settings.session_expire_days)

        user_session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=now,
            last_activity_at=now,
        )
        user.last_login_at = now
        self.db.add(user_session)
        await self.db.commit()

        return user, raw_token

    async def validate_session(self, raw_token: str) -> User:
        """Verify session token against PostgreSQL authority and return active user."""
        if not raw_token:
            raise SessionNotFoundError()

        token_hash = hash_token(raw_token)
        now = datetime.now(UTC)

        query = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(UserSession.token_hash == token_hash)
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise SessionNotFoundError()

        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at <= now:
            await self.db.execute(delete(UserSession).where(UserSession.id == session.id))
            await self.db.commit()
            raise SessionExpiredError()

        if session.user.status != "active":
            raise UserInactiveError()

        session.last_activity_at = now
        await self.db.commit()

        return session.user

    async def logout(self, raw_token: str) -> None:
        """Revoke active session token in PostgreSQL."""
        if not raw_token:
            return
        token_hash = hash_token(raw_token)
        await self.db.execute(delete(UserSession).where(UserSession.token_hash == token_hash))
        await self.db.commit()
