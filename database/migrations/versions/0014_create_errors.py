"""create errors adhering to docs/Phases.md Section 19 and docs/Memory.md Section 20

Revision ID: 0014_create_errors
Revises: 0013_create_agent_presence
Create Date: 2026-09-24 19:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014_create_errors"
down_revision: str | Sequence[str] | None = "0013_create_agent_presence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include errors table."""
    op.create_table(
        "errors",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=32), server_default="MEDIUM", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="OPEN", nullable=False),
        sa.Column("detected_by", sa.String(length=255), nullable=False),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("investigated_by", sa.String(length=255), nullable=True),
        sa.Column("resolved_by", sa.String(length=255), nullable=True),
        sa.Column("verified_by", sa.String(length=255), nullable=True),
        sa.Column("assigned_agent_id", sa.String(length=36), nullable=True),
        sa.Column("assigned_user_id", sa.String(length=36), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("evidence", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_errors_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_errors_project_id_projects",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_errors_task_id_tasks",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_agent_id"],
            ["agents.id"],
            name="fk_errors_assigned_agent_id_agents",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_user_id"],
            ["users.id"],
            name="fk_errors_assigned_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_errors"),
    )
    op.create_index("ix_errors_company_id", "errors", ["company_id"], unique=False)
    op.create_index("ix_errors_project_id", "errors", ["project_id"], unique=False)
    op.create_index("ix_errors_task_id", "errors", ["task_id"], unique=False)
    op.create_index("ix_errors_severity", "errors", ["severity"], unique=False)
    op.create_index("ix_errors_status", "errors", ["status"], unique=False)
    op.create_index("ix_errors_assigned_agent_id", "errors", ["assigned_agent_id"], unique=False)
    op.create_index("ix_errors_assigned_user_id", "errors", ["assigned_user_id"], unique=False)
    op.create_index("ix_errors_created_at", "errors", ["created_at"], unique=False)
    op.create_index("ix_errors_company_status", "errors", ["company_id", "status"], unique=False)
    op.create_index(
        "ix_errors_company_severity", "errors", ["company_id", "severity"], unique=False
    )
    op.create_index(
        "ix_errors_company_created", "errors", ["company_id", "created_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema to drop errors table."""
    op.drop_index("ix_errors_company_created", table_name="errors")
    op.drop_index("ix_errors_company_severity", table_name="errors")
    op.drop_index("ix_errors_company_status", table_name="errors")
    op.drop_index("ix_errors_created_at", table_name="errors")
    op.drop_index("ix_errors_assigned_user_id", table_name="errors")
    op.drop_index("ix_errors_assigned_agent_id", table_name="errors")
    op.drop_index("ix_errors_status", table_name="errors")
    op.drop_index("ix_errors_severity", table_name="errors")
    op.drop_index("ix_errors_task_id", table_name="errors")
    op.drop_index("ix_errors_project_id", table_name="errors")
    op.drop_index("ix_errors_company_id", table_name="errors")
    op.drop_table("errors")
