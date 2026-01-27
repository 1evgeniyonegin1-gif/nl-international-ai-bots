"""
Обработчики команд администратора
"""
from datetime import datetime
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config.settings import settings
from shared.database.base import AsyncSessionLocal
from shared.style_monitor import get_style_service
from content_manager_bot.ai.content_generator import ContentGenerator
from content_manager_bot.database.models import Post, PostStatus, AdminAction
from content_manager_bot.utils.keyboards import Keyboards
from content_manager_bot.analytics import StatsCollector, AnalyticsService

router = Router()

# Инициализируем генератор контента
content_generator = ContentGenerator()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in settings.admin_ids_list


async def get_pending_count() -> int:
    """Получить количество постов на модерации"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count(Post.id)).where(Post.status == "pending")
        )
        return result.scalar() or 0


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ Этот бот доступен только администраторам.\n"
            "Если вы администратор, убедитесь что ваш ID добавлен в настройки."
        )
        return

    pending_count = await get_pending_count()

    # Отправляем приветствие с reply-клавиатурой (кнопки внизу)
    await message.answer(
        "👋 <b>Добро пожаловать в AI-Контент-Менеджер!</b>\n\n"
        "Этот бот помогает создавать и публиковать контент "
        "в Telegram канал NL International.\n\n"
        "⬇️ <b>Используйте кнопки внизу для навигации</b>",
        reply_markup=Keyboards.reply_main_menu()
    )

    # Также показываем inline меню
    await message.answer(
        "🎛 <b>Или выберите действие здесь:</b>",
        reply_markup=Keyboards.main_menu(pending_count)
    )

    # Логируем действие
    async with AsyncSessionLocal() as session:
        action = AdminAction(
            admin_id=message.from_user.id,
            action="start_bot"
        )
        session.add(action)
        await session.commit()


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Обработчик команды /menu - показать главное меню"""
    if not is_admin(message.from_user.id):
        return

    pending_count = await get_pending_count()

    await message.answer(
        "🎛 <b>ГЛАВНОЕ МЕНЮ</b>\n\n"
        "Выберите действие:",
        reply_markup=Keyboards.main_menu(pending_count)
    )


# === Обработчики текстовых кнопок (Reply Keyboard) ===

@router.message(F.text == "📝 Создать пост")
async def btn_create_post(message: Message):
    """Кнопка: Создать пост"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📝 <b>СОЗДАНИЕ ПОСТА</b>\n\n"
        "Выберите тип контента:",
        reply_markup=Keyboards.post_type_selection_with_back()
    )


@router.message(F.text == "📋 На модерации")
async def btn_pending(message: Message):
    """Кнопка: На модерации"""
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Post)
            .where(Post.status == "pending")
            .order_by(Post.generated_at.desc())
            .limit(10)
        )
        posts = result.scalars().all()

    if not posts:
        await message.answer(
            "📭 <b>Нет постов на модерации</b>\n\n"
            "Используйте кнопку «📝 Создать пост» для генерации.",
            reply_markup=Keyboards.back_to_menu()
        )
        return

    type_names = ContentGenerator.get_available_post_types()

    await message.answer(f"📋 <b>Посты на модерации ({len(posts)}):</b>")

    for post in posts:
        type_name = type_names.get(post.post_type, post.post_type)
        preview = post.content[:200] + "..." if len(post.content) > 200 else post.content
        has_image = bool(post.image_url)

        await message.answer(
            f"📝 <b>#{post.id}</b> ({type_name})\n\n"
            f"{preview}\n\n"
            f"<i>Создан: {post.generated_at.strftime('%d.%m.%Y %H:%M')}</i>",
            reply_markup=Keyboards.post_moderation(post.id, has_image)
        )


@router.message(F.text == "📊 Статистика")
async def btn_stats(message: Message):
    """Кнопка: Статистика"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📊 <b>СТАТИСТИКА</b>\n\n"
        "Выберите период:",
        reply_markup=Keyboards.stats_menu()
    )


