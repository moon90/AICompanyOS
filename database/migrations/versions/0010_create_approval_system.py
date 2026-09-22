"""create approval system adhering to docs/Phases.md Section 14 and docs/Architecture.md Sections 40-45

Revision ID: 0010_create_approval_system
Revises: 0009_create_tool_system
Create Date: 2026-09-22 23:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010_create_approval_system"
down_revision: str | Sequence[str] | None = "0009_create_tool_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include approval_requests."""
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("agent_id", sa.String(length=36), nullable=True),
        sa.Column("execution_id", sa.String(length=36), nullable=True),
        sa.Column("tool_execution_id", sa.String(length=36), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("risk_level", sa.String(length=16), server_default="MEDIUM", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("reviewed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_approval_requests_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_approval_requests_task_id_tasks",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_approval_requests_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["execution_records.id"],
            name="fk_approval_requests_execution_id_execution_records",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tool_execution_id"],
            ["tool_execution_records.id"],
            name="fk_approval_requests_tool_execution_id_tool_execution_records",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name="fk_approval_requests_reviewed_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_approval_requests"),
    )
    op.create_index(
        "ix_approval_requests_company_id",
        "approval_requests",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_task_id",
        "approval_requests",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_agent_id",
        "approval_requests",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_execution_id",
        "approval_requests",
        ["execution_id"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_tool_execution_id",
        "approval_requests",
        ["tool_execution_id"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_reviewed_by_user_id",
        "approval_requests",
        ["reviewed_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_company_status",
        "approval_requests",
        ["company_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_company_created",
        "approval_requests",
        ["company_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema removing approval_requests."""
    op.drop_index("ix_approval_requests_company_created", table_name="approval_requests")
    op.drop_index("ix_approval_requests_company_status", table_name="approval_requests")
    op.drop_index("ix_approval_requests_reviewed_by_user_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_tool_execution_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_execution_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_agent_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_task_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_company_id", table_name="approval_requests")
    op.drop_table("approval_requests")
