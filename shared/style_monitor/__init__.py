"""
Модуль мониторинга каналов-образцов для анализа стиля.
"""
from .channel_fetcher import (
    ChannelFetcher,
    StyleChannelService,
    get_style_service
)

__all__ = [
    "ChannelFetcher",
    "StyleChannelService",
    "get_style_service"
]
