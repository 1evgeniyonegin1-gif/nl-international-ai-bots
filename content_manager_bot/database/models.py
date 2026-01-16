"""
Модели базы данных для AI-Контент-Менеджера
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, BigInteger, Text, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
import enum

from shared.database.base import Base, TimestampMixin


class PostStatus(enum.Enum):
    """Статусы поста"""
    DRAFT = "draft"           # Черновик
    PENDING = "pending"       # На модерации
    APPROVED = "approved"     # Одобрен
    PUBLISHED = "published"   # Опубликован
    REJECTED = "rejected"     # Отклонён
    SCHEDULED = "scheduled"   # Запланирован


class PostType(enum.Enum):
    """Типы контента"""
    PRODUCT = "product"              # О продуктах NL
    MOTIVATION = "motivation"        # Мотивационные посты
    NEWS = "news"                    # Новости компании
    TIPS = "tips"                    # Советы по продажам
    SUCCESS_STORY = "success_story"  # Истории успеха
    PROMO = "promo"                  # Акции и предложения


class Post(Base, TimestampMixin):
    """Модель поста для публикации в канал"""
    __tablename__ = "content_posts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Контент поста
    content: Mapped[str] = mapped_column(Text)
    post_type: Mapped[str] = mapped_column(String(50), index=True)  # product, motivation, news, etc.

    # Статус
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)

    # Временные метки
    generated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(nullable=True, index=True)

    # Связь с Telegram
    channel_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Модерация
    admin_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI метаданные
    ai_model: Mapped[Optional[str]] = mapped_column(String(50))
    prompt_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_params: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Метрики (заполняются после публикации)
    views_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reactions_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, type={self.post_type}, status={self.status})>"

    def to_telegram_format(self) -> str:
        """Форматирует пост для отправки в Telegram"""
        return self.content


class ContentSchedule(Base, TimestampMixin):
    """Расписание автоматической генерации контента"""
    __tablename__ = "content_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Настройки генерации
    post_type: Mapped[str] = mapped_column(String(50))
    cron_expression: Mapped[str] = mapped_column(String(100))  # e.g., "0 9 * * *" = каждый день в 9:00

    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Временные метки
    last_run: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_run: Mapped[Optional[datetime]] = mapped_column(nullable=True, index=True)

    # Статистика
    total_generated: Mapped[int] = mapped_column(Integer, default=0)
    total_published: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<ContentSchedule(id={self.id}, type={self.post_type}, cron={self.cron_expression})>"


class AdminAction(Base, TimestampMixin):
    """Лог действий администраторов"""
    __tablename__ = "content_admin_actions"

    id: Mapped[int] = mapped_column(primary_key=True)

    admin_id: Mapped[int] = mapped_column(BigInteger, index=True)
    post_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    action: Mapped[str] = mapped_column(String(50))  # generate, approve, reject, publish, edit
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AdminAction(id={self.id}, admin={self.admin_id}, action={self.action})>"
