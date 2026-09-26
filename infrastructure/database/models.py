"""Database models for AI Company OS infrastructure, authentication, and company organization."""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    desc,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.base import Base


class SystemMetadata(Base):
    """System metadata table to verify baseline database and migration connectivity."""

    __tablename__ = "system_metadata"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class User(Base):
    """User account entity adhering to docs/Phases.md Section 5."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationship to sessions
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Relationship to company memberships
    memberships: Mapped[list["CompanyMember"]] = relationship(
        "CompanyMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Relationship to reviewed approval requests
    reviewed_approvals: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="reviewed_by_user",
        foreign_keys="ApprovalRequest.reviewed_by_user_id",
    )
    decisions: Mapped[list["CompanyDecision"]] = relationship(
        "CompanyDecision",
        back_populates="decided_by_user",
        foreign_keys="CompanyDecision.decided_by_user_id",
    )
    assigned_errors: Mapped[list["ErrorRecord"]] = relationship(
        "ErrorRecord",
        back_populates="assigned_user",
        foreign_keys="ErrorRecord.assigned_user_id",
    )
    security_audit_logs: Mapped[list["SecurityAuditLog"]] = relationship(
        "SecurityAuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSession(Base):
    """Authoritative user session entity stored in PostgreSQL."""

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship to user
    user: Mapped["User"] = relationship("User", back_populates="sessions")


class Company(Base):
    """Company entity adhering to docs/Phases.md Section 7 and docs/Architecture.md Section 63."""

    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    members: Mapped[list["CompanyMember"]] = relationship(
        "CompanyMember",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    plans: Mapped[list["CeoPlan"]] = relationship(
        "CeoPlan",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    delegation_records: Mapped[list["DelegationRecord"]] = relationship(
        "DelegationRecord",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    execution_records: Mapped[list["ExecutionRecord"]] = relationship(
        "ExecutionRecord",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    tool_execution_records: Mapped[list["ToolExecutionRecord"]] = relationship(
        "ToolExecutionRecord",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[list["CompanyDecision"]] = relationship(
        "CompanyDecision",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    activity_events: Mapped[list["ActivityEvent"]] = relationship(
        "ActivityEvent",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    agent_presences: Mapped[list["AgentPresence"]] = relationship(
        "AgentPresence",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    errors: Mapped[list["ErrorRecord"]] = relationship(
        "ErrorRecord",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    file_changes: Mapped[list["TaskFileChange"]] = relationship(
        "TaskFileChange",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    knowledge_items: Mapped[list["CompanyKnowledge"]] = relationship(
        "CompanyKnowledge",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    vector_embeddings: Mapped[list["VectorEmbedding"]] = relationship(
        "VectorEmbedding",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    voice_sessions: Mapped[list["VoiceSession"]] = relationship(
        "VoiceSession",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    voice_interactions: Mapped[list["VoiceInteraction"]] = relationship(
        "VoiceInteraction",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    verification_runs: Mapped[list["VerificationRun"]] = relationship(
        "VerificationRun",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    evaluation_benchmarks: Mapped[list["EvaluationBenchmark"]] = relationship(
        "EvaluationBenchmark",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    security_audit_logs: Mapped[list["SecurityAuditLog"]] = relationship(
        "SecurityAuditLog",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    agent_security_policies: Mapped[list["AgentSecurityPolicy"]] = relationship(
        "AgentSecurityPolicy",
        back_populates="company",
        cascade="all, delete-orphan",
    )


class CompanyMember(Base):
    """Explicit user-to-company membership entity supporting multi-company isolation."""

    __tablename__ = "company_members"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="owner",
        server_default="owner",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    __table_args__ = (UniqueConstraint("company_id", "user_id", name="uq_company_member_user"),)


class Department(Base):
    """Department organizational entity adhering to docs/Phases.md Section 7 and docs/Architecture.md Section 25."""

    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="departments")
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="department")

    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_company_department_code"),)


class Agent(Base):
    """Authoritative Agent entity adhering to docs/Phases.md Section 8 and docs/Rules.md Section 156."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="specialist",
        server_default="specialist",
    )
    reports_to: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    authority_level: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="specialist",
        server_default="specialist",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="agents")
    department: Mapped["Department | None"] = relationship("Department", back_populates="agents")
    manager: Mapped["Agent | None"] = relationship(
        "Agent",
        remote_side=[id],
        back_populates="subordinates",
    )
    subordinates: Mapped[list["Agent"]] = relationship(
        "Agent",
        back_populates="manager",
    )
    definitions: Mapped[list["AgentDefinition"]] = relationship(
        "AgentDefinition",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by=lambda: desc(AgentDefinition.created_at),
    )
    execution_records: Mapped[list["ExecutionRecord"]] = relationship(
        "ExecutionRecord",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    tool_execution_records: Mapped[list["ToolExecutionRecord"]] = relationship(
        "ToolExecutionRecord",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[list["CompanyDecision"]] = relationship(
        "CompanyDecision",
        back_populates="decided_by_agent",
        foreign_keys="CompanyDecision.decided_by_agent_id",
    )
    presence: Mapped["AgentPresence | None"] = relationship(
        "AgentPresence",
        uselist=False,
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    assigned_errors: Mapped[list["ErrorRecord"]] = relationship(
        "ErrorRecord",
        back_populates="assigned_agent",
        foreign_keys="ErrorRecord.assigned_agent_id",
    )
    file_changes: Mapped[list["TaskFileChange"]] = relationship(
        "TaskFileChange",
        back_populates="agent",
    )
    security_policy: Mapped["AgentSecurityPolicy | None"] = relationship(
        "AgentSecurityPolicy",
        uselist=False,
        back_populates="agent",
        cascade="all, delete-orphan",
    )


class AgentDefinition(Base):
    """Versioned Agent Definition adhering to docs/Rules.md Section 129 and docs/Memory.md Section 2153."""

    __tablename__ = "agent_definitions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0",
        server_default="1.0",
    )
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="gemini-1.5-pro",
        server_default="gemini-1.5-pro",
    )
    capabilities: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    tools: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="definitions")

    __table_args__ = (
        UniqueConstraint("agent_id", "version", name="uq_agent_definitions_agent_version"),
    )


