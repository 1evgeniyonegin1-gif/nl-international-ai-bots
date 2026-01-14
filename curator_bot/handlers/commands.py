"""
Обработчики команд для AI-Куратора
"""
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.base import AsyncSessionLocal
from curator_bot.database.models import User
from curator_bot.ai.prompts import get_welcome_message
from loguru import logger


router = Router(name="commands")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    Регистрирует нового пользователя или приветствует существующего
    """
    try:
        async with AsyncSessionLocal() as session:
            # Проверяем, есть ли пользователь в БД
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()

            if not user:
                # Создаем нового пользователя
                user = User(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    user_type="lead",
                    qualification="beginner"
                )
                session.add(user)
                await session.commit()
                logger.info(f"New user registered: {message.from_user.id}")

                # Отправляем приветственное сообщение
                welcome_text = get_welcome_message(user.first_name or "Друг")
                await message.answer(welcome_text)
            else:
                # Приветствуем существующего пользователя
                await message.answer(
                    f"С возвращением, {user.first_name}! 👋\n\n"
                    f"Чем могу помочь сегодня?"
                )
                logger.info(f"Existing user returned: {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in /start command: {e}")
        await message.answer(
            "Извини, произошла ошибка при регистрации. "
            "Попробуй еще раз через несколько секунд."
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """<b>📚 Справка по AI-Куратору</b>

<b>Что я умею:</b>
✅ Отвечать на вопросы о продуктах NL
✅ Объяснять маркетинг-план и квалификации
✅ Помогать с продажами и привлечением
✅ Мотивировать и поддерживать
✅ Давать практические советы

<b>Доступные команды:</b>
/start - Начать работу с куратором
/help - Эта справка
/progress - Мой прогресс и статистика
/goal - Установить цель
/support - Связаться с руководителем

<b>Просто напиши мне любой вопрос!</b>
Я работаю 24/7 и всегда рад помочь 🚀"""

    await message.answer(help_text)


@router.message(Command("progress"))
async def cmd_progress(message: Message):
    """Показывает прогресс пользователя"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()

            if not user:
                await message.answer("Сначала нажми /start для регистрации")
                return

            # Словарь квалификаций
            qual_names = {
                "beginner": "🌱 Новичок",
                "manager": "⭐ Manager",
                "master": "💎 Master",
                "star": "🌟 Star",
                "diamond": "💍 Diamond"
            }

            progress_text = f"""<b>📊 Твой прогресс</b>

<b>Текущая квалификация:</b> {qual_names.get(user.qualification, "Новичок")}
<b>Пройдено уроков:</b> 0 из 25
<b>Дней в бизнесе:</b> {(message.date - user.created_at).days}

<b>Твои достижения:</b>
🏆 Зарегистрирован в системе
"""

            if user.current_goal:
                progress_text += f"\n<b>Твоя цель:</b> {user.current_goal}"

            progress_text += "\n\n💪 Продолжай в том же духе!"

            await message.answer(progress_text)

    except Exception as e:
        logger.error(f"Error in /progress command: {e}")
        await message.answer("Произошла ошибка при получении статистики")


@router.message(Command("goal"))
async def cmd_goal(message: Message):
    """Помогает установить цель"""
    from curator_bot.ai.prompts import get_goal_setting_prompt

    await message.answer(get_goal_setting_prompt())


@router.message(Command("support"))
async def cmd_support(message: Message):
    """Связь с руководителем"""
    support_text = """<b>🆘 Техподдержка</b>

По техническим вопросам:
📧 support@example.com

По вопросам бизнеса - напиши своему руководителю.

Также ты всегда можешь задать вопрос мне!"""

    await message.answer(support_text)
