from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.auth_service import AuthService
from domain.users.exceptions import (
    InvalidCredentialsError,
    PasswordValidationError,
    SessionNotFoundError,
    UserAlreadyExistsError,
)
from infrastructure.config import Settings
from infrastructure.database.base import Base


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated in-memory SQLite database session for unit tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_register_and_login_lifecycle(db_session: AsyncSession) -> None:
    """Verify registration, login, session validation, and logout."""
    settings = Settings(session_expire_days=7)
    service = AuthService(session=db_session, settings=settings)

    # 1. Register
    user = await service.register(
        name="Alice Founder",
        email="alice@company.os",
        password="password-12345",
        confirm_password="password-12345",
    )
    assert user.id is not None
    assert user.name == "Alice Founder"
    assert user.email == "alice@company.os"
    assert user.status == "active"

    # 2. Duplicate registration fails
    with pytest.raises(UserAlreadyExistsError):
        await service.register(
            name="Alice Again",
            email="alice@company.os",
            password="password-12345",
            confirm_password="password-12345",
        )

    # 3. Password mismatch fails
    with pytest.raises(PasswordValidationError, match="Passwords do not match"):
        await service.register(
            name="Bob",
            email="bob@company.os",
            password="password-12345",
            confirm_password="different-password",
        )

    # 4. Login with invalid password fails
    with pytest.raises(InvalidCredentialsError):
        await service.login(email="alice@company.os", password="wrong-password")

    # 5. Login with correct password succeeds
    auth_user, token = await service.login(email="alice@company.os", password="password-12345")
    assert auth_user.id == user.id
    assert token is not None

    # 6. Validate session returns user
    validated_user = await service.validate_session(token)
    assert validated_user.id == user.id
    assert validated_user.email == user.email

    # 7. Logout revokes session
    await service.logout(token)
    with pytest.raises(SessionNotFoundError):
        await service.validate_session(token)
