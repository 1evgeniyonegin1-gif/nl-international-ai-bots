"""
RAG Engine - объединяет поиск по базе знаний и генерацию ответов.
"""

from typing import List, Optional, Callable, Awaitable
from dataclasses import dataclass

from shared.utils.logger import get_logger
from .vector_store import VectorStore, SearchResult, get_vector_store

logger = get_logger(__name__)


@dataclass
class RAGContext:
    """Контекст для генерации ответа."""
    query: str
    relevant_docs: List[SearchResult]
    augmented_prompt: str


class RAGEngine:
    """
    Retrieval-Augmented Generation движок.
    Находит релевантные документы и формирует промпт для AI.
    """

    DEFAULT_SYSTEM_TEMPLATE = """Ты - AI-куратор NL International.
Используй предоставленную информацию из базы знаний для ответа на вопрос.
Если информация не найдена в базе знаний, честно скажи об этом и дай общий ответ на основе своих знаний.

### База знаний NL International:
{context}

### Правила ответа:
1. Отвечай конкретно и по делу
2. Если информация из базы знаний, ссылайся на неё
3. Если вопрос не связан с NL International, отвечай как обычный помощник
4. Будь дружелюбным и поддерживающим"""

    DEFAULT_CONTEXT_TEMPLATE = """[Источник: {source}] (Релевантность: {similarity:.0%})
{content}
---"""

    def __init__(
        self,
        vector_store: VectorStore = None,
        system_template: str = None,
        context_template: str = None,
        top_k: int = 5,
        min_similarity: float = 0.4
    ):
        self._vector_store = vector_store
        self.system_template = system_template or self.DEFAULT_SYSTEM_TEMPLATE
        self.context_template = context_template or self.DEFAULT_CONTEXT_TEMPLATE
        self.top_k = top_k
        self.min_similarity = min_similarity

    async def _get_vector_store(self) -> VectorStore:
        """Получить vector store (ленивая инициализация)."""
        if self._vector_store is None:
            self._vector_store = await get_vector_store()
        return self._vector_store

    async def retrieve(
        self,
        query: str,
        category: str = None,
        top_k: int = None,
        min_similarity: float = None
    ) -> List[SearchResult]:
        """
        Найти релевантные документы по запросу.

        Args:
            query: Поисковый запрос
            category: Фильтр по категории
            top_k: Количество результатов
            min_similarity: Минимальный порог схожести

        Returns:
            Список найденных документов
        """
        store = await self._get_vector_store()
        results = await store.search(
            query=query,
            top_k=top_k or self.top_k,
            category=category,
            min_similarity=min_similarity or self.min_similarity
        )
        logger.debug(f"Найдено {len(results)} релевантных документов для запроса: {query[:50]}...")
        return results

    def format_context(self, docs: List[SearchResult]) -> str:
        """
        Форматировать найденные документы в контекст для промпта.

        Args:
            docs: Список найденных документов

        Returns:
            Отформатированный текст контекста
        """
        if not docs:
            return "Релевантная информация в базе знаний не найдена."

        context_parts = []
        for doc in docs:
            part = self.context_template.format(
                source=doc.source or "База знаний",
                similarity=doc.similarity,
                content=doc.content
            )
            context_parts.append(part)

        return "\n".join(context_parts)

    async def augment_prompt(
        self,
        query: str,
        category: str = None
    ) -> RAGContext:
        """
        Создать augmented промпт с контекстом из базы знаний.

        Args:
            query: Вопрос пользователя
            category: Категория для поиска

        Returns:
            RAGContext с промптом и найденными документами
        """
        # Поиск релевантных документов
        relevant_docs = await self.retrieve(query, category=category)

        # Форматирование контекста
        context = self.format_context(relevant_docs)

        # Создание augmented промпта
        augmented_prompt = self.system_template.format(context=context)

        return RAGContext(
            query=query,
            relevant_docs=relevant_docs,
            augmented_prompt=augmented_prompt
        )

    async def query(
        self,
        user_query: str,
        generate_fn: Callable[[str, str], Awaitable[str]],
        category: str = None
    ) -> str:
        """
        Полный цикл RAG: поиск + генерация ответа.

        Args:
            user_query: Вопрос пользователя
            generate_fn: Асинхронная функция генерации (system_prompt, user_message) -> response
            category: Категория для поиска

        Returns:
            Сгенерированный ответ
        """
        # Получаем контекст из базы знаний
        rag_context = await self.augment_prompt(user_query, category=category)

        # Логируем найденные документы
        if rag_context.relevant_docs:
            sources = [doc.source for doc in rag_context.relevant_docs]
            logger.info(f"RAG: найдено {len(rag_context.relevant_docs)} документов: {sources}")
        else:
            logger.info("RAG: релевантные документы не найдены, используем общие знания AI")

        # Генерируем ответ с augmented промптом
        response = await generate_fn(rag_context.augmented_prompt, user_query)

        return response

    async def add_to_knowledge_base(
        self,
        content: str,
        source: str = None,
        category: str = None,
        metadata: dict = None
    ) -> int:
        """
        Добавить документ в базу знаний.

        Args:
            content: Текст документа
            source: Источник
            category: Категория
            metadata: Дополнительные данные

        Returns:
            ID документа
        """
        store = await self._get_vector_store()
        return await store.add_document(
            content=content,
            source=source,
            category=category,
            metadata=metadata
        )

    async def get_stats(self) -> dict:
        """Получить статистику базы знаний."""
        store = await self._get_vector_store()
        return await store.get_stats()


# Глобальный экземпляр
_rag_engine: Optional[RAGEngine] = None


async def get_rag_engine() -> RAGEngine:
    """Получить глобальный экземпляр RAGEngine."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
