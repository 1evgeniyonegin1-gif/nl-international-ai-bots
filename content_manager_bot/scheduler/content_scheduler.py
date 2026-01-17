"""
Планировщик автоматической генерации и публикации контента
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from aiogram import Bot
from loguru import logger
from sqlalchemy import select, and_

from shared.config.settings import settings
from shared.database.base import AsyncSessionLocal
from content_manager_bot.database.models import Post, ContentSchedule
from content_manager_bot.ai.content_generator import ContentGenerator
from content_manager_bot.utils.keyboards import Keyboards


class ContentScheduler:
    """
    Планировщик для автоматической публикации запланированных постов
    и генерации нового контента по расписанию
    """

    def __init__(self, bot: Bot):
        """
        Инициализация планировщика

        Args:
            bot: Экземпляр бота для публикации
        """
        self.bot = bot
        self.content_generator = ContentGenerator()
        self.running = False
        self._task: Optional[asyncio.Task] = None
        logger.info("ContentScheduler initialized")

    async def start(self):
        """Запуск планировщика"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("ContentScheduler started")

    async def stop(self):
        """Остановка планировщика"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ContentScheduler stopped")

    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.running:
            try:
                # Проверяем запланированные посты
                await self._publish_scheduled_posts()

                # Проверяем расписание автогенерации
                await self._check_auto_generation()

                # Ждём 60 секунд до следующей проверки
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)

    async def _publish_scheduled_posts(self):
        """Публикация постов, время которых наступило"""
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()

            # Находим посты для публикации
            result = await session.execute(
                select(Post).where(
                    and_(
                        Post.status == "scheduled",
                        Post.scheduled_for <= now
                    )
                )
            )
            posts = result.scalars().all()

            for post in posts:
                try:
                    await self._publish_post(post, session)
                except Exception as e:
                    logger.error(f"Error publishing scheduled post #{post.id}: {e}")

    async def _publish_post(self, post: Post, session):
        """
        Публикация поста в группу с Topics или канал

        Args:
            post: Пост для публикации
            session: Сессия БД
        """
        try:
            # Определяем куда публиковать (тема в группе)
            topic_id = settings.get_topic_id(post.post_type)

            # Добавляем ссылку на куратора
            post_with_curator = (
                f"{post.content}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"❓ Есть вопросы? Спроси AI-Куратора → {settings.curator_bot_username}"
            )

            # Публикуем в группу с Topics или в канал
            if settings.group_id and topic_id:
                message = await self.bot.send_message(
                    chat_id=settings.group_id,
                    text=post_with_curator,
                    message_thread_id=topic_id
                )
                publish_target = f"группа (тема #{topic_id})"
            else:
                message = await self.bot.send_message(
                    chat_id=settings.channel_username,
                    text=post_with_curator
                )
                publish_target = settings.channel_username

            # Обновляем статус
            post.status = "published"
            post.published_at = datetime.utcnow()
            post.channel_message_id = message.message_id

            await session.commit()

            logger.info(f"Scheduled post #{post.id} published to {publish_target}")

            # Уведомляем админов
            await self._notify_admins(
                f"📢 Автопубликация\n\n"
                f"Пост #{post.id} опубликован в {publish_target} по расписанию."
            )

        except Exception as e:
            logger.error(f"Failed to publish post #{post.id}: {e}")
            raise

    async def _check_auto_generation(self):
        """Проверка расписания автоматической генерации"""
        async with AsyncSessionLocal() as session:
            now = datetime.utcnow()

            # Находим активные расписания, время которых наступило
            result = await session.execute(
                select(ContentSchedule).where(
                    and_(
                        ContentSchedule.is_active == True,
                        ContentSchedule.next_run <= now
                    )
                )
            )
            schedules = result.scalars().all()

            for schedule in schedules:
                try:
                    await self._run_auto_generation(schedule, session)
                except Exception as e:
                    logger.error(f"Error in auto generation for schedule #{schedule.id}: {e}")

    async def _run_auto_generation(self, schedule: ContentSchedule, session):
        """
        Запуск автоматической генерации по расписанию

        Args:
            schedule: Расписание
            session: Сессия БД
        """
        logger.info(f"Running auto generation for schedule #{schedule.id} ({schedule.post_type})")

        # Генерируем пост
        content, prompt_used = await self.content_generator.generate_post(
            post_type=schedule.post_type
        )

        # Сохраняем как pending (требует модерации)
        post = Post(
            content=content,
            post_type=schedule.post_type,
            status="pending",
            generated_at=datetime.utcnow(),
            ai_model="GigaChat",
            prompt_used=prompt_used
        )
        session.add(post)

        # Обновляем расписание
        schedule.last_run = datetime.utcnow()
        schedule.total_generated += 1

        # Вычисляем следующий запуск (пока простая логика - через 24 часа)
        schedule.next_run = datetime.utcnow() + timedelta(days=1)

        await session.commit()
        await session.refresh(post)

        logger.info(f"Auto generated post #{post.id} ({schedule.post_type})")

        # Отправляем пост админам сразу с кнопками модерации
        type_names = ContentGenerator.get_available_post_types()
        type_name = type_names.get(schedule.post_type, schedule.post_type)

        await self._send_post_for_moderation(
            post_id=post.id,
            content=content,
            post_type=type_name
        )

    async def _send_post_for_moderation(self, post_id: int, content: str, post_type: str):
        """
        Отправка поста админам с кнопками модерации

        Args:
            post_id: ID поста
            content: Текст поста
            post_type: Название типа поста
        """
        message_text = (
            f"🤖 <b>Автогенерация: {post_type}</b>\n"
            f"ID: #{post_id}\n\n"
            f"{content}\n\n"
            f"<i>Что делаем с постом?</i>"
        )

        for admin_id in settings.admin_ids_list:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message_text,
                    reply_markup=Keyboards.post_moderation(post_id)
                )
            except Exception as e:
                logger.error(f"Failed to send post for moderation to admin {admin_id}: {e}")

    async def _notify_admins(self, message: str):
        """
        Уведомление всех админов

        Args:
            message: Текст уведомления
        """
        for admin_id in settings.admin_ids_list:
            try:
                await self.bot.send_message(chat_id=admin_id, text=message)
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

    async def add_schedule(
        self,
        post_type: str,
        cron_expression: str = "0 9 * * *"
    ) -> ContentSchedule:
        """
        Добавление нового расписания автогенерации

        Args:
            post_type: Тип поста
            cron_expression: Cron выражение (по умолчанию каждый день в 9:00)

        Returns:
            ContentSchedule: Созданное расписание
        """
        async with AsyncSessionLocal() as session:
            schedule = ContentSchedule(
                post_type=post_type,
                cron_expression=cron_expression,
                is_active=True,
                next_run=datetime.utcnow() + timedelta(days=1)
            )
            session.add(schedule)
            await session.commit()
            await session.refresh(schedule)

            logger.info(f"Created schedule #{schedule.id} for {post_type}")
            return schedule

    async def get_schedules(self) -> List[ContentSchedule]:
        """
        Получение всех активных расписаний

        Returns:
            List[ContentSchedule]: Список расписаний
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ContentSchedule).where(ContentSchedule.is_active == True)
            )
            return result.scalars().all()

    async def toggle_schedule(self, schedule_id: int) -> bool:
        """
        Включение/выключение расписания

        Args:
            schedule_id: ID расписания

        Returns:
            bool: Новое состояние (True = активно)
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ContentSchedule).where(ContentSchedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()

            if schedule:
                schedule.is_active = not schedule.is_active
                await session.commit()
                return schedule.is_active

            return False
