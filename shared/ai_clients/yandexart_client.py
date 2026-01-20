"""
Клиент для работы с YandexART API (генерация изображений)
"""
from typing import Optional
from enum import Enum
import httpx
import jwt
import time
import base64
import asyncio
from loguru import logger

from shared.config.settings import settings


class ImageStyle(str, Enum):
    """Визуальные стили для генерации изображений"""
    PHOTO = "photo"                    # Фотореалистичный стиль
    MINIMALISM = "minimalism"          # Минималистичный дизайн
    ILLUSTRATION = "illustration"      # Иллюстрация/арт
    INFOGRAPHIC = "infographic"        # Инфографика
    BUSINESS = "business"              # Бизнес-стиль
    VIBRANT = "vibrant"                # Яркий/энергичный стиль
    CINEMATIC = "cinematic"            # Кинематографичный стиль
    FLAT_LAY = "flat_lay"              # Раскладка сверху (для продуктов)
    LIFESTYLE = "lifestyle"            # Lifestyle съемка
    GRADIENT = "gradient"              # Градиентный/абстрактный фон


# Расширенные описания стилей с деталями (lighting, composition, mood, etc.)
STYLE_DETAILS = {
    ImageStyle.PHOTO: {
        "style": "коммерческая фотография, профессиональный product shot",
        "lighting": "мягкий студийный свет с контровым освещением, создающим объем",
        "composition": "центрированная композиция, малая глубина резкости, красивое боке",
        "mood": "премиальный, чистый, привлекательный",
        "colors": "естественные тона, мягкие тени"
    },
    ImageStyle.MINIMALISM: {
        "style": "минималистичный скандинавский дизайн",
        "lighting": "ровное рассеянное освещение, мягкие тени",
        "composition": "много негативного пространства, простые геометрические формы",
        "mood": "спокойный, элегантный, современный",
        "colors": "приглушенная палитра, пастельные тона, белый и серый"
    },
    ImageStyle.ILLUSTRATION: {
        "style": "современная цифровая иллюстрация, vector art",
        "lighting": "плоское стилизованное освещение с яркими акцентами",
        "composition": "динамичная композиция, стилизованные формы",
        "mood": "креативный, современный, дружелюбный",
        "colors": "яркая контрастная палитра, градиенты"
    },
    ImageStyle.INFOGRAPHIC: {
        "style": "инфографика, информационный дизайн",
        "lighting": "ровное освещение без теней",
        "composition": "структурированная сетка, иконки, визуальная иерархия",
        "mood": "профессиональный, информативный, понятный",
        "colors": "корпоративные цвета, контрастные акценты"
    },
    ImageStyle.BUSINESS: {
        "style": "корпоративная фотография, деловой стиль",
        "lighting": "естественный офисный свет, мягкие тени",
        "composition": "профессиональный ракурс, глубина пространства",
        "mood": "надежный, профессиональный, успешный",
        "colors": "сдержанные корпоративные тона, синий, серый, белый"
    },
    ImageStyle.VIBRANT: {
        "style": "яркая рекламная фотография, pop art влияние",
        "lighting": "яркое контрастное освещение, цветные акценты",
        "composition": "динамичная диагональная композиция, энергичные линии",
        "mood": "энергичный, позитивный, привлекающий внимание",
        "colors": "насыщенные яркие цвета, неоновые акценты, высокий контраст"
    },
    ImageStyle.CINEMATIC: {
        "style": "кинематографический кадр, cinematic photography",
        "lighting": "драматичное освещение золотого часа, контровой свет, лучи",
        "composition": "широкоугольная эпическая перспектива, правило третей",
        "mood": "вдохновляющий, эпический, эмоциональный",
        "colors": "теплые золотые и оранжевые тона, глубокие синие тени"
    },
    ImageStyle.FLAT_LAY: {
        "style": "flat lay фотография, вид сверху",
        "lighting": "мягкий рассеянный свет сверху, минимальные тени",
        "composition": "симметричная раскладка, геометрический порядок, вид сверху 90 градусов",
        "mood": "организованный, эстетичный, Instagram-worthy",
        "colors": "гармоничная палитра, координированные цвета"
    },
    ImageStyle.LIFESTYLE: {
        "style": "lifestyle фотография, естественные моменты",
        "lighting": "естественный дневной свет, золотой час",
        "composition": "непринужденная композиция, реальные ситуации",
        "mood": "аутентичный, вдохновляющий, aspirational",
        "colors": "теплые естественные тона, мягкая обработка"
    },
    ImageStyle.GRADIENT: {
        "style": "абстрактный градиентный фон, modern design",
        "lighting": "внутреннее свечение, без явного источника",
        "composition": "плавные переходы, абстрактные формы",
        "mood": "современный, технологичный, премиальный",
        "colors": "плавные градиенты, модные цветовые сочетания 2025"
    }
}

