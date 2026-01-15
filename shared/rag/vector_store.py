"""
Vector Store с использованием PostgreSQL + pgvector.
Хранит документы и их embeddings для семантического поиска.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, Text, DateTime, func, text, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from pgvector.sqlalchemy import Vector

from shared.database.base import Base, AsyncSessionLocal, engine
from shared.utils.logger import get_logger
from .embeddings import get_embedding_service, EmbeddingService

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Результат поиска в базе знаний."""
    id: int
    content: str
    source: str
    category: str
    similarity: float
    metadata: dict


class Document(Base):
    """Модель документа в базе знаний."""
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=True)  # Источник: файл, URL и т.д.
    category = Column(String(100), nullable=True)  # Категория: продукты, бизнес-план и т.д.
    chunk_index = Column(Integer, default=0)  # Индекс чанка если документ разбит
    embedding = Column(Vector(384), nullable=True)  # 384 = размерность MiniLM
    metadata = Column(JSONB, default={})  # Дополнительные данные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Индекс для быстрого поиска по категории
    __table_args__ = (
        Index("idx_documents_category", "category"),
        Index("idx_documents_source", "source"),
    )


class VectorStore:
    """
    Хранилище векторов с поддержкой семантического поиска.
    """

    def __init__(self, embedding_service: EmbeddingService = None):
        self.embedding_service = embedding_service or get_embedding_service()
        self._pgvector_enabled = None

    async def ensure_pgvector(self) -> bool:
        """
        Проверить и включить расширение pgvector.
        Возвращает True если pgvector доступен.
        """
        if self._pgvector_enabled is not None:
            return self._pgvector_enabled

        try:
            async with engine.begin() as conn:
                # Пробуем создать расширение
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                self._pgvector_enabled = True
                logger.info("pgvector расширение включено")
        except Exception as e:
            logger.warning(f"pgvector недоступен: {e}")
            logger.warning("Будет использоваться поиск без векторов (медленнее)")
            self._pgvector_enabled = False

        return self._pgvector_enabled

    async def init_tables(self):
        """Создать таблицы для хранения документов."""
        await self.ensure_pgvector()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы для RAG созданы")

    async def add_document(
        self,
        content: str,
        source: str = None,
        category: str = None,
        chunk_index: int = 0,
        metadata: dict = None
    ) -> int:
        """
        Добавить документ в базу знаний.

        Args:
            content: Текст документа
            source: Источник (файл, URL и т.д.)
            category: Категория документа
            chunk_index: Индекс чанка если разбит
            metadata: Дополнительные данные

        Returns:
            ID созданного документа
        """
        # Получаем embedding
        embedding = await self.embedding_service.aget_embedding(content)

        async with AsyncSessionLocal() as session:
            doc = Document(
                content=content,
                source=source,
                category=category,
                chunk_index=chunk_index,
                embedding=embedding,
                metadata=metadata or {}
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            logger.debug(f"Документ добавлен: id={doc.id}, source={source}")
            return doc.id

    async def add_documents(
        self,
        documents: List[dict],
        batch_size: int = 32
    ) -> List[int]:
        """
        Добавить несколько документов пакетом.

        Args:
            documents: Список словарей с ключами: content, source, category, metadata
            batch_size: Размер пакета для embeddings

        Returns:
            Список ID созданных документов
        """
        if not documents:
            return []

        # Получаем embeddings пакетом
        contents = [doc["content"] for doc in documents]
        embeddings = await self.embedding_service.aget_embeddings(contents, batch_size)

        doc_ids = []
        async with AsyncSessionLocal() as session:
            for i, doc_data in enumerate(documents):
                doc = Document(
                    content=doc_data["content"],
                    source=doc_data.get("source"),
                    category=doc_data.get("category"),
                    chunk_index=doc_data.get("chunk_index", 0),
                    embedding=embeddings[i],
                    metadata=doc_data.get("metadata", {})
                )
                session.add(doc)
                doc_ids.append(doc)

            await session.commit()
            for doc in doc_ids:
                await session.refresh(doc)

            result_ids = [doc.id for doc in doc_ids]
            logger.info(f"Добавлено {len(result_ids)} документов")
            return result_ids

    async def search(
        self,
        query: str,
        top_k: int = 5,
        category: str = None,
        min_similarity: float = 0.3
    ) -> List[SearchResult]:
        """
        Семантический поиск по базе знаний.

        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            category: Фильтр по категории
            min_similarity: Минимальный порог схожести (0-1)

        Returns:
            Список результатов поиска
        """
        # Получаем embedding запроса
        query_embedding = await self.embedding_service.aget_embedding(query)

        async with AsyncSessionLocal() as session:
            # Используем косинусное расстояние pgvector
            # 1 - distance = similarity (чем ближе к 1, тем более похоже)
            distance_expr = Document.embedding.cosine_distance(query_embedding)

            query_stmt = (
                select(
                    Document.id,
                    Document.content,
                    Document.source,
                    Document.category,
                    Document.metadata,
                    (1 - distance_expr).label("similarity")
                )
                .where(Document.embedding.isnot(None))
                .order_by(distance_expr)
                .limit(top_k * 2)  # Берем больше, потом фильтруем
            )

            if category:
                query_stmt = query_stmt.where(Document.category == category)

            result = await session.execute(query_stmt)
            rows = result.fetchall()

            results = []
            for row in rows:
                similarity = float(row.similarity)
                if similarity >= min_similarity:
                    results.append(SearchResult(
                        id=row.id,
                        content=row.content,
                        source=row.source,
                        category=row.category,
                        similarity=similarity,
                        metadata=row.metadata or {}
                    ))

            return results[:top_k]

    async def get_document(self, doc_id: int) -> Optional[Document]:
        """Получить документ по ID."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Document).where(Document.id == doc_id)
            )
            return result.scalar_one_or_none()

    async def delete_document(self, doc_id: int) -> bool:
        """Удалить документ по ID."""
        async with AsyncSessionLocal() as session:
            doc = await session.get(Document, doc_id)
            if doc:
                await session.delete(doc)
                await session.commit()
                return True
            return False

    async def delete_by_source(self, source: str) -> int:
        """Удалить все документы из указанного источника."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Document).where(Document.source == source)
            )
            docs = result.scalars().all()
            count = len(docs)
            for doc in docs:
                await session.delete(doc)
            await session.commit()
            logger.info(f"Удалено {count} документов из источника: {source}")
            return count

    async def get_stats(self) -> dict:
        """Получить статистику базы знаний."""
        async with AsyncSessionLocal() as session:
            # Общее количество документов
            total = await session.execute(select(func.count(Document.id)))
            total_count = total.scalar()

            # По категориям
            categories = await session.execute(
                select(Document.category, func.count(Document.id))
                .group_by(Document.category)
            )
            category_counts = {row[0] or "Без категории": row[1] for row in categories.fetchall()}

            # По источникам
            sources = await session.execute(
                select(Document.source, func.count(Document.id))
                .group_by(Document.source)
            )
            source_counts = {row[0] or "Неизвестно": row[1] for row in sources.fetchall()}

            return {
                "total_documents": total_count,
                "by_category": category_counts,
                "by_source": source_counts,
                "embedding_dimension": self.embedding_service.embedding_dimension
            }


# Глобальный экземпляр
_vector_store: Optional[VectorStore] = None


async def get_vector_store() -> VectorStore:
    """Получить глобальный экземпляр VectorStore."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        await _vector_store.init_tables()
    return _vector_store