class CeoPlan(Base):
    """CEO Plan proposal entity adhering to docs/Phases.md Section 9 and docs/Architecture.md Section 16-20."""

    __tablename__ = "ceo_plans"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ceo_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    requested_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="medium",
        server_default="medium",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="proposed",
        server_default="proposed",
    )
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    context_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    plan_steps: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    delegation_proposals: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    approval_requirements: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    risks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    assumptions: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="plans")
    user: Mapped["User"] = relationship("User")
    ceo_agent: Mapped["Agent | None"] = relationship("Agent")
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project: Mapped["Project | None"] = relationship("Project")


# Table indexes
Index("ix_user_sessions_user_expires", UserSession.user_id, UserSession.expires_at)
Index("ix_departments_company_status", Department.company_id, Department.status)
Index("ix_company_members_company_role", CompanyMember.company_id, CompanyMember.role)
Index("ix_agents_company_status", Agent.company_id, Agent.status)
Index("ix_agents_company_department", Agent.company_id, Agent.department_id)
Index("ix_agent_definitions_agent_current", AgentDefinition.agent_id, AgentDefinition.is_current)
Index("ix_ceo_plans_company_created", CeoPlan.company_id, CeoPlan.created_at)
Index("ix_ceo_plans_company_status", CeoPlan.company_id, CeoPlan.status)


