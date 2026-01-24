"""
Утилита для работы с фото продуктов NL International.
Находит и отправляет фото продуктов клиентам.
"""
import os
import random
from pathlib import Path
from typing import Optional, List
from loguru import logger

# Базовый путь к фото продуктов
UNIFIED_PRODUCTS_PATH = Path(__file__).parent.parent.parent / "content" / "unified_products"


# Маппинг ключевых слов на папки с фото
PRODUCT_FOLDERS = {
    # ED Smart
    "ed_smart": ["ed_smart", "energy_diet"],
    "ed smart": ["ed_smart", "energy_diet"],
    "коктейль": ["ed_smart", "energy_diet"],
    "шоколад": ["ed_smart", "energy_diet"],
    "ваниль": ["ed_smart", "energy_diet"],
    "капучино": ["ed_smart", "energy_diet"],
    "фисташка": ["ed_smart", "energy_diet"],

    # Greenflash БАД
    "collagen": ["collagen", "greenflash"],
    "коллаген": ["collagen", "greenflash"],
    "omega": ["omega", "greenflash"],
    "омега": ["omega", "greenflash"],
    "vitamin": ["vitamin_d", "greenflash"],
    "витамин": ["vitamin_d", "greenflash"],
    "greenflash": ["greenflash"],
    "детокс": ["greenflash"],
    "detox": ["greenflash"],

    # 3D Slim
    "3d slim": ["3d_slim"],
    "draineffect": ["draineffect", "3d_slim"],
    "дрейн": ["draineffect", "3d_slim"],
    "похудение": ["3d_slim", "draineffect"],

    # Для детей
    "happy smile": ["happy_smile", "nlka"],
    "для детей": ["nlka", "happy_smile"],
    "детские": ["nlka", "happy_smile"],
    "nlka": ["nlka"],
    "prohelper": ["prohelper", "nlka"],

    # Косметика
    "beloved": ["beloved"],
    "be loved": ["beloved"],
    "косметика": ["beloved"],
    "крем": ["beloved"],
    "сыворотка": ["beloved"],

    # Волосы
    "occuba": ["occuba"],
    "шампунь": ["occuba"],
    "волосы": ["occuba"],

    # Другое
    "biodrone": ["biodrone"],
    "биодрон": ["biodrone"],
    "biotuning": ["biotuning"],
    "fineffect": ["fineffect"],
    "enerwood": ["enerwood"],
    "чай": ["enerwood"],
    "sport": ["sport"],
    "спорт": ["sport"],
    "стартовый набор": ["starter_kit"],
    "starter": ["starter_kit"],
}


def find_product_photos(product_name: str, limit: int = 5) -> List[str]:
    """
    Ищет фото продукта по названию.

    Args:
        product_name: Название или ключевое слово продукта
        limit: Максимальное количество фото

    Returns:
        Список путей к фото
    """
    photos = []
    product_lower = product_name.lower()

    # Находим подходящие папки
    folders_to_search = []
    for keyword, folder_list in PRODUCT_FOLDERS.items():
        if keyword in product_lower:
            folders_to_search.extend(folder_list)

    # Если ничего не нашли - ищем по всем папкам
    if not folders_to_search:
        folders_to_search = list(UNIFIED_PRODUCTS_PATH.iterdir()) if UNIFIED_PRODUCTS_PATH.exists() else []
        folders_to_search = [f.name for f in folders_to_search if f.is_dir() and not f.name.startswith('_')]

    # Убираем дубликаты и ищем фото
    folders_to_search = list(set(folders_to_search))

    for folder_name in folders_to_search:
        folder_path = UNIFIED_PRODUCTS_PATH / folder_name

        if not folder_path.exists():
            continue

        # Рекурсивно ищем jpg файлы
        for photo_path in folder_path.rglob("*.jpg"):
            photos.append(str(photo_path))

        for photo_path in folder_path.rglob("*.png"):
            photos.append(str(photo_path))

        if len(photos) >= limit * 3:  # Собираем больше для рандома
            break

    # Перемешиваем и возвращаем
    if photos:
        random.shuffle(photos)
        return photos[:limit]

    logger.warning(f"No photos found for product: {product_name}")
    return []


def get_random_product_photo(product_name: str) -> Optional[str]:
    """
    Возвращает случайное фото продукта.

    Args:
        product_name: Название продукта

    Returns:
        Путь к фото или None
    """
    photos = find_product_photos(product_name, limit=10)
    if photos:
        return random.choice(photos)
    return None


def get_photo_for_pain(pain: str) -> Optional[str]:
    """
    Возвращает фото продукта для конкретной боли.

    Args:
        pain: Боль клиента (weight, energy, immunity, beauty, kids, sport)

    Returns:
        Путь к фото или None
    """
    pain_to_product = {
        "weight": "ed smart шоколад",
        "energy": "greenflash витамин",
        "immunity": "greenflash витамин",
        "beauty": "collagen",
        "skin": "beloved",
        "kids": "happy smile",
        "sport": "ed smart",
        "detox": "draineffect",
        "sleep": "greenflash",
    }

    product_hint = pain_to_product.get(pain, "ed smart")
    return get_random_product_photo(product_hint)


# Маппинг категорий на фото для быстрого доступа
CATEGORY_PHOTO_MAP = {
    "Energy Diet": "ed_smart",
    "Greenflash БАД": "greenflash",
    "Косметика Be Loved": "beloved",
    "Для детей NLka": "nlka",
    "3D Slim": "3d_slim",
    "Уход за волосами": "occuba",
    "Чай и напитки": "enerwood",
}


def get_photo_by_category(category: str) -> Optional[str]:
    """
    Возвращает фото по категории продукта.

    Args:
        category: Название категории

    Returns:
        Путь к фото или None
    """
    folder = CATEGORY_PHOTO_MAP.get(category)
    if folder:
        return get_random_product_photo(folder)
    return None


# Проверка наличия фото при импорте
if UNIFIED_PRODUCTS_PATH.exists():
    total_photos = sum(1 for _ in UNIFIED_PRODUCTS_PATH.rglob("*.jpg"))
    logger.info(f"Product photos loaded: {total_photos} photos in {UNIFIED_PRODUCTS_PATH}")
else:
    logger.warning(f"Product photos path not found: {UNIFIED_PRODUCTS_PATH}")
