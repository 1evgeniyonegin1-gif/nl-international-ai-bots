"""
Обработчик текстовых сообщений для AI-Куратора
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.base import AsyncSessionLocal
from shared.ai_clients.gigachat_client import GigaChatClient
from shared.config.settings import settings
from shared.rag import get_rag_engine
from curator_bot.database.models import User, ConversationMessage
from curator_bot.ai.chat_engine import CuratorChatEngine
from loguru import logger


router = Router(name="messages")

# Инициализируем AI клиент глобально
# Используем GigaChat (Сбер) - бесплатный
ai_client = GigaChatClient(
    auth_token=settings.gigachat_auth_token,
    model="GigaChat"
)

# Инициализируем движок чата
chat_engine = CuratorChatEngine(ai_client=ai_client)


@router.message(F.text)
async def handle_message(message: Message):
    """
    Обработчик всех текстовых сообщений
    Генерирует ответ с помощью AI
    """
    try:
        # Показываем, что бот печатает
        await message.bot.send_chat_action(message.chat.id, "typing")

        async with AsyncSessionLocal() as session:
            # Получаем пользователя
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()

            if not user:
                # Если пользователь не зарегистрирован
                await message.answer(
                    "Привет! Сначала нажми /start чтобы начать работу со мной 😊"
                )
                return

            # Обновляем последнюю активность
            user.last_activity = datetime.now()

            # Сохраняем сообщение пользователя в БД
            user_msg = ConversationMessage(
                user_id=user.id,
                message_text=message.text,
                sender="user",
                timestamp=datetime.now()
            )
            session.add(user_msg)
            await session.commit()

            logger.info(f"Processing message from user {user.telegram_id}: {message.text[:50]}...")

            # Получаем историю диалога
            history_result = await session.execute(
                select(ConversationMessage)
                .where(ConversationMessage.user_id == user.id)
                .order_by(ConversationMessage.timestamp.desc())
                .limit(20)
            )
            conversation_history = list(history_result.scalars().all())

            # Анализируем намерение пользователя
            intent = await chat_engine.analyze_user_intent(message.text)

            # Определяем, нужна ли база знаний
            knowledge_fragments = None
            if chat_engine.should_use_rag(intent):
                try:
                    # Получаем RAG движок и ищем релевантные документы
                    rag_engine = await get_rag_engine()

                    # Определяем категорию для поиска
                    category = intent.get("category")
                    if category == "sales":
                        category = "training"  # Скрипты продаж в категории training

                    # Выполняем поиск по базе знаний
                    search_results = await rag_engine.retrieve(
                        query=message.text,
                        category=category,
                        top_k=5,
                        min_similarity=0.3
                    )

                    if search_results:
                        # Преобразуем результаты в список строк для chat_engine
                        knowledge_fragments = [
                            f"[{r.source}]: {r.content}"
                            for r in search_results
                        ]
                        logger.info(f"RAG: найдено {len(search_results)} документов для категории '{category}'")
                    else:
                        logger.info(f"RAG: документы не найдены для запроса в категории '{category}'")

                except Exception as rag_error:
                    logger.warning(f"RAG search failed, continuing without knowledge base: {rag_error}")
                    # Продолжаем без RAG если произошла ошибка

            # Генерируем ответ от AI
            ai_response = await chat_engine.generate_response(
                user=user,
                user_message=message.text,
                conversation_history=conversation_history,
                knowledge_fragments=knowledge_fragments
            )

            # Сохраняем ответ бота в БД
            bot_msg = ConversationMessage(
                user_id=user.id,
                message_text=ai_response,
                sender="bot",
                timestamp=datetime.now(),
                ai_model=settings.curator_ai_model,
                tokens_used=None  # OpenAI возвращает usage в ответе, можно добавить позже
            )
            session.add(bot_msg)
            await session.commit()

            # Отправляем ответ пользователю
            await message.answer(ai_response)

            logger.info(f"Response sent to user {user.telegram_id}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await message.answer(
            "Извини, произошла ошибка при обработке твоего сообщения 😔\n"
            "Попробуй написать еще раз или используй /help"
        )
