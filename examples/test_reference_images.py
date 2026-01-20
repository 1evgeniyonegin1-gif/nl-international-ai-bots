"""
Пример тестирования reference images
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from content_manager_bot.ai.content_generator import ContentGenerator
from content_manager_bot.utils.product_reference import ProductReferenceManager
from content_manager_bot.utils.image_helpers import add_watermark, add_logo_overlay, PILLOW_AVAILABLE
from loguru import logger


async def test_product_reference_manager():
    """Тест менеджера референсов"""
    logger.info("=== Тестирование ProductReferenceManager ===")

    manager = ProductReferenceManager()

    # Загружаем маппинг
    products = manager.list_all_products()
    logger.info(f"Найдено категорий: {len(products)}")

    for category, items in products.items():
        logger.info(f"\n{category}: {len(items)} продуктов")
        for key, info in items.items():
            logger.info(f"  - {info['name']}")

    # Тест поиска по контенту
    test_content = "Сегодня хочу рассказать про GreenFlash Vision Plus - лучшие витамины для зрения!"
    result = manager.extract_product_from_content(test_content)

    if result:
        category, product_key, product_info = result
        logger.info(f"\n✅ Найден продукт в тексте: {product_info['name']} ({category}/{product_key})")

        # Проверяем наличие изображения
        image_base64 = manager.get_product_image_base64(product_key, category)
        if image_base64:
            logger.info(f"✅ Изображение найдено: {len(image_base64)} символов base64")
        else:
            logger.warning(f"⚠️  Изображение не найдено (это нормально - нужно добавить фото)")
    else:
        logger.info("❌ Продукт не найден в тексте")


async def test_image_generation():
    """Тест генерации изображений с референсами"""
    logger.info("\n=== Тестирование генерации изображений ===")

    generator = ContentGenerator()

    if not generator.is_image_generation_available():
        logger.warning("⚠️  YandexART не настроен - пропускаем тест генерации")
        return

    # Генерируем пост о продукте
    logger.info("Генерируем пост о продукте...")
    post_text, _ = await generator.generate_post(
        post_type="product",
        custom_topic="GreenFlash Vision Plus"
    )
    logger.info(f"Пост сгенерирован ({len(post_text)} символов):\n{post_text[:200]}...")

    # Генерируем изображение (автоматически определит режим)
    logger.info("\nГенерируем изображение...")
    image_base64, prompt = await generator.generate_image(
        post_type="product",
        post_content=post_text,
        use_product_reference=True
    )

    if image_base64:
        logger.info(f"✅ Изображение сгенерировано: {len(image_base64)} символов")
        logger.info(f"Промпт: {prompt[:150]}...")

        # Проверяем режим
        if "[image-to-image mode]" in prompt:
            logger.info("✅ Использован image-to-image режим (с референсом)")
        else:
            logger.info("ℹ️  Использован text-to-image режим (без референса)")
    else:
        logger.error("❌ Ошибка генерации изображения")


async def test_compositing():
    """Тест композитинга (водяные знаки, логотипы)"""
    logger.info("\n=== Тестирование композитинга ===")

    if not PILLOW_AVAILABLE:
        logger.warning("⚠️  Pillow не установлен - установите: pip install Pillow")
        return

    logger.info("✅ Pillow установлен и доступен")

    # Для теста используем фиктивное изображение (1x1 JPEG)
    import base64
    # Минимальный JPEG (1x1 пиксель, черный)
    test_image = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="

    # Тест watermark
    logger.info("\nТест добавления водяного знака...")
    result = add_watermark(
        test_image,
        watermark_text="NL International",
        position="bottom_right",
        opacity=128
    )
    if result:
        logger.info("✅ Водяной знак добавлен успешно")
    else:
        logger.error("❌ Ошибка добавления водяного знака")

    # Тест logo overlay
    logger.info("\nТест наложения логотипа...")
    logo_path = Path(__file__).parent.parent / "content" / "resources" / "nl_logo.png"

    if logo_path.exists():
        result = add_logo_overlay(
            test_image,
            str(logo_path),
            position="bottom_right",
            logo_size_percent=10
        )
        if result:
            logger.info("✅ Логотип наложен успешно")
        else:
            logger.error("❌ Ошибка наложения логотипа")
    else:
        logger.info(f"ℹ️  Логотип не найден: {logo_path}")
        logger.info("   Добавьте логотип для тестирования наложения")


async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Начинаем тестирование Reference Images системы\n")

    try:
        # Тест 1: Менеджер референсов
        await test_product_reference_manager()

        # Тест 2: Генерация изображений
        await test_image_generation()

        # Тест 3: Композитинг
        await test_compositing()

        logger.info("\n✅ Все тесты завершены!")
        logger.info("\n📝 Следующие шаги:")
        logger.info("1. Добавьте фотографии продуктов в content/product_images/")
        logger.info("2. Обновите products_mapping.json")
        logger.info("3. (Опционально) Добавьте логотип в content/resources/nl_logo.png")
        logger.info("4. Запустите бота и протестируйте: /generate product")

    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
