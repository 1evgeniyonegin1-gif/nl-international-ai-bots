"""
Конфигурация pytest и общие фикстуры для тестов
"""
import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from shared.database.base import Base
from curator_bot.database.models import User, ConversationMessage, KnowledgeBaseChunk
from content_manager_bot.database.models import Post, ContentSchedule


# Тестовая база данных (в памяти SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Создаёт политику event loop для всех async тестов"""
    return asyncio.get_event_loop_policy()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Создаёт тестовый движок базы данных"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool
    )
    
    # Создаём все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Удаляем все таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Создаёт тестовую сессию базы данных"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Создаёт тестового пользователя"""
    user = User(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        user_type="partner",
        qualification="consultant"  # Обновлено на новую систему квалификаций
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_knowledge_chunk(test_session: AsyncSession) -> KnowledgeBaseChunk:
    """Создаёт тестовый фрагмент базы знаний"""
    chunk = KnowledgeBaseChunk(
        source_file="test_product.md",
        chunk_text="Energy Diet - это функциональное питание для контроля веса",
        category="products",
        meta_data={"product": "Energy Diet"}
    )
    test_session.add(chunk)
    await test_session.commit()
    await test_session.refresh(chunk)
    return chunk


@pytest_asyncio.fixture
async def test_post(test_session: AsyncSession) -> Post:
    """Создаёт тестовый пост"""
    post = Post(
        content="🌟 Новый продукт Energy Diet!",
        post_type="product",
        status="draft",
        ai_model="test_model"
    )
    test_session.add(post)
    await test_session.commit()
    await test_session.refresh(post)
    return post


# Мок для AI клиента
class MockAIClient:
    """Мок AI клиента для тестов"""
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Возвращает тестовый ответ"""
        return "Это тестовый ответ от AI"
    
    async def generate_embedding(self, text: str) -> list[float]:
        """Возвращает тестовый вектор"""
        return [0.1] * 384  # Вектор размерности 384


@pytest.fixture
def mock_ai_client() -> MockAIClient:
    """Возвращает мок AI клиента"""
    return MockAIClient()
