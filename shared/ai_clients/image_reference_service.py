"""
Сервис для работы с референсными изображениями из NL Ассистента

Позволяет:
1. Загружать базу референсов
2. Выбирать подходящий референс для продукта/категории
3. Генерировать image-to-image с референсом через YandexART
"""

import json
import base64
import random
from pathlib import Path
from typing import Optional
from loguru import logger


class ImageReferenceService:
    """Сервис для работы с референсными изображениями"""

    def __init__(self, references_path: Optional[Path] = None):
        """
        Инициализация сервиса

        Args:
            references_path: Путь к файлу image_references.json
        """
        if references_path is None:
            references_path = (
                Path(__file__).parent.parent.parent
                / 'content'
                / 'nl_assistant_materials'
                / 'image_references.json'
            )

        self.references_path = references_path
        self.references_db = None
        self._load_references()

    def _load_references(self):
        """Загружает базу референсов"""
        if not self.references_path.exists():
            logger.warning(f"References file not found: {self.references_path}")
            self.references_db = {'products': {}, 'categories': {}}
            return

        try:
            with open(self.references_path, 'r', encoding='utf-8') as f:
                self.references_db = json.load(f)
            logger.info(
                f"Loaded references: {len(self.references_db.get('products', {}))} products"
            )
        except Exception as e:
            logger.error(f"Error loading references: {e}")
            self.references_db = {'products': {}, 'categories': {}}

    def has_references(self) -> bool:
        """Проверяет, есть ли загруженные референсы"""
        return bool(self.references_db.get('products'))

    def get_product_ids(self) -> list:
        """Возвращает список ID продуктов с референсами"""
        return list(self.references_db.get('products', {}).keys())

    def get_reference_for_product(
        self,
        product_id: str,
        media_category: Optional[str] = None
    ) -> Optional[dict]:
        """
        Получает референсное изображение для продукта

        Args:
            product_id: ID продукта (energy_diet, collagen, etc.)
            media_category: Категория медиа (promo, presentation, etc.)

        Returns:
            dict с path и context или None
        """
        products = self.references_db.get('products', {})

        # Пробуем точное совпадение
        if product_id in products:
            references = products[product_id].get('references', [])
        else:
            # Пробуем частичное совпадение
            for pid, data in products.items():
                if product_id.lower() in pid.lower() or pid.lower() in product_id.lower():
                    references = data.get('references', [])
                    break
            else:
                # Возвращаем из general
                references = products.get('general', {}).get('references', [])

        if not references:
            return None

        # Фильтруем по категории медиа
        if media_category:
            filtered = [r for r in references if r.get('category') == media_category]
            if filtered:
                references = filtered

        # Выбираем случайный референс
        return random.choice(references)

    def get_reference_by_category(self, media_category: str) -> Optional[dict]:
        """
        Получает референс по категории медиа (promo, presentation, etc.)

        Args:
            media_category: Категория медиа

        Returns:
            dict с path, product и context или None
        """
        categories = self.references_db.get('categories', {})

        if media_category not in categories:
            return None

        items = categories[media_category]
        if not items:
            return None

        return random.choice(items)

    def get_reference_image_base64(self, reference: dict) -> Optional[str]:
        """
        Загружает референсное изображение и конвертирует в base64

        Args:
            reference: dict с path к изображению

        Returns:
            Base64-encoded изображение или None
        """
        if not reference or 'path' not in reference:
            return None

        image_path = Path(reference['path'])

        if not image_path.exists():
            logger.warning(f"Reference image not found: {image_path}")
            return None

        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading reference image: {e}")
            return None

    def detect_product_from_text(self, text: str) -> Optional[str]:
        """
        Определяет продукт из текста поста

        Args:
            text: Текст поста

        Returns:
            ID продукта или None
        """
        text_lower = text.lower()

        # Маппинг ключевых слов к product_id
        keyword_map = {
            'energy_diet': ['energy diet', 'энерджи дайет', 'энерджи диет', 'ed '],
            'energy_diet_smart': ['ed smart', 'smart', 'смарт'],
            'energy_diet_hd': ['ed hd', 'hd', 'хд'],
            'greenflash': ['greenflash', 'green flash', 'грин флеш', 'гринфлеш'],
            'collagen': ['collagen', 'коллаген'],
            'draineffect': ['draineffect', 'drain effect', 'драйн', 'дрейн'],
            '3d_slim': ['3d slim', '3д слим', 'слим'],
            'omega': ['omega', 'омега'],
            'biodrone': ['biodrone', 'биодрон'],
            'enerwood': ['enerwood', 'энервуд', 'чай'],
            'occuba': ['occuba', 'оккуба', 'косметика'],
            'beloved': ['be loved', 'белавед', 'би лавед'],
            'baby_food': ['детское', 'baby', 'малыш', 'ребёнок', 'для детей'],
            'sport': ['протеин', 'protein', 'спорт', 'sport', 'гейнер', 'bcaa'],
        }

        for product_id, keywords in keyword_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return product_id

        return None

    def get_best_reference_for_post(
        self,
        post_content: str,
        post_type: str = 'product',
    ) -> Optional[tuple[str, dict]]:
        """
        Выбирает лучший референс для поста

        Args:
            post_content: Текст поста
            post_type: Тип поста (product, promo, etc.)

        Returns:
            tuple(base64_image, reference_info) или None
        """
        # Определяем продукт из текста
        product_id = self.detect_product_from_text(post_content)

        # Определяем категорию медиа из типа поста
        post_type_to_media = {
            'product': 'promo',
            'promo': 'promo',
            'tips': 'info',
            'success_story': 'result',
            'motivation': 'presentation',
        }
        media_category = post_type_to_media.get(post_type)

        # Получаем референс
        reference = None

        if product_id:
            reference = self.get_reference_for_product(product_id, media_category)
            logger.info(f"Found reference for product: {product_id}")

        if not reference and media_category:
            reference = self.get_reference_by_category(media_category)
            logger.info(f"Found reference by category: {media_category}")

        if not reference:
            # Берем любой из general
            reference = self.get_reference_for_product('general')
            logger.info("Using general reference")

        if not reference:
            return None

        # Загружаем изображение
        image_base64 = self.get_reference_image_base64(reference)

        if not image_base64:
            return None

        return image_base64, reference


# Глобальный экземпляр сервиса
_reference_service: Optional[ImageReferenceService] = None


def get_reference_service() -> ImageReferenceService:
    """Возвращает глобальный экземпляр сервиса референсов"""
    global _reference_service
    if _reference_service is None:
        _reference_service = ImageReferenceService()
    return _reference_service
