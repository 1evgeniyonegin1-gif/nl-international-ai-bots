"""
Менеджер персон Данила.

Управляет выбором версии персоны на основе:
- Текущего настроения
- Типа контента
- Контекста общения

Используется в:
- AI-Контент-Менеджер: выбор тона для постов
- AI-Куратор: адаптация стиля общения
"""

import random
from typing import Optional, NamedTuple
from dataclasses import dataclass
from loguru import logger

from .mood_config import (
    MOOD_CATEGORIES,
    MOOD_WEIGHTS,
    INTENSITY_DISTRIBUTION,
    PERSONA_CHARACTERISTICS,
    MOOD_TO_PERSONA_MAP,
    get_personas_for_mood,
    get_persona_temperature
)
from .hook_selector import HookSelector


@dataclass
class MoodState:
    """Состояние настроения (упрощённая версия без БД)"""
    category: str       # joy, sadness, anger, etc.
    emotion: str        # конкретная эмоция (happy, angry, etc.)
    intensity: str      # light, medium, strong, extreme
    persona_version: str  # expert, friend, rebel, etc.
    trigger: Optional[str] = None  # событие-триггер


class PersonaContext(NamedTuple):
    """Контекст для генерации контента с персоной"""
    persona_version: str      # Версия персоны
    persona_name: str         # "Данил-Эксперт", etc.
    tone: str                 # Описание тона
    emoji: list[str]          # Подходящие эмодзи
    speech_patterns: list[str]  # Характерные фразы
    temperature: float        # Рекомендуемая температура AI
    hook: Optional[str]       # Цепляющая фраза (если запрошена)
    mood: Optional[MoodState]  # Текущее настроение