class Project(Base):
    """Project entity adhering to docs/Phases.md Section 10 and docs/Architecture.md Section 43."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PLANNED",
        server_default="PLANNED",
    )
    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="medium",
        server_default="medium",
    )
    owner_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    owner_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="projects")
    owner_user: Mapped["User | None"] = relationship("User")
    owner_agent: Mapped["Agent | None"] = relationship("Agent")
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[list["CompanyDecision"]] = relationship(
        "CompanyDecision",
        back_populates="project",
    )
    activity_events: Mapped[list["ActivityEvent"]] = relationship(
        "ActivityEvent",
        back_populates="project",
    )
    active_presences: Mapped[list["AgentPresence"]] = relationship(
        "AgentPresence",
        back_populates="current_project",
        foreign_keys="AgentPresence.current_project_id",
    )
    errors: Mapped[list["ErrorRecord"]] = relationship(
        "ErrorRecord",
        back_populates="project",
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact",
        back_populates="project",
    )
    knowledge_items: Mapped[list["CompanyKnowledge"]] = relationship(
        "CompanyKnowledge",
        back_populates="project",
    )


class Task(Base):
    """Task entity adhering to docs/Phases.md Section 10 and docs/Architecture.md Section 43."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    parent_task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="CREATED",
        server_default="CREATED",
    )
    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="medium",
        server_default="medium",
    )
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="tasks")
    project: Mapped["Project | None"] = relationship("Project", back_populates="tasks")
    parent_task: Mapped["Task | None"] = relationship(
        "Task",
        remote_side=[id],
        back_populates="subtasks",
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="parent_task",
        cascade="all, delete-orphan",
    )
    department: Mapped["Department | None"] = relationship("Department")
    created_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_user_id])
    created_by_agent: Mapped["Agent | None"] = relationship(
        "Agent", foreign_keys=[created_by_agent_id]
    )
    assigned_agent: Mapped["Agent | None"] = relationship(
        "Agent", foreign_keys=[assigned_to_agent_id]
    )
    assigned_user: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_to_user_id])

    dependencies: Mapped[list["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    dependents: Mapped[list["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on_task",
        cascade="all, delete-orphan",
    )
    delegation_records: Mapped[list["DelegationRecord"]] = relationship(
        "DelegationRecord",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    execution_records: Mapped[list["ExecutionRecord"]] = relationship(
        "ExecutionRecord",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by=lambda: desc(ExecutionRecord.created_at),
    )
    tool_execution_records: Mapped[list["ToolExecutionRecord"]] = relationship(
        "ToolExecutionRecord",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by=lambda: desc(ToolExecutionRecord.created_at),
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[list["CompanyDecision"]] = relationship(
        "CompanyDecision",
        back_populates="task",
    )
    activity_events: Mapped[list["ActivityEvent"]] = relationship(
        "ActivityEvent",
        back_populates="task",
    )
    active_presences: Mapped[list["AgentPresence"]] = relationship(
        "AgentPresence",
        back_populates="current_task",
        foreign_keys="AgentPresence.current_task_id",
    )
    errors: Mapped[list["ErrorRecord"]] = relationship(
        "ErrorRecord",
        back_populates="task",
    )
    engineering_context: Mapped["TaskEngineeringContext | None"] = relationship(
        "TaskEngineeringContext",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )
    file_changes: Mapped[list["TaskFileChange"]] = relationship(
        "TaskFileChange",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact",
        back_populates="task",
    )
    knowledge_items: Mapped[list["CompanyKnowledge"]] = relationship(
        "CompanyKnowledge",
        back_populates="task",
    )


class TaskDependency(Base):
    """Task dependency link adhering to docs/Architecture.md line 1175."""

    __tablename__ = "task_dependencies"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    depends_on_task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependencies_pair"),
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task", foreign_keys=[task_id], back_populates="dependencies"
    )
    depends_on_task: Mapped["Task"] = relationship(
        "Task", foreign_keys=[depends_on_task_id], back_populates="dependents"
    )


Index("ix_projects_company_status", Project.company_id, Project.status)
Index("ix_projects_company_created", Project.company_id, Project.created_at)
Index("ix_tasks_company_status", Task.company_id, Task.status)
Index("ix_tasks_company_project", Task.company_id, Task.project_id)
Index("ix_tasks_company_assigned", Task.company_id, Task.assigned_to_agent_id)
Index("ix_tasks_company_created", Task.company_id, Task.created_at)
Index("ix_task_dependencies_company", TaskDependency.company_id)


class DelegationRecord(Base):
    """Delegation history record adhering to docs/Memory.md Section 18 and docs/Rules.md §§ 60 & 61."""

    __tablename__ = "delegation_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    delegated_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delegated_by_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delegated_to_agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="delegation_records")
    task: Mapped["Task"] = relationship("Task", back_populates="delegation_records")
    delegated_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[delegated_by_user_id]
    )
    delegated_by_agent: Mapped["Agent | None"] = relationship(
        "Agent", foreign_keys=[delegated_by_agent_id]
    )
    delegated_to_agent: Mapped["Agent"] = relationship(
        "Agent", foreign_keys=[delegated_to_agent_id]
    )


Index(
    "ix_delegation_records_company_task",
    DelegationRecord.company_id,
    DelegationRecord.task_id,
)
Index(
    "ix_delegation_records_company_target",
    DelegationRecord.company_id,
    DelegationRecord.delegated_to_agent_id,
)
Index(
    "ix_delegation_records_company_created",
    DelegationRecord.company_id,
    DelegationRecord.created_at,
)


class ExecutionRecord(Base):
    """Authoritative audit record of an agent task execution run adhering to docs/Phases.md Section 12."""

    __tablename__ = "execution_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    executed_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="RUNNING",
        server_default="RUNNING",
    )
    step_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    estimated_cost: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0.0"
    )
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    deliverable: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="execution_records")
    task: Mapped["Task"] = relationship("Task", back_populates="execution_records")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="execution_records")
    executed_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[executed_by_user_id]
    )
    tool_executions: Mapped[list["ToolExecutionRecord"]] = relationship(
        "ToolExecutionRecord",
        back_populates="execution_record",
        cascade="all, delete-orphan",
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="execution_record",
        cascade="all, delete-orphan",
    )


