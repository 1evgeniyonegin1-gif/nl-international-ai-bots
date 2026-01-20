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

    # Изображения (YandexART)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # URL или base64 изображения
    image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Промпт для генерации
    image_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # pending, generated, approved, rejected

    # Метрики (заполняются после публикации)
    views_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    reactions_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    forwards_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    # Детальная аналитика реакций (JSONB для хранения разбивки по типам)
    reactions_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Метрики эффективности
    engagement_rate: Mapped[Optional[float]] = mapped_column(nullable=True)  # (реакции + пересылки) / просмотры
    last_metrics_update: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, type={self.post_type}, status={self.status})>"

    def to_telegram_format(self) -> str:
        """Форматирует пост для отправки в Telegram"""
        return self.content

    def calculate_engagement_rate(self) -> Optional[float]:
        """Рассчитывает коэффициент вовлеченности (engagement rate)"""
        if not self.views_count or self.views_count == 0:
            return None

        total_engagement = (self.reactions_count or 0) + (self.forwards_count or 0)
        return round((total_engagement / self.views_count) * 100, 2)

    def update_engagement_rate(self):
        """Обновляет расчетный коэффициент вовлеченности"""
        self.engagement_rate = self.calculate_engagement_rate()
        self.last_metrics_update = datetime.utcnow()


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


class PostAnalytics(Base, TimestampMixin):
    """Детальная аналитика поста (исторические снимки метрик)"""
    __tablename__ = "content_post_analytics"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Связь с постом
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    channel_message_id: Mapped[int] = mapped_column(BigInteger)

    # Метрики на момент снимка
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    reactions_count: Mapped[int] = mapped_column(Integer, default=0)
    forwards_count: Mapped[int] = mapped_column(Integer, default=0)

    # Детальная разбивка реакций
    reactions_breakdown: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Пример: {"👍": 10, "❤️": 5, "🔥": 3}

    # Временная метка снимка
    snapshot_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    # Прирост с предыдущего снимка
    views_delta: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reactions_delta: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<PostAnalytics(post_id={self.post_id}, views={self.views_count}, reactions={self.reactions_count})>"


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
