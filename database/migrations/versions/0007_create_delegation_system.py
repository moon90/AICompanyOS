"""create delegation system and link ceo plans to projects

Revision ID: 0007_create_delegation_system
Revises: 0006_create_projects_tasks
Create Date: 2026-09-21 05:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_create_delegation_system"
down_revision: str | Sequence[str] | None = "0006_create_projects_tasks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include delegation_records and ceo_plans.project_id."""
    # 1. Add project_id to ceo_plans
    op.add_column("ceo_plans", sa.Column("project_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_ceo_plans_project_id_projects",
        "ceo_plans",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_ceo_plans_project_id",
        "ceo_plans",
        ["project_id"],
        unique=False,
    )

    # 2. Create delegation_records table
    op.create_table(
        "delegation_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("delegated_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("delegated_by_agent_id", sa.String(length=36), nullable=True),
        sa.Column("delegated_to_agent_id", sa.String(length=36), nullable=False),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("depth", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_delegation_records_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_delegation_records_task_id_tasks",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["delegated_by_user_id"],
            ["users.id"],
            name="fk_delegation_records_delegated_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["delegated_by_agent_id"],
            ["agents.id"],
            name="fk_delegation_records_delegated_by_agent_id_agents",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["delegated_to_agent_id"],
            ["agents.id"],
            name="fk_delegation_records_delegated_to_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_delegation_records"),
    )

    # 3. Create indexes on delegation_records
    op.create_index(
        "ix_delegation_records_company_id",
        "delegation_records",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_delegation_records_task_id",
        "delegation_records",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_delegation_records_delegated_by_user_id",
        "delegation_records",
        ["delegated_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_delegation_records_delegated_by_agent_id",
        "delegation_records",
        ["delegated_by_agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_delegation_records_delegated_to_agent_id",
        "delegation_records",
        ["delegated_to_agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_delegation_records_company_task",
        "delegation_records",
        ["company_id", "task_id"],
        unique=False,
    )
    op.create_index(
        "ix_delegation_records_company_target",
        "delegation_records",
        ["company_id", "delegated_to_agent_id"],
        unique=False,
    )
    op.create_index(
        "ix_delegation_records_company_created",
        "delegation_records",
        ["company_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema to remove delegation_records and ceo_plans.project_id."""
    # 1. Drop delegation_records indexes and table
    op.drop_index("ix_delegation_records_company_created", table_name="delegation_records")
    op.drop_index("ix_delegation_records_company_target", table_name="delegation_records")
    op.drop_index("ix_delegation_records_company_task", table_name="delegation_records")
    op.drop_index("ix_delegation_records_delegated_to_agent_id", table_name="delegation_records")
    op.drop_index("ix_delegation_records_delegated_by_agent_id", table_name="delegation_records")
    op.drop_index("ix_delegation_records_delegated_by_user_id", table_name="delegation_records")
    op.drop_index("ix_delegation_records_task_id", table_name="delegation_records")
    op.drop_index("ix_delegation_records_company_id", table_name="delegation_records")
    op.drop_table("delegation_records")

    # 2. Drop ceo_plans.project_id index, FK, and column
    op.drop_index("ix_ceo_plans_project_id", table_name="ceo_plans")
    op.drop_constraint("fk_ceo_plans_project_id_projects", "ceo_plans", type_="foreignkey")
    op.drop_column("ceo_plans", "project_id")