Index(
    "ix_execution_records_company_task",
    ExecutionRecord.company_id,
    ExecutionRecord.task_id,
)
Index(
    "ix_execution_records_company_agent",
    ExecutionRecord.company_id,
    ExecutionRecord.agent_id,
)
Index(
    "ix_execution_records_company_created",
    ExecutionRecord.company_id,
    ExecutionRecord.created_at,
)


class ToolExecutionRecord(Base):
    """Authoritative audit record of an agent external tool invocation through Tool Gateway."""

    __tablename__ = "tool_execution_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    execution_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("execution_records.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="LOW",
        server_default="LOW",
    )
    requires_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="SUCCESS",
        server_default="SUCCESS",
    )
    input_params: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    output_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="tool_execution_records")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="tool_execution_records")
    task: Mapped["Task | None"] = relationship("Task", back_populates="tool_execution_records")
    execution_record: Mapped["ExecutionRecord | None"] = relationship(
        "ExecutionRecord", back_populates="tool_executions"
    )
    approval_request: Mapped["ApprovalRequest | None"] = relationship(
        "ApprovalRequest",
        back_populates="tool_execution",
        uselist=False,
    )


Index(
    "ix_tool_execution_records_company_created",
    ToolExecutionRecord.company_id,
    ToolExecutionRecord.created_at,
)
Index(
    "ix_tool_execution_records_agent_created",
    ToolExecutionRecord.agent_id,
    ToolExecutionRecord.created_at,
)
Index(
    "ix_tool_execution_records_task_created",
    ToolExecutionRecord.task_id,
    ToolExecutionRecord.created_at,
)


