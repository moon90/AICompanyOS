"""create vector embeddings adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40

Revision ID: 0018_create_vector_embeddings
Revises: 0017_create_knowledge
Create Date: 2026-09-25 01:35:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0018_create_vector_embeddings"
down_revision: str | Sequence[str] | None = "0017_create_knowledge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to include vector_embeddings table."""
    # Ensure vector extension is installed on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        "vector_embeddings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
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
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_vector_embeddings_company_id", "vector_embeddings", ["company_id"], unique=False
    )
    op.create_index(
        "ix_vector_embeddings_source_type", "vector_embeddings", ["source_type"], unique=False
    )
    op.create_index(
        "ix_vector_embeddings_source_id", "vector_embeddings", ["source_id"], unique=False
    )
    op.create_index(
        "ix_vector_embeddings_created_at", "vector_embeddings", ["created_at"], unique=False
    )
    op.create_index(
        "ix_vector_embeddings_company_source",
        "vector_embeddings",
        ["company_id", "source_type"],
        unique=False,
    )
    op.create_index(
        "ix_vector_embeddings_company_source_id",
        "vector_embeddings",
        ["company_id", "source_id"],
        unique=False,
    )
    op.create_index(
        "ix_vector_embeddings_company_created",
        "vector_embeddings",
        ["company_id", "created_at"],
        unique=False,
    )

    # Create HNSW index for high-speed approximate nearest neighbor cosine search on PostgreSQL
    if bind.dialect.name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_vector_embeddings_hnsw "
            "ON vector_embeddings USING hnsw (embedding vector_cosine_ops);"
        )


def downgrade() -> None:
    """Downgrade schema to remove vector_embeddings table."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_vector_embeddings_hnsw;")

    op.drop_index("ix_vector_embeddings_company_created", table_name="vector_embeddings")
    op.drop_index("ix_vector_embeddings_company_source_id", table_name="vector_embeddings")
    op.drop_index("ix_vector_embeddings_company_source", table_name="vector_embeddings")
    op.drop_index("ix_vector_embeddings_created_at", table_name="vector_embeddings")
    op.drop_index("ix_vector_embeddings_source_id", table_name="vector_embeddings")
    op.drop_index("ix_vector_embeddings_source_type", table_name="vector_embeddings")
    op.drop_index("ix_vector_embeddings_company_id", table_name="vector_embeddings")
    op.drop_table("vector_embeddings")