class PersonaManager:
    """
    Менеджер персон для AI-ботов.

    Предоставляет:
    - Генерацию настроения
    - Выбор версии персоны
    - Получение контекста для генерации
    - Выбор hook'ов
    """

    def __init__(self):
        """Инициализация менеджера"""
        self.hook_selector = HookSelector()
        self._current_mood: Optional[MoodState] = None
        logger.info("[PersonaManager] Инициализирован")

    def generate_mood(
        self,
        force_category: Optional[str] = None,
        force_intensity: Optional[str] = None,
        trigger: Optional[str] = None
    ) -> MoodState:
        """
        Генерирует новое настроение.

        Args:
            force_category: Принудительная категория (для тестирования)
            force_intensity: Принудительная интенсивность
            trigger: Событие-триггер

        Returns:
            MoodState: Сгенерированное настроение
        """
        # 1. Выбираем категорию
        if force_category and force_category in MOOD_CATEGORIES:
            category = force_category
        else:
            category = self._select_category_weighted()

        # 2. Выбираем интенсивность
        if force_intensity and force_intensity in INTENSITY_DISTRIBUTION:
            intensity = force_intensity
        else:
            intensity = self._select_intensity()

        # 3. Выбираем конкретную эмоцию
        emotion = self._select_emotion(category, intensity)

        # 4. Выбираем версию персоны
        persona_version = self._select_persona(category, intensity)

        # 5. Создаём MoodState
        mood = MoodState(
            category=category,
            emotion=emotion,
            intensity=intensity,
            persona_version=persona_version,
            trigger=trigger
        )

        self._current_mood = mood

        logger.info(
            f"[PersonaManager] Настроение: {emotion} ({category}/{intensity}) -> {persona_version}"
        )

        return mood

    def trigger_mood_change(
        self,
        event: str,
        force_category: Optional[str] = None
    ) -> MoodState:
        """
        Изменяет настроение по триггеру (событие).

        Args:
            event: Название события
            force_category: Категория настроения (опционально)

        Returns:
            MoodState: Новое настроение
        """
        # Маппинг событий -> категории
        event_to_category = {
            "big_achievement": "joy",
            "small_win": "joy",
            "failure": "sadness",
            "setback": "sadness",
            "controversy": "anger",
            "frustration": "anger",
            "challenge": "anticipation",
            "new_opportunity": "excitement",
            "breakthrough": "surprise",
            "deep_thought": "calm"
        }

        # Маппинг событий -> интенсивность
        event_to_intensity = {
            "big_achievement": "extreme",
            "small_win": "medium",
            "failure": "strong",
            "setback": "medium",
            "controversy": "strong",
            "frustration": "medium",
            "challenge": "medium",
            "new_opportunity": "strong",
            "breakthrough": "extreme",
            "deep_thought": "strong"
        }

        category = force_category or event_to_category.get(event)
        intensity = event_to_intensity.get(event, "medium")

        if not category:
            logger.warning(f"[PersonaManager] Неизвестное событие: {event}")
            return self.generate_mood(trigger=event)

        return self.generate_mood(
            force_category=category,
            force_intensity=intensity,
            trigger=event
        )

    def get_persona_context(
        self,
        mood: Optional[MoodState] = None,
        post_type: Optional[str] = None,
        include_hook: bool = False,
        hook_variables: Optional[dict[str, str]] = None
    ) -> PersonaContext:
        """
        Возвращает полный контекст персоны для генерации.

        Args:
            mood: Настроение (если None - используется текущее или генерируется)
            post_type: Тип поста/контента
            include_hook: Включить цепляющую фразу
            hook_variables: Переменные для hook'а

        Returns:
            PersonaContext: Контекст для генерации
        """
        # Получаем или генерируем настроение
        if mood is None:
            mood = self._current_mood or self.generate_mood()

        # Адаптируем персону под тип поста если нужно
        persona_version = self._adapt_persona_for_post_type(
            base_persona=mood.persona_version,
            post_type=post_type
        )

        # Получаем характеристики персоны
        persona_data = PERSONA_CHARACTERISTICS.get(
            persona_version,
            PERSONA_CHARACTERISTICS["friend"]
        )

        # Получаем hook если запрошен
        hook = None
        if include_hook:
            if hook_variables:
                hook = self.hook_selector.select_hook_with_variables(
                    persona_version=persona_version,
                    variables=hook_variables,
                    mood_category=mood.category,
                    post_type=post_type
                )
            else:
                hook = self.hook_selector.select_hook(
                    persona_version=persona_version,
                    mood_category=mood.category,
                    post_type=post_type
                )

        return PersonaContext(
            persona_version=persona_version,
            persona_name=persona_data["name"],
            tone=persona_data["tone"],
            emoji=persona_data["emoji"],
            speech_patterns=persona_data["speech_patterns"],
            temperature=persona_data.get("temperature", 0.7),
            hook=hook,
            mood=mood
        )

    def get_prompt_enhancement(self, context: PersonaContext) -> str:
        """
        Возвращает дополнение к промпту на основе контекста персоны.

        Args:
            context: Контекст персоны

        Returns:
            str: Дополнительный текст для промпта
        """
        persona_data = PERSONA_CHARACTERISTICS.get(
            context.persona_version,
            PERSONA_CHARACTERISTICS["friend"]
        )

        enhancement = f"""
=== СТИЛЬ ОБЩЕНИЯ ===

ВЕРСИЯ ПЕРСОНЫ: {context.persona_name}
ТОН: {context.tone}

ХАРАКТЕРНЫЕ ФРАЗЫ:
{chr(10).join(f'- "{phrase}"' for phrase in context.speech_patterns)}

ОПИСАНИЕ: {persona_data['description']}

ЭМОДЗИ (используй умеренно): {' '.join(context.emoji[:5])}
"""

        if context.mood:
            # Получаем инструкции по эмоциям
            emotion_instructions = self._get_emotion_instructions(
                context.mood.category,
                context.mood.intensity
            )
            enhancement += f"""
ТЕКУЩЕЕ НАСТРОЕНИЕ: {context.mood.emotion} ({context.mood.category}/{context.mood.intensity})

{emotion_instructions}
"""

        if context.hook:
            enhancement += f"""

══════════════════════════════════════════
🎯 ОБЯЗАТЕЛЬНЫЙ HOOK (используй ДОСЛОВНО!)
══════════════════════════════════════════

НАЧНИ ПОСТ РОВНО С ЭТОЙ ФРАЗЫ:
"{context.hook}"

⚠️ СТРОГО! НЕ меняй эту фразу! НЕ переформулируй!
Используй её БУКВАЛЬНО как первое предложение.
После неё развивай мысль в стиле персоны.
══════════════════════════════════════════
"""

        return enhancement

    def _get_emotion_instructions(self, category: str, intensity: str) -> str:
        """
        Возвращает конкретные инструкции для эмоции.

        Args:
            category: Категория настроения
            intensity: Интенсивность

        Returns:
            str: Инструкции для AI
        """
        # Базовые инструкции по категориям
        category_instructions = {
            "joy": {
                "light": "Пиши спокойно-позитивно. Эмодзи: 1-2. Тон: умиротворённый.",
                "medium": "Пиши с теплотой и благодарностью. Эмодзи: 2-3. Делись радостью.",
                "strong": "Пиши с энтузиазмом! Эмодзи: 3-4. Восклицания уместны!",
                "extreme": "ЗАРАЖАЙ ЭНЕРГИЕЙ!!! Эмодзи: 5-7!!! Капс для акцентов!!!"
            },
            "sadness": {
                "light": "Пиши задумчиво, с ноткой грусти. Эмодзи: 0-1. Тон: рефлексивный.",
                "medium": "Пиши честно о сложностях. Эмодзи: 1. Покажи уязвимость.",
                "strong": "Пиши откровенно. Без прикрас. Эмодзи: 0-1. Настоящая боль.",
                "extreme": "Raw и честно. Никаких эмодзи. Только правда. Тяжело — так тяжело."
            },
            "anger": {
                "light": "Пиши с лёгким раздражением. Риторические вопросы. Эмодзи: 1-2.",
                "medium": "Пиши резко, по делу. Короткие фразы. Эмодзи: 2-3 агрессивных.",
                "strong": "Пиши ДЕРЗКО! Провоцируй! Эмодзи: 3-4 огненных! 🔥💥",
                "extreme": "ХВАТИТ! Рви шаблоны! Капс! Эмодзи: 5+! Борись!"
            },
            "love": {
                "light": "Пиши тепло, с заботой. Эмодзи: 1-2 тёплых. Мягкий тон.",
                "medium": "Пиши с искренней любовью. Эмодзи: 2-3 ❤️. Благодарность.",
                "strong": "Пиши от всего сердца! Эмодзи: 3-4! Признательность!",
                "extreme": "Пиши с переполняющей любовью! Эмодзи: 5+! Ты лучшие!"
            },
            "surprise": {
                "light": "Пиши с любопытством. Вопросы. Эмодзи: 1-2. Интерес.",
                "medium": "Пиши с удивлением! Эмодзи: 2-3. 'Не ожидал!' 'Вау!'",
                "strong": "ЧТО?! Не верю! Эмодзи: 3-4! Шок! Изумление!",
                "extreme": "КАКОГО?! НЕВЕРОЯТНО!! Эмодзи: 5+! Мозг взрывается!"
            },
            "anticipation": {
                "light": "Пиши с предвкушением. Эмодзи: 1-2. 'Скоро...' 'Жду...'",
                "medium": "Пиши с нетерпением! Эмодзи: 2-3. 'Не могу дождаться!'",
                "strong": "УЖЕ СКОРО!! Эмодзи: 3-4! Горю! Готов!",
                "extreme": "НЕ МОГУ ЖДАТЬ!!! Эмодзи: 5+! Разрываюсь!"
            },
            "calm": {
                "light": "Пиши расслабленно. Эмодзи: 0-1. Спокойный тон.",
                "medium": "Пиши с мудрым спокойствием. Эмодзи: 1. Zen.",
                "strong": "Пиши глубоко-философски. Эмодзи: 1. Созерцание.",
                "extreme": "Пиши из абсолютного покоя. Минимум слов. Глубина."
            },
            "excitement": {
                "light": "Пиши энергично. Эмодзи: 2. Живо и бодро.",
                "medium": "Пиши с огнём! Эмодзи: 3! Энергия! Драйв!",
                "strong": "ЗАЖИГАЙ!! Эмодзи: 4-5! Капс! Огонь! 🔥🚀",
                "extreme": "БЕЗУМИЕ ЭНЕРГИИ!!! Эмодзи: 6+!!! Взрыв!!!"
            },
            "trust": {
                "light": "Пиши доверительно. Эмодзи: 1-2. 'Между нами...'",
                "medium": "Пиши как другу. Эмодзи: 2. Открыто и честно.",
                "strong": "Пиши с полным доверием. Эмодзи: 2-3. Близость.",
                "extreme": "Пиши как самому близкому. Эмодзи: 3. Душа нараспашку."
            },
            "interest": {
                "light": "Пиши с любопытством. Эмодзи: 1. Наблюдательно.",
                "medium": "Пиши увлечённо! Эмодзи: 2. Погружённо.",
                "strong": "Пиши с глубоким интересом! Эмодзи: 2-3. Исследуй!",
                "extreme": "ПОГРУЖЁН ПОЛНОСТЬЮ!! Эмодзи: 3-4! Одержим темой!"
            }
        }

        # Получаем инструкцию
        cat_data = category_instructions.get(category, {})
        instruction = cat_data.get(intensity, "Пиши естественно. Эмодзи: 2-3.")

        return f"КАК ПИСАТЬ: {instruction}"

    def _select_category_weighted(self) -> str:
        """Выбирает категорию настроения с учётом весов"""
        categories = list(MOOD_WEIGHTS.keys())
        weights = list(MOOD_WEIGHTS.values())
        return random.choices(categories, weights=weights, k=1)[0]

    def _select_intensity(self) -> str:
        """Выбирает интенсивность настроения"""
        intensities = list(INTENSITY_DISTRIBUTION.keys())
        probabilities = list(INTENSITY_DISTRIBUTION.values())
        return random.choices(intensities, weights=probabilities, k=1)[0]

    def _select_emotion(self, category: str, intensity: str) -> str:
        """Выбирает конкретную эмоцию из категории и интенсивности"""
        emotions = MOOD_CATEGORIES[category]["emotions"][intensity]
        return random.choice(emotions)

    def _select_persona(self, category: str, intensity: str) -> str:
        """Выбирает версию персоны на основе настроения"""
        personas = get_personas_for_mood(category, intensity)
        return random.choice(personas)

    def _adapt_persona_for_post_type(
        self,
        base_persona: str,
        post_type: Optional[str]
    ) -> str:
        """
        Адаптирует версию персоны под тип поста.

        Args:
            base_persona: Базовая версия персоны (из настроения)
            post_type: Тип поста

        Returns:
            str: Адаптированная версия персоны
        """
        if not post_type:
            return base_persona

        # Типы постов, где нужна конкретная персона
        post_type_preferences = {
            "product": ["expert", "friend"],
            "motivation": ["friend", "philosopher", "rebel"],
            "news": ["expert", "friend"],
            "tips": ["expert", "friend"],
            "success_story": ["friend", "crazy", "philosopher"],
            "promo": ["crazy", "rebel", "expert"],
            "faq": ["expert", "friend"],
            "myth_busting": ["rebel", "expert"],
            "personal": ["tired", "friend", "philosopher"],
            "celebration": ["crazy", "friend"],
            "philosophical": ["philosopher", "tired"],
            "controversial": ["rebel", "philosopher"]
        }

        preferred = post_type_preferences.get(post_type, [])

        # Если базовая персона подходит под тип поста - оставляем
        if base_persona in preferred:
            return base_persona

        # Иначе выбираем из предпочтительных
        if preferred:
            return random.choice(preferred)

        return base_persona

    @property
    def current_mood(self) -> Optional[MoodState]:
        """Возвращает текущее настроение"""
        return self._current_mood

    def set_mood(self, mood: MoodState):
        """Устанавливает настроение вручную"""
        self._current_mood = mood
        logger.info(f"[PersonaManager] Настроение установлено: {mood.emotion} -> {mood.persona_version}")

    @staticmethod
    def get_all_personas() -> list[str]:
        """Возвращает список всех доступных версий персоны"""
        return list(PERSONA_CHARACTERISTICS.keys())

    @staticmethod
    def get_persona_info(persona_version: str) -> dict:
        """
        Возвращает информацию о версии персоны.

        Args:
            persona_version: Версия персоны

        Returns:
            dict: Информация о персоне
        """
        return PERSONA_CHARACTERISTICS.get(
            persona_version,
            PERSONA_CHARACTERISTICS["friend"]
        )

    def explain_choice(
        self,
        mood: MoodState,
        post_type: Optional[str] = None
    ) -> str:
        """
        Объясняет почему была выбрана эта версия персоны.

        Args:
            mood: Настроение
            post_type: Тип поста

        Returns:
            str: Объяснение выбора
        """
        persona_data = self.get_persona_info(mood.persona_version)

        explanation = (
            f"Выбрана версия: {persona_data['name']}\n"
            f"Настроение: {mood.emotion} ({mood.category}/{mood.intensity})\n"
        )

        if post_type:
            explanation += f"Тип поста: {post_type}\n"

        explanation += (
            f"Тон: {persona_data['tone']}\n"
            f"Когда используется: {persona_data['when_to_use']}"
        )

        if mood.trigger:
            explanation += f"\nТриггер: {mood.trigger}"

        return explanation
