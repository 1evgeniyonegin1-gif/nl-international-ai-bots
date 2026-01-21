"""
Обработчики callback-кнопок для воронки продаж
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.base import AsyncSessionLocal
from curator_bot.database.models import User
from curator_bot.funnels.keyboards import (
    get_pain_keyboard,
    get_income_goal_keyboard,
    get_continue_keyboard,
    get_weight_goal_keyboard,
    get_product_interest_keyboard,
    get_order_keyboard,
    get_business_continue_keyboard,
    get_business_next_keyboard,
    get_registration_keyboard,
    get_contact_request_keyboard,
    get_start_keyboard,
    get_back_to_start_keyboard,
)
from curator_bot.funnels.messages import (
    WELCOME_CLIENT,
    WELCOME_BUSINESS,
    WELCOME_CURIOUS,
    CLIENT_WEIGHT_STEP_1,
    CLIENT_WEIGHT_STEP_2,
    CLIENT_WEIGHT_STEP_3,
    get_client_weight_recommendation,
    CLIENT_ENERGY_STEP_1,
    CLIENT_ENERGY_STEP_2,
    CLIENT_IMMUNITY_STEP_1,
    CLIENT_BEAUTY_STEP_1,
    CLIENT_KIDS_STEP_1,
    CLIENT_SPORT_STEP_1,
    BUSINESS_STEP_1_10_30K,
    BUSINESS_STEP_1_50_100K,
    BUSINESS_STEP_1_200K,
    BUSINESS_STEP_1_UNSURE,
    BUSINESS_STEP_2_CALC,
    BUSINESS_STEP_3_GROWTH,
    get_business_registration_message,
    CONTACT_REQUEST,
    CONTACT_PHONE_REQUEST,
    CONTACT_EMAIL_REQUEST,
    CONTACT_THANKS,
    CONTACT_SKIP,
)
from curator_bot.funnels.referral_links import (
    get_shop_link,
    get_registration_link,
    format_product_message,
)
from loguru import logger


router = Router(name="callbacks")


# ============================================
# HELPER FUNCTIONS
# ============================================

async def update_user_funnel(
    telegram_id: int,
    user_intent: str = None,
    pain_point: str = None,
    income_goal: str = None,
    funnel_step: int = None,
    lead_status: str = None,
) -> User:
    """Обновляет данные воронки пользователя"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            if user_intent is not None:
                user.user_intent = user_intent
            if pain_point is not None:
                user.pain_point = pain_point
            if income_goal is not None:
                user.income_goal = income_goal
            if funnel_step is not None:
                user.funnel_step = funnel_step
            if lead_status is not None:
                user.lead_status = lead_status

            user.last_activity = datetime.utcnow()

            await session.commit()
            await session.refresh(user)

        return user


async def log_funnel_event(
    telegram_id: int,
    event_type: str,
    event_data: dict = None
):
    """Логирует событие воронки"""
    logger.info(f"Funnel event: user={telegram_id}, type={event_type}, data={event_data}")
    # TODO: Сохранять в таблицу funnel_events после миграции


# ============================================
# ЭТАП 1: ВЫБОР ПУТИ (intent)
# ============================================

@router.callback_query(F.data == "intent_client")
async def handle_client_intent(callback: CallbackQuery):
    """Пользователь выбрал 'Хочу улучшить здоровье'"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        user_intent="client",
        funnel_step=1,
        lead_status="qualified"
    )

    await log_funnel_event(
        telegram_id=callback.from_user.id,
        event_type="intent_selected",
        event_data={"intent": "client"}
    )

    await callback.message.edit_text(
        WELCOME_CLIENT,
        reply_markup=get_pain_keyboard()
    )


@router.callback_query(F.data == "intent_business")
async def handle_business_intent(callback: CallbackQuery):
    """Пользователь выбрал 'Интересует заработок'"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        user_intent="business",
        funnel_step=1,
        lead_status="qualified"
    )

    await log_funnel_event(
        telegram_id=callback.from_user.id,
        event_type="intent_selected",
        event_data={"intent": "business"}
    )

    await callback.message.edit_text(
        WELCOME_BUSINESS,
        reply_markup=get_income_goal_keyboard()
    )


