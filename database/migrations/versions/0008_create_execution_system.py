"""create execution system adhering to docs/Phases.md Section 12

Revision ID: 0008_create_execution_system
Revises: 0007_create_delegation_system
Create Date: 2026-09-21 07:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_create_execution_system"
down_revision: str | Sequence[str] | None = "0007_create_delegation_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include execution_records."""
    op.create_table(
        "execution_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("agent_id", sa.String(length=36), nullable=False),
        sa.Column("executed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="RUNNING", nullable=False),
        sa.Column("step_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duration_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tokens_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("estimated_cost", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("deliverable", sa.Text(), nullable=True),
        sa.Column("steps_json", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_execution_records_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_execution_records_task_id_tasks",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_execution_records_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["executed_by_user_id"],
            ["users.id"],
            name="fk_execution_records_executed_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_execution_records"),
    )
    op.create_index(
        "ix_execution_records_company_id",
        "execution_records",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_records_task_id",
        "execution_records",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_records_agent_id",
        "execution_records",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_records_executed_by_user_id",
        "execution_records",
        ["executed_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_records_company_task",
        "execution_records",
        ["company_id", "task_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_records_company_agent",
        "execution_records",
        ["company_id", "agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_execution_records_company_created",
        "execution_records",
        ["company_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema removing execution_records."""
    op.drop_index("ix_execution_records_company_created", table_name="execution_records")
    op.drop_index("ix_execution_records_company_agent", table_name="execution_records")
    op.drop_index("ix_execution_records_company_task", table_name="execution_records")
    op.drop_index("ix_execution_records_executed_by_user_id", table_name="execution_records")
    op.drop_index("ix_execution_records_agent_id", table_name="execution_records")
    op.drop_index("ix_execution_records_task_id", table_name="execution_records")
    op.drop_index("ix_execution_records_company_id", table_name="execution_records")
    op.drop_table("execution_records")
