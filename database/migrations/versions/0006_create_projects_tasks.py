"""create projects and tasks

Revision ID: 0006_create_projects_tasks
Revises: 0005_create_ceo_plans
Create Date: 2026-09-21 04:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_create_projects_tasks"
down_revision: str | Sequence[str] | None = "0005_create_ceo_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include projects, tasks, and task_dependencies."""
    # 1. Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="PLANNED", nullable=False),
        sa.Column("priority", sa.String(length=32), server_default="medium", nullable=False),
        sa.Column("owner_user_id", sa.String(length=36), nullable=True),
        sa.Column("owner_agent_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_company_id"), "projects", ["company_id"], unique=False)
    op.create_index(
        op.f("ix_projects_owner_agent_id"), "projects", ["owner_agent_id"], unique=False
    )
    op.create_index(op.f("ix_projects_owner_user_id"), "projects", ["owner_user_id"], unique=False)
    op.create_index(
        "ix_projects_company_status", "projects", ["company_id", "status"], unique=False
    )
    op.create_index(
        "ix_projects_company_created", "projects", ["company_id", "created_at"], unique=False
    )

    # 2. Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("parent_task_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("created_by_agent_id", sa.String(length=36), nullable=True),
        sa.Column("assigned_to_agent_id", sa.String(length=36), nullable=True),
        sa.Column("assigned_to_user_id", sa.String(length=36), nullable=True),
        sa.Column("department_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="CREATED", nullable=False),
        sa.Column("priority", sa.String(length=32), server_default="medium", nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to_agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_company_id"), "tasks", ["company_id"], unique=False)
    op.create_index(op.f("ix_tasks_project_id"), "tasks", ["project_id"], unique=False)
    op.create_index(op.f("ix_tasks_parent_task_id"), "tasks", ["parent_task_id"], unique=False)
    op.create_index(
        op.f("ix_tasks_created_by_user_id"), "tasks", ["created_by_user_id"], unique=False
    )
    op.create_index(
        op.f("ix_tasks_created_by_agent_id"), "tasks", ["created_by_agent_id"], unique=False
    )
    op.create_index(
        op.f("ix_tasks_assigned_to_agent_id"), "tasks", ["assigned_to_agent_id"], unique=False
    )
    op.create_index(
        op.f("ix_tasks_assigned_to_user_id"), "tasks", ["assigned_to_user_id"], unique=False
    )
    op.create_index(op.f("ix_tasks_department_id"), "tasks", ["department_id"], unique=False)
    op.create_index("ix_tasks_company_status", "tasks", ["company_id", "status"], unique=False)
    op.create_index("ix_tasks_company_project", "tasks", ["company_id", "project_id"], unique=False)
    op.create_index(
        "ix_tasks_company_assigned", "tasks", ["company_id", "assigned_to_agent_id"], unique=False
    )
    op.create_index("ix_tasks_company_created", "tasks", ["company_id", "created_at"], unique=False)

    # 3. Create task_dependencies table
    op.create_table(
        "task_dependencies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("depends_on_task_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["depends_on_task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependencies_pair"),
    )
    op.create_index(
        op.f("ix_task_dependencies_company_id"), "task_dependencies", ["company_id"], unique=False
    )
    op.create_index(
        op.f("ix_task_dependencies_task_id"), "task_dependencies", ["task_id"], unique=False
    )
    op.create_index(
        op.f("ix_task_dependencies_depends_on_task_id"),
        "task_dependencies",
        ["depends_on_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_task_dependencies_company", "task_dependencies", ["company_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema removing task_dependencies, tasks, and projects."""
    op.drop_table("task_dependencies")
    op.drop_table("tasks")
    op.drop_table("projects")