@router.callback_query(F.data == "intent_curious")
async def handle_curious_intent(callback: CallbackQuery):
    """Пользователь выбрал 'Просто хочу узнать больше'"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        user_intent="curious",
        funnel_step=1,
        lead_status="cold"
    )

    await log_funnel_event(
        telegram_id=callback.from_user.id,
        event_type="intent_selected",
        event_data={"intent": "curious"}
    )

    await callback.message.edit_text(
        WELCOME_CURIOUS,
        reply_markup=get_start_keyboard()
    )


@router.callback_query(F.data == "back_to_start")
async def handle_back_to_start(callback: CallbackQuery):
    """Возврат к выбору пути"""
    await callback.answer()

    welcome_text = """<b>Привет! 👋</b>

Я AI-помощник для партнёров NL International.
Помогу разобраться в продуктах, бизнесе и ответить на любые вопросы.

<b>С чего начнём?</b>"""

    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_start_keyboard()
    )


# ============================================
# ЭТАП 1.2: ВЫБОР БОЛИ (для клиентов)
# ============================================

@router.callback_query(F.data == "pain_weight")
async def handle_pain_weight(callback: CallbackQuery):
    """Выбрана боль: Похудение"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        pain_point="weight",
        funnel_step=2
    )

    await log_funnel_event(
        telegram_id=callback.from_user.id,
        event_type="pain_selected",
        event_data={"pain": "weight"}
    )

    await callback.message.edit_text(
        CLIENT_WEIGHT_STEP_1,
        reply_markup=get_continue_keyboard()
    )


@router.callback_query(F.data == "pain_energy")
async def handle_pain_energy(callback: CallbackQuery):
    """Выбрана боль: Энергия"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        pain_point="energy",
        funnel_step=2
    )

    await callback.message.edit_text(
        CLIENT_ENERGY_STEP_1,
        reply_markup=get_continue_keyboard()
    )


@router.callback_query(F.data == "pain_immunity")
async def handle_pain_immunity(callback: CallbackQuery):
    """Выбрана боль: Иммунитет"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        pain_point="immunity",
        funnel_step=2
    )

    await callback.message.edit_text(
        CLIENT_IMMUNITY_STEP_1,
        reply_markup=get_continue_keyboard()
    )


@router.callback_query(F.data == "pain_beauty")
async def handle_pain_beauty(callback: CallbackQuery):
    """Выбрана боль: Красота"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        pain_point="beauty",
        funnel_step=2
    )

    await callback.message.edit_text(
        CLIENT_BEAUTY_STEP_1,
        reply_markup=get_continue_keyboard()
    )


@router.callback_query(F.data == "pain_kids")
async def handle_pain_kids(callback: CallbackQuery):
    """Выбрана боль: Дети"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        pain_point="kids",
        funnel_step=2
    )

    await callback.message.edit_text(
        CLIENT_KIDS_STEP_1,
        reply_markup=get_continue_keyboard()
    )


