"""
Обработчики команд для AI-Куратора
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.base import AsyncSessionLocal
from shared.config.settings import settings
from curator_bot.database.models import User
from curator_bot.ai.prompts import get_welcome_message
# Кнопки убраны - диалоговый режим
# from curator_bot.funnels.keyboards import get_start_keyboard, get_main_menu_reply_keyboard
from curator_bot.analytics.funnel_stats import get_funnel_stats, format_funnel_stats
from curator_bot.analytics.lead_scoring import get_leads_needing_attention
from loguru import logger


router = Router(name="commands")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    Регистрирует нового пользователя и начинает ДИАЛОГОВЫЙ режим (без кнопок)
    """
    try:
        async with AsyncSessionLocal() as session:
            # Проверяем, есть ли пользователь в БД
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()

            first_name = message.from_user.first_name or "Друг"

            if not user:
                # Создаем нового пользователя
                user = User(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    user_type="lead",
                    qualification="consultant",
                    funnel_started_at=datetime.utcnow(),
                    lead_status="new"
                )
                session.add(user)
                await session.commit()
                logger.info(f"New user registered: {message.from_user.id}")

                # ДИАЛОГОВЫЙ РЕЖИМ - предлагаем варианты сразу
                welcome_text = f"""Йо, {first_name}! 👋

Я Данил — твой гайд по NL.

Чё интересно?

1️⃣ **Продукты** — расскажу про ED Smart, Greenflash, косметику
2️⃣ **Бабки** — сколько реально зарабатывают (без понтов)
3️⃣ **Как начать** — с нуля до первых денег

Просто напиши цифру или своими словами 🤙"""

                await message.answer(welcome_text)

            else:
                # Существующий пользователь — диалоговый режим
                user.last_activity = datetime.utcnow()
                await session.commit()

                welcome_text = f"""Йо, {first_name}! 👋

Рад что вернулся. Чё новенького?

1️⃣ Вопросы по продуктам
2️⃣ Хочу понять про заработок
3️⃣ Нужна помощь с клиентами

Или просто напиши что на уме 💬"""

                await message.answer(welcome_text)
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

            # Словарь квалификаций по системе NL International
            qual_names = {
                "consultant": "🌱 Консультант (3%)",
                "consultant_6": "📈 Консультант 6%",
                "manager_9": "⭐ Менеджер 9%",
                "senior_manager": "💼 Старший менеджер (12%)",
                "manager_15": "📊 Менеджер 15%",
                "director_21": "🎯 Директор 21%",
                "M1": "🔥 Middle 1",
                "M2": "🔥 Middle 2",
                "M3": "🔥 Middle 3",
                "B1": "💼 Business Partner 1",
                "B2": "💼 Business Partner 2",
                "B3": "💼 Business Partner 3",
                "TOP": "⭐ TOP",
                "TOP1": "⭐ TOP 1",
                "TOP2": "⭐ TOP 2",
                "TOP3": "⭐ TOP 3",
                "TOP4": "⭐ TOP 4",
                "TOP5": "⭐ TOP 5",
                "AC1": "👑 Ambassador Club 1",
                "AC2": "👑 Ambassador Club 2",
                "AC3": "👑 Ambassador Club 3",
                "AC4": "👑 Ambassador Club 4",
                "AC5": "👑 Ambassador Club 5",
                "AC6": "👑 Ambassador Club 6",
            }

            progress_text = f"""<b>📊 Твой прогресс</b>

<b>Текущая квалификация:</b> {qual_names.get(user.qualification, "🌱 Консультант")}
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


@router.message(Command("funnel_stats"))
async def cmd_funnel_stats(message: Message):
    """
    Статистика воронки продаж (только для админов)
    Использование: /funnel_stats [дней]
    """
    # Проверяем права админа
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    try:
        # Парсим количество дней из аргументов
        args = message.text.split()
        period_days = 7  # по умолчанию
        if len(args) > 1:
            try:
                period_days = int(args[1])
                period_days = max(1, min(period_days, 365))  # Ограничиваем 1-365
            except ValueError:
                pass

        await message.answer("⏳ Собираю статистику...")

        # Получаем статистику
        stats = await get_funnel_stats(period_days)
        stats_text = format_funnel_stats(stats)

        await message.answer(stats_text)

    except Exception as e:
        logger.error(f"Error in /funnel_stats command: {e}", exc_info=True)
        await message.answer("❌ Ошибка при получении статистики")


@router.message(Command("hot_leads"))
async def cmd_hot_leads(message: Message):
    """
    Список горячих лидов (только для админов)
    """
    # Проверяем права админа
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    try:
        leads = await get_leads_needing_attention()

        if not leads:
            await message.answer("🔍 Горячих лидов, требующих внимания, нет")
            return

        intent_names = {
            "client": "Клиент",
            "business": "Бизнес",
        }

        response = f"🔥 <b>ГОРЯЧИЕ ЛИДЫ ({len(leads)})</b>\n\n"

        for i, lead in enumerate(leads[:10], 1):  # Максимум 10
            contact = lead.phone or lead.email or "нет контакта"
            intent = intent_names.get(lead.user_intent, lead.user_intent or "-")

            response += f"""{i}. <b>{lead.first_name or 'Без имени'}</b>
   📞 {contact}
   🎯 {intent} | Скор: {lead.lead_score}
   👉 @{lead.username or f'id{lead.telegram_id}'}

"""

        if len(leads) > 10:
            response += f"\n<i>...и ещё {len(leads) - 10} лидов</i>"

        await message.answer(response)

    except Exception as e:
        logger.error(f"Error in /hot_leads command: {e}", exc_info=True)
        await message.answer("❌ Ошибка при получении списка лидов")
