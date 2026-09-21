from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.main import create_application
from infrastructure.config import Settings
from infrastructure.database.base import Base
from infrastructure.database.session import get_db_session


@pytest.fixture
async def app_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client with in-memory database and overridden dependencies."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    settings = Settings(
        app_name="AI Company OS Test",
        app_env="test",
        session_cookie_name="ai_company_session_test",
        login_rate_limit_attempts=3,
        cookie_secure=False,
    )
    app = create_application(settings=settings)
    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    await engine.dispose()


@pytest.mark.asyncio
async def test_auth_api_complete_lifecycle(app_client: AsyncClient) -> None:
    """Verify complete HTTP registration, login, profile inspection, and logout flow."""
    # 1. Unauthenticated /api/v1/auth/me returns 401
    resp = await app_client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    # 2. Register user
    reg_payload = {
        "name": "Evelyn Owner",
        "email": "evelyn@company.os",
        "password": "strong-password-123",
        "confirm_password": "strong-password-123",
    }
    resp = await app_client.post("/api/v1/auth/register", json=reg_payload)
    assert resp.status_code == 201
    reg_data = resp.json()
    assert reg_data["email"] == "evelyn@company.os"
    assert reg_data["name"] == "Evelyn Owner"
    assert "id" in reg_data

    # 3. Duplicate registration returns 409
    resp = await app_client.post("/api/v1/auth/register", json=reg_payload)
    assert resp.status_code == 409

    # 4. Login with invalid credentials returns 401
    bad_login = {"email": "evelyn@company.os", "password": "wrong-password"}
    resp = await app_client.post("/api/v1/auth/login", json=bad_login)
    assert resp.status_code == 401

    # 5. Login with valid credentials returns 200 and sets cookie
    good_login = {"email": "evelyn@company.os", "password": "strong-password-123"}
    resp = await app_client.post("/api/v1/auth/login", json=good_login)
    assert resp.status_code == 200
    login_data = resp.json()
    assert "token" in login_data
    token = login_data["token"]
    assert "ai_company_session_test" in resp.cookies

    # 6. Authenticated /api/v1/auth/me using cookie returns 200
    resp = await app_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    me_data = resp.json()
    assert me_data["email"] == "evelyn@company.os"

    # 7. Authenticated /api/v1/auth/me using Authorization header returns 200
    resp = await app_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    # 8. Logout revokes session and clears cookie
    resp = await app_client.post("/api/v1/auth/logout")
    assert resp.status_code == 200

    # 9. Access /api/v1/auth/me after logout returns 401
    resp = await app_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_api_rate_limiting(app_client: AsyncClient) -> None:
    """Verify rate limiter triggers HTTP 429 after threshold failures."""
    email = "target@company.os"
    # Register first
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Target",
            "email": email,
            "password": "valid-password-123",
            "confirm_password": "valid-password-123",
        },
    )

    # 3 failed attempts (configured limit is 3)
    for _ in range(3):
        resp = await app_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong"},
        )
        assert resp.status_code == 401

    # 4th attempt should be blocked with 429
    resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong"},
    )
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
