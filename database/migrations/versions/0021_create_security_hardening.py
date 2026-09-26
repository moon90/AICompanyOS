"""Create security hardening audit logs and agent policies tables.

Revision ID: 0021_create_security_hardening
Revises: 0020_create_verification_eval
Create Date: 2026-09-26 04:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0021_create_security_hardening"
down_revision: str | None = "0020_create_verification_eval"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create security_audit_logs table
    op.create_table(
        "security_audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("actor_type", sa.String(length=32), server_default="USER", nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), server_default="LOW", nullable=False),
        sa.Column("resource_type", sa.String(length=64), server_default="GENERAL", nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("action_details", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("is_blocked", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_security_audit_logs_company_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_security_audit_logs_user_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_security_audit_logs"),
    )
    op.create_index(
        "ix_security_audit_logs_company_id",
        "security_audit_logs",
        ["company_id"],
    )
    op.create_index(
        "ix_security_audit_logs_user_id",
        "security_audit_logs",
        ["user_id"],
    )
    op.create_index(
        "ix_security_audit_logs_event_type",
        "security_audit_logs",
        ["event_type"],
    )
    op.create_index(
        "ix_security_audit_logs_severity",
        "security_audit_logs",
        ["severity"],
    )
    op.create_index(
        "ix_security_audit_logs_created_at",
        "security_audit_logs",
        ["created_at"],
    )
    op.create_index(
        "ix_security_audit_logs_company_created",
        "security_audit_logs",
        ["company_id", "created_at"],
    )
    op.create_index(
        "ix_security_audit_logs_event_sev",
        "security_audit_logs",
        ["event_type", "severity"],
    )

    # 2. Create agent_security_policies table
    op.create_table(
        "agent_security_policies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("agent_id", sa.String(length=36), nullable=False),
        sa.Column("default_posture", sa.String(length=16), server_default="DENY", nullable=False),
        sa.Column("allowed_capabilities", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("denied_capabilities", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("rate_limit_rpm", sa.Integer(), server_default="60", nullable=False),
        sa.Column("max_daily_budget", sa.Float(), server_default="50.0", nullable=False),
        sa.Column(
            "can_execute_destructive_tools", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column(
            "requires_human_approval_for_tools", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column("is_quarantined", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("quarantine_reason", sa.Text(), nullable=True),
        sa.Column("quarantined_at", sa.DateTime(timezone=True), nullable=True),
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
            name="fk_agent_security_policies_company_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_agent_security_policies_agent_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_agent_security_policies"),
    )
    op.create_index(
        "ix_agent_security_policies_company_id",
        "agent_security_policies",
        ["company_id"],
    )
    op.create_index(
        "ix_agent_security_policies_agent_id",
        "agent_security_policies",
        ["agent_id"],
        unique=True,
    )
    op.create_index(
        "ix_agent_security_policies_company_agent",
        "agent_security_policies",
        ["company_id", "agent_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_security_policies_company_agent", table_name="agent_security_policies")
    op.drop_index("ix_agent_security_policies_agent_id", table_name="agent_security_policies")
    op.drop_index("ix_agent_security_policies_company_id", table_name="agent_security_policies")
    op.drop_table("agent_security_policies")

    op.drop_index("ix_security_audit_logs_event_sev", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_company_created", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_created_at", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_severity", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_event_type", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_user_id", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_company_id", table_name="security_audit_logs")
    op.drop_table("security_audit_logs")
