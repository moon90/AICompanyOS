"""create activity events adhering to docs/Phases.md Section 17

Revision ID: 0012_create_activity_events
Revises: 0011_create_decision_memory
Create Date: 2026-09-23 05:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_create_activity_events"
down_revision: str | Sequence[str] | None = "0011_create_decision_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include activity_events table."""
    op.create_table(
        "activity_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("actor_type", sa.String(length=32), server_default="system", nullable=False),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_activity_events_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_activity_events_project_id_projects",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_activity_events_task_id_tasks",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_activity_events"),
    )
    op.create_index(
        "ix_activity_events_company_id",
        "activity_events",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_activity_events_project_id",
        "activity_events",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_activity_events_task_id",
        "activity_events",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_activity_events_actor_id",
        "activity_events",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_activity_events_company_created",
        "activity_events",
        ["company_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_activity_events_project_created",
        "activity_events",
        ["project_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_activity_events_task_created",
        "activity_events",
        ["task_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_activity_events_actor",
        "activity_events",
        ["company_id", "actor_type", "actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_activity_events_event_type",
        "activity_events",
        ["company_id", "event_type"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema to drop activity_events table."""
    op.drop_index("ix_activity_events_event_type", table_name="activity_events")
    op.drop_index("ix_activity_events_actor", table_name="activity_events")
    op.drop_index("ix_activity_events_task_created", table_name="activity_events")
    op.drop_index("ix_activity_events_project_created", table_name="activity_events")
    op.drop_index("ix_activity_events_company_created", table_name="activity_events")
    op.drop_index("ix_activity_events_actor_id", table_name="activity_events")
    op.drop_index("ix_activity_events_task_id", table_name="activity_events")
    op.drop_index("ix_activity_events_project_id", table_name="activity_events")
    op.drop_index("ix_activity_events_company_id", table_name="activity_events")
    op.drop_table("activity_events")
