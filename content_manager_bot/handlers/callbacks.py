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
from content_manager_bot.database.models import Post, AdminAction, ContentSchedule
from content_manager_bot.utils.keyboards import Keyboards
from content_manager_bot.handlers.admin import is_admin, generate_and_show_post
from content_manager_bot.scheduler.content_scheduler import ContentScheduler

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
    import base64
    from aiogram.types import BufferedInputFile

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
            # Определяем куда публиковать (тема в группе)
            topic_id = settings.get_topic_id(post.post_type)

            # Добавляем ссылку на куратора в конец поста
            post_with_curator = (
                f"{post.content}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"❓ Есть вопросы? Спроси AI-Куратора → {settings.curator_bot_username}"
            )

            # Публикуем в группу с Topics или в канал
            target_chat = settings.group_id if settings.group_id and topic_id else settings.channel_username
            publish_target = f"группа (тема #{topic_id})" if settings.group_id and topic_id else settings.channel_username

            # Если есть изображение - публикуем с изображением
            if post.image_url:
                try:
                    # Конвертируем base64 в файл
                    image_bytes = base64.b64decode(post.image_url)
                    image_file = BufferedInputFile(image_bytes, filename=f"post_{post_id}.jpg")

                    if settings.group_id and topic_id:
                        channel_message = await bot.send_photo(
                            chat_id=target_chat,
                            photo=image_file,
                            caption=post_with_curator,
                            message_thread_id=topic_id
                        )
                    else:
                        channel_message = await bot.send_photo(
                            chat_id=target_chat,
                            photo=image_file,
                            caption=post_with_curator
                        )
                except Exception as e:
                    logger.error(f"Error sending image for post #{post_id}: {e}")
                    # Фолбэк: публикуем без изображения
                    if settings.group_id and topic_id:
                        channel_message = await bot.send_message(
                            chat_id=target_chat,
                            text=post_with_curator,
                            message_thread_id=topic_id
                        )
                    else:
                        channel_message = await bot.send_message(
                            chat_id=target_chat,
                            text=post_with_curator
                        )
            else:
                # Публикуем без изображения
                if settings.group_id and topic_id:
                    channel_message = await bot.send_message(
                        chat_id=target_chat,
                        text=post_with_curator,
                        message_thread_id=topic_id
                    )
                else:
                    channel_message = await bot.send_message(
                        chat_id=target_chat,
                        text=post_with_curator
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
                action="publish",
                details={"topic_id": topic_id, "has_image": bool(post.image_url)} if topic_id else {"has_image": bool(post.image_url)}
            )
            session.add(action)

            await session.commit()

            # Обновляем сообщение админу
            image_info = "🖼 с изображением" if post.image_url else ""
            await callback.message.edit_text(
                f"✅ <b>Пост #{post_id} опубликован! {image_info}</b>\n\n"
                f"{post.content[:300]}...\n\n"
                f"<i>Опубликовано в: {publish_target}</i>"
            )

            logger.info(f"Post #{post_id} published to {publish_target} (with_image={bool(post.image_url)})")

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


# === Автопостинг ===