class ApprovalRequest(Base):
    """Authoritative Human Approval & Oversight request entity adhering to docs/Phases.md Section 14 and docs/Architecture.md Sections 40-45."""

    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    execution_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("execution_records.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    tool_execution_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tool_execution_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    risk_level: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="MEDIUM",
        server_default="MEDIUM",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )
    reviewed_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="approval_requests")
    task: Mapped["Task | None"] = relationship("Task", back_populates="approval_requests")
    agent: Mapped["Agent | None"] = relationship("Agent", back_populates="approval_requests")
    execution_record: Mapped["ExecutionRecord | None"] = relationship(
        "ExecutionRecord", back_populates="approval_requests"
    )
    tool_execution: Mapped["ToolExecutionRecord | None"] = relationship(
        "ToolExecutionRecord", back_populates="approval_request"
    )
    reviewed_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[reviewed_by_user_id], back_populates="reviewed_approvals"
    )


Index("ix_approval_requests_company_status", ApprovalRequest.company_id, ApprovalRequest.status)
Index(
    "ix_approval_requests_company_created", ApprovalRequest.company_id, ApprovalRequest.created_at
)


class CompanyDecision(Base):
    """Authoritative company decision entity adhering to docs/Memory.md § 33.

    Decisions represent durable strategic, architectural, and operational determinations.
    Historical decisions are immutable; superseded decisions point to newer decisions
    via `superseded_by_decision_id` while transitioning status to SUPERSEDED.
    """

    __tablename__ = "company_decisions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
    )
    decided_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    decided_by_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    superseded_by_decision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("company_decisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="decisions")
    project: Mapped["Project | None"] = relationship("Project", back_populates="decisions")
    task: Mapped["Task | None"] = relationship("Task", back_populates="decisions")
    decided_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[decided_by_user_id], back_populates="decisions"
    )
    decided_by_agent: Mapped["Agent | None"] = relationship(
        "Agent", foreign_keys=[decided_by_agent_id], back_populates="decisions"
    )
    superseded_by_decision: Mapped["CompanyDecision | None"] = relationship(
        "CompanyDecision",
        remote_side="CompanyDecision.id",
        foreign_keys=[superseded_by_decision_id],
        backref="supersedes_decisions",
    )
    knowledge_items: Mapped[list["CompanyKnowledge"]] = relationship(
        "CompanyKnowledge",
        back_populates="decision",
    )


Index("ix_company_decisions_company_status", CompanyDecision.company_id, CompanyDecision.status)
Index(
    "ix_company_decisions_company_created",
    CompanyDecision.company_id,
    CompanyDecision.created_at,
)


class ActivityEvent(Base):
    """Activity event entity adhering to docs/Phases.md Section 17.

    Human-readable operational company timeline tracking what happened over time.
    """

    __tablename__ = "activity_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="system",
        server_default="system",
    )
    actor_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="activity_events")
    project: Mapped["Project | None"] = relationship("Project", back_populates="activity_events")
    task: Mapped["Task | None"] = relationship("Task", back_populates="activity_events")


Index("ix_activity_events_company_created", ActivityEvent.company_id, ActivityEvent.created_at)
Index("ix_activity_events_project_created", ActivityEvent.project_id, ActivityEvent.created_at)
Index("ix_activity_events_task_created", ActivityEvent.task_id, ActivityEvent.created_at)
Index(
    "ix_activity_events_actor",
    ActivityEvent.company_id,
    ActivityEvent.actor_type,
    ActivityEvent.actor_id,
)
Index("ix_activity_events_event_type", ActivityEvent.company_id, ActivityEvent.event_type)


class AgentPresence(Base):
    """Authoritative agent presence entity adhering to docs/Phases.md Section 18 and docs/Memory.md Section 20."""

    __tablename__ = "agent_presences"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="IDLE",
        server_default="IDLE",
    )
    current_task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    current_project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    current_activity: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    current_step: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="presence")
    company: Mapped["Company"] = relationship("Company", back_populates="agent_presences")
    current_task: Mapped["Task | None"] = relationship(
        "Task",
        foreign_keys=[current_task_id],
        back_populates="active_presences",
    )
    current_project: Mapped["Project | None"] = relationship(
        "Project",
        foreign_keys=[current_project_id],
        back_populates="active_presences",
    )


