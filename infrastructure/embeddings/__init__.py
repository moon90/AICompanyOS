"""Embeddings package for AI Company OS."""

from infrastructure.embeddings.engine import (
    EMBEDDING_DIMENSION,
    EmbeddingEngine,
    cosine_similarity,
    default_embedding_engine,
)

__all__ = [
    "EMBEDDING_DIMENSION",
    "EmbeddingEngine",
    "cosine_similarity",
    "default_embedding_engine",
]