@router.message(F.text == "🏆 Топ посты")
async def btn_top(message: Message):
    """Кнопка: Топ посты"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🏆 <b>ТОП ПОСТЫ</b>\n\n"
        "Выберите метрику для сортировки:",
        reply_markup=Keyboards.top_posts_menu()
    )


@router.message(F.text == "⏰ Автопостинг")
async def btn_schedule(message: Message):
    """Кнопка: Автопостинг"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⏰ <b>АВТОПОСТИНГ</b>\n\n"
        "Включите/выключите автоматическую генерацию\n"
        "для каждого типа контента:",
        reply_markup=Keyboards.auto_schedule_settings()
    )


@router.message(F.text == "🎛 Меню")
async def btn_menu(message: Message):
    """Кнопка: Меню (показать inline меню)"""
    if not is_admin(message.from_user.id):
        return

    pending_count = await get_pending_count()

    await message.answer(
        "🎛 <b>ГЛАВНОЕ МЕНЮ</b>\n\n"
        "Выберите действие:",
        reply_markup=Keyboards.main_menu(pending_count)
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📖 <b>Справка по командам</b>\n\n"
        "<b>📝 ГЕНЕРАЦИЯ КОНТЕНТА</b>\n"
        "/generate - генерация нового поста\n"
        "  • /generate product - пост о продукте\n"
        "  • /generate motivation - мотивационный пост\n"
        "  • /generate success_story - история успеха\n\n"
        "/pending - посты ожидающие модерации\n\n"

        "<b>📊 АНАЛИТИКА</b>\n"
        "/stats - базовая статистика\n"
        "/analytics [дней] - детальная аналитика\n"
        "/update_stats - обновить из Telegram\n"
        "/top [views|reactions] [N] [дней] - топ постов\n\n"

        "<b>📺 КАНАЛЫ-ОБРАЗЦЫ (стиль)</b>\n"
        "/add_channel @username [категория] - добавить канал\n"
        "/channels - список каналов\n"
        "/fetch_posts - загрузить посты из каналов\n"
        "/remove_channel [id] - удалить канал\n\n"

        "<b>Категории стиля:</b>\n"
        "• motivation - мотивация\n"
        "• product - продукты\n"
        "• lifestyle - лайфстайл\n"
        "• business - бизнес\n\n"

        "<b>⚙️ НАСТРОЙКИ</b>\n"
        "/schedule - автоматическая генерация\n\n"

        "<b>Типы контента:</b>\n"
        "📦 product | 💪 motivation | 📰 news\n"
        "💡 tips | 🌟 success_story | 🎁 promo"
    )


@router.message(Command("generate"))
async def cmd_generate(message: Message):
    """Обработчик команды /generate"""
    if not is_admin(message.from_user.id):
        return

    # Парсим аргументы команды
    args = message.text.split(maxsplit=1)

    if len(args) == 1:
        # Без аргументов - показываем меню выбора
        await message.answer(
            "📝 <b>Выберите тип поста для генерации:</b>",
            reply_markup=Keyboards.post_type_selection()
        )
        return

    post_type = args[1].lower().strip()

    # Проверяем валидность типа
    valid_types = ContentGenerator.get_available_post_types()
    if post_type not in valid_types:
        await message.answer(
            f"❌ Неизвестный тип поста: {post_type}\n\n"
            f"Доступные типы: {', '.join(valid_types.keys())}"
        )
        return

    # Генерируем пост
    await generate_and_show_post(message, post_type)


