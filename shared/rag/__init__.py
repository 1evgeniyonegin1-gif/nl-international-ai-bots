"""
RAG (Retrieval-Augmented Generation) модуль для NL International AI Bots.
Использует Sentence Transformers для локальных embeddings (бесплатно).
"""

from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .rag_engine import RAGEngine

__all__ = ["EmbeddingService", "VectorStore", "RAGEngine"]
