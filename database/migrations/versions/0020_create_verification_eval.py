"""create verification and evaluation tables adhering to docs/Phases.md Section 26, docs/Architecture.md Sections 71-72, and docs/Rules.md Sections 17 & 146

Revision ID: 0020_create_verification_eval
Revises: 0019_create_voice_interface
Create Date: 2026-09-25 02:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020_create_verification_eval"
down_revision: str | Sequence[str] | None = "0019_create_voice_interface"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include verification_runs, evaluation_criterion_scores, and evaluation_benchmarks tables."""
    # 1. Create verification_runs table
    op.create_table(
        "verification_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("target_type", sa.String(length=32), server_default="TASK", nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("agent_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="RUNNING", nullable=False),
        sa.Column("overall_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column(
            "pipeline_stage",
            sa.String(length=64),
            server_default="SCHEMA_VALIDATION",
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_verification_runs_company_id", "verification_runs", ["company_id"], unique=False
    )
    op.create_index(
        "ix_verification_runs_target_type", "verification_runs", ["target_type"], unique=False
    )
    op.create_index(
        "ix_verification_runs_target_id", "verification_runs", ["target_id"], unique=False
    )
    op.create_index(
        "ix_verification_runs_agent_id", "verification_runs", ["agent_id"], unique=False
    )
    op.create_index("ix_verification_runs_status", "verification_runs", ["status"], unique=False)
    op.create_index(
        "ix_verification_runs_created_at", "verification_runs", ["created_at"], unique=False
    )
    op.create_index(
        "ix_verification_runs_company_target",
        "verification_runs",
        ["company_id", "target_id"],
        unique=False,
    )

    # 2. Create evaluation_criterion_scores table
    op.create_table(
        "evaluation_criterion_scores",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("criterion", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), server_default="100.0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="PASSED", nullable=False),
        sa.Column("details", sa.Text(), server_default="", nullable=False),
        sa.Column("evidence", sa.JSON(), server_default="{}", nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["verification_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evaluation_criterion_scores_run_id",
        "evaluation_criterion_scores",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        "ix_evaluation_criterion_scores_criterion",
        "evaluation_criterion_scores",
        ["criterion"],
        unique=False,
    )

    # 3. Create evaluation_benchmarks table
    op.create_table(
        "evaluation_benchmarks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("task_prompt", sa.Text(), nullable=False),
        sa.Column("target_role", sa.String(length=64), server_default="GENERAL", nullable=False),
        sa.Column("expected_output_pattern", sa.Text(), nullable=True),
        sa.Column("min_passing_score", sa.Float(), server_default="75.0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evaluation_benchmarks_company_id", "evaluation_benchmarks", ["company_id"], unique=False
    )
    op.create_index(
        "ix_evaluation_benchmarks_category", "evaluation_benchmarks", ["category"], unique=False
    )
    op.create_index(
        "ix_evaluation_benchmarks_company_cat",
        "evaluation_benchmarks",
        ["company_id", "category"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema removing evaluation and verification tables."""
    op.drop_index("ix_evaluation_benchmarks_company_cat", table_name="evaluation_benchmarks")
    op.drop_index("ix_evaluation_benchmarks_category", table_name="evaluation_benchmarks")
    op.drop_index("ix_evaluation_benchmarks_company_id", table_name="evaluation_benchmarks")
    op.drop_table("evaluation_benchmarks")

    op.drop_index(
        "ix_evaluation_criterion_scores_criterion", table_name="evaluation_criterion_scores"
    )
    op.drop_index("ix_evaluation_criterion_scores_run_id", table_name="evaluation_criterion_scores")
    op.drop_table("evaluation_criterion_scores")

    op.drop_index("ix_verification_runs_company_target", table_name="verification_runs")
    op.drop_index("ix_verification_runs_created_at", table_name="verification_runs")
    op.drop_index("ix_verification_runs_status", table_name="verification_runs")
    op.drop_index("ix_verification_runs_agent_id", table_name="verification_runs")
    op.drop_index("ix_verification_runs_target_id", table_name="verification_runs")
    op.drop_index("ix_verification_runs_target_type", table_name="verification_runs")
    op.drop_index("ix_verification_runs_company_id", table_name="verification_runs")
    op.drop_table("verification_runs")