async def generate_and_show_post(
    message: Message,
    post_type: str,
    custom_topic: Optional[str] = None
):
    """
    Генерирует пост и показывает админу на модерацию
    Автоматически подставляет фото продукта из базы, если найдено

    Args:
        message: Сообщение от админа
        post_type: Тип поста
        custom_topic: Дополнительная тема
    """
    from aiogram.types import BufferedInputFile
    import base64

    type_names = ContentGenerator.get_available_post_types()
    type_name = type_names.get(post_type, post_type)

    # Отправляем сообщение о генерации
    status_msg = await message.answer(f"⏳ Генерирую пост ({type_name})...")

    try:
        # Генерируем контент
        content, prompt_used = await content_generator.generate_post(
            post_type=post_type,
            custom_topic=custom_topic
        )

        # Сохраняем в БД
        async with AsyncSessionLocal() as session:
            post = Post(
                content=content,
                post_type=post_type,
                status="pending",
                generated_at=datetime.utcnow(),
                ai_model="GigaChat",
                prompt_used=prompt_used
            )
            session.add(post)
            await session.commit()
            await session.refresh(post)

            # Логируем действие
            action = AdminAction(
                admin_id=message.from_user.id,
                post_id=post.id,
                action="generate",
                details={"post_type": post_type}
            )
            session.add(action)
            await session.commit()

            post_id = post.id

        # Генерируем изображение (если доступно)
        has_image = False
        if content_generator.is_image_generation_available():
            try:
                await status_msg.edit_text(
                    f"⏳ Пост сгенерирован!\n"
                    f"🖼 Генерирую изображение ({type_name})...\n"
                    "Это может занять 30-60 секунд."
                )

                image_base64, image_prompt = await content_generator.generate_image(
                    post_type=post_type,
                    post_content=content
                )

                if image_base64:
                    # Сохраняем изображение в БД
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(
                            select(Post).where(Post.id == post_id)
                        )
                        post = result.scalar_one()
                        post.image_url = image_base64
                        post.image_prompt = image_prompt
                        post.image_status = "generated"
                        await session.commit()

                    has_image = True
                    logger.info(f"Image generated for post #{post_id}")
                else:
                    logger.warning(f"Failed to generate image for post #{post_id}")

            except Exception as e:
                logger.error(f"Error generating image for post #{post_id}: {e}")
                # Продолжаем без изображения

        # Удаляем статусное сообщение
        await status_msg.delete()

        # Показываем пост на модерацию
        if has_image:
            try:
                # Конвертируем base64 в файл
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(Post).where(Post.id == post_id)
                    )
                    post = result.scalar_one()

                    image_bytes = base64.b64decode(post.image_url)
                    image_file = BufferedInputFile(image_bytes, filename=f"post_{post_id}.jpg")

                    await message.answer_photo(
                        photo=image_file,
                        caption=(
                            f"📝 <b>Новый пост ({type_name})</b>\n"
                            f"ID: #{post_id}\n\n"
                            f"{content}\n\n"
                            f"<i>Что делаем с постом?</i>"
                        ),
                        reply_markup=Keyboards.post_moderation(post_id, has_image=True)
                    )
            except Exception as e:
                logger.error(f"Error showing image: {e}")
                # Фолбэк: показываем без изображения
                await message.answer(
                    f"📝 <b>Новый пост ({type_name})</b>\n"
                    f"ID: #{post_id}\n\n"
                    f"{content}\n\n"
                    f"🖼 <i>Изображение сгенерировано, но ошибка отображения</i>\n\n"
                    f"<i>Что делаем с постом?</i>",
                    reply_markup=Keyboards.post_moderation(post_id, has_image=True)
                )
        else:
            # Без изображения
            await message.answer(
                f"📝 <b>Новый пост ({type_name})</b>\n"
                f"ID: #{post_id}\n\n"
                f"{content}\n\n"
                f"<i>Что делаем с постом?</i>",
                reply_markup=Keyboards.post_moderation(post_id, has_image=False)
            )

    except Exception as e:
        logger.error(f"Error generating post: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка при генерации поста:\n{str(e)}\n\n"
            "Попробуйте ещё раз."
        )


