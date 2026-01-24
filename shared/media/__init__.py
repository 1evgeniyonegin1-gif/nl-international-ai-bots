"""
Модуль для работы с медиа контентом (стикеры, гифки, изображения).

Предоставляет:
- MediaManager: управление медиа для ботов
- Каталог стикеров, гифок, эмодзи
"""

from .media_manager import MediaManager, get_media_manager

__all__ = ["MediaManager", "get_media_manager"]
