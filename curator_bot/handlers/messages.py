"""
Обработчик текстовых сообщений для AI-Куратора
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.base import AsyncSessionLocal
from shared.ai_clients.anthropic_client import AnthropicClient
from shared.config.settings import settings
from curator_bot.database.models import User, ConversationMessage
from curator_bot.ai.chat_engine import CuratorChatEngine
from loguru import logger


router = Router(name="messages")

# Инициализируем AI клиент глобально
# Используем Claude (Anthropic)
ai_client = AnthropicClient(
    api_key=settings.anthropic_api_key,
    model=settings.curator_ai_model
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
                # TODO: Реализовать поиск по базе знаний (RAG)
                # knowledge_fragments = await search_knowledge_base(message.text, intent)
                logger.info(f"RAG search would be performed for keywords: {intent['keywords']}")
                # Пока используем None

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
