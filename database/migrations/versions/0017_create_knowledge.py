"""create company knowledge adhering to docs/Phases.md Section 23 and docs/Memory.md Sections 31-39

Revision ID: 0017_create_knowledge
Revises: 0016_create_artifacts
Create Date: 2026-09-24 22:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017_create_knowledge"
down_revision: str | Sequence[str] | None = "0016_create_artifacts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include company_knowledge table."""
    op.create_table(
        "company_knowledge",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("task_id", sa.String(length=36), nullable=True),
        sa.Column("decision_id", sa.String(length=36), nullable=True),
        sa.Column("artifact_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), server_default="GENERAL", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=64), server_default="USER", nullable=False),
        sa.Column("source_uri", sa.String(length=1024), nullable=True),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.String(length=32), server_default="HIGH", nullable=False),
        sa.Column("tags", sa.JSON(), server_default="[]", nullable=False),
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
            name="fk_company_knowledge_company_id_companies",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_company_knowledge_project_id_projects",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_company_knowledge_task_id_tasks",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["decision_id"],
            ["company_decisions.id"],
            name="fk_company_knowledge_decision_id_company_decisions",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_id"],
            ["artifacts.id"],
            name="fk_company_knowledge_artifact_id_artifacts",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_company_knowledge"),
    )
    op.create_index(
        "ix_company_knowledge_company_id", "company_knowledge", ["company_id"], unique=False
    )
    op.create_index(
        "ix_company_knowledge_project_id", "company_knowledge", ["project_id"], unique=False
    )
    op.create_index("ix_company_knowledge_task_id", "company_knowledge", ["task_id"], unique=False)
    op.create_index(
        "ix_company_knowledge_decision_id", "company_knowledge", ["decision_id"], unique=False
    )
    op.create_index(
        "ix_company_knowledge_artifact_id", "company_knowledge", ["artifact_id"], unique=False
    )
    op.create_index("ix_company_knowledge_title", "company_knowledge", ["title"], unique=False)
    op.create_index(
        "ix_company_knowledge_category", "company_knowledge", ["category"], unique=False
    )
    op.create_index(
        "ix_company_knowledge_created_at", "company_knowledge", ["created_at"], unique=False
    )

    op.create_index(
        "ix_company_knowledge_company_cat",
        "company_knowledge",
        ["company_id", "category"],
        unique=False,
    )
    op.create_index(
        "ix_company_knowledge_company_project",
        "company_knowledge",
        ["company_id", "project_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_knowledge_company_created",
        "company_knowledge",
        ["company_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema to drop company_knowledge table."""
    op.drop_index("ix_company_knowledge_company_created", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_company_project", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_company_cat", table_name="company_knowledge")

    op.drop_index("ix_company_knowledge_created_at", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_category", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_title", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_artifact_id", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_decision_id", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_task_id", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_project_id", table_name="company_knowledge")
    op.drop_index("ix_company_knowledge_company_id", table_name="company_knowledge")
    op.drop_table("company_knowledge")
