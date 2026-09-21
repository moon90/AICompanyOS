"""FastAPI route handlers for Tool Gateway adhering to docs/Phases.md Section 13 and docs/Architecture.md Sections 30-36."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.tool_service import ToolService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.tool import (
    ToolDefinitionResponse,
    ToolExecuteApiRequest,
    ToolExecutionListResponse,
    ToolExecutionResponse,
    ToolListResponse,
)
from domain.runtime.exceptions import AgentInactiveError
from domain.tools.exceptions import (
    ToolAccessDeniedError,
    ToolExecutionFailedError,
    ToolExecutionNotFoundError,
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolValidationError,
)
from domain.tools.schemas import ToolCallRequest
from domain.work.exceptions import TaskNotFoundError
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}/tools", tags=["Tool Gateway"])


@router.get(
    "",
    response_model=ToolListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available tools in the Tool Gateway",
)
async def list_tools(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    role: str | None = Query(None, description="Optional role filter for tool permissions"),
) -> ToolListResponse:
    """Retrieve all authorized tools registered in the gateway."""
    tool_service = ToolService(db=db)
    try:
        tools = await tool_service.list_tools(
            company_id=company_id,
            user_id=current_user.id,
            role=role,
        )
        items = [
            ToolDefinitionResponse(
                name=t.name,
                provider=t.provider,
                description=t.description,
                version=t.version,
                risk_level=t.risk_level.value,
                requires_approval=t.requires_approval,
                allowed_roles=t.allowed_roles,
                input_schema=t.input_schema,
                output_schema=t.output_schema,
            )
            for t in tools
        ]
        return ToolListResponse(items=items, total=len(items))
    except ToolAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/definitions/{tool_name}",
    response_model=ToolDefinitionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed tool definition and parameter schema",
)
async def get_tool(
    company_id: str,
    tool_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ToolDefinitionResponse:
    """Retrieve a single registered tool definition."""
    tool_service = ToolService(db=db)
    try:
        t = await tool_service.get_tool(
            company_id=company_id,
            user_id=current_user.id,
            tool_name=tool_name,
        )
        return ToolDefinitionResponse(
            name=t.name,
            provider=t.provider,
            description=t.description,
            version=t.version,
            risk_level=t.risk_level.value,
            requires_approval=t.requires_approval,
            allowed_roles=t.allowed_roles,
            input_schema=t.input_schema,
            output_schema=t.output_schema,
        )
    except ToolAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ToolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/execute",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a tool through the authoritative 8-step Tool Gateway",
)
async def execute_tool(
    company_id: str,
    request: ToolExecuteApiRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ToolExecutionResponse:
    """Execute a tool invocation for an agent through the secure pipeline and record audit log."""
    tool_service = ToolService(db=db)
    tool_call = ToolCallRequest(
        agent_id=request.agent_id,
        tool_name=request.tool_name,
        action=request.action,
        parameters=request.parameters,
        task_id=request.task_id,
        execution_id=request.execution_id,
    )

    try:
        record = await tool_service.execute_tool(
            company_id=company_id,
            user_id=current_user.id,
            request=tool_call,
        )
        return ToolExecutionResponse.model_validate(record)
    except ToolAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ToolPermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AgentInactiveError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ToolNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ToolValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": str(exc), "details": exc.details},
        ) from exc
    except ToolExecutionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ToolExecutionFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get(
    "/executions",
    response_model=ToolExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tool execution audit logs with filtering",
)
async def list_tool_executions(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    agent_id: str | None = Query(None, description="Filter by calling agent ID"),
    task_id: str | None = Query(None, description="Filter by associated task ID"),
    tool_name: str | None = Query(None, description="Filter by tool name"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by execution status"
    ),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> ToolExecutionListResponse:
    """Retrieve immutable audit records for tool executions in company."""
    tool_service = ToolService(db=db)
    try:
        records, total = await tool_service.list_tool_executions(
            company_id=company_id,
            user_id=current_user.id,
            agent_id=agent_id,
            task_id=task_id,
            tool_name=tool_name,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        return ToolExecutionListResponse(
            items=[ToolExecutionResponse.model_validate(r) for r in records],
            total=total,
        )
    except ToolAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/executions/{execution_id}",
    response_model=ToolExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single tool execution audit record details",
)
async def get_tool_execution(
    company_id: str,
    execution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ToolExecutionResponse:
    """Retrieve details and normalized I/O for a specific tool execution."""
    tool_service = ToolService(db=db)
    try:
        record = await tool_service.get_tool_execution(
            company_id=company_id,
            user_id=current_user.id,
            execution_id=execution_id,
        )
        return ToolExecutionResponse.model_validate(record)
    except ToolAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ToolExecutionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
