"""
Обработчики callback-кнопок
"""
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from sqlalchemy import select

from shared.config.settings import settings
from shared.database.base import AsyncSessionLocal
from content_manager_bot.ai.content_generator import ContentGenerator
from content_manager_bot.database.models import Post, AdminAction
from content_manager_bot.utils.keyboards import Keyboards
from content_manager_bot.handlers.admin import is_admin, generate_and_show_post

router = Router()

# Инициализируем генератор контента
content_generator = ContentGenerator()


class EditPostStates(StatesGroup):
    """Состояния для редактирования поста"""
    waiting_for_edit = State()
    waiting_for_feedback = State()
    waiting_for_custom_time = State()


# === Генерация по типу ===

@router.callback_query(F.data.startswith("gen_type:"))
async def callback_generate_by_type(callback: CallbackQuery):
    """Обработка выбора типа поста для генерации"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_type = callback.data.split(":")[1]

    await callback.message.edit_text(
        f"⏳ Генерирую пост типа: {post_type}..."
    )

    await generate_and_show_post(callback.message, post_type)
    await callback.answer()


# === Публикация ===

@router.callback_query(F.data.startswith("publish:"))
async def callback_publish(callback: CallbackQuery, bot: Bot):
    """Публикация поста в канал"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        # Получаем пост
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            await callback.answer("❌ Пост не найден", show_alert=True)
            return

        try:
            # Публикуем в канал
            channel_message = await bot.send_message(
                chat_id=settings.channel_username,
                text=post.content
            )

            # Обновляем статус поста
            post.status = "published"
            post.published_at = datetime.utcnow()
            post.approved_at = datetime.utcnow()
            post.admin_id = callback.from_user.id
            post.channel_message_id = channel_message.message_id

            # Логируем действие
            action = AdminAction(
                admin_id=callback.from_user.id,
                post_id=post_id,
                action="publish"
            )
            session.add(action)

            await session.commit()

            # Обновляем сообщение админу
            await callback.message.edit_text(
                f"✅ <b>Пост #{post_id} опубликован!</b>\n\n"
                f"{post.content[:300]}...\n\n"
                f"<i>Канал: {settings.channel_username}</i>"
            )

            logger.info(f"Post #{post_id} published to {settings.channel_username}")

        except Exception as e:
            logger.error(f"Error publishing post #{post_id}: {e}")
            await callback.answer(f"❌ Ошибка публикации: {str(e)}", show_alert=True)
            return

    await callback.answer("✅ Опубликовано!")


# === Планирование ===

@router.callback_query(F.data.startswith("schedule:"))
async def callback_schedule(callback: CallbackQuery):
    """Показать меню планирования публикации"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    await callback.message.edit_reply_markup(
        reply_markup=Keyboards.schedule_time_selection(post_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sched_time:"))
async def callback_schedule_time(callback: CallbackQuery):
    """Обработка выбора времени публикации"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    parts = callback.data.split(":")
    time_option = parts[1]
    post_id = int(parts[2])

    # Вычисляем время публикации
    now = datetime.utcnow()
    scheduled_time = None

    if time_option == "1h":
        scheduled_time = now + timedelta(hours=1)
    elif time_option == "3h":
        scheduled_time = now + timedelta(hours=3)
    elif time_option == "tomorrow_9":
        tomorrow = now.date() + timedelta(days=1)
        scheduled_time = datetime.combine(tomorrow, datetime.min.time().replace(hour=6))  # 9:00 MSK = 6:00 UTC
    elif time_option == "tomorrow_18":
        tomorrow = now.date() + timedelta(days=1)
        scheduled_time = datetime.combine(tomorrow, datetime.min.time().replace(hour=15))  # 18:00 MSK = 15:00 UTC
    elif time_option == "custom":
        await callback.message.edit_text(
            "📅 Введите дату и время публикации в формате:\n"
            "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
            "Например: <code>25.01.2026 14:30</code>"
        )
        # TODO: добавить FSM для кастомного времени
        await callback.answer()
        return

    if scheduled_time:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Post).where(Post.id == post_id)
            )
            post = result.scalar_one_or_none()

            if post:
                post.status = "scheduled"
                post.scheduled_for = scheduled_time

                action = AdminAction(
                    admin_id=callback.from_user.id,
                    post_id=post_id,
                    action="schedule",
                    details={"scheduled_for": scheduled_time.isoformat()}
                )
                session.add(action)

                await session.commit()

                # Время в московском часовом поясе (+3)
                msk_time = scheduled_time + timedelta(hours=3)

                await callback.message.edit_text(
                    f"📅 <b>Пост #{post_id} запланирован!</b>\n\n"
                    f"Время публикации: {msk_time.strftime('%d.%m.%Y %H:%M')} (МСК)\n\n"
                    f"<i>Пост будет автоматически опубликован в указанное время.</i>"
                )

    await callback.answer()


# === Редактирование ===