Index("ix_agent_presence_company_status", AgentPresence.company_id, AgentPresence.status)
Index(
    "ix_agent_presence_company_heartbeat", AgentPresence.company_id, AgentPresence.last_heartbeat_at
)


class ErrorRecord(Base):
    """Authoritative error and bug management record adhering to docs/Phases.md Section 19.

    Captures structured discovery, assignment, investigation, resolution, and verification.
    """

    __tablename__ = "errors"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="MEDIUM",
        server_default="MEDIUM",
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="OPEN",
        server_default="OPEN",
        index=True,
    )
    detected_by: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    investigated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="errors")
    project: Mapped["Project | None"] = relationship("Project", back_populates="errors")
    task: Mapped["Task | None"] = relationship("Task", back_populates="errors")
    assigned_agent: Mapped["Agent | None"] = relationship(
        "Agent", foreign_keys=[assigned_agent_id], back_populates="assigned_errors"
    )
    assigned_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_user_id], back_populates="assigned_errors"
    )


Index("ix_errors_company_status", ErrorRecord.company_id, ErrorRecord.status)
Index("ix_errors_company_severity", ErrorRecord.company_id, ErrorRecord.severity)
Index("ix_errors_company_created", ErrorRecord.company_id, ErrorRecord.created_at)


class TaskEngineeringContext(Base):
    """Engineering context for a task adhering to docs/Phases.md Section 20.

    Connects task to branch, PR, commit counts, test status, and verification state.
    """

    __tablename__ = "task_engineering_contexts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    repository: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="main",
        server_default="main",
    )
    branch: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="main",
        server_default="main",
        index=True,
    )
    pull_request_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pull_request_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pull_request_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    test_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
    )
    test_output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
    )
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    task: Mapped["Task"] = relationship("Task", back_populates="engineering_context")


class TaskFileChange(Base):
    """File modification tracked for a task adhering to docs/Phases.md Section 20.

    Tracks: file_path, repository, branch, agent, task, last_modified, commit, change_summary.
    """

    __tablename__ = "task_file_changes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    repository: Mapped[str] = mapped_column(
        String(255), nullable=False, default="main", server_default="main"
    )
    branch: Mapped[str] = mapped_column(
        String(255), nullable=False, default="main", server_default="main", index=True
    )
    agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    change_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="MODIFIED",
        server_default="MODIFIED",
    )
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    commit_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    additions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    deletions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="file_changes")
    task: Mapped["Task"] = relationship("Task", back_populates="file_changes")
    agent: Mapped["Agent | None"] = relationship("Agent", back_populates="file_changes")


Index("ix_task_eng_company_task", TaskEngineeringContext.company_id, TaskEngineeringContext.task_id)
Index("ix_task_file_changes_company_task", TaskFileChange.company_id, TaskFileChange.task_id)
Index("ix_task_file_changes_company_file", TaskFileChange.company_id, TaskFileChange.file_path)
Index("ix_task_file_changes_company_branch", TaskFileChange.company_id, TaskFileChange.branch)


