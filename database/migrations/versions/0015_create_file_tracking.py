"""create engineering file tracking adhering to docs/Phases.md Section 20 and docs/Memory.md Section 61

Revision ID: 0015_create_file_tracking
Revises: 0014_create_errors
Create Date: 2026-09-24 19:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015_create_file_tracking"
down_revision: str | Sequence[str] | None = "0014_create_errors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include task_engineering_contexts and task_file_changes tables."""
    # 1. task_engineering_contexts
    op.create_table(
        "task_engineering_contexts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("repository", sa.String(length=255), server_default="main", nullable=False),
        sa.Column("branch", sa.String(length=255), server_default="main", nullable=False),
        sa.Column("pull_request_number", sa.String(length=64), nullable=True),
        sa.Column("pull_request_url", sa.String(length=512), nullable=True),
        sa.Column("pull_request_title", sa.String(length=255), nullable=True),
        sa.Column("commit_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("test_status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("test_output_summary", sa.Text(), nullable=True),
        sa.Column(
            "verification_state", sa.String(length=32), server_default="PENDING", nullable=False
        ),
        sa.Column("verification_notes", sa.Text(), nullable=True),
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
            name="fk_task_engineering_contexts_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_task_engineering_contexts_task_id_tasks",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_task_engineering_contexts"),
    )
    op.create_index(
        "ix_task_engineering_contexts_company_id",
        "task_engineering_contexts",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_task_engineering_contexts_task_id",
        "task_engineering_contexts",
        ["task_id"],
        unique=True,
    )
    op.create_index(
        "ix_task_engineering_contexts_branch",
        "task_engineering_contexts",
        ["branch"],
        unique=False,
    )
    op.create_index(
        "ix_task_engineering_contexts_test_status",
        "task_engineering_contexts",
        ["test_status"],
        unique=False,
    )
    op.create_index(
        "ix_task_engineering_contexts_verification_state",
        "task_engineering_contexts",
        ["verification_state"],
        unique=False,
    )
    op.create_index(
        "ix_task_eng_company_task",
        "task_engineering_contexts",
        ["company_id", "task_id"],
        unique=False,
    )

    # 2. task_file_changes
    op.create_table(
        "task_file_changes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("repository", sa.String(length=255), server_default="main", nullable=False),
        sa.Column("branch", sa.String(length=255), server_default="main", nullable=False),
        sa.Column("agent_id", sa.String(length=36), nullable=True),
        sa.Column("agent_name", sa.String(length=255), nullable=False),
        sa.Column("change_type", sa.String(length=32), server_default="MODIFIED", nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("commit_hash", sa.String(length=64), nullable=True),
        sa.Column("commit_message", sa.String(length=255), nullable=True),
        sa.Column("additions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("deletions", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "last_modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_task_file_changes_agent_id_agents",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_task_file_changes_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_task_file_changes_task_id_tasks",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_task_file_changes"),
    )
    op.create_index(
        "ix_task_file_changes_company_id", "task_file_changes", ["company_id"], unique=False
    )
    op.create_index("ix_task_file_changes_task_id", "task_file_changes", ["task_id"], unique=False)
    op.create_index(
        "ix_task_file_changes_file_path", "task_file_changes", ["file_path"], unique=False
    )
    op.create_index("ix_task_file_changes_branch", "task_file_changes", ["branch"], unique=False)
    op.create_index(
        "ix_task_file_changes_agent_id", "task_file_changes", ["agent_id"], unique=False
    )
    op.create_index(
        "ix_task_file_changes_company_task",
        "task_file_changes",
        ["company_id", "task_id"],
        unique=False,
    )
    op.create_index(
        "ix_task_file_changes_company_file",
        "task_file_changes",
        ["company_id", "file_path"],
        unique=False,
    )
    op.create_index(
        "ix_task_file_changes_company_branch",
        "task_file_changes",
        ["company_id", "branch"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema to drop task_file_changes and task_engineering_contexts tables."""
    op.drop_index("ix_task_file_changes_company_branch", table_name="task_file_changes")
    op.drop_index("ix_task_file_changes_company_file", table_name="task_file_changes")
    op.drop_index("ix_task_file_changes_company_task", table_name="task_file_changes")
    op.drop_index("ix_task_file_changes_agent_id", table_name="task_file_changes")
    op.drop_index("ix_task_file_changes_branch", table_name="task_file_changes")
    op.drop_index("ix_task_file_changes_file_path", table_name="task_file_changes")
    op.drop_index("ix_task_file_changes_task_id", table_name="task_file_changes")
    op.drop_index("ix_task_file_changes_company_id", table_name="task_file_changes")
    op.drop_table("task_file_changes")

    op.drop_index("ix_task_eng_company_task", table_name="task_engineering_contexts")
    op.drop_index(
        "ix_task_engineering_contexts_verification_state", table_name="task_engineering_contexts"
    )
    op.drop_index(
        "ix_task_engineering_contexts_test_status", table_name="task_engineering_contexts"
    )
    op.drop_index("ix_task_engineering_contexts_branch", table_name="task_engineering_contexts")
    op.drop_index("ix_task_engineering_contexts_task_id", table_name="task_engineering_contexts")
    op.drop_index("ix_task_engineering_contexts_company_id", table_name="task_engineering_contexts")
    op.drop_table("task_engineering_contexts")