@router.callback_query(F.data.startswith("edit:"))
async def callback_edit(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    # Сохраняем ID поста в состояние
    await state.update_data(editing_post_id=post_id)
    await state.set_state(EditPostStates.waiting_for_edit)

    await callback.message.edit_text(
        f"📝 <b>Редактирование поста #{post_id}</b>\n\n"
        "Отправьте инструкции по редактированию.\n"
        "Например: «Сделай короче» или «Добавь больше эмодзи»\n\n"
        "<i>Или отправьте /cancel для отмены</i>"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("regenerate:"))
async def callback_regenerate(callback: CallbackQuery, state: FSMContext):
    """Перегенерация поста с обратной связью"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    await state.update_data(regenerating_post_id=post_id)
    await state.set_state(EditPostStates.waiting_for_feedback)

    await callback.message.edit_text(
        f"🔄 <b>Перегенерация поста #{post_id}</b>\n\n"
        "Напишите, что не понравилось или что нужно изменить.\n"
        "AI учтёт ваши пожелания при генерации нового варианта.\n\n"
        "<i>Или отправьте /cancel для отмены</i>"
    )
    await callback.answer()


# === Отклонение ===

@router.callback_query(F.data.startswith("reject:"))
async def callback_reject(callback: CallbackQuery):
    """Отклонение поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if post:
            post.status = "rejected"
            post.admin_id = callback.from_user.id

            action = AdminAction(
                admin_id=callback.from_user.id,
                post_id=post_id,
                action="reject"
            )
            session.add(action)

            await session.commit()

    await callback.message.edit_text(
        f"❌ <b>Пост #{post_id} отклонён</b>\n\n"
        "Используйте /generate для создания нового поста."
    )
    await callback.answer("Пост отклонён")


# === Отмена ===

@router.callback_query(F.data.startswith("cancel:"))
async def callback_cancel(callback: CallbackQuery):
    """Отмена текущего действия"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    # Возвращаем клавиатуру модерации
    await callback.message.edit_reply_markup(
        reply_markup=Keyboards.post_moderation(post_id)
    )
    await callback.answer("Отменено")


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    await callback.message.edit_text(
        "📋 <b>Главное меню</b>\n\n"
        "🔹 /generate - сгенерировать пост\n"
        "🔹 /pending - посты на модерации\n"
        "🔹 /stats - статистика\n"
        "🔹 /schedule - автопостинг"
    )
    await callback.answer()


# === Обработка текста в состояниях ===

@router.message(EditPostStates.waiting_for_edit)
async def process_edit_instructions(message: Message, state: FSMContext):
    """Обработка инструкций по редактированию"""
    if not is_admin(message.from_user.id):
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Редактирование отменено")
        return

    data = await state.get_data()
    post_id = data.get("editing_post_id")

    if not post_id:
        await state.clear()
        return

    status_msg = await message.answer("⏳ Редактирую пост...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            await status_msg.edit_text("❌ Пост не найден")
            await state.clear()
            return

        try:
            # Редактируем через AI
            new_content = await content_generator.edit_post(
                original_post=post.content,
                edit_instructions=message.text
            )

            post.content = new_content

            action = AdminAction(
                admin_id=message.from_user.id,
                post_id=post_id,
                action="edit",
                details={"instructions": message.text}
            )
            session.add(action)

            await session.commit()

            await status_msg.delete()

            type_names = ContentGenerator.get_available_post_types()
            type_name = type_names.get(post.post_type, post.post_type)

            await message.answer(
                f"📝 <b>Отредактированный пост ({type_name})</b>\n"
                f"ID: #{post_id}\n\n"
                f"{new_content}\n\n"
                f"<i>Что делаем с постом?</i>",
                reply_markup=Keyboards.post_moderation(post_id)
            )

        except Exception as e:
            logger.error(f"Error editing post: {e}")
            await status_msg.edit_text(f"❌ Ошибка редактирования: {str(e)}")

    await state.clear()


@router.message(EditPostStates.waiting_for_feedback)
async def process_regenerate_feedback(message: Message, state: FSMContext):
    """Обработка фидбека для перегенерации"""
    if not is_admin(message.from_user.id):
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Перегенерация отменена")
        return

    data = await state.get_data()
    post_id = data.get("regenerating_post_id")

    if not post_id:
        await state.clear()
        return

    status_msg = await message.answer("⏳ Генерирую новый вариант...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            await status_msg.edit_text("❌ Пост не найден")
            await state.clear()
            return

        try:
            # Перегенерируем через AI
            new_content = await content_generator.regenerate_post(
                original_post=post.content,
                feedback=message.text
            )

            post.content = new_content

            action = AdminAction(
                admin_id=message.from_user.id,
                post_id=post_id,
                action="regenerate",
                details={"feedback": message.text}
            )
            session.add(action)

            await session.commit()

            await status_msg.delete()

            type_names = ContentGenerator.get_available_post_types()
            type_name = type_names.get(post.post_type, post.post_type)

            await message.answer(
                f"🔄 <b>Перегенерированный пост ({type_name})</b>\n"
                f"ID: #{post_id}\n\n"
                f"{new_content}\n\n"
                f"<i>Что делаем с постом?</i>",
                reply_markup=Keyboards.post_moderation(post_id)
            )

        except Exception as e:
            logger.error(f"Error regenerating post: {e}")
            await status_msg.edit_text(f"❌ Ошибка перегенерации: {str(e)}")

    await state.clear()
