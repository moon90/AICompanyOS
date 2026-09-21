"""API route handlers for Agent Registry, organizational hierarchy, and definitions."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.agent_service import AgentService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.agent import (
    AgentCreateRequest,
    AgentDefinitionCreateRequest,
    AgentDefinitionResponse,
    AgentDetailResponse,
    AgentResponse,
    AgentUpdateRequest,
    DepartmentSummary,
    ManagerSummary,
    SubordinateSummary,
)
from domain.agents.exceptions import (
    AgentAccessDeniedError,
    AgentNotFoundError,
    DuplicateAgentVersionError,
    InvalidAgentDataError,
    InvalidAgentDepartmentError,
    InvalidAgentHierarchyError,
)
from infrastructure.database.models import Agent, AgentDefinition, User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}/agents", tags=["agents"])


def get_agent_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentService:
    """Dependency provider for AgentService."""
    return AgentService(session=session)


def _format_definition(d: AgentDefinition) -> AgentDefinitionResponse:
    return AgentDefinitionResponse(
        id=d.id,
        agent_id=d.agent_id,
        version=d.version,
        system_prompt=d.system_prompt,
        model=d.model,
        capabilities=d.capabilities or [],
        tools=d.tools or [],
        configuration=d.configuration or {},
        is_current=d.is_current,
        created_at=d.created_at,
    )


def _format_agent(agent: Agent) -> AgentResponse:
    dept_summary = None
    if agent.department:
        dept_summary = DepartmentSummary(
            id=agent.department.id,
            name=agent.department.name,
            code=agent.department.code,
        )

    mgr_summary = None
    if agent.manager:
        mgr_summary = ManagerSummary(
            id=agent.manager.id,
            name=agent.manager.name,
            role=agent.manager.role,
        )

    curr_def = None
    if agent.definitions:
        for d in agent.definitions:
            if d.is_current:
                curr_def = _format_definition(d)
                break
        if not curr_def and len(agent.definitions) > 0:
            curr_def = _format_definition(agent.definitions[0])

    return AgentResponse(
        id=agent.id,
        company_id=agent.company_id,
        department_id=agent.department_id,
        department=dept_summary,
        name=agent.name,
        role=agent.role,
        type=agent.type,
        reports_to=agent.reports_to,
        manager=mgr_summary,
        mission=agent.mission,
        status=agent.status,
        authority_level=agent.authority_level,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        current_definition=curr_def,
    )


def _format_agent_detail(agent: Agent) -> AgentDetailResponse:
    base = _format_agent(agent)
    all_defs = [_format_definition(d) for d in (agent.definitions or [])]
    subordinates = [
        SubordinateSummary(
            id=s.id,
            name=s.name,
            role=s.role,
            status=s.status,
        )
        for s in (agent.subordinates or [])
    ]
    return AgentDetailResponse(
        **base.model_dump(),
        definitions=all_defs,
        subordinates=subordinates,
    )


@router.get(
    "",
    response_model=list[AgentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Agents",
    description="List all agents registered in the company with current definitions and hierarchy references.",
)
async def list_agents(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(get_agent_service)],
    department_id: Annotated[str | None, Query(description="Filter by department UUID")] = None,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status (active/inactive/archived)")
    ] = None,
) -> list[AgentResponse]:
    """Retrieve agents registered to company."""
    try:
        agents = await service.get_company_agents(
            company_id=company_id,
            user_id=current_user.id,
            department_id=department_id,
            status=status_filter,
        )
        return [_format_agent(a) for a in agents]
    except AgentAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Agent",
    description="Register a new agent in the company registry with an initial definition (v1.0).",
)
async def register_agent(
    company_id: str,
    request: AgentCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentResponse:
    """Register a new agent in the company."""
    try:
        agent = await service.create_agent(
            company_id=company_id,
            user_id=current_user.id,
            name=request.name,
            role=request.role,
            type=request.type,
            department_id=request.department_id,
            reports_to=request.reports_to,
            mission=request.mission,
            authority_level=request.authority_level,
            system_prompt=request.system_prompt,
            model=request.model,
            capabilities=request.capabilities,
            tools=request.tools,
            configuration=request.configuration,
        )
        return _format_agent(agent)
    except AgentAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except (InvalidAgentDataError, InvalidAgentDepartmentError, InvalidAgentHierarchyError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.post(
    "/provision-defaults",
    response_model=list[AgentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Provision Default Organization Agents",
    description="Provision the foundational 11 initial company agents (CEO, CTO, CMO, Sales Director, specialists).",
)
async def provision_default_agents(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> list[AgentResponse]:
    """Provision foundational company agents."""
    try:
        agents = await service.provision_default_agents(
            company_id=company_id,
            user_id=current_user.id,
        )
        return [_format_agent(a) for a in agents]
    except AgentAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get(
    "/{agent_id}",
    response_model=AgentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Agent Detail",
    description="Retrieve agent details, reporting subordinates, and definition version history.",
)
async def get_agent(
    company_id: str,
    agent_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentDetailResponse:
    """Retrieve detailed agent profile."""
    try:
        agent = await service.get_agent(
            company_id=company_id,
            agent_id=agent_id,
            user_id=current_user.id,
        )
        return _format_agent_detail(agent)
    except AgentAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Agent",
    description="Update an agent's organizational metadata, role, or reporting hierarchy.",
)
async def update_agent(
    company_id: str,
    agent_id: str,
    request: AgentUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentResponse:
    """Update agent details."""
    try:
        # Check unset vs explicitly null
        payload = request.model_dump(exclude_unset=True)
        update_kwargs: dict[str, Any] = {}
        for k in ("name", "role", "type", "mission", "status", "authority_level"):
            if k in payload:
                update_kwargs[k] = payload[k]

        if "department_id" in payload:
            update_kwargs["department_id"] = payload["department_id"]
        if "reports_to" in payload:
            update_kwargs["reports_to"] = payload["reports_to"]

        agent = await service.update_agent(
            company_id=company_id,
            agent_id=agent_id,
            user_id=current_user.id,
            **update_kwargs,
        )
        return _format_agent(agent)
    except AgentAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (InvalidAgentDataError, InvalidAgentDepartmentError, InvalidAgentHierarchyError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.post(
    "/{agent_id}/definitions",
    response_model=AgentDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Agent Definition Version",
    description="Create a new versioned definition for the agent, preserving prior versions.",
)
async def create_agent_definition(
    company_id: str,
    agent_id: str,
    request: AgentDefinitionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentDefinitionResponse:
    """Create a new versioned agent definition."""
    try:
        new_def = await service.create_agent_definition(
            company_id=company_id,
            agent_id=agent_id,
            user_id=current_user.id,
            version=request.version,
            system_prompt=request.system_prompt,
            model=request.model,
            capabilities=request.capabilities,
            tools=request.tools,
            configuration=request.configuration,
        )
        return _format_definition(new_def)
    except AgentAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DuplicateAgentVersionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except InvalidAgentDataError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.get(
    "/{agent_id}/definitions",
    response_model=list[AgentDefinitionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Agent Definitions",
    description="Retrieve all definition versions for an agent ordered from newest to oldest.",
)
async def list_agent_definitions(
    company_id: str,
    agent_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AgentService, Depends(get_agent_service)],
) -> list[AgentDefinitionResponse]:
    """List historical and current definitions for an agent."""
    try:
        defs = await service.get_agent_definitions(
            company_id=company_id,
            agent_id=agent_id,
            user_id=current_user.id,
        )
        return [_format_definition(d) for d in defs]
    except AgentAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except AgentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
