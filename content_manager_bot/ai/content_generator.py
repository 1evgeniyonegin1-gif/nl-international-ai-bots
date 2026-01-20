"""
Генератор контента с использованием GigaChat, YandexGPT и GPT-4 (гибридный подход)
Поддерживает генерацию изображений через YandexART
"""
from typing import Optional, Tuple
from datetime import datetime
from loguru import logger

from shared.ai_clients.gigachat_client import GigaChatClient
from shared.ai_clients.yandexgpt_client import YandexGPTClient
from shared.ai_clients.yandexart_client import YandexARTClient, ImageStyle
from shared.ai_clients.openai_client import OpenAIClient
from shared.config.settings import settings
from content_manager_bot.ai.prompts import ContentPrompts
from content_manager_bot.utils.product_reference import ProductReferenceManager


# Типы постов, где используется GPT-4 для лучшего качества
# Это эмоциональные/сторителлинг посты, где важна "человечность"
PREMIUM_POST_TYPES = [
    "transformation",      # Истории трансформации
    "motivation",          # Мотивационные посты
    "success_story",       # Истории успеха
    "business_lifestyle",  # Образ жизни партнёра
]


class ContentGenerator:
    """Генератор контента для Telegram канала (гибридный: GigaChat/YandexGPT + GPT-4)"""

    def __init__(self):
        """Инициализация генератора"""
        self.prompts = ContentPrompts()

        # Определяем основную модель из настроек
        main_model = settings.content_manager_ai_model.lower()

        # Инициализируем клиенты
        self.gigachat_client = None
        self.yandexgpt_client = None
        self.openai_client = None
        self.yandexart_client = None
        self.main_client = None
        self.main_model_name = "unknown"

        # YandexGPT (если настроен)
        if main_model.startswith("yandex") or "yandex" in main_model:
            if settings.yandex_folder_id and settings.yandex_private_key:
                self.yandexgpt_client = YandexGPTClient()
                self.main_client = self.yandexgpt_client
                self.main_model_name = "yandexgpt"
                logger.info("ContentGenerator initialized with YandexGPT as main model")
            else:
                logger.warning("YandexGPT selected but credentials missing, falling back to GigaChat")

        # GigaChat (бесплатный, запасной вариант)
        if not self.main_client and settings.gigachat_auth_token:
            self.gigachat_client = GigaChatClient(
                auth_token=settings.gigachat_auth_token,
                model="GigaChat"
            )
            self.main_client = self.gigachat_client
            self.main_model_name = "gigachat"
            logger.info("ContentGenerator initialized with GigaChat as main model")

        # OpenAI GPT (для premium постов, если настроен)
        if settings.openai_api_key:
            self.openai_client = OpenAIClient(
                api_key=settings.openai_api_key,
                model="gpt-4"
            )
            logger.info("OpenAI GPT-4 available for premium posts")

        # YandexART (для генерации изображений)
        if settings.yandex_art_enabled and settings.yandex_folder_id and settings.yandex_private_key:
            self.yandexart_client = YandexARTClient()
            logger.info("YandexART available for image generation")

        # Менеджер референсных изображений продуктов
        self.product_reference = ProductReferenceManager()

        if not self.main_client:
            raise ValueError("No AI client configured! Check .env settings")

    def _get_client_for_post_type(self, post_type: str):
        """
        Выбирает AI клиент в зависимости от типа поста

        Args:
            post_type: Тип поста

        Returns:
            AI клиент (OpenAI для premium постов, основной клиент для остальных)
        """
        # Для эмоциональных постов используем GPT-4 (если доступен)
        if post_type in PREMIUM_POST_TYPES and self.openai_client:
            logger.info(f"Using GPT-4 for premium post type: {post_type}")
            return self.openai_client, "gpt-4"

        # Для остальных - основной клиент (YandexGPT или GigaChat)
        logger.info(f"Using {self.main_model_name} for post type: {post_type}")
        return self.main_client, self.main_model_name

    async def generate_post(
        self,
        post_type: str,
        custom_topic: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Tuple[str, str]:
        """
        Генерирует пост для Telegram канала

        Args:
            post_type: Тип поста (product, motivation, news, tips, success_story, promo)
            custom_topic: Дополнительная тема для уточнения
            temperature: Креативность (0.0-1.0), если None - используется дефолт для модели

        Returns:
            Tuple[str, str]: (текст поста, использованный промпт)
        """
        try:
            # Получаем промпт для типа поста
            user_prompt = self.prompts.get_prompt_for_type(post_type, custom_topic)

            # Выбираем клиент в зависимости от типа поста
            ai_client, model_name = self._get_client_for_post_type(post_type)

            # Устанавливаем температуру в зависимости от модели
            if temperature is None:
                temperature = 0.85 if model_name == "gigachat" else 0.8

            logger.info(f"Generating {post_type} post with {model_name}" +
                       (f" about '{custom_topic}'" if custom_topic else "") +
                       f" (temp={temperature})")

            # Генерируем контент
            content = await ai_client.generate_response(
                system_prompt=ContentPrompts.SYSTEM_PROMPT,
                user_message=user_prompt,
                temperature=temperature,
                max_tokens=1000
            )

            # Очищаем контент от возможных артефактов
            content = self._clean_content(content)

            logger.info(f"Post generated successfully with {model_name}: {len(content)} chars")

            return content, user_prompt

        except Exception as e:
            logger.error(f"Error generating post: {e}")
            raise

    async def regenerate_post(
        self,
        original_post: str,
        feedback: str,
        post_type: Optional[str] = None,
        temperature: float = 0.85
    ) -> str:
        """
        Перегенерирует пост с учётом обратной связи

        Args:
            original_post: Оригинальный пост
            feedback: Комментарий от админа
            post_type: Тип поста (для выбора модели)
            temperature: Креативность

        Returns:
            str: Новый текст поста
        """
        try:
            prompt = self.prompts.get_regenerate_prompt(original_post, feedback)

            # Выбираем клиент (если известен тип - используем гибридную логику)
            if post_type:
                ai_client, model_name = self._get_client_for_post_type(post_type)
            else:
                ai_client, model_name = self.main_client, self.main_model_name

            content = await ai_client.generate_response(
                system_prompt=ContentPrompts.SYSTEM_PROMPT,
                user_message=prompt,
                temperature=temperature,
                max_tokens=1000
            )

            content = self._clean_content(content)

            logger.info(f"Post regenerated successfully with {model_name}: {len(content)} chars")

            return content

        except Exception as e:
            logger.error(f"Error regenerating post: {e}")
            raise

    async def edit_post(
        self,
        original_post: str,
        edit_instructions: str,
        post_type: Optional[str] = None
    ) -> str:
        """
        Редактирует пост согласно инструкциям

        Args:
            original_post: Оригинальный пост
            edit_instructions: Инструкции по редактированию
            post_type: Тип поста (для выбора модели)

        Returns:
            str: Отредактированный текст
        """
        try:
            prompt = self.prompts.get_edit_prompt(original_post, edit_instructions)

            # Выбираем клиент (если известен тип - используем гибридную логику)
            if post_type:
                ai_client, model_name = self._get_client_for_post_type(post_type)
            else:
                ai_client, model_name = self.main_client, self.main_model_name

            content = await ai_client.generate_response(
                system_prompt=ContentPrompts.SYSTEM_PROMPT,
                user_message=prompt,
                temperature=0.5,  # Меньше креативности для редактирования
                max_tokens=1000
            )

            content = self._clean_content(content)

            logger.info(f"Post edited successfully with {model_name}: {len(content)} chars")

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
            "motivation": "Мотивационный пост (GPT-4)",
            "news": "Новости компании",
            "tips": "Советы для партнёров",
            "success_story": "История успеха (GPT-4)",
            "transformation": "История трансформации (GPT-4)",
            "business_lifestyle": "Образ жизни партнёра (GPT-4)",
            "promo": "Акция/промо",
            "myth_busting": "Разрушение мифов",
            "faq": "Вопрос-ответ",
            "business": "Бизнес-возможности",
            "business_myths": "Мифы о сетевом бизнесе"
        }

    @staticmethod
    def get_premium_post_types() -> list:
        """
        Возвращает типы постов, которые генерируются через GPT-4

        Returns:
            list: список типов premium постов
        """
        return PREMIUM_POST_TYPES

    # === Методы для работы с изображениями ===

    def is_image_generation_available(self) -> bool:
        """Проверяет, доступна ли генерация изображений"""
        return self.yandexart_client is not None

    async def generate_image(
        self,
        post_type: str,
        post_content: str,
        custom_prompt: Optional[str] = None,
        style: Optional[ImageStyle] = None,
        use_product_reference: bool = True
    ) -> Tuple[Optional[str], str]:
        """
        Генерирует изображение для поста (с поддержкой референсных изображений продуктов)

        Args:
            post_type: Тип поста
            post_content: Текст поста
            custom_prompt: Пользовательский промпт (опционально)
            style: Визуальный стиль изображения (ImageStyle enum)
            use_product_reference: Использовать reference image если найден продукт (image-to-image)

        Returns:
            Tuple[Optional[str], str]: (base64 изображения или None, использованный промпт)
        """
        if not self.yandexart_client:
            logger.warning("YandexART client not available")
            return None, ""

        try:
            reference_image = None
            reference_used = False

            # Пытаемся найти референсное изображение продукта (только для постов о продуктах)
            if use_product_reference and post_type == "product":
                product_info_tuple = self.product_reference.extract_product_from_content(post_content)
                if product_info_tuple:
                    category, product_key, product_info = product_info_tuple
                    reference_image = self.product_reference.get_product_image_base64(product_key, category)
                    if reference_image:
                        logger.info(f"Using reference image for product: {product_info['name']}")
                        reference_used = True
                        # Модифицируем промпт для image-to-image режима
                        if custom_prompt:
                            custom_prompt = self.product_reference.generate_image_to_image_prompt(
                                product_info, custom_prompt
                            )

            # Генерируем изображение
            if reference_image:
                # Image-to-image режим
                if not custom_prompt:
                    custom_prompt = self.yandexart_client._generate_image_prompt(post_type, post_content, style)
                    custom_prompt = self.product_reference.generate_image_to_image_prompt(
                        product_info, custom_prompt
                    )

                image_base64 = await self.yandexart_client.generate_image(
                    prompt=custom_prompt,
                    reference_image=reference_image
                )
                prompt_info = f"{custom_prompt} [image-to-image mode]"
            else:
                # Text-to-image режим (обычная генерация)
                image_base64, prompt_info = await self.yandexart_client.generate_image_for_post(
                    post_type=post_type,
                    post_content=post_content,
                    custom_prompt=custom_prompt,
                    style=style
                )

            return image_base64, prompt_info
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None, ""

    async def regenerate_image(
        self,
        post_type: str,
        post_content: str,
        feedback: Optional[str] = None,
        style: Optional[ImageStyle] = None
    ) -> Tuple[Optional[str], str]:
        """
        Перегенерирует изображение с учётом фидбека

        Args:
            post_type: Тип поста
            post_content: Текст поста
            feedback: Комментарий для улучшения
            style: Визуальный стиль изображения (ImageStyle enum)

        Returns:
            Tuple[Optional[str], str]: (base64 изображения или None, использованный промпт)
        """
        custom_prompt = None
        if feedback:
            # Формируем новый промпт с учётом фидбека
            custom_prompt = f"{feedback}. Контекст поста: {post_content[:100]}"

        return await self.generate_image(post_type, post_content, custom_prompt, style)

    @staticmethod
    def get_available_image_styles() -> dict:
        """
        Возвращает доступные стили изображений

        Returns:
            dict: {style_code: description}
        """
        return {
            ImageStyle.PHOTO.value: "Фотореалистичный",
            ImageStyle.MINIMALISM.value: "Минимализм",
            ImageStyle.ILLUSTRATION.value: "Иллюстрация",
            ImageStyle.INFOGRAPHIC.value: "Инфографика",
            ImageStyle.BUSINESS.value: "Бизнес-стиль",
            ImageStyle.VIBRANT.value: "Яркий/энергичный",
            ImageStyle.CINEMATIC.value: "Кинематографичный",
            ImageStyle.FLAT_LAY.value: "Flat Lay (сверху)",
            ImageStyle.LIFESTYLE.value: "Lifestyle",
            ImageStyle.GRADIENT.value: "Градиент/абстракция"
        }
