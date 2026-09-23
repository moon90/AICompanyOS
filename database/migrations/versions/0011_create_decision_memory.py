"""create decision memory adhering to docs/Phases.md Section 15 and docs/Memory.md Sections 33-34

Revision ID: 0011_create_decision_memory
Revises: 0010_create_approval_system
Create Date: 2026-09-23 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011_create_decision_memory"
down_revision: str | Sequence[str] | None = "0010_create_approval_system"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include company_decisions table."""
    op.create_table(
        "company_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="ACTIVE", nullable=False),
        sa.Column("decided_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("decided_by_agent_id", sa.String(length=36), nullable=True),
        sa.Column("superseded_by_decision_id", sa.String(length=36), nullable=True),
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
            name="fk_company_decisions_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_company_decisions_project_id_projects",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_company_decisions_task_id_tasks",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_user_id"],
            ["users.id"],
            name="fk_company_decisions_decided_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_agent_id"],
            ["agents.id"],
            name="fk_company_decisions_decided_by_agent_id_agents",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_decision_id"],
            ["company_decisions.id"],
            name="fk_company_decisions_superseded_by_decisions",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_company_decisions"),
    )
    op.create_index(
        "ix_company_decisions_company_id",
        "company_decisions",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_decisions_project_id",
        "company_decisions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_decisions_task_id",
        "company_decisions",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_decisions_decided_by_user_id",
        "company_decisions",
        ["decided_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_decisions_decided_by_agent_id",
        "company_decisions",
        ["decided_by_agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_decisions_superseded_by_decision_id",
        "company_decisions",
        ["superseded_by_decision_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_decisions_company_status",
        "company_decisions",
        ["company_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_company_decisions_company_created",
        "company_decisions",
        ["company_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema removing company_decisions."""
    op.drop_index("ix_company_decisions_company_created", table_name="company_decisions")
    op.drop_index("ix_company_decisions_company_status", table_name="company_decisions")
    op.drop_index("ix_company_decisions_superseded_by_decision_id", table_name="company_decisions")
    op.drop_index("ix_company_decisions_decided_by_agent_id", table_name="company_decisions")
    op.drop_index("ix_company_decisions_decided_by_user_id", table_name="company_decisions")
    op.drop_index("ix_company_decisions_task_id", table_name="company_decisions")
    op.drop_index("ix_company_decisions_project_id", table_name="company_decisions")
    op.drop_index("ix_company_decisions_company_id", table_name="company_decisions")
    op.drop_table("company_decisions")
