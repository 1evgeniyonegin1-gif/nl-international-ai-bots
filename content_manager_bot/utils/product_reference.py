"""
Утилиты для работы с референсными изображениями продуктов
"""
import os
import json
import base64
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger


class ProductReferenceManager:
    """Менеджер для работы с референсными изображениями продуктов"""

    def __init__(self, base_path: Optional[str] = None):
        """
        Инициализация менеджера

        Args:
            base_path: Базовый путь к папке с изображениями продуктов
        """
        if base_path is None:
            # Определяем путь относительно корня проекта
            project_root = Path(__file__).parent.parent.parent
            base_path = project_root / "content" / "product_images"

        self.base_path = Path(base_path)
        self.mapping_file = self.base_path / "products_mapping.json"
        self._mapping: Optional[Dict[str, Any]] = None

    def load_mapping(self) -> Dict[str, Any]:
        """
        Загружает маппинг продуктов из JSON файла

        Returns:
            Dict: Словарь с информацией о продуктах
        """
        if self._mapping is not None:
            return self._mapping

        if not self.mapping_file.exists():
            logger.warning(f"Product mapping file not found: {self.mapping_file}")
            return {}

        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                self._mapping = json.load(f)
                logger.info(f"Loaded product mapping: {len(self._mapping)} categories")
                return self._mapping
        except Exception as e:
            logger.error(f"Error loading product mapping: {e}")
            return {}

    def get_product_info(self, product_key: str, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о продукте

        Args:
            product_key: Ключ продукта (например, "vision_plus")
            category: Категория (например, "greenflash"). Если None, ищет по всем категориям

        Returns:
            Dict: Информация о продукте или None
        """
        mapping = self.load_mapping()

        if category:
            # Поиск в конкретной категории
            if category in mapping and product_key in mapping[category]:
                return mapping[category][product_key]
        else:
            # Поиск по всем категориям
            for cat_name, products in mapping.items():
                if product_key in products:
                    return products[product_key]

        return None

    def get_product_image_base64(self, product_key: str, category: Optional[str] = None) -> Optional[str]:
        """
        Загружает изображение продукта в base64

        Args:
            product_key: Ключ продукта
            category: Категория (опционально)

        Returns:
            str: Base64-encoded изображение или None
        """
        product_info = self.get_product_info(product_key, category)
        if not product_info:
            logger.warning(f"Product not found: {product_key} in category {category}")
            return None

        image_path = self.base_path / product_info["image"]
        if not image_path.exists():
            logger.warning(f"Product image not found: {image_path}")
            return None

        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                logger.info(f"Loaded product image: {product_info['name']}")
                return image_base64
        except Exception as e:
            logger.error(f"Error loading product image: {e}")
            return None

    def find_product_by_name(self, product_name: str) -> Optional[tuple[str, str, Dict[str, Any]]]:
        """
        Ищет продукт по части названия

        Args:
            product_name: Название или часть названия продукта

        Returns:
            tuple: (category, product_key, product_info) или None
        """
        mapping = self.load_mapping()
        product_name_lower = product_name.lower()

        for category, products in mapping.items():
            for product_key, product_info in products.items():
                if (product_name_lower in product_info["name"].lower() or
                    product_name_lower in product_info["description"].lower() or
                    product_name_lower in product_key.lower()):
                    return category, product_key, product_info

        return None

    def list_all_products(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Возвращает список всех доступных продуктов

        Returns:
            Dict: Полный маппинг продуктов
        """
        return self.load_mapping()

    def extract_product_from_content(self, content: str) -> Optional[tuple[str, str, Dict[str, Any]]]:
        """
        Пытается извлечь упоминание продукта из текста контента

        Args:
            content: Текст поста

        Returns:
            tuple: (category, product_key, product_info) или None
        """
        # Список ключевых слов для поиска продуктов
        product_keywords = {
            "vision": ("greenflash", "vision_plus"),
            "зрение": ("greenflash", "vision_plus"),
            "лютеин": ("greenflash", "vision_plus"),
            "мультивитамин": ("greenflash", "multivitamin"),
            "витамины": ("greenflash", "multivitamin"),
            "омега": ("greenflash", "omega3"),
            "omega": ("greenflash", "omega3"),
            "рыбий жир": ("greenflash", "omega3"),
            "витамин d": ("greenflash", "vitamin_d3"),
            "витамин д": ("greenflash", "vitamin_d3"),
            "d3": ("greenflash", "vitamin_d3"),
            "коллаген": ("greenflash", "collagen"),
            "collagen": ("greenflash", "collagen"),
            "крем": ("lovely", "face_cream"),
            "сыворотка": ("lovely", "serum"),
            "serum": ("lovely", "serum"),
            "мицеллярн": ("lovely", "micellar_water"),
            "micellar": ("lovely", "micellar_water"),
            "лосьон": ("lovely", "body_lotion"),
            "lotion": ("lovely", "body_lotion"),
            "energy diet": ("energy_diet", "smart"),
            "энерджи диет": ("energy_diet", "smart"),
            "коктейль": ("energy_diet", "shake_chocolate"),
            "shake": ("energy_diet", "shake_chocolate"),
            "детские": ("other", "kids_vitamins"),
            "детям": ("other", "kids_vitamins"),
            "чай": ("other", "tea"),
            "tea": ("other", "tea")
        }

        content_lower = content.lower()

        # Ищем ключевые слова в тексте
        for keyword, (category, product_key) in product_keywords.items():
            if keyword in content_lower:
                product_info = self.get_product_info(product_key, category)
                if product_info:
                    logger.info(f"Found product reference in content: {product_info['name']}")
                    return category, product_key, product_info

        return None

    def generate_image_to_image_prompt(self, product_info: Dict[str, Any], original_prompt: str) -> str:
        """
        Генерирует промпт для image-to-image режима

        Args:
            product_info: Информация о продукте
            original_prompt: Оригинальный промпт

        Returns:
            str: Модифицированный промпт для улучшения фона
        """
        # Для image-to-image мы хотим сохранить продукт, но улучшить фон
        prompt = (
            f"Улучши фон этого изображения продукта {product_info['name']}. "
            f"Сохрани продукт без изменений, но создай профессиональный студийный фон. "
            f"{original_prompt}. "
            f"Продукт должен оставаться в центре внимания, фон - дополнять композицию."
        )

        return prompt
