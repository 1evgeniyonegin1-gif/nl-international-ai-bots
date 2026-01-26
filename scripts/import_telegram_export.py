#!/usr/bin/env python3
"""
Парсер экспорта Telegram для импорта тем/вдохновения в контент-бота.

Использование:
    python scripts/import_telegram_export.py "C:\path\to\ChatExport\result.json"

Автор: Claude Code
Дата: 2026-01-26
"""

import json
import sys
import asyncio
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from collections import Counter

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from shared.database.base import AsyncSessionLocal
from content_manager_bot.database.models import ImportedPost


# Ключевые слова для категоризации
CATEGORY_KEYWORDS = {
    "product": [
        # NL продукты
        "коктейль", "протеин", "витамин", "коллаген", "ed", "energy diet",
        "энерджи", "дрейн", "drain", "метабуст", "metaboost", "greenflash",
        "omega", "омега", "пробиотик", "пребиотик", "бад", "добавка",
        "препарат", "порошок", "капсулы", "сыворотка", "крем",
        # Проблемы здоровья (которые решают продукты)
        "похудеть", "похудение", "вес", "сон", "спать", "усталость",
        "энергия", "волосы", "кожа", "ногти", "суставы", "иммунитет",
        "пищеварение", "обмен веществ", "метаболизм", "завтрак",
    ],
    "motivation": [
        "мотивация", "начать", "страх", "мечта", "цель", "вера",
        "уверенность", "не сдавайся", "первый шаг", "действуй", "сделал",
        "решился", "начал", "достиг", "смог", "получилось", "победа",
        "препятствие", "трудность", "сложно", "справился", "преодолел",
        "лень", "прокрастинация", "сомнения", "боюсь", "не могу",
    ],
    "business": [
        "бизнес", "сетевой", "партнёр", "партнер", "команда", "доход",
        "заработок", "nl", "компания", "структура", "спонсор", "лидер",
        "квалификация", "статус", "bonus", "бонус", "оборот", "товарооборот",
        "рекрутинг", "приглашать", "регистрация", "новичок", "наставник",
        "обучение", "вебинар", "тренинг", "презентация", "мероприятие",
    ],
    "success": [
        "история", "результат", "достижение", "путь", "трансформация",
        "было-стало", "до и после", "первый чек", "первая продажа",
        "первый партнёр", "кейс", "отзыв", "благодарность", "спасибо",
        "изменил жизнь", "вышла в", "закрыл", "закрыла", "выполнил",
        "рост", "прогресс", "динамика", "mlm", "сетевик",
    ],
    "tips": [
        "совет", "лайфхак", "ошибка", "секрет", "способ", "метод",
        "как", "почему", "зачем", "лучше", "хуже", "важно",
        "утро", "привычка", "режим", "планирование", "тайм-менеджмент",
        "продуктивность", "эффективность", "правило", "принцип",
        "рекомендую", "не делай", "делай", "попробуй",
    ],
    "news": [
        "новинка", "акция", "скидка", "событие", "анонс", "запуск",
        "релиз", "обновление", "промо", "распродажа", "подарок",
        "конкурс", "розыгрыш", "winner", "победитель", "результаты",
    ],
    "lifestyle": [
        "жизнь", "семья", "дети", "ребёнок", "муж", "жена",
        "путешествие", "отдых", "хобби", "время", "свобода",
        "баланс", "личное", "выходные", "отпуск", "удовольствие",
        "счастье", "радость", "благодарность", "утро", "вечер",
    ],
}


def extract_text_from_message(message: dict) -> Optional[str]:
    """
    Извлекает текст из сообщения Telegram экспорта.

    В экспорте text может быть:
    - строкой
    - списком объектов с type и text
    """
    text_field = message.get("text", "")

    if isinstance(text_field, str):
        return text_field.strip() if text_field else None

    if isinstance(text_field, list):
        parts = []
        for item in text_field:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        text = "".join(parts).strip()
        return text if text else None

    return None


def extract_reactions_count(message: dict) -> int:
    """Извлекает общее количество реакций на сообщение."""
    reactions = message.get("reactions", [])
    total = 0
    for reaction in reactions:
        total += reaction.get("count", 0)
    return total


def check_has_formatting(message: dict) -> bool:
    """Проверяет, есть ли форматирование в сообщении."""
    text_field = message.get("text", "")

    if isinstance(text_field, list):
        for item in text_field:
            if isinstance(item, dict):
                item_type = item.get("type", "plain")
                if item_type in ("bold", "italic", "underline", "text_link", "code"):
                    return True

    # Проверяем text_entities
    entities = message.get("text_entities", [])
    for entity in entities:
        if isinstance(entity, dict):
            entity_type = entity.get("type", "plain")
            if entity_type in ("bold", "italic", "underline", "text_link", "code"):
                return True

    return False


def categorize_text(text: str) -> str:
    """
    Определяет категорию текста по ключевым словам.
    Возвращает категорию с максимальным количеством совпадений.
    """
    text_lower = text.lower()
    scores: Dict[str, int] = Counter()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                scores[category] += 1

    if not scores:
        return "lifestyle"  # По умолчанию

    # Возвращаем категорию с максимальным score
    return scores.most_common(1)[0][0]


