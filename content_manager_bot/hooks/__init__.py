"""
Hook-система для генерации цепляющих фраз.

DEPRECATED: Этот модуль перемещён в shared/persona/.
Используйте импорты из shared.persona вместо content_manager_bot.hooks.

Пример:
    # Старый способ (deprecated):
    from content_manager_bot.hooks import HookSelector

    # Новый способ:
    from shared.persona import HookSelector
"""

# Re-export из shared.persona для обратной совместимости
from shared.persona import (
    HOOK_TEMPLATES,
    TOTAL_HOOKS,
    HookSelector,
)

__all__ = [
    "HOOK_TEMPLATES",
    "TOTAL_HOOKS",
    "HookSelector",
]
