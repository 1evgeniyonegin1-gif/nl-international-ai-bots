"""
Общие настройки для обоих ботов
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


class Settings(BaseSettings):
    """Общие настройки приложения"""

    # Telegram Bot Tokens
    curator_bot_token: str = Field(..., env="CURATOR_BOT_TOKEN")
    content_manager_bot_token: str = Field(..., env="CONTENT_MANAGER_BOT_TOKEN")
    channel_username: str = Field(..., env="CHANNEL_USERNAME")

    # Group with Topics (for content publishing)
    group_id: str = Field(default="", env="GROUP_ID")
    curator_bot_username: str = Field(default="@nl_mentor1_bot", env="CURATOR_BOT_USERNAME")

    # Topic IDs (message_thread_id for each topic)
    topic_products: int = Field(default=0, env="TOPIC_PRODUCTS")
    topic_business: int = Field(default=0, env="TOPIC_BUSINESS")
    topic_training: int = Field(default=0, env="TOPIC_TRAINING")
    topic_news: int = Field(default=0, env="TOPIC_NEWS")
    topic_success: int = Field(default=0, env="TOPIC_SUCCESS")
    topic_faq: int = Field(default=0, env="TOPIC_FAQ")

    def get_topic_id(self, post_type: str) -> int:
        """Возвращает ID темы для типа поста"""
        mapping = {
            # Продукты
            "product": self.topic_products,
            "product_deep_dive": self.topic_products,
            "product_comparison": self.topic_products,

            # Бизнес
            "business": self.topic_business,
            "business_lifestyle": self.topic_business,
            "business_myths": self.topic_business,

            # Истории успеха
            "motivation": self.topic_success,
            "success_story": self.topic_success,
            "transformation": self.topic_success,

            # Обучение
            "tips": self.topic_training,

            # Новости
            "news": self.topic_news,
            "promo": self.topic_news,

            # FAQ
            "faq": self.topic_faq,
            "myth_busting": self.topic_faq,
        }
        return mapping.get(post_type, self.topic_products)  # По умолчанию в продукты

    # AI API Keys
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    anthropic_base_url: str = Field(default="", env="ANTHROPIC_BASE_URL")  # Прокси для обхода блокировки
    gigachat_auth_token: str = Field(default="", env="GIGACHAT_AUTH_TOKEN")
    gigachat_client_id: str = Field(default="", env="GIGACHAT_CLIENT_ID")

    # YandexGPT (Yandex Cloud)
    yandex_service_account_id: str = Field(default="", env="YANDEX_SERVICE_ACCOUNT_ID")
    yandex_key_id: str = Field(default="", env="YANDEX_KEY_ID")
    yandex_private_key: str = Field(default="", env="YANDEX_PRIVATE_KEY")
    yandex_private_key_file: str = Field(default="", env="YANDEX_PRIVATE_KEY_FILE")
    yandex_folder_id: str = Field(default="", env="YANDEX_FOLDER_ID")
    yandex_model: str = Field(default="yandexgpt-32k", env="YANDEX_MODEL")

    @model_validator(mode='after')
    def load_private_key_from_file(self) -> 'Settings':
        """Загружает приватный ключ из файла если указан путь"""
        if self.yandex_private_key_file and not self.yandex_private_key:
            key_path = Path(self.yandex_private_key_file)
            if key_path.exists():
                self.yandex_private_key = key_path.read_text(encoding='utf-8')
        return self

    # YandexART (генерация изображений)
    yandex_art_enabled: bool = Field(default=False, env="YANDEX_ART_ENABLED")  # default=False чтобы не генерировать без явного включения
    yandex_art_width: int = Field(default=1024, env="YANDEX_ART_WIDTH")
    yandex_art_height: int = Field(default=1024, env="YANDEX_ART_HEIGHT")

    # Database
    database_url: str = Field(..., env="DATABASE_URL")

    # Admin Settings
    admin_telegram_ids: str = Field(..., env="ADMIN_TELEGRAM_IDS")

    @property
    def admin_ids_list(self) -> List[int]:
        """Преобразует строку ID админов в список"""
        return [int(id_.strip()) for id_ in self.admin_telegram_ids.split(",")]

    # AI Model Configuration
    curator_ai_model: str = Field(default="gemini-1.5-flash", env="CURATOR_AI_MODEL")
    content_manager_ai_model: str = Field(default="gpt-3.5-turbo", env="CONTENT_MANAGER_AI_MODEL")

    # Redis (optional)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Telethon (для мониторинга каналов-образцов)
    # Получить на https://my.telegram.org/apps
    telethon_api_id: int = Field(default=0, env="TELETHON_API_ID")
    telethon_api_hash: str = Field(default="", env="TELETHON_API_HASH")
    telethon_session_name: str = Field(default="nl_style_monitor", env="TELETHON_SESSION_NAME")

    # Other Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    timezone: str = Field(default="Europe/Moscow", env="TIMEZONE")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


# Глобальный экземпляр настроек
settings = Settings()
