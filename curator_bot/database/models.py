"""
Модели базы данных для AI-Куратора
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, BigInteger, Text, Integer, Boolean, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from shared.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Модель пользователя (партнера)"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    # Тип и квалификация
    user_type: Mapped[str] = mapped_column(String(20), default="lead")  # 'lead' или 'partner'
    qualification: Mapped[str] = mapped_column(String(50), default="beginner")  # beginner, manager, master, star, diamond

    # Реферальная система
    referrer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    # Цели и активность
    current_goal: Mapped[Optional[str]] = mapped_column(Text)
    last_activity: Mapped[Optional[datetime]] = mapped_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    messages: Mapped[List["ConversationMessage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    context: Mapped[Optional["ConversationContext"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, name={self.first_name})>"


class ConversationMessage(Base, TimestampMixin):
    """История диалогов с куратором"""
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message_text: Mapped[str] = mapped_column(Text)
    sender: Mapped[str] = mapped_column(String(20))  # 'user' или 'bot'
    timestamp: Mapped[datetime] = mapped_column(index=True)

    # AI метаданные
    ai_model: Mapped[Optional[str]] = mapped_column(String(50))
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    context_used: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, user_id={self.user_id}, sender={self.sender})>"


class ConversationContext(Base, TimestampMixin):
    """Контекст диалогов для быстрого доступа"""
    __tablename__ = "conversation_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    # Контекстная информация
    recent_topics: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    pending_actions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    last_question: Mapped[Optional[str]] = mapped_column(Text)
    last_recommendation: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="context")

    def __repr__(self) -> str:
        return f"<ConversationContext(id={self.id}, user_id={self.user_id})>"


class KnowledgeBaseChunk(Base, TimestampMixin):
    """Фрагменты базы знаний для RAG"""
    __tablename__ = "knowledge_base_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_file: Mapped[str] = mapped_column(String(255))
    chunk_text: Mapped[str] = mapped_column(Text)

    # Векторное представление для поиска (используем pgvector)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384))  # sentence-transformers размерность 384

    # Метаданные
    category: Mapped[str] = mapped_column(String(100), index=True)  # products, marketing_plan, sales_scripts, etc.
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    def __repr__(self) -> str:
        return f"<KnowledgeBaseChunk(id={self.id}, category={self.category})>"


class UserReminder(Base, TimestampMixin):
    """Напоминания и задачи для партнеров"""
    __tablename__ = "user_reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    reminder_type: Mapped[str] = mapped_column(String(50))  # lesson, goal, activity, custom
    message: Mapped[str] = mapped_column(Text)

    scheduled_at: Mapped[datetime] = mapped_column(index=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, sent, cancelled

    def __repr__(self) -> str:
        return f"<UserReminder(id={self.id}, user_id={self.user_id}, type={self.reminder_type})>"


class UserFeedback(Base, TimestampMixin):
    """Обратная связь от партнеров о качестве ответов"""
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    message_id: Mapped[int] = mapped_column(ForeignKey("conversation_messages.id"))

    rating: Mapped[int] = mapped_column(Integer)  # 1-5
    feedback_text: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<UserFeedback(id={self.id}, user_id={self.user_id}, rating={self.rating})>"
