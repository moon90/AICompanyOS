"""FastAPI route handlers for Agent Task Execution adhering to docs/Phases.md Section 12."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.execution_service import ExecutionService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.execution import (
    ExecutionListResponse,
    ExecutionRecordResponse,
    TaskExecuteRequest,
)
from domain.runtime.exceptions import (
    AgentInactiveError,
    ExecutionAccessDeniedError,
    ExecutionError,
    ExecutionTimeoutError,
    InvalidTaskStateForExecutionError,
    MaxStepsExceededError,
    UnassignedTaskError,
)
from domain.runtime.schemas import RuntimeLimits
from domain.work.exceptions import TaskNotFoundError
from infrastructure.database.models import ExecutionRecord, User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}", tags=["Agent Execution"])


def _to_response(rec: ExecutionRecord) -> ExecutionRecordResponse:
    """Safely map ExecutionRecord ORM model to response schema."""
    agent_name = None
    agent_role = None
    if "agent" in rec.__dict__ and rec.agent:
        agent_name = rec.agent.name
        agent_role = rec.agent.role

    executed_by_user_name = None
    if "executed_by_user" in rec.__dict__ and rec.executed_by_user:
        executed_by_user_name = rec.executed_by_user.name

    return ExecutionRecordResponse(
        id=rec.id,
        company_id=rec.company_id,
        task_id=rec.task_id,
        agent_id=rec.agent_id,
        executed_by_user_id=rec.executed_by_user_id,
        status=rec.status,
        step_count=rec.step_count,
        duration_ms=rec.duration_ms,
        tokens_used=rec.tokens_used,
        estimated_cost=rec.estimated_cost,
        result_summary=rec.result_summary,
        deliverable=rec.deliverable,
        steps_json=rec.steps_json or [],
        error_details=rec.error_details,
        created_at=rec.created_at,
        completed_at=rec.completed_at,
        agent_name=agent_name,
        agent_role=agent_role,
        executed_by_user_name=executed_by_user_name,
    )


@router.post(
    "/tasks/{task_id}/execute",
    response_model=ExecutionRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute a task using its assigned specialist agent",
)
async def execute_task(
    company_id: str,
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    request: TaskExecuteRequest | None = None,
) -> ExecutionRecordResponse:
    """Execute a task with its assigned agent and advance to VERIFYING upon deliverable production."""
    execution_service = ExecutionService(db=db)

    limits = RuntimeLimits()
    if request:
        if request.max_steps is not None:
            limits.max_steps = request.max_steps
        if request.max_duration_seconds is not None:
            limits.max_duration_seconds = request.max_duration_seconds
        if request.max_tokens is not None:
            limits.max_tokens = request.max_tokens

    try:
        record = await execution_service.execute_task(
            company_id=company_id,
            task_id=task_id,
            user_id=current_user.id,
            limits=limits,
        )
        return _to_response(record)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExecutionAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (UnassignedTaskError, InvalidTaskStateForExecutionError, AgentInactiveError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ExecutionTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    except MaxStepsExceededError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/tasks/{task_id}/executions",
    response_model=ExecutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all execution runs for a task",
)
async def list_task_executions(
    company_id: str,
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExecutionListResponse:
    """Retrieve the full historical execution audit trail for a task."""
    execution_service = ExecutionService(db=db)
    try:
        records = await execution_service.list_task_executions(
            company_id=company_id,
            task_id=task_id,
            user_id=current_user.id,
        )
        return ExecutionListResponse(
            items=[_to_response(r) for r in records],
            total=len(records),
        )
    except ExecutionAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed execution run by ID",
)
async def get_execution(
    company_id: str,
    execution_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExecutionRecordResponse:
    """Retrieve an individual execution record with full reasoning transcripts."""
    execution_service = ExecutionService(db=db)
    try:
        record = await execution_service.get_execution(
            company_id=company_id,
            execution_id=execution_id,
            user_id=current_user.id,
        )
        return _to_response(record)
    except ExecutionAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
