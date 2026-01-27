"""
Генератор контента с использованием GigaChat, YandexGPT и GPT-4 (гибридный подход)
Использует готовые фото продуктов из базы unified_products/
Поддерживает обучение на образцах стиля из каналов
Интегрирована система персон и настроений
Интегрирована RAG система для использования базы знаний
"""
import random
import re
from typing import Optional, Tuple, List
from datetime import datetime
from loguru import logger

from shared.ai_clients.gigachat_client import GigaChatClient
from shared.ai_clients.yandexgpt_client import YandexGPTClient
# YandexART удалён — используем готовые фото из базы unified_products/
from shared.ai_clients.openai_client import OpenAIClient
from shared.ai_clients.anthropic_client import AnthropicClient
from shared.config.settings import settings
from shared.style_monitor import get_style_service
from shared.persona import PersonaManager, PersonaContext
from shared.rag import get_rag_engine, RAGEngine
from content_manager_bot.ai.prompts import ContentPrompts
from content_manager_bot.database.models import ImportedPost
from content_manager_bot.utils.product_reference import ProductReferenceManager
from shared.media import media_library  # НОВОЕ: индексированная медиа-библиотека


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
        self.anthropic_client = None
        # YandexART удалён
        self.main_client = None
        self.main_model_name = "unknown"

        # Claude (приоритет если настроен)
        if "claude" in main_model and settings.anthropic_api_key:
            try:
                self.anthropic_client = AnthropicClient()
                self.main_client = self.anthropic_client
                self.main_model_name = "claude"
                logger.info(f"ContentGenerator initialized with Claude as main model: {settings.content_manager_ai_model}")
            except Exception as e:
                logger.warning(f"Claude init failed: {e}, falling back to other models")

        # YandexGPT (если настроен)
        if not self.main_client and (main_model.startswith("yandex") or "yandex" in main_model):
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

        # YandexART удалён — используем только готовые фото из базы

        # Менеджер референсных изображений продуктов (старый, для совместимости)
        self.product_reference = ProductReferenceManager()

        # НОВОЕ: индексированная медиа-библиотека (< 20ms поиск)
        self.media_library = media_library

        if not self.main_client:
            raise ValueError("No AI client configured! Check .env settings")

        # Флаг использования образцов стиля
        self.use_style_samples = True

        # Система персон и настроений
        self.persona_manager = PersonaManager()
        self.use_persona_system = True  # Можно отключить для тестирования
        logger.info("PersonaManager initialized for content generation")

        # RAG система для использования базы знаний
        self._rag_engine: Optional[RAGEngine] = None
        self.use_knowledge_base = True  # Использовать примеры из базы знаний
        logger.info("RAG knowledge base integration enabled")

    async def _get_rag_engine(self) -> RAGEngine:
        """Получить RAG engine (ленивая инициализация)."""
        if self._rag_engine is None:
            self._rag_engine = await get_rag_engine()
        return self._rag_engine

    async def _get_knowledge_context(
        self,
        post_type: str,
        custom_topic: Optional[str] = None,
        limit: int = 3
    ) -> str:
        """
        Получает релевантный контекст из базы знаний для генерации поста.

        Args:
            post_type: Тип поста
            custom_topic: Дополнительная тема
            limit: Максимум документов

        Returns:
            str: Отформатированный контекст из базы знаний
        """
        if not self.use_knowledge_base:
            return ""

        # Маппинг типов постов на категории RAG
        type_to_category = {
            "product": "products",
            "product_deep_dive": "products",
            "product_comparison": "products",
            "motivation": "motivation",
            "success_story": "success_stories",
            "transformation": "success_stories",
            "business_lifestyle": "business",
            "business": "business",
            "business_myths": "business",
            "tips": "training",
            "news": "news",
            "promo": "promo_examples",
            "myth_busting": "faq",
            "faq": "faq"
        }

        category = type_to_category.get(post_type, None)

        # Формируем поисковый запрос
        search_query = f"пост {post_type}"
        if custom_topic:
            search_query = f"{custom_topic} {post_type}"

        try:
            rag_engine = await self._get_rag_engine()
            results = await rag_engine.retrieve(
                query=search_query,
                category=category,
                top_k=limit,
                min_similarity=0.3  # Низкий порог для большего покрытия
            )

            if not results:
                # Пробуем без категории
                results = await rag_engine.retrieve(
                    query=search_query,
                    category=None,
                    top_k=limit,
                    min_similarity=0.25
                )

            if not results:
                return ""

            # Форматируем примеры
            examples = []
            for i, doc in enumerate(results, 1):
                # Берём только первые 600 символов для краткости
                content = doc.content[:600]
                if len(doc.content) > 600:
                    content += "..."
                examples.append(f"ПРИМЕР {i} (источник: {doc.source or 'база знаний'}):\n{content}")

            context_block = """

### ПРИМЕРЫ ИЗ БАЗЫ ЗНАНИЙ (используй как образец стиля и информации):

{}

### ВАЖНО:
- Используй факты и стиль из примеров
- НЕ копируй дословно, создавай уникальный контент
- Адаптируй под текущую тему и персону
""".format("\n\n---\n\n".join(examples))

            logger.info(f"Added {len(results)} knowledge base examples for {post_type}")
            return context_block

        except Exception as e:
            logger.warning(f"Could not get knowledge context: {e}")
            return ""

    async def _get_inspiration_topic(
        self,
        post_type: str
    ) -> Optional[Tuple[str, int]]:
        """
        Получает неиспользованный импортированный пост как тему/вдохновение.

        Args:
            post_type: Тип поста для маппинга на категорию

        Returns:
            Tuple[str, int]: (текст темы, id импортированного поста) или None
        """
        # Маппинг типов постов на категории импорта
        category_map = {
            "product": "product",
            "motivation": "motivation",
            "success_story": "success",
            "transformation": "success",
            "business_lifestyle": "lifestyle",
            "business": "business",
            "business_myths": "business",
            "tips": "tips",
            "news": "news",
            "promo": "news",
            "myth_busting": "motivation",
            "faq": "tips"
        }
        category = category_map.get(post_type, "motivation")

        try:
            from sqlalchemy import select
            from shared.database.base import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                # Получаем неиспользованный пост с наибольшим quality_score
                result = await session.execute(
                    select(ImportedPost)
                    .where(ImportedPost.category == category)
                    .where(ImportedPost.is_used == False)
                    .order_by(ImportedPost.quality_score.desc())
                    .limit(1)
                )
                post = result.scalar_one_or_none()

                if post:
                    # Берём первые 500 символов как тему
                    topic_text = post.text[:500]
                    if len(post.text) > 500:
                        topic_text += "..."
                    logger.info(f"Found inspiration topic from '{post.source_channel}' (id={post.id}, category={category})")
                    return (topic_text, post.id)

                # Fallback: пробуем любую категорию
                result = await session.execute(
                    select(ImportedPost)
                    .where(ImportedPost.is_used == False)
                    .order_by(ImportedPost.quality_score.desc())
                    .limit(1)
                )
                post = result.scalar_one_or_none()

                if post:
                    topic_text = post.text[:500]
                    if len(post.text) > 500:
                        topic_text += "..."
                    logger.info(f"Found fallback inspiration topic (id={post.id}, category={post.category})")
                    return (topic_text, post.id)

            logger.info(f"No unused inspiration topics found for {post_type}")
            return None

        except Exception as e:
            logger.warning(f"Could not get inspiration topic: {e}")
            return None

    async def _mark_inspiration_used(self, imported_post_id: int, generated_post_id: Optional[int] = None):
        """
        Отмечает импортированный пост как использованный.

        Args:
            imported_post_id: ID импортированного поста
            generated_post_id: ID сгенерированного поста (опционально)
        """
        try:
            from sqlalchemy import update
            from shared.database.base import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(ImportedPost)
                    .where(ImportedPost.id == imported_post_id)
                    .values(
                        is_used=True,
                        used_at=datetime.utcnow(),
                        used_for_post_id=generated_post_id
                    )
                )
                await session.commit()
                logger.info(f"Marked inspiration topic {imported_post_id} as used")

        except Exception as e:
            logger.error(f"Could not mark inspiration as used: {e}")

    def _get_content_style_guide(self) -> str:
        """
        Читает примеры из CONTENT_STYLE_GUIDE.md для обучения стилю.

        Returns:
            str: Отформатированные примеры из гайда или пустая строка
        """
        try:
            from pathlib import Path

            # Путь к файлу относительно content_manager_bot/ai/
            style_guide_path = Path(__file__).parent.parent.parent / "docs" / "CONTENT_STYLE_GUIDE.md"

            if not style_guide_path.exists():
                logger.warning(f"CONTENT_STYLE_GUIDE.md not found at {style_guide_path}")
                return ""

            content = style_guide_path.read_text(encoding="utf-8")

            # Извлекаем примеры из секции "Примеры живых постов"
            import re
            examples_section = re.search(
                r"## Примеры живых постов.*?(?=##|\Z)",
                content,
                re.DOTALL
            )

            if examples_section:
                examples_text = examples_section.group(0)
                return f"""

### 📚 ПРИМЕРЫ СТИЛЯ (ОБЯЗАТЕЛЬНО СЛЕДУЙ ЭТОМУ ФОРМАТУ):

{examples_text}

### ⚠️ ВАЖНО:
- Используй ТОТ ЖЕ живой стиль написания
- Короткие абзацы (1-2 предложения)
- HTML-теги: <blockquote>, <b>, <i>, <tg-spoiler>
- Разговорный язык, как в примерах
- Вопрос или CTA в конце
"""

            logger.info("Loaded style examples from CONTENT_STYLE_GUIDE.md")
            return ""

        except Exception as e:
            logger.warning(f"Could not load CONTENT_STYLE_GUIDE.md: {e}")
            return ""

    async def _get_style_samples(
        self,
        post_type: str,
        limit: int = 3
    ) -> List[str]:
        """
        Получает образцы постов из каналов-образцов для обучения стилю.

        ВРЕМЕННО ОТКЛЮЧЕНО: Telethon API keys не настроены, вызов тормозит.
        Включить когда будут настроены TELETHON_API_ID и TELETHON_API_HASH.

        Args:
            post_type: Тип поста для маппинга на категорию стиля
            limit: Максимум образцов

        Returns:
            List[str]: Список текстов образцов (пустой пока отключено)
        """
        # ВРЕМЕННО ОТКЛЮЧЕНО — Telethon тормозит без API keys
        # TODO: Включить когда будут настроены TELETHON_API_ID и TELETHON_API_HASH
        return []

        # Оригинальный код закомментирован:
        # if not self.use_style_samples:
        #     return []
        #
        # type_to_category = {
        #     "product": "product",
        #     "motivation": "motivation",
        #     "success_story": "motivation",
        #     "transformation": "motivation",
        #     "business_lifestyle": "lifestyle",
        #     "business": "business",
        #     "business_myths": "business",
        #     "tips": "general",
        #     "news": "general",
        #     "promo": "general",
        #     "myth_busting": "general",
        #     "faq": "general"
        # }
        #
        # style_category = type_to_category.get(post_type, "general")
        #
        # try:
        #     style_service = get_style_service()
        #     samples = await style_service.get_style_samples(
        #         style_category=style_category,
        #         limit=limit,
        #         min_quality=7
        #     )
        #
        #     if not samples:
        #         samples = await style_service.get_style_samples(
        #             style_category=None,
        #             limit=limit,
        #             min_quality=None
        #         )
        #
        #     return [s.text for s in samples if s.text]
        #
        # except Exception as e:
        #     logger.debug(f"Could not get style samples: {e}")
        #     return []

    def _format_style_examples(self, samples: List[str]) -> str:
        """
        Форматирует образцы стиля для добавления в промпт.

        Args:
            samples: Список текстов образцов

        Returns:
            str: Отформатированный блок с образцами
        """
        if not samples:
            return ""

        examples_text = "\n\n---\n\n".join([
            f"ПРИМЕР {i+1}:\n{sample[:500]}{'...' if len(sample) > 500 else ''}"
            for i, sample in enumerate(samples)
        ])

        return f"""

### ОБРАЗЦЫ СТИЛЯ (ориентируйся на эти примеры):

{examples_text}

### ВАЖНО:
- Используй похожий тон и структуру
- Сохраняй свою уникальность, но учись у примеров
- НЕ копируй дословно, создавай оригинальный контент
"""

    def _get_client_for_post_type(self, post_type: str):
        """
        Выбирает AI клиент в зависимости от типа поста

        Args:
            post_type: Тип поста

        Returns:
            AI клиент (основной клиент для всех типов, OpenAI отключён из-за блокировки в РФ)
        """
        # NOTE: OpenAI отключён - заблокирован в России (403 unsupported_country_region_territory)
        # Все типы постов теперь используют основной клиент (YandexGPT или GigaChat)

        if post_type in PREMIUM_POST_TYPES:
            logger.info(f"Using {self.main_model_name} for premium post type: {post_type}")
        else:
            logger.info(f"Using {self.main_model_name} for post type: {post_type}")

        return self.main_client, self.main_model_name

    async def generate_post(
        self,
        post_type: str,
        custom_topic: Optional[str] = None,
        temperature: Optional[float] = None,
        use_style_samples: bool = True,
        use_persona: bool = True,
        force_persona: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Генерирует пост для Telegram канала

        Args:
            post_type: Тип поста (product, motivation, news, tips, success_story, promo)
            custom_topic: Дополнительная тема для уточнения
            temperature: Креативность (0.0-1.0), если None - используется дефолт для модели/персоны
            use_style_samples: Использовать образцы стиля из каналов-образцов
            use_persona: Использовать систему персон и настроений
            force_persona: Принудительно выбрать версию персоны (expert, friend, rebel, etc.)

        Returns:
            Tuple[str, str]: (текст поста, использованный промпт)
        """
        # Переменная для отслеживания использованной темы из базы
        inspiration_post_id: Optional[int] = None

        try:
            # Получаем промпт для типа поста
            user_prompt = self.prompts.get_prompt_for_type(post_type, custom_topic)

            # === ИНТЕГРАЦИЯ ТЕМ ИЗ БАЗЫ ИМПОРТИРОВАННЫХ ПОСТОВ ===
            # Если не задана custom_topic, пробуем взять тему из базы
            if not custom_topic:
                inspiration = await self._get_inspiration_topic(post_type)
                if inspiration:
                    topic_text, inspiration_post_id = inspiration
                    # Добавляем тему в промпт с инструкцией адаптировать
                    inspiration_block = f"""

═══════════════════════════════════════════
📌 ТЕМА ДЛЯ ВДОХНОВЕНИЯ (адаптируй под NL):
═══════════════════════════════════════════

{topic_text}

═══════════════════════════════════════════
⚠️ ВАЖНО:
• Возьми ИДЕЮ/ТЕМУ из этого поста
• Адаптируй под продукты NL International
• Напиши СВОИМ голосом (от лица Данила)
• НЕ копируй текст дословно!
═══════════════════════════════════════════
"""
                    user_prompt = inspiration_block + "\n\n" + user_prompt
                    logger.info(f"Added inspiration topic (id={inspiration_post_id}) to prompt")

            # Получаем контекст персоны (если включена система)
            persona_context: Optional[PersonaContext] = None
            if use_persona and self.use_persona_system:
                # Генерируем настроение если нужно выбрать персону
                if force_persona:
                    # Принудительная персона
                    mood = self.persona_manager.generate_mood()
                    mood = mood._replace(persona_version=force_persona) if hasattr(mood, '_replace') else mood
                    from shared.persona.persona_manager import MoodState
                    mood = MoodState(
                        category=mood.category,
                        emotion=mood.emotion,
                        intensity=mood.intensity,
                        persona_version=force_persona,
                        trigger=mood.trigger
                    )
                    self.persona_manager.set_mood(mood)

                # Получаем контекст персоны с hook'ом
                # Формируем переменные для hook'ов
                topic_for_hook = custom_topic or self._get_topic_for_post_type(post_type)
                hook_variables = {
                    "topic": topic_for_hook,
                    "story": "одну важную историю",
                    "myth": "распространённое заблуждение",
                    "percentage": str(random.randint(70, 95)),
                    "product": "продукт NL",
                    "mechanism": "этот процесс",
                    "period": "месяц",
                    "person": "партнёром",
                    "situation": "что-то не получается",
                    "opinion": "это невозможно",
                    "action": "ждать идеального момента",
                    "year": "2025",
                }
                persona_context = self.persona_manager.get_persona_context(
                    post_type=post_type,
                    include_hook=True,
                    hook_variables=hook_variables
                )

                # Добавляем дополнение к промпту с информацией о персоне
                persona_enhancement = self.persona_manager.get_prompt_enhancement(persona_context)
                user_prompt = persona_enhancement + "\n\n" + user_prompt

                logger.info(
                    f"Using persona: {persona_context.persona_name} "
                    f"(mood: {persona_context.mood.emotion if persona_context.mood else 'none'})"
                )

            # 1. ВСЕГДА добавляем примеры из CONTENT_STYLE_GUIDE.md (приоритет!)
            style_guide_examples = self._get_content_style_guide()
            if style_guide_examples:
                user_prompt = user_prompt + style_guide_examples
                logger.info("Added examples from CONTENT_STYLE_GUIDE.md")

            # 2. Добавляем образцы стиля если доступны (Telethon - пока отключено)
            if use_style_samples and self.use_style_samples:
                style_samples = await self._get_style_samples(post_type, limit=3)
                if style_samples:
                    style_block = self._format_style_examples(style_samples)
                    user_prompt = user_prompt + style_block
                    logger.info(f"Added {len(style_samples)} style samples to prompt")

            # 3. Добавляем контекст из базы знаний (RAG)
            if self.use_knowledge_base:
                knowledge_context = await self._get_knowledge_context(
                    post_type=post_type,
                    custom_topic=custom_topic,
                    limit=2  # 2 примера чтобы не перегружать промпт
                )
                if knowledge_context:
                    user_prompt = user_prompt + knowledge_context

            # Выбираем клиент в зависимости от типа поста
            ai_client, model_name = self._get_client_for_post_type(post_type)

            # Устанавливаем температуру: персона > параметр > дефолт модели
            if temperature is None:
                if persona_context:
                    temperature = persona_context.temperature
                else:
                    temperature = 0.85 if model_name == "gigachat" else 0.8

            logger.info(f"Generating {post_type} post with {model_name}" +
                       (f" about '{custom_topic}'" if custom_topic else "") +
                       f" (temp={temperature})" +
                       (f" [persona: {persona_context.persona_version}]" if persona_context else ""))

            # Получаем SYSTEM_PROMPT — персона-специфичный если есть
            if persona_context:
                system_prompt = ContentPrompts.get_system_prompt_for_persona(
                    persona_context.persona_version
                )
            else:
                system_prompt = ContentPrompts.SYSTEM_PROMPT

            # ВАЖНО: Добавляем жёсткие требования к формату в конец user_prompt
            format_requirements = """

═══════════════════════════════════════════
⚠️ TELEGRAM HTML-ФОРМАТИРОВАНИЕ (ОБЯЗАТЕЛЬНО!):
═══════════════════════════════════════════

ИСПОЛЬЗУЙ ЭТИ HTML-ТЕГИ В КАЖДОМ ПОСТЕ:

1. <blockquote>ЦИТАТА</blockquote> (минимум 1 раз!) - ключевая мысль:
<blockquote>Вот так выглядит цитата в Telegram</blockquote>
(это создаёт синий блок слева)

2. <b>ЖИРНЫЙ</b> - для 2-4 ключевых слов/фраз

3. <i>КУРСИВ</i> - для мыслей в скобках, внутреннего голоса:
<i>ну ты понял</i> или <i>(исследование целое есть)</i>

4. БУЛЛЕТЫ для списков:
• пункт первый
• пункт второй

НАЗВАНИЯ ПРОДУКТОВ (ПРОСТЫЕ!):
• "коктейль" — вместо Energy Diet
• "коллаген" — вместо Collagen Trinity
• "витамины" — вместо Greenflash
• "дрейн", "метабуст", "адаптогены" — простые названия

СТРУКТУРА ПОСТА:
- Короткие абзацы (1-2 предложения)
- Пустая строка между абзацами
- Вопрос или CTA в конце

ПРИМЕР ПРАВИЛЬНОГО ФОРМАТИРОВАНИЯ:
---
Баланс - это когда вы оба равны. Это понятно, да?

<blockquote>Баба уведёт тот, кто пишет ей раз в 3 дня</blockquote>

<i>Да, многие с первой секунды именно это и транслируют</i> = только не теряй ко мне интерес!

И <b>баба это видит</b>. И мокро от этого у неё не будет.

• По факту, больше значимости у того, кто меньше зависит
• И может выйти из отношений в любой момент

Знакомо? 👇
---

Выдай ТОЛЬКО текст поста."""
            user_prompt = user_prompt + format_requirements

            # Генерируем контент
            content = await ai_client.generate_response(
                system_prompt=system_prompt,
                user_message=user_prompt,
                temperature=temperature,
                max_tokens=1000
            )

            # Очищаем контент от возможных артефактов
            content = self._clean_content(content)

            # Применяем post-processing для гарантии соблюдения инструкций
            content = self._apply_post_processing(content, persona_context)

            logger.info(f"Post generated successfully with {model_name}: {len(content)} chars")

            # Отмечаем тему как использованную (если была взята из базы)
            if inspiration_post_id:
                await self._mark_inspiration_used(inspiration_post_id)

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

    def _get_topic_for_post_type(self, post_type: str) -> str:
        """
        Возвращает тему для типа поста (используется в hook_variables).

        Args:
            post_type: Тип поста

        Returns:
            str: Тема для подстановки в hook
        """
        topic_map = {
            "product": "продуктах NL",
            "motivation": "мотивации",
            "news": "новостях компании",
            "tips": "полезных советах",
            "success_story": "успехе",
            "transformation": "трансформации",
            "business_lifestyle": "образе жизни",
            "promo": "акции",
            "myth_busting": "мифах",
            "faq": "частых вопросах",
            "business": "бизнесе",
            "business_myths": "мифах о сетевом"
        }
        return topic_map.get(post_type, "важном")

    def _convert_markdown_to_html(self, content: str) -> str:
        """
        Конвертирует markdown-форматирование в Telegram HTML.

        Преобразования:
        - **bold** → <b>bold</b>
        - *italic* → <i>italic</i>  (но не ** которое bold)
        - __underline__ → <u>underline</u>
        - ~~strike~~ → <s>strike</s>
        - `code` → <code>code</code>

        Args:
            content: Текст с возможным markdown

        Returns:
            str: Текст с HTML-тегами
        """
        # Bold: **text** → <b>text</b>
        content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content, flags=re.DOTALL)

        # Italic: *text* → <i>text</i> (но не ** которое bold)
        # Используем negative lookbehind/lookahead чтобы не затронуть уже преобразованное
        content = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', content)

        # Underline: __text__ → <u>text</u>
        content = re.sub(r'__(.+?)__', r'<u>\1</u>', content, flags=re.DOTALL)

        # Strikethrough: ~~text~~ → <s>text</s>
        content = re.sub(r'~~(.+?)~~', r'<s>\1</s>', content, flags=re.DOTALL)

        # Inline code: `text` → <code>text</code>
        content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)

        return content

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

        # ВАЖНО: Конвертируем markdown в HTML
        content = self._convert_markdown_to_html(content)

        # Убираем лишние переносы строк
        while "\n\n\n" in content:
            content = content.replace("\n\n\n", "\n\n")

        return content.strip()

    def _apply_post_processing(
        self,
        content: str,
        persona_context: Optional[PersonaContext]
    ) -> str:
        """
        Применяет post-processing для гарантии соблюдения инструкций AI.

        Исправляет типичные проблемы:
        1. AI игнорирует hook - принудительно вставляем в начало
        2. AI мало эмодзи - добавляем из набора персоны

        Args:
            content: Сгенерированный контент
            persona_context: Контекст персоны (если использовалась)

        Returns:
            str: Контент с гарантированным соблюдением инструкций
        """
        if not persona_context:
            return content

        # === 1. ПРОВЕРКА HOOK (без принудительной вставки) ===
        # Принудительная вставка убрана - AI получает hook через промпт
        # с правильно заполненными переменными
        if persona_context.hook:
            hook = persona_context.hook.strip()
            # Проверяем начинается ли контент с hook (для логирования)
            import re
            content_text_start = re.sub(r'^[\U0001F300-\U0001F9FF\s]+', '', content[:150]).lower()
            hook_lower = hook.lower()

            if not content_text_start.startswith(hook_lower[:30]):
                # Hook не в начале - только логируем, не вставляем
                # (AI должен сам использовать hook из промпта)
                logger.debug(f"[POST-PROCESSING] Hook не в начале поста: {hook[:50]}...")

        # === 2. ВАЛИДАЦИЯ ЭМОДЗИ ===
        # Определяем минимум эмодзи для персоны
        emoji_requirements = {
            "crazy": 5,      # Безумный Данил - много эмодзи
            "friend": 4,     # Дружелюбный - достаточно эмодзи
            "rebel": 3,      # Бунтарь - умеренно
            "expert": 2,     # Эксперт - мало
            "philosopher": 2,  # Философ - мало
            "tired": 1       # Уставший - минимум
        }

        min_emojis = emoji_requirements.get(persona_context.persona_version, 2)
        current_emojis = self._count_emojis(content)

        if current_emojis < min_emojis and persona_context.emoji:
            # Добавляем эмодзи из набора персоны
            needed = min_emojis - current_emojis
            import random
            emojis_to_add = random.sample(
                persona_context.emoji,
                min(needed, len(persona_context.emoji))
            )

            # Вставляем эмодзи в разные места текста
            lines = content.split('\n')
            for i, emoji in enumerate(emojis_to_add):
                insert_pos = (i * len(lines)) // len(emojis_to_add)
                if insert_pos < len(lines) and lines[insert_pos].strip():
                    # Добавляем в конец строки
                    lines[insert_pos] = lines[insert_pos].rstrip() + f" {emoji}"

            content = '\n'.join(lines)
            logger.info(f"[POST-PROCESSING] Added {len(emojis_to_add)} emojis for {persona_context.persona_version}")

        return content

    def _count_emojis(self, text: str) -> int:
        """Подсчитывает количество эмодзи в тексте"""
        import re
        emoji_pattern = re.compile(
            "[\U0001F300-\U0001F9FF"  # Misc Symbols, Emoticons, etc.
            "\U00002600-\U000027BF"    # Misc symbols
            "\U0001F600-\U0001F64F"    # Emoticons
            "\U0001F680-\U0001F6FF"    # Transport
            "\U0001F1E0-\U0001F1FF"    # Flags
            "]+",
            flags=re.UNICODE
        )
        return len(emoji_pattern.findall(text))

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
            "transformation": "История трансформации",
            "business_lifestyle": "Образ жизни партнёра",
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

    # === Методы для работы с персонами ===

    def get_available_personas(self) -> list[str]:
        """Возвращает список доступных версий персоны"""
        return self.persona_manager.get_all_personas()

    def get_persona_info(self, persona_version: str) -> dict:
        """Возвращает информацию о версии персоны"""
        return self.persona_manager.get_persona_info(persona_version)

    def get_current_mood(self):
        """Возвращает текущее настроение"""
        return self.persona_manager.current_mood

    def trigger_mood_change(self, event: str):
        """
        Изменяет настроение по событию.

        Events: big_achievement, small_win, failure, controversy, etc.
        """
        return self.persona_manager.trigger_mood_change(event)

    def generate_new_mood(self):
        """Генерирует новое случайное настроение"""
        return self.persona_manager.generate_mood()

    # === Методы для работы с изображениями ===

    def is_image_generation_available(self) -> bool:
        """Проверяет, доступен ли поиск фото продуктов"""
        # Всегда доступен — используем базу готовых фото
        return True

    async def generate_image(
        self,
        post_type: str,
        post_content: str,
        custom_prompt: Optional[str] = None,
        style: Optional[ImageStyle] = None,
        use_product_reference: bool = True
    ) -> Tuple[Optional[str], str]:
        """
        Генерирует изображение для поста.

        ПРИОРИТЕТ:
        1. Готовое фото из unified_products/ (если это пост о продукте)
        2. Случайное фото из категории
        3. ТОЛЬКО если нет готового — генерировать через YandexART

        Args:
            post_type: Тип поста
            post_content: Текст поста
            custom_prompt: Пользовательский промпт (опционально)
            style: Визуальный стиль изображения (ImageStyle enum)
            use_product_reference: Использовать готовые фото продуктов

        Returns:
            Tuple[Optional[str], str]: (base64 изображения или путь к файлу, описание)
        """
        try:
            # === 1. СНАЧАЛА ВСЕГДА ИЩЕМ ГОТОВОЕ ФОТО (через MediaLibrary) ===
            # Ищем фото для ЛЮБОГО типа поста, если в тексте упоминается продукт
            if use_product_reference:
                import time
                import base64

                start_time = time.time()

                # НОВОЕ: используем индексированный поиск через MediaLibrary
                try:
                    asset = await self.media_library.find_in_text(post_content, asset_type="product")
                    search_time_ms = (time.time() - start_time) * 1000

                    if asset and asset.file_path:
                        from pathlib import Path
                        photo_path = Path(asset.file_path)

                        if photo_path.exists():
                            with open(photo_path, 'rb') as f:
                                image_base64 = base64.b64encode(f.read()).decode('utf-8')

                            product_name = asset.nl_products[0] if asset.nl_products else "unknown"
                            logger.info(f"[ФОТО] ✅ MediaLibrary: найдено фото {product_name} за {search_time_ms:.1f}ms")
                            return image_base64, f"готовое фото: {product_name} ({photo_path.name})"
                        else:
                            logger.warning(f"[ФОТО] ❌ Файл не существует: {photo_path}")
                    else:
                        logger.info(f"[ФОТО] MediaLibrary: продукт не найден за {search_time_ms:.1f}ms")

                except Exception as e:
                    logger.error(f"[ФОТО] Ошибка MediaLibrary: {e}, fallback на старый метод")

                # FALLBACK: старый метод через ProductReferenceManager
                product_result = self.product_reference.extract_product_from_content(post_content)
                if product_result:
                    keyword, folder_path, photo_path = product_result
                    logger.info(f"[ФОТО] Fallback: найден продукт '{keyword}' → {folder_path}")
                    if photo_path and photo_path.exists():
                        with open(photo_path, 'rb') as f:
                            image_base64 = base64.b64encode(f.read()).decode('utf-8')
                        logger.info(f"[ФОТО] ✅ Fallback: используем фото {photo_path}")
                        return image_base64, f"готовое фото: {keyword} ({photo_path.name})"

            # Фото не найдено — возвращаем None (YandexART удалён)
            logger.info("[ФОТО] Продукт не найден в тексте, фото не будет добавлено")
            return None, ""

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None, ""

    async def regenerate_image(
        self,
        post_type: str,
        post_content: str,
        feedback: Optional[str] = None,
        style: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Повторно ищет фото продукта для поста.

        YandexART удалён — просто повторный поиск готового фото.

        Args:
            post_type: Тип поста
            post_content: Текст поста
            feedback: Не используется (оставлен для совместимости)
            style: Не используется (оставлен для совместимости)

        Returns:
            Tuple[Optional[str], str]: (base64 изображения или None, описание)
        """
        return await self.generate_image(post_type, post_content)

    @staticmethod
    def get_available_image_styles() -> dict:
        """
        Возвращает пустой словарь — стили не используются (YandexART удалён)
        Оставлен для совместимости с интерфейсом.
        """
        return {}
