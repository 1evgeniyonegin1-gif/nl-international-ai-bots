"""
Обработчик текстовых сообщений для AI-Куратора
"""
import re
from datetime import datetime
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.base import AsyncSessionLocal
from shared.ai_clients.yandexgpt_client import YandexGPTClient
from shared.ai_clients.anthropic_client import AnthropicClient
from shared.config.settings import settings
from shared.rag import get_rag_engine
from curator_bot.database.models import User, ConversationMessage
from curator_bot.ai.chat_engine import CuratorChatEngine
from curator_bot.funnels.messages import CONTACT_THANKS
# Кнопки убраны - диалоговый режим
# from curator_bot.funnels.keyboards import (
#     get_pain_keyboard,
#     get_income_goal_keyboard,
#     get_start_keyboard,
#     get_curious_keyboard,
# )
from content_manager_bot.utils.product_reference import ProductReferenceManager
from loguru import logger


router = Router(name="messages")

# Регулярные выражения для контактов
PHONE_PATTERN = re.compile(r'^\+?[78]?\d{10}$|^\+7\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Инициализируем AI клиент глобально
def get_ai_client():
    """Выбирает AI клиент: Claude если настроен, иначе YandexGPT"""
    model = settings.curator_ai_model.lower()
    if settings.anthropic_api_key and "claude" in model:
        try:
            client = AnthropicClient()
            logger.info(f"Curator using Claude: {settings.curator_ai_model}")
            return client
        except Exception as e:
            logger.warning(f"Claude init failed: {e}, falling back to YandexGPT")
    logger.info("Curator using YandexGPT")
    return YandexGPTClient()

ai_client = get_ai_client()

# Инициализируем движок чата
chat_engine = CuratorChatEngine(ai_client=ai_client)

# Инициализируем менеджер фото продуктов
product_manager = ProductReferenceManager()


# ============================================
# REPLY-КНОПКИ УБРАНЫ - ДИАЛОГОВЫЙ РЕЖИМ
# ============================================
# Теперь куратор ведёт естественный диалог без кнопок.
# Воронка продаж работает через conversational_funnel.py
# который анализирует текст и определяет этап воронки.

# ============================================
# ОБЩИЙ ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ
# ============================================

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

            # Проверяем, ожидает ли пользователь ввод контакта
            if user.lead_status == "contact_requested":
                text = message.text.strip()

                # Проверяем телефон
                phone_clean = re.sub(r'[\s\-\(\)]', '', text)
                if PHONE_PATTERN.match(phone_clean) or (phone_clean.isdigit() and len(phone_clean) >= 10):
                    # Нормализуем телефон
                    if not phone_clean.startswith('+'):
                        if phone_clean.startswith('8'):
                            phone_clean = '+7' + phone_clean[1:]
                        elif phone_clean.startswith('7'):
                            phone_clean = '+' + phone_clean
                        else:
                            phone_clean = '+7' + phone_clean

                    user.phone = phone_clean
                    user.lead_status = "hot"
                    await session.commit()

                    logger.info(f"User {user.telegram_id} provided phone: {phone_clean}")
                    await message.answer(CONTACT_THANKS)
                    return

                # Проверяем email
                if EMAIL_PATTERN.match(text):
                    user.email = text.lower()
                    user.lead_status = "hot"
                    await session.commit()

                    logger.info(f"User {user.telegram_id} provided email: {text}")
                    await message.answer(CONTACT_THANKS)
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

            # Проверяем упоминание продукта и отправляем фото если найден
            # Ищем в ОБОИХ текстах: сообщении пользователя И ответе AI
            try:
                combined_text = f"{message.text} {ai_response}"
                product_tuple = product_manager.extract_product_from_content(combined_text)
                if product_tuple:
                    category, product_key, product_info = product_tuple
                    logger.info(f"[PRODUCT] Found: {category}/{product_key} - {product_info['name']}")
                    photo_path = product_manager._find_product_photo(product_key, category)
                    logger.info(f"[PRODUCT] Photo path: {photo_path}, exists={photo_path.exists() if photo_path else False}")
                    if photo_path and photo_path.exists():
                        await message.answer_photo(
                            photo=FSInputFile(photo_path),
                            caption=f"📦 {product_info['name']}"
                        )
                        logger.info(f"[PRODUCT] ✅ Sent photo: {product_info['name']}")
                else:
                    logger.debug(f"[PRODUCT] No product found in: {combined_text[:100]}")
            except Exception as photo_error:
                logger.error(f"[PRODUCT] ❌ Error sending photo: {photo_error}", exc_info=True)

            logger.info(f"Response sent to user {user.telegram_id}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await message.answer(
            "Извини, произошла ошибка при обработке твоего сообщения 😔\n"
            "Попробуй написать еще раз или используй /help"
        )