@router.message(Command("pending"))
async def cmd_pending(message: Message):
    """Обработчик команды /pending - показать посты на модерации"""
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        # Получаем посты со статусом pending
        result = await session.execute(
            select(Post)
            .where(Post.status == "pending")
            .order_by(Post.generated_at.desc())
            .limit(10)
        )
        posts = result.scalars().all()

        if not posts:
            await message.answer(
                "📭 <b>Нет постов на модерации</b>\n\n"
                "Используйте /generate для создания нового поста."
            )
            return

        await message.answer(f"📋 <b>Посты на модерации ({len(posts)}):</b>")

        type_names = ContentGenerator.get_available_post_types()

        for post in posts:
            type_name = type_names.get(post.post_type, post.post_type)
            preview = post.content[:200] + "..." if len(post.content) > 200 else post.content

            await message.answer(
                f"📝 <b>#{post.id}</b> ({type_name})\n\n"
                f"{preview}\n\n"
                f"<i>Создан: {post.generated_at.strftime('%d.%m.%Y %H:%M')}</i>",
                reply_markup=Keyboards.post_moderation(post.id)
            )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Обработчик команды /stats - статистика"""
    if not is_admin(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        # Считаем статистику по статусам
        stats = {}
        for status in ["draft", "pending", "published", "rejected"]:
            result = await session.execute(
                select(func.count(Post.id)).where(Post.status == status)
            )
            stats[status] = result.scalar() or 0

        # Общее количество
        total_result = await session.execute(select(func.count(Post.id)))
        total = total_result.scalar() or 0

        # Статистика по типам
        type_stats_result = await session.execute(
            select(Post.post_type, func.count(Post.id))
            .where(Post.status == "published")
            .group_by(Post.post_type)
        )
        type_stats = {row[0]: row[1] for row in type_stats_result.all()}

    type_names = ContentGenerator.get_available_post_types()

    type_stats_text = "\n".join([
        f"  • {type_names.get(t, t)}: {c}"
        for t, c in type_stats.items()
    ]) or "  Пока нет публикаций"

    await message.answer(
        "📊 <b>Статистика контент-менеджера</b>\n\n"
        f"📝 Всего сгенерировано: <b>{total}</b>\n"
        f"✅ Опубликовано: <b>{stats['published']}</b>\n"
        f"⏳ На модерации: <b>{stats['pending']}</b>\n"
        f"📋 Черновики: <b>{stats['draft']}</b>\n"
        f"❌ Отклонено: <b>{stats['rejected']}</b>\n\n"
        f"<b>Опубликовано по типам:</b>\n{type_stats_text}\n\n"
        f"<i>Используйте /analytics для детальной аналитики постов</i>",
        reply_markup=Keyboards.analytics_menu()
    )


@router.message(Command("schedule"))
async def cmd_schedule(message: Message):
    """Обработчик команды /schedule - настройки автопостинга"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "⚙️ <b>Настройки автоматической генерации</b>\n\n"
        "Выберите тип контента для включения/отключения автопостинга:\n\n"
        "• <b>Продукты</b> — ежедневно в 10:00\n"
        "• <b>Мотивация</b> — ежедневно в 08:00\n"
        "• <b>Советы</b> — через день в 14:00\n"
        "• <b>Новости</b> — пн/ср/пт в 12:00\n"
        "• <b>Истории успеха</b> — вт/сб в 18:00\n"
        "• <b>Промо</b> — чт/вс в 16:00\n\n"
        "Нажмите на тип, чтобы включить/выключить.",
        reply_markup=Keyboards.auto_schedule_settings()
    )


@router.message(Command("analytics"))
async def cmd_analytics(message: Message):
    """Обработчик команды /analytics - детальная аналитика постов"""
    if not is_admin(message.from_user.id):
        return

    # Парсим аргументы команды
    args = message.text.split(maxsplit=1)
    days = 7  # По умолчанию 7 дней

    if len(args) > 1:
        try:
            days = int(args[1])
            if days < 1 or days > 365:
                days = 7
        except ValueError:
            days = 7

    status_msg = await message.answer("⏳ Собираю аналитику...")

    try:
        async with AsyncSessionLocal() as session:
            analytics_service = AnalyticsService(session)
            dashboard = await analytics_service.format_dashboard(days=days)

        await status_msg.delete()
        await message.answer(dashboard, reply_markup=Keyboards.analytics_menu())

    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка при генерации аналитики:\n{str(e)}"
        )


