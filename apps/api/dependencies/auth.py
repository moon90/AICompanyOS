"""Authentication dependencies for FastAPI route handlers."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.auth_service import AuthService
from domain.users.exceptions import SessionExpiredError, SessionNotFoundError, UserInactiveError
from infrastructure.config import Settings, get_settings
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    request: Request,
) -> AuthService:
    """Dependency provider for AuthService."""
    settings = getattr(request.app.state, "settings", None) or get_settings()
    rate_limiter = getattr(request.app.state, "rate_limiter", None)
    return AuthService(session=session, settings=settings, rate_limiter=rate_limiter)


async def get_current_user(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Extract session token from cookie or Authorization header and return authenticated User."""
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()

    # 1. Check HttpOnly session cookie
    token = request.cookies.get(settings.session_cookie_name)

    # 2. Check Authorization Bearer header fallback
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await auth_service.validate_session(token)
        return user
    except SessionExpiredError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except UserInactiveError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        ) from err
    except SessionNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
