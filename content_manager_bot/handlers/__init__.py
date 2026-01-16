"""
Обработчики команд и callback для контент-менеджер бота
"""
from content_manager_bot.handlers.admin import router as admin_router
from content_manager_bot.handlers.callbacks import router as callbacks_router

__all__ = ["admin_router", "callbacks_router"]