@router.message(Command("update_stats"))
async def cmd_update_stats(message: Message):
    """Обработчик команды /update_stats - обновление статистики всех постов"""
    if not is_admin(message.from_user.id):
        return

    from aiogram import Bot

    status_msg = await message.answer("⏳ Обновляю статистику постов из Telegram...")

    try:
        async with AsyncSessionLocal() as session:
            # Получаем бота из message
            bot = message.bot
            stats_collector = StatsCollector(bot, session)

            # Обновляем все опубликованные посты
            updated_count = await stats_collector.update_all_published_posts()

        await status_msg.edit_text(
            f"✅ Статистика обновлена!\n\n"
            f"Обновлено постов: {updated_count}\n\n"
            f"Используйте /analytics для просмотра аналитики."
        )

    except Exception as e:
        logger.error(f"Error updating stats: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка при обновлении статистики:\n{str(e)}"
        )


@router.message(Command("top"))
async def cmd_top(message: Message):
    """Обработчик команды /top - топ постов по метрикам"""
    if not is_admin(message.from_user.id):
        return

    # Парсим аргументы: /top [views|reactions|engagement] [количество] [дней]
    args = message.text.split()
    sort_by = args[1] if len(args) > 1 else 'engagement'
    limit = int(args[2]) if len(args) > 2 and args[2].isdigit() else 10
    days = int(args[3]) if len(args) > 3 and args[3].isdigit() else 30

    if sort_by not in ['views', 'reactions', 'engagement']:
        sort_by = 'engagement'

    status_msg = await message.answer("⏳ Получаю топ постов...")

    try:
        async with AsyncSessionLocal() as session:
            analytics_service = AnalyticsService(session)
            top_posts = await analytics_service.get_top_posts(
                limit=limit,
                days=days,
                sort_by=sort_by
            )

        if not top_posts:
            await status_msg.edit_text(
                f"📭 Нет опубликованных постов за последние {days} дней"
            )
            return

        sort_names = {
            'views': 'просмотрам',
            'reactions': 'реакциям',
            'engagement': 'вовлеченности'
        }

        type_names = {
            'product': '🛍️',
            'motivation': '💪',
            'news': '📰',
            'tips': '💡',
            'success_story': '⭐',
            'promo': '🎁'
        }

        response = f"🏆 <b>Топ-{limit} постов</b> (по {sort_names[sort_by]})\n"
        response += f"<i>За последние {days} дней</i>\n\n"

        for i, post in enumerate(top_posts, 1):
            emoji = type_names.get(post['type'], '📝')
            response += f"{i}. {emoji} ID #{post['id']}\n"
            response += f"   👁 {post['views']} | ❤️ {post['reactions']} | "
            response += f"📊 {post['engagement_rate']:.2f}%\n"
            response += f"   <i>{post['content_preview']}</i>\n\n"

        await status_msg.edit_text(response)

    except Exception as e:
        logger.error(f"Error getting top posts: {e}")
        await status_msg.edit_text(
            f"❌ Ошибка при получении топ постов:\n{str(e)}"
        )


# ============== КОМАНДЫ ДЛЯ КАНАЛОВ-ОБРАЗЦОВ ==============

