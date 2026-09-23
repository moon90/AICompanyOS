"""create agent presence adhering to docs/Phases.md Section 18 and docs/Memory.md Section 20

Revision ID: 0013_create_agent_presence
Revises: 0012_create_activity_events
Create Date: 2026-09-23 23:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013_create_agent_presence"
down_revision: str | Sequence[str] | None = "0012_create_activity_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include agent_presences table."""
    op.create_table(
        "agent_presences",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("agent_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="IDLE", nullable=False),
        sa.Column("current_task_id", sa.String(length=36), nullable=True),
        sa.Column("current_project_id", sa.String(length=36), nullable=True),
        sa.Column("current_activity", sa.String(length=255), nullable=True),
        sa.Column("current_step", sa.String(length=255), nullable=True),
        sa.Column(
            "last_heartbeat_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("details", sa.JSON(), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_agent_presences_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_agent_presences_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["current_task_id"],
            ["tasks.id"],
            name="fk_agent_presences_current_task_id_tasks",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["current_project_id"],
            ["projects.id"],
            name="fk_agent_presences_current_project_id_projects",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_agent_presences"),
    )
    op.create_index(
        "ix_agent_presences_agent_id",
        "agent_presences",
        ["agent_id"],
        unique=True,
    )
    op.create_index(
        "ix_agent_presences_company_id",
        "agent_presences",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_presences_current_task_id",
        "agent_presences",
        ["current_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_presences_current_project_id",
        "agent_presences",
        ["current_project_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_presence_company_status",
        "agent_presences",
        ["company_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_agent_presence_company_heartbeat",
        "agent_presences",
        ["company_id", "last_heartbeat_at"],
        unique=False,
    )

    # Initial presence backfill for existing agents
    op.execute(
        sa.text(
            """
            INSERT INTO agent_presences (id, agent_id, company_id, status, current_activity, last_heartbeat_at, updated_at, details)
            SELECT
                gen_random_uuid()::text,
                id,
                company_id,
                CASE WHEN status = 'active' THEN 'IDLE' ELSE 'OFFLINE' END,
                NULL,
                now(),
                now(),
                '{}'::json
            FROM agents
            ON CONFLICT (agent_id) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema to drop agent_presences table."""
    op.drop_index("ix_agent_presence_company_heartbeat", table_name="agent_presences")
    op.drop_index("ix_agent_presence_company_status", table_name="agent_presences")
    op.drop_index("ix_agent_presences_current_project_id", table_name="agent_presences")
    op.drop_index("ix_agent_presences_current_task_id", table_name="agent_presences")
    op.drop_index("ix_agent_presences_company_id", table_name="agent_presences")
    op.drop_index("ix_agent_presences_agent_id", table_name="agent_presences")
    op.drop_table("agent_presences")
