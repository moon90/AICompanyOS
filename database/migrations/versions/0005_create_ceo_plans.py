"""create ceo plans

Revision ID: 0005_create_ceo_plans
Revises: 0004_create_agent_registry
Create Date: 2026-09-21 03:33:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_create_ceo_plans"
down_revision: str | Sequence[str] | None = "0004_create_agent_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ceo_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("ceo_agent_id", sa.String(length=36), nullable=True),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("requested_outcome", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=32), server_default="medium", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="proposed", nullable=False),
        sa.Column("reasoning_summary", sa.Text(), nullable=False),
        sa.Column("context_snapshot", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("plan_steps", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("delegation_proposals", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("approval_requirements", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("risks", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("assumptions", sa.JSON(), server_default="[]", nullable=False),
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
        sa.ForeignKeyConstraint(["ceo_agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ceo_plans_ceo_agent_id"), "ceo_plans", ["ceo_agent_id"], unique=False)
    op.create_index(
        "ix_ceo_plans_company_created", "ceo_plans", ["company_id", "created_at"], unique=False
    )
    op.create_index(op.f("ix_ceo_plans_company_id"), "ceo_plans", ["company_id"], unique=False)
    op.create_index(
        "ix_ceo_plans_company_status", "ceo_plans", ["company_id", "status"], unique=False
    )
    op.create_index(op.f("ix_ceo_plans_user_id"), "ceo_plans", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_ceo_plans_user_id"), table_name="ceo_plans")
    op.drop_index("ix_ceo_plans_company_status", table_name="ceo_plans")
    op.drop_index(op.f("ix_ceo_plans_company_id"), table_name="ceo_plans")
    op.drop_index("ix_ceo_plans_company_created", table_name="ceo_plans")
    op.drop_index(op.f("ix_ceo_plans_ceo_agent_id"), table_name="ceo_plans")
    op.drop_table("ceo_plans")
