"""Authentication route handlers adhering to thin-controller principles."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from application.services.auth_service import AuthService
from apps.api.dependencies.auth import get_auth_service, get_current_user
from apps.api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)
from domain.users.exceptions import (
    InvalidCredentialsError,
    PasswordValidationError,
    RateLimitExceededError,
    UserAlreadyExistsError,
    UserInactiveError,
)
from infrastructure.config import Settings, get_settings
from infrastructure.database.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account with validated credentials.",
)
async def register(
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Register a new user account."""
    try:
        user = await service.register(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            confirm_password=payload.confirm_password,
        )
        return UserResponse.model_validate(user)
    except UserAlreadyExistsError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=err.message,
        ) from err
    except PasswordValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err.message,
        ) from err


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and obtain session",
    description="Validates credentials, generates session token, and sets secure HttpOnly cookie.",
)
async def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    """Authenticate user credentials and issue session."""
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()

    try:
        user, raw_token = await service.login(
            email=payload.email,
            password=payload.password,
        )

        # Set secure HttpOnly session cookie
        max_age_seconds = settings.session_expire_days * 86400
        response.set_cookie(
            key=settings.session_cookie_name,
            value=raw_token,
            max_age=max_age_seconds,
            expires=max_age_seconds,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/",
        )

        return AuthResponse(
            user=UserResponse.model_validate(user),
            token=raw_token,
            token_type="bearer",
        )
    except RateLimitExceededError as err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=err.message,
            headers={"Retry-After": str(err.retry_after_seconds)},
        ) from err
    except InvalidCredentialsError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err.message,
        ) from err
    except UserInactiveError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.message,
        ) from err


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke active session",
    description="Revokes current session in PostgreSQL and clears HttpOnly session cookie.",
)
async def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    """Revoke session and clear session cookie."""
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()

    # Extract token if present
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if token:
        await service.logout(token)

    # Clear cookie
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )

    return MessageResponse(message="Successfully logged out.")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Returns profile of user associated with active session.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return authenticated user profile."""
    return UserResponse.model_validate(current_user)
