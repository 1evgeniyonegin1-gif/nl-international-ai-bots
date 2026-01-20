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


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ Этот бот доступен только администраторам.\n"
            "Если вы администратор, убедитесь что ваш ID добавлен в настройки."
        )
        return

    await message.answer(
        "👋 <b>Добро пожаловать в AI-Контент-Менеджер!</b>\n\n"
        "Этот бот помогает создавать и публиковать контент "
        "в Telegram канал NL International.\n\n"
        "<b>Доступные команды:</b>\n"
        "🔹 /generate - сгенерировать новый пост\n"
        "🔹 /pending - посты на модерации\n"
        "🔹 /stats - статистика публикаций\n"
        "🔹 /schedule - настройки автопостинга\n"
        "🔹 /help - справка по командам\n\n"
        f"<i>Канал: {settings.channel_username}</i>"
    )

    # Логируем действие
    async with AsyncSessionLocal() as session:
        action = AdminAction(
            admin_id=message.from_user.id,
            action="start_bot"
        )
        session.add(action)
        await session.commit()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📖 <b>Справка по командам</b>\n\n"
        "<b>/generate</b> - генерация нового поста\n"
        "  • /generate - показать меню выбора типа\n"
        "  • /generate product - пост о продукте\n"
        "  • /generate motivation - мотивационный пост\n"
        "  • /generate news - новость\n"
        "  • /generate tips - советы\n"
        "  • /generate success_story - история успеха\n"
        "  • /generate promo - акция/промо\n\n"
        "<b>/pending</b> - посты ожидающие модерации\n\n"
        "<b>/stats</b> - базовая статистика:\n"
        "  • Всего сгенерировано\n"
        "  • Опубликовано\n"
        "  • Отклонено\n"
        "  • На модерации\n\n"
        "<b>/analytics</b> [дней] - детальная аналитика постов\n"
        "  • /analytics - за 7 дней\n"
        "  • /analytics 30 - за 30 дней\n\n"
        "<b>/update_stats</b> - обновить статистику из Telegram\n"
        "  (собирает просмотры и реакции)\n\n"
        "<b>/top</b> [критерий] [количество] [дней] - топ постов\n"
        "  • /top - топ-10 по вовлеченности за 30 дней\n"
        "  • /top views - топ по просмотрам\n"
        "  • /top reactions 5 7 - топ-5 по реакциям за 7 дней\n\n"
        "<b>/schedule</b> - настройки автоматической генерации\n\n"
        "<b>Типы контента:</b>\n"
        "📦 product - о продуктах NL\n"
        "💪 motivation - мотивация для партнёров\n"
        "📰 news - новости компании\n"
        "💡 tips - советы по продажам\n"
        "🌟 success_story - истории успеха\n"
        "🎁 promo - акции и предложения"
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
    Автоматически генерирует изображение, если YandexART доступен

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
        "Здесь вы можете настроить автоматическую генерацию постов "
        "по расписанию.\n\n"
        "<i>Функция в разработке...</i>",
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


