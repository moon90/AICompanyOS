"""create tool system adhering to docs/Phases.md Section 13 and docs/Architecture.md Section 30

Revision ID: 0009_create_tool_system
Revises: 0008_create_execution_system
Create Date: 2026-09-21 07:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009_create_tool_system"
down_revision: str | Sequence[str] | None = "0008_create_execution_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include tool_execution_records."""
    op.create_table(
        "tool_execution_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("agent_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("execution_id", sa.String(length=36), nullable=True),
        sa.Column("tool_name", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("risk_level", sa.String(length=16), server_default="LOW", nullable=False),
        sa.Column("requires_approval", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="SUCCESS", nullable=False),
        sa.Column("input_params", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("output_data", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_tool_execution_records_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_tool_execution_records_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_tool_execution_records_task_id_tasks",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["execution_records.id"],
            name="fk_tool_execution_records_execution_id_execution_records",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tool_execution_records"),
    )
    op.create_index(
        "ix_tool_execution_records_company_id",
        "tool_execution_records",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_tool_execution_records_agent_id",
        "tool_execution_records",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_tool_execution_records_task_id",
        "tool_execution_records",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_tool_execution_records_execution_id",
        "tool_execution_records",
        ["execution_id"],
        unique=False,
    )
    op.create_index(
        "ix_tool_execution_records_tool_name",
        "tool_execution_records",
        ["tool_name"],
        unique=False,
    )
    op.create_index(
        "ix_tool_execution_records_company_created",
        "tool_execution_records",
        ["company_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_tool_execution_records_agent_created",
        "tool_execution_records",
        ["agent_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_tool_execution_records_task_created",
        "tool_execution_records",
        ["task_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema removing tool_execution_records."""
    op.drop_index("ix_tool_execution_records_task_created", table_name="tool_execution_records")
    op.drop_index("ix_tool_execution_records_agent_created", table_name="tool_execution_records")
    op.drop_index("ix_tool_execution_records_company_created", table_name="tool_execution_records")
    op.drop_index("ix_tool_execution_records_tool_name", table_name="tool_execution_records")
    op.drop_index("ix_tool_execution_records_execution_id", table_name="tool_execution_records")
    op.drop_index("ix_tool_execution_records_task_id", table_name="tool_execution_records")
    op.drop_index("ix_tool_execution_records_agent_id", table_name="tool_execution_records")
    op.drop_index("ix_tool_execution_records_company_id", table_name="tool_execution_records")
    op.drop_table("tool_execution_records")
