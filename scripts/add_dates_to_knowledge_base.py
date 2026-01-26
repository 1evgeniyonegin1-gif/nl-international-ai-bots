"""
Скрипт для добавления метаданных с датами в документы базы знаний

Добавляет front matter с date_created и date_updated в файлы .md
которые ещё не имеют этих полей.
"""
import os
import re
from datetime import datetime
from pathlib import Path

# Базовая директория
KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "content" / "knowledge_base"

# Даты по умолчанию для разных категорий
DEFAULT_DATES = {
    "products": {"created": "2024-06-01", "updated": "2026-01-20"},
    "faq": {"created": "2024-08-01", "updated": "2026-01-20"},
    "business": {"created": "2024-07-01", "updated": "2026-01-20"},
    "training": {"created": "2024-09-01", "updated": "2026-01-20"},
    "success_stories": {"created": "2024-10-01", "updated": "2026-01-20"},
    "company": {"created": "2024-06-01", "updated": "2026-01-15"},
    "tools": {"created": "2024-11-01", "updated": "2026-01-20"},
    "from_telegram": {"created": "2026-01-23", "updated": "2026-01-23"},
}


def has_front_matter(content: str) -> bool:
    """Проверяет, есть ли front matter в документе"""
    return content.startswith("---")


def has_dates(content: str) -> bool:
    """Проверяет, есть ли даты в front matter"""
    return "date_created:" in content and "date_updated:" in content


def get_category(filepath: Path) -> str:
    """Определяет категорию документа по пути"""
    parts = filepath.parts
    for i, part in enumerate(parts):
        if part == "knowledge_base" and i + 1 < len(parts):
            return parts[i + 1]
    return "products"  # По умолчанию


def add_dates_to_file(filepath: Path) -> bool:
    """
    Добавляет даты в файл

    Returns:
        True если файл был изменён
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Пропускаем если даты уже есть
    if has_dates(content):
        return False

    category = get_category(filepath)
    dates = DEFAULT_DATES.get(category, DEFAULT_DATES["products"])

    date_front_matter = f"date_created: {dates['created']}\ndate_updated: {dates['updated']}\n"

    if has_front_matter(content):
        # Вставляем даты после первого ---
        new_content = content.replace("---\n", f"---\n{date_front_matter}", 1)
    else:
        # Добавляем front matter в начало
        new_content = f"---\n{date_front_matter}---\n\n{content}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True


def main():
    """Основная функция"""
    modified_count = 0
    skipped_count = 0

    for md_file in KNOWLEDGE_BASE_DIR.rglob("*.md"):
        if add_dates_to_file(md_file):
            print(f"[+] Updated: {md_file.relative_to(KNOWLEDGE_BASE_DIR)}")
            modified_count += 1
        else:
            skipped_count += 1

    print(f"\nResults:")
    print(f"   Modified: {modified_count}")
    print(f"   Skipped (already had dates): {skipped_count}")


if __name__ == "__main__":
    main()
