"""
Проактивный онбординг для AI-Куратора

Модуль включает:
- proactive_tasks.py - Чеклисты по дням для новичков
- onboarding_scheduler.py - Автоматические напоминания
"""

from .proactive_tasks import (
    OnboardingTasks,
    get_task_for_day,
    get_user_progress,
    mark_task_completed
)
from .onboarding_scheduler import OnboardingScheduler

__all__ = [
    'OnboardingTasks',
    'get_task_for_day',
    'get_user_progress',
    'mark_task_completed',
    'OnboardingScheduler'
]
