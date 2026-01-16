# API Документация - NL International AI Bots

Документация основных API и функций проекта.

---

## Модели базы данных

### Curator Bot

#### User
Модель пользователя (партнера NL International).

**Поля:**
- `telegram_id` (int) - ID пользователя в Telegram (уникальный)
- `username` (str) - Username в Telegram
- `first_name` (str) - Имя
- `last_name` (str) - Фамилия
- `user_type` (str) - Тип: 'lead' или 'partner'
- `qualification` (str) - Квалификация: 'beginner', 'manager', 'master', 'star', 'diamond'
- `current_goal` (str) - Текущая цель партнера
- `is_active` (bool) - Активен ли пользователь

**Relationships:**
- `messages` - История сообщений
- `context` - Контекст диалога

#### ConversationMessage
История диалогов с куратором.

**Поля:**
- `user_id` (int) - ID пользователя
- `message_text` (str) - Текст сообщения
- `sender` (str) - 'user' или 'bot'
- `timestamp` (datetime) - Время сообщения
- `ai_model` (str) - Использованная AI модель
- `tokens_used` (int) - Количество токенов

#### KnowledgeBaseChunk
Фрагменты базы знаний для RAG.

**Поля:**
- `source_file` (str) - Исходный файл
- `chunk_text` (str) - Текст фрагмента
- `embedding` (Vector(384)) - Векторное представление для поиска
- `category` (str) - Категория: 'products', 'business', 'faq', etc.
- `meta_data` (dict) - Дополнительные метаданные

---

### Content Manager Bot

#### Post
Модель поста для публикации в канал.

**Поля:**
- `content` (str) - Контент поста
- `post_type` (str) - Тип: 'product', 'motivation', 'news', 'tips', 'success_story', 'promo'
- `status` (str) - Статус: 'draft', 'pending', 'approved', 'published', 'rejected', 'scheduled'
- `generated_at` (datetime) - Время генерации
- `scheduled_for` (datetime) - Время публикации (если запланирован)
- `channel_message_id` (int) - ID сообщения в канале
- `ai_model` (str) - Использованная AI модель

**Методы:**
- `to_telegram_format()` - Форматирует пост для Telegram

#### ContentSchedule
Расписание автоматической генерации контента.

**Поля:**
- `post_type` (str) - Тип постов для генерации
- `cron_expression` (str) - Cron выражение для расписания
- `is_active` (bool) - Активно ли расписание
- `total_generated` (int) - Всего сгенерировано
- `total_published` (int) - Всего опубликовано

---

## AI Клиенты

### GigaChatClient

Клиент для работы с GigaChat API (Сбер).

**Инициализация:**
```python
from shared.ai_clients.gigachat_client import GigaChatClient

client = GigaChatClient(
    auth_token="your_token",
    client_id="your_client_id"
)
```

**Методы:**

#### `async generate_response(prompt: str, **kwargs) -> str`
Генерирует ответ на промпт.

**Параметры:**
- `prompt` (str) - Текст промпта
- `temperature` (float) - Температура генерации (0.0-1.0)
- `max_tokens` (int) - Максимум токенов

**Возвращает:** Сгенерированный текст

**Пример:**
```python
response = await client.generate_response(
    "Расскажи о продукте Energy Diet",
    temperature=0.7,
    max_tokens=500
)
```

#### `async generate_embedding(text: str) -> List[float]`
Генерирует векторное представление текста.

**Параметры:**
- `text` (str) - Текст для векторизации

**Возвращает:** Список float (размерность 384)

---

## RAG Система

### VectorStore

Класс для работы с векторным хранилищем.

**Инициализация:**
```python
from shared.rag.vector_store import VectorStore

store = VectorStore(session=db_session)
```

**Методы:**

#### `async add_document(text: str, category: str, metadata: dict) -> KnowledgeBaseChunk`
Добавляет документ в базу знаний.

**Параметры:**
- `text` (str) - Текст документа
- `category` (str) - Категория
- `metadata` (dict) - Метаданные

**Возвращает:** Созданный фрагмент

#### `async search(query: str, limit: int = 5) -> List[KnowledgeBaseChunk]`
Поиск релевантных фрагментов.

**Параметры:**
- `query` (str) - Поисковый запрос
- `limit` (int) - Максимум результатов

**Возвращает:** Список релевантных фрагментов

**Пример:**
```python
results = await store.search(
    "Как работает план вознаграждения?",
    limit=3
)
```

---

## Планировщик контента

### ContentScheduler

Планировщик автоматической генерации и публикации контента.

**Инициализация:**
```python
from content_manager_bot.scheduler.content_scheduler import ContentScheduler

scheduler = ContentScheduler(bot=bot_instance)
```

**Методы:**

#### `async start()`
Запускает планировщик.

#### `async stop()`
Останавливает планировщик.

#### `async schedule_post(post_id: int, publish_time: datetime)`
Планирует публикацию поста.

**Параметры:**
- `post_id` (int) - ID поста
- `publish_time` (datetime) - Время публикации

---

## Утилиты

### Logger

Настройка логирования для ботов.

**Использование:**
```python
from shared.utils.logger import setup_logger

logger = setup_logger("curator", log_level="INFO")
logger.info("Бот запущен")
logger.error("Произошла ошибка")
```

**Параметры:**
- `bot_name` (str) - Имя бота ('curator' или 'content_manager')
- `log_level` (str) - Уровень: 'DEBUG', 'INFO', 'WARNING', 'ERROR'

**Особенности:**
- Автоматическая ротация логов при достижении 10MB
- Хранение логов 1 неделю (обычные) и 1 месяц (ошибки)
- Автоматическое сжатие старых логов

---

## Настройки

### Settings

Глобальные настройки приложения из `.env` файла.

**Использование:**
```python
from shared.config.settings import settings

bot_token = settings.curator_bot_token
db_url = settings.database_url
admin_ids = settings.admin_ids_list
```

**Доступные настройки:**
- `curator_bot_token` - Токен AI-Куратора
- `content_manager_bot_token` - Токен Контент-Менеджера
- `database_url` - URL базы данных
- `gigachat_auth_token` - Токен GigaChat
- `admin_ids_list` - Список ID администраторов
- `channel_username` - Username канала для публикаций

---

## Примеры использования

### Создание пользователя

```python
from curator_bot.database.models import User
from shared.database.base import get_session

async with get_session() as session:
    user = User(
        telegram_id=123456789,
        username="partner_ivan",
        first_name="Иван",
        user_type="partner",
        qualification="manager"
    )
    session.add(user)
    await session.commit()
```

### Генерация поста

```python
from content_manager_bot.ai.content_generator import ContentGenerator

generator = ContentGenerator()
post_content = await generator.generate_post(
    post_type="product",
    topic="Energy Diet"
)
```

### Поиск в базе знаний

```python
from shared.rag.vector_store import VectorStore

async with get_session() as session:
    store = VectorStore(session)
    results = await store.search("Коллаген NL", limit=5)
    
    for chunk in results:
        print(f"Категория: {chunk.category}")
        print(f"Текст: {chunk.chunk_text}")
```

---

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Конкретный файл
pytest tests/test_curator_bot.py -v

# С покрытием кода
pytest tests/ --cov=. --cov-report=html
```

### Создание фикстур

```python
import pytest
from tests.conftest import test_session, test_user

@pytest.mark.asyncio
async def test_my_function(test_session, test_user):
    # Ваш тест
    assert test_user.telegram_id == 123456789
```

---

## Развертывание

См. [DEPLOYMENT.md](DEPLOYMENT.md) для подробных инструкций по развертыванию на различных платформах.