# Негативные промпты для исключения нежелательных элементов
NEGATIVE_PROMPTS = {
    "universal": "без текста, без надписей, без водяных знаков, без логотипов, без артефактов",
    "quality": "без размытия, без шума, без пересвета, без недосвета, без искажений",
    "people": "без лишних людей на фоне",
    "photo": "без мультяшности, без рисованного стиля",
    "illustration": "без фотореализма, без фотографий"
}


class YandexARTClient:
    """Клиент для работы с YandexART API (генерация изображений)"""

    def __init__(
        self,
        service_account_id: Optional[str] = None,
        key_id: Optional[str] = None,
        private_key: Optional[str] = None,
        folder_id: Optional[str] = None
    ):
        """
        Инициализация клиента

        Args:
            service_account_id: ID сервисного аккаунта
            key_id: ID ключа
            private_key: Приватный ключ (содержимое PEM файла)
            folder_id: ID каталога в Yandex Cloud
        """
        self.service_account_id = service_account_id or settings.yandex_service_account_id
        self.key_id = key_id or settings.yandex_key_id
        self.private_key = private_key or settings.yandex_private_key
        self.folder_id = folder_id or settings.yandex_folder_id
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync"
        self.operation_url = "https://llm.api.cloud.yandex.net/operations"
        self.iam_token = None
        self.token_expires_at = 0
        logger.info("YandexART client initialized")

    def _create_jwt_token(self) -> str:
        """
        Создание JWT токена для получения IAM токена

        Returns:
            str: JWT токен
        """
        now = int(time.time())
        payload = {
            'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            'iss': self.service_account_id,
            'iat': now,
            'exp': now + 3600
        }

        encoded_token = jwt.encode(
            payload,
            self.private_key,
            algorithm='PS256',
            headers={'kid': self.key_id}
        )

        return encoded_token

    async def _get_iam_token(self, force_refresh: bool = False) -> str:
        """
        Получение IAM токена через JWT

        Args:
            force_refresh: Принудительно обновить токен

        Returns:
            str: IAM токен
        """
        if self.iam_token and not force_refresh and time.time() < self.token_expires_at:
            return self.iam_token

        try:
            jwt_token = self._create_jwt_token()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                    json={'jwt': jwt_token}
                )
                response.raise_for_status()
                result = response.json()

                self.iam_token = result['iamToken']
                self.token_expires_at = time.time() + (11 * 3600)

                logger.info("YandexART IAM token obtained" + (" (refreshed)" if force_refresh else ""))
                return self.iam_token

        except Exception as e:
            logger.error(f"Error obtaining IAM token: {e}")
            raise

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        reference_image: Optional[str] = None,
        max_wait_seconds: int = 120
    ) -> Optional[str]:
        """
        Генерирует изображение по текстовому описанию (text-to-image или image-to-image)

        Args:
            prompt: Текстовое описание изображения
            width: Ширина изображения (кратно 8, мин 256, макс 1024)
            height: Высота изображения (кратно 8, мин 256, макс 1024)
            seed: Seed для воспроизводимости результатов
            reference_image: Base64-encoded исходное изображение для image-to-image
            max_wait_seconds: Максимальное время ожидания генерации

        Returns:
            str: Base64-encoded изображение или None при ошибке
        """
        for attempt in range(2):
            try:
                iam_token = await self._get_iam_token(force_refresh=(attempt > 0))

                # Формируем запрос на генерацию
                request_body = {
                    "modelUri": f"art://{self.folder_id}/yandex-art/latest",
                    "generationOptions": {
                        "mimeType": "image/jpeg",
                        "aspectRatio": {
                            "widthRatio": str(width // 8),
                            "heightRatio": str(height // 8)
                        }
                    },
                    "messages": []
                }

                # Добавляем reference image, если указан (image-to-image mode)
                if reference_image:
                    request_body["messages"].append({
                        "weight": "1",
                        "image": reference_image
                    })
                    logger.info("Using image-to-image mode with reference image")

                # Добавляем текстовый промпт
                request_body["messages"].append({
                    "weight": "1",
                    "text": prompt
                })

                if seed is not None:
                    request_body["generationOptions"]["seed"] = str(seed)

                logger.info(f"Starting YandexART image generation: {prompt[:50]}...")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Отправляем запрос на генерацию
                    response = await client.post(
                        self.base_url,
                        headers={
                            "Authorization": f"Bearer {iam_token}",
                            "Content-Type": "application/json",
                            "x-folder-id": self.folder_id
                        },
                        json=request_body
                    )

                    if response.status_code in [401, 403] and attempt == 0:
                        logger.warning("YandexART token expired, refreshing...")
                        self.iam_token = None
                        self.token_expires_at = 0
                        continue

                    response.raise_for_status()
                    operation = response.json()

                operation_id = operation.get("id")
                if not operation_id:
                    logger.error(f"No operation ID in response: {operation}")
                    return None

                logger.info(f"YandexART operation started: {operation_id}")

                # Ожидаем завершения операции
                image_base64 = await self._wait_for_operation(
                    operation_id,
                    iam_token,
                    max_wait_seconds
                )

                return image_base64

            except httpx.HTTPStatusError as e:
                if e.response.status_code in [401, 403] and attempt == 0:
                    logger.warning("YandexART token expired (HTTPStatusError), refreshing...")
                    self.iam_token = None
                    self.token_expires_at = 0
                    continue
                logger.error(f"Error calling YandexART API: {e}")
                logger.error(f"Response body: {e.response.text if hasattr(e, 'response') else 'N/A'}")
                return None

            except Exception as e:
                logger.error(f"Error calling YandexART API: {e}")
                return None

        return None

    async def _wait_for_operation(
        self,
        operation_id: str,
        iam_token: str,
        max_wait_seconds: int
    ) -> Optional[str]:
        """
        Ожидает завершения операции генерации

        Args:
            operation_id: ID операции
            iam_token: IAM токен
            max_wait_seconds: Максимальное время ожидания

        Returns:
            str: Base64-encoded изображение или None
        """
        start_time = time.time()
        poll_interval = 2  # секунды между проверками

        async with httpx.AsyncClient(timeout=30.0) as client:
            while time.time() - start_time < max_wait_seconds:
                try:
                    response = await client.get(
                        f"{self.operation_url}/{operation_id}",
                        headers={
                            "Authorization": f"Bearer {iam_token}"
                        }
                    )
                    response.raise_for_status()
                    operation = response.json()

                    if operation.get("done"):
                        if "error" in operation:
                            error = operation["error"]
                            logger.error(f"YandexART generation failed: {error}")
                            return None

                        # Извлекаем изображение из ответа
                        response_data = operation.get("response", {})
                        image_base64 = response_data.get("image")

                        if image_base64:
                            logger.info("YandexART image generated successfully")
                            return image_base64
                        else:
                            logger.error(f"No image in response: {response_data}")
                            return None

                    # Операция еще не завершена, ждем
                    await asyncio.sleep(poll_interval)

                except Exception as e:
                    logger.error(f"Error polling operation status: {e}")
                    await asyncio.sleep(poll_interval)

        logger.error(f"YandexART operation timed out after {max_wait_seconds}s")
        return None

    async def generate_image_for_post(
        self,
        post_type: str,
        post_content: str,
        custom_prompt: Optional[str] = None,
        style: Optional[ImageStyle] = None
    ) -> tuple[Optional[str], str]:
        """
        Генерирует изображение для поста на основе его типа и содержимого

        Args:
            post_type: Тип поста (product, motivation, etc.)
            post_content: Текст поста
            custom_prompt: Пользовательский промпт (если не указан, генерируется автоматически)
            style: Визуальный стиль изображения (ImageStyle enum)

        Returns:
            tuple: (base64_image, prompt_used)
        """
        # Генерируем промпт для изображения на основе типа поста
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._generate_image_prompt(post_type, post_content, style)

        image_base64 = await self.generate_image(prompt)

        return image_base64, prompt

    def _generate_image_prompt(
        self,
        post_type: str,
        post_content: str,
        style: Optional[ImageStyle] = None
    ) -> str:
        """
        Генерирует промпт для изображения на основе типа поста и стиля.
        Использует структурированную формулу:
        [Subject] + [Style] + [Lighting] + [Composition] + [Colors] + [Mood] + [Technical] + [Negative]

        Args:
            post_type: Тип поста
            post_content: Текст поста
            style: Визуальный стиль (если None - выбирается автоматически)

        Returns:
            str: Промпт для генерации изображения
        """
        # Автоматический выбор стиля для типа поста (если не указан)
        if style is None:
            style = self._get_default_style_for_post_type(post_type)

        # Получаем детали стиля
        style_details = STYLE_DETAILS.get(style, STYLE_DETAILS[ImageStyle.BUSINESS])

        # Улучшенные контекстные описания субъектов для типов постов
        post_type_subjects = {
            "product": "Премиальная упаковка продуктов здорового питания NL International на элегантной мраморной поверхности, витамины и БАДы",
            "motivation": "Успешный человек на вершине горы смотрит на восход солнца, символ достижения целей и мечты",
            "news": "Современное корпоративное мероприятие, профессиональная бизнес-встреча партнёров",
            "tips": "Визуализация полезных советов и лайфхаков, образовательный контент для развития",
            "success_story": "Счастливые успешные люди празднуют достижения, радость победы и успеха",
            "promo": "Привлекательное специальное предложение, акция с выгодными условиями",
            "transformation": "Впечатляющая трансформация к здоровому образу жизни, позитивные изменения",
            "business_lifestyle": "Успешный предприниматель наслаждается свободой и путешествиями, качественная жизнь",
            "business": "Возможности партнёрского бизнеса, рост и развитие карьеры",
            "myth_busting": "Разоблачение популярных мифов, поиск правды и фактов",
            "faq": "Ответы на частые вопросы, помощь и поддержка клиентов"
        }

        # Получаем субъект для типа поста
        subject = post_type_subjects.get(post_type, "Профессиональный бизнес-контент для социальных сетей")

        # Извлекаем ключевые слова из текста поста
        content_hint = self._extract_keywords_from_content(post_content)

        # Собираем структурированный промпт по формуле
        prompt_parts = []

        # 1. Subject (главный объект)
        prompt_parts.append(subject)
        if content_hint:
            prompt_parts.append(f"тема: {content_hint}")

        # 2. Style (стиль)
        prompt_parts.append(style_details["style"])

        # 3. Lighting (освещение)
        prompt_parts.append(style_details["lighting"])

        # 4. Composition (композиция)
        prompt_parts.append(style_details["composition"])

        # 5. Colors (цвета)
        prompt_parts.append(style_details["colors"])

        # 6. Mood (настроение)
        prompt_parts.append(f"атмосфера: {style_details['mood']}")

        # 7. Technical (качество)
        prompt_parts.append("8K разрешение, высокая детализация, профессиональное исполнение")

        # Собираем основную часть промпта
        prompt = ". ".join(prompt_parts)

        # 8. Negative (исключения) - добавляем в конце
        negative = self._get_negative_prompt(style)
        prompt += f". {negative}"

        logger.info(f"Generated enhanced prompt for {post_type} with {style.value} style: {prompt[:100]}...")

        return prompt

    def _get_negative_prompt(self, style: ImageStyle) -> str:
        """
        Формирует негативный промпт для исключения нежелательных элементов

        Args:
            style: Стиль изображения

        Returns:
            str: Негативный промпт
        """
        parts = [NEGATIVE_PROMPTS["universal"], NEGATIVE_PROMPTS["quality"]]

        # Добавляем специфичные негативы для стиля
        if style in [ImageStyle.PHOTO, ImageStyle.BUSINESS, ImageStyle.LIFESTYLE,
                     ImageStyle.FLAT_LAY, ImageStyle.CINEMATIC]:
            parts.append(NEGATIVE_PROMPTS["photo"])
        elif style in [ImageStyle.ILLUSTRATION, ImageStyle.INFOGRAPHIC]:
            parts.append(NEGATIVE_PROMPTS["illustration"])

        return ", ".join(parts)

    def _get_default_style_for_post_type(self, post_type: str) -> ImageStyle:
        """
        Возвращает стиль по умолчанию для типа поста

        Args:
            post_type: Тип поста

        Returns:
            ImageStyle: Рекомендуемый стиль
        """
        default_styles = {
            "product": ImageStyle.FLAT_LAY,           # Flat lay для продуктов
            "motivation": ImageStyle.CINEMATIC,       # Кинематографичный для мотивации
            "news": ImageStyle.BUSINESS,              # Деловой для новостей
            "tips": ImageStyle.INFOGRAPHIC,           # Инфографика для советов
            "success_story": ImageStyle.CINEMATIC,    # Кинематографичный для историй
            "promo": ImageStyle.VIBRANT,              # Яркий для акций
            "transformation": ImageStyle.LIFESTYLE,   # Lifestyle для трансформаций
            "business_lifestyle": ImageStyle.LIFESTYLE,  # Lifestyle
            "business": ImageStyle.BUSINESS,          # Деловой
            "myth_busting": ImageStyle.ILLUSTRATION,  # Иллюстрация для мифов
            "faq": ImageStyle.MINIMALISM              # Минимализм для FAQ
        }

        return default_styles.get(post_type, ImageStyle.BUSINESS)

    def _extract_keywords_from_content(self, content: str, max_length: int = 80) -> str:
        """
        Извлекает ключевые слова из контента для промпта

        Args:
            content: Текст поста
            max_length: Максимальная длина извлеченного текста

        Returns:
            str: Ключевые слова или пустая строка
        """
        # Убираем эмодзи и лишние символы
        import re
        cleaned = re.sub(r'[^\w\s\-,.]', ' ', content)
        cleaned = ' '.join(cleaned.split())

        # Берем первые N символов
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length].rsplit(' ', 1)[0]

        return cleaned.strip()