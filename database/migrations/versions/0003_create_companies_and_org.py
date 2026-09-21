"""Create companies, company_members, and departments tables.

Revision ID: 0003_create_companies_departments_members
Revises: 0002_create_users_and_sessions
Create Date: 2026-09-21 03:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_create_companies_and_org"
down_revision: str | None = "0002_create_users_and_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create companies, company_members, and departments tables with indexes and constraints."""
    # 1. Create companies table
    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mission", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Create company_members table
    op.create_table(
        "company_members",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=32), server_default="owner", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "user_id", name="uq_company_member_user"),
    )
    op.create_index(
        op.f("ix_company_members_company_id"), "company_members", ["company_id"], unique=False
    )
    op.create_index(
        op.f("ix_company_members_user_id"), "company_members", ["user_id"], unique=False
    )
    op.create_index(
        "ix_company_members_company_role", "company_members", ["company_id", "role"], unique=False
    )

    # 3. Create departments table
    op.create_table(
        "departments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("lead_role", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
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
        sa.UniqueConstraint("company_id", "code", name="uq_company_department_code"),
    )
    op.create_index(op.f("ix_departments_company_id"), "departments", ["company_id"], unique=False)
    op.create_index(
        "ix_departments_company_status", "departments", ["company_id", "status"], unique=False
    )


def downgrade() -> None:
    """Drop departments, company_members, and companies tables."""
    op.drop_index("ix_departments_company_status", table_name="departments")
    op.drop_index(op.f("ix_departments_company_id"), table_name="departments")
    op.drop_table("departments")

    op.drop_index("ix_company_members_company_role", table_name="company_members")
    op.drop_index(op.f("ix_company_members_user_id"), table_name="company_members")
    op.drop_index(op.f("ix_company_members_company_id"), table_name="company_members")
    op.drop_table("company_members")

    op.drop_table("companies")
