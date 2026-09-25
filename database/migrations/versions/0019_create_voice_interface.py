"""create voice interface tables adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60

Revision ID: 0019_create_voice_interface
Revises: 0018_create_vector_embeddings
Create Date: 2026-09-25 01:56:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019_create_voice_interface"
down_revision: str | Sequence[str] | None = "0018_create_vector_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include voice_sessions and voice_interactions tables."""
    # 1. Create voice_sessions table
    op.create_table(
        "voice_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), server_default="Voice Session", nullable=False),
        sa.Column("state", sa.String(length=32), server_default="IDLE", nullable=False),
        sa.Column("context_data", sa.JSON(), server_default="{}", nullable=False),
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
    )
    op.create_index("ix_voice_sessions_company_id", "voice_sessions", ["company_id"], unique=False)
    op.create_index("ix_voice_sessions_user_id", "voice_sessions", ["user_id"], unique=False)
    op.create_index("ix_voice_sessions_state", "voice_sessions", ["state"], unique=False)
    op.create_index("ix_voice_sessions_created_at", "voice_sessions", ["created_at"], unique=False)
    op.create_index(
        "ix_voice_sessions_company_user",
        "voice_sessions",
        ["company_id", "user_id"],
        unique=False,
    )

    # 2. Create voice_interactions table
    op.create_table(
        "voice_interactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=64), server_default="GENERAL_INQUIRY", nullable=False),
        sa.Column("action_taken", sa.String(length=255), nullable=True),
        sa.Column("action_entity_id", sa.String(length=36), nullable=True),
        sa.Column("action_success", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("spoken_response", sa.Text(), nullable=False),
        sa.Column("detailed_response", sa.Text(), nullable=False),
        sa.Column("execution_time_ms", sa.Float(), server_default="0.0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["voice_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_voice_interactions_session_id", "voice_interactions", ["session_id"], unique=False
    )
    op.create_index(
        "ix_voice_interactions_company_id", "voice_interactions", ["company_id"], unique=False
    )
    op.create_index(
        "ix_voice_interactions_user_id", "voice_interactions", ["user_id"], unique=False
    )
    op.create_index("ix_voice_interactions_intent", "voice_interactions", ["intent"], unique=False)
    op.create_index(
        "ix_voice_interactions_created_at", "voice_interactions", ["created_at"], unique=False
    )
    op.create_index(
        "ix_voice_interactions_session_created",
        "voice_interactions",
        ["session_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema to remove voice_interactions and voice_sessions tables."""
    op.drop_table("voice_interactions")
    op.drop_table("voice_sessions")
