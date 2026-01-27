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

    # Изображения (фото из базы unified_products/)
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


class MoodState(Base, TimestampMixin):
    """Текущее настроение бота (меняется раз в день или по триггеру)"""
    __tablename__ = "content_mood_states"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Дата настроения
    date: Mapped[datetime] = mapped_column(index=True, default=datetime.utcnow)

    # Категория настроения (joy, sadness, anger, fear, etc.)
    category: Mapped[str] = mapped_column(String(50))

    # Конкретная эмоция (e.g., "ecstatic", "melancholy")
    emotion: Mapped[str] = mapped_column(String(50))

    # Интенсивность (light, medium, strong, extreme)
    intensity: Mapped[str] = mapped_column(String(20))

    # Версия персоны Данила (expert, friend, rebel, philosopher, crazy, tired)
    persona_version: Mapped[str] = mapped_column(String(50))

    # Событие-триггер (если есть)
    trigger: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Текущее или историческое
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    def __repr__(self) -> str:
        return f"<MoodState(date={self.date.date()}, emotion={self.emotion}, persona={self.persona_version})>"


class MediaAsset(Base, TimestampMixin):
    """Медиа-ресурс (мем, гифка, стикер, фото продукта, чек партнёра)"""
    __tablename__ = "content_media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Telegram file_id (опционально для локальных файлов)
    file_id: Mapped[Optional[str]] = mapped_column(String(200), unique=True, index=True, nullable=True)

    # Тип файла (gif, image, sticker, video)
    file_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # ====== НОВЫЕ ПОЛЯ ДЛЯ ИНДЕКСИРОВАННОГО ПОИСКА ======
    # Тип ресурса (product, testimonial, sticker, gif)
    asset_type: Mapped[str] = mapped_column(String(50), default="sticker", index=True)

    # Ключевые слова для поиска ["коллаген", "collagen", "peptides"]
    keywords: Mapped[Optional[list]] = mapped_column(JSONB, default=list, nullable=True)

    # Описание (особенно для testimonials)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Связанные продукты NL ["3d_slim", "omega"]
    nl_products: Mapped[Optional[list]] = mapped_column(JSONB, default=list, nullable=True)

    # SHA256 хеш файла для дедупликации
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)

    # Дополнительные теги ["семья", "успех", "первый_чек"]
    tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list, nullable=True)

    # ====== СТАРЫЕ ПОЛЯ (для обратной совместимости) ======
    # Категория (morning, work, products, relationships, achievements, emotions, meta, seasonal, industry, random)
    category: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)

    # Конкретная ситуация
    situation: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Теги эмоций [happy, tired, excited] (JSONB)
    emotion_tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list, nullable=True)

    # Теги персон [expert, friend, rebel] (JSONB)
    persona_tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list, nullable=True)

    # Статистика использования
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Локальный путь (для фото продуктов и testimonials)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Промпт для генерации (для регенерации)
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        if self.asset_type == "product":
            return f"<MediaAsset(id={self.id}, type=product, products={self.nl_products})>"
        elif self.asset_type == "testimonial":
            return f"<MediaAsset(id={self.id}, type=testimonial, desc={self.description[:50] if self.description else 'N/A'})>"
        else:
            return f"<MediaAsset(id={self.id}, category={self.category}, situation={self.situation})>"


class MediaKeywordIndex(Base):
    """Индекс для быстрого O(1) поиска медиа по ключевым словам"""
    __tablename__ = "media_keyword_index"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Оригинальное ключевое слово
    keyword: Mapped[str] = mapped_column(String(255))

    # Нормализованное для поиска (lowercase, без спецсимволов)
    normalized_keyword: Mapped[str] = mapped_column(String(255), index=True)

    # Ссылка на медиа-ресурс
    asset_id: Mapped[int] = mapped_column(Integer, index=True)

    # Приоритет при множественных совпадениях (1-10, выше = приоритетнее)
    priority: Mapped[int] = mapped_column(Integer, default=1)

    def __repr__(self) -> str:
        return f"<MediaKeywordIndex(keyword={self.keyword}, asset_id={self.asset_id}, priority={self.priority})>"


class ImportedPost(Base, TimestampMixin):
    """Импортированный пост из Telegram экспорта для использования как тема/вдохновение"""
    __tablename__ = "content_imported_posts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Источник
    source_id: Mapped[int] = mapped_column(Integer, index=True)  # Оригинальный ID сообщения
    source_channel: Mapped[str] = mapped_column(String(200))     # Название канала

    # Контент
    text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), index=True)  # product, motivation, business, success, tips, news, lifestyle

    # Метрики качества
    reactions_count: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    has_formatting: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_score: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Дата оригинального поста
    original_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Статус использования
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    used_for_post_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<ImportedPost(id={self.id}, channel={self.source_channel}, category={self.category}, used={self.is_used})>"


class HookTemplate(Base, TimestampMixin):
    """Шаблон hook'а (цепляющей фразы)"""
    __tablename__ = "content_hook_templates"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Версия персоны (expert, friend, rebel, philosopher, crazy, tired)
    persona_version: Mapped[str] = mapped_column(String(50), index=True)

    # Шаблон фразы (e.g., "Давай разберёмся: {topic}")
    template: Mapped[str] = mapped_column(Text)

    # Переменные в шаблоне ["topic", "fact"] (JSONB)
    variables: Mapped[list] = mapped_column(JSONB, default=list)

    # Категории настроений [joy, excitement] (JSONB)
    mood_categories: Mapped[list] = mapped_column(JSONB, default=list)

    # Типы постов [product, motivation] (JSONB)
    post_types: Mapped[list] = mapped_column(JSONB, default=list)

    # Статистика использования
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # Оценка эффективности (для A/B тестирования)
    effectiveness_score: Mapped[Optional[float]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<HookTemplate(id={self.id}, persona={self.persona_version}, template={self.template[:50]}...)>"