class Artifact(Base):
    """Authoritative Artifact and Document entity adhering to docs/Phases.md Section 22 and docs/Memory.md Section 31."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    creator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="DOCUMENT",
        server_default="DOCUMENT",
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    parent_artifact_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="artifacts")
    project: Mapped["Project | None"] = relationship("Project", back_populates="artifacts")
    task: Mapped["Task | None"] = relationship("Task", back_populates="artifacts")
    created_by_agent: Mapped["Agent | None"] = relationship(
        "Agent", foreign_keys=[created_by_agent_id]
    )
    created_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_user_id])
    parent_artifact: Mapped["Artifact | None"] = relationship(
        "Artifact",
        remote_side=[id],
        back_populates="child_versions",
    )
    child_versions: Mapped[list["Artifact"]] = relationship(
        "Artifact",
        back_populates="parent_artifact",
    )
    knowledge_items: Mapped[list["CompanyKnowledge"]] = relationship(
        "CompanyKnowledge",
        back_populates="artifact",
    )


Index("ix_artifacts_company_type", Artifact.company_id, Artifact.artifact_type)
Index("ix_artifacts_company_project", Artifact.company_id, Artifact.project_id)
Index("ix_artifacts_company_task", Artifact.company_id, Artifact.task_id)
Index("ix_artifacts_company_parent", Artifact.company_id, Artifact.parent_artifact_id)
Index("ix_artifacts_company_created", Artifact.company_id, Artifact.created_at)


class CompanyKnowledge(Base):
    """Authoritative company knowledge entity adhering to docs/Phases.md Section 23 and docs/Memory.md Sections 31-39.

    Stores research, strategies, policies, meeting notes, decision rationales, procedures,
    and historical results with full provenance and confidence metrics.
    """

    __tablename__ = "company_knowledge"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    decision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("company_decisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    artifact_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="GENERAL",
        server_default="GENERAL",
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="USER",
        server_default="USER",
    )
    source_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="HIGH",
        server_default="HIGH",
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    knowledge_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="knowledge_items")
    project: Mapped["Project | None"] = relationship("Project", back_populates="knowledge_items")
    task: Mapped["Task | None"] = relationship("Task", back_populates="knowledge_items")
    decision: Mapped["CompanyDecision | None"] = relationship(
        "CompanyDecision", back_populates="knowledge_items"
    )
    artifact: Mapped["Artifact | None"] = relationship("Artifact", back_populates="knowledge_items")


Index("ix_company_knowledge_company_cat", CompanyKnowledge.company_id, CompanyKnowledge.category)
Index(
    "ix_company_knowledge_company_project", CompanyKnowledge.company_id, CompanyKnowledge.project_id
)
Index(
    "ix_company_knowledge_company_created", CompanyKnowledge.company_id, CompanyKnowledge.created_at
)


class VectorEmbedding(Base):
    """Authoritative semantic vector embedding record adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40.

    Stores normalized 768-dimensional dense embeddings for company knowledge chunks, decisions,
    artifacts, and tasks. Enables sub-millisecond approximate nearest neighbor (ANN) retrieval
    without altering authoritative structured state.
    """

    __tablename__ = "vector_embeddings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(768),
        nullable=False,
    )
    embedding_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="vector_embeddings")


Index(
    "ix_vector_embeddings_company_source", VectorEmbedding.company_id, VectorEmbedding.source_type
)
Index(
    "ix_vector_embeddings_company_source_id", VectorEmbedding.company_id, VectorEmbedding.source_id
)
Index(
    "ix_vector_embeddings_company_created", VectorEmbedding.company_id, VectorEmbedding.created_at
)
Index(
    "ix_vector_embeddings_hnsw",
    VectorEmbedding.embedding,
    postgresql_using="hnsw",
    postgresql_ops={"embedding": "vector_cosine_ops"},
)


class VoiceSession(Base):
    """Conversational voice control session adhering to docs/Phases.md Section 25."""

    __tablename__ = "voice_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Voice Session",
        server_default="Voice Session",
    )
    state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="IDLE",
        server_default="IDLE",
        index=True,
    )
    context_data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="voice_sessions")
    user: Mapped["User"] = relationship("User")
    interactions: Mapped[list["VoiceInteraction"]] = relationship(
        "VoiceInteraction",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="VoiceInteraction.created_at",
        lazy="selectin",
    )


class VoiceInteraction(Base):
    """Individual voice conversation turn and action execution record adhering to docs/Phases.md Section 25."""

    __tablename__ = "voice_interactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("voice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="GENERAL_INQUIRY",
        server_default="GENERAL_INQUIRY",
        index=True,
    )
    action_taken: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action_success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    spoken_response: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_response: Mapped[str] = mapped_column(Text, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    session: Mapped["VoiceSession"] = relationship("VoiceSession", back_populates="interactions")
    company: Mapped["Company"] = relationship("Company", back_populates="voice_interactions")
    user: Mapped["User"] = relationship("User")


Index("ix_voice_sessions_company_user", VoiceSession.company_id, VoiceSession.user_id)
Index(
    "ix_voice_interactions_session_created",
    VoiceInteraction.session_id,
    VoiceInteraction.created_at,
)


class VerificationRun(Base):
    """Authoritative record of a verification pipeline execution adhering to docs/Phases.md Section 26 and docs/Architecture.md Section 71."""

    __tablename__ = "verification_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="TASK",
        server_default="TASK",
        index=True,
    )
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="RUNNING",
        server_default="RUNNING",
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0",
    )
    pipeline_stage: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="SCHEMA_VALIDATION",
        server_default="SCHEMA_VALIDATION",
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="verification_runs")
    agent: Mapped["Agent | None"] = relationship("Agent")
    criterion_scores: Mapped[list["EvaluationCriterionScore"]] = relationship(
        "EvaluationCriterionScore",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EvaluationCriterionScore.criterion",
        lazy="selectin",
    )


class EvaluationCriterionScore(Base):
    """Score and evidence for an individual evaluation criterion across the 8 canonical dimensions."""

    __tablename__ = "evaluation_criterion_scores"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("verification_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    criterion: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    score: Mapped[float] = mapped_column(
        Float, nullable=False, default=100.0, server_default="100.0"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PASSED",
        server_default="PASSED",
    )
    details: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    evidence: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Relationships
    run: Mapped["VerificationRun"] = relationship(
        "VerificationRun", back_populates="criterion_scores"
    )


class EvaluationBenchmark(Base):
    """Configured evaluation benchmark suite or representative task specification per docs/Phases.md Section 26."""

    __tablename__ = "evaluation_benchmarks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    task_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    target_role: Mapped[str] = mapped_column(
        String(64), nullable=False, default="GENERAL", server_default="GENERAL"
    )
    expected_output_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_passing_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=75.0, server_default="75.0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="evaluation_benchmarks")


Index("ix_verification_runs_company_target", VerificationRun.company_id, VerificationRun.target_id)
Index(
    "ix_evaluation_benchmarks_company_cat",
    EvaluationBenchmark.company_id,
    EvaluationBenchmark.category,
)


class SecurityAuditLog(Base):
    """Immutable audit record for security-sensitive operations, access attempts, and threat mitigations per docs/Phases.md § 27 and docs/Rules.md § 185."""

    __tablename__ = "security_audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="USER",
        server_default="USER",
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="LOW",
        server_default="LOW",
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="GENERAL", server_default="GENERAL"
    )
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action_details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    company: Mapped["Company | None"] = relationship(
        "Company", back_populates="security_audit_logs"
    )
    user: Mapped["User | None"] = relationship("User", back_populates="security_audit_logs")


class AgentSecurityPolicy(Base):
    """Authoritative agent capability constraints, sandboxing, and Default-DENY access control per docs/Phases.md § 27 and docs/Rules.md § 185."""

    __tablename__ = "agent_security_policies"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    default_posture: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="DENY",
        server_default="DENY",
    )
    allowed_capabilities: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    denied_capabilities: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
    rate_limit_rpm: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        server_default="60",
    )
    max_daily_budget: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=50.0,
        server_default="50.0",
    )
    can_execute_destructive_tools: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    requires_human_approval_for_tools: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    is_quarantined: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    quarantine_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    quarantined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="agent_security_policies")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="security_policy")


Index(
    "ix_security_audit_logs_company_created",
    SecurityAuditLog.company_id,
    SecurityAuditLog.created_at,
)
Index("ix_security_audit_logs_event_sev", SecurityAuditLog.event_type, SecurityAuditLog.severity)
Index(
    "ix_agent_security_policies_company_agent",
    AgentSecurityPolicy.company_id,
    AgentSecurityPolicy.agent_id,
)