def calculate_quality_score(
    reactions_count: int,
    char_count: int,
    has_formatting: bool
) -> float:
    """
    Рассчитывает score качества поста.

    Формула: reactions * 0.4 + log(char_count) * 0.3 + has_formatting * 0.3
    """
    # Нормализуем реакции (логарифмически)
    reactions_score = math.log(reactions_count + 1) * 2  # +1 чтобы избежать log(0)

    # Нормализуем длину текста
    # Идеальная длина 200-800 символов
    if char_count < 50:
        length_score = 0
    elif char_count < 200:
        length_score = char_count / 200 * 3
    elif char_count <= 800:
        length_score = 3
    elif char_count <= 1500:
        length_score = 3 - (char_count - 800) / 700
    else:
        length_score = 1

    # Бонус за форматирование
    formatting_score = 2 if has_formatting else 0

    # Итоговый score
    total = reactions_score * 0.4 + length_score * 0.3 + formatting_score * 0.3
    return round(total, 2)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Парсит дату из формата Telegram экспорта."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


async def import_telegram_export(export_path: str, min_length: int = 50) -> Tuple[int, int, int]:
    """
    Импортирует посты из Telegram экспорта в базу данных.

    Args:
        export_path: Путь к файлу result.json
        min_length: Минимальная длина текста для импорта

    Returns:
        (imported_count, skipped_count, duplicate_count)
    """
    export_file = Path(export_path)
    if not export_file.exists():
        raise FileNotFoundError(f"Файл не найден: {export_path}")

    print(f"Загружаю экспорт из: {export_path}")

    with open(export_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    channel_name = data.get("name", "Unknown Channel")
    messages = data.get("messages", [])

    print(f"Канал: {channel_name}")
    print(f"Всего сообщений: {len(messages)}")

    imported = 0
    skipped = 0
    duplicates = 0

    # Статистика по категориям
    category_stats: Dict[str, int] = Counter()

    async with AsyncSessionLocal() as session:
        for msg in messages:
            # Пропускаем служебные сообщения
            if msg.get("type") != "message":
                skipped += 1
                continue

            # Извлекаем текст
            text = extract_text_from_message(msg)
            if not text or len(text) < min_length:
                skipped += 1
                continue

            # Пропускаем сообщения с медиа без текста
            if msg.get("media_type") and len(text) < 100:
                skipped += 1
                continue

            source_id = msg.get("id", 0)
            reactions_count = extract_reactions_count(msg)
            has_formatting = check_has_formatting(msg)
            char_count = len(text)
            category = categorize_text(text)
            quality_score = calculate_quality_score(reactions_count, char_count, has_formatting)
            original_date = parse_date(msg.get("date"))

            # Используем upsert для избежания дубликатов
            stmt = insert(ImportedPost).values(
                source_id=source_id,
                source_channel=channel_name,
                text=text,
                category=category,
                reactions_count=reactions_count,
                char_count=char_count,
                has_formatting=has_formatting,
                quality_score=quality_score,
                original_date=original_date,
                is_used=False,
            ).on_conflict_do_nothing(
                index_elements=["source_channel", "source_id"]
            )

            result = await session.execute(stmt)

            if result.rowcount > 0:
                imported += 1
                category_stats[category] += 1
            else:
                duplicates += 1

        await session.commit()

    print(f"\n=== Результаты импорта ===")
    print(f"Импортировано: {imported}")
    print(f"Пропущено (короткие/служебные): {skipped}")
    print(f"Дубликаты: {duplicates}")
    print(f"\n=== По категориям ===")
    for cat, count in sorted(category_stats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    return imported, skipped, duplicates


async def show_stats():
    """Показывает статистику импортированных постов."""
    async with AsyncSessionLocal() as session:
        # Общее количество
        total = await session.scalar(select(func.count(ImportedPost.id)))

        # По категориям
        category_counts = await session.execute(
            select(ImportedPost.category, func.count(ImportedPost.id))
            .group_by(ImportedPost.category)
        )

        # Использованных
        used = await session.scalar(
            select(func.count(ImportedPost.id)).where(ImportedPost.is_used == True)
        )

        print(f"\n=== Статистика базы тем ===")
        print(f"Всего: {total}")
        print(f"Использовано: {used}")
        print(f"Доступно: {total - used}")
        print(f"\nПо категориям:")
        for category, count in category_counts:
            print(f"  {category}: {count}")


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python {sys.argv[0]} <путь_к_result.json>")
        print(f"  python {sys.argv[0]} --stats")
        print()
        print("Примеры:")
        print(f'  python {sys.argv[0]} "C:\\Users\\...\\ChatExport\\result.json"')
        print(f'  python {sys.argv[0]} --stats')
        sys.exit(1)

    if sys.argv[1] == "--stats":
        asyncio.run(show_stats())
    else:
        export_path = sys.argv[1]
        asyncio.run(import_telegram_export(export_path))


if __name__ == "__main__":
    main()
