"""FastAPI Application Entrypoint for AI Company OS."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routes.activity import router as activity_router
from apps.api.routes.agent import router as agent_router
from apps.api.routes.approval import router as approval_router
from apps.api.routes.auth import router as auth_router
from apps.api.routes.ceo import router as ceo_router
from apps.api.routes.company import router as company_router
from apps.api.routes.delegation import router as delegation_router
from apps.api.routes.engineering import router as engineering_router
from apps.api.routes.errors import router as errors_router
from apps.api.routes.execution import router as execution_router
from apps.api.routes.health import router as health_router
from apps.api.routes.memory import router as memory_router
from apps.api.routes.presence import router as presence_router
from apps.api.routes.project import router as project_router
from apps.api.routes.realtime import router as realtime_router
from apps.api.routes.system import router as system_router
from apps.api.routes.task import router as task_router
from apps.api.routes.tool import router as tool_router
from infrastructure.config import Settings, get_settings
from infrastructure.security.rate_limiter import LoginRateLimiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    # Startup logic
    yield
    # Shutdown logic


def create_application(settings: Settings | None = None) -> FastAPI:
    """FastAPI application factory."""
    app_settings = settings or get_settings()

    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        debug=app_settings.debug,
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    application.state.rate_limiter = LoginRateLimiter(
        max_attempts=app_settings.login_rate_limit_attempts,
        window_seconds=app_settings.login_rate_limit_window_seconds,
    )

    # CORS configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(system_router)
    application.include_router(company_router)
    application.include_router(agent_router)
    application.include_router(ceo_router)
    application.include_router(project_router)
    application.include_router(task_router)
    application.include_router(delegation_router)
    application.include_router(execution_router)
    application.include_router(tool_router)
    application.include_router(approval_router)
    application.include_router(memory_router)
    application.include_router(activity_router)
    application.include_router(presence_router)
    application.include_router(errors_router)
    application.include_router(engineering_router)
    application.include_router(realtime_router)

    return application


app = create_application()
