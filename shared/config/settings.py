"""
Общие настройки для обоих ботов
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Общие настройки приложения"""

    # Telegram Bot Tokens
    curator_bot_token: str = Field(..., env="CURATOR_BOT_TOKEN")
    content_manager_bot_token: str = Field(..., env="CONTENT_MANAGER_BOT_TOKEN")
    channel_username: str = Field(..., env="CHANNEL_USERNAME")

    # AI API Keys
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    gigachat_auth_token: str = Field(default="", env="GIGACHAT_AUTH_TOKEN")
    gigachat_client_id: str = Field(default="", env="GIGACHAT_CLIENT_ID")

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

    # Other Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    timezone: str = Field(default="Europe/Moscow", env="TIMEZONE")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


# Глобальный экземпляр настроек
settings = Settings()
