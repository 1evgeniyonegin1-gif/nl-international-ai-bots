"""
Модуль настроений для content_manager_bot.

DEPRECATED: Этот модуль перемещён в shared/persona/.
Используйте импорты из shared.persona вместо content_manager_bot.mood.

Пример:
    # Старый способ (deprecated):
    from content_manager_bot.mood.mood_config import MOOD_CATEGORIES

    # Новый способ:
    from shared.persona import MOOD_CATEGORIES
"""

# Re-export из shared.persona для обратной совместимости
from shared.persona import (
    PersonaManager,
    MOOD_CATEGORIES,
    MOOD_WEIGHTS,
    PERSONA_CHARACTERISTICS,
    MOOD_TO_PERSONA_MAP,
    INTENSITY_DISTRIBUTION,
    get_personas_for_mood,
    TOTAL_EMOTIONS,
)

# Псевдоним для обратной совместимости
MoodSystem = PersonaManager

__all__ = [
    "PersonaManager",
    "MoodSystem",  # deprecated alias
    "MOOD_CATEGORIES",
    "MOOD_WEIGHTS",
    "PERSONA_CHARACTERISTICS",
    "MOOD_TO_PERSONA_MAP",
    "INTENSITY_DISTRIBUTION",
    "get_personas_for_mood",
    "TOTAL_EMOTIONS",
]