@router.callback_query(F.data == "pain_sport")
async def handle_pain_sport(callback: CallbackQuery):
    """Выбрана боль: Спорт"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        pain_point="sport",
        funnel_step=2
    )

    await callback.message.edit_text(
        CLIENT_SPORT_STEP_1,
        reply_markup=get_continue_keyboard()
    )


# ============================================
# ЭТАП 2: ПРОГРЕВ КЛИЕНТОВ
# ============================================

@router.callback_query(F.data == "funnel_continue")
async def handle_funnel_continue(callback: CallbackQuery):
    """Кнопка 'Продолжить' — переход к следующему шагу прогрева"""
    await callback.answer()

    # Получаем данные пользователя
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    if not user:
        await callback.message.answer("Пожалуйста, начни с /start")
        return

    pain_point = user.pain_point or "weight"
    current_step = user.funnel_step or 2

    # Логика перехода по шагам
    if pain_point == "weight":
        if current_step == 2:
            # Переход к шагу 3 (описание продукта)
            await update_user_funnel(
                telegram_id=callback.from_user.id,
                funnel_step=3
            )
            await callback.message.edit_text(
                CLIENT_WEIGHT_STEP_2,
                reply_markup=get_product_interest_keyboard()
            )
        elif current_step == 3:
            # Переход к шагу 4 (выбор цели по весу)
            await update_user_funnel(
                telegram_id=callback.from_user.id,
                funnel_step=4
            )
            await callback.message.edit_text(
                CLIENT_WEIGHT_STEP_3,
                reply_markup=get_weight_goal_keyboard()
            )
    else:
        # Для других болей — сразу показываем рекомендацию продукта
        await update_user_funnel(
            telegram_id=callback.from_user.id,
            funnel_step=4
        )
        product_message = format_product_message(pain_point)
        await callback.message.edit_text(
            product_message,
            reply_markup=get_order_keyboard(get_shop_link()),
            disable_web_page_preview=True
        )


@router.callback_query(F.data == "product_select")
async def handle_product_select(callback: CallbackQuery):
    """Клиент нажал 'Да, подбери для меня'"""
    await callback.answer()

    # Для похудения — спрашиваем цель по весу
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user and user.pain_point == "weight":
        await callback.message.edit_text(
            CLIENT_WEIGHT_STEP_3,
            reply_markup=get_weight_goal_keyboard()
        )
    else:
        # Для других болей — показываем рекомендацию
        pain_point = user.pain_point if user else "weight"
        product_message = format_product_message(pain_point)
        await callback.message.edit_text(
            product_message,
            reply_markup=get_order_keyboard(get_shop_link()),
            disable_web_page_preview=True
        )


@router.callback_query(F.data == "product_price")
async def handle_product_price(callback: CallbackQuery):
    """Клиент нажал 'Сколько это стоит?'"""
    await callback.answer()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    pain_point = user.pain_point if user else "weight"
    product_message = format_product_message(pain_point)

    await callback.message.edit_text(
        product_message,
        reply_markup=get_order_keyboard(get_shop_link()),
        disable_web_page_preview=True
    )


@router.callback_query(F.data == "product_questions")
async def handle_product_questions(callback: CallbackQuery):
    """Клиент нажал 'Есть вопросы'"""
    await callback.answer()

    await callback.message.answer(
        "<b>Конечно, задавай вопрос! 💬</b>\n\n"
        "Напиши, что тебя интересует — отвечу подробно."
    )


# ============================================
# ВЫБОР ЦЕЛИ ПО ВЕСУ
# ============================================

@router.callback_query(F.data.startswith("weight_"))
async def handle_weight_goal(callback: CallbackQuery):
    """Обработка выбора цели по весу"""
    await callback.answer()

    weight_goal = callback.data  # weight_5_10, weight_10_20, etc.

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        funnel_step=5,
        lead_status="hot"
    )

    await log_funnel_event(
        telegram_id=callback.from_user.id,
        event_type="product_shown",
        event_data={"weight_goal": weight_goal}
    )

    recommendation = get_client_weight_recommendation(weight_goal)

    await callback.message.edit_text(
        recommendation,
        reply_markup=get_order_keyboard(get_shop_link()),
        disable_web_page_preview=True
    )


# ============================================
# ЭТАП 1.3: ВЫБОР ЦЕЛИ ДОХОДА (для бизнеса)
# ============================================

@router.callback_query(F.data == "income_10_30k")
async def handle_income_10_30k(callback: CallbackQuery):
    """Выбрана цель: 10-30к/мес"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        income_goal="10_30k",
        funnel_step=2
    )

    await log_funnel_event(
        telegram_id=callback.from_user.id,
        event_type="income_selected",
        event_data={"income_goal": "10_30k"}
    )

    await callback.message.edit_text(
        BUSINESS_STEP_1_10_30K,
        reply_markup=get_business_continue_keyboard()
    )