@router.callback_query(F.data.startswith("autosched:"))
async def callback_autoschedule(callback: CallbackQuery):
    """Управление автопостингом"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    action = callback.data.split(":")[1]
    logger.info(f"Autoschedule callback: action={action}, user={callback.from_user.id}")

    try:
        if action == "status":
            # Показываем статус расписаний
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(ContentSchedule))
                schedules = result.scalars().all()

                if not schedules:
                    await callback.message.edit_text(
                        "📅 <b>Расписание автопостинга</b>\n\n"
                        "Пока нет активных расписаний.\n\n"
                        "Нажмите на тип поста чтобы включить автогенерацию:",
                        reply_markup=Keyboards.auto_schedule_settings()
                    )
                else:
                    status_text = "📅 <b>Расписание автопостинга</b>\n\n"
                    type_names = ContentGenerator.get_available_post_types()

                    for sched in schedules:
                        type_name = type_names.get(sched.post_type, sched.post_type)
                        status_emoji = "✅" if sched.is_active else "❌"
                        next_run = sched.next_run.strftime("%d.%m %H:%M") if sched.next_run else "—"

                        status_text += f"{status_emoji} {type_name}\n"
                        status_text += f"   Следующий: {next_run}\n"
                        status_text += f"   Всего: {sched.total_generated} постов\n\n"

                    await callback.message.edit_text(
                        status_text,
                        reply_markup=Keyboards.auto_schedule_settings()
                    )

        else:
            # Включаем/выключаем расписание для типа поста
            post_type = action

            # Используем конфигурацию из ContentScheduler (единый источник истины)
            config = ContentScheduler.SCHEDULE_CONFIG.get(post_type, {"hours": 24, "desc": "ежедневно"})

            async with AsyncSessionLocal() as session:
                # Ищем существующее расписание
                result = await session.execute(
                    select(ContentSchedule).where(ContentSchedule.post_type == post_type)
                )
                schedule = result.scalar_one_or_none()

                if schedule:
                    # Переключаем статус
                    schedule.is_active = not schedule.is_active
                    status = "включен" if schedule.is_active else "выключен"
                else:
                    # Создаём новое расписание с настройками для типа
                    schedule = ContentSchedule(
                        post_type=post_type,
                        cron_expression=f"Every {config['hours']} hours",  # Описательное поле для справки
                        is_active=True,
                        next_run=datetime.utcnow() + timedelta(hours=config["hours"]),
                        total_generated=0
                    )
                    session.add(schedule)
                    status = "включен"
                    logger.info(f"Created new schedule for {post_type}: interval={config['hours']}h, next_run={schedule.next_run}")

                await session.commit()

            type_names = ContentGenerator.get_available_post_types()
            type_name = type_names.get(post_type, post_type)

            await callback.answer(f"Автопостинг {type_name}: {status}", show_alert=True)

            # Обновляем меню с информацией о расписании
            await callback.message.edit_text(
                "⚙️ <b>Настройки автопостинга</b>\n\n"
                f"{'✅' if status == 'включен' else '❌'} <b>{type_name}</b>: {status}\n"
                f"📅 Расписание: {config['desc']}\n\n"
                "<i>Бот будет генерировать посты и присылать на модерацию.</i>",
                reply_markup=Keyboards.auto_schedule_settings()
            )

    except Exception as e:
        logger.error(f"Error in autoschedule callback: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)


# === Работа с изображениями ===

@router.callback_query(F.data.startswith("gen_image:"))
async def callback_generate_image(callback: CallbackQuery):
    """Генерация изображения для поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    # Проверяем доступность генерации
    if not content_generator.is_image_generation_available():
        await callback.answer(
            "❌ Генерация изображений недоступна. Проверьте настройки YandexART.",
            show_alert=True
        )
        return

    await callback.answer("⏳ Генерирую изображение...")

    # Обновляем сообщение
    await callback.message.edit_text(
        f"🖼 Генерирую изображение для поста #{post_id}...\n"
        "Это может занять 30-60 секунд."
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            await callback.message.edit_text("❌ Пост не найден")
            return

        try:
            # Генерируем изображение
            image_base64, image_prompt = await content_generator.generate_image(
                post_type=post.post_type,
                post_content=post.content
            )

            if image_base64:
                # Сохраняем в БД
                post.image_url = image_base64
                post.image_prompt = image_prompt
                post.image_status = "generated"

                action = AdminAction(
                    admin_id=callback.from_user.id,
                    post_id=post_id,
                    action="generate_image",
                    details={"prompt": image_prompt}
                )
                session.add(action)
                await session.commit()

                # Показываем пост с изображением
                await _show_post_with_image(callback.message, post)

                logger.info(f"Image generated for post #{post_id}")

            else:
                await callback.message.edit_text(
                    f"❌ Не удалось сгенерировать изображение для поста #{post_id}\n\n"
                    "Попробуйте ещё раз или продолжите без изображения.",
                    reply_markup=Keyboards.post_moderation(post_id, has_image=False)
                )

        except Exception as e:
            logger.error(f"Error generating image for post #{post_id}: {e}")
            await callback.message.edit_text(
                f"❌ Ошибка при генерации изображения:\n{str(e)}\n\n"
                "Попробуйте ещё раз или продолжите без изображения.",
                reply_markup=Keyboards.post_moderation(post_id, has_image=False)
            )


@router.callback_query(F.data.startswith("regen_image:"))
async def callback_regenerate_image(callback: CallbackQuery, state: FSMContext):
    """Перегенерация изображения с возможностью указать фидбек"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    # Проверяем доступность генерации
    if not content_generator.is_image_generation_available():
        await callback.answer(
            "❌ Генерация изображений недоступна. Проверьте настройки YandexART.",
            show_alert=True
        )
        return

    await callback.answer("⏳ Генерирую новое изображение...")

    # Обновляем сообщение
    await callback.message.edit_text(
        f"🖼 Генерирую новое изображение для поста #{post_id}...\n"
        "Это может занять 30-60 секунд."
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            await callback.message.edit_text("❌ Пост не найден")
            return

        try:
            # Перегенерируем изображение (с другим seed - получится другой результат)
            image_base64, image_prompt = await content_generator.generate_image(
                post_type=post.post_type,
                post_content=post.content
            )

            if image_base64:
                # Обновляем в БД
                post.image_url = image_base64
                post.image_prompt = image_prompt
                post.image_status = "generated"

                action = AdminAction(
                    admin_id=callback.from_user.id,
                    post_id=post_id,
                    action="regenerate_image",
                    details={"prompt": image_prompt}
                )
                session.add(action)
                await session.commit()

                # Показываем пост с новым изображением
                await _show_post_with_image(callback.message, post)

                logger.info(f"Image regenerated for post #{post_id}")

            else:
                await callback.message.edit_text(
                    f"❌ Не удалось сгенерировать изображение для поста #{post_id}\n\n"
                    "Попробуйте ещё раз.",
                    reply_markup=Keyboards.post_moderation(post_id, has_image=bool(post.image_url))
                )

        except Exception as e:
            logger.error(f"Error regenerating image for post #{post_id}: {e}")
            await callback.message.edit_text(
                f"❌ Ошибка при генерации изображения:\n{str(e)}",
                reply_markup=Keyboards.post_moderation(post_id, has_image=bool(post.image_url))
            )


@router.callback_query(F.data.startswith("remove_image:"))
async def callback_remove_image(callback: CallbackQuery):
    """Удаление изображения из поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return

    post_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if not post:
            await callback.answer("❌ Пост не найден", show_alert=True)
            return

        # Удаляем изображение
        post.image_url = None
        post.image_prompt = None
        post.image_status = None

        action = AdminAction(
            admin_id=callback.from_user.id,
            post_id=post_id,
            action="remove_image"
        )
        session.add(action)
        await session.commit()

        type_names = ContentGenerator.get_available_post_types()
        type_name = type_names.get(post.post_type, post.post_type)

        # Показываем пост без изображения
        await callback.message.edit_text(
            f"📝 <b>Пост ({type_name})</b>\n"
            f"ID: #{post_id}\n\n"
            f"{post.content}\n\n"
            f"<i>Что делаем с постом?</i>",
            reply_markup=Keyboards.post_moderation(post_id, has_image=False)
        )

    await callback.answer("✅ Изображение удалено")
    logger.info(f"Image removed from post #{post_id}")


async def _show_post_with_image(message: Message, post: Post):
    """
    Helper функция для показа поста с изображением

    Args:
        message: Сообщение для редактирования
        post: Объект поста с изображением
    """
    import base64
    import io
    from aiogram.types import BufferedInputFile

    type_names = ContentGenerator.get_available_post_types()
    type_name = type_names.get(post.post_type, post.post_type)

    try:
        # Конвертируем base64 в файл
        image_bytes = base64.b64decode(post.image_url)
        image_file = BufferedInputFile(image_bytes, filename=f"post_{post.id}.jpg")

        # Удаляем старое сообщение (с текстом "генерирую...")
        try:
            await message.delete()
        except:
            pass

        # Отправляем новое сообщение с изображением
        await message.answer_photo(
            photo=image_file,
            caption=(
                f"📝 <b>Пост ({type_name})</b>\n"
                f"ID: #{post.id}\n\n"
                f"{post.content}\n\n"
                f"<i>Что делаем с постом?</i>"
            ),
            reply_markup=Keyboards.post_moderation(post.id, has_image=True)
        )

    except Exception as e:
        logger.error(f"Error showing post with image: {e}")
        # Фолбэк: показываем без изображения
        await message.edit_text(
            f"📝 <b>Пост ({type_name})</b>\n"
            f"ID: #{post.id}\n\n"
            f"{post.content}\n\n"
            f"🖼 <i>Изображение сгенерировано, но ошибка отображения</i>\n\n"
            f"<i>Что делаем с постом?</i>",
            reply_markup=Keyboards.post_moderation(post.id, has_image=True)
        )
