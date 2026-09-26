"""FastAPI route handlers for Security Hardening, Default-DENY policies, and audit logging."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.security_service import SecurityService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.security import (
    AgentPolicyResponse,
    AgentPolicyUpdateRequest,
    AgentQuarantineRequest,
    PromptScanRequest,
    PromptScanResponse,
    SecurityLogCreateRequest,
    SecurityLogItem,
    SecurityLogListResponse,
    SecuritySummaryResponse,
)
from domain.security.enums import ActorType, SecurityEventType, SecuritySeverity
from domain.security.exceptions import (
    CrossTenantAccessError,
)
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/security",
    tags=["Security Hardening"],
)


@router.get(
    "/summary",
    response_model=SecuritySummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_security_summary(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> SecuritySummaryResponse:
    """Retrieve operational security posture, active policies, and threat telemetry."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        return await service.get_security_summary(company_id)
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/logs",
    response_model=SecurityLogListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_security_logs(
    company_id: str,
    event_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    is_blocked: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> SecurityLogListResponse:
    """Query paginated security audit logs with optional threat filters."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        items, total = await service.get_security_logs(
            company_id=company_id,
            event_type=event_type,
            severity=severity,
            is_blocked=is_blocked,
            limit=limit,
            offset=offset,
        )
        return SecurityLogListResponse(
            items=[
                SecurityLogItem(
                    id=log.id,
                    company_id=log.company_id,
                    user_id=log.user_id,
                    actor_type=ActorType(log.actor_type),
                    event_type=SecurityEventType(log.event_type),
                    severity=SecuritySeverity(log.severity),
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    action_details=log.action_details,
                    is_blocked=log.is_blocked,
                    created_at=log.created_at,
                )
                for log in items
            ],
            total=total,
            limit=limit,
            offset=offset,
        )
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/logs",
    response_model=SecurityLogItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_security_log(
    company_id: str,
    payload: SecurityLogCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> SecurityLogItem:
    """Record an authoritative security audit event."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        log = await service.log_security_event(
            company_id=company_id,
            user_id=payload.user_id or current_user.id,
            actor_type=payload.actor_type,
            event_type=payload.event_type,
            severity=payload.severity,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            ip_address=payload.ip_address,
            user_agent=payload.user_agent,
            action_details=payload.action_details,
            is_blocked=payload.is_blocked,
        )
        return SecurityLogItem(
            id=log.id,
            company_id=log.company_id,
            user_id=log.user_id,
            actor_type=ActorType(log.actor_type),
            event_type=SecurityEventType(log.event_type),
            severity=SecuritySeverity(log.severity),
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            action_details=log.action_details,
            is_blocked=log.is_blocked,
            created_at=log.created_at,
        )
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/policies",
    response_model=list[AgentPolicyResponse],
    status_code=status.HTTP_200_OK,
)
async def list_agent_policies(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> list[AgentPolicyResponse]:
    """List capability boundaries and security policies across all agents."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        policies = await service.list_agent_policies(company_id)
        return [
            AgentPolicyResponse(
                id=p.id,
                company_id=p.company_id,
                agent_id=p.agent_id,
                default_posture=p.default_posture,  # type: ignore[arg-type]
                allowed_capabilities=p.allowed_capabilities or [],
                denied_capabilities=p.denied_capabilities or [],
                rate_limit_rpm=p.rate_limit_rpm,
                max_daily_budget=p.max_daily_budget,
                can_execute_destructive_tools=p.can_execute_destructive_tools,
                requires_human_approval_for_tools=p.requires_human_approval_for_tools,
                is_quarantined=p.is_quarantined,
                quarantine_reason=p.quarantine_reason,
                quarantined_at=p.quarantined_at,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in policies
        ]
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/policies/agent/{agent_id}",
    response_model=AgentPolicyResponse,
    status_code=status.HTTP_200_OK,
)
async def get_agent_policy(
    company_id: str,
    agent_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> AgentPolicyResponse:
    """Retrieve security policy for a specific agent (auto-initializes Default-DENY)."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        p = await service.get_agent_policy(company_id, agent_id)
        return AgentPolicyResponse(
            id=p.id,
            company_id=p.company_id,
            agent_id=p.agent_id,
            default_posture=p.default_posture,  # type: ignore[arg-type]
            allowed_capabilities=p.allowed_capabilities or [],
            denied_capabilities=p.denied_capabilities or [],
            rate_limit_rpm=p.rate_limit_rpm,
            max_daily_budget=p.max_daily_budget,
            can_execute_destructive_tools=p.can_execute_destructive_tools,
            requires_human_approval_for_tools=p.requires_human_approval_for_tools,
            is_quarantined=p.is_quarantined,
            quarantine_reason=p.quarantine_reason,
            quarantined_at=p.quarantined_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.put(
    "/policies/agent/{agent_id}",
    response_model=AgentPolicyResponse,
    status_code=status.HTTP_200_OK,
)
async def update_agent_policy(
    company_id: str,
    agent_id: str,
    payload: AgentPolicyUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> AgentPolicyResponse:
    """Update capability boundaries, rate limit, or tool approval requirements for an agent."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        p = await service.update_agent_policy(company_id, agent_id, payload)
        return AgentPolicyResponse(
            id=p.id,
            company_id=p.company_id,
            agent_id=p.agent_id,
            default_posture=p.default_posture,  # type: ignore[arg-type]
            allowed_capabilities=p.allowed_capabilities or [],
            denied_capabilities=p.denied_capabilities or [],
            rate_limit_rpm=p.rate_limit_rpm,
            max_daily_budget=p.max_daily_budget,
            can_execute_destructive_tools=p.can_execute_destructive_tools,
            requires_human_approval_for_tools=p.requires_human_approval_for_tools,
            is_quarantined=p.is_quarantined,
            quarantine_reason=p.quarantine_reason,
            quarantined_at=p.quarantined_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/agents/{agent_id}/quarantine",
    response_model=AgentPolicyResponse,
    status_code=status.HTTP_200_OK,
)
async def quarantine_agent(
    company_id: str,
    agent_id: str,
    payload: AgentQuarantineRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> AgentPolicyResponse:
    """Place an agent into quarantine, immediately revoking all action privileges."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        p = await service.quarantine_agent(company_id, agent_id, payload.reason)
        return AgentPolicyResponse(
            id=p.id,
            company_id=p.company_id,
            agent_id=p.agent_id,
            default_posture=p.default_posture,  # type: ignore[arg-type]
            allowed_capabilities=p.allowed_capabilities or [],
            denied_capabilities=p.denied_capabilities or [],
            rate_limit_rpm=p.rate_limit_rpm,
            max_daily_budget=p.max_daily_budget,
            can_execute_destructive_tools=p.can_execute_destructive_tools,
            requires_human_approval_for_tools=p.requires_human_approval_for_tools,
            is_quarantined=p.is_quarantined,
            quarantine_reason=p.quarantine_reason,
            quarantined_at=p.quarantined_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/agents/{agent_id}/unquarantine",
    response_model=AgentPolicyResponse,
    status_code=status.HTTP_200_OK,
)
async def unquarantine_agent(
    company_id: str,
    agent_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> AgentPolicyResponse:
    """Restore an agent from quarantine."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        p = await service.unquarantine_agent(company_id, agent_id)
        return AgentPolicyResponse(
            id=p.id,
            company_id=p.company_id,
            agent_id=p.agent_id,
            default_posture=p.default_posture,  # type: ignore[arg-type]
            allowed_capabilities=p.allowed_capabilities or [],
            denied_capabilities=p.denied_capabilities or [],
            rate_limit_rpm=p.rate_limit_rpm,
            max_daily_budget=p.max_daily_budget,
            can_execute_destructive_tools=p.can_execute_destructive_tools,
            requires_human_approval_for_tools=p.requires_human_approval_for_tools,
            is_quarantined=p.is_quarantined,
            quarantine_reason=p.quarantine_reason,
            quarantined_at=p.quarantined_at,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/scan-prompt",
    response_model=PromptScanResponse,
    status_code=status.HTTP_200_OK,
)
async def scan_prompt(
    company_id: str,
    payload: PromptScanRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> PromptScanResponse:
    """Scan untrusted content for prompt injection exploits and redact sensitive credentials."""
    service = SecurityService(session)
    try:
        await service.verify_tenant_boundary(current_user.id, company_id)
        res = await service.scan_and_sanitize_prompt(
            company_id=company_id,
            content=payload.content,
            source_type=payload.source_type,
            actor_id=current_user.id,
        )
        return PromptScanResponse(
            is_safe=res.is_safe,
            injection_detected=res.injection_detected,
            injection_indicators=res.injection_indicators,
            redacted_content=res.redacted_content,
            redacted_secrets_count=res.redacted_secrets_count,
            data_tagged_content=res.data_tagged_content,
        )
    except CrossTenantAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