@router.callback_query(F.data == "income_50_100k")
async def handle_income_50_100k(callback: CallbackQuery):
    """Выбрана цель: 50-100к/мес"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        income_goal="50_100k",
        funnel_step=2
    )

    await callback.message.edit_text(
        BUSINESS_STEP_1_50_100K,
        reply_markup=get_business_continue_keyboard()
    )


@router.callback_query(F.data == "income_200k_plus")
async def handle_income_200k_plus(callback: CallbackQuery):
    """Выбрана цель: 200к+/мес"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        income_goal="200k_plus",
        funnel_step=2
    )

    await callback.message.edit_text(
        BUSINESS_STEP_1_200K,
        reply_markup=get_business_continue_keyboard()
    )


@router.callback_query(F.data == "income_unsure")
async def handle_income_unsure(callback: CallbackQuery):
    """Выбрана цель: Пока не уверен"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        income_goal="unsure",
        funnel_step=2
    )

    await callback.message.edit_text(
        BUSINESS_STEP_1_UNSURE,
        reply_markup=get_business_continue_keyboard()
    )


# ============================================
# ЭТАП 2: ПРОГРЕВ БИЗНЕСА
# ============================================

@router.callback_query(F.data == "business_calc")
async def handle_business_calc(callback: CallbackQuery):
    """Показать расчёт дохода"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        funnel_step=3
    )

    await callback.message.edit_text(
        BUSINESS_STEP_2_CALC,
        reply_markup=get_business_next_keyboard()
    )


@router.callback_query(F.data == "business_next")
async def handle_business_next(callback: CallbackQuery):
    """Следующий шаг бизнес-прогрева"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        funnel_step=4,
        lead_status="hot"
    )

    await callback.message.edit_text(
        BUSINESS_STEP_3_GROWTH,
        reply_markup=get_registration_keyboard(get_registration_link())
    )


@router.callback_query(F.data == "business_questions")
async def handle_business_questions(callback: CallbackQuery):
    """Бизнес-лид нажал 'Есть вопросы'"""
    await callback.answer()

    await callback.message.answer(
        "<b>Конечно, задавай вопрос! 💬</b>\n\n"
        "Напиши, что тебя интересует про бизнес в NL — отвечу подробно."
    )


# ============================================
# ЭТАП 4: СБОР КОНТАКТОВ
# ============================================

@router.callback_query(F.data == "contact_phone")
async def handle_contact_phone(callback: CallbackQuery):
    """Запрос телефона"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        lead_status="contact_requested"
    )

    await callback.message.edit_text(CONTACT_PHONE_REQUEST)


@router.callback_query(F.data == "contact_email")
async def handle_contact_email(callback: CallbackQuery):
    """Запрос email"""
    await callback.answer()

    await update_user_funnel(
        telegram_id=callback.from_user.id,
        lead_status="contact_requested"
    )

    await callback.message.edit_text(CONTACT_EMAIL_REQUEST)


@router.callback_query(F.data == "contact_skip")
async def handle_contact_skip(callback: CallbackQuery):
    """Пользователь отказался от сбора контакта"""
    await callback.answer()

    await callback.message.edit_text(CONTACT_SKIP)


# ============================================
# НАПОМИНАНИЯ
# ============================================

@router.callback_query(F.data == "reminder_continue")
async def handle_reminder_continue(callback: CallbackQuery):
    """Пользователь хочет продолжить после напоминания"""
    await callback.answer()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user and user.user_intent == "client":
        # Показываем рекомендацию продукта
        pain_point = user.pain_point or "weight"
        product_message = format_product_message(pain_point)
        await callback.message.edit_text(
            product_message,
            reply_markup=get_order_keyboard(get_shop_link()),
            disable_web_page_preview=True
        )
    elif user and user.user_intent == "business":
        # Показываем регистрацию
        await callback.message.edit_text(
            get_business_registration_message(),
            disable_web_page_preview=True
        )
    else:
        await callback.message.edit_text(
            "Отлично! Напиши, чем могу помочь 👇"
        )


@router.callback_query(F.data == "reminder_later")
async def handle_reminder_later(callback: CallbackQuery):
    """Пользователь отложил на потом"""
    await callback.answer()

    await callback.message.edit_text(
        "Хорошо, напишу позже! 👌\n\n"
        "Если что-то понадобится раньше — просто напиши."
    )
