"""Pydantic schemas for Project and Task API endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateRequest(BaseModel):
    """Payload to create a new project."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: str | None = Field(
        default=None, max_length=5000, description="Project description"
    )
    objective: str | None = Field(default=None, max_length=5000, description="Strategic objective")
    status: str = Field(default="PLANNED", description="Project lifecycle status")
    priority: str = Field(default="medium", description="Project priority")
    owner_user_id: str | None = Field(default=None, description="Owner user UUID")
    owner_agent_id: str | None = Field(default=None, description="Owner agent UUID")


class ProjectUpdateRequest(BaseModel):
    """Payload to update an existing project."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    objective: str | None = Field(default=None, max_length=5000)
    status: str | None = None
    priority: str | None = None
    owner_user_id: str | None = None
    owner_agent_id: str | None = None


class ProjectTaskStats(BaseModel):
    """Task rollup statistics for a project."""

    total_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    in_progress_tasks: int = 0
    planned_tasks: int = 0


class ProjectResponse(BaseModel):
    """Response representing a project entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    name: str
    description: str | None = None
    objective: str | None = None
    status: str
    priority: str
    owner_user_id: str | None = None
    owner_agent_id: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    stats: ProjectTaskStats | None = None


class ProjectListResponse(BaseModel):
    """Paginated response containing projects."""

    items: list[ProjectResponse]
    total: int


class TaskDependencyResponse(BaseModel):
    """Representation of a prerequisite task dependency."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    depends_on_task_id: str
    depends_on_task_title: str | None = None
    depends_on_task_status: str | None = None
    created_at: datetime


class TaskCreateRequest(BaseModel):
    """Payload to create a new task."""

    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: str | None = Field(default=None, max_length=5000, description="Task description")
    objective: str | None = Field(default=None, max_length=5000, description="Task objective")
    project_id: str | None = Field(default=None, description="Optional parent project UUID")
    parent_task_id: str | None = Field(
        default=None, description="Optional parent task UUID for subtasks"
    )
    assigned_to_agent_id: str | None = Field(
        default=None, description="Target specialist agent UUID"
    )
    assigned_to_user_id: str | None = Field(default=None, description="Target human user UUID")
    department_id: str | None = Field(default=None, description="Department UUID")
    status: str = Field(default="CREATED", description="Initial task status")
    priority: str = Field(default="medium", description="Task priority")
    deadline: datetime | None = Field(default=None, description="Target completion timestamp")
    dependency_task_ids: list[str] = Field(
        default_factory=list, description="Prerequisite task IDs"
    )


class TaskUpdateRequest(BaseModel):
    """Payload to update task details."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    objective: str | None = Field(default=None, max_length=5000)
    project_id: str | None = None
    department_id: str | None = None
    priority: str | None = None
    deadline: datetime | None = None


class TaskStatusUpdateRequest(BaseModel):
    """Payload to advance or transition a task status."""

    status: str = Field(..., description="Target status from authoritative state machine")
    output: str | None = Field(
        default=None, max_length=10000, description="Completion output or verification notes"
    )
    error_details: str | None = Field(
        default=None, max_length=10000, description="Failure reason or error context"
    )


class TaskAssignRequest(BaseModel):
    """Payload to assign a task to an agent or user."""

    assigned_to_agent_id: str | None = None
    assigned_to_user_id: str | None = None


class TaskDependencyCreateRequest(BaseModel):
    """Payload to add a prerequisite dependency."""

    depends_on_task_id: str = Field(..., description="UUID of task that must be completed first")


class TaskResponse(BaseModel):
    """Full task response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    project_id: str | None = None
    parent_task_id: str | None = None
    title: str
    description: str | None = None
    objective: str | None = None
    created_by_user_id: str | None = None
    assigned_to_agent_id: str | None = None
    assigned_to_user_id: str | None = None
    department_id: str | None = None
    status: str
    priority: str
    deadline: datetime | None = None
    output: str | None = None
    error_details: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Enriched presentation fields
    project_name: str | None = None
    assigned_agent_name: str | None = None
    assigned_agent_role: str | None = None
    department_name: str | None = None
    dependencies: list[TaskDependencyResponse] = []
    subtasks_count: int = 0


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    items: list[TaskResponse]
    total: int


class KanbanColumn(BaseModel):
    """Schema representing a Kanban board column."""

    id: str = Field(..., description="Column identifier, e.g. READY, IN_PROGRESS")
    title: str = Field(..., description="Display title for the column")
    statuses: list[str] = Field(..., description="Task statuses included in this column")
    color: str = Field(default="zinc", description="Color token for visual branding")
    task_count: int = Field(default=0, description="Number of tasks currently in column")


class BoardSummaryStats(BaseModel):
    """Summary statistics for tasks on the project board."""

    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    waiting_tasks: int = 0
    blocked_tasks: int = 0
    completion_rate: float = 0.0


class ProjectBoardResponse(BaseModel):
    """Authoritative response representing a project Kanban board."""

    project: ProjectResponse
    columns: list[KanbanColumn]
    tasks: list[TaskResponse]
    allowed_transitions: dict[str, list[str]]
    summary: BoardSummaryStats
