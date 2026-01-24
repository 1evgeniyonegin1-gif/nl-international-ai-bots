"""
Маппер настроения → версия персоны.

Дополнительная логика для выбора версии Данила на основе контекста.
"""

import random
from content_manager_bot.database.models import MoodState
from .mood_config import MOOD_TO_PERSONA_MAP, PERSONA_CHARACTERISTICS


class MoodToPersonaMapper:
    """Маппит настроение на версию Данила с учётом контекста"""

    def map_mood_to_persona(
        self,
        mood: MoodState,
        post_type: str,
        prefer_persona: str | None = None
    ) -> str:
        """
        Выбирает версию Данила на основе:
        - Категории настроения (joy, anger, etc.)
        - Интенсивности (light, extreme)
        - Типа поста (product, motivation, etc.)
        - Предпочтительной версии (если указано)

        Args:
            mood: Текущее настроение
            post_type: Тип поста
            prefer_persona: Предпочтительная версия (опционально)

        Returns:
            str: Название версии персоны
        """
        # Если указана предпочтительная версия — используем её
        if prefer_persona and prefer_persona in PERSONA_CHARACTERISTICS:
            return prefer_persona

        # Базовый маппинг из конфига
        base_personas = MOOD_TO_PERSONA_MAP.get(
            (mood.category, mood.intensity),
            ["friend"]  # По умолчанию — друг
        )

        # Дополнительная логика на основе типа поста
        post_type_personas = self._get_personas_for_post_type(post_type)

        # Пересечение: кто подходит и под настроение, и под тип поста
        suitable_personas = [
            p for p in base_personas if p in post_type_personas
        ]

        # Если есть подходящие — выбираем из них
        if suitable_personas:
            return random.choice(suitable_personas)

        # Если нет пересечения — приоритет настроению
        return random.choice(base_personas)

    def _get_personas_for_post_type(self, post_type: str) -> list[str]:
        """
        Возвращает подходящие версии для типа поста.

        Args:
            post_type: Тип поста

        Returns:
            list[str]: Список подходящих версий
        """
        post_type_map = {
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

        return post_type_map.get(post_type, ["friend", "expert"])

    def get_persona_characteristics(self, persona_version: str) -> dict:
        """
        Возвращает характеристики версии персоны.

        Args:
            persona_version: Название версии

        Returns:
            dict: Характеристики персоны
        """
        return PERSONA_CHARACTERISTICS.get(persona_version, PERSONA_CHARACTERISTICS["friend"])

    def explain_choice(
        self,
        mood: MoodState,
        persona_version: str,
        post_type: str
    ) -> str:
        """
        Объясняет почему была выбрана эта версия персоны.

        Args:
            mood: Настроение
            persona_version: Выбранная версия
            post_type: Тип поста

        Returns:
            str: Объяснение выбора
        """
        persona_data = self.get_persona_characteristics(persona_version)

        return (
            f"Выбрана версия: {persona_data['name']}\n"
            f"Настроение: {mood.emotion} ({mood.category}/{mood.intensity})\n"
            f"Тип поста: {post_type}\n"
            f"Тон: {persona_data['tone']}\n"
            f"Когда используется: {persona_data['when_to_use']}"
        )
