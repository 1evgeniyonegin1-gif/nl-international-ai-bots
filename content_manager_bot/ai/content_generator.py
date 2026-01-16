"""
Генератор контента с использованием GigaChat
"""
from typing import Optional, Tuple
from datetime import datetime
from loguru import logger

from shared.ai_clients.gigachat_client import GigaChatClient
from shared.config.settings import settings
from content_manager_bot.ai.prompts import ContentPrompts


class ContentGenerator:
    """Генератор контента для Telegram канала"""

    def __init__(self):
        """Инициализация генератора"""
        self.ai_client = GigaChatClient(
            auth_token=settings.gigachat_auth_token,
            model=settings.content_manager_ai_model or "GigaChat"
        )
        self.prompts = ContentPrompts()
        logger.info("ContentGenerator initialized with GigaChat")

    async def generate_post(
        self,
        post_type: str,
        custom_topic: Optional[str] = None,
        temperature: float = 0.8
    ) -> Tuple[str, str]:
        """
        Генерирует пост для Telegram канала

        Args:
            post_type: Тип поста (product, motivation, news, tips, success_story, promo)
            custom_topic: Дополнительная тема для уточнения
            temperature: Креативность (0.0-1.0), по умолчанию 0.8

        Returns:
            Tuple[str, str]: (текст поста, использованный промпт)
        """
        try:
            # Получаем промпт для типа поста
            user_prompt = self.prompts.get_prompt_for_type(post_type, custom_topic)

            logger.info(f"Generating {post_type} post" + (f" about '{custom_topic}'" if custom_topic else ""))

            # Генерируем контент
            content = await self.ai_client.generate_response(
                system_prompt=ContentPrompts.SYSTEM_PROMPT,
                user_message=user_prompt,
                temperature=temperature,
                max_tokens=1000
            )

            # Очищаем контент от возможных артефактов
            content = self._clean_content(content)

            logger.info(f"Post generated successfully: {len(content)} chars")

            return content, user_prompt

        except Exception as e:
            logger.error(f"Error generating post: {e}")
            raise

    async def regenerate_post(
        self,
        original_post: str,
        feedback: str,
        temperature: float = 0.8
    ) -> str:
        """
        Перегенерирует пост с учётом обратной связи

        Args:
            original_post: Оригинальный пост
            feedback: Комментарий от админа
            temperature: Креативность

        Returns:
            str: Новый текст поста
        """
        try:
            prompt = self.prompts.get_regenerate_prompt(original_post, feedback)

            content = await self.ai_client.generate_response(
                system_prompt=ContentPrompts.SYSTEM_PROMPT,
                user_message=prompt,
                temperature=temperature,
                max_tokens=1000
            )

            content = self._clean_content(content)

            logger.info(f"Post regenerated successfully: {len(content)} chars")

            return content

        except Exception as e:
            logger.error(f"Error regenerating post: {e}")
            raise

    async def edit_post(
        self,
        original_post: str,
        edit_instructions: str
    ) -> str:
        """
        Редактирует пост согласно инструкциям

        Args:
            original_post: Оригинальный пост
            edit_instructions: Инструкции по редактированию

        Returns:
            str: Отредактированный текст
        """
        try:
            prompt = self.prompts.get_edit_prompt(original_post, edit_instructions)

            content = await self.ai_client.generate_response(
                system_prompt=ContentPrompts.SYSTEM_PROMPT,
                user_message=prompt,
                temperature=0.5,  # Меньше креативности для редактирования
                max_tokens=1000
            )

            content = self._clean_content(content)

            logger.info(f"Post edited successfully: {len(content)} chars")

            return content

        except Exception as e:
            logger.error(f"Error editing post: {e}")
            raise

    def _clean_content(self, content: str) -> str:
        """
        Очищает сгенерированный контент от артефактов

        Args:
            content: Сырой контент от AI

        Returns:
            str: Очищенный контент
        """
        # Убираем возможные обрамления
        content = content.strip()

        # Убираем маркеры кода если есть
        if content.startswith("```"):
            lines = content.split("\n")
            if len(lines) > 2:
                content = "\n".join(lines[1:-1])

        # Убираем кавычки в начале и конце
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]

        # Убираем лишние переносы строк
        while "\n\n\n" in content:
            content = content.replace("\n\n\n", "\n\n")

        return content.strip()

    @staticmethod
    def get_available_post_types() -> dict:
        """
        Возвращает доступные типы постов

        Returns:
            dict: {type_code: description}
        """
        return {
            "product": "О продуктах NL",
            "motivation": "Мотивационный пост",
            "news": "Новости компании",
            "tips": "Советы для партнёров",
            "success_story": "История успеха",
            "promo": "Акция/промо"
        }
