"""
Модуль воронки продаж для AI-Куратора

Структура:
- keyboards.py - Inline-клавиатуры для воронки
- messages.py - Тексты сообщений прогрева
- client_funnel.py - Цепочка для клиентов
- business_funnel.py - Цепочка для бизнеса
- referral_links.py - Генерация реферальных ссылок
"""

from curator_bot.funnels.keyboards import (
    get_start_keyboard,
    get_pain_keyboard,
    get_income_goal_keyboard,
    get_weight_goal_keyboard,
)
from curator_bot.funnels.referral_links import (
    get_registration_link,
    get_shop_link,
    get_client_registration_link,
)

__all__ = [
    "get_start_keyboard",
    "get_pain_keyboard",
    "get_income_goal_keyboard",
    "get_weight_goal_keyboard",
    "get_registration_link",
    "get_shop_link",
    "get_client_registration_link",
]