@router.message(Command("add_channel"))
async def cmd_add_channel(message: Message):
    """
    Добавить канал для мониторинга стиля.
    Формат: /add_channel @username [категория] [описание]
    """
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=3)
    if len(args) < 2:
        await message.answer(
            "📺 <b>Добавление канала-образца</b>\n\n"
            "Формат: /add_channel @username [категория] [описание]\n\n"
            "Категории стиля:\n"
            "• <code>motivation</code> — мотивационный контент\n"
            "• <code>product</code> — посты о продуктах\n"
            "• <code>lifestyle</code> — лайфстайл контент\n"
            "• <code>business</code> — бизнес-контент\n"
            "• <code>general</code> — общий стиль\n\n"
            "Пример:\n"
            "<code>/add_channel @channel_name motivation Канал с мотивацией</code>"
        )
        return

    username = args[1]
    style_category = args[2] if len(args) > 2 else "general"
    description = args[3] if len(args) > 3 else None

    status_msg = await message.answer(f"⏳ Проверяю канал {username}...")

    try:
        style_service = get_style_service()
        channel = await style_service.add_channel(
            username_or_id=username,
            description=description,
            style_category=style_category
        )

        if channel:
            await status_msg.edit_text(
                f"✅ <b>Канал добавлен!</b>\n\n"
                f"📺 {channel.title}\n"
                f"🏷 Категория: {style_category}\n"
                f"📝 {description or 'Без описания'}\n\n"
                f"Используйте /fetch_posts для загрузки постов."
            )
        else:
            await status_msg.edit_text(
                f"❌ Не удалось добавить канал {username}.\n"
                "Возможные причины:\n"
                "• Канал не существует\n"
                "• Канал приватный\n"
                "• Канал уже добавлен\n"
                "• Не настроены Telethon credentials"
            )

    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


@router.message(Command("channels"))
async def cmd_channels(message: Message):
    """Показать список каналов-образцов."""
    if not is_admin(message.from_user.id):
        return

    try:
        style_service = get_style_service()
        channels = await style_service.get_active_channels()

        if not channels:
            await message.answer(
                "📭 <b>Нет каналов-образцов</b>\n\n"
                "Добавьте каналы командой:\n"
                "<code>/add_channel @username</code>"
            )
            return

        text = "📺 <b>Каналы-образцы для анализа стиля:</b>\n\n"
        for ch in channels:
            username = f"@{ch.username}" if ch.username else f"ID: {ch.channel_id}"
            text += f"• <b>{ch.title}</b> ({username})\n"
            text += f"  🏷 {ch.style_category or 'general'} | "
            text += f"📝 {ch.posts_count} постов\n"
            if ch.last_fetched_at:
                text += f"  ⏱ Обновлено: {ch.last_fetched_at.strftime('%d.%m %H:%M')}\n"
            text += "\n"

        await message.answer(text)

    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(Command("fetch_posts"))
async def cmd_fetch_posts(message: Message):
    """Загрузить посты из всех каналов-образцов."""
    if not is_admin(message.from_user.id):
        return

    status_msg = await message.answer("⏳ Загружаю посты из каналов-образцов...")

    try:
        style_service = get_style_service()
        stats = await style_service.fetch_all_channels(limit_per_channel=50)

        text = (
            f"✅ <b>Загрузка завершена!</b>\n\n"
            f"📺 Обработано каналов: {stats['channels_processed']}\n"
            f"📝 Новых постов: {stats['total_new_posts']}\n"
        )

        if stats['errors']:
            text += f"\n⚠️ Ошибки ({len(stats['errors'])}):\n"
            for err in stats['errors'][:3]:
                text += f"• {err}\n"

        await status_msg.edit_text(text)

    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}")


@router.message(Command("remove_channel"))
async def cmd_remove_channel(message: Message):
    """Удалить канал из мониторинга."""
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Формат: /remove_channel <channel_id>\n\n"
            "Используйте /channels чтобы увидеть ID каналов."
        )
        return

    try:
        channel_id = int(args[1])
        style_service = get_style_service()

        if await style_service.remove_channel(channel_id):
            await message.answer(f"✅ Канал {channel_id} удалён")
        else:
            await message.answer(f"❌ Канал {channel_id} не найден")

    except ValueError:
        await message.answer("❌ Неверный формат ID канала")
    except Exception as e:
        logger.error(f"Error removing channel: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


