"""create artifacts and documents adhering to docs/Phases.md Section 22 and docs/Memory.md Section 31

Revision ID: 0016_create_artifacts
Revises: 0015_create_file_tracking
Create Date: 2026-09-24 21:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016_create_artifacts"
down_revision: str | Sequence[str] | None = "0015_create_file_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include artifacts table."""
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("created_by_agent_id", sa.String(length=36), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("creator_name", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("artifact_type", sa.String(length=32), server_default="DOCUMENT", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("parent_artifact_id", sa.String(length=36), nullable=True),
        sa.Column("location", sa.String(length=1024), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False),
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
            name="fk_artifacts_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_artifacts_project_id_projects",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_artifacts_task_id_tasks",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_agent_id"],
            ["agents.id"],
            name="fk_artifacts_created_by_agent_id_agents",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_artifacts_created_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["parent_artifact_id"],
            ["artifacts.id"],
            name="fk_artifacts_parent_artifact_id_artifacts",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_artifacts"),
    )
    op.create_index("ix_artifacts_company_id", "artifacts", ["company_id"], unique=False)
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"], unique=False)
    op.create_index("ix_artifacts_task_id", "artifacts", ["task_id"], unique=False)
    op.create_index(
        "ix_artifacts_created_by_agent_id", "artifacts", ["created_by_agent_id"], unique=False
    )
    op.create_index(
        "ix_artifacts_created_by_user_id", "artifacts", ["created_by_user_id"], unique=False
    )
    op.create_index("ix_artifacts_name", "artifacts", ["name"], unique=False)
    op.create_index("ix_artifacts_artifact_type", "artifacts", ["artifact_type"], unique=False)
    op.create_index(
        "ix_artifacts_parent_artifact_id", "artifacts", ["parent_artifact_id"], unique=False
    )
    op.create_index("ix_artifacts_created_at", "artifacts", ["created_at"], unique=False)

    op.create_index(
        "ix_artifacts_company_type", "artifacts", ["company_id", "artifact_type"], unique=False
    )
    op.create_index(
        "ix_artifacts_company_project", "artifacts", ["company_id", "project_id"], unique=False
    )
    op.create_index(
        "ix_artifacts_company_task", "artifacts", ["company_id", "task_id"], unique=False
    )
    op.create_index(
        "ix_artifacts_company_parent",
        "artifacts",
        ["company_id", "parent_artifact_id"],
        unique=False,
    )
    op.create_index(
        "ix_artifacts_company_created", "artifacts", ["company_id", "created_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema to drop artifacts table."""
    op.drop_index("ix_artifacts_company_created", table_name="artifacts")
    op.drop_index("ix_artifacts_company_parent", table_name="artifacts")
    op.drop_index("ix_artifacts_company_task", table_name="artifacts")
    op.drop_index("ix_artifacts_company_project", table_name="artifacts")
    op.drop_index("ix_artifacts_company_type", table_name="artifacts")

    op.drop_index("ix_artifacts_created_at", table_name="artifacts")
    op.drop_index("ix_artifacts_parent_artifact_id", table_name="artifacts")
    op.drop_index("ix_artifacts_artifact_type", table_name="artifacts")
    op.drop_index("ix_artifacts_name", table_name="artifacts")
    op.drop_index("ix_artifacts_created_by_user_id", table_name="artifacts")
    op.drop_index("ix_artifacts_created_by_agent_id", table_name="artifacts")
    op.drop_index("ix_artifacts_task_id", table_name="artifacts")
    op.drop_index("ix_artifacts_project_id", table_name="artifacts")
    op.drop_index("ix_artifacts_company_id", table_name="artifacts")
    op.drop_table("artifacts")
